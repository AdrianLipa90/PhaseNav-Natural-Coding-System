from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Mapping, Sequence

PROGRAM_CONTRACT_ID = "PNCS_NATIVE_PNV_PROGRAM_UNITS_V0_24"
PROGRAM_CONTENT_SCHEMA = "PNCS_PROGRAM_UNIT_CONTENT_V0_24"
PROGRAM_BUILD_CONTRACT_ID = "PNCS_NATIVE_PNV_PROGRAM_BUILD_V0_24"
PROGRAM_BUILD_SCHEMA = "PNCS_NATIVE_PNV_PROGRAM_BUILD_RECEIPT_V0_24"
EXPECTED_COMPOSITION_CONTRACT_ID = "PNCS_NATURAL_PROGRAM_COMPOSITION_V0_23"
EXPECTED_LINEAGE_CONTRACT_ID = "PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22"
DEFAULT_SURFACE_ROOT = Path("/dev/shm/ciel_noema")
DEFAULT_SOCKET = Path("/run/user/1000/noema/ciel_headless.sock")

_PROGRAM_PREFIX = "pncs:program:sha256:"
_COMPOSITION_PREFIX = "pncs:composition:sha256:"
_DEFINITION_PREFIX = "pncs:def:sha256:"
_ROUTE_REF_PREFIX = "pncs:route-ref:sha256:"
_RETURN_REF_PREFIX = "pncs:return-ref:sha256:"
_BUILD_PREFIX = "pncs:program-build:sha256:"
_COMPOSITION_ADMISSION_PREFIX = "pncs:composition-admission:sha256:"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_HEADER = (
    "PNV 1",
    "PNCS PROGRAM_UNIT 0.24",
    "EPISTEMIC CHYBA",
    "MODE READ_ONLY",
)


class NativeProgramV24Error(ValueError):
    pass


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise NativeProgramV24Error("non-finite value is not canonical JSON")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise NativeProgramV24Error(f"unsupported canonical value type: {type(value).__name__}")


def _compact_json(value: object) -> str:
    return json.dumps(
        _jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_compact_json(value).encode("utf-8"))


def _typed_id(prefix: str, value: object) -> str:
    return f"{prefix}:sha256:{_sha256_json(value)}"


def _typed(value: object, prefix: str, field: str) -> str:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise NativeProgramV24Error(f"{field} has invalid typed-ID prefix")
    digest = value[len(prefix):]
    if not _DIGEST_RE.fullmatch(digest):
        raise NativeProgramV24Error(f"{field} must contain lowercase SHA-256")
    return value


def _digest(value: object, field: str) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise NativeProgramV24Error(f"{field} must be lowercase 64-hex SHA-256")
    return value


def _false(value: object, field: str) -> None:
    if value is not False:
        raise NativeProgramV24Error(f"{field} must remain false in v0.24")


def _true(value: object, field: str) -> None:
    if value is not True:
        raise NativeProgramV24Error(f"{field} must remain true in v0.24")


def _composition_payload(composition: object) -> Mapping[str, object]:
    payload = getattr(composition, "payload", None)
    if not isinstance(payload, Mapping):
        raise NativeProgramV24Error("v0.23 NaturalProgramComposition-compatible object required")
    if payload.get("schema") != EXPECTED_COMPOSITION_CONTRACT_ID:
        raise NativeProgramV24Error("composition schema mismatch")
    if payload.get("composition_contract_id") != EXPECTED_COMPOSITION_CONTRACT_ID:
        raise NativeProgramV24Error("composition contract mismatch")
    _false(payload.get("external_effects"), "composition.external_effects")
    _false(payload.get("free_form_nl_execution"), "composition.free_form_nl_execution")
    _false(payload.get("v0_20_executable"), "composition.v0_20_executable")
    _true(payload.get("deterministic_fields_only"), "composition.deterministic_fields_only")
    if payload.get("required_result_lineage_contract_id") != EXPECTED_LINEAGE_CONTRACT_ID:
        raise NativeProgramV24Error("composition lineage contract mismatch")
    return payload


