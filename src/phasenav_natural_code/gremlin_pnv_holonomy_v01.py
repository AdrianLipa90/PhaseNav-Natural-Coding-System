from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from numbers import Real
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
from .gremlin_relational_compiler_v01 import RelationalCompilation
from .gremlin_strict_admission_v01 import (
    GremlinStrictAdmissionError,
    finite_real,
    nonnegative_real,
)
from .model import Kaku, RadicalGraph, Relation
from .native_pnv_exec_v01 import NativePNVExecutionResult, execute_pnv, parse_pnv

HOLONOMY_CONTRACT = "PNCS_PNV_INFORMATION_HOLONOMY_V0_1"
HOLONOMY_COMPILATION_RECEIPT_SCHEMA = "PNCS_PNV_INFORMATION_HOLONOMY_COMPILATION_RECEIPT_V0_1"
HOLONOMY_AUDIT_RECEIPT_SCHEMA = "PNCS_PNV_INFORMATION_HOLONOMY_AUDIT_RECEIPT_V0_1"
INFORMATION_TRANSPORT_CONNECTION_ID = "PNCS_INFORMATION_TRANSPORT_CONNECTION_V0_1"
LEGACY_TYPED_CONNECTION_CONTRACT = "PNV_CONNECTION_TYPED_HOLONOMY_CONTRACT_V1_CANDIDATE"
LEGACY_TYPED_CONNECTION_CONTRACT_SHA256 = "bb243b1d2b8f96df28bbe011b50032214aff981cf0ff35384b1b1251df7af997"
CONNECTION_STATES = frozenset({"READY_CANDIDATE", "OPEN"})


class PNVInformationHolonomyError(RuntimeError):
    pass


def _canonical_value(value: Any, field: str = "holonomy value") -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise PNVInformationHolonomyError(f"{field} must be canonical finite JSON")
        return value
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item, f"{field}[{i}]") for i, item in enumerate(value)]
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise PNVInformationHolonomyError(
                    f"{field} contains a non-string JSON object key"
                )
            out[key] = _canonical_value(item, f"{field}.{key}")
        return {key: out[key] for key in sorted(out)}
    raise PNVInformationHolonomyError(f"{field} must be canonical finite JSON")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _canonical_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _finite_numeric(value: Any, field: str) -> float:
    try:
        return finite_real(value, field)
    except GremlinStrictAdmissionError as exc:
        raise PNVInformationHolonomyError(f"{field} must be finite numeric") from exc


def _finite_nonnegative(value: Any, field: str) -> float:
    try:
        return nonnegative_real(value, field)
    except GremlinStrictAdmissionError as exc:
        raise PNVInformationHolonomyError(f"{field} must be finite non-negative") from exc


def _nonempty(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PNVInformationHolonomyError(f"{field} must be a non-empty string")
    return value.strip()


def _safe_token(value: str) -> str:
    text = _nonempty(value, "token").upper()
    token = "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")
    if not token:
        raise PNVInformationHolonomyError("empty canonical token")
    return token


def exact_state_metric(left: Any, right: Any) -> float:
    return 0.0 if _canonical_bytes(left) == _canonical_bytes(right) else 1.0


def numeric_linf_metric(left: Any, right: Any) -> float:
    if isinstance(left, Real) and not isinstance(left, bool):
        if not isinstance(right, Real) or isinstance(right, bool):
            raise PNVInformationHolonomyError("numeric L-inf metric type mismatch")
        a = _finite_numeric(left, "numeric L-inf left")
        b = _finite_numeric(right, "numeric L-inf right")
        defect = abs(a - b)
        if not math.isfinite(defect):
            raise PNVInformationHolonomyError("numeric L-inf metric overflowed")
        return defect
    if isinstance(left, Sequence) and not isinstance(left, (str, bytes, bytearray)):
        if not isinstance(right, Sequence) or isinstance(right, (str, bytes, bytearray)):
            raise PNVInformationHolonomyError("numeric L-inf metric sequence mismatch")
        if len(left) != len(right) or not left:
            raise PNVInformationHolonomyError(
                "numeric L-inf metric requires equal non-empty sequences"
            )
        defects = []
        for index, (a_raw, b_raw) in enumerate(zip(left, right)):
            try:
                a = finite_real(a_raw, f"numeric L-inf left[{index}]")
                b = finite_real(b_raw, f"numeric L-inf right[{index}]")
            except GremlinStrictAdmissionError as exc:
                raise PNVInformationHolonomyError(
                    "numeric L-inf metric requires finite numeric coordinates"
                ) from exc
            defect = abs(a - b)
            if not math.isfinite(defect):
                raise PNVInformationHolonomyError("numeric L-inf metric overflowed")
            defects.append(defect)
        return max(defects)
    raise PNVInformationHolonomyError(
        "numeric L-inf metric supports finite scalar or flat numeric sequence"
    )


