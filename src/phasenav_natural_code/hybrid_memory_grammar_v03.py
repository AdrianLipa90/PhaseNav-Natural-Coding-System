"""PNCS Hybrid Memory Grammar v0.3.

Memory-Ontology-informed extension of PNCS Hybrid Grammar v0.2.

Core separation:
- active program state is not memory;
- memory is history-bearing transition structure;
- memory ontology is not representation;
- representation is not physical substrate;
- direct/reconstructive access is distinct from implicit guidance.

The compiler remains fail-closed and performs no persistent write or external
actuation. Memory mutations in this module are semantic transition requests;
durable persistence still requires the v0.2 PERSIST capability boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
import shlex
from typing import Mapping

from .hybrid_grammar_v02 import (
    CompiledHybridProgram,
    HybridGrammarError,
    compile_hybrid_program,
)

GRAMMAR_SCHEMA = "PNCS_HYBRID_MEMORY_GRAMMAR_V0_3"
IR_SCHEMA = "PNCS_HYBRID_IR_V0_3"
MEMORY_SCHEMA = "PNCS_MEMORY_OBJECT_V0_3"
REPRESENTATION_SCHEMA = "PNCS_MEMORY_REPRESENTATION_PROFILE_V0_3"
OP_SCHEMA = "PNCS_MEMORY_OPERATION_V0_3"

_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")

RETAINED_OBJECTS = frozenset(
    {"STATE", "RELATION", "PATH", "TOPOLOGY", "OPERATOR", "BOUNDARY"}
)
PERSISTENCE = frozenset(
    {"EPHEMERAL", "TRANSIENT", "PERSISTENT", "STRUCTURAL", "EFFECTIVELY_INVARIANT"}
)
ACCESS_MODES = frozenset({"DIRECT", "RECONSTRUCTIVE", "IMPLICIT", "LATENT"})
PLASTICITY = frozenset(
    {"VOLATILE", "ADAPTIVE", "CONSOLIDATING", "APPEND_ONLY", "SELF_MODIFYING"}
)
EFFECTS = frozenset({"BIAS", "CONSTRAINT", "ATTRACTOR", "ROUTING", "GENERATIVE"})
MEMORY_EPISTEMIC = frozenset(
    {
        "FORMAL_EXAMPLE",
        "HYPOTHESIS",
        "SYNTHETIC_EVIDENCE",
        "EMPIRICAL_EVIDENCE",
        "VALIDATED_DOMAIN_MODEL",
    }
)
REPRESENTATION_FAMILIES = frozenset(
    {"QUANTUM_NATIVE", "BINARY", "HYBRID", "SUBSTRATE_NEUTRAL"}
)
REPRESENTATION_EVIDENCE = frozenset(
    {
        "FORMAL_ONLY",
        "PARITY",
        "CLASSICAL_COMPRESSION",
        "CANDIDATE_Q_NATIVE_ADVANTAGE",
        "EMPIRICAL_Q_NATIVE_ADVANTAGE",
        "THEORETICAL_SEPARATION",
        "PHYSICAL_QUANTUM_NECESSITY",
    }
)
COST_METRICS = frozenset(
    {
        "STORAGE",
        "COMPILE_TIME",
        "UPDATE_TIME",
        "QUERY_TIME",
        "SAMPLE_COUNT",
        "SEQUENTIAL_DEPTH",
    }
)
COUPLING_MODES = frozenset(
    {"CONSOLIDATE", "REACTIVATE", "REINFORCE", "INHIBIT", "GATE", "ROUTE"}
)
PROVENANCE_CLASSES = frozenset(
    {"RECALLED", "RECONSTRUCTED", "INFERRED", "IMAGINED"}
)
MEMORY_VALUE_TYPES = frozenset(
    {
        "STATE",
        "RELATION",
        "PATH",
        "TOPOLOGY",
        "OPERATOR",
        "BOUNDARY",
        "TRACE",
        "EVENT",
        "GRAPH",
        "TEXT",
        "DOCUMENT",
        "JSON",
        "BYTES",
        "REAL",
        "INTEGER",
        "BOOLEAN",
        "ANY",
    }
)


class HybridMemoryGrammarError(ValueError):
    pass


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _id(value: str, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise HybridMemoryGrammarError(f"{field} must be a PNCS identifier")
    return value


def _tokens(line: str, line_no: int) -> list[str]:
    try:
        return shlex.split(line)
    except ValueError as exc:
        raise HybridMemoryGrammarError(f"line {line_no}: {exc}") from exc


def _split_sections(
    parts: list[str],
    start: int,
    keys: tuple[str, ...],
    line_no: int,
) -> dict[str, list[str]]:
    positions: list[tuple[int, str]] = []
    keyset = set(keys)
    for i in range(start, len(parts)):
        upper = parts[i].upper()
        if upper in keyset:
            positions.append((i, upper))
    if not positions:
        raise HybridMemoryGrammarError(f"line {line_no}: missing required sections")
    if positions[0][0] != start:
        raise HybridMemoryGrammarError(f"line {line_no}: unexpected token before {positions[0][1]}")
    if len({key for _, key in positions}) != len(positions):
        raise HybridMemoryGrammarError(f"line {line_no}: duplicate section keyword")
    out: dict[str, list[str]] = {}
    for idx, (pos, key) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(parts)
        values = parts[pos + 1 : end]
        if not values:
            raise HybridMemoryGrammarError(f"line {line_no}: {key} requires value(s)")
        out[key] = values
    return out


def _enum_values(
    raw: list[str],
    allowed: frozenset[str],
    field: str,
    line_no: int,
) -> tuple[str, ...]:
    values = tuple(x.upper() for x in raw)
    unknown = [x for x in values if x not in allowed]
    if unknown:
        raise HybridMemoryGrammarError(
            f"line {line_no}: unsupported {field} value(s): {unknown}"
        )
    if len(set(values)) != len(values):
        raise HybridMemoryGrammarError(f"line {line_no}: duplicate {field} value")
    return values


@dataclass(frozen=True)
class MemoryObject:
    memory_id: str
    retained_objects: tuple[str, ...]
    persistence: str
    access: tuple[str, ...]
    plasticity: tuple[str, ...]
    effects: tuple[str, ...]
    epistemic_status: str
    substrate: str = "unspecified"

    def __post_init__(self) -> None:
        object.__setattr__(self, "memory_id", _id(self.memory_id, "memory id"))
        if not self.retained_objects:
            raise HybridMemoryGrammarError("memory requires retained object(s)")
        if any(x not in RETAINED_OBJECTS for x in self.retained_objects):
            raise HybridMemoryGrammarError("invalid retained object")
        if self.persistence not in PERSISTENCE:
            raise HybridMemoryGrammarError("invalid persistence class")
        if not self.access or any(x not in ACCESS_MODES for x in self.access):
            raise HybridMemoryGrammarError("invalid access mode")
        if not self.plasticity or any(x not in PLASTICITY for x in self.plasticity):
            raise HybridMemoryGrammarError("invalid plasticity mode")
        if not self.effects or any(x not in EFFECTS for x in self.effects):
            raise HybridMemoryGrammarError("invalid memory effect")
        if self.epistemic_status not in MEMORY_EPISTEMIC:
            raise HybridMemoryGrammarError("invalid memory epistemic status")

    def to_dict(self) -> dict:
        return {
            "schema": MEMORY_SCHEMA,
            "ontology_source": "Memory-Ontology/v0.1",
            "memory_id": self.memory_id,
            "retained_objects": [x.lower() for x in self.retained_objects],
            "persistence": self.persistence.lower(),
            "access": [x.lower() for x in self.access],
            "plasticity": [x.lower() for x in self.plasticity],
            "effects": [x.lower() for x in self.effects],
            "substrate": self.substrate,
            "epistemic_status": self.epistemic_status.lower(),
        }


@dataclass(frozen=True)
class RepresentationProfile:
    memory_id: str
    family: str
    epsilon: float
    horizon: int | str
    observable_contract: str
    cost_metrics: tuple[str, ...]
    evidence_status: str
    distance: str | None = None
    physical_substrate_claim: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "memory_id", _id(self.memory_id, "memory id"))
        if self.family not in REPRESENTATION_FAMILIES:
            raise HybridMemoryGrammarError("invalid representation family")
        eps = float(self.epsilon)
        if not math.isfinite(eps) or eps < 0:
            raise HybridMemoryGrammarError("epsilon must be finite and non-negative")
        object.__setattr__(self, "epsilon", eps)
        if isinstance(self.horizon, int):
            if self.horizon < 1:
                raise HybridMemoryGrammarError("horizon must be positive")
        elif not isinstance(self.horizon, str) or not self.horizon:
            raise HybridMemoryGrammarError("invalid representation horizon")
        _id(self.observable_contract, "observable contract")
        if not self.cost_metrics or any(x not in COST_METRICS for x in self.cost_metrics):
            raise HybridMemoryGrammarError("invalid representation cost metrics")
        if self.evidence_status not in REPRESENTATION_EVIDENCE:
            raise HybridMemoryGrammarError("invalid representation evidence status")
        if self.physical_substrate_claim:
            raise HybridMemoryGrammarError(
                "v0.3 cannot assert physical quantum substrate necessity"
            )
        if self.distance is not None:
            _id(self.distance, "distance contract")

    def to_dict(self) -> dict:
        contract = {
            "epsilon": self.epsilon,
            "horizon": self.horizon,
            "observable_contract": self.observable_contract,
        }
        if self.distance is not None:
            contract["distance"] = self.distance
        return {
            "schema": REPRESENTATION_SCHEMA,
            "memory_id": self.memory_id,
            "representation_family": self.family.lower(),
            "physical_substrate_claim": False,
            "equivalence_contract": contract,
            "cost_metrics": [x.lower() for x in self.cost_metrics],
            "evidence_status": self.evidence_status.lower(),
        }


@dataclass(frozen=True)
class MemoryOperation:
    op_id: str
    kind: str
    task_id: str
    attributes: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "op_id", _id(self.op_id, "memory operation id"))
        object.__setattr__(self, "kind", _id(self.kind, "memory operation kind").upper())
        object.__setattr__(self, "task_id", _id(self.task_id, "task id"))

    def to_dict(self) -> dict:
        return {
            "schema": OP_SCHEMA,
            "op_id": self.op_id,
            "kind": self.kind,
            "task_id": self.task_id,
            "attributes": dict(self.attributes),
            "persistent_write_performed": False,
            "external_actuation_performed": False,
        }


@dataclass(frozen=True)
class RecallBinding:
    symbol: str
    type_name: str
    memory_id: str
    access_mode: str
    provenance_class: str
    task_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _id(self.symbol, "recall symbol"))
        t = self.type_name.upper()
        if t not in MEMORY_VALUE_TYPES:
            raise HybridMemoryGrammarError(f"unsupported memory value type: {t}")
        object.__setattr__(self, "type_name", t)
        object.__setattr__(self, "memory_id", _id(self.memory_id, "memory id"))
        if self.access_mode not in {"DIRECT", "RECONSTRUCTIVE"}:
            raise HybridMemoryGrammarError(
                "RECALL supports DIRECT or RECONSTRUCTIVE access; use GUIDE for implicit memory"
            )
        expected = "RECALLED" if self.access_mode == "DIRECT" else "RECONSTRUCTED"
        if self.provenance_class != expected:
            raise HybridMemoryGrammarError(
                f"{self.access_mode} recall must carry provenance {expected}"
            )
        object.__setattr__(self, "task_id", _id(self.task_id, "task id"))


@dataclass(frozen=True)
class CompiledHybridMemoryProgram:
    source: str
    base_program: CompiledHybridProgram
    memories: tuple[MemoryObject, ...]
    representations: tuple[RepresentationProfile, ...]
    operations: tuple[MemoryOperation, ...]
    recalls: tuple[RecallBinding, ...]

    @property
    def source_sha256(self) -> str:
        return hashlib.sha256(self.source.encode("utf-8")).hexdigest()

    def to_ir(self) -> dict:
        ir = self.base_program.to_ir()
        ir = json.loads(json.dumps(ir))

        recall_map = {r.symbol: r for r in self.recalls}
        for symbol in ir.get("symbols", []):
            binding = recall_map.get(symbol.get("name"))
            if binding is not None:
                symbol["type"] = binding.type_name

        for node in ir.get("nodes", []):
            node_id = node.get("node_id", "")
            if not node_id.startswith("input."):
                continue
            name = node_id[len("input.") :]
            binding = recall_map.get(name)
            if binding is None:
                continue
            node["kind"] = "MEMORY_ACCESS"
            node["execution_class"] = "MEMORY_RECALL"
            node["output_type"] = binding.type_name
            node["attributes"] = {
                "memory_id": binding.memory_id,
                "access_mode": binding.access_mode.lower(),
                "provenance_class": binding.provenance_class,
                "history_bearing_structure": True,
            }

        ir["schema"] = IR_SCHEMA
        ir["base_hybrid_schema"] = "PNCS_HYBRID_IR_V0_2"
        ir["memory_model"] = {
            "ontology_source": "AdrianLipa90/Memory-Ontology@memory-ontology/v0.1",
            "law": {
                "active_state_distinct_from_memory": True,
                "memory_definition": (
                    "persistent history-dependent modification of transition structure "
                    "that changes future reachable trajectories"
                ),
                "ontological_chain": ["EVENT", "TRACE", "PATH", "STRUCTURE", "LAW"],
                "representation_is_orthogonal": True,
            },
            "objects": [x.to_dict() for x in self.memories],
            "representations": [x.to_dict() for x in self.representations],
            "operations": [x.to_dict() for x in self.operations],
            "accesses": [
                {
                    "symbol": r.symbol,
                    "type": r.type_name,
                    "memory_id": r.memory_id,
                    "access_mode": r.access_mode.lower(),
                    "provenance_class": r.provenance_class,
                    "task_id": r.task_id,
                }
                for r in self.recalls
            ],
            "runtime_contract": {
                "memory_mutation_is_semantic_transition_request": True,
                "durable_persistence_requires_explicit_PERSIST": True,
                "procedural_memory_is_path_topology_operator_structure": True,
                "implicit_memory_uses_GUIDE_not_RECALL": True,
                "no_storage_equals_memory_shortcut": True,
            },
        }
        ir["compiler_policy"]["memory_native_semantics"] = True
        ir["compiler_policy"]["memory_representation_separated_from_ontology"] = True
        return ir

    @property
    def ir_sha256(self) -> str:
        return _sha256(self.to_ir())

    def to_dict(self) -> dict:
        return {
            "schema": GRAMMAR_SCHEMA,
            "program_id": self.base_program.program_id,
            "source_sha256": self.source_sha256,
            "ir_sha256": self.ir_sha256,
            "ir": self.to_ir(),
        }


def _parse_memory(parts: list[str], line_no: int) -> MemoryObject:
    if len(parts) < 14:
        raise HybridMemoryGrammarError(f"line {line_no}: incomplete MEMORY declaration")
    memory_id = _id(parts[1], "memory id")
    sections = _split_sections(
        parts,
        2,
        ("RETAINS", "PERSISTENCE", "ACCESS", "PLASTICITY", "EFFECT", "EPISTEMIC", "SUBSTRATE"),
        line_no,
    )
    required = {"RETAINS", "PERSISTENCE", "ACCESS", "PLASTICITY", "EFFECT", "EPISTEMIC"}
    missing = sorted(required - set(sections))
    if missing:
        raise HybridMemoryGrammarError(f"line {line_no}: missing MEMORY sections {missing}")
    retained = _enum_values(sections["RETAINS"], RETAINED_OBJECTS, "retained object", line_no)
    persistence = _enum_values(
        sections["PERSISTENCE"], PERSISTENCE, "persistence", line_no
    )
    if len(persistence) != 1:
        raise HybridMemoryGrammarError(f"line {line_no}: PERSISTENCE takes one value")
    access = _enum_values(sections["ACCESS"], ACCESS_MODES, "access", line_no)
    plasticity = _enum_values(sections["PLASTICITY"], PLASTICITY, "plasticity", line_no)
    effects = _enum_values(sections["EFFECT"], EFFECTS, "effect", line_no)
    epistemic = _enum_values(
        sections["EPISTEMIC"], MEMORY_EPISTEMIC, "epistemic", line_no
    )
    if len(epistemic) != 1:
        raise HybridMemoryGrammarError(f"line {line_no}: EPISTEMIC takes one value")
    substrate = "unspecified"
    if "SUBSTRATE" in sections:
        if len(sections["SUBSTRATE"]) != 1:
            raise HybridMemoryGrammarError(f"line {line_no}: SUBSTRATE takes one value")
        substrate = sections["SUBSTRATE"][0]
    return MemoryObject(
        memory_id=memory_id,
        retained_objects=retained,
        persistence=persistence[0],
        access=access,
        plasticity=plasticity,
        effects=effects,
        epistemic_status=epistemic[0],
        substrate=substrate,
    )


def _parse_representation(
    parts: list[str],
    line_no: int,
    memories: dict[str, MemoryObject],
) -> RepresentationProfile:
    if len(parts) < 14 or parts[2].upper() != "AS":
        raise HybridMemoryGrammarError(f"line {line_no}: malformed REPRESENT")
    memory_id = _id(parts[1], "memory id")
    if memory_id not in memories:
        raise HybridMemoryGrammarError(f"line {line_no}: unknown memory {memory_id}")
    family = parts[3].upper()
    if family not in REPRESENTATION_FAMILIES:
        raise HybridMemoryGrammarError(f"line {line_no}: unsupported representation family")
    sections = _split_sections(
        parts,
        4,
        ("EPSILON", "HORIZON", "OBSERVABLE", "COST", "EVIDENCE", "DISTANCE", "PHYSICAL_QUANTUM"),
        line_no,
    )
    required = {"EPSILON", "HORIZON", "OBSERVABLE", "COST", "EVIDENCE"}
    missing = sorted(required - set(sections))
    if missing:
        raise HybridMemoryGrammarError(f"line {line_no}: missing REPRESENT sections {missing}")

    if any(len(sections[k]) != 1 for k in ("EPSILON", "HORIZON", "OBSERVABLE", "EVIDENCE")):
        raise HybridMemoryGrammarError(f"line {line_no}: scalar REPRESENT section has wrong arity")
    try:
        epsilon = float(sections["EPSILON"][0])
    except ValueError as exc:
        raise HybridMemoryGrammarError(f"line {line_no}: invalid EPSILON") from exc
    hraw = sections["HORIZON"][0]
    horizon: int | str = int(hraw) if hraw.isdigit() else hraw
    observable = _id(sections["OBSERVABLE"][0], "observable contract")
    cost = _enum_values(sections["COST"], COST_METRICS, "cost metric", line_no)
    evidence = _enum_values(
        sections["EVIDENCE"], REPRESENTATION_EVIDENCE, "representation evidence", line_no
    )
    if len(evidence) != 1:
        raise HybridMemoryGrammarError(f"line {line_no}: EVIDENCE takes one value")
    distance = None
    if "DISTANCE" in sections:
        if len(sections["DISTANCE"]) != 1:
            raise HybridMemoryGrammarError(f"line {line_no}: DISTANCE takes one value")
        distance = _id(sections["DISTANCE"][0], "distance")
    physical = False
    if "PHYSICAL_QUANTUM" in sections:
        if len(sections["PHYSICAL_QUANTUM"]) != 1:
            raise HybridMemoryGrammarError(
                f"line {line_no}: PHYSICAL_QUANTUM takes TRUE/FALSE"
            )
        flag = sections["PHYSICAL_QUANTUM"][0].upper()
        if flag not in {"TRUE", "FALSE"}:
            raise HybridMemoryGrammarError(
                f"line {line_no}: PHYSICAL_QUANTUM takes TRUE/FALSE"
            )
        physical = flag == "TRUE"

    return RepresentationProfile(
        memory_id=memory_id,
        family=family,
        epsilon=epsilon,
        horizon=horizon,
        observable_contract=observable,
        cost_metrics=cost,
        evidence_status=evidence[0],
        distance=distance,
        physical_substrate_claim=physical,
    )


def compile_hybrid_memory_program(source: str) -> CompiledHybridMemoryProgram:
    if not isinstance(source, str) or not source.strip():
        raise HybridMemoryGrammarError("hybrid-memory source must be non-empty text")

    base_lines: list[str] = []
    memories: dict[str, MemoryObject] = {}
    representations: dict[str, RepresentationProfile] = {}
    operations: list[MemoryOperation] = []
    recalls: list[RecallBinding] = []
    events: set[str] = set()
    routes: dict[str, tuple[str, ...]] = {}
    laws: dict[str, tuple[str, str]] = {}
    current_task = "root"
    in_quantum = False
    returned = False

    for line_no, raw in enumerate(source.splitlines(), start=1):
        stripped = raw.split("#", 1)[0].strip()
        if not stripped:
            continue
        parts = _tokens(stripped, line_no)
        head = parts[0].upper()

        if in_quantum:
            base_lines.append(stripped)
            if head == "QUANTUM" and len(parts) == 2 and parts[1].upper() == "END":
                in_quantum = False
            continue

        if returned:
            raise HybridMemoryGrammarError(
                f"line {line_no}: RETURN must remain the final top-level statement"
            )

        if head == "QUANTUM":
            base_lines.append(stripped)
            if len(parts) >= 2 and parts[1].upper() == "BEGIN":
                in_quantum = True
            continue

        if head == "TASK":
            if len(parts) != 2:
                raise HybridMemoryGrammarError(f"line {line_no}: TASK requires one id")
            current_task = _id(parts[1], "task")
            base_lines.append(stripped)
            continue

        if head == "MEMORY":
            obj = _parse_memory(parts, line_no)
            if obj.memory_id in memories:
                raise HybridMemoryGrammarError(
                    f"line {line_no}: duplicate memory {obj.memory_id}"
                )
            memories[obj.memory_id] = obj
            continue

        if head == "REPRESENT":
            profile = _parse_representation(parts, line_no, memories)
            if profile.memory_id in representations:
                raise HybridMemoryGrammarError(
                    f"line {line_no}: duplicate representation for {profile.memory_id}"
                )
            representations[profile.memory_id] = profile
            continue

        if head == "EVENT":
            if len(parts) != 4 or parts[2].upper() != "FROM":
                raise HybridMemoryGrammarError(
                    f"line {line_no}: EVENT syntax is EVENT id FROM symbol"
                )
            event_id = _id(parts[1], "event id")
            if event_id in events:
                raise HybridMemoryGrammarError(f"line {line_no}: duplicate event {event_id}")
            events.add(event_id)
            operations.append(
                MemoryOperation(
                    op_id=f"event.{event_id}",
                    kind="EVENT",
                    task_id=current_task,
                    attributes={"event_id": event_id, "source_symbol": _id(parts[3], "event source")},
                )
            )
            continue

        if head == "LAW":
            if (
                len(parts) != 6
                or parts[2].upper() != "FOR"
                or parts[4].upper() != "USING"
            ):
                raise HybridMemoryGrammarError(
                    f"line {line_no}: LAW syntax is LAW id FOR memory USING operator"
                )
            law_id = _id(parts[1], "law id")
            mem = _id(parts[3], "memory id")
            if mem not in memories:
                raise HybridMemoryGrammarError(f"line {line_no}: unknown memory {mem}")
            operator = _id(parts[5], "law operator")
            if law_id in laws:
                raise HybridMemoryGrammarError(f"line {line_no}: duplicate law {law_id}")
            laws[law_id] = (mem, operator)
            operations.append(
                MemoryOperation(
                    op_id=f"law.{law_id}",
                    kind="LAW",
                    task_id=current_task,
                    attributes={"law_id": law_id, "memory_id": mem, "operator": operator},
                )
            )
            continue

        if head == "TRACE":
            if len(parts) not in {6, 8} or parts[2].upper() != "FROM" or parts[4].upper() != "INTO":
                raise HybridMemoryGrammarError(
                    f"line {line_no}: TRACE syntax is TRACE id FROM event INTO memory [LAW law]"
                )
            trace_id = _id(parts[1], "trace id")
            event = _id(parts[3], "event id")
            mem = _id(parts[5], "memory id")
            if event not in events:
                raise HybridMemoryGrammarError(f"line {line_no}: unknown event {event}")
            if mem not in memories:
                raise HybridMemoryGrammarError(f"line {line_no}: unknown memory {mem}")
            attrs: dict[str, object] = {
                "trace_id": trace_id,
                "event_id": event,
                "memory_id": mem,
                "history_encoding": True,
                "memory_update_requested": True,
            }
            if len(parts) == 8:
                if parts[6].upper() != "LAW":
                    raise HybridMemoryGrammarError(f"line {line_no}: expected LAW")
                law = _id(parts[7], "law id")
                if law not in laws or laws[law][0] != mem:
                    raise HybridMemoryGrammarError(
                        f"line {line_no}: law {law} is not bound to memory {mem}"
                    )
                attrs["law_id"] = law
            operations.append(
                MemoryOperation(
                    op_id=f"trace.{trace_id}",
                    kind="TRACE",
                    task_id=current_task,
                    attributes=attrs,
                )
            )
            continue

        if head == "ROUTE":
            if len(parts) < 5 or parts[2] != ":":
                raise HybridMemoryGrammarError(
                    f"line {line_no}: ROUTE syntax is ROUTE id : node1 node2 ..."
                )
            route_id = _id(parts[1], "route id")
            if route_id in routes:
                raise HybridMemoryGrammarError(f"line {line_no}: duplicate route {route_id}")
            members = tuple(_id(x, "route node") for x in parts[3:])
            if len(members) < 2:
                raise HybridMemoryGrammarError(f"line {line_no}: ROUTE needs at least two nodes")
            routes[route_id] = members
            operations.append(
                MemoryOperation(
                    op_id=f"route.{route_id}",
                    kind="PATH",
                    task_id=current_task,
                    attributes={"route_id": route_id, "node_path": list(members)},
                )
            )
            continue

        if head == "REINFORCE":
            if (
                len(parts) not in {6, 8}
                or parts[2].upper() != "INTO"
                or parts[4].upper() != "MODE"
            ):
                raise HybridMemoryGrammarError(
                    f"line {line_no}: REINFORCE syntax is "
                    "REINFORCE route INTO memory MODE plasticity [LAW law]"
                )
            route = _id(parts[1], "route id")
            mem = _id(parts[3], "memory id")
            mode = parts[5].upper()
            if route not in routes:
                raise HybridMemoryGrammarError(f"line {line_no}: unknown route {route}")
            if mem not in memories:
                raise HybridMemoryGrammarError(f"line {line_no}: unknown memory {mem}")
            obj = memories[mem]
            if "PATH" not in obj.retained_objects:
                raise HybridMemoryGrammarError(
                    f"line {line_no}: reinforced procedural memory must retain PATH"
                )
            if mode not in PLASTICITY or mode not in obj.plasticity:
                raise HybridMemoryGrammarError(
                    f"line {line_no}: reinforcement mode must be declared in memory plasticity"
                )
            attrs = {
                "route_id": route,
                "memory_id": mem,
                "plasticity_mode": mode.lower(),
                "path_weight_update_requested": True,
                "metastable_not_immutable": True,
            }
            if len(parts) == 8:
                if parts[6].upper() != "LAW":
                    raise HybridMemoryGrammarError(f"line {line_no}: expected LAW")
                law = _id(parts[7], "law id")
                if law not in laws or laws[law][0] != mem:
                    raise HybridMemoryGrammarError(
                        f"line {line_no}: law {law} is not bound to memory {mem}"
                    )
                attrs["law_id"] = law
            operations.append(
                MemoryOperation(
                    op_id=f"reinforce.{route}.{mem}",
                    kind="REINFORCE",
                    task_id=current_task,
                    attributes=attrs,
                )
            )
            continue

        if head == "COUPLE":
            if len(parts) not in {6, 8} or parts[2].upper() != "TO" or parts[4].upper() != "MODE":
                raise HybridMemoryGrammarError(
                    f"line {line_no}: COUPLE syntax is "
                    "COUPLE source TO target MODE relation [TIMESCALE value]"
                )
            src = _id(parts[1], "source memory")
            dst = _id(parts[3], "target memory")
            mode = parts[5].upper()
            if src not in memories or dst not in memories:
                raise HybridMemoryGrammarError(f"line {line_no}: unknown coupling memory")
            if src == dst:
                raise HybridMemoryGrammarError(f"line {line_no}: self-coupling is not admitted")
            if mode not in COUPLING_MODES:
                raise HybridMemoryGrammarError(f"line {line_no}: unsupported coupling mode {mode}")
            attrs: dict[str, object] = {
                "source_memory": src,
                "target_memory": dst,
                "relation": mode.lower(),
            }
            if len(parts) == 8:
                if parts[6].upper() != "TIMESCALE":
                    raise HybridMemoryGrammarError(f"line {line_no}: expected TIMESCALE")
                attrs["timescale"] = parts[7]
            operations.append(
                MemoryOperation(
                    op_id=f"couple.{src}.{dst}.{mode.lower()}",
                    kind="COUPLE",
                    task_id=current_task,
                    attributes=attrs,
                )
            )
            continue

        if head == "RECALL":
            if (
                len(parts) not in {8, 10}
                or parts[2] != ":"
                or parts[4].upper() != "FROM"
                or parts[6].upper() != "MODE"
            ):
                raise HybridMemoryGrammarError(
                    f"line {line_no}: RECALL syntax is "
                    "RECALL symbol : TYPE FROM memory MODE DIRECT|RECONSTRUCTIVE "
                    "[PROVENANCE class]"
                )
            symbol = _id(parts[1], "recall symbol")
            value_type = parts[3].upper()
            mem = _id(parts[5], "memory id")
            mode = parts[7].upper()
            if mem not in memories:
                raise HybridMemoryGrammarError(f"line {line_no}: unknown memory {mem}")
            if mode not in memories[mem].access:
                raise HybridMemoryGrammarError(
                    f"line {line_no}: access mode {mode} not declared for memory {mem}"
                )
            expected = "RECALLED" if mode == "DIRECT" else "RECONSTRUCTED"
            provenance = expected
            if len(parts) == 10:
                if parts[8].upper() != "PROVENANCE":
                    raise HybridMemoryGrammarError(f"line {line_no}: expected PROVENANCE")
                provenance = parts[9].upper()
                if provenance not in PROVENANCE_CLASSES:
                    raise HybridMemoryGrammarError(
                        f"line {line_no}: unsupported provenance class {provenance}"
                    )
            recalls.append(
                RecallBinding(
                    symbol=symbol,
                    type_name=value_type,
                    memory_id=mem,
                    access_mode=mode,
                    provenance_class=provenance,
                    task_id=current_task,
                )
            )
            base_lines.append(f"INPUT {symbol} : ANY FROM memory.{mem}")
            continue

        if head == "GUIDE":
            if len(parts) != 4 or parts[2].upper() != "USING":
                raise HybridMemoryGrammarError(
                    f"line {line_no}: GUIDE syntax is GUIDE node_id USING memory"
                )
            target = _id(parts[1], "guide target")
            mem = _id(parts[3], "memory id")
            if mem not in memories:
                raise HybridMemoryGrammarError(f"line {line_no}: unknown memory {mem}")
            if "IMPLICIT" not in memories[mem].access:
                raise HybridMemoryGrammarError(
                    f"line {line_no}: GUIDE requires memory with IMPLICIT access"
                )
            operations.append(
                MemoryOperation(
                    op_id=f"guide.{target}.{mem}",
                    kind="GUIDE",
                    task_id=current_task,
                    attributes={
                        "target_node_id": target,
                        "memory_id": mem,
                        "effects": [x.lower() for x in memories[mem].effects],
                        "direct_retrieval": False,
                        "changes_future_transition_policy": True,
                    },
                )
            )
            continue

        base_lines.append(stripped)
        if head == "RETURN":
            returned = True

    if in_quantum:
        raise HybridMemoryGrammarError("unterminated QUANTUM block")

    try:
        base_program = compile_hybrid_program("\n".join(base_lines) + "\n")
    except HybridGrammarError as exc:
        raise HybridMemoryGrammarError(str(exc)) from exc

    base_ir = base_program.to_ir()
    symbol_names = {x["name"] for x in base_ir.get("symbols", [])}
    node_ids = {x["node_id"] for x in base_ir.get("nodes", [])}

    for op in operations:
        attrs = op.attributes
        if op.kind == "EVENT":
            if attrs["source_symbol"] not in symbol_names:
                raise HybridMemoryGrammarError(
                    f"EVENT {attrs['event_id']} references unknown symbol {attrs['source_symbol']}"
                )
        elif op.kind == "PATH":
            missing = [x for x in attrs["node_path"] if x not in node_ids]
            if missing:
                raise HybridMemoryGrammarError(
                    f"ROUTE {attrs['route_id']} references unknown node(s): {missing}"
                )
        elif op.kind == "GUIDE":
            if attrs["target_node_id"] not in node_ids:
                raise HybridMemoryGrammarError(
                    f"GUIDE references unknown node {attrs['target_node_id']}"
                )

    for recall in recalls:
        if recall.symbol not in symbol_names:
            raise HybridMemoryGrammarError(
                f"internal recall binding missing base symbol {recall.symbol}"
            )

    return CompiledHybridMemoryProgram(
        source=source,
        base_program=base_program,
        memories=tuple(memories[k] for k in sorted(memories)),
        representations=tuple(representations[k] for k in sorted(representations)),
        operations=tuple(operations),
        recalls=tuple(recalls),
    )


__all__ = [
    "GRAMMAR_SCHEMA",
    "IR_SCHEMA",
    "MEMORY_SCHEMA",
    "REPRESENTATION_SCHEMA",
    "OP_SCHEMA",
    "HybridMemoryGrammarError",
    "MemoryObject",
    "RepresentationProfile",
    "MemoryOperation",
    "RecallBinding",
    "CompiledHybridMemoryProgram",
    "compile_hybrid_memory_program",
]
