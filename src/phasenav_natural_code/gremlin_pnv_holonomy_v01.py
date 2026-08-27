from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .gremlin_inverse_lineage_v01 import (
    GremlinCandidateInverseLineage,
    resolve_gremlin_candidate_inverse_lineage,
)
from .gremlin_pnv_authoring_v02 import (
    build_kaku_candidate,
    build_operator_candidate,
    build_radical_candidate,
    persist_candidate,
    render_operator_program,
)
from .gremlin_relational_compiler_v01 import (
    RelationalCompilation,
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
)
from .model import Kaku, RadicalGraph, Relation
from .native_pnv_exec_v01 import NativePNVExecutionResult, execute_pnv, parse_pnv

HOLONOMY_CONTRACT = "PNCS_PNV_INFORMATION_HOLONOMY_V0_1"
HOLONOMY_COMPILATION_RECEIPT_SCHEMA = "PNCS_PNV_INFORMATION_HOLONOMY_COMPILATION_RECEIPT_V0_1"
HOLONOMY_AUDIT_RECEIPT_SCHEMA = "PNCS_PNV_INFORMATION_HOLONOMY_AUDIT_RECEIPT_V0_1"


class PNVInformationHolonomyError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _finite_nonnegative(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise PNVInformationHolonomyError(f"{field} must be finite non-negative") from exc
    if not math.isfinite(out) or out < 0.0:
        raise PNVInformationHolonomyError(f"{field} must be finite non-negative")
    return out


def _safe_token(value: str) -> str:
    token = "".join(ch if ch.isalnum() else "_" for ch in str(value).upper()).strip("_")
    if not token:
        raise PNVInformationHolonomyError("empty canonical token")
    return token


def exact_state_metric(left: Any, right: Any) -> float:
    return 0.0 if _canonical_bytes(left) == _canonical_bytes(right) else 1.0


def numeric_linf_metric(left: Any, right: Any) -> float:
    if isinstance(left, (int, float)) and not isinstance(left, bool):
        if not isinstance(right, (int, float)) or isinstance(right, bool):
            raise PNVInformationHolonomyError("numeric L-inf metric type mismatch")
        a, b = float(left), float(right)
        if not math.isfinite(a) or not math.isfinite(b):
            raise PNVInformationHolonomyError("numeric L-inf metric requires finite values")
        return abs(a - b)
    if isinstance(left, Sequence) and not isinstance(left, (str, bytes, bytearray)):
        if not isinstance(right, Sequence) or isinstance(right, (str, bytes, bytearray)):
            raise PNVInformationHolonomyError("numeric L-inf metric sequence mismatch")
        if len(left) != len(right) or not left:
            raise PNVInformationHolonomyError("numeric L-inf metric requires equal non-empty sequences")
        defects = []
        for a_raw, b_raw in zip(left, right):
            if isinstance(a_raw, bool) or isinstance(b_raw, bool):
                raise PNVInformationHolonomyError("numeric L-inf metric rejects boolean coordinates")
            try:
                a, b = float(a_raw), float(b_raw)
            except (TypeError, ValueError) as exc:
                raise PNVInformationHolonomyError("numeric L-inf metric requires numeric coordinates") from exc
            if not math.isfinite(a) or not math.isfinite(b):
                raise PNVInformationHolonomyError("numeric L-inf metric requires finite coordinates")
            defects.append(abs(a - b))
        return max(defects)
    raise PNVInformationHolonomyError("numeric L-inf metric supports finite scalar or flat numeric sequence")


@dataclass(frozen=True)
class LawFrameNode:
    law_id: str
    domain: str
    kaku: Kaku
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.law_id or not self.domain:
            raise PNVInformationHolonomyError("law_id and domain are required")
        if not isinstance(self.kaku, Kaku):
            raise PNVInformationHolonomyError("LawFrameNode requires Kaku")

    @property
    def node_id(self) -> str:
        return self.kaku.kaku_id


@dataclass(frozen=True)
class LawTransport:
    edge_id: str
    source_node_id: str
    target_node_id: str
    transform_name: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all((self.edge_id, self.source_node_id, self.target_node_id, self.transform_name)):
            raise PNVInformationHolonomyError("law transport fields are required")


@dataclass(frozen=True)
class HolonomyInvariant:
    invariant_id: str
    mode: str = "EXACT"
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        if not self.invariant_id:
            raise PNVInformationHolonomyError("invariant_id is required")
        mode = str(self.mode).upper()
        if mode not in {"EXACT", "ABS"}:
            raise PNVInformationHolonomyError("invariant mode must be EXACT or ABS")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "tolerance", _finite_nonnegative(self.tolerance, "invariant tolerance"))


