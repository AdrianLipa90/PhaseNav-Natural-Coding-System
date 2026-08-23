from __future__ import annotations

from dataclasses import dataclass
import cmath
import hashlib
import json
import math
from typing import Sequence

DIM = 36
TAU = 2.0 * math.pi

TEMPORAL_GEOMETRY_CONTRACT_ID = "PNCS_TEMPORAL_GEOMETRY_V0_2"
RIEMANN_TEMPLATE_SCHEMA = "PNCS_RIEMANN_CONFORMAL_TEMPLATE_RECEIPT_V0_2"
TEMPORAL_POINT_SCHEMA = "PNCS_TEMPORAL_CONFORMAL_POINT_V0_2"
TEMPORAL_DUAL_PAIR_SCHEMA = "PNCS_TEMPORAL_DUAL_PAIR_RECEIPT_V0_2"
TEMPORAL_T36_SCHEMA = "PNCS_TEMPORAL_T36_PROJECTION_V0_2"
TEMPORAL_WAVE36_SCHEMA = "PNCS_TEMPORAL_WAVE36_STATE_V0_2"
TEMPORAL_OBSERVATION_SCHEMA = "PNCS_TEMPORAL_OBSERVATION_RECEIPT_V0_2"
TEMPORAL_WAVE_CORPUSCLE_SCHEMA = "PNCS_TEMPORAL_WAVE_CORPUSCLE_RECEIPT_V0_2"

EPISTEMIC_STATUS = "CHYBA"
PROMOTION_TRACK = "POST_V1_EXPERIMENTAL"
SOURCE_DOCUMENT = "Riemann_1overz_Baginski_3pager.pdf"


class TemporalGeometryV02Error(ValueError):
    pass


def _finite(value: object, field: str) -> float:
    try:
        out = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise TemporalGeometryV02Error(f"{field} must be finite") from exc
    if not math.isfinite(out):
        raise TemporalGeometryV02Error(f"{field} must be finite")
    return out


def _positive(value: object, field: str) -> float:
    out = _finite(value, field)
    if out <= 0.0:
        raise TemporalGeometryV02Error(f"{field} must be positive")
    return out


def _finite_complex(value: object, field: str) -> complex:
    try:
        out = complex(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise TemporalGeometryV02Error(f"{field} must be finite complex") from exc
    if not (math.isfinite(out.real) and math.isfinite(out.imag)):
        raise TemporalGeometryV02Error(f"{field} must be finite complex")
    return out


def _complex_payload(value: complex) -> list[float]:
    z = _finite_complex(value, "complex_value")
    return [float(z.real), float(z.imag)]


def _jsonable(value: object) -> object:
    if isinstance(value, complex):
        return _complex_payload(value)
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TemporalGeometryV02Error("non-finite canonical value")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TemporalGeometryV02Error(f"unsupported canonical type: {type(value).__name__}")


def _typed_id(prefix: str, payload: object) -> str:
    raw = json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(raw).hexdigest()}"


def _phase(value: complex) -> float:
    theta = cmath.phase(value) % TAU
    if theta == TAU:
        return 0.0
    return float(theta)


# Exact conformal template from the author's Riemann 1/z note.

def riemann_center(s: complex) -> complex:
    return 2.0 * _finite_complex(s, "s") - 1.0


def riemann_cayley(s: complex) -> complex:
    z = _finite_complex(s, "s")
    if z == 0:
        raise TemporalGeometryV02Error("s=0 is outside z=(s-1)/s chart")
    return (z - 1.0) / z


def riemann_functional_dual(s: complex) -> complex:
    return 1.0 - _finite_complex(s, "s")


