from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import struct
from typing import Mapping, Sequence

from .definitions_v11 import DefinitionContent, DefinitionRecord, DefinitionRegistry
from .execution_v20_model import (
    DEFAULT_SOCKET,
    DEFAULT_SURFACE_ROOT,
    _DIGEST_RE,
    _compact_json,
    _sha256_bytes,
    _sha256_json,
    _typed_id,
)
from .lineage_v22 import LINEAGE_CONTRACT_ID
from .natural_control_v16 import (
    NaturalControlRegistry,
    NaturalControlV16Error,
    NaturalControlResolution,
    RouteSpec,
    default_control_registry,
    resolve_natural_control,
)

COMPOSITION_CONTRACT_ID = "PNCS_NATURAL_PROGRAM_COMPOSITION_V0_23"
COMPOSITION_SCHEMA = COMPOSITION_CONTRACT_ID
ROUTE_REF_SCHEMA = "PNCS_REGISTERED_ROUTE_REFERENCE_V0_23"
RETURN_REF_SCHEMA = "PNCS_REGISTERED_RETURN_REFERENCE_V0_23"
CONTROL_LINEAGE_BINDING_SCHEMA = "PNCS_PROGRAM_CONTROL_LINEAGE_BINDING_V0_23"
COMPOSITION_ADMISSION_SCHEMA = "PNCS_NATURAL_PROGRAM_COMPOSITION_ADMISSION_V0_23"
OPERATOR_WITNESS_SCHEMA = "PNCS_PROGRAM_OPERATOR_WITNESS_V0_23"

_COMPOSITION_PREFIX = "pncs:composition:sha256:"
_ROUTE_REF_PREFIX = "pncs:route-ref:sha256:"
_RETURN_REF_PREFIX = "pncs:return-ref:sha256:"
_LINEAGE_PREFIX = "pncs:lineage:sha256:"
_RESULT_PREFIX = "pncs:result:sha256:"
_DEF_PREFIX = "pncs:def:sha256:"
_NAME_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_CONTINUATION_RE = re.compile(
    r"^\s*(?:GO(?:\s+TO)?|ROUTE\s+TO)\s+(?P<route>.+?)\s*$",
    re.IGNORECASE,
)
_AND_THEN_RE = re.compile(r"\s+AND\s+THEN\s+", re.IGNORECASE)
_RETURN_SEP_RE = re.compile(r"\s+RETURN\s+", re.IGNORECASE)


class NaturalProgramV23Error(ValueError):
    pass


def _phrase(raw: str) -> str:
    if not isinstance(raw, str):
        raise NaturalProgramV23Error("registered phrase must be a string")
    return " ".join(raw.strip().lower().replace("_", " ").split())


def _typed(value: object, prefix: str, field: str) -> str:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise NaturalProgramV23Error(f"{field} has invalid typed-ID prefix")
    digest = value[len(prefix):]
    if not _DIGEST_RE.fullmatch(digest):
        raise NaturalProgramV23Error(f"{field} must contain lowercase SHA-256")
    return value


@dataclass(frozen=True)
class RegisteredRouteRef:
    canonical: str
    route_kind: str = "INTERNAL_TRANSFORM"

    def __post_init__(self) -> None:
        if not _NAME_RE.fullmatch(self.canonical):
            raise NaturalProgramV23Error("canonical continuation route must be a PNCS identifier")
        if self.route_kind != "INTERNAL_TRANSFORM":
            raise NaturalProgramV23Error("v0.23 continuation routes must remain INTERNAL_TRANSFORM")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": ROUTE_REF_SCHEMA,
            "canonical": self.canonical,
            "route_kind": self.route_kind,
        }

    @property
    def ref_id(self) -> str:
        return _typed_id("pncs:route-ref", self.payload)


