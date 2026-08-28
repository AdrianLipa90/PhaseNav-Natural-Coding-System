from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .gremlin_pnv_authoring_v02 import (
    GremlinPNVAuthoringSession,
    build_kaku_candidate,
    build_operator_candidate,
    build_radical_candidate,
    open_gremlin_pnv_authoring_live,
    persist_candidate,
    render_operator_program,
)
from .model import Kaku, RadicalGraph, Relation
from .native_pnv_exec_v01 import NativePNVExecutionResult, execute_pnv, parse_pnv

COMPILER_SCHEMA = "PNCS_GREMLIN_RELATIONAL_ISOMORPHISM_COMPILER_V0_1"
COMPILATION_RECEIPT_SCHEMA = "PNCS_GREMLIN_RELATIONAL_COMPILATION_RECEIPT_V0_1"

DEFAULT_RELATION_OPCODE = {
    "ORDER": "ORDER",
    "PRECEDES": "ORDER",
    "TRANSFORMS_TO": "ORDER",
    "FLOWS_TO": "ORDER",
    "CAUSES": "ORDER",
    "BINDS": "COMPOSITION",
    "COUPLES": "COMPOSITION",
    "COMPOSES_WITH": "COMPOSITION",
    "RELATES_TO": "COMPOSITION",
    "MAPS_TO": "COMPOSITION",
    "ISOMORPHIC_TO": "COMPOSITION",
    "DIFFERENCE": "DIFFERENCE",
    "DIFFERS_FROM": "DIFFERENCE",
    "EXACT_IDENTITY": "IDENTITY",
}


class GremlinRelationalCompilerError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _safe_token(value: str) -> str:
    out = "".join(ch if ch.isalnum() else "_" for ch in str(value).upper()).strip("_")
    if not out:
        raise GremlinRelationalCompilerError("empty canonical token")
    return out


@dataclass(frozen=True)
class RelationalNode:
    kaku: Kaku
    domain: str
    observation_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kaku, Kaku):
            raise GremlinRelationalCompilerError("RelationalNode requires Kaku")
        if not self.domain or not self.observation_ref:
            raise GremlinRelationalCompilerError("node domain and observation_ref are required")


@dataclass(frozen=True)
class RelationalEdge:
    relation_id: str
    source_id: str
    target_id: str
    relation_type: str

    def __post_init__(self) -> None:
        if not all((self.relation_id, self.source_id, self.target_id, self.relation_type)):
            raise GremlinRelationalCompilerError("relational edge fields are required")