@dataclass(frozen=True, slots=True)
class RiemannConformalTemplateReceipt:
    s: complex
    tolerance: float = 1e-12

    def __post_init__(self) -> None:
        object.__setattr__(self, "s", _finite_complex(self.s, "s"))
        object.__setattr__(self, "tolerance", _positive(self.tolerance, "tolerance"))
        if self.s == 0 or self.s == 1:
            raise TemporalGeometryV02Error("template receipt requires s outside chart poles 0 and 1")

    @property
    def z(self) -> complex:
        return riemann_cayley(self.s)

    @property
    def dual_z(self) -> complex:
        return riemann_cayley(riemann_functional_dual(self.s))

    @property
    def inversion_residual(self) -> float:
        return abs(self.dual_z - 1.0 / self.z)

    @property
    def critical_line_residual(self) -> float:
        return abs(abs(self.z) - 1.0)

    @property
    def on_critical_line(self) -> bool:
        return abs(self.s.real - 0.5) <= self.tolerance

    @property
    def on_unit_circle(self) -> bool:
        return self.critical_line_residual <= self.tolerance

    @property
    def symmetry_pass(self) -> bool:
        return self.inversion_residual <= self.tolerance

    @property
    def critical_equivalence_pass(self) -> bool:
        return self.on_critical_line == self.on_unit_circle

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": RIEMANN_TEMPLATE_SCHEMA,
            "contract_id": TEMPORAL_GEOMETRY_CONTRACT_ID,
            "s": self.s,
            "w": riemann_center(self.s),
            "z": self.z,
            "dual_s": riemann_functional_dual(self.s),
            "dual_z": self.dual_z,
            "inverse_z": 1.0 / self.z,
            "inversion_residual": self.inversion_residual,
            "critical_line_residual": self.critical_line_residual,
            "on_critical_line": self.on_critical_line,
            "on_unit_circle": self.on_unit_circle,
            "symmetry_pass": self.symmetry_pass,
            "critical_equivalence_pass": self.critical_equivalence_pass,
            "source_document": SOURCE_DOCUMENT,
            "source_identity": "w=2s-1; z=(s-1)/s; s<->1-s => z<->1/z",
        }

    @property
    def receipt_id(self) -> str:
        return _typed_id("pncs:riemann-conformal-template", self.payload)


# Temporal conformal model:
# u=(t-now)/lambda, w_T=i*u, z_T=(w_T-1)/(w_T+1).

def _temporal_z_from_u(u: float) -> complex:
    x = _finite(u, "u")
    w = 1j * x
    return (w - 1.0) / (w + 1.0)


@dataclass(frozen=True, slots=True)
class TemporalConformalPoint:
    time_value: float
    now: float
    scale: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_value", _finite(self.time_value, "time_value"))
        object.__setattr__(self, "now", _finite(self.now, "now"))
        object.__setattr__(self, "scale", _positive(self.scale, "scale"))

    @property
    def u(self) -> float:
        return (self.time_value - self.now) / self.scale

    @property
    def w(self) -> complex:
        return 1j * self.u

    @property
    def z(self) -> complex:
        return _temporal_z_from_u(self.u)

    @property
    def phase(self) -> float:
        return _phase(self.z)

    @property
    def modulus(self) -> float:
        return abs(self.z)

    @property
    def branch(self) -> str:
        if self.time_value < self.now:
            return "PAST"
        if self.time_value > self.now:
            return "FUTURE"
        return "NOW"

    @property
    def reflected_time(self) -> float:
        return 2.0 * self.now - self.time_value

    @property
    def dual(self) -> "TemporalConformalPoint":
        return TemporalConformalPoint(self.reflected_time, self.now, self.scale)

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TEMPORAL_POINT_SCHEMA,
            "contract_id": TEMPORAL_GEOMETRY_CONTRACT_ID,
            "epistemic_status": EPISTEMIC_STATUS,
            "promotion_track": PROMOTION_TRACK,
            "time_value": self.time_value,
            "now": self.now,
            "scale": self.scale,
            "u": self.u,
            "w": self.w,
            "z": self.z,
            "phase": self.phase,
            "modulus": self.modulus,
            "branch": self.branch,
            "reflected_time": self.reflected_time,
            "chart": "TEMPORAL_CAYLEY_S1",
        }

    @property
    def point_id(self) -> str:
        return _typed_id("pncs:temporal-geometry-point", self.payload)


