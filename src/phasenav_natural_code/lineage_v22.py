from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import re
from typing import Mapping, Sequence

from .execution_v20_model import (
    DEFAULT_SOCKET,
    DEFAULT_SURFACE_ROOT,
    EXECUTABLE_INTERNAL_OPERATORS,
    EXECUTION_CONTRACT_ID as EXECUTION_CONTRACT_ID_V20,
    RECEIPT_SCHEMA as EXECUTION_RECEIPT_SCHEMA_V20,
    _DIGEST_RE,
    _compact_json,
    _sha256_json,
    _typed_id,
)

LINEAGE_CONTRACT_ID = "PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22"
LINEAGE_SCHEMA = LINEAGE_CONTRACT_ID
HIERARCHY_PATH_SCHEMA = "PNCS_HIERARCHY_LINEAGE_PATH_V0_22"
DEFINITION_RADICAL_BINDING_SCHEMA = "PNCS_DEFINITION_RADICAL_BINDING_V0_22"
RESULT_ID_SCHEMA = "PNCS_EXECUTION_RESULT_ID_V0_22"

_PREFIX = {
    "SYSTEM": "pncs:system:sha256:",
    "HIGH_ORCHESTRATOR": "pncs:high-orchestrator:sha256:",
    "LOW_ORCHESTRATOR": "pncs:low-orchestrator:sha256:",
    "SUBSYSTEM": "pncs:subsystem:sha256:",
    "DAEMON": "pncs:daemon:sha256:",
    "CLUSTER": "pncs:cluster:sha256:",
    "FILE": "pncs:file:sha256:",
    "CLASS": "pncs:class:sha256:",
    "DEFINITION": "pncs:def:sha256:",
}
_SHA_ID_RE = re.compile(r"^pncs:[a-z0-9-]+:sha256:[0-9a-f]{64}$")


class ExactInverseLineageV22Error(ValueError):
    pass


def _sha(value: object) -> str:
    return _sha256_json(value)


def _typed_level(level: str, value: object) -> str:
    prefix = _PREFIX[level]
    if not isinstance(value, str) or not value.startswith(prefix) or len(value) != len(prefix) + 64 or not _DIGEST_RE.fullmatch(value[-64:]):
        raise ExactInverseLineageV22Error(f"invalid {level} content ID")
    return value


def _sha_id(value: object, field: str, prefix: str | None = None) -> str:
    if not isinstance(value, str) or not _SHA_ID_RE.fullmatch(value):
        raise ExactInverseLineageV22Error(f"{field} must be a typed PNCS SHA-256 ID")
    if prefix is not None and not value.startswith(prefix):
        raise ExactInverseLineageV22Error(f"{field} has wrong typed-ID prefix")
    return value


def _digest(value: object, field: str) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise ExactInverseLineageV22Error(f"{field} must be lowercase 64-hex SHA-256")
    return value


def _content(registry: object, cid: str, label: str) -> object:
    fn = getattr(registry, "content", None)
    if not callable(fn):
        raise ExactInverseLineageV22Error(f"{label} registry has no content()")
    try:
        return fn(cid)
    except Exception as exc:
        raise ExactInverseLineageV22Error(f"missing {label} content: {cid}") from exc


def _kaku_payload(kaku: object) -> dict[str, object]:
    vector = getattr(kaku, "vector", None)
    values = tuple(getattr(vector, "values", ()))
    phase_raw = getattr(kaku, "phase", None)
    phase = None if phase_raw is None else list(tuple(phase_raw))
    if len(values) != 36 or (phase is not None and len(phase) != 36):
        raise ExactInverseLineageV22Error("KAKU vector/phase must be exact 36D")
    for value in values + (() if phase is None else tuple(phase)):
        if not math.isfinite(float(value)):
            raise ExactInverseLineageV22Error("KAKU contains non-finite 36D value")
    mass = getattr(kaku, "semantic_mass", None)
    polarity = getattr(kaku, "polarity", None)
    if not isinstance(mass, (int, float)) or isinstance(mass, bool) or not math.isfinite(float(mass)):
        raise ExactInverseLineageV22Error("KAKU semantic_mass must be finite")
    if not isinstance(polarity, (int, float)) or isinstance(polarity, bool) or not math.isfinite(float(polarity)):
        raise ExactInverseLineageV22Error("KAKU polarity must be finite")
    return {
        "kaku_id": getattr(kaku, "kaku_id", None),
        "basis_id": getattr(vector, "basis_id", None),
        "vector36": list(values),
        "semantic_mass": mass,
        "direction": getattr(kaku, "direction", None),
        "polarity": polarity,
        "role": getattr(kaku, "role", None),
        "phase36": phase,
    }