@dataclass(frozen=True)
class InformationHolonomyLoop:
    loop_id: str
    nodes: tuple[LawFrameNode, ...]
    transports: tuple[LawTransport, ...]
    invariants: tuple[HolonomyInvariant, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.loop_id:
            raise PNVInformationHolonomyError("loop_id is required")
        if len(self.nodes) < 2:
            raise PNVInformationHolonomyError("information-holonomy loop requires at least two law nodes")
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise PNVInformationHolonomyError("law-frame node ids must be unique")
        if len({node.domain for node in self.nodes}) < 2:
            raise PNVInformationHolonomyError("law-frame loop requires at least two source domains")
        basis_ids = {node.kaku.vector.basis_id for node in self.nodes}
        if len(basis_ids) != 1:
            raise PNVInformationHolonomyError("law-frame KAKU nodes must share one exact PNCS basis")
        if len(self.transports) != len(self.nodes):
            raise PNVInformationHolonomyError("closed law-frame loop requires one ordered transport per node")
        for index, edge in enumerate(self.transports):
            expected_source = self.nodes[index].node_id
            expected_target = self.nodes[(index + 1) % len(self.nodes)].node_id
            if edge.source_node_id != expected_source or edge.target_node_id != expected_target:
                raise PNVInformationHolonomyError(
                    f"transport order does not close loop at index {index}: "
                    f"{edge.source_node_id}->{edge.target_node_id} != {expected_source}->{expected_target}"
                )
        invariant_ids = [item.invariant_id for item in self.invariants]
        if len(invariant_ids) != len(set(invariant_ids)):
            raise PNVInformationHolonomyError("holonomy invariant ids must be unique")


@dataclass(frozen=True)
class InformationHolonomyAudit:
    loop: InformationHolonomyLoop
    compilation: RelationalCompilation
    execution: NativePNVExecutionResult
    inverse_lineage: GremlinCandidateInverseLineage
    state_defect: float
    invariant_results: tuple[Mapping[str, Any], ...]
    receipt: Mapping[str, Any]


def _loop_evidence(loop: InformationHolonomyLoop) -> tuple[str, ...]:
    return tuple(sorted(set((*loop.evidence_refs, f"holonomy_loop:{loop.loop_id}"))))


def compile_information_holonomy_loop(
    loop: InformationHolonomyLoop,
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    authoring_root: Path | str | None = None,
) -> RelationalCompilation:
    if not isinstance(loop, InformationHolonomyLoop):
        raise PNVInformationHolonomyError("InformationHolonomyLoop required")
    if not generation_binding or not identity or not authority:
        raise PNVInformationHolonomyError("generation_binding, identity and authority are required")

    spec = RelationalIsomorphism(
        isomorphism_id=f"HOL.{loop.loop_id}",
        invariant_id=f"HOLONOMY.{loop.loop_id}",
        invariant_description="information transport around an admitted closed physical-law frame",
        nodes=tuple(
            RelationalNode(node.kaku, node.domain, f"law:{node.law_id}")
            for node in loop.nodes
        ),
        edges=tuple(
            RelationalEdge(edge.edge_id, edge.source_node_id, edge.target_node_id, "FLOWS_TO")
            for edge in loop.transports
        ),
        evidence_refs=_loop_evidence(loop),
    )

    basis_id = loop.nodes[0].kaku.vector.basis_id
    radical = RadicalGraph(f"HOLONOMY.{_safe_token(loop.loop_id)}", basis_id)
    kaku_candidates: dict[str, Mapping[str, Any]] = {}
    kaku_refs: dict[str, str] = {}
    for node in loop.nodes:
        radical.add_kaku(node.kaku)
        candidate = build_kaku_candidate(
            node.kaku,
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            evidence_refs=tuple(sorted(set((*_loop_evidence(loop), *node.evidence_refs, f"law_id:{node.law_id}", f"domain:{node.domain}")))),
        )
        kaku_candidates[node.node_id] = candidate
        kaku_refs[node.node_id] = str(candidate["candidate_id"])
        if authoring_root is not None:
            persist_candidate(candidate, authoring_root=authoring_root)

    for edge in loop.transports:
        radical.add_relation(Relation(edge.edge_id, edge.source_node_id, edge.target_node_id, f"LAW_TRANSPORT:{edge.transform_name}"))

    radical_candidate = build_radical_candidate(
        radical,
        kaku_candidate_ids=kaku_refs,
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        evidence_refs=_loop_evidence(loop),
    )
    if authoring_root is not None:
        persist_candidate(radical_candidate, authoring_root=authoring_root)
    radical_id = str(radical_candidate["candidate_id"])

    operators: list[Mapping[str, Any]] = []
    source = build_operator_candidate(
        "HOL.START",
        "SOURCE",
        ("holonomy.input",),
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        radical_candidate_id=radical_id,
        evidence_refs=_loop_evidence(loop),
    )
    operators.append(source)
    if authoring_root is not None:
        persist_candidate(source, authoring_root=authoring_root)

    previous = "HOL.START"
    transport_plan: list[dict[str, Any]] = []
    for index, edge in enumerate(loop.transports):
        name = f"HOL.EDGE.{index:03d}"
        candidate = build_operator_candidate(
            name,
            "TRANSFORM",
            (previous, edge.transform_name),
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            radical_candidate_id=radical_id,
            evidence_refs=tuple(sorted(set((*_loop_evidence(loop), *edge.evidence_refs, f"transport:{edge.edge_id}", f"transform:{edge.transform_name}")))),
        )
        operators.append(candidate)
        if authoring_root is not None:
            persist_candidate(candidate, authoring_root=authoring_root)
        transport_plan.append(
            {
                "index": index,
                "edge_id": edge.edge_id,
                "source_node_id": edge.source_node_id,
                "target_node_id": edge.target_node_id,
                "transform_name": edge.transform_name,
                "operator_name": name,
            }
        )
        previous = name

    returned = build_operator_candidate(
        "HOL.RETURN",
        "RETURN",
        (previous,),
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        radical_candidate_id=radical_id,
        evidence_refs=_loop_evidence(loop),
    )
    operators.append(returned)
    if authoring_root is not None:
        persist_candidate(returned, authoring_root=authoring_root)

    pnv_text = render_operator_program(tuple(operators), emits=("HOL.RETURN",), mode="READ_ONLY")
    parsed = parse_pnv(pnv_text)
    body = {
        "schema": HOLONOMY_COMPILATION_RECEIPT_SCHEMA,
        "holonomy_contract": HOLONOMY_CONTRACT,
        "loop_id": loop.loop_id,
        "node_candidate_ids": {k: str(v["candidate_id"]) for k, v in sorted(kaku_candidates.items())},
        "radical_candidate_id": radical_id,
        "operator_candidate_ids": [str(candidate["candidate_id"]) for candidate in operators],
        "transport_plan": transport_plan,
        "invariants": [
            {"invariant_id": item.invariant_id, "mode": item.mode, "tolerance": item.tolerance}
            for item in loop.invariants
        ],
        "pnv_source_sha256": parsed.source_sha256,
        "pnv_graph_sha256": parsed.graph_sha256,
        "epistemic": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "conformance_execution_allowed": True,
    }
    receipt = {**body, "receipt_sha256": _sha256(body)}
    return RelationalCompilation(
        spec=spec,
        kaku_candidates=kaku_candidates,
        radical_candidate=radical_candidate,
        operator_candidates=tuple(operators),
        pnv_text=pnv_text,
        source_bindings={},
        receipt=receipt,
    )


def _invariant_defect(mode: str, baseline: Any, current: Any) -> float:
    if mode == "EXACT":
        return exact_state_metric(baseline, current)
    if mode == "ABS":
        if isinstance(baseline, bool) or isinstance(current, bool):
            raise PNVInformationHolonomyError("ABS invariant requires numeric scalar")
        try:
            left, right = float(baseline), float(current)
        except (TypeError, ValueError) as exc:
            raise PNVInformationHolonomyError("ABS invariant requires numeric scalar") from exc
        if not math.isfinite(left) or not math.isfinite(right):
            raise PNVInformationHolonomyError("ABS invariant requires finite scalar")
        return abs(left - right)
    raise PNVInformationHolonomyError(f"unsupported invariant mode: {mode}")


def audit_information_holonomy(
    loop: InformationHolonomyLoop,
    compilation: RelationalCompilation,
    *,
    initial_state: Any,
    transforms: Mapping[str, Callable[[Any], Any]],
    state_metric: Callable[[Any, Any], float],
    metric_id: str,
    state_tolerance: float = 0.0,
    invariant_evaluators: Mapping[str, Callable[[Any], Any]] | None = None,
) -> InformationHolonomyAudit:
    if not isinstance(loop, InformationHolonomyLoop):
        raise PNVInformationHolonomyError("InformationHolonomyLoop required")
    if not isinstance(compilation, RelationalCompilation):
        raise PNVInformationHolonomyError("RelationalCompilation required")
    if compilation.receipt.get("loop_id") != loop.loop_id or compilation.receipt.get("holonomy_contract") != HOLONOMY_CONTRACT:
        raise PNVInformationHolonomyError("holonomy loop/compilation receipt mismatch")
    if not callable(state_metric) or not metric_id:
        raise PNVInformationHolonomyError("explicit state metric and metric_id are required")
    tolerance = _finite_nonnegative(state_tolerance, "state_tolerance")
    required_transforms = [edge.transform_name for edge in loop.transports]
    missing = [name for name in required_transforms if name not in transforms or not callable(transforms[name])]
    if missing:
        raise PNVInformationHolonomyError(f"missing admitted holonomy transform(s): {sorted(set(missing))}")

    evaluators = dict(invariant_evaluators or {})
    missing_invariants = [item.invariant_id for item in loop.invariants if item.invariant_id not in evaluators or not callable(evaluators[item.invariant_id])]
    if missing_invariants:
        raise PNVInformationHolonomyError(f"missing invariant evaluator(s): {sorted(set(missing_invariants))}")

    execution = execute_pnv(
        compilation.pnv_text,
        sources={"holonomy.input": initial_state},
        transforms={name: transforms[name] for name in sorted(set(required_transforms))},
    )
    final_state = execution.emitted.get("HOL.RETURN")
    raw_state_defect = state_metric(initial_state, final_state)
    state_defect = _finite_nonnegative(raw_state_defect, "state holonomy defect")

    stages: list[tuple[str, Any]] = [("HOL.START", initial_state)]
    for index in range(len(loop.transports)):
        name = f"HOL.EDGE.{index:03d}"
        if name not in execution.values:
            raise PNVInformationHolonomyError(f"missing holonomy execution stage: {name}")
        stages.append((name, execution.values[name]))

    invariant_results: list[Mapping[str, Any]] = []
    all_invariants_pass = True
    for invariant in loop.invariants:
        evaluator = evaluators[invariant.invariant_id]
        baseline = evaluator(initial_state)
        stage_rows = []
        max_defect = 0.0
        for stage_name, stage_state in stages:
            value = evaluator(stage_state)
            defect = _finite_nonnegative(
                _invariant_defect(invariant.mode, baseline, value),
                f"invariant defect {invariant.invariant_id}",
            )
            max_defect = max(max_defect, defect)
            stage_rows.append(
                {
                    "stage": stage_name,
                    "value_sha256": _sha256(value),
                    "defect_from_initial": defect,
                }
            )
        passed = max_defect <= invariant.tolerance
        all_invariants_pass = all_invariants_pass and passed
        invariant_results.append(
            {
                "invariant_id": invariant.invariant_id,
                "mode": invariant.mode,
                "tolerance": invariant.tolerance,
                "max_defect": max_defect,
                "passed": passed,
                "stages": stage_rows,
            }
        )

    inverse = resolve_gremlin_candidate_inverse_lineage(compilation, execution)
    passed = state_defect <= tolerance and all_invariants_pass
    body = {
        "schema": HOLONOMY_AUDIT_RECEIPT_SCHEMA,
        "holonomy_contract": HOLONOMY_CONTRACT,
        "loop_id": loop.loop_id,
        "compilation_receipt_sha256": compilation.receipt["receipt_sha256"],
        "native_execution_receipt_sha256": execution.receipt["receipt_sha256"],
        "inverse_lineage_id": inverse.lineage_id,
        "inverse_lineage_receipt_sha256": inverse.receipt["receipt_sha256"],
        "metric_id": metric_id,
        "state_tolerance": tolerance,
        "state_defect": state_defect,
        "invariant_results": invariant_results,
        "status": "PASS" if passed else "FAIL",
        "epistemic": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "external_effects": False,
        "deterministic_fields_only": True,
    }
    receipt = {**body, "receipt_sha256": _sha256(body)}
    return InformationHolonomyAudit(
        loop=loop,
        compilation=compilation,
        execution=execution,
        inverse_lineage=inverse,
        state_defect=state_defect,
        invariant_results=tuple(invariant_results),
        receipt=receipt,
    )


def persist_information_holonomy_audit(
    audit: InformationHolonomyAudit,
    *,
    authoring_root: Path | str,
) -> str:
    if not isinstance(audit, InformationHolonomyAudit):
        raise PNVInformationHolonomyError("InformationHolonomyAudit required")
    root = Path(authoring_root) / "holonomy"
    root.mkdir(parents=True, exist_ok=True)
    digest = str(audit.receipt["receipt_sha256"])
    target = root / f"{digest}.json"
    raw = _canonical_bytes(audit.receipt) + b"\n"
    try:
        with target.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        if target.read_bytes() != raw:
            raise PNVInformationHolonomyError("content-addressed holonomy receipt collision")
    return str(target)