@dataclass(frozen=True, slots=True)
class TemporalDualPairReceipt:
    now: float
    delta: float
    scale: float = 1.0
    tolerance: float = 1e-12

    def __post_init__(self) -> None:
        object.__setattr__(self, "now", _finite(self.now, "now"))
        delta = _finite(self.delta, "delta")
        if delta < 0.0:
            raise TemporalGeometryV02Error("delta must be non-negative")
        object.__setattr__(self, "delta", delta)
        object.__setattr__(self, "scale", _positive(self.scale, "scale"))
        object.__setattr__(self, "tolerance", _positive(self.tolerance, "tolerance"))

    @property
    def past(self) -> TemporalConformalPoint:
        return TemporalConformalPoint(self.now - self.delta, self.now, self.scale)

    @property
    def future(self) -> TemporalConformalPoint:
        return TemporalConformalPoint(self.now + self.delta, self.now, self.scale)

    @property
    def inversion_residual(self) -> float:
        return abs(self.future.z - 1.0 / self.past.z)

    @property
    def conjugation_residual(self) -> float:
        return abs(self.future.z - self.past.z.conjugate())

    @property
    def unit_circle_residual(self) -> float:
        return max(abs(self.past.modulus - 1.0), abs(self.future.modulus - 1.0))

    @property
    def now_fixed_point_residual(self) -> float:
        now_point = TemporalConformalPoint(self.now, self.now, self.scale)
        return abs(now_point.z + 1.0)

    @property
    def passed(self) -> bool:
        return max(
            self.inversion_residual,
            self.conjugation_residual,
            self.unit_circle_residual,
            self.now_fixed_point_residual,
        ) <= self.tolerance

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TEMPORAL_DUAL_PAIR_SCHEMA,
            "contract_id": TEMPORAL_GEOMETRY_CONTRACT_ID,
            "epistemic_status": EPISTEMIC_STATUS,
            "now": self.now,
            "delta": self.delta,
            "scale": self.scale,
            "past_point_id": self.past.point_id,
            "future_point_id": self.future.point_id,
            "past_z": self.past.z,
            "future_z": self.future.z,
            "inversion_residual": self.inversion_residual,
            "conjugation_residual": self.conjugation_residual,
            "unit_circle_residual": self.unit_circle_residual,
            "now_fixed_point_residual": self.now_fixed_point_residual,
            "passed": self.passed,
            "invariant": "t-now -> -(t-now) implies z_T -> 1/z_T; NOW maps to z_T=-1",
        }

    @property
    def receipt_id(self) -> str:
        return _typed_id("pncs:temporal-dual-pair", self.payload)


@dataclass(frozen=True, slots=True)
class TemporalPhaseProjection36:
    times: tuple[float, ...]
    now: float
    scale: float = 1.0

    def __init__(self, times: Sequence[float], now: float, scale: float = 1.0) -> None:
        vals = tuple(_finite(v, "times") for v in times)
        if len(vals) != DIM:
            raise TemporalGeometryV02Error(f"times must contain exactly {DIM} values")
        if any(b <= a for a, b in zip(vals, vals[1:])):
            raise TemporalGeometryV02Error("times must be strictly increasing")
        object.__setattr__(self, "times", vals)
        object.__setattr__(self, "now", _finite(now, "now"))
        object.__setattr__(self, "scale", _positive(scale, "scale"))

    @property
    def points(self) -> tuple[TemporalConformalPoint, ...]:
        return tuple(TemporalConformalPoint(t, self.now, self.scale) for t in self.times)

    @property
    def theta(self) -> tuple[float, ...]:
        return tuple(point.phase for point in self.points)

    @property
    def z_coordinates(self) -> tuple[complex, ...]:
        return tuple(point.z for point in self.points)

    @property
    def branches(self) -> tuple[str, ...]:
        return tuple(point.branch for point in self.points)

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TEMPORAL_T36_SCHEMA,
            "contract_id": TEMPORAL_GEOMETRY_CONTRACT_ID,
            "epistemic_status": EPISTEMIC_STATUS,
            "promotion_track": PROMOTION_TRACK,
            "space": "T^36",
            "coordinate_semantics": "temporal_cayley_phase_radians",
            "times": list(self.times),
            "now": self.now,
            "scale": self.scale,
            "theta": list(self.theta),
            "z_coordinates": list(self.z_coordinates),
            "branches": list(self.branches),
            "projection_scope": "PURE_TEMPORAL_PHASE_PROJECTION",
        }

    @property
    def projection_id(self) -> str:
        return _typed_id("pncs:temporal-t36-projection", self.payload)

    def to_phase_flow_state36(self, *, phase_proper_time: float = 0.0):
        try:
            from .hydro_time_v27 import PhaseFlowState36
        except ImportError:  # isolated harness compatibility
            from hydro_time_v27 import PhaseFlowState36  # type: ignore
        return PhaseFlowState36(self.theta, velocity=(0.0,) * DIM, phase_proper_time=phase_proper_time)