@dataclass(frozen=True)
class ReturnSpec:
    canonical: str
    aliases: tuple[str, ...]
    source_kind: str

    def __post_init__(self) -> None:
        if not _NAME_RE.fullmatch(self.canonical):
            raise NaturalProgramV23Error("canonical return selector must be a PNCS identifier")
        if not self.aliases:
            raise NaturalProgramV23Error("return selector requires at least one alias")
        if self.source_kind not in {"V0_20_RESULT", "V0_20_FINAL_STATE", "V0_22_LINEAGE"}:
            raise NaturalProgramV23Error("unsupported v0.23 return source kind")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": RETURN_REF_SCHEMA,
            "canonical": self.canonical,
            "source_kind": self.source_kind,
        }

    @property
    def ref_id(self) -> str:
        return _typed_id("pncs:return-ref", self.payload)


class ReturnRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ReturnSpec] = {}
        self._aliases: dict[str, str] = {}

    def register(self, spec: ReturnSpec) -> ReturnSpec:
        if not isinstance(spec, ReturnSpec):
            raise NaturalProgramV23Error("ReturnSpec required")
        if spec.canonical in self._specs:
            raise NaturalProgramV23Error(f"duplicate canonical return selector: {spec.canonical}")
        aliases = {_phrase(spec.canonical), *(_phrase(x) for x in spec.aliases)}
        for alias in aliases:
            if not alias:
                raise NaturalProgramV23Error("empty return alias")
            prior = self._aliases.get(alias)
            if prior is not None and prior != spec.canonical:
                raise NaturalProgramV23Error(f"ambiguous return alias: {alias}")
        self._specs[spec.canonical] = spec
        for alias in aliases:
            self._aliases[alias] = spec.canonical
        return spec

    def resolve(self, phrase: str) -> ReturnSpec:
        alias = _phrase(phrase)
        canonical = self._aliases.get(alias)
        if canonical is None:
            raise NaturalProgramV23Error(f"unknown registered return selector: {phrase}")
        return self._specs[canonical]


def default_return_registry() -> ReturnRegistry:
    registry = ReturnRegistry()
    registry.register(ReturnSpec("result.control_location", ("control location", "selected route", "route"), "V0_20_RESULT"))
    registry.register(ReturnSpec("result.branch_truth_state", ("branch truth state", "truth state"), "V0_20_RESULT"))
    registry.register(ReturnSpec("result.final_sigma_id", ("final sigma id", "final sigma"), "V0_20_FINAL_STATE"))
    registry.register(ReturnSpec("result.lineage_id", ("lineage id", "inverse lineage id"), "V0_22_LINEAGE"))
    return registry


@dataclass(frozen=True)
class NaturalProgramRegistry:
    controls: NaturalControlRegistry
    definitions: DefinitionRegistry
    returns: ReturnRegistry


def default_program_registry() -> NaturalProgramRegistry:
    controls = default_control_registry()
    definitions = DefinitionRegistry()
    seed = resolve_natural_control(
        "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN GO safety pause ELSE GO runtime continue",
        controls,
    )
    definitions.register(
        DefinitionRecord(
            alias="safety_bifurcation",
            content=seed.content,
            provenance=("v0.23:default_registered_control_authority",),
        )
    )
    return NaturalProgramRegistry(controls=controls, definitions=definitions, returns=default_return_registry())


@dataclass(frozen=True)
class ProgramResolutionStep:
    kind: str
    surface: str
    canonical: str
    reference_id: str

    def __post_init__(self) -> None:
        if self.kind not in {"CONTROL", "AND_THEN_ROUTE", "RETURN"}:
            raise NaturalProgramV23Error("unsupported program resolution step kind")
        if not self.surface or not self.canonical:
            raise NaturalProgramV23Error("program resolution step requires surface and canonical values")