def _radical_payload(radical: object) -> dict[str, object]:
    rid, basis, nodes = getattr(radical, "radical_id", None), getattr(radical, "basis_id", None), getattr(radical, "nodes", None)
    if not isinstance(rid, str) or not rid or not isinstance(basis, str) or not basis or not isinstance(nodes, Mapping) or not nodes:
        raise ExactInverseLineageV22Error("RadicalGraph-compatible object required")
    payloads = []
    for kid in sorted(nodes):
        kaku = nodes[kid]
        if getattr(kaku, "kaku_id", None) != kid:
            raise ExactInverseLineageV22Error("Radical node key/KAKU ID mismatch")
        row = _kaku_payload(kaku)
        if row["basis_id"] != basis:
            raise ExactInverseLineageV22Error("Radical/KAKU basis mismatch")
        payloads.append(row)
    edges = sorted(
        ({
            "relation_id": getattr(e, "relation_id", None),
            "source_id": getattr(e, "source_id", None),
            "target_id": getattr(e, "target_id", None),
            "relation_type": getattr(e, "relation_type", None),
        } for e in getattr(radical, "edges", ())),
        key=lambda x: tuple(str(x[k]) for k in ("relation_id", "source_id", "target_id", "relation_type")),
    )
    return {"radical_id": rid, "basis_id": basis, "nodes": payloads, "edges": edges}


@dataclass(frozen=True)
class DefinitionRadicalBinding:
    definition_id: str
    radical_id: str
    radical_sha256: str
    basis_id: str
    kaku_ids: tuple[str, ...]
    operator_ids: tuple[str, ...]
    kaku_sha256s: tuple[str, ...]

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": DEFINITION_RADICAL_BINDING_SCHEMA,
            "definition_id": self.definition_id,
            "radical_id": self.radical_id,
            "radical_sha256": self.radical_sha256,
            "basis_id": self.basis_id,
            "kaku_ids": list(self.kaku_ids),
            "operator_ids": list(self.operator_ids),
            "kaku_sha256s": list(self.kaku_sha256s),
        }

    @property
    def binding_id(self) -> str:
        return _typed_id("pncs:def-radical-binding", self.payload)


def bind_definition_radical(definition: object, radical: object, kaku_ids: Sequence[str]) -> DefinitionRadicalBinding:
    verify = getattr(definition, "verify", None)
    if callable(verify):
        verify()
    did, leaves = getattr(definition, "content_id", None), tuple(getattr(definition, "leaf_path", ()))
    _typed_level("DEFINITION", did)
    if not leaves:
        raise ExactInverseLineageV22Error("Definition leaf_path is empty")
    nodes = getattr(radical, "nodes", None)
    if not isinstance(nodes, Mapping) or not nodes:
        raise ExactInverseLineageV22Error("RadicalGraph-compatible object required")
    schedule = tuple(str(x) for x in kaku_ids)
    if not schedule:
        raise ExactInverseLineageV22Error("definition->radical KAKU schedule is empty")
    missing = [x for x in schedule if x not in nodes]
    if missing:
        raise ExactInverseLineageV22Error(f"definition->radical schedule references missing KAKU: {missing}")
    if set(schedule) != set(nodes):
        raise ExactInverseLineageV22Error(f"radical contains KAKU outside exact definition schedule: {sorted(set(nodes)-set(schedule))}")
    roles = tuple(str(getattr(nodes[x], "role", "")) for x in schedule)
    if roles != leaves:
        raise ExactInverseLineageV22Error(f"KAKU operator schedule does not match Definition leaf_path: {roles} != {leaves}")
    rp = _radical_payload(radical)
    return DefinitionRadicalBinding(
        definition_id=did,
        radical_id=str(rp["radical_id"]),
        radical_sha256=_sha(rp),
        basis_id=str(rp["basis_id"]),
        kaku_ids=schedule,
        operator_ids=roles,
        kaku_sha256s=tuple(_sha(_kaku_payload(nodes[x])) for x in schedule),
    )