@dataclass(frozen=True, slots=True)
class TemporalDualPairProjection36:
    deltas: tuple[float, ...]
    now: float
    scale: float = 1.0

    def __init__(self, deltas: Sequence[float], now: float, scale: float = 1.0) -> None:
        vals = tuple(_finite(v, "deltas") for v in deltas)
        if len(vals) != DIM // 2:
            raise TemporalGeometryV02Error("deltas must contain exactly 18 values")
        if any(v < 0.0 for v in vals):
            raise TemporalGeometryV02Error("deltas must be non-negative")
        if any(b <= a for a, b in zip(vals, vals[1:])):
            raise TemporalGeometryV02Error("deltas must be strictly increasing")
        object.__setattr__(self, "deltas", vals)
        object.__setattr__(self, "now", _finite(now, "now"))
        object.__setattr__(self, "scale", _positive(scale, "scale"))

    @property
    def time_pairs(self) -> tuple[tuple[float, float], ...]:
        return tuple((self.now - d, self.now + d) for d in self.deltas)

    @property
    def z_pairs(self) -> tuple[tuple[complex, complex], ...]:
        out: list[tuple[complex, complex]] = []
        for delta in self.deltas:
            past_z = _temporal_z_from_u(-delta / self.scale)
            future_from_invariant = 1.0 / past_z
            out.append((past_z, future_from_invariant))
        return tuple(out)

    @property
    def theta(self) -> tuple[float, ...]:
        out: list[float] = []
        for past_z, future_z in self.z_pairs:
            out.extend((_phase(past_z), _phase(future_z)))
        return tuple(out)

    @property
    def verification_residual(self) -> float:
        residual = 0.0
        for delta, (past_z, future_z) in zip(self.deltas, self.z_pairs):
            direct_future = TemporalConformalPoint(self.now + delta, self.now, self.scale).z
            residual = max(
                residual,
                abs(future_z - direct_future),
                abs(future_z - past_z.conjugate()),
                abs(abs(past_z) - 1.0),
                abs(abs(future_z) - 1.0),
            )
        return residual

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": "PNCS_TEMPORAL_DUAL_T36_PROJECTION_V0_2",
            "contract_id": TEMPORAL_GEOMETRY_CONTRACT_ID,
            "epistemic_status": EPISTEMIC_STATUS,
            "promotion_track": PROMOTION_TRACK,
            "space": "T^36",
            "pair_count": DIM // 2,
            "deltas": list(self.deltas),
            "now": self.now,
            "scale": self.scale,
            "time_pairs": [list(pair) for pair in self.time_pairs],
            "z_pairs": [[past, future] for past, future in self.z_pairs],
            "theta": list(self.theta),
            "verification_residual": self.verification_residual,
            "construction": "18 past points + inversion-derived future partners",
            "projection_scope": "PURE_TEMPORAL_DUAL_PAIR_PHASE_PROJECTION",
        }

    @property
    def projection_id(self) -> str:
        return _typed_id("pncs:temporal-dual-t36-projection", self.payload)


