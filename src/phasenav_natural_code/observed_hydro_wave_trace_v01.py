from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from numbers import Real
from typing import Mapping, Sequence

from .hydro_time_v27 import (
    DIM,
    HydrodynamicTrace,
    PhaseFlowState36,
    advance_phase_flow,
)
from .temporal_geometry_v02 import TemporalObservationReceipt


CONTRACT_ID = "PNCS_OBSERVED_HYDRO_WAVE_TRACE_V0_1"
SCHEMA = "PNCS_OBSERVED_HYDRO_WAVE_TRACE_BINDING_V0_1"
PAIR_PROFILE_SCHEMA = "PNCS_OBSERVED_HYDRO_PAIR_PROFILE_V0_1"
FROZEN_POST_OBSERVATION = "FROZEN_POST_OBSERVATION"
PARENT_SOURCE_COMMIT = "8855abed440e9949f576ffbe2153325f69e78963"


class ObservedHydroWaveTraceError(ValueError):
    pass


def _canon(value: object) -> object:
    if isinstance(value, tuple):
        return [_canon(x) for x in value]
    if isinstance(value, list):
        return [_canon(x) for x in value]
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise ObservedHydroWaveTraceError("canonical mapping keys must be strings")
        return {k: _canon(value[k]) for k in sorted(value)}
    if isinstance(value, complex):
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise ObservedHydroWaveTraceError("complex value must be finite")
        return [float(value.real), float(value.imag)]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ObservedHydroWaveTraceError("canonical float must be finite")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise ObservedHydroWaveTraceError(
        f"unsupported canonical type: {type(value).__name__}"
    )