@dataclass(frozen=True)
class LineageNode:
    level: str
    content_id: str
    child_index: int | None

    def __post_init__(self) -> None:
        if self.level not in _PREFIX:
            raise ExactInverseLineageV22Error(f"unsupported lineage level: {self.level}")
        _typed_level(self.level, self.content_id)
        if self.level == "SYSTEM":
            if self.child_index is not None:
                raise ExactInverseLineageV22Error("SYSTEM child_index must be None")
        elif not isinstance(self.child_index, int) or self.child_index < 0:
            raise ExactInverseLineageV22Error("non-root lineage node requires child_index")

    @property
    def payload(self) -> dict[str, object]:
        return {"level": self.level, "content_id": self.content_id, "child_index": self.child_index}


@dataclass(frozen=True)
class HierarchyLineage:
    nodes: tuple[LineageNode, ...]

    def __post_init__(self) -> None:
        levels = tuple(x.level for x in self.nodes)
        if len(levels) != 8 or levels[:3] != ("SYSTEM", "HIGH_ORCHESTRATOR", "LOW_ORCHESTRATOR") or levels[3] not in {"SUBSYSTEM", "DAEMON"} or levels[4:] != ("CLUSTER", "FILE", "CLASS", "DEFINITION"):
            raise ExactInverseLineageV22Error("invalid exact hierarchy lineage sequence")

    @property
    def definition_id(self) -> str:
        return self.nodes[-1].content_id

    @property
    def payload(self) -> dict[str, object]:
        return {"schema": HIERARCHY_PATH_SCHEMA, "nodes": [x.payload for x in self.nodes]}

    @property
    def path_id(self) -> str:
        return _typed_id("pncs:hierarchy-lineage", self.payload)


@dataclass(frozen=True)
class LineageRegistries:
    definitions: object
    classes: object
    files: object
    clusters: object
    hierarchy: object