def _normalize_amplitudes(values: Sequence[complex]) -> tuple[complex, ...]:
    vals = tuple(_finite_complex(v, "amplitudes") for v in values)
    if len(vals) != DIM:
        raise TemporalGeometryV02Error(f"amplitudes must contain exactly {DIM} values")
    norm2 = sum(abs(v) ** 2 for v in vals)
    if not math.isfinite(norm2) or norm2 <= 0.0:
        raise TemporalGeometryV02Error("amplitudes must have non-zero finite norm")
    norm = math.sqrt(norm2)
    return tuple(v / norm for v in vals)


@dataclass(frozen=True, slots=True)
class TemporalWaveState36:
    times: tuple[float, ...]
    amplitudes: tuple[complex, ...]
    now: float
    scale: float = 1.0

    def __init__(self, times: Sequence[float], amplitudes: Sequence[complex], now: float, scale: float = 1.0) -> None:
        projection = TemporalPhaseProjection36(times, now, scale)
        object.__setattr__(self, "times", projection.times)
        object.__setattr__(self, "amplitudes", _normalize_amplitudes(amplitudes))
        object.__setattr__(self, "now", projection.now)
        object.__setattr__(self, "scale", projection.scale)

    @property
    def projection(self) -> TemporalPhaseProjection36:
        return TemporalPhaseProjection36(self.times, self.now, self.scale)

    @property
    def probabilities(self) -> tuple[float, ...]:
        return tuple(float(abs(a) ** 2) for a in self.amplitudes)

    @property
    def probability_total(self) -> float:
        return sum(self.probabilities)

    @property
    def past_probability(self) -> float:
        return sum(p for t, p in zip(self.times, self.probabilities) if t < self.now)

    @property
    def now_probability(self) -> float:
        return sum(p for t, p in zip(self.times, self.probabilities) if t == self.now)

    @property
    def future_probability(self) -> float:
        return sum(p for t, p in zip(self.times, self.probabilities) if t > self.now)

    @property
    def temporal_variance(self) -> float:
        return sum(p * (t - self.now) ** 2 for t, p in zip(self.times, self.probabilities))

    @property
    def support_size(self) -> int:
        return sum(1 for a in self.amplitudes if abs(a) > 1e-15)

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TEMPORAL_WAVE36_SCHEMA,
            "contract_id": TEMPORAL_GEOMETRY_CONTRACT_ID,
            "epistemic_status": EPISTEMIC_STATUS,
            "promotion_track": PROMOTION_TRACK,
            "projection_id": self.projection.projection_id,
            "times": list(self.times),
            "now": self.now,
            "scale": self.scale,
            "amplitudes": list(self.amplitudes),
            "probabilities": list(self.probabilities),
            "past_probability": self.past_probability,
            "now_probability": self.now_probability,
            "future_probability": self.future_probability,
            "temporal_variance": self.temporal_variance,
            "support_size": self.support_size,
            "state_scope": "COMPUTATIONAL_TEMPORAL_WAVE_STATE",
        }

    @property
    def state_id(self) -> str:
        return _typed_id("pncs:temporal-wave36-state", self.payload)


@dataclass(frozen=True, slots=True)
class TemporalObservationReceipt:
    mode: str
    before_state_id: str
    after_state: TemporalWaveState36
    kernel_sigma: float | None
    selected_index: int | None
    pre_variance: float
    post_variance: float
    pre_support: int
    post_support: int

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TEMPORAL_OBSERVATION_SCHEMA,
            "contract_id": TEMPORAL_GEOMETRY_CONTRACT_ID,
            "epistemic_status": EPISTEMIC_STATUS,
            "promotion_track": PROMOTION_TRACK,
            "mode": self.mode,
            "before_state_id": self.before_state_id,
            "after_state_id": self.after_state.state_id,
            "kernel_sigma": self.kernel_sigma,
            "selected_index": self.selected_index,
            "observation_time": self.after_state.now,
            "pre_variance": self.pre_variance,
            "post_variance": self.post_variance,
            "pre_support": self.pre_support,
            "post_support": self.post_support,
            "observation_scope": "COMPUTATIONAL_TEMPORAL_LOCALIZATION",
        }

    @property
    def receipt_id(self) -> str:
        return _typed_id("pncs:temporal-observation", self.payload)


