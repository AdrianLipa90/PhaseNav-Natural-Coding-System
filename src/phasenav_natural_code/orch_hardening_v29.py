from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Sequence

TAU = 2.0 * math.pi
HARDENING_CONTRACT_ID = "PNCS_ORCHORBITAL_HARVEST_HARDENING_V0_29"
FOUNDATION_REPOSITORY = "AdrianLipa90/CIEL-Omega-ApokalypOS"
FOUNDATION_COMMIT = "aa0da54ef29a1f80dd0390427935342225388950"

ENTITY_PROJECTION_SCHEMA = "PNCS_ORCH_ENTITY_PROJECTION_V0_29"
PACKAGE_ADMISSION_SCHEMA = "PNCS_PACKAGE_ADMISSION_RECEIPT_V0_29"
SEMANTIC_ACTION_AUDIT_SCHEMA = "PNCS_SEMANTIC_ACTION_AUDIT_RECEIPT_V0_29"
LEAK_RECEIPT_SCHEMA = "PNCS_INERT_LEAK_RECEIPT_V0_29"
GEOMETRY_PROJECTION_SCHEMA = "PNCS_OPERATIONAL_GEOMETRY_PROJECTION_V0_29"

_PNCS_SHA_ID_RE = re.compile(r"^pncs:[a-z0-9-]+:sha256:[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

CHART_POINCARE = "POINCARE_OPERATIONAL"
CHART_BLOCH = "BLOCH_LOCAL_REDUCED"
CHART_KINDS = (CHART_POINCARE, CHART_BLOCH)


class OrchHardeningV29Error(ValueError):
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
            raise OrchHardeningV29Error("non-finite canonical value")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise OrchHardeningV29Error(f"unsupported canonical type: {type(value).__name__}")


def _typed_id(prefix: str, payload: object) -> str:
    raw = json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(raw).hexdigest()}"


def _finite(value: object, field: str) -> float:
    try:
        out = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise OrchHardeningV29Error(f"{field} must be finite") from exc
    if not math.isfinite(out):
        raise OrchHardeningV29Error(f"{field} must be finite")
    return out


def _nonnegative(value: object, field: str) -> float:
    out = _finite(value, field)
    if out < 0.0:
        raise OrchHardeningV29Error(f"{field} must be non-negative")
    return out


def _nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OrchHardeningV29Error(f"{field} must be a non-negative integer")
    return value


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OrchHardeningV29Error(f"{field} must be a non-empty string")
    return value


def _pncs_id(value: object, field: str, prefix: str | None = None) -> str:
    if not isinstance(value, str) or not _PNCS_SHA_ID_RE.fullmatch(value):
        raise OrchHardeningV29Error(f"{field} must be a typed PNCS SHA-256 ID")
    if prefix is not None and not value.startswith(prefix):
        raise OrchHardeningV29Error(f"{field} has wrong typed-ID prefix")
    return value


def _typed_links(values: Sequence[str], field: str) -> tuple[str, ...]:
    out = tuple(_pncs_id(v, field) for v in values)
    if len(set(out)) != len(out):
        raise OrchHardeningV29Error(f"{field} contains duplicate IDs")
    return out


def _phase(value: object) -> float:
    out = _finite(value, "phase")
    if out < 0.0 or out >= TAU:
        raise OrchHardeningV29Error("phase must be in [0,2pi)")
    return out