@dataclass(frozen=True)
class ProgramDependency:
    kind: str
    content_id: str

    def __post_init__(self) -> None:
        prefixes = {
            "COMPOSITION": _COMPOSITION_PREFIX,
            "CONTROL_DEFINITION": _DEFINITION_PREFIX,
            "ROUTE_REF": _ROUTE_REF_PREFIX,
            "RETURN_REF": _RETURN_REF_PREFIX,
        }
        prefix = prefixes.get(self.kind)
        if prefix is None:
            raise NativeProgramV24Error(f"unsupported program dependency kind: {self.kind}")
        _typed(self.content_id, prefix, f"{self.kind} dependency")

    @property
    def payload(self) -> dict[str, object]:
        return {"kind": self.kind, "content_id": self.content_id}


@dataclass(frozen=True)
class ProgramDependencyOccurrence:
    index: int
    kind: str
    content_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or self.index < 0:
            raise NativeProgramV24Error("dependency occurrence index must be non-negative")
        ProgramDependency(self.kind, self.content_id)

    @property
    def payload(self) -> dict[str, object]:
        return {"index": self.index, "kind": self.kind, "content_id": self.content_id}


def _dependency_kind(content_id: str) -> str:
    if content_id.startswith(_DEFINITION_PREFIX):
        return "CONTROL_DEFINITION"
    if content_id.startswith(_ROUTE_REF_PREFIX):
        return "ROUTE_REF"
    if content_id.startswith(_RETURN_REF_PREFIX):
        return "RETURN_REF"
    raise NativeProgramV24Error(f"unsupported v0.23 composition dependency ID: {content_id}")


def _dependency_occurrences(
    composition_id: str,
    dependency_ids: Sequence[object],
) -> tuple[ProgramDependencyOccurrence, ...]:
    _typed(composition_id, _COMPOSITION_PREFIX, "composition_id")
    out: list[ProgramDependencyOccurrence] = []
    for index, raw in enumerate(dependency_ids):
        if not isinstance(raw, str):
            raise NativeProgramV24Error("composition dependency_ids must contain strings")
        out.append(ProgramDependencyOccurrence(index, _dependency_kind(raw), raw))
    if not out or out[0].kind != "CONTROL_DEFINITION":
        raise NativeProgramV24Error("v0.24 composition must begin with CONTROL_DEFINITION dependency")
    if out[-1].kind != "RETURN_REF":
        raise NativeProgramV24Error("v0.24 composition must terminate dependency occurrences with RETURN_REF")
    if sum(x.kind == "RETURN_REF" for x in out) != 1:
        raise NativeProgramV24Error("v0.24 requires exactly one RETURN_REF dependency occurrence")
    return tuple(out)


def _dependency_closure(
    composition_id: str,
    occurrences: Sequence[ProgramDependencyOccurrence],
) -> tuple[ProgramDependency, ...]:
    rows: dict[tuple[str, str], ProgramDependency] = {
        ("COMPOSITION", composition_id): ProgramDependency("COMPOSITION", composition_id)
    }
    for occ in occurrences:
        rows[(occ.kind, occ.content_id)] = ProgramDependency(occ.kind, occ.content_id)
    order = {"COMPOSITION": 0, "CONTROL_DEFINITION": 1, "ROUTE_REF": 2, "RETURN_REF": 3}
    return tuple(sorted(rows.values(), key=lambda d: (order[d.kind], d.content_id)))