@dataclass(frozen=True)
class NaturalProgramComposition:
    control_content: DefinitionContent
    continuation_routes: tuple[RegisteredRouteRef, ...]
    return_spec: ReturnSpec

    def __post_init__(self) -> None:
        if not isinstance(self.control_content, DefinitionContent):
            raise NaturalProgramV23Error("registered DefinitionContent authority required")
        self.control_content.verify()
        if self.control_content.kind != "INTERNAL_BRANCH":
            raise NaturalProgramV23Error("v0.23 control root must be INTERNAL_BRANCH")
        for route in self.continuation_routes:
            if not isinstance(route, RegisteredRouteRef):
                raise NaturalProgramV23Error("continuation_routes must contain RegisteredRouteRef values")
        if not isinstance(self.return_spec, ReturnSpec):
            raise NaturalProgramV23Error("registered ReturnSpec required")

    @property
    def control_graph_sha256(self) -> str:
        return _sha256_json(self.control_content.canonical_graph)

    @property
    def operator_schedule(self) -> tuple[str, ...]:
        schedule = tuple(self.control_content.leaf_path)
        for _route in self.continuation_routes:
            schedule += ("ORDER", "TRANSFORM", "COMPOSITION")
        return schedule + ("RETURN",)

    @property
    def dependency_ids(self) -> tuple[str, ...]:
        return (self.control_content.content_id, *(x.ref_id for x in self.continuation_routes), self.return_spec.ref_id)

    @property
    def canonical_graph(self) -> tuple[object, ...]:
        return (
            "program_composition",
            ("control_ref", self.control_content.content_id, self.control_graph_sha256),
            ("and_then", *(("route_ref", route.ref_id, route.canonical, route.route_kind) for route in self.continuation_routes)),
            ("return_ref", self.return_spec.ref_id, self.return_spec.canonical, self.return_spec.source_kind),
        )

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": COMPOSITION_SCHEMA,
            "composition_contract_id": COMPOSITION_CONTRACT_ID,
            "kind": "BOUNDED_NATURAL_PROGRAM_COMPOSITION",
            "canonical_graph": self.canonical_graph,
            "control_definition_id": self.control_content.content_id,
            "control_graph_sha256": self.control_graph_sha256,
            "continuation_routes": [x.payload | {"ref_id": x.ref_id} for x in self.continuation_routes],
            "return_selector": self.return_spec.payload | {"ref_id": self.return_spec.ref_id},
            "dependency_ids": list(self.dependency_ids),
            "operator_schedule": list(self.operator_schedule),
            "required_result_lineage_contract_id": LINEAGE_CONTRACT_ID,
            "external_effects": False,
            "free_form_nl_execution": False,
            "v0_20_executable": False,
            "deterministic_fields_only": True,
        }

    @property
    def composition_id(self) -> str:
        return _typed_id("pncs:composition", self.payload)


@dataclass(frozen=True)
class NaturalProgramResolution:
    source_text: str
    control_resolution: NaturalControlResolution
    composition: NaturalProgramComposition
    trace: tuple[ProgramResolutionStep, ...]

    @property
    def composition_id(self) -> str:
        return self.composition.composition_id

    @property
    def canonical_graph(self) -> tuple[object, ...]:
        return self.composition.canonical_graph

    @property
    def operator_schedule(self) -> tuple[str, ...]:
        return self.composition.operator_schedule


def _registered_control(resolution: NaturalControlResolution, definitions: DefinitionRegistry) -> DefinitionContent:
    try:
        authoritative = definitions.content(resolution.content_id)
    except Exception as exc:
        raise NaturalProgramV23Error(f"resolved control Definition is not registered authority: {resolution.content_id}") from exc
    if authoritative.semantic_payload != resolution.content.semantic_payload:
        raise NaturalProgramV23Error("registered control Definition payload mismatch")
    if authoritative.kind != "INTERNAL_BRANCH":
        raise NaturalProgramV23Error("registered control authority is not INTERNAL_BRANCH")
    return authoritative


def _continuation_ref(surface: str, registry: NaturalControlRegistry) -> RegisteredRouteRef:
    match = _CONTINUATION_RE.fullmatch(surface)
    if match is None:
        raise NaturalProgramV23Error("AND THEN accepts only registered internal GO/GO TO/ROUTE TO continuation")
    try:
        route: RouteSpec = registry.routes.resolve(match.group("route"))
    except NaturalControlV16Error as exc:
        raise NaturalProgramV23Error(str(exc)) from exc
    return RegisteredRouteRef(route.canonical, route.route_kind)