@dataclass(frozen=True)
class HolonomyConnection:
    connection_id: str
    connection_kind: str
    state_space_id: str
    contract_ref: str
    execution_state: str = "READY_CANDIDATE"
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "connection_id", _nonempty(self.connection_id, "connection_id")
        )
        object.__setattr__(
            self, "connection_kind", _nonempty(self.connection_kind, "connection_kind")
        )
        object.__setattr__(
            self, "state_space_id", _nonempty(self.state_space_id, "state_space_id")
        )
        object.__setattr__(
            self, "contract_ref", _nonempty(self.contract_ref, "contract_ref")
        )
        state = _nonempty(self.execution_state, "execution_state").upper()
        if state not in CONNECTION_STATES:
            raise PNVInformationHolonomyError(
                f"connection execution_state must be one of {sorted(CONNECTION_STATES)}"
            )
        object.__setattr__(self, "execution_state", state)
        refs = tuple(_nonempty(ref, "connection evidence_ref") for ref in self.evidence_refs)
        object.__setattr__(self, "evidence_refs", refs)

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "connection_kind": self.connection_kind,
            "state_space_id": self.state_space_id,
            "contract_ref": self.contract_ref,
            "execution_state": self.execution_state,
            "evidence_refs": list(self.evidence_refs),
        }

    @property
    def connection_sha256(self) -> str:
        return _sha256(self.payload)


def information_transport_connection(
    state_space_id: str,
    *,
    evidence_refs: Sequence[str] = (),
) -> HolonomyConnection:
    return HolonomyConnection(
        connection_id=INFORMATION_TRANSPORT_CONNECTION_ID,
        connection_kind="INFORMATION_TRANSPORT",
        state_space_id=state_space_id,
        contract_ref=HOLONOMY_CONTRACT,
        execution_state="READY_CANDIDATE",
        evidence_refs=tuple(evidence_refs),
    )


@dataclass(frozen=True)
class LawFrameNode:
    law_id: str
    domain: str
    kaku: Kaku
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "law_id", _nonempty(self.law_id, "law_id"))
        object.__setattr__(self, "domain", _nonempty(self.domain, "domain"))
        if not isinstance(self.kaku, Kaku):
            raise PNVInformationHolonomyError("LawFrameNode requires Kaku")
        refs = tuple(_nonempty(ref, "law-frame evidence_ref") for ref in self.evidence_refs)
        object.__setattr__(self, "evidence_refs", refs)

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
        object.__setattr__(self, "edge_id", _nonempty(self.edge_id, "edge_id"))
        object.__setattr__(
            self, "source_node_id", _nonempty(self.source_node_id, "source_node_id")
        )
        object.__setattr__(
            self, "target_node_id", _nonempty(self.target_node_id, "target_node_id")
        )
        object.__setattr__(
            self, "transform_name", _nonempty(self.transform_name, "transform_name")
        )
        refs = tuple(_nonempty(ref, "transport evidence_ref") for ref in self.evidence_refs)
        object.__setattr__(self, "evidence_refs", refs)