@dataclass(frozen=True)
class NativeProgramUnit:
    composition_id: str
    composition_payload_sha256: str
    composition_graph_sha256: str
    dependency_closure: tuple[ProgramDependency, ...]
    dependency_occurrences: tuple[ProgramDependencyOccurrence, ...]
    operator_schedule: tuple[str, ...]
    return_ref_id: str
    lineage_contract_id: str = EXPECTED_LINEAGE_CONTRACT_ID

    def __post_init__(self) -> None:
        _typed(self.composition_id, _COMPOSITION_PREFIX, "composition_id")
        _digest(self.composition_payload_sha256, "composition_payload_sha256")
        _digest(self.composition_graph_sha256, "composition_graph_sha256")
        if not self.dependency_closure:
            raise NativeProgramV24Error("dependency closure is empty")
        if self.dependency_closure[0] != ProgramDependency("COMPOSITION", self.composition_id):
            raise NativeProgramV24Error("dependency closure must begin with exact COMPOSITION")
        if not self.dependency_occurrences:
            raise NativeProgramV24Error("dependency occurrences are empty")
        for expected, occ in enumerate(self.dependency_occurrences):
            if occ.index != expected:
                raise NativeProgramV24Error("dependency occurrence indexes must be contiguous from zero")
        _typed(self.return_ref_id, _RETURN_REF_PREFIX, "return_ref_id")
        if self.dependency_occurrences[-1].content_id != self.return_ref_id:
            raise NativeProgramV24Error("RETURN_REF occurrence/return_ref_id mismatch")
        if not self.operator_schedule:
            raise NativeProgramV24Error("operator schedule is empty")
        for operator_id in self.operator_schedule:
            if not isinstance(operator_id, str) or not operator_id or operator_id != operator_id.upper():
                raise NativeProgramV24Error("operator schedule must contain canonical uppercase operator IDs")
        if self.operator_schedule[-1] != "RETURN":
            raise NativeProgramV24Error("v0.24 operator schedule must terminate with existing RETURN operator")
        if self.lineage_contract_id != EXPECTED_LINEAGE_CONTRACT_ID:
            raise NativeProgramV24Error("v0.24 requires exact v0.22 lineage contract")

    @classmethod
    def from_composition(cls, composition: object) -> "NativeProgramUnit":
        payload = _composition_payload(composition)
        composition_id = _typed(
            getattr(composition, "composition_id", None),
            _COMPOSITION_PREFIX,
            "composition_id",
        )
        if _typed_id("pncs:composition", payload) != composition_id:
            raise NativeProgramV24Error("composition content-address identity mismatch")

        graph = getattr(composition, "canonical_graph", None)
        if graph is None:
            raise NativeProgramV24Error("composition canonical_graph unavailable")
        graph_sha = _sha256_json(graph)
        if payload.get("canonical_graph") != graph:
            if _jsonable(payload.get("canonical_graph")) != _jsonable(graph):
                raise NativeProgramV24Error("composition canonical graph/payload mismatch")

        dependency_ids = getattr(composition, "dependency_ids", None)
        if not isinstance(dependency_ids, (tuple, list)):
            raise NativeProgramV24Error("composition dependency_ids unavailable")
        if list(dependency_ids) != list(payload.get("dependency_ids", [])):
            raise NativeProgramV24Error("composition dependency IDs/payload mismatch")
        occurrences = _dependency_occurrences(composition_id, dependency_ids)
        closure = _dependency_closure(composition_id, occurrences)

        schedule_raw = getattr(composition, "operator_schedule", None)
        if not isinstance(schedule_raw, (tuple, list)):
            raise NativeProgramV24Error("composition operator_schedule unavailable")
        schedule = tuple(str(x) for x in schedule_raw)
        if list(schedule) != list(payload.get("operator_schedule", [])):
            raise NativeProgramV24Error("composition operator schedule/payload mismatch")

        return_selector = payload.get("return_selector")
        if not isinstance(return_selector, Mapping):
            raise NativeProgramV24Error("composition return selector unavailable")
        return_ref_id = _typed(return_selector.get("ref_id"), _RETURN_REF_PREFIX, "return_ref_id")
        if occurrences[-1].content_id != return_ref_id:
            raise NativeProgramV24Error("composition return dependency mismatch")

        return cls(
            composition_id=composition_id,
            composition_payload_sha256=_sha256_json(payload),
            composition_graph_sha256=graph_sha,
            dependency_closure=closure,
            dependency_occurrences=occurrences,
            operator_schedule=schedule,
            return_ref_id=return_ref_id,
        )

    @property
    def dependency_closure_sha256(self) -> str:
        return _sha256_json([x.payload for x in self.dependency_closure])

    @property
    def dependency_occurrences_sha256(self) -> str:
        return _sha256_json([x.payload for x in self.dependency_occurrences])

    @property
    def operator_schedule_sha256(self) -> str:
        return _sha256_json(list(self.operator_schedule))

    @property
    def semantic_payload(self) -> dict[str, object]:
        return {
            "schema": PROGRAM_CONTENT_SCHEMA,
            "program_contract_id": PROGRAM_CONTRACT_ID,
            "composition_contract_id": EXPECTED_COMPOSITION_CONTRACT_ID,
            "composition_id": self.composition_id,
            "composition_payload_sha256": self.composition_payload_sha256,
            "composition_graph_sha256": self.composition_graph_sha256,
            "dependency_closure": [x.payload for x in self.dependency_closure],
            "dependency_closure_sha256": self.dependency_closure_sha256,
            "dependency_occurrences": [x.payload for x in self.dependency_occurrences],
            "dependency_occurrences_sha256": self.dependency_occurrences_sha256,
            "operator_schedule": list(self.operator_schedule),
            "operator_schedule_sha256": self.operator_schedule_sha256,
            "return_ref_id": self.return_ref_id,
            "required_result_lineage_contract_id": self.lineage_contract_id,
            "external_effects": False,
            "free_form_nl_execution": False,
            "native_execution_opened": False,
            "return_execution_opened": False,
            "static_runtime_fallback": False,
            "deterministic_fields_only": True,
        }

    @property
    def program_id(self) -> str:
        return _typed_id("pncs:program", self.semantic_payload)

    def verify(self) -> None:
        expected = _typed_id("pncs:program", self.semantic_payload)
        if expected != self.program_id:
            raise NativeProgramV24Error("program content digest mismatch")