@dataclass(frozen=True, slots=True)
class EntityRecordProjection:
    canonical_id: str
    object_type: str
    lineage_id: str
    hierarchy_path_id: str
    definition_id: str
    definition_radical_binding_id: str
    radical_id: str
    kaku_ids: tuple[str, ...]
    sphere_id: str
    parent_sphere_id: str | None
    orbit_index: int
    phase: float
    w_ec: float
    w_zs: float
    w_rel: float
    w_red: float
    epistemic_status: str
    dependency_links: tuple[str, ...] = ()
    extra_provenance_links: tuple[str, ...] = ()
    semantic_mass: float | None = None
    mass_binding_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "canonical_id", _pncs_id(self.canonical_id, "canonical_id"))
        object_type = _nonempty(self.object_type, "object_type")
        if not _TOKEN_RE.fullmatch(object_type):
            raise OrchHardeningV29Error("object_type must be an uppercase typed token")
        object.__setattr__(self, "object_type", object_type)
        object.__setattr__(self, "lineage_id", _pncs_id(self.lineage_id, "lineage_id", "pncs:lineage:sha256:"))
        object.__setattr__(self, "hierarchy_path_id", _pncs_id(self.hierarchy_path_id, "hierarchy_path_id", "pncs:hierarchy-lineage:sha256:"))
        object.__setattr__(self, "definition_id", _pncs_id(self.definition_id, "definition_id", "pncs:def:sha256:"))
        object.__setattr__(
            self,
            "definition_radical_binding_id",
            _pncs_id(self.definition_radical_binding_id, "definition_radical_binding_id", "pncs:def-radical-binding:sha256:"),
        )
        object.__setattr__(self, "radical_id", _nonempty(self.radical_id, "radical_id"))
        kakus = tuple(_nonempty(v, "kaku_id") for v in self.kaku_ids)
        if not kakus:
            raise OrchHardeningV29Error("kaku_ids must contain at least one exact occurrence")
        object.__setattr__(self, "kaku_ids", kakus)
        object.__setattr__(self, "sphere_id", _nonempty(self.sphere_id, "sphere_id"))
        if self.parent_sphere_id is not None:
            object.__setattr__(self, "parent_sphere_id", _nonempty(self.parent_sphere_id, "parent_sphere_id"))
        if isinstance(self.orbit_index, bool) or not isinstance(self.orbit_index, int) or self.orbit_index < 0:
            raise OrchHardeningV29Error("orbit_index must be a non-negative integer")
        object.__setattr__(self, "phase", _phase(self.phase))
        for field in ("w_ec", "w_zs", "w_rel", "w_red"):
            object.__setattr__(self, field, _finite(getattr(self, field), field))
        object.__setattr__(self, "epistemic_status", _nonempty(self.epistemic_status, "epistemic_status"))
        object.__setattr__(self, "dependency_links", _typed_links(self.dependency_links, "dependency_links"))
        object.__setattr__(self, "extra_provenance_links", _typed_links(self.extra_provenance_links, "extra_provenance_links"))
        if (self.semantic_mass is None) != (self.mass_binding_id is None):
            raise OrchHardeningV29Error("semantic_mass and mass_binding_id must be supplied together")
        if self.semantic_mass is not None:
            object.__setattr__(self, "semantic_mass", _nonnegative(self.semantic_mass, "semantic_mass"))
            object.__setattr__(self, "mass_binding_id", _pncs_id(self.mass_binding_id, "mass_binding_id", "pncs:mass-binding:sha256:"))

    @property
    def winding_components(self) -> dict[str, float]:
        return {"w_ec": self.w_ec, "w_zs": self.w_zs, "w_rel": self.w_rel, "w_red": self.w_red}

    @property
    def provenance_links(self) -> tuple[str, ...]:
        base = (
            self.lineage_id,
            self.hierarchy_path_id,
            self.definition_radical_binding_id,
        )
        if self.mass_binding_id is not None:
            base = base + (self.mass_binding_id,)
        return tuple(dict.fromkeys(base + self.extra_provenance_links))

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": ENTITY_PROJECTION_SCHEMA,
            "contract_id": HARDENING_CONTRACT_ID,
            "canonical_id": self.canonical_id,
            "object_type": self.object_type,
            "lineage_id": self.lineage_id,
            "hierarchy_path_id": self.hierarchy_path_id,
            "definition_id": self.definition_id,
            "definition_radical_binding_id": self.definition_radical_binding_id,
            "radical_id": self.radical_id,
            "kaku_ids": list(self.kaku_ids),
            "sphere_id": self.sphere_id,
            "parent_sphere_id": self.parent_sphere_id,
            "orbit_index": self.orbit_index,
            "phase": self.phase,
            "winding_components": self.winding_components,
            "epistemic_status": self.epistemic_status,
            "dependency_links": list(self.dependency_links),
            "provenance_links": list(self.provenance_links),
            "semantic_mass": self.semantic_mass,
            "mass_binding_id": self.mass_binding_id,
            "identity_authority": False,
            "routing_authority": False,
            "effect_authority": False,
        }

    @property
    def projection_id(self) -> str:
        return _typed_id("pncs:entity-projection", self.payload)


@dataclass(frozen=True, slots=True)
class PackageEvidenceRefs:
    schema_receipt_id: str | None
    test_receipt_id: str | None
    metrics_receipt_id: str | None
    replay_receipt_id: str | None

    def __post_init__(self) -> None:
        for field in ("schema_receipt_id", "test_receipt_id", "metrics_receipt_id", "replay_receipt_id"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _pncs_id(value, field))

    @property
    def missing(self) -> tuple[str, ...]:
        pairs = (
            ("SCHEMA", self.schema_receipt_id),
            ("TESTS", self.test_receipt_id),
            ("METRICS", self.metrics_receipt_id),
            ("REPLAYABILITY", self.replay_receipt_id),
        )
        return tuple(name for name, value in pairs if value is None)

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema_receipt_id": self.schema_receipt_id,
            "test_receipt_id": self.test_receipt_id,
            "metrics_receipt_id": self.metrics_receipt_id,
            "replay_receipt_id": self.replay_receipt_id,
        }


