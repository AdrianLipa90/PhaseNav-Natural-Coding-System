from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Mapping, Sequence

DIM = 36
TAU = 2.0 * math.pi
DEFAULT_SURFACE_ROOT = Path("/dev/shm/ciel_noema")
HYDRO_TIME_CONTRACT_ID = "PNCS_HYDRODYNAMIC_PROPER_TIME_V0_27"
STATE_SCHEMA = "PNCS_T36_PHASE_FLOW_STATE_V0_27"
GATE_SCHEMA = "PNCS_HYDRODYNAMIC_PHASE_GATE_V0_27"
STEP_SCHEMA = "PNCS_HYDRODYNAMIC_PHASE_STEP_V0_27"
TRACE_SCHEMA = "PNCS_HYDRODYNAMIC_PHASE_TRACE_V0_27"
LIVE_BINDING_SCHEMA = "PNCS_HYDRODYNAMIC_LIVE_BINDING_V0_27"

class HydrodynamicProperTimeV27Error(ValueError):
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
            raise HydrodynamicProperTimeV27Error("non-finite canonical value")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise HydrodynamicProperTimeV27Error(f"unsupported canonical type: {type(value).__name__}")


def _compact_json(value: object) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_compact_json(value).encode("utf-8"))


def _typed_id(prefix: str, payload: object) -> str:
    return f"{prefix}:sha256:{_sha256_json(payload)}"


def _finite(value: object, field: str) -> float:
    try:
        x = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise HydrodynamicProperTimeV27Error(f"{field} must be finite") from exc
    if not math.isfinite(x):
        raise HydrodynamicProperTimeV27Error(f"{field} must be finite")
    return x


def _vector36(values: Sequence[float], field: str) -> tuple[float, ...]:
    vals = tuple(_finite(v, field) for v in values)
    if len(vals) != DIM:
        raise HydrodynamicProperTimeV27Error(f"{field} must contain exactly {DIM} values")
    return vals


def _angles36(values: Sequence[float]) -> tuple[float, ...]:
    vals = _vector36(values, "theta")
    for i, value in enumerate(vals):
        if value < 0.0 or value >= TAU:
            raise HydrodynamicProperTimeV27Error(f"theta[{i}] must be in [0, 2pi)")
    return vals


def _normalize_drive(values: Sequence[float]) -> tuple[float, ...]:
    vec = _vector36(values, "drive")
    norm = math.sqrt(sum(x * x for x in vec))
    if norm <= 0.0:
        raise HydrodynamicProperTimeV27Error("drive vector must have non-zero norm")
    return tuple(x / norm for x in vec)


def _wrap_phase(value: float) -> float:
    out = value % TAU
    if out == TAU:
        return 0.0
    return out


@dataclass(frozen=True)
class PhaseFlowState36:
    theta: tuple[float, ...]
    velocity: tuple[float, ...]
    phase_proper_time: float = 0.0

    def __init__(self, theta: Sequence[float], velocity: Sequence[float] | None = None, phase_proper_time: float = 0.0) -> None:
        object.__setattr__(self, "theta", _angles36(theta))
        object.__setattr__(self, "velocity", _vector36(velocity if velocity is not None else (0.0,) * DIM, "velocity"))
        tau = _finite(phase_proper_time, "phase_proper_time")
        if tau < 0.0:
            raise HydrodynamicProperTimeV27Error("phase_proper_time must be non-negative")
        object.__setattr__(self, "phase_proper_time", tau)

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": STATE_SCHEMA,
            "contract_id": HYDRO_TIME_CONTRACT_ID,
            "space": "T^36",
            "coordinate_semantics": "phase_angles_radians",
            "theta": list(self.theta),
            "velocity": list(self.velocity),
            "phase_proper_time": self.phase_proper_time,
            "laboratory_time_modified": False,
            "external_effects": False,
        }

    @property
    def state_id(self) -> str:
        return _typed_id("pncs:t36-flow-state", self.payload)