class NativeProgramUnitRegistry:
    """Authority registry for v0.24 first-class native program units.

    Serialized .pnv text cannot create program semantics. A claimed PROGRAM_ID
    must already be registered from a verified v0.23 composition.
    """

    def __init__(self) -> None:
        self._by_program: dict[str, NativeProgramUnit] = {}
        self._by_composition: dict[str, str] = {}

    def register_composition(self, composition: object) -> NativeProgramUnit:
        unit = NativeProgramUnit.from_composition(composition)
        return self.register_unit(unit)

    def register_unit(self, unit: NativeProgramUnit) -> NativeProgramUnit:
        if not isinstance(unit, NativeProgramUnit):
            raise NativeProgramV24Error("NativeProgramUnit required")
        unit.verify()
        prior = self._by_program.get(unit.program_id)
        if prior is not None and prior.semantic_payload != unit.semantic_payload:
            raise NativeProgramV24Error("program content-address collision")
        prior_program = self._by_composition.get(unit.composition_id)
        if prior_program is not None and prior_program != unit.program_id:
            raise NativeProgramV24Error("one composition resolved to multiple v0.24 program identities")
        self._by_program[unit.program_id] = unit
        self._by_composition[unit.composition_id] = unit.program_id
        return unit

    def unit(self, program_id: str) -> NativeProgramUnit:
        _typed(program_id, _PROGRAM_PREFIX, "program_id")
        try:
            return self._by_program[program_id]
        except KeyError as exc:
            raise NativeProgramV24Error(f"program ID is not registered authority: {program_id}") from exc

    def from_composition(self, composition_id: str) -> NativeProgramUnit:
        _typed(composition_id, _COMPOSITION_PREFIX, "composition_id")
        try:
            return self.unit(self._by_composition[composition_id])
        except KeyError as exc:
            raise NativeProgramV24Error(
                f"composition ID is not registered as a v0.24 program: {composition_id}"
            ) from exc


@dataclass(frozen=True)
class WrittenNativeProgramUnit:
    unit: NativeProgramUnit
    text: str

    @property
    def program_id(self) -> str:
        return self.unit.program_id

    @property
    def pnv_sha256(self) -> str:
        return _sha256_bytes(self.text.encode("utf-8"))


def _index(value: int) -> str:
    if not isinstance(value, int) or value < 0 or value > 999:
        raise NativeProgramV24Error("v0.24 serialized index must be in [0,999]")
    return f"{value:03d}"


def render_native_program_unit(unit: NativeProgramUnit) -> str:
    if not isinstance(unit, NativeProgramUnit):
        raise NativeProgramV24Error("NativeProgramUnit required")
    unit.verify()
    if (
        len(unit.dependency_closure) > 1000
        or len(unit.dependency_occurrences) > 1000
        or len(unit.operator_schedule) > 1000
    ):
        raise NativeProgramV24Error(
            "v0.24 canonical serializer supports at most 1000 indexed rows per section"
        )

    lines = [
        *_HEADER,
        f"PROGRAM_ID {unit.program_id}",
        f"COMPOSITION_ID {unit.composition_id}",
        f"COMPOSITION_CONTRACT {EXPECTED_COMPOSITION_CONTRACT_ID}",
        f"COMPOSITION_PAYLOAD_SHA256 {unit.composition_payload_sha256}",
        f"COMPOSITION_GRAPH_SHA256 {unit.composition_graph_sha256}",
        f"DEPENDENCY_CLOSURE_SHA256 {unit.dependency_closure_sha256}",
        f"DEPENDENCY_OCCURRENCES_SHA256 {unit.dependency_occurrences_sha256}",
        f"OPERATOR_SCHEDULE_SHA256 {unit.operator_schedule_sha256}",
        f"LINEAGE_CONTRACT {unit.lineage_contract_id}",
    ]
    for index, dep in enumerate(unit.dependency_closure):
        lines.append(f"DEPENDENCY {_index(index)} {dep.kind} {dep.content_id}")
    for occ in unit.dependency_occurrences:
        lines.append(f"OCCURRENCE {_index(occ.index)} {occ.kind} {occ.content_id}")
    for index, operator_id in enumerate(unit.operator_schedule):
        lines.append(f"OPERATOR {_index(index)} {operator_id}")
    lines += [
        f"RETURN_REF {unit.return_ref_id}",
        "EXTERNAL_EFFECTS FALSE",
        "FREE_FORM_NL_EXECUTION FALSE",
        "NATIVE_EXECUTION_OPENED FALSE",
        "RETURN_EXECUTION_OPENED FALSE",
        "STATIC_RUNTIME_FALLBACK FALSE",
        "END PROGRAM_UNIT",
    ]
    return "\n".join(lines) + "\n"


