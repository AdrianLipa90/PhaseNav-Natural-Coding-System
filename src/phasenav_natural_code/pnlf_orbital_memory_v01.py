from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import math
import re
from typing import Any, Iterable, Mapping, Sequence


PNLF_SCHEMA = "PNLF_ORBITAL_MEMORY_V0_1"
CHECKPOINT_SCHEMA = "PNLF_STATE_MEMORY_CHECKPOINT_V0_1"
LIMINAL_SCHEMA = "PNLF_LIMINAL_SEGMENT_REVISION_V0_1"
TAU_FRAME_SCHEMA = "PNLF_TAU_FRAME_V0_1"

ORBITAL_BANDS = frozenset(f"O{i}" for i in range(9))
M_LAYERS = frozenset({"M0", "M1", "M2", "M3", "M4", "M5", "M6.1a", "M7", "M8"})
RESOLUTION_STATES = frozenset({"OPEN", "ADMITTED", "REJECTED"})
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CHECKPOINT_ID_RE = re.compile(r"^pnlf:checkpoint:sha256:[0-9a-f]{64}$")


class PNLFOrbitalMemoryError(ValueError):
    pass


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise PNLFOrbitalMemoryError("non-finite value cannot enter canonical PNLF JSON")
        return value
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, Mapping):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    raise PNLFOrbitalMemoryError(f"unsupported canonical value type: {type(value).__name__}")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _finite(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise PNLFOrbitalMemoryError(f"{field} must be finite") from exc
    if not math.isfinite(out):
        raise PNLFOrbitalMemoryError(f"{field} must be finite")
    return out


def _non_negative(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out < 0.0:
        raise PNLFOrbitalMemoryError(f"{field} must be non-negative")
    return out


def _positive(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out <= 0.0:
        raise PNLFOrbitalMemoryError(f"{field} must be positive")
    return out


def _require_text(value: Any, field: str) -> str:
    out = str(value or "").strip()
    if not out:
        raise PNLFOrbitalMemoryError(f"{field} must be non-empty")
    return out


def _digest(value: Any, field: str) -> str:
    out = str(value or "")
    if not _DIGEST_RE.fullmatch(out):
        raise PNLFOrbitalMemoryError(f"{field} must be lowercase SHA-256")
    return out


def _checkpoint_id(value: Any, field: str) -> str:
    out = str(value or "")
    if not _CHECKPOINT_ID_RE.fullmatch(out):
        raise PNLFOrbitalMemoryError(f"{field} must be a PNLF checkpoint ID")
    return out


def _layers(values: Iterable[str]) -> tuple[str, ...]:
    out = tuple(sorted(set(str(v) for v in values)))
    if not out:
        raise PNLFOrbitalMemoryError("at least one active M-layer is required")
    unknown = sorted(set(out) - M_LAYERS)
    if unknown:
        raise PNLFOrbitalMemoryError(f"unknown PNLF M-layer(s): {unknown}")
    return out


def _events(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(_digest(v, "event_commitment") for v in values)


@dataclass(frozen=True)
class OrbitalState:
    attractor_id: str
    orbital_band: str
    r_phase: float
    phase: float
    E_bind: float
    L_phase: float
    semantic_mass: float
    orbit_period: float
    winding: float
    proper_time: float
    memory_affinity: float
    mass_model_id: str
    orbit_quantizer_id: str
    proper_time_model_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "attractor_id", _require_text(self.attractor_id, "attractor_id"))
        band = str(self.orbital_band)
        if band not in ORBITAL_BANDS:
            raise PNLFOrbitalMemoryError(f"orbital_band must be one of {sorted(ORBITAL_BANDS)}")
        object.__setattr__(self, "orbital_band", band)
        r_phase = _non_negative(self.r_phase, "r_phase")
        if r_phase > math.pi:
            raise PNLFOrbitalMemoryError("r_phase must be a circular phase distance in [0,pi]")
        object.__setattr__(self, "r_phase", r_phase)
        object.__setattr__(self, "phase", _finite(self.phase, "phase") % (2.0 * math.pi))
        object.__setattr__(self, "E_bind", _finite(self.E_bind, "E_bind"))
        object.__setattr__(self, "L_phase", _finite(self.L_phase, "L_phase"))
        object.__setattr__(self, "semantic_mass", _non_negative(self.semantic_mass, "semantic_mass"))
        object.__setattr__(self, "orbit_period", _positive(self.orbit_period, "orbit_period"))
        object.__setattr__(self, "winding", _finite(self.winding, "winding"))
        object.__setattr__(self, "proper_time", _non_negative(self.proper_time, "proper_time"))
        affinity = _finite(self.memory_affinity, "memory_affinity")
        if not 0.0 <= affinity <= 1.0:
            raise PNLFOrbitalMemoryError("memory_affinity must be in [0,1]")
        object.__setattr__(self, "memory_affinity", affinity)
        object.__setattr__(self, "mass_model_id", _require_text(self.mass_model_id, "mass_model_id"))
        object.__setattr__(self, "orbit_quantizer_id", _require_text(self.orbit_quantizer_id, "orbit_quantizer_id"))
        object.__setattr__(self, "proper_time_model_id", _require_text(self.proper_time_model_id, "proper_time_model_id"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "attractor_id": self.attractor_id,
            "orbital_band": self.orbital_band,
            "r_phase": self.r_phase,
            "phase": self.phase,
            "E_bind": self.E_bind,
            "L_phase": self.L_phase,
            "semantic_mass": self.semantic_mass,
            "orbit_period": self.orbit_period,
            "winding": self.winding,
            "proper_time": self.proper_time,
            "memory_affinity": self.memory_affinity,
            "mass_model_id": self.mass_model_id,
            "orbit_quantizer_id": self.orbit_quantizer_id,
            "proper_time_model_id": self.proper_time_model_id,
        }


@dataclass(frozen=True)
class PNLFHeader:
    file_id: str
    object_id: str
    genesis_anchor: str
    basis_id: str
    schema_binding: str
    storage_profile: str
    mass_model_id: str
    orbit_quantizer_id: str
    proper_time_model_id: str
    t36_basis_id: str
    lineage_head: str | None = None

    def __post_init__(self) -> None:
        for field in (
            "file_id",
            "object_id",
            "basis_id",
            "schema_binding",
            "storage_profile",
            "mass_model_id",
            "orbit_quantizer_id",
            "proper_time_model_id",
            "t36_basis_id",
        ):
            object.__setattr__(self, field, _require_text(getattr(self, field), field))
        object.__setattr__(self, "genesis_anchor", _digest(self.genesis_anchor, "genesis_anchor"))
        if self.lineage_head is not None:
            object.__setattr__(self, "lineage_head", _checkpoint_id(self.lineage_head, "lineage_head"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": PNLF_SCHEMA,
            "file_id": self.file_id,
            "object_id": self.object_id,
            "genesis_anchor": self.genesis_anchor,
            "basis_id": self.basis_id,
            "schema_binding": self.schema_binding,
            "storage_profile": self.storage_profile,
            "mass_model_id": self.mass_model_id,
            "orbit_quantizer_id": self.orbit_quantizer_id,
            "proper_time_model_id": self.proper_time_model_id,
            "t36_basis_id": self.t36_basis_id,
            "lineage_head": self.lineage_head,
            "runtime_execution_authority": False,
            "canon_write_authority": False,
        }

    def with_lineage_head(self, checkpoint_id: str) -> "PNLFHeader":
        return replace(self, lineage_head=_checkpoint_id(checkpoint_id, "lineage_head"))


@dataclass(frozen=True)
class StateMemoryCheckpoint:
    checkpoint_object_id: str
    object_id: str
    tau: float
    content_commitment: str
    predecessor_checkpoint_id: str | None
    active_m_layers: tuple[str, ...]
    orbital_state: OrbitalState
    state_commitment: str
    t36_witness_sha256: str
    reduction_witness_sha256: str
    consolidation_witness_sha256: str
    relation_braid_commitment: str
    admission_state: str = "ADMITTED"

    def __post_init__(self) -> None:
        object.__setattr__(self, "checkpoint_object_id", _checkpoint_id(self.checkpoint_object_id, "checkpoint_object_id"))
        object.__setattr__(self, "object_id", _require_text(self.object_id, "object_id"))
        object.__setattr__(self, "tau", _non_negative(self.tau, "tau"))
        object.__setattr__(self, "content_commitment", _digest(self.content_commitment, "content_commitment"))
        if self.predecessor_checkpoint_id is not None:
            object.__setattr__(self, "predecessor_checkpoint_id", _checkpoint_id(self.predecessor_checkpoint_id, "predecessor_checkpoint_id"))
        object.__setattr__(self, "active_m_layers", _layers(self.active_m_layers))
        if not isinstance(self.orbital_state, OrbitalState):
            raise PNLFOrbitalMemoryError("orbital_state must be OrbitalState")
        if abs(self.orbital_state.proper_time - self.tau) > 1e-12:
            raise PNLFOrbitalMemoryError("checkpoint tau must equal orbital_state.proper_time")
        object.__setattr__(self, "state_commitment", _digest(self.state_commitment, "state_commitment"))
        object.__setattr__(self, "t36_witness_sha256", _digest(self.t36_witness_sha256, "t36_witness_sha256"))
        object.__setattr__(self, "reduction_witness_sha256", _digest(self.reduction_witness_sha256, "reduction_witness_sha256"))
        object.__setattr__(self, "consolidation_witness_sha256", _digest(self.consolidation_witness_sha256, "consolidation_witness_sha256"))
        object.__setattr__(self, "relation_braid_commitment", _digest(self.relation_braid_commitment, "relation_braid_commitment"))
        if self.admission_state != "ADMITTED":
            raise PNLFOrbitalMemoryError("State Memory checkpoint must be ADMITTED")
        body = _checkpoint_body(self)
        expected_state = _sha256(body)
        if _checkpoint_id_from_body(body) != self.checkpoint_object_id:
            raise PNLFOrbitalMemoryError("checkpoint_object_id does not match canonical checkpoint content")
        if expected_state != self.state_commitment:
            raise PNLFOrbitalMemoryError("state_commitment does not match canonical checkpoint content")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": CHECKPOINT_SCHEMA,
            "checkpoint_object_id": self.checkpoint_object_id,
            "object_id": self.object_id,
            "tau": self.tau,
            "content_commitment": self.content_commitment,
            "predecessor_checkpoint_id": self.predecessor_checkpoint_id,
            "active_m_layers": list(self.active_m_layers),
            "orbital_state": self.orbital_state.to_dict(),
            "state_commitment": self.state_commitment,
            "t36_witness_sha256": self.t36_witness_sha256,
            "reduction_witness_sha256": self.reduction_witness_sha256,
            "consolidation_witness_sha256": self.consolidation_witness_sha256,
            "relation_braid_commitment": self.relation_braid_commitment,
            "admission_state": self.admission_state,
            "runtime_execution_authority": False,
            "canon_write_authority": False,
        }


def _checkpoint_body(checkpoint: StateMemoryCheckpoint) -> dict[str, Any]:
    return {
        "schema": CHECKPOINT_SCHEMA,
        "object_id": checkpoint.object_id,
        "tau": checkpoint.tau,
        "content_commitment": checkpoint.content_commitment,
        "predecessor_checkpoint_id": checkpoint.predecessor_checkpoint_id,
        "active_m_layers": list(checkpoint.active_m_layers),
        "orbital_state": checkpoint.orbital_state.to_dict(),
        "t36_witness_sha256": checkpoint.t36_witness_sha256,
        "reduction_witness_sha256": checkpoint.reduction_witness_sha256,
        "consolidation_witness_sha256": checkpoint.consolidation_witness_sha256,
        "relation_braid_commitment": checkpoint.relation_braid_commitment,
        "admission_state": "ADMITTED",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
    }


def _checkpoint_id_from_body(body: Mapping[str, Any]) -> str:
    return f"pnlf:checkpoint:sha256:{_sha256(body)}"


def build_state_checkpoint(
    *,
    object_id: str,
    tau: float,
    content_commitment: str,
    predecessor_checkpoint_id: str | None,
    active_m_layers: Sequence[str],
    orbital_state: OrbitalState,
    t36_witness_sha256: str,
    reduction_witness_sha256: str,
    consolidation_witness_sha256: str,
    relation_braid_commitment: str,
) -> StateMemoryCheckpoint:
    proto = object.__new__(StateMemoryCheckpoint)
    object.__setattr__(proto, "checkpoint_object_id", "pnlf:checkpoint:sha256:" + "0" * 64)
    object.__setattr__(proto, "object_id", _require_text(object_id, "object_id"))
    object.__setattr__(proto, "tau", _non_negative(tau, "tau"))
    object.__setattr__(proto, "content_commitment", _digest(content_commitment, "content_commitment"))
    object.__setattr__(proto, "predecessor_checkpoint_id", None if predecessor_checkpoint_id is None else _checkpoint_id(predecessor_checkpoint_id, "predecessor_checkpoint_id"))
    object.__setattr__(proto, "active_m_layers", _layers(active_m_layers))
    if not isinstance(orbital_state, OrbitalState):
        raise PNLFOrbitalMemoryError("orbital_state must be OrbitalState")
    if abs(orbital_state.proper_time - float(tau)) > 1e-12:
        raise PNLFOrbitalMemoryError("checkpoint tau must equal orbital_state.proper_time")
    object.__setattr__(proto, "orbital_state", orbital_state)
    object.__setattr__(proto, "state_commitment", "0" * 64)
    object.__setattr__(proto, "t36_witness_sha256", _digest(t36_witness_sha256, "t36_witness_sha256"))
    object.__setattr__(proto, "reduction_witness_sha256", _digest(reduction_witness_sha256, "reduction_witness_sha256"))
    object.__setattr__(proto, "consolidation_witness_sha256", _digest(consolidation_witness_sha256, "consolidation_witness_sha256"))
    object.__setattr__(proto, "relation_braid_commitment", _digest(relation_braid_commitment, "relation_braid_commitment"))
    object.__setattr__(proto, "admission_state", "ADMITTED")
    body = _checkpoint_body(proto)
    digest = _sha256(body)
    return StateMemoryCheckpoint(
        checkpoint_object_id=f"pnlf:checkpoint:sha256:{digest}",
        object_id=proto.object_id,
        tau=proto.tau,
        content_commitment=proto.content_commitment,
        predecessor_checkpoint_id=proto.predecessor_checkpoint_id,
        active_m_layers=proto.active_m_layers,
        orbital_state=proto.orbital_state,
        state_commitment=digest,
        t36_witness_sha256=proto.t36_witness_sha256,
        reduction_witness_sha256=proto.reduction_witness_sha256,
        consolidation_witness_sha256=proto.consolidation_witness_sha256,
        relation_braid_commitment=proto.relation_braid_commitment,
    )


@dataclass(frozen=True)
class LiminalSegmentRevision:
    segment_id: str
    segment_commitment: str
    previous_segment_commitment: str | None
    object_id: str
    pilot_l_checkpoint_id: str
    pilot_r_checkpoint_id: str | None
    tau_start: float
    tau_cursor: float
    tau_end: float | None
    active_m_layers: tuple[str, ...]
    relation_braid_commitment: str
    trajectory_commitment: str
    modulation_commitment: str
    t36_trajectory_commitment: str
    event_commitments: tuple[str, ...]
    source_orbital_state: OrbitalState
    target_orbital_state: OrbitalState | None
    epistemic_state: str
    resolution_state: str
    resolution_witness_sha256: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "segment_id", _require_text(self.segment_id, "segment_id"))
        object.__setattr__(self, "segment_commitment", _digest(self.segment_commitment, "segment_commitment"))
        if self.previous_segment_commitment is not None:
            object.__setattr__(self, "previous_segment_commitment", _digest(self.previous_segment_commitment, "previous_segment_commitment"))
        object.__setattr__(self, "object_id", _require_text(self.object_id, "object_id"))
        object.__setattr__(self, "pilot_l_checkpoint_id", _checkpoint_id(self.pilot_l_checkpoint_id, "pilot_l_checkpoint_id"))
        if self.pilot_r_checkpoint_id is not None:
            object.__setattr__(self, "pilot_r_checkpoint_id", _checkpoint_id(self.pilot_r_checkpoint_id, "pilot_r_checkpoint_id"))
        start = _non_negative(self.tau_start, "tau_start")
        cursor = _non_negative(self.tau_cursor, "tau_cursor")
        if cursor < start:
            raise PNLFOrbitalMemoryError("tau_cursor must be >= tau_start")
        object.__setattr__(self, "tau_start", start)
        object.__setattr__(self, "tau_cursor", cursor)
        if self.tau_end is not None:
            object.__setattr__(self, "tau_end", _non_negative(self.tau_end, "tau_end"))
        object.__setattr__(self, "active_m_layers", _layers(self.active_m_layers))
        for field in (
            "relation_braid_commitment",
            "trajectory_commitment",
            "modulation_commitment",
            "t36_trajectory_commitment",
        ):
            object.__setattr__(self, field, _digest(getattr(self, field), field))
        object.__setattr__(self, "event_commitments", _events(self.event_commitments))
        if not isinstance(self.source_orbital_state, OrbitalState):
            raise PNLFOrbitalMemoryError("source_orbital_state must be OrbitalState")
        if self.target_orbital_state is not None and not isinstance(self.target_orbital_state, OrbitalState):
            raise PNLFOrbitalMemoryError("target_orbital_state must be OrbitalState or None")
        object.__setattr__(self, "epistemic_state", _require_text(self.epistemic_state, "epistemic_state"))
        state = str(self.resolution_state).upper()
        if state not in RESOLUTION_STATES:
            raise PNLFOrbitalMemoryError(f"resolution_state must be one of {sorted(RESOLUTION_STATES)}")
        object.__setattr__(self, "resolution_state", state)
        if state == "OPEN":
            if self.tau_end is not None or self.pilot_r_checkpoint_id is not None or self.resolution_witness_sha256 is not None:
                raise PNLFOrbitalMemoryError("OPEN liminal segment cannot have tau_end, right pilot, or resolution witness")
            if self.target_orbital_state is not None:
                raise PNLFOrbitalMemoryError("OPEN liminal segment cannot claim admitted target orbital state")
        else:
            if self.tau_end is None or abs(self.tau_end - self.tau_cursor) > 1e-12:
                raise PNLFOrbitalMemoryError("closed liminal segment requires tau_end == tau_cursor")
            if self.resolution_witness_sha256 is None:
                raise PNLFOrbitalMemoryError("closed liminal segment requires resolution witness")
            object.__setattr__(self, "resolution_witness_sha256", _digest(self.resolution_witness_sha256, "resolution_witness_sha256"))
            if state == "ADMITTED" and (self.pilot_r_checkpoint_id is None or self.target_orbital_state is None):
                raise PNLFOrbitalMemoryError("ADMITTED liminal segment requires right pilot and target orbital state")
            if state == "REJECTED" and (self.pilot_r_checkpoint_id is not None or self.target_orbital_state is not None):
                raise PNLFOrbitalMemoryError("REJECTED liminal segment cannot bind admitted right state")
        if _sha256(_segment_body(self)) != self.segment_commitment:
            raise PNLFOrbitalMemoryError("segment_commitment does not match canonical liminal revision")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": LIMINAL_SCHEMA,
            **_segment_body(self),
            "segment_commitment": self.segment_commitment,
        }


def _segment_body(segment: LiminalSegmentRevision) -> dict[str, Any]:
    return {
        "segment_id": segment.segment_id,
        "previous_segment_commitment": segment.previous_segment_commitment,
        "object_id": segment.object_id,
        "pilot_l_checkpoint_id": segment.pilot_l_checkpoint_id,
        "pilot_r_checkpoint_id": segment.pilot_r_checkpoint_id,
        "tau_start": segment.tau_start,
        "tau_cursor": segment.tau_cursor,
        "tau_end": segment.tau_end,
        "active_m_layers": list(segment.active_m_layers),
        "relation_braid_commitment": segment.relation_braid_commitment,
        "trajectory_commitment": segment.trajectory_commitment,
        "modulation_commitment": segment.modulation_commitment,
        "t36_trajectory_commitment": segment.t36_trajectory_commitment,
        "event_commitments": list(segment.event_commitments),
        "source_orbital_state": segment.source_orbital_state.to_dict(),
        "target_orbital_state": None if segment.target_orbital_state is None else segment.target_orbital_state.to_dict(),
        "epistemic_state": segment.epistemic_state,
        "resolution_state": segment.resolution_state,
        "resolution_witness_sha256": segment.resolution_witness_sha256,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
    }


def _make_segment(**kwargs: Any) -> LiminalSegmentRevision:
    proto = object.__new__(LiminalSegmentRevision)
    for key, value in kwargs.items():
        object.__setattr__(proto, key, value)
    body = _segment_body(proto)
    return LiminalSegmentRevision(segment_commitment=_sha256(body), **kwargs)


def open_liminal_segment(
    *,
    segment_id: str,
    source_checkpoint: StateMemoryCheckpoint,
    tau_start: float,
    active_m_layers: Sequence[str],
    relation_braid_commitment: str,
    trajectory_commitment: str,
    modulation_commitment: str,
    t36_trajectory_commitment: str,
    event_commitments: Sequence[str] = (),
    epistemic_state: str = "CHYBA",
) -> LiminalSegmentRevision:
    if not isinstance(source_checkpoint, StateMemoryCheckpoint):
        raise PNLFOrbitalMemoryError("source_checkpoint must be admitted StateMemoryCheckpoint")
    start = _non_negative(tau_start, "tau_start")
    if start < source_checkpoint.tau:
        raise PNLFOrbitalMemoryError("liminal tau_start cannot precede source checkpoint tau")
    return _make_segment(
        segment_id=_require_text(segment_id, "segment_id"),
        previous_segment_commitment=None,
        object_id=source_checkpoint.object_id,
        pilot_l_checkpoint_id=source_checkpoint.checkpoint_object_id,
        pilot_r_checkpoint_id=None,
        tau_start=start,
        tau_cursor=start,
        tau_end=None,
        active_m_layers=_layers(active_m_layers),
        relation_braid_commitment=_digest(relation_braid_commitment, "relation_braid_commitment"),
        trajectory_commitment=_digest(trajectory_commitment, "trajectory_commitment"),
        modulation_commitment=_digest(modulation_commitment, "modulation_commitment"),
        t36_trajectory_commitment=_digest(t36_trajectory_commitment, "t36_trajectory_commitment"),
        event_commitments=_events(event_commitments),
        source_orbital_state=source_checkpoint.orbital_state,
        target_orbital_state=None,
        epistemic_state=_require_text(epistemic_state, "epistemic_state"),
        resolution_state="OPEN",
        resolution_witness_sha256=None,
    )


def advance_liminal_segment(
    segment: LiminalSegmentRevision,
    *,
    tau_cursor: float,
    trajectory_commitment: str,
    t36_trajectory_commitment: str,
    event_commitment: str | None = None,
    modulation_commitment: str | None = None,
    active_m_layers: Sequence[str] | None = None,
) -> LiminalSegmentRevision:
    if not isinstance(segment, LiminalSegmentRevision) or segment.resolution_state != "OPEN":
        raise PNLFOrbitalMemoryError("LIMINAL_ADVANCE requires OPEN liminal segment")
    cursor = _non_negative(tau_cursor, "tau_cursor")
    if cursor <= segment.tau_cursor:
        raise PNLFOrbitalMemoryError("LIMINAL_ADVANCE requires strictly increasing proper time")
    events = list(segment.event_commitments)
    if event_commitment is not None:
        events.append(_digest(event_commitment, "event_commitment"))
    return _make_segment(
        segment_id=segment.segment_id,
        previous_segment_commitment=segment.segment_commitment,
        object_id=segment.object_id,
        pilot_l_checkpoint_id=segment.pilot_l_checkpoint_id,
        pilot_r_checkpoint_id=None,
        tau_start=segment.tau_start,
        tau_cursor=cursor,
        tau_end=None,
        active_m_layers=segment.active_m_layers if active_m_layers is None else _layers(active_m_layers),
        relation_braid_commitment=segment.relation_braid_commitment,
        trajectory_commitment=_digest(trajectory_commitment, "trajectory_commitment"),
        modulation_commitment=segment.modulation_commitment if modulation_commitment is None else _digest(modulation_commitment, "modulation_commitment"),
        t36_trajectory_commitment=_digest(t36_trajectory_commitment, "t36_trajectory_commitment"),
        event_commitments=tuple(events),
        source_orbital_state=segment.source_orbital_state,
        target_orbital_state=None,
        epistemic_state=segment.epistemic_state,
        resolution_state="OPEN",
        resolution_witness_sha256=None,
    )


def admit_liminal_segment(
    segment: LiminalSegmentRevision,
    *,
    right_checkpoint: StateMemoryCheckpoint,
    resolution_witness_sha256: str,
) -> LiminalSegmentRevision:
    if not isinstance(segment, LiminalSegmentRevision) or segment.resolution_state != "OPEN":
        raise PNLFOrbitalMemoryError("STATE_COMMIT requires OPEN liminal segment")
    if not isinstance(right_checkpoint, StateMemoryCheckpoint):
        raise PNLFOrbitalMemoryError("right_checkpoint must be admitted StateMemoryCheckpoint")
    if right_checkpoint.object_id != segment.object_id:
        raise PNLFOrbitalMemoryError("right checkpoint object_id does not match liminal segment")
    if right_checkpoint.predecessor_checkpoint_id != segment.pilot_l_checkpoint_id:
        raise PNLFOrbitalMemoryError("right checkpoint must descend from the segment left pilot")
    if abs(right_checkpoint.tau - segment.tau_cursor) > 1e-12:
        raise PNLFOrbitalMemoryError("STATE_COMMIT requires right checkpoint tau == current liminal tau_cursor")
    return _make_segment(
        segment_id=segment.segment_id,
        previous_segment_commitment=segment.segment_commitment,
        object_id=segment.object_id,
        pilot_l_checkpoint_id=segment.pilot_l_checkpoint_id,
        pilot_r_checkpoint_id=right_checkpoint.checkpoint_object_id,
        tau_start=segment.tau_start,
        tau_cursor=right_checkpoint.tau,
        tau_end=right_checkpoint.tau,
        active_m_layers=segment.active_m_layers,
        relation_braid_commitment=segment.relation_braid_commitment,
        trajectory_commitment=segment.trajectory_commitment,
        modulation_commitment=segment.modulation_commitment,
        t36_trajectory_commitment=segment.t36_trajectory_commitment,
        event_commitments=segment.event_commitments,
        source_orbital_state=segment.source_orbital_state,
        target_orbital_state=right_checkpoint.orbital_state,
        epistemic_state=segment.epistemic_state,
        resolution_state="ADMITTED",
        resolution_witness_sha256=_digest(resolution_witness_sha256, "resolution_witness_sha256"),
    )


def reject_liminal_segment(
    segment: LiminalSegmentRevision,
    *,
    resolution_witness_sha256: str,
) -> LiminalSegmentRevision:
    if not isinstance(segment, LiminalSegmentRevision) or segment.resolution_state != "OPEN":
        raise PNLFOrbitalMemoryError("rejection requires OPEN liminal segment")
    return _make_segment(
        segment_id=segment.segment_id,
        previous_segment_commitment=segment.segment_commitment,
        object_id=segment.object_id,
        pilot_l_checkpoint_id=segment.pilot_l_checkpoint_id,
        pilot_r_checkpoint_id=None,
        tau_start=segment.tau_start,
        tau_cursor=segment.tau_cursor,
        tau_end=segment.tau_cursor,
        active_m_layers=segment.active_m_layers,
        relation_braid_commitment=segment.relation_braid_commitment,
        trajectory_commitment=segment.trajectory_commitment,
        modulation_commitment=segment.modulation_commitment,
        t36_trajectory_commitment=segment.t36_trajectory_commitment,
        event_commitments=segment.event_commitments,
        source_orbital_state=segment.source_orbital_state,
        target_orbital_state=None,
        epistemic_state=segment.epistemic_state,
        resolution_state="REJECTED",
        resolution_witness_sha256=_digest(resolution_witness_sha256, "resolution_witness_sha256"),
    )


def validate_checkpoint_against_header(header: PNLFHeader, checkpoint: StateMemoryCheckpoint) -> None:
    if not isinstance(header, PNLFHeader) or not isinstance(checkpoint, StateMemoryCheckpoint):
        raise PNLFOrbitalMemoryError("header and checkpoint types are required")
    if checkpoint.object_id != header.object_id:
        raise PNLFOrbitalMemoryError("checkpoint object_id does not match PNLF header")
    state = checkpoint.orbital_state
    if state.mass_model_id != header.mass_model_id:
        raise PNLFOrbitalMemoryError("checkpoint mass model does not match PNLF header")
    if state.orbit_quantizer_id != header.orbit_quantizer_id:
        raise PNLFOrbitalMemoryError("checkpoint orbit quantizer does not match PNLF header")
    if state.proper_time_model_id != header.proper_time_model_id:
        raise PNLFOrbitalMemoryError("checkpoint proper-time model does not match PNLF header")
    if header.file_id in {checkpoint.content_commitment, checkpoint.checkpoint_object_id}:
        raise PNLFOrbitalMemoryError("FILE_ID cannot collapse into content/checkpoint identity")
    if checkpoint.content_commitment == checkpoint.checkpoint_object_id:
        raise PNLFOrbitalMemoryError("CONTENT_COMMITMENT cannot collapse into CHECKPOINT_OBJECT_ID")


def validate_segment_against_header(header: PNLFHeader, segment: LiminalSegmentRevision) -> None:
    if not isinstance(header, PNLFHeader) or not isinstance(segment, LiminalSegmentRevision):
        raise PNLFOrbitalMemoryError("header and segment types are required")
    if segment.object_id != header.object_id:
        raise PNLFOrbitalMemoryError("segment object_id does not match PNLF header")
    states = [segment.source_orbital_state]
    if segment.target_orbital_state is not None:
        states.append(segment.target_orbital_state)
    for state in states:
        if state.mass_model_id != header.mass_model_id:
            raise PNLFOrbitalMemoryError("segment orbital state mass model does not match PNLF header")
        if state.orbit_quantizer_id != header.orbit_quantizer_id:
            raise PNLFOrbitalMemoryError("segment orbit quantizer does not match PNLF header")
        if state.proper_time_model_id != header.proper_time_model_id:
            raise PNLFOrbitalMemoryError("segment proper-time model does not match PNLF header")
    if header.file_id == segment.segment_commitment:
        raise PNLFOrbitalMemoryError("FILE_ID cannot collapse into SEGMENT_COMMITMENT")


def logical_address(object_id: str, tau: float, relation: str) -> tuple[str, float, str]:
    return (
        _require_text(object_id, "object_id"),
        _non_negative(tau, "tau"),
        _require_text(relation, "relation"),
    )


def tau_frame(segment: LiminalSegmentRevision, tau: float) -> dict[str, Any]:
    if not isinstance(segment, LiminalSegmentRevision):
        raise PNLFOrbitalMemoryError("tau_frame requires LiminalSegmentRevision")
    t = _non_negative(tau, "tau")
    if not segment.tau_start <= t <= segment.tau_cursor:
        raise PNLFOrbitalMemoryError("tau is outside represented liminal revision")
    return {
        "schema": TAU_FRAME_SCHEMA,
        "pilot_l": segment.pilot_l_checkpoint_id,
        "lambda": {
            "segment_id": segment.segment_id,
            "segment_commitment": segment.segment_commitment,
            "tau": t,
            "trajectory_commitment": segment.trajectory_commitment,
        },
        "pilot_r": segment.pilot_r_checkpoint_id,
        "t36": segment.t36_trajectory_commitment,
        "proper_time_model_id": segment.source_orbital_state.proper_time_model_id,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
    }


__all__ = [
    "PNLF_SCHEMA",
    "CHECKPOINT_SCHEMA",
    "LIMINAL_SCHEMA",
    "TAU_FRAME_SCHEMA",
    "ORBITAL_BANDS",
    "M_LAYERS",
    "PNLFOrbitalMemoryError",
    "OrbitalState",
    "PNLFHeader",
    "StateMemoryCheckpoint",
    "LiminalSegmentRevision",
    "build_state_checkpoint",
    "open_liminal_segment",
    "advance_liminal_segment",
    "admit_liminal_segment",
    "reject_liminal_segment",
    "validate_checkpoint_against_header",
    "validate_segment_against_header",
    "logical_address",
    "tau_frame",
]