@dataclass(frozen=True)
class HydrodynamicPhaseGate:
    density: float
    effective_viscosity: float
    drive_gain: float = 0.05
    coordinate_dt: float = 0.01
    steps: int = 1
    lapse_min: float = 1.0 / 64.0
    lapse_max: float = 8.0
    max_speed: float = 64.0

    def __post_init__(self) -> None:
        rho = _finite(self.density, "density")
        nu = _finite(self.effective_viscosity, "effective_viscosity")
        gain = _finite(self.drive_gain, "drive_gain")
        dt = _finite(self.coordinate_dt, "coordinate_dt")
        lmin = _finite(self.lapse_min, "lapse_min")
        lmax = _finite(self.lapse_max, "lapse_max")
        vmax = _finite(self.max_speed, "max_speed")
        if rho <= 0.0:
            raise HydrodynamicProperTimeV27Error("density must be positive")
        if nu < 0.0:
            raise HydrodynamicProperTimeV27Error("effective_viscosity must be non-negative")
        if gain < 0.0 or dt <= 0.0 or lmin <= 0.0 or lmax < lmin or vmax <= 0.0:
            raise HydrodynamicProperTimeV27Error("invalid hydrodynamic gate bounds")
        if isinstance(self.steps, bool) or not isinstance(self.steps, int) or self.steps < 1 or self.steps > 1_000_000:
            raise HydrodynamicProperTimeV27Error("steps must be an integer in [1,1000000]")

    @property
    def sound_speed(self) -> float:
        return math.sqrt(self.density)

    @property
    def lapse(self) -> float:
        raw = self.sound_speed / (1.0 + self.effective_viscosity)
        return min(self.lapse_max, max(self.lapse_min, raw))

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": GATE_SCHEMA,
            "contract_id": HYDRO_TIME_CONTRACT_ID,
            "density": self.density,
            "effective_viscosity": self.effective_viscosity,
            "drive_gain": self.drive_gain,
            "coordinate_dt": self.coordinate_dt,
            "steps": self.steps,
            "lapse_min": self.lapse_min,
            "lapse_max": self.lapse_max,
            "max_speed": self.max_speed,
            "sound_speed": self.sound_speed,
            "lapse": self.lapse,
            "lapse_source": "sqrt(density)/(1+effective_viscosity)",
            "viscosity_semantics": "effective_damping_not_classical_BEC_viscosity",
            "laboratory_time_modified": False,
        }

    @property
    def gate_id(self) -> str:
        return _typed_id("pncs:hydro-gate", self.payload)


def effective_transport_tensor(state: PhaseFlowState36, gate: HydrodynamicPhaseGate) -> tuple[tuple[float, ...], ...]:
    if not isinstance(state, PhaseFlowState36) or not isinstance(gate, HydrodynamicPhaseGate):
        raise HydrodynamicProperTimeV27Error("PhaseFlowState36 and HydrodynamicPhaseGate required")
    rho = gate.density
    u = state.velocity
    return tuple(tuple(rho * (1.0 if i == j else 0.0) + u[i] * u[j] for j in range(DIM)) for i in range(DIM))


def transport_tensor_sha256(state: PhaseFlowState36, gate: HydrodynamicPhaseGate) -> str:
    return _sha256_json(effective_transport_tensor(state, gate))


def transport_quadratic_form(state: PhaseFlowState36, gate: HydrodynamicPhaseGate, probe: Sequence[float]) -> float:
    q = _vector36(probe, "probe")
    uq = sum(a * b for a, b in zip(state.velocity, q))
    qq = sum(x * x for x in q)
    return gate.density * qq + uq * uq


@dataclass(frozen=True)
class HydrodynamicStep:
    index: int
    before_state_id: str
    after_state: PhaseFlowState36
    gate_id: str
    drive_sha256: str
    coordinate_dt: float
    proper_dt: float
    tensor_sha256_before: str
    speed_before: float
    speed_after: float

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": STEP_SCHEMA,
            "contract_id": HYDRO_TIME_CONTRACT_ID,
            "index": self.index,
            "before_state_id": self.before_state_id,
            "after_state_id": self.after_state.state_id,
            "gate_id": self.gate_id,
            "drive_sha256": self.drive_sha256,
            "coordinate_dt": self.coordinate_dt,
            "proper_dt": self.proper_dt,
            "tensor_sha256_before": self.tensor_sha256_before,
            "speed_before": self.speed_before,
            "speed_after": self.speed_after,
            "external_effects": False,
        }

    @property
    def step_id(self) -> str:
        return _typed_id("pncs:hydro-step", self.payload)


def advance_phase_flow(state: PhaseFlowState36, gate: HydrodynamicPhaseGate, drive: Sequence[float], *, index: int = 0) -> HydrodynamicStep:
    if not isinstance(state, PhaseFlowState36) or not isinstance(gate, HydrodynamicPhaseGate):
        raise HydrodynamicProperTimeV27Error("PhaseFlowState36 and HydrodynamicPhaseGate required")
    d = _normalize_drive(drive)
    drive_sha = _sha256_json(list(d))
    proper_dt = gate.lapse * gate.coordinate_dt
    u = state.velocity
    dot_ud = sum(a * b for a, b in zip(u, d))
    # Closed form G_eff @ d for G_eff = rho I + u u^T.
    force = tuple(gate.density * d[i] + u[i] * dot_ud for i in range(DIM))
    accel = tuple(gate.drive_gain * force[i] - gate.effective_viscosity * u[i] for i in range(DIM))
    new_u = tuple(u[i] + proper_dt * accel[i] for i in range(DIM))
    speed_before = math.sqrt(sum(x * x for x in u))
    speed_after = math.sqrt(sum(x * x for x in new_u))
    if not math.isfinite(speed_after) or speed_after > gate.max_speed:
        raise HydrodynamicProperTimeV27Error("hydrodynamic step exceeded max_speed")
    new_theta = tuple(_wrap_phase(state.theta[i] + proper_dt * new_u[i]) for i in range(DIM))
    after = PhaseFlowState36(new_theta, new_u, state.phase_proper_time + proper_dt)
    return HydrodynamicStep(
        index=index,
        before_state_id=state.state_id,
        after_state=after,
        gate_id=gate.gate_id,
        drive_sha256=drive_sha,
        coordinate_dt=gate.coordinate_dt,
        proper_dt=proper_dt,
        tensor_sha256_before=transport_tensor_sha256(state, gate),
        speed_before=speed_before,
        speed_after=speed_after,
    )