def find_definition_occurrences(system_id: str, definition_id: str, registries: LineageRegistries) -> tuple[HierarchyLineage, ...]:
    _typed_level("SYSTEM", system_id)
    _typed_level("DEFINITION", definition_id)
    _content(registries.definitions, definition_id, "definition")
    root = _content(registries.hierarchy, system_id, "hierarchy")
    if getattr(root, "level", None) != "SYSTEM":
        raise ExactInverseLineageV22Error("requested root is not SYSTEM content")
    out: list[HierarchyLineage] = []

    def high(cid: str, nodes: tuple[LineageNode, ...], ancestors: tuple[str, ...]) -> None:
        if cid in ancestors:
            raise ExactInverseLineageV22Error("hierarchy cycle detected")
        c = _content(registries.hierarchy, cid, "hierarchy")
        level, children = str(getattr(c, "level", "")), tuple(getattr(c, "child_ids", ()))
        if not children:
            raise ExactInverseLineageV22Error(f"{level} has no children")
        if level in {"SUBSYSTEM", "DAEMON"}:
            for i, cluster_id in enumerate(children):
                _typed_level("CLUSTER", cluster_id)
                cluster(cluster_id, nodes + (LineageNode("CLUSTER", cluster_id, i),))
            return
        expected = {"SYSTEM": "HIGH_ORCHESTRATOR", "HIGH_ORCHESTRATOR": "LOW_ORCHESTRATOR"}.get(level)
        for i, child_id in enumerate(children):
            child = _content(registries.hierarchy, child_id, "hierarchy")
            child_level = str(getattr(child, "level", ""))
            if level == "LOW_ORCHESTRATOR":
                if child_level not in {"SUBSYSTEM", "DAEMON"}:
                    raise ExactInverseLineageV22Error("LOW_ORCHESTRATOR child level mismatch")
            elif child_level != expected:
                raise ExactInverseLineageV22Error(f"{level} child level mismatch")
            high(child_id, nodes + (LineageNode(child_level, child_id, i),), ancestors + (cid,))

    def cluster(cid: str, nodes: tuple[LineageNode, ...]) -> None:
        files = tuple(getattr(_content(registries.clusters, cid, "cluster"), "file_ids", ()))
        if not files:
            raise ExactInverseLineageV22Error("CLUSTER has no FILE children")
        for i, file_id in enumerate(files):
            _typed_level("FILE", file_id)
            file(file_id, nodes + (LineageNode("FILE", file_id, i),))

    def file(cid: str, nodes: tuple[LineageNode, ...]) -> None:
        classes = tuple(getattr(_content(registries.files, cid, "file"), "class_ids", ()))
        if not classes:
            raise ExactInverseLineageV22Error("FILE has no CLASS children")
        for i, class_id in enumerate(classes):
            _typed_level("CLASS", class_id)
            cls(class_id, nodes + (LineageNode("CLASS", class_id, i),))

    def cls(cid: str, nodes: tuple[LineageNode, ...]) -> None:
        definitions = tuple(getattr(_content(registries.classes, cid, "class"), "definition_ids", ()))
        if not definitions:
            raise ExactInverseLineageV22Error("CLASS has no DEFINITION children")
        for i, did in enumerate(definitions):
            _typed_level("DEFINITION", did)
            if did == definition_id:
                out.append(HierarchyLineage(nodes + (LineageNode("DEFINITION", did, i),)))

    high(system_id, (LineageNode("SYSTEM", system_id, None),), ())
    return tuple(out)


def select_exact_occurrence(occurrences: Sequence[HierarchyLineage], selected: HierarchyLineage | None = None) -> HierarchyLineage:
    rows = tuple(occurrences)
    if not rows:
        raise ExactInverseLineageV22Error("execution Definition is not contained by requested SYSTEM")
    if selected is None:
        if len(rows) != 1:
            raise ExactInverseLineageV22Error(f"ambiguous inverse lineage: {len(rows)} exact hierarchy occurrences")
        return rows[0]
    if sum(x == selected for x in rows) != 1:
        raise ExactInverseLineageV22Error("explicit hierarchy occurrence is not an exact candidate")
    return selected