def parse_native_program_unit(
    text: str,
    registry: NativeProgramUnitRegistry,
) -> WrittenNativeProgramUnit:
    if not isinstance(text, str) or not text:
        raise NativeProgramV24Error("non-empty .pnv program unit required")
    if not isinstance(registry, NativeProgramUnitRegistry):
        raise NativeProgramV24Error("NativeProgramUnitRegistry authority required")
    if not text.endswith("\n"):
        raise NativeProgramV24Error("canonical .pnv program unit must end with newline")
    lines = text.splitlines()
    if len(lines) < 12:
        raise NativeProgramV24Error("truncated v0.24 .pnv program unit")
    if tuple(lines[:4]) != _HEADER:
        raise NativeProgramV24Error("unsupported v0.24 .pnv program header")

    m_program = re.fullmatch(r"PROGRAM_ID (pncs:program:sha256:[0-9a-f]{64})", lines[4])
    m_composition = re.fullmatch(
        r"COMPOSITION_ID (pncs:composition:sha256:[0-9a-f]{64})",
        lines[5],
    )
    if m_program is None or m_composition is None:
        raise NativeProgramV24Error("invalid PROGRAM_ID/COMPOSITION_ID declaration")

    authoritative = registry.unit(m_program.group(1))
    if authoritative.composition_id != m_composition.group(1):
        raise NativeProgramV24Error("serialized composition/program authority mismatch")
    canonical = render_native_program_unit(authoritative)
    if text != canonical:
        raise NativeProgramV24Error(
            "serialized .pnv bytes are not canonical for registered program authority"
        )
    return WrittenNativeProgramUnit(authoritative, canonical)


@dataclass(frozen=True)
class ProgramBuildReceipt:
    program_id: str
    composition_id: str
    pnv_sha256: str
    pnv_size_bytes: int
    dependency_closure_sha256: str
    dependency_occurrences_sha256: str
    operator_schedule_sha256: str
    composition_admission_id: str
    live_surface: Mapping[str, object]
    operator_witnesses_sha256: str

    def __post_init__(self) -> None:
        _typed(self.program_id, _PROGRAM_PREFIX, "program_id")
        _typed(self.composition_id, _COMPOSITION_PREFIX, "composition_id")
        for field, value in (
            ("pnv_sha256", self.pnv_sha256),
            ("dependency_closure_sha256", self.dependency_closure_sha256),
            ("dependency_occurrences_sha256", self.dependency_occurrences_sha256),
            ("operator_schedule_sha256", self.operator_schedule_sha256),
            ("operator_witnesses_sha256", self.operator_witnesses_sha256),
        ):
            _digest(value, field)
        if not isinstance(self.pnv_size_bytes, int) or self.pnv_size_bytes <= 0:
            raise NativeProgramV24Error("pnv_size_bytes must be positive")
        _typed(
            self.composition_admission_id,
            _COMPOSITION_ADMISSION_PREFIX,
            "composition_admission_id",
        )
        if (
            not isinstance(self.live_surface, Mapping)
            or self.live_surface.get("root") != str(DEFAULT_SURFACE_ROOT)
        ):
            raise NativeProgramV24Error(
                "build receipt requires canonical live /dev/shm surface"
            )

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": PROGRAM_BUILD_SCHEMA,
            "build_contract_id": PROGRAM_BUILD_CONTRACT_ID,
            "program_id": self.program_id,
            "composition_id": self.composition_id,
            "pnv_sha256": self.pnv_sha256,
            "pnv_size_bytes": self.pnv_size_bytes,
            "dependency_closure_sha256": self.dependency_closure_sha256,
            "dependency_occurrences_sha256": self.dependency_occurrences_sha256,
            "operator_schedule_sha256": self.operator_schedule_sha256,
            "composition_admission_id": self.composition_admission_id,
            "live_surface": dict(self.live_surface),
            "operator_witnesses_sha256": self.operator_witnesses_sha256,
            "roundtrip_byte_identical": True,
            "execution_opened": False,
            "return_execution_opened": False,
            "external_effects": False,
            "static_runtime_fallback": False,
            "deterministic_fields_only": True,
        }

    @property
    def build_id(self) -> str:
        return _typed_id("pncs:program-build", self.payload)