@dataclass(frozen=True, slots=True)
class PackageAdmissionReceipt:
    package_id: str
    evidence: PackageEvidenceRefs

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_id", _pncs_id(self.package_id, "package_id"))
        if not isinstance(self.evidence, PackageEvidenceRefs):
            raise OrchHardeningV29Error("evidence must be PackageEvidenceRefs")

    @property
    def admitted(self) -> bool:
        return not self.evidence.missing

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": PACKAGE_ADMISSION_SCHEMA,
            "contract_id": HARDENING_CONTRACT_ID,
            "package_id": self.package_id,
            "evidence": self.evidence.payload,
            "required_evidence": ["SCHEMA", "TESTS", "METRICS", "REPLAYABILITY"],
            "missing_evidence": list(self.evidence.missing),
            "admitted": self.admitted,
            "routing_authority": False,
            "effect_authority": False,
        }

    @property
    def admission_id(self) -> str:
        return _typed_id("pncs:package-admission", self.payload)


def evaluate_package_admission(package_id: str, evidence: PackageEvidenceRefs) -> PackageAdmissionReceipt:
    return PackageAdmissionReceipt(package_id=package_id, evidence=evidence)


@dataclass(frozen=True, slots=True)
class SemanticActionWeights:
    weight_path: float
    weight_phase: float
    weight_relational_defect: float
    weight_truth_struct: float
    weight_truth_audit: float

    def __post_init__(self) -> None:
        for field in (
            "weight_path",
            "weight_phase",
            "weight_relational_defect",
            "weight_truth_struct",
            "weight_truth_audit",
        ):
            object.__setattr__(self, field, _nonnegative(getattr(self, field), field))

    @property
    def payload(self) -> dict[str, float]:
        return {
            "weight_path": self.weight_path,
            "weight_phase": self.weight_phase,
            "weight_relational_defect": self.weight_relational_defect,
            "weight_truth_struct": self.weight_truth_struct,
            "weight_truth_audit": self.weight_truth_audit,
        }


@dataclass(frozen=True, slots=True)
class FactAuditCounts:
    fact_count: int
    false_count: int = 0
    unmarked_count: int = 0
    omit_count: int = 0
    hallucination_count: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.fact_count, bool) or not isinstance(self.fact_count, int) or self.fact_count < 1:
            raise OrchHardeningV29Error("fact_count must be a positive integer")
        for field in ("false_count", "unmarked_count", "omit_count", "hallucination_count"):
            value = _nonnegative_int(getattr(self, field), field)
            if value > self.fact_count:
                raise OrchHardeningV29Error(f"{field} cannot exceed fact_count")

    @property
    def audit_truth_penalty(self) -> float:
        return (
            self.false_count
            + self.unmarked_count
            + self.omit_count
            + self.hallucination_count
        ) / self.fact_count

    @property
    def payload(self) -> dict[str, int]:
        return {
            "fact_count": self.fact_count,
            "false_count": self.false_count,
            "unmarked_count": self.unmarked_count,
            "omit_count": self.omit_count,
            "hallucination_count": self.hallucination_count,
        }


@dataclass(frozen=True, slots=True)
class SemanticActionAuditReceipt:
    source_artifact_id: str
    path_length: float
    phase_transport_cost: float
    relational_defect: float
    structural_truth_penalty: float
    counts: FactAuditCounts
    weights: SemanticActionWeights

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_artifact_id", _pncs_id(self.source_artifact_id, "source_artifact_id"))
        for field in ("path_length", "phase_transport_cost", "relational_defect", "structural_truth_penalty"):
            object.__setattr__(self, field, _nonnegative(getattr(self, field), field))
        if not isinstance(self.counts, FactAuditCounts):
            raise OrchHardeningV29Error("counts must be FactAuditCounts")
        if not isinstance(self.weights, SemanticActionWeights):
            raise OrchHardeningV29Error("weights must be SemanticActionWeights")

    @property
    def online_action(self) -> float:
        return (
            self.weights.weight_path * self.path_length
            + self.weights.weight_phase * self.phase_transport_cost
            + self.weights.weight_relational_defect * self.relational_defect
            + self.weights.weight_truth_struct * self.structural_truth_penalty
        )

    @property
    def full_action(self) -> float:
        return self.online_action + self.weights.weight_truth_audit * self.counts.audit_truth_penalty

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": SEMANTIC_ACTION_AUDIT_SCHEMA,
            "contract_id": HARDENING_CONTRACT_ID,
            "source_artifact_id": self.source_artifact_id,
            "measurements": {
                "path_length": self.path_length,
                "phase_transport_cost": self.phase_transport_cost,
                "relational_defect": self.relational_defect,
                "structural_truth_penalty": self.structural_truth_penalty,
            },
            "counts": self.counts.payload,
            "weights": self.weights.payload,
            "audit_truth_penalty": self.counts.audit_truth_penalty,
            "online_action": self.online_action,
            "full_action": self.full_action,
            "measurement_only": True,
            "routing_feedback_opened": False,
            "effect_authority": False,
        }

    @property
    def audit_id(self) -> str:
        return _typed_id("pncs:semantic-action-audit", self.payload)