def resolve_natural_program(text: str, registry: NaturalProgramRegistry | None = None) -> NaturalProgramResolution:
    if not isinstance(text, str) or not text.strip():
        raise NaturalProgramV23Error("non-empty natural program required")
    active = registry or default_program_registry()
    source = text.strip()
    if source.endswith("."):
        source = source[:-1].rstrip()

    return_matches = list(_RETURN_SEP_RE.finditer(source))
    if len(return_matches) != 1:
        raise NaturalProgramV23Error("v0.23 program requires exactly one terminal RETURN clause")
    marker = return_matches[0]
    prefix = source[: marker.start()].strip()
    return_surface = source[marker.end() :].strip()
    if not prefix or not return_surface:
        raise NaturalProgramV23Error("v0.23 program requires control body and registered RETURN selector")

    segments = _AND_THEN_RE.split(prefix)
    if not segments or any(not x.strip() for x in segments):
        raise NaturalProgramV23Error("malformed AND THEN composition")
    control_surface = segments[0].strip()

    try:
        control_resolution = resolve_natural_control(control_surface, active.controls)
    except NaturalControlV16Error as exc:
        raise NaturalProgramV23Error(str(exc)) from exc
    authoritative = _registered_control(control_resolution, active.definitions)

    continuation_refs: list[RegisteredRouteRef] = []
    trace: list[ProgramResolutionStep] = [ProgramResolutionStep("CONTROL", control_surface, authoritative.content_id, authoritative.content_id)]
    for surface in segments[1:]:
        surface = surface.strip()
        ref = _continuation_ref(surface, active.controls)
        continuation_refs.append(ref)
        trace.append(ProgramResolutionStep("AND_THEN_ROUTE", surface, ref.canonical, ref.ref_id))

    return_spec = active.returns.resolve(return_surface)
    trace.append(ProgramResolutionStep("RETURN", return_surface, return_spec.canonical, return_spec.ref_id))

    composition = NaturalProgramComposition(authoritative, tuple(continuation_refs), return_spec)
    return NaturalProgramResolution(text, control_resolution, composition, tuple(trace))


@dataclass(frozen=True)
class ProgramControlLineageBinding:
    composition_id: str
    control_definition_id: str
    control_result_id: str
    control_lineage_id: str
    lineage_contract_id: str = LINEAGE_CONTRACT_ID

    def __post_init__(self) -> None:
        _typed(self.composition_id, _COMPOSITION_PREFIX, "composition_id")
        _typed(self.control_definition_id, _DEF_PREFIX, "control_definition_id")
        _typed(self.control_result_id, _RESULT_PREFIX, "control_result_id")
        _typed(self.control_lineage_id, _LINEAGE_PREFIX, "control_lineage_id")
        if self.lineage_contract_id != LINEAGE_CONTRACT_ID:
            raise NaturalProgramV23Error("v0.23 requires exact v0.22 lineage contract")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": CONTROL_LINEAGE_BINDING_SCHEMA,
            "composition_id": self.composition_id,
            "control_definition_id": self.control_definition_id,
            "control_result_id": self.control_result_id,
            "control_lineage_id": self.control_lineage_id,
            "lineage_contract_id": self.lineage_contract_id,
            "binding_scope": "CONTROL_RESULT_ONLY",
            "continuation_execution_claimed": False,
        }

    @property
    def binding_id(self) -> str:
        return _typed_id("pncs:program-control-lineage", self.payload)


def bind_control_result_lineage(composition: NaturalProgramComposition, lineage: object) -> ProgramControlLineageBinding:
    if not isinstance(composition, NaturalProgramComposition):
        raise NaturalProgramV23Error("NaturalProgramComposition required")
    payload = getattr(lineage, "payload", None)
    hierarchy = getattr(lineage, "hierarchy", None)
    if not isinstance(payload, Mapping) or hierarchy is None:
        raise NaturalProgramV23Error("ExactInverseLineage-compatible object required")
    if payload.get("lineage_contract_id") != LINEAGE_CONTRACT_ID:
        raise NaturalProgramV23Error("control result does not expose the v0.22 lineage contract")
    definition_id = getattr(hierarchy, "definition_id", None)
    if definition_id != composition.control_content.content_id:
        raise NaturalProgramV23Error("control lineage Definition does not match program control Definition")
    result_id = _typed(getattr(lineage, "result_id", None), _RESULT_PREFIX, "control result_id")
    lineage_id = _typed(getattr(lineage, "lineage_id", None), _LINEAGE_PREFIX, "control lineage_id")
    receipt = getattr(lineage, "receipt", None)
    if not isinstance(receipt, Mapping) or receipt.get("lineage_id") != lineage_id:
        raise NaturalProgramV23Error("control lineage receipt/identity mismatch")
    return ProgramControlLineageBinding(composition.composition_id, composition.control_content.content_id, result_id, lineage_id)