@dataclass(frozen=True)
class HolonomyInvariant:
    invariant_id: str
    mode: str = "EXACT"
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "invariant_id", _nonempty(self.invariant_id, "invariant_id")
        )
        mode = _nonempty(self.mode, "invariant mode").upper()
        if mode not in {"EXACT", "ABS"}:
            raise PNVInformationHolonomyError("invariant mode must be EXACT or ABS")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(
            self, "tolerance", _finite_nonnegative(self.tolerance, "invariant tolerance")
        )


@dataclass(frozen=True)
class InformationHolonomyLoop:
    loop_id: str
    connection: HolonomyConnection
    nodes: tuple[LawFrameNode, ...]
    transports: tuple[LawTransport, ...]
    invariants: tuple[HolonomyInvariant, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "loop_id", _nonempty(self.loop_id, "loop_id"))
        if not isinstance(self.connection, HolonomyConnection):
            raise PNVInformationHolonomyError(
                "information-holonomy loop requires explicit HolonomyConnection"
            )
        if not self.nodes:
            raise PNVInformationHolonomyError(
                "information-holonomy loop requires at least one law node"
            )
        if any(not isinstance(node, LawFrameNode) for node in self.nodes):
            raise PNVInformationHolonomyError("holonomy nodes must be LawFrameNode entries")
        if any(not isinstance(edge, LawTransport) for edge in self.transports):
            raise PNVInformationHolonomyError(
                "holonomy transports must be LawTransport entries"
            )
        if any(not isinstance(item, HolonomyInvariant) for item in self.invariants):
            raise PNVInformationHolonomyError(
                "holonomy invariants must be HolonomyInvariant entries"
            )
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise PNVInformationHolonomyError("law-frame node ids must be unique")
        basis_ids = {node.kaku.vector.basis_id for node in self.nodes}
        if len(basis_ids) != 1:
            raise PNVInformationHolonomyError(
                "law-frame KAKU nodes must share one exact PNCS basis"
            )
        if len(self.transports) != len(self.nodes):
            raise PNVInformationHolonomyError(
                "closed law-frame loop requires one ordered transport per node"
            )
        for index, edge in enumerate(self.transports):
            expected_source = self.nodes[index].node_id
            expected_target = self.nodes[(index + 1) % len(self.nodes)].node_id
            if (
                edge.source_node_id != expected_source
                or edge.target_node_id != expected_target
            ):
                raise PNVInformationHolonomyError(
                    f"transport order does not close loop at index {index}: "
                    f"{edge.source_node_id}->{edge.target_node_id} != "
                    f"{expected_source}->{expected_target}"
                )
        invariant_ids = [item.invariant_id for item in self.invariants]
        if len(invariant_ids) != len(set(invariant_ids)):
            raise PNVInformationHolonomyError("holonomy invariant ids must be unique")
        refs = tuple(_nonempty(ref, "loop evidence_ref") for ref in self.evidence_refs)
        object.__setattr__(self, "evidence_refs", refs)


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
    return tuple(
        sorted(
            set(
                (
                    *loop.evidence_refs,
                    *loop.connection.evidence_refs,
                    f"holonomy_loop:{loop.loop_id}",
                    f"connection_id:{loop.connection.connection_id}",
                    f"connection_contract:{loop.connection.contract_ref}",
                    f"connection_sha256:{loop.connection.connection_sha256}",
                )
            )
        )
    )


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
    generation_binding = _nonempty(generation_binding, "generation_binding")
    identity = _nonempty(identity, "identity")
    authority = _nonempty(authority, "authority")

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
            evidence_refs=tuple(
                sorted(
                    set(
                        (
                            *_loop_evidence(loop),
                            *node.evidence_refs,
                            f"law_id:{node.law_id}",
                            f"domain:{node.domain}",
                        )
                    )
                )
            ),
        )
        kaku_candidates[node.node_id] = candidate
        kaku_refs[node.node_id] = str(candidate["candidate_id"])
        if authoring_root is not None:
            persist_candidate(candidate, authoring_root=authoring_root)

    for edge in loop.transports:
        radical.add_relation(
            Relation(
                edge.edge_id,
                edge.source_node_id,
                edge.target_node_id,
                f"LAW_TRANSPORT:{loop.connection.connection_id}:{edge.transform_name}",
            )
        )

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
            evidence_refs=tuple(
                sorted(
                    set(
                        (
                            *_loop_evidence(loop),
                            *edge.evidence_refs,
                            f"transport:{edge.edge_id}",
                            f"transform:{edge.transform_name}",
                        )
                    )
                )
            ),
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
                "connection_id": loop.connection.connection_id,
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

    pnv_text = render_operator_program(
        tuple(operators), emits=("HOL.RETURN",), mode="READ_ONLY"
    )
    parsed = parse_pnv(pnv_text)
    body = {
        "schema": HOLONOMY_COMPILATION_RECEIPT_SCHEMA,
        "holonomy_contract": HOLONOMY_CONTRACT,
        "loop_id": loop.loop_id,
        "connection": {
            **loop.connection.payload,
            "connection_sha256": loop.connection.connection_sha256,
        },
        "legacy_connection_firewall": {
            "contract": LEGACY_TYPED_CONNECTION_CONTRACT,
            "contract_sha256": LEGACY_TYPED_CONNECTION_CONTRACT_SHA256,
            "principle": "EXPLICIT_CONNECTION_TYPE_REQUIRED",
        },
        "law_frame": [
            {
                "node_id": node.node_id,
                "law_id": node.law_id,
                "domain": node.domain,
                "kaku_candidate_id": kaku_refs[node.node_id],
            }
            for node in loop.nodes
        ],
        "node_candidate_ids": {
            k: str(v["candidate_id"]) for k, v in sorted(kaku_candidates.items())
        },
        "radical_candidate_id": radical_id,
        "operator_candidate_ids": [
            str(candidate["candidate_id"]) for candidate in operators
        ],
        "transport_plan": transport_plan,
        "invariants": [
            {
                "invariant_id": item.invariant_id,
                "mode": item.mode,
                "tolerance": item.tolerance,
            }
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
        spec=loop,
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
        try:
            left = finite_real(baseline, "ABS invariant baseline")
            right = finite_real(current, "ABS invariant current")
        except GremlinStrictAdmissionError as exc:
            raise PNVInformationHolonomyError("ABS invariant requires finite numeric scalar") from exc
        defect = abs(left - right)
        if not math.isfinite(defect):
            raise PNVInformationHolonomyError("ABS invariant defect overflowed")
        return defect
    raise PNVInformationHolonomyError(f"unsupported invariant mode: {mode}")


def _call_metric(
    callback: Callable[..., Any],
    label: str,
    *args: Any,
) -> Any:
    try:
        return callback(*args)
    except PNVInformationHolonomyError:
        raise
    except Exception as exc:
        raise PNVInformationHolonomyError(f"{label} callback failed") from exc


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
    receipt_connection = compilation.receipt.get("connection")
    if (
        compilation.receipt.get("loop_id") != loop.loop_id
        or compilation.receipt.get("holonomy_contract") != HOLONOMY_CONTRACT
        or not isinstance(receipt_connection, Mapping)
        or receipt_connection.get("connection_sha256")
        != loop.connection.connection_sha256
        or receipt_connection.get("connection_id") != loop.connection.connection_id
    ):
        raise PNVInformationHolonomyError(
            "holonomy loop/connection/compilation receipt mismatch"
        )
    if loop.connection.execution_state != "READY_CANDIDATE":
        raise PNVInformationHolonomyError(
            f"holonomy connection execution gate OPEN: {loop.connection.connection_id}"
        )
    if not callable(state_metric):
        raise PNVInformationHolonomyError("explicit state metric is required")
    metric_id = _nonempty(metric_id, "metric_id")
    tolerance = _finite_nonnegative(state_tolerance, "state_tolerance")

    required_transforms = [edge.transform_name for edge in loop.transports]
    missing = [
        name
        for name in required_transforms
        if name not in transforms or not callable(transforms[name])
    ]
    if missing:
        raise PNVInformationHolonomyError(
            f"missing admitted holonomy transform(s): {sorted(set(missing))}"
        )

    evaluators = dict(invariant_evaluators or {})
    missing_invariants = [
        item.invariant_id
        for item in loop.invariants
        if item.invariant_id not in evaluators
        or not callable(evaluators[item.invariant_id])
    ]
    if missing_invariants:
        raise PNVInformationHolonomyError(
            f"missing invariant evaluator(s): {sorted(set(missing_invariants))}"
        )

    execution = execute_pnv(
        compilation.pnv_text,
        sources={"holonomy.input": initial_state},
        transforms={
            name: transforms[name] for name in sorted(set(required_transforms))
        },
    )
    final_state = execution.emitted.get("HOL.RETURN")
    raw_state_defect = _call_metric(
        state_metric,
        f"state metric {metric_id}",
        initial_state,
        final_state,
    )
    state_defect = _finite_nonnegative(raw_state_defect, "state holonomy defect")

    stages: list[tuple[str, Any]] = [("HOL.START", initial_state)]
    for index in range(len(loop.transports)):
        name = f"HOL.EDGE.{index:03d}"
        if name not in execution.values:
            raise PNVInformationHolonomyError(
                f"missing holonomy execution stage: {name}"
            )
        stages.append((name, execution.values[name]))

    invariant_results: list[Mapping[str, Any]] = []
    all_invariants_pass = True
    for invariant in loop.invariants:
        evaluator = evaluators[invariant.invariant_id]
        baseline = _call_metric(
            evaluator,
            f"invariant evaluator {invariant.invariant_id}",
            initial_state,
        )
        stage_rows = []
        max_defect = 0.0
        for stage_name, stage_state in stages:
            value = _call_metric(
                evaluator,
                f"invariant evaluator {invariant.invariant_id}",
                stage_state,
            )
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
        invariant_passed = max_defect <= invariant.tolerance
        all_invariants_pass = all_invariants_pass and invariant_passed
        invariant_results.append(
            {
                "invariant_id": invariant.invariant_id,
                "mode": invariant.mode,
                "tolerance": invariant.tolerance,
                "max_defect": max_defect,
                "passed": invariant_passed,
                "stages": stage_rows,
            }
        )

    inverse = resolve_gremlin_candidate_inverse_lineage(compilation, execution)
    passed = state_defect <= tolerance and all_invariants_pass
    native_boundary = execution.receipt.get("effect_boundary")
    if not isinstance(native_boundary, Mapping):
        raise PNVInformationHolonomyError(
            "native execution effect boundary receipt is missing"
        )
    audit_callbacks = [
        f"state_metric:{metric_id}",
        *[
            f"invariant_evaluator:{item.invariant_id}"
            for item in loop.invariants
        ],
    ]
    body = {
        "schema": HOLONOMY_AUDIT_RECEIPT_SCHEMA,
        "holonomy_contract": HOLONOMY_CONTRACT,
        "loop_id": loop.loop_id,
        "connection_id": loop.connection.connection_id,
        "connection_sha256": loop.connection.connection_sha256,
        "connection_contract_ref": loop.connection.contract_ref,
        "state_space_id": loop.connection.state_space_id,
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
        "effect_boundary": {
            "external_effects": None,
            "external_effects_status": "UNVERIFIED_CALLBACK_BOUNDARY",
            "callback_effects_verified": False,
            "native_execution_external_effects": native_boundary.get(
                "external_effects"
            ),
            "native_execution_external_effects_status": native_boundary.get(
                "external_effects_status"
            ),
            "native_callbacks_invoked": list(
                native_boundary.get("callbacks_invoked", [])
            ),
            "audit_callbacks_invoked": audit_callbacks,
        },
        "external_effects": None,
        "external_effects_status": "UNVERIFIED_CALLBACK_BOUNDARY",
        "deterministic_fields_only": False,
        "deterministic_serialization": True,
        "callback_determinism_verified": False,
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
            raise PNVInformationHolonomyError(
                "content-addressed holonomy receipt collision"
            )
    return str(target)