def _validate_execution_result(result: object) -> tuple[str, str, dict[str, object]]:
    receipt, final_state = getattr(result, "receipt", None), getattr(result, "final_state", None)
    if not isinstance(receipt, Mapping) or final_state is None:
        raise ExactInverseLineageV22Error("NativeExecutionResult-compatible object required")
    if receipt.get("schema") != EXECUTION_RECEIPT_SCHEMA_V20 or receipt.get("execution_contract_id") != EXECUTION_CONTRACT_ID_V20:
        raise ExactInverseLineageV22Error("execution receipt schema/contract mismatch")
    receipt_sha = _digest(receipt.get("receipt_sha256"), "execution receipt digest")
    body = dict(receipt); body.pop("receipt_sha256", None)
    if _sha(body) != receipt_sha:
        raise ExactInverseLineageV22Error("execution receipt digest mismatch")
    program = receipt.get("program")
    if not isinstance(program, Mapping):
        raise ExactInverseLineageV22Error("execution receipt missing program provenance")
    did = _typed_level("DEFINITION", program.get("content_id"))
    _sha_id(program.get("realization_id"), "realization_id", "pncs:realization36:sha256:")
    _sha_id(program.get("realization_binding_id"), "realization_binding_id", "pncs:binding36:sha256:")
    _sha_id(program.get("mass_binding_id"), "mass_binding_id", "pncs:mass-binding:sha256:")
    _digest(program.get("phase36_sha256"), "phase36_sha256")
    mass = program.get("semantic_mass")
    if not isinstance(mass, (int, float)) or isinstance(mass, bool) or not math.isfinite(float(mass)):
        raise ExactInverseLineageV22Error("program semantic_mass must be finite")
    if getattr(final_state, "content_id", None) != did:
        raise ExactInverseLineageV22Error("final Sigma/program Definition mismatch")
    initial_id = _sha_id(receipt.get("initial_sigma_id"), "initial Sigma", "pncs:sigma:sha256:")
    final_id = _sha_id(getattr(final_state, "state_id", None), "final Sigma", "pncs:sigma:sha256:")
    if receipt.get("final_sigma_id") != final_id:
        raise ExactInverseLineageV22Error("execution receipt/final Sigma mismatch")
    steps = receipt.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ExactInverseLineageV22Error("execution receipt must contain a non-empty KAKU transition trace")
    before = initial_id
    for index, step in enumerate(steps, 1):
        if not isinstance(step, Mapping) or step.get("index") != index or step.get("operator_id") not in EXECUTABLE_INTERNAL_OPERATORS:
            raise ExactInverseLineageV22Error("invalid execution step index/operator")
        _digest(step.get("operator_vector_sha256"), "operator vector digest")
        if _sha_id(step.get("before_sigma_id"), "step before Sigma", "pncs:sigma:sha256:") != before:
            raise ExactInverseLineageV22Error("execution Sigma transition chain is discontinuous")
        before = _sha_id(step.get("after_sigma_id"), "step after Sigma", "pncs:sigma:sha256:")
    if before != final_id:
        raise ExactInverseLineageV22Error("execution transition trace does not terminate at final Sigma")
    result_payload = receipt.get("result")
    if not isinstance(result_payload, Mapping) or result_payload.get("kind") != "INTERNAL_TRANSFORM":
        raise ExactInverseLineageV22Error("v0.22 accepts only INTERNAL_TRANSFORM results")
    target = getattr(result, "target", None)
    if result_payload.get("control_location") != target or getattr(final_state, "control_location", None) != target:
        raise ExactInverseLineageV22Error("execution result/control-location mismatch")
    admission = receipt.get("admission")
    if not isinstance(admission, Mapping) or admission.get("branch_truth_state") != getattr(result, "branch_truth_state", None):
        raise ExactInverseLineageV22Error("execution admission/result truth-state mismatch")
    live = receipt.get("live_surface")
    if not isinstance(live, Mapping) or live.get("root") != str(DEFAULT_SURFACE_ROOT):
        raise ExactInverseLineageV22Error("execution receipt is not bound to canonical /dev/shm/ciel_noema surface")
    for field in ("phi_sha256", "aux_phi_sha256", "aux_feedback_phi_sha256", "operator_registry_sha256", "tether_receipt_sha256"):
        _digest(live.get(field), f"live_surface.{field}")
    if receipt.get("external_effects") is not False or receipt.get("semantic_mass_is_authorization") is not False or receipt.get("free_form_nl_execution") is not False or receipt.get("deterministic_fields_only") is not True:
        raise ExactInverseLineageV22Error("execution receipt violates v0.20 authority/determinism boundary")
    identity = {
        "schema": RESULT_ID_SCHEMA,
        "execution_receipt_sha256": receipt_sha,
        "final_sigma_id": final_id,
        "definition_id": did,
        "branch_truth_state": getattr(result, "branch_truth_state", None),
        "result": dict(result_payload),
    }
    return did, _typed_id("pncs:result", identity), identity