@dataclass(frozen=True)
class NativeProgramBuild:
    unit: NativeProgramUnit
    written: WrittenNativeProgramUnit
    receipt: ProgramBuildReceipt
    program_path: str | None
    receipt_path: str | None


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with tmp.open("wb") as fh:
        fh.write(raw)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def build_native_program_unit(
    composition: object,
    *,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
    persist: bool = True,
) -> NativeProgramBuild:
    root = Path(surface_root)
    if root != DEFAULT_SURFACE_ROOT:
        raise NativeProgramV24Error(
            "v0.24 native program build is fixed to /dev/shm/ciel_noema"
        )

    unit = NativeProgramUnit.from_composition(composition)
    registry = NativeProgramUnitRegistry()
    registry.register_unit(unit)
    text = render_native_program_unit(unit)
    written = parse_native_program_unit(text, registry)

    try:
        from .composition_v23 import admit_program_composition

        admission = admit_program_composition(
            composition,
            surface_root=root,
            socket_path=socket_path,
            max_heartbeat_age_s=max_heartbeat_age_s,
            persist=False,
        )
    except Exception as exc:
        raise NativeProgramV24Error(
            f"live v0.23 composition admission failed: {exc}"
        ) from exc

    if getattr(admission, "composition_id", None) != unit.composition_id:
        raise NativeProgramV24Error("live admission/composition identity mismatch")
    admission_id = getattr(admission, "admission_id", None)
    _typed(admission_id, _COMPOSITION_ADMISSION_PREFIX, "composition_admission_id")
    live_surface = getattr(admission, "live_surface", None)
    if not isinstance(live_surface, Mapping):
        raise NativeProgramV24Error("live admission does not expose live surface receipt")
    witnesses = getattr(admission, "operator_witnesses", None)
    if not isinstance(witnesses, tuple) or not witnesses:
        raise NativeProgramV24Error("live admission does not expose operator witnesses")
    witness_payloads = []
    for witness in witnesses:
        payload = getattr(witness, "payload", None)
        if not isinstance(payload, Mapping):
            raise NativeProgramV24Error("malformed v0.23 operator witness")
        witness_payloads.append(dict(payload))
    if tuple(str(x.get("operator_id")) for x in witness_payloads) != unit.operator_schedule:
        raise NativeProgramV24Error(
            "live operator witness schedule differs from program unit"
        )

    raw = text.encode("utf-8")
    receipt = ProgramBuildReceipt(
        program_id=unit.program_id,
        composition_id=unit.composition_id,
        pnv_sha256=_sha256_bytes(raw),
        pnv_size_bytes=len(raw),
        dependency_closure_sha256=unit.dependency_closure_sha256,
        dependency_occurrences_sha256=unit.dependency_occurrences_sha256,
        operator_schedule_sha256=unit.operator_schedule_sha256,
        composition_admission_id=admission_id,
        live_surface=live_surface,
        operator_witnesses_sha256=_sha256_json(witness_payloads),
    )

    program_path: str | None = None
    receipt_path: str | None = None
    if persist:
        program_file = (
            root
            / "pncs/v0.24/programs"
            / f"{unit.program_id.rsplit(':', 1)[-1]}.pnv"
        )
        receipt_file = (
            root
            / "pncs/v0.24/receipts"
            / f"{receipt.build_id.rsplit(':', 1)[-1]}.json"
        )
        _atomic_write(program_file, raw)
        _atomic_write(
            receipt_file,
            (
                _compact_json({**receipt.payload, "build_id": receipt.build_id})
                + "\n"
            ).encode("utf-8"),
        )
        program_path = str(program_file)
        receipt_path = str(receipt_file)

    return NativeProgramBuild(unit, written, receipt, program_path, receipt_path)