@dataclass(frozen=True)
class ProgramOperatorWitness:
    index: int
    operator_id: str
    operator_vector_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or self.index < 1:
            raise NaturalProgramV23Error("operator witness index must be positive")
        if not isinstance(self.operator_id, str) or not self.operator_id:
            raise NaturalProgramV23Error("operator witness requires operator_id")
        if not _DIGEST_RE.fullmatch(self.operator_vector_sha256):
            raise NaturalProgramV23Error("operator witness requires lowercase SHA-256")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": OPERATOR_WITNESS_SCHEMA,
            "index": self.index,
            "operator_id": self.operator_id,
            "operator_vector_sha256": self.operator_vector_sha256,
        }


@dataclass(frozen=True)
class ProgramCompositionAdmission:
    composition_id: str
    live_surface: Mapping[str, object]
    operator_witnesses: tuple[ProgramOperatorWitness, ...]

    def __post_init__(self) -> None:
        _typed(self.composition_id, _COMPOSITION_PREFIX, "composition_id")
        if not isinstance(self.live_surface, Mapping) or self.live_surface.get("root") != str(DEFAULT_SURFACE_ROOT):
            raise NaturalProgramV23Error("program composition admission requires canonical live surface")
        if not self.operator_witnesses:
            raise NaturalProgramV23Error("program composition admission requires operator witnesses")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": COMPOSITION_ADMISSION_SCHEMA,
            "composition_contract_id": COMPOSITION_CONTRACT_ID,
            "composition_id": self.composition_id,
            "live_surface": dict(self.live_surface),
            "operator_witnesses": [x.payload for x in self.operator_witnesses],
            "execution_opened": False,
            "return_execution_opened": False,
            "external_effects": False,
            "operator_presence_is_execution_authority": False,
            "static_runtime_fallback": False,
            "deterministic_fields_only": True,
        }

    @property
    def admission_id(self) -> str:
        return _typed_id("pncs:composition-admission", self.payload)


def admit_program_composition(
    composition: NaturalProgramComposition,
    *,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
    persist: bool = True,
) -> ProgramCompositionAdmission:
    if not isinstance(composition, NaturalProgramComposition):
        raise NaturalProgramV23Error("NaturalProgramComposition required")
    root = Path(surface_root)
    if root != DEFAULT_SURFACE_ROOT:
        raise NaturalProgramV23Error("v0.23 composition admission is fixed to /dev/shm/ciel_noema")

    from .execution_v20_live import load_live_surface

    live = load_live_surface(root, socket_path=socket_path, require_socket=True, max_heartbeat_age_s=max_heartbeat_age_s)
    if live.root != str(DEFAULT_SURFACE_ROOT):
        raise NaturalProgramV23Error("live surface root mismatch")

    witnesses: list[ProgramOperatorWitness] = []
    for index, operator_id in enumerate(composition.operator_schedule, start=1):
        vector = live.operator_vectors.get(operator_id)
        if vector is None:
            raise NaturalProgramV23Error(f"live PhaseNav registry is missing v0.23 composition operator: {operator_id}")
        raw = struct.pack("<36d", *vector)
        witnesses.append(ProgramOperatorWitness(index, operator_id, _sha256_bytes(raw)))

    admission = ProgramCompositionAdmission(composition.composition_id, live.receipt_payload, tuple(witnesses))
    if persist:
        path = root / "pncs/v0.23/compositions" / f"{admission.admission_id.rsplit(':', 1)[-1]}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        raw = (_compact_json({**admission.payload, "admission_id": admission.admission_id}) + "\n").encode("utf-8")
        with tmp.open("wb") as fh:
            fh.write(raw)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    return admission