def _digest(value: object) -> str:
    raw = json.dumps(
        _canon(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _finite_real(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ObservedHydroWaveTraceError(f"{name} must be finite real")
    out = float(value)
    if not math.isfinite(out):
        raise ObservedHydroWaveTraceError(f"{name} must be finite real")
    return out


def _drive36(value: Sequence[float]) -> tuple[float, ...]:
    try:
        vals = tuple(_finite_real("drive", x) for x in value)
    except TypeError as exc:
        raise ObservedHydroWaveTraceError("drive must be a finite 36-vector") from exc
    if len(vals) != DIM:
        raise ObservedHydroWaveTraceError("drive must contain exactly 36 values")
    norm = math.sqrt(sum(x * x for x in vals))
    if norm <= 0.0:
        raise ObservedHydroWaveTraceError("drive must have non-zero norm")
    return tuple(x / norm for x in vals)


@dataclass(frozen=True, slots=True)
class ObservedPairProfile:
    pair_index: int
    left_index: int
    right_index: int
    p_left: float
    p_right: float
    pair_support: float
    imbalance_u: float

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": PAIR_PROFILE_SCHEMA,
            "contract_id": CONTRACT_ID,
            "pair_index": self.pair_index,
            "left_index": self.left_index,
            "right_index": self.right_index,
            "p_left": self.p_left,
            "p_right": self.p_right,
            "pair_support": self.pair_support,
            "imbalance_u": self.imbalance_u,
        }


def observed_pair_profile(
    observation: TemporalObservationReceipt,
    pair_index: int,
) -> ObservedPairProfile:
    if not isinstance(observation, TemporalObservationReceipt):
        raise ObservedHydroWaveTraceError(
            "observation must be TemporalObservationReceipt"
        )
    if isinstance(pair_index, bool) or not isinstance(pair_index, int):
        raise ObservedHydroWaveTraceError("pair_index must be integer")
    if pair_index < 0 or pair_index >= DIM // 2:
        raise ObservedHydroWaveTraceError("pair_index outside 18-pair domain")

    left = 2 * pair_index
    right = left + 1
    probs = observation.after_state.probabilities
    p_left = float(probs[left])
    p_right = float(probs[right])
    q = p_left + p_right
    if not math.isfinite(q) or q <= 0.0:
        raise ObservedHydroWaveTraceError("observed pair has zero/non-finite support")
    u = (p_left - p_right) / q
    return ObservedPairProfile(
        pair_index=pair_index,
        left_index=left,
        right_index=right,
        p_left=p_left,
        p_right=p_right,
        pair_support=q,
        imbalance_u=u,
    )


@dataclass(frozen=True, slots=True)
class ObservedHydroWaveTraceBinding:
    observation_receipt_id: str
    observed_after_state_id: str
    temporal_projection_id: str
    initial_phase_state_id: str
    hydro_trace_id: str
    hydro_gate_id: str
    hydro_drive_sha256: str
    hydro_step_ids: tuple[str, ...]
    phase_proper_time_start: float
    phase_proper_time_end: float
    amplitude_policy: str
    observed_probabilities_sha256: str
    receipt_sha256: str

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "contract_id": CONTRACT_ID,
            "parent_source_commit": PARENT_SOURCE_COMMIT,
            "observation_receipt_id": self.observation_receipt_id,
            "observed_after_state_id": self.observed_after_state_id,
            "temporal_projection_id": self.temporal_projection_id,
            "initial_phase_state_id": self.initial_phase_state_id,
            "hydro_trace_id": self.hydro_trace_id,
            "hydro_gate_id": self.hydro_gate_id,
            "hydro_drive_sha256": self.hydro_drive_sha256,
            "hydro_step_ids": list(self.hydro_step_ids),
            "phase_proper_time_start": self.phase_proper_time_start,
            "phase_proper_time_end": self.phase_proper_time_end,
            "amplitude_policy": self.amplitude_policy,
            "observed_probabilities_sha256": self.observed_probabilities_sha256,
            "basis_binding_mode": "EXACT_INITIAL_THETA_EQUALITY",
            "amplitude_scope": "OBSERVATION_POST_STATE_FIXED_OVER_HYDRO_TRACE",
            "epistemic_state": "CHYBA",
            "promotion_state": "CANDIDATE_ONLY",
            "runtime_execution_authority": False,
            "canon_write_authority": False,
            "state_memory_write_authority": False,
            "receipt_sha256": self.receipt_sha256,
        }


@dataclass(frozen=True, slots=True)
class ObservedHydroWaveTraceReplay:
    binding: ObservedHydroWaveTraceBinding
    phase_states: tuple[PhaseFlowState36, ...]

    @property
    def probabilities(self) -> tuple[float, ...]:
        # Probabilities are committed by the binding's observed_after_state_id and
        # observed_probabilities_sha256.  The native replay intentionally stores
        # only phase states to avoid duplicating the source observation object.
        raise AttributeError(
            "probabilities remain owned by the TemporalObservationReceipt source"
        )


def bind_observed_hydro_wave_trace(
    observation: TemporalObservationReceipt,
    initial_phase_state: PhaseFlowState36,
    trace: HydrodynamicTrace,
    drive: Sequence[float],
    *,
    amplitude_policy: str = FROZEN_POST_OBSERVATION,
) -> ObservedHydroWaveTraceBinding:
    if not isinstance(observation, TemporalObservationReceipt):
        raise ObservedHydroWaveTraceError(
            "observation must be TemporalObservationReceipt"
        )
    if not isinstance(initial_phase_state, PhaseFlowState36):
        raise ObservedHydroWaveTraceError(
            "initial_phase_state must be PhaseFlowState36"
        )
    if not isinstance(trace, HydrodynamicTrace):
        raise ObservedHydroWaveTraceError("trace must be HydrodynamicTrace")
    if amplitude_policy != FROZEN_POST_OBSERVATION:
        raise ObservedHydroWaveTraceError(
            "only FROZEN_POST_OBSERVATION amplitude policy is admitted"
        )

    observed_theta = tuple(observation.after_state.projection.theta)
    if observed_theta != tuple(initial_phase_state.theta):
        raise ObservedHydroWaveTraceError(
            "temporal observation projection and hydro initial theta mismatch"
        )
    if trace.initial_state_id != initial_phase_state.state_id:
        raise ObservedHydroWaveTraceError(
            "hydro trace initial-state identity mismatch"
        )
    if not trace.step_ids:
        raise ObservedHydroWaveTraceError("hydro trace must contain at least one step")

    normalized_drive = _drive36(drive)
    current = initial_phase_state
    replay_step_ids: list[str] = []
    for index in range(trace.gate.steps):
        step = advance_phase_flow(current, trace.gate, normalized_drive, index=index)
        replay_step_ids.append(step.step_id)
        current = step.after_state

    if tuple(replay_step_ids) != tuple(trace.step_ids):
        raise ObservedHydroWaveTraceError("hydro trace step lineage replay mismatch")
    if current.state_id != trace.final_state.state_id:
        raise ObservedHydroWaveTraceError("hydro trace final-state replay mismatch")

    observation_probs = tuple(float(x) for x in observation.after_state.probabilities)
    body = {
        "schema": SCHEMA,
        "contract_id": CONTRACT_ID,
        "parent_source_commit": PARENT_SOURCE_COMMIT,
        "observation_receipt_id": observation.receipt_id,
        "observed_after_state_id": observation.after_state.state_id,
        "temporal_projection_id": observation.after_state.projection.projection_id,
        "initial_phase_state_id": initial_phase_state.state_id,
        "hydro_trace_id": trace.trace_id,
        "hydro_gate_id": trace.gate.gate_id,
        "hydro_drive_sha256": trace.payload["drive_sha256"],
        "hydro_step_ids": list(trace.step_ids),
        "phase_proper_time_start": initial_phase_state.phase_proper_time,
        "phase_proper_time_end": trace.final_state.phase_proper_time,
        "amplitude_policy": amplitude_policy,
        "observed_probabilities_sha256": _digest(list(observation_probs)),
        "basis_binding_mode": "EXACT_INITIAL_THETA_EQUALITY",
        "amplitude_scope": "OBSERVATION_POST_STATE_FIXED_OVER_HYDRO_TRACE",
        "epistemic_state": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "state_memory_write_authority": False,
    }
    receipt_sha256 = _digest(body)

    return ObservedHydroWaveTraceBinding(
        observation_receipt_id=observation.receipt_id,
        observed_after_state_id=observation.after_state.state_id,
        temporal_projection_id=observation.after_state.projection.projection_id,
        initial_phase_state_id=initial_phase_state.state_id,
        hydro_trace_id=trace.trace_id,
        hydro_gate_id=trace.gate.gate_id,
        hydro_drive_sha256=str(trace.payload["drive_sha256"]),
        hydro_step_ids=tuple(trace.step_ids),
        phase_proper_time_start=initial_phase_state.phase_proper_time,
        phase_proper_time_end=trace.final_state.phase_proper_time,
        amplitude_policy=amplitude_policy,
        observed_probabilities_sha256=_digest(list(observation_probs)),
        receipt_sha256=receipt_sha256,
    )


def replay_observed_hydro_wave_trace(
    observation: TemporalObservationReceipt,
    initial_phase_state: PhaseFlowState36,
    trace: HydrodynamicTrace,
    drive: Sequence[float],
    *,
    amplitude_policy: str = FROZEN_POST_OBSERVATION,
) -> ObservedHydroWaveTraceReplay:
    binding = bind_observed_hydro_wave_trace(
        observation,
        initial_phase_state,
        trace,
        drive,
        amplitude_policy=amplitude_policy,
    )
    normalized_drive = _drive36(drive)
    current = initial_phase_state
    states = [current]
    for index in range(trace.gate.steps):
        step = advance_phase_flow(current, trace.gate, normalized_drive, index=index)
        states.append(step.after_state)
        current = step.after_state
    return ObservedHydroWaveTraceReplay(binding=binding, phase_states=tuple(states))