def project_observation_now(state: TemporalWaveState36) -> TemporalObservationReceipt:
    if not isinstance(state, TemporalWaveState36):
        raise TemporalGeometryV02Error("state must be TemporalWaveState36")
    matches = [i for i, t in enumerate(state.times) if t == state.now]
    if len(matches) != 1:
        raise TemporalGeometryV02Error("exact NOW projector requires exactly one sample at now")
    idx = matches[0]
    source = state.amplitudes[idx]
    phase = source / abs(source) if abs(source) > 0.0 else (1.0 + 0.0j)
    amplitudes = [0.0j] * DIM
    amplitudes[idx] = phase
    after = TemporalWaveState36(state.times, amplitudes, state.now, state.scale)
    return TemporalObservationReceipt(
        mode="EXACT_NOW_PROJECTOR",
        before_state_id=state.state_id,
        after_state=after,
        kernel_sigma=None,
        selected_index=idx,
        pre_variance=state.temporal_variance,
        post_variance=after.temporal_variance,
        pre_support=state.support_size,
        post_support=after.support_size,
    )


def gaussian_observation_now(state: TemporalWaveState36, sigma: float) -> TemporalObservationReceipt:
    if not isinstance(state, TemporalWaveState36):
        raise TemporalGeometryV02Error("state must be TemporalWaveState36")
    s = _positive(sigma, "sigma")
    exponents = [-0.25 * ((t - state.now) / s) ** 2 for t in state.times]
    shift = max(exponents)
    weights = [math.exp(x - shift) for x in exponents]
    amplitudes = [a * w for a, w in zip(state.amplitudes, weights)]
    after = TemporalWaveState36(state.times, amplitudes, state.now, state.scale)
    return TemporalObservationReceipt(
        mode="FINITE_GAUSSIAN_NOW_LOCALIZATION",
        before_state_id=state.state_id,
        after_state=after,
        kernel_sigma=s,
        selected_index=None,
        pre_variance=state.temporal_variance,
        post_variance=after.temporal_variance,
        pre_support=state.support_size,
        post_support=after.support_size,
    )


@dataclass(frozen=True, slots=True)
class TemporalWaveCorpuscleReceipt:
    source_state: TemporalWaveState36
    observation: TemporalObservationReceipt

    def __post_init__(self) -> None:
        if self.observation.before_state_id != self.source_state.state_id:
            raise TemporalGeometryV02Error("observation/source state mismatch")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TEMPORAL_WAVE_CORPUSCLE_SCHEMA,
            "contract_id": TEMPORAL_GEOMETRY_CONTRACT_ID,
            "epistemic_status": EPISTEMIC_STATUS,
            "promotion_track": PROMOTION_TRACK,
            "source_state_id": self.source_state.state_id,
            "observation_receipt_id": self.observation.receipt_id,
            "wave_support_before": self.source_state.support_size,
            "localized_support_after": self.observation.after_state.support_size,
            "past_probability_before": self.source_state.past_probability,
            "now_probability_before": self.source_state.now_probability,
            "future_probability_before": self.source_state.future_probability,
            "now_probability_after": self.observation.after_state.now_probability,
            "pre_variance": self.observation.pre_variance,
            "post_variance": self.observation.post_variance,
            "measurement_scope": "TEMPORAL_WAVE_TO_LOCALIZED_NOW_RECEIPT",
        }

    @property
    def receipt_id(self) -> str:
        return _typed_id("pncs:temporal-wave-corpuscle", self.payload)