@dataclass(frozen=True)
class HydrodynamicTrace:
    initial_state_id: str
    final_state: PhaseFlowState36
    gate: HydrodynamicPhaseGate
    drive_sha256: str
    step_ids: tuple[str, ...]
    coordinate_time: float
    proper_time_advanced: float

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TRACE_SCHEMA,
            "contract_id": HYDRO_TIME_CONTRACT_ID,
            "initial_state_id": self.initial_state_id,
            "final_state_id": self.final_state.state_id,
            "gate_id": self.gate.gate_id,
            "drive_sha256": self.drive_sha256,
            "step_ids": list(self.step_ids),
            "coordinate_time": self.coordinate_time,
            "proper_time_advanced": self.proper_time_advanced,
            "lapse": self.gate.lapse,
            "external_effects": False,
            "laboratory_time_modified": False,
        }

    @property
    def trace_id(self) -> str:
        return _typed_id("pncs:hydro-trace", self.payload)


def run_hydrodynamic_gate(state: PhaseFlowState36, gate: HydrodynamicPhaseGate, drive: Sequence[float]) -> HydrodynamicTrace:
    d = _normalize_drive(drive)
    drive_sha = _sha256_json(list(d))
    current = state
    ids: list[str] = []
    for i in range(gate.steps):
        step = advance_phase_flow(current, gate, d, index=i)
        ids.append(step.step_id)
        current = step.after_state
    return HydrodynamicTrace(
        initial_state_id=state.state_id,
        final_state=current,
        gate=gate,
        drive_sha256=drive_sha,
        step_ids=tuple(ids),
        coordinate_time=gate.steps * gate.coordinate_dt,
        proper_time_advanced=current.phase_proper_time - state.phase_proper_time,
    )


def torus_chord_distance(left: Sequence[float], right: Sequence[float]) -> float:
    a = _angles36(left)
    b = _angles36(right)
    total = 0.0
    for x, y in zip(a, b):
        delta = abs(x - y) % TAU
        delta = min(delta, TAU - delta)
        total += delta * delta
    return math.sqrt(total)


def load_live_phase_and_drive(
    operator_name: str,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    *,
    require_canonical_root: bool = True,
) -> tuple[PhaseFlowState36, tuple[float, ...], dict[str, object]]:
    root = Path(surface_root)
    if require_canonical_root and root != DEFAULT_SURFACE_ROOT:
        raise HydrodynamicProperTimeV27Error("live v0.27 runtime is fixed to /dev/shm/ciel_noema")
    binding_path = root / "ciel_binding_status"
    try:
        if binding_path.read_text("utf-8").strip() != "ACTIVE":
            raise HydrodynamicProperTimeV27Error("live NOEMA binding is not ACTIVE")
        phi_raw = (root / "phi").read_bytes()
        registry_raw = (root / "phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl").read_bytes()
    except OSError as exc:
        raise HydrodynamicProperTimeV27Error("live T^36 inputs unavailable") from exc
    if len(phi_raw) != DIM * 8:
        raise HydrodynamicProperTimeV27Error("live phi must contain exactly 36 doubles")
    theta = struct.unpack("<36d", phi_raw)
    state = PhaseFlowState36(theta)
    wanted = str(operator_name).strip().upper()
    drive: tuple[float, ...] | None = None
    for line_no, line in enumerate(registry_raw.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HydrodynamicProperTimeV27Error(f"invalid operator registry JSONL line {line_no}") from exc
        if not isinstance(rec, dict) or rec.get("schema") != "PHASENAV_OPERATOR_VECTOR_V1":
            raise HydrodynamicProperTimeV27Error("unexpected live operator schema")
        name = str(rec.get("operator_name", rec.get("operator_id", rec.get("card_id", "")))).strip().upper()
        if name == wanted:
            raw = rec.get("orbit_vector", rec.get("vector_36d"))
            if not isinstance(raw, list):
                raise HydrodynamicProperTimeV27Error("operator vector missing")
            if drive is not None:
                raise HydrodynamicProperTimeV27Error("duplicate live operator")
            drive = _normalize_drive(raw)
    if drive is None:
        raise HydrodynamicProperTimeV27Error(f"live operator not found: {wanted}")
    binding = {
        "schema": LIVE_BINDING_SCHEMA,
        "contract_id": HYDRO_TIME_CONTRACT_ID,
        "root": str(root),
        "operator_name": wanted,
        "phi_sha256": _sha256_bytes(phi_raw),
        "operator_registry_sha256": _sha256_bytes(registry_raw),
        "initial_state_id": state.state_id,
        "drive_sha256": _sha256_json(list(drive)),
        "static_runtime_fallback": False,
    }
    return state, drive, binding