@dataclass(frozen=True, slots=True)
class InertLeakReceipt:
    source_state_id: str
    sphere_id: str
    parent_sphere_id: str | None
    holonomic_defect_real: float
    holonomic_defect_imag: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_state_id", _pncs_id(self.source_state_id, "source_state_id"))
        object.__setattr__(self, "sphere_id", _nonempty(self.sphere_id, "sphere_id"))
        if self.parent_sphere_id is not None:
            object.__setattr__(self, "parent_sphere_id", _nonempty(self.parent_sphere_id, "parent_sphere_id"))
        object.__setattr__(self, "holonomic_defect_real", _finite(self.holonomic_defect_real, "holonomic_defect_real"))
        object.__setattr__(self, "holonomic_defect_imag", _finite(self.holonomic_defect_imag, "holonomic_defect_imag"))

    @property
    def epsilon_real(self) -> float:
        return -self.holonomic_defect_real

    @property
    def epsilon_imag(self) -> float:
        return -self.holonomic_defect_imag

    @property
    def leak_amplitude(self) -> float:
        return math.hypot(self.epsilon_real, self.epsilon_imag)

    @property
    def leak_phase(self) -> float:
        if self.leak_amplitude == 0.0:
            return 0.0
        return math.atan2(self.epsilon_imag, self.epsilon_real) % TAU

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": LEAK_RECEIPT_SCHEMA,
            "contract_id": HARDENING_CONTRACT_ID,
            "source_state_id": self.source_state_id,
            "sphere_id": self.sphere_id,
            "parent_sphere_id": self.parent_sphere_id,
            "holonomic_defect": [self.holonomic_defect_real, self.holonomic_defect_imag],
            "epsilon": [self.epsilon_real, self.epsilon_imag],
            "leak_amplitude": self.leak_amplitude,
            "leak_phase": self.leak_phase,
            "propagation_opened": False,
            "parent_mutation_opened": False,
            "split_merge_elevate_opened": False,
            "routing_feedback_opened": False,
        }

    @property
    def leak_receipt_id(self) -> str:
        return _typed_id("pncs:inert-leak", self.payload)


@dataclass(frozen=True, slots=True)
class OperationalGeometryProjection:
    source_state_id: str
    source_entity_projection_id: str
    chart_kind: str
    coordinates: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_state_id", _pncs_id(self.source_state_id, "source_state_id"))
        object.__setattr__(
            self,
            "source_entity_projection_id",
            _pncs_id(self.source_entity_projection_id, "source_entity_projection_id", "pncs:entity-projection:sha256:"),
        )
        if self.chart_kind not in CHART_KINDS:
            raise OrchHardeningV29Error("unsupported operational chart kind")
        coords = tuple(_finite(v, "coordinates") for v in self.coordinates)
        expected = 2 if self.chart_kind == CHART_POINCARE else 3
        if len(coords) != expected:
            raise OrchHardeningV29Error(f"{self.chart_kind} requires exactly {expected} coordinates")
        radius_sq = sum(v * v for v in coords)
        if self.chart_kind == CHART_POINCARE and radius_sq >= 1.0:
            raise OrchHardeningV29Error("Poincare operational coordinates must lie inside the unit disk")
        if self.chart_kind == CHART_BLOCH and radius_sq > 1.0:
            raise OrchHardeningV29Error("Bloch local coordinates must lie inside or on the unit ball")
        object.__setattr__(self, "coordinates", coords)

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": GEOMETRY_PROJECTION_SCHEMA,
            "contract_id": HARDENING_CONTRACT_ID,
            "source_state_id": self.source_state_id,
            "source_entity_projection_id": self.source_entity_projection_id,
            "base_relational_manifold": "M_rel",
            "geometric_anchor": "projective_Hilbert_Kahler_Fubini_Study",
            "chart_kind": self.chart_kind,
            "coordinates": list(self.coordinates),
            "chart_role": "OPERATIONAL_PROJECTION" if self.chart_kind == CHART_POINCARE else "LOCAL_REDUCED_INSPECTION",
            "semantic_identity_authority": False,
            "routing_authority": False,
            "renderer_authority": False,
        }

    @property
    def projection_id(self) -> str:
        return _typed_id("pncs:geometry-projection", self.payload)