@dataclass(frozen=True)
class ExactInverseLineage:
    result_id: str
    execution_receipt_sha256: str
    result_identity_payload: Mapping[str, object]
    hierarchy: HierarchyLineage
    definition_radical: DefinitionRadicalBinding

    @property
    def inverse_chain(self) -> list[dict[str, object]]:
        rows = [{"level": "RESULT", "id": self.result_id}]
        rows += [{"level": n.level, "id": n.content_id, "child_index": n.child_index} for n in self.hierarchy.nodes]
        rows += [
            {"level": "RADICAL", "id": self.definition_radical.radical_id, "sha256": self.definition_radical.radical_sha256},
            {"level": "KAKU", "ids": list(self.definition_radical.kaku_ids), "operators": list(self.definition_radical.operator_ids), "sha256s": list(self.definition_radical.kaku_sha256s)},
        ]
        return rows

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": LINEAGE_SCHEMA,
            "lineage_contract_id": LINEAGE_CONTRACT_ID,
            "result_id": self.result_id,
            "execution_receipt_sha256": self.execution_receipt_sha256,
            "result_identity": dict(self.result_identity_payload),
            "hierarchy_path_id": self.hierarchy.path_id,
            "hierarchy": self.hierarchy.payload,
            "definition_radical_binding_id": self.definition_radical.binding_id,
            "definition_radical": self.definition_radical.payload,
            "inverse_chain": self.inverse_chain,
            "runtime_location_is_semantic_authority": False,
            "aliases_are_semantic_authority": False,
            "ambiguity_policy": "FAIL_CLOSED_UNLESS_EXACT_OCCURRENCE_SELECTED",
            "deterministic_fields_only": True,
        }

    @property
    def lineage_id(self) -> str:
        return _typed_id("pncs:lineage", self.payload)

    @property
    def receipt(self) -> dict[str, object]:
        return {**self.payload, "lineage_id": self.lineage_id}


def resolve_exact_inverse_lineage(execution_result: object, system_content_id: str, registries: LineageRegistries, radical: object, kaku_ids: Sequence[str], *, selected_occurrence: HierarchyLineage | None = None) -> ExactInverseLineage:
    did, result_id, identity = _validate_execution_result(execution_result)
    definition = _content(registries.definitions, did, "definition")
    receipt = getattr(execution_result, "receipt")
    if tuple(receipt.get("canonical_leaf_path", ())) != tuple(getattr(definition, "leaf_path", ())):
        raise ExactInverseLineageV22Error("execution receipt leaf path/Definition mismatch")
    graph = getattr(definition, "canonical_graph", None)
    if graph is not None and receipt.get("canonical_graph_sha256") != _sha(graph):
        raise ExactInverseLineageV22Error("execution receipt canonical graph/Definition mismatch")
    binding = bind_definition_radical(definition, radical, kaku_ids)
    hierarchy = select_exact_occurrence(find_definition_occurrences(system_content_id, did, registries), selected_occurrence)
    if hierarchy.definition_id != binding.definition_id:
        raise ExactInverseLineageV22Error("hierarchy Definition/radical binding mismatch")
    return ExactInverseLineage(result_id, str(receipt["receipt_sha256"]), identity, hierarchy, binding)


def persist_exact_inverse_lineage(lineage: ExactInverseLineage, *, surface_root: Path | str = DEFAULT_SURFACE_ROOT, socket_path: Path | str = DEFAULT_SOCKET, max_heartbeat_age_s: float = 2.0) -> str:
    root = Path(surface_root)
    if root != DEFAULT_SURFACE_ROOT:
        raise ExactInverseLineageV22Error("v0.22 operational lineage persistence is fixed to /dev/shm/ciel_noema")
    from .execution_v20_live import load_live_surface
    live = load_live_surface(root, socket_path=socket_path, require_socket=True, max_heartbeat_age_s=max_heartbeat_age_s)
    if live.root != str(DEFAULT_SURFACE_ROOT):
        raise ExactInverseLineageV22Error("live surface root mismatch")
    path = root / "pncs/v0.22/lineage" / f"{lineage.lineage_id.rsplit(':',1)[-1]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    raw = (_compact_json(lineage.receipt) + "\n").encode("utf-8")
    with tmp.open("wb") as fh:
        fh.write(raw); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)
    return str(path)