@dataclass(frozen=True)
class RelationalIsomorphism:
    isomorphism_id: str
    invariant_id: str
    invariant_description: str
    nodes: tuple[RelationalNode, ...]
    edges: tuple[RelationalEdge, ...]
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.isomorphism_id or not self.invariant_id or not self.invariant_description:
            raise GremlinRelationalCompilerError("isomorphism and invariant metadata are required")
        if not self.nodes:
            raise GremlinRelationalCompilerError("relational isomorphism requires nodes")
        node_ids = [node.kaku.kaku_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise GremlinRelationalCompilerError("duplicate KAKU node id")
        domains = {node.domain for node in self.nodes}
        if len(domains) < 2:
            raise GremlinRelationalCompilerError("relational isomorphism requires at least two domains")
        edge_ids = [edge.relation_id for edge in self.edges]
        if len(edge_ids) != len(set(edge_ids)):
            raise GremlinRelationalCompilerError("duplicate relation id")
        allowed = set(node_ids)
        for edge in self.edges:
            if edge.source_id not in allowed or edge.target_id not in allowed:
                raise GremlinRelationalCompilerError("relation endpoint missing from isomorphism nodes")


@dataclass(frozen=True)
class RelationalCompilation:
    spec: RelationalIsomorphism
    kaku_candidates: Mapping[str, Mapping[str, Any]]
    radical_candidate: Mapping[str, Any]
    operator_candidates: tuple[Mapping[str, Any], ...]
    pnv_text: str
    source_bindings: Mapping[str, Any]
    receipt: Mapping[str, Any]


def _node_evidence(spec: RelationalIsomorphism, node: RelationalNode) -> tuple[str, ...]:
    return tuple(sorted(set((*spec.evidence_refs, f"domain:{node.domain}", f"observation:{node.observation_ref}", f"invariant:{spec.invariant_id}"))))


def _global_evidence(spec: RelationalIsomorphism) -> tuple[str, ...]:
    return tuple(sorted(set((*spec.evidence_refs, f"invariant:{spec.invariant_id}", f"isomorphism:{spec.isomorphism_id}"))))


def _build_radical(spec: RelationalIsomorphism) -> RadicalGraph:
    basis_ids = {node.kaku.vector.basis_id for node in spec.nodes}
    if len(basis_ids) != 1:
        raise GremlinRelationalCompilerError("all KAKU nodes must share one PNCS basis before RADICAL compilation")
    radical = RadicalGraph(f"GREMLIN.ISO.{_safe_token(spec.isomorphism_id)}", next(iter(basis_ids)))
    for node in sorted(spec.nodes, key=lambda x: x.kaku.kaku_id):
        radical.add_kaku(node.kaku)
    for edge in sorted(spec.edges, key=lambda x: (x.relation_id, x.source_id, x.target_id, x.relation_type)):
        radical.add_relation(Relation(edge.relation_id, edge.source_id, edge.target_id, edge.relation_type))
    return radical


def _relation_opcode(relation_type: str, overrides: Mapping[str, str] | None) -> str:
    relation = str(relation_type).upper()
    mapping = dict(DEFAULT_RELATION_OPCODE)
    if overrides:
        mapping.update({str(k).upper(): str(v).upper() for k, v in overrides.items()})
    opcode = mapping.get(relation)
    if opcode is None:
        raise GremlinRelationalCompilerError(f"relation type requires explicit opcode binding: {relation_type}")
    if opcode not in {"ORDER", "COMPOSITION", "DIFFERENCE", "IDENTITY"}:
        raise GremlinRelationalCompilerError(f"relation opcode is outside deterministic compiler subset: {opcode}")
    return opcode


def compile_relational_isomorphism(
    spec: RelationalIsomorphism,
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    relation_opcode_overrides: Mapping[str, str] | None = None,
    authoring_root: Path | str | None = None,
) -> RelationalCompilation:
    if not isinstance(spec, RelationalIsomorphism):
        raise GremlinRelationalCompilerError("RelationalIsomorphism required")
    radical = _build_radical(spec)
    kaku_candidates: dict[str, Mapping[str, Any]] = {}
    kaku_refs: dict[str, str] = {}
    source_bindings: dict[str, Any] = {}
    node_op_names: dict[str, str] = {}
    operators: list[Mapping[str, Any]] = []
    global_evidence = _global_evidence(spec)

    for index, node in enumerate(sorted(spec.nodes, key=lambda x: x.kaku.kaku_id)):
        candidate = build_kaku_candidate(
            node.kaku,
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            evidence_refs=_node_evidence(spec, node),
        )
        kaku_candidates[node.kaku.kaku_id] = candidate
        kaku_refs[node.kaku.kaku_id] = str(candidate["candidate_id"])
        if authoring_root is not None:
            persist_candidate(candidate, authoring_root=authoring_root)
        source_key = f"gremlin.iso.source.{index:03d}"
        source_bindings[source_key] = candidate
        op_name = f"ISO.NODE.{index:03d}"
        node_op_names[node.kaku.kaku_id] = op_name

    radical_candidate = build_radical_candidate(
        radical,
        kaku_candidate_ids=kaku_refs,
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        evidence_refs=global_evidence,
    )
    if authoring_root is not None:
        persist_candidate(radical_candidate, authoring_root=authoring_root)
    radical_id = str(radical_candidate["candidate_id"])

    for index, node in enumerate(sorted(spec.nodes, key=lambda x: x.kaku.kaku_id)):
        op = build_operator_candidate(
            node_op_names[node.kaku.kaku_id],
            "SOURCE",
            (f"gremlin.iso.source.{index:03d}",),
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            radical_candidate_id=radical_id,
            evidence_refs=global_evidence,
        )
        operators.append(op)
        if authoring_root is not None:
            persist_candidate(op, authoring_root=authoring_root)

    relation_op_names: list[str] = []
    relation_plan: list[dict[str, str]] = []
    for index, edge in enumerate(sorted(spec.edges, key=lambda x: (x.relation_id, x.source_id, x.target_id, x.relation_type))):
        opcode = _relation_opcode(edge.relation_type, relation_opcode_overrides)
        op_name = f"ISO.REL.{index:03d}"
        args = (node_op_names[edge.source_id], node_op_names[edge.target_id])
        op = build_operator_candidate(
            op_name,
            opcode,
            args,
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            radical_candidate_id=radical_id,
            evidence_refs=(*global_evidence, f"relation:{edge.relation_id}", f"relation_type:{edge.relation_type}"),
        )
        operators.append(op)
        relation_op_names.append(op_name)
        relation_plan.append({"relation_id": edge.relation_id, "relation_type": edge.relation_type, "opcode": opcode, "operator": op_name})
        if authoring_root is not None:
            persist_candidate(op, authoring_root=authoring_root)

    fold_inputs = relation_op_names or [node_op_names[node.kaku.kaku_id] for node in sorted(spec.nodes, key=lambda x: x.kaku.kaku_id)]
    current = fold_inputs[0]
    for index, next_name in enumerate(fold_inputs[1:]):
        fold_name = f"ISO.FOLD.{index:03d}"
        fold = build_operator_candidate(
            fold_name,
            "COMPOSITION",
            (current, next_name),
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            radical_candidate_id=radical_id,
            evidence_refs=global_evidence,
        )
        operators.append(fold)
        current = fold_name
        if authoring_root is not None:
            persist_candidate(fold, authoring_root=authoring_root)

    return_op = build_operator_candidate(
        "ISO.RETURN",
        "RETURN",
        (current,),
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        radical_candidate_id=radical_id,
        evidence_refs=global_evidence,
    )
    operators.append(return_op)
    if authoring_root is not None:
        persist_candidate(return_op, authoring_root=authoring_root)

    pnv_text = render_operator_program(tuple(operators), emits=("ISO.RETURN",), mode="READ_ONLY")
    parsed = parse_pnv(pnv_text)
    receipt_body = {
        "schema": COMPILATION_RECEIPT_SCHEMA,
        "compiler_contract": COMPILER_SCHEMA,
        "isomorphism_id": spec.isomorphism_id,
        "invariant_id": spec.invariant_id,
        "invariant_description_sha256": hashlib.sha256(spec.invariant_description.encode("utf-8")).hexdigest(),
        "domains": sorted({node.domain for node in spec.nodes}),
        "node_candidate_ids": {k: str(v["candidate_id"]) for k, v in sorted(kaku_candidates.items())},
        "radical_candidate_id": radical_id,
        "operator_candidate_ids": [str(op["candidate_id"]) for op in operators],
        "relation_plan": relation_plan,
        "pnv_source_sha256": parsed.source_sha256,
        "pnv_graph_sha256": parsed.graph_sha256,
        "epistemic": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "conformance_execution_allowed": True,
    }
    receipt = {**receipt_body, "receipt_sha256": _sha256(receipt_body)}
    return RelationalCompilation(
        spec=spec,
        kaku_candidates=kaku_candidates,
        radical_candidate=radical_candidate,
        operator_candidates=tuple(operators),
        pnv_text=pnv_text,
        source_bindings=source_bindings,
        receipt=receipt,
    )


def validate_compiled_relational_candidate(compilation: RelationalCompilation) -> NativePNVExecutionResult:
    if not isinstance(compilation, RelationalCompilation):
        raise GremlinRelationalCompilerError("RelationalCompilation required")
    result = execute_pnv(compilation.pnv_text, sources=compilation.source_bindings)
    if result.receipt["effect_boundary"]["external_effects"] is not False:
        raise GremlinRelationalCompilerError("candidate conformance execution crossed external effect boundary")
    return result


def compile_relational_isomorphism_live(
    spec: RelationalIsomorphism,
    *,
    session: GremlinPNVAuthoringSession | None = None,
    relation_opcode_overrides: Mapping[str, str] | None = None,
) -> RelationalCompilation:
    live = session or open_gremlin_pnv_authoring_live()
    compilation = compile_relational_isomorphism(
        spec,
        generation_binding=live.generation_binding,
        identity=live.identity,
        authority=live.authority,
        relation_opcode_overrides=relation_opcode_overrides,
        authoring_root=live.authoring_root,
    )
    receipt_dir = live.authoring_root / "compilation"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    target = receipt_dir / f"{compilation.receipt['receipt_sha256']}.json"
    raw = _canonical_bytes(compilation.receipt) + b"\n"
    try:
        with target.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        if target.read_bytes() != raw:
            raise GremlinRelationalCompilerError("content-addressed compilation receipt collision")
    return compilation
