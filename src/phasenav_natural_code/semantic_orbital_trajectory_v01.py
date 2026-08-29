from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Sequence

from .semantic_orbital_carrier_v01 import SemanticOrbitalBinding


SCHEMA = "PNCS_SEMANTIC_ORBITAL_TRAJECTORY_V0_1"
TRAPEZOIDAL_PROFILE = "TRAPEZOIDAL_PHASE_RATE_V0_1"


class SemanticOrbitalTrajectoryError(ValueError):
    pass


def _finite(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise SemanticOrbitalTrajectoryError(f"{name} must be finite")
    return value


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class SemanticOrbitalTrajectoryPoint:
    binding: SemanticOrbitalBinding
    winding: float

    def __post_init__(self) -> None:
        if not isinstance(self.binding, SemanticOrbitalBinding):
            raise SemanticOrbitalTrajectoryError(
                "binding must be SemanticOrbitalBinding"
            )
        object.__setattr__(self, "winding", _finite("winding", self.winding))

    @property
    def lifted_phase(self) -> float:
        return self.binding.sample.phi + (2.0 * math.pi * self.winding)

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_receipt": self.binding.deterministic_receipt(),
            "winding": self.winding,
            "lifted_phase": self.lifted_phase,
        }


def point_from_binding(
    binding: SemanticOrbitalBinding,
    *,
    winding: float | None = None,
) -> SemanticOrbitalTrajectoryPoint:
    if not isinstance(binding, SemanticOrbitalBinding):
        raise SemanticOrbitalTrajectoryError(
            "binding must be SemanticOrbitalBinding"
        )
    if winding is None:
        source = binding.source_orbital_state
        if source is None or "winding" not in source:
            raise SemanticOrbitalTrajectoryError(
                "explicit winding or source_orbital_state winding is required"
            )
        winding = float(source["winding"])
    return SemanticOrbitalTrajectoryPoint(binding=binding, winding=winding)


def _validate_points(
    points: Sequence[SemanticOrbitalTrajectoryPoint],
) -> tuple[SemanticOrbitalTrajectoryPoint, ...]:
    points = tuple(points)
    if len(points) < 2:
        raise SemanticOrbitalTrajectoryError(
            "trajectory requires at least two points"
        )
    if not all(isinstance(p, SemanticOrbitalTrajectoryPoint) for p in points):
        raise SemanticOrbitalTrajectoryError(
            "trajectory points must be SemanticOrbitalTrajectoryPoint"
        )

    first = points[0].binding.sample
    for point in points[1:]:
        sample = point.binding.sample
        if sample.kaku_id != first.kaku_id:
            raise SemanticOrbitalTrajectoryError(
                "trajectory must preserve one KAKU id"
            )
        if sample.content_id != first.content_id:
            raise SemanticOrbitalTrajectoryError(
                "trajectory must preserve one content id"
            )

    times = [p.binding.sample.sample_time for p in points]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise SemanticOrbitalTrajectoryError(
            "trajectory sample times must be strictly increasing"
        )
    return points


def trajectory_segments(
    points: Sequence[SemanticOrbitalTrajectoryPoint],
    *,
    profile_id: str = TRAPEZOIDAL_PROFILE,
) -> tuple[dict[str, float], ...]:
    points = _validate_points(points)
    if profile_id != TRAPEZOIDAL_PROFILE:
        raise SemanticOrbitalTrajectoryError(
            f"unsupported phase-rate profile: {profile_id}"
        )

    out: list[dict[str, float]] = []
    for left, right in zip(points, points[1:]):
        l = left.binding.sample
        r = right.binding.sample
        delta_t = r.sample_time - l.sample_time
        delta_lifted_phase = right.lifted_phase - left.lifted_phase
        integrated_phase = 0.5 * (l.omega + r.omega) * delta_t
        residual = delta_lifted_phase - integrated_phase
        out.append(
            {
                "t_left": l.sample_time,
                "t_right": r.sample_time,
                "delta_t": delta_t,
                "delta_lifted_phase": delta_lifted_phase,
                "integrated_phase_from_omega": integrated_phase,
                "phase_residual": residual,
            }
        )
    return tuple(out)


def semantic_orbital_trajectory_receipt(
    points: Sequence[SemanticOrbitalTrajectoryPoint],
    *,
    tolerance: float = 0.0,
    profile_id: str = TRAPEZOIDAL_PROFILE,
) -> dict[str, Any]:
    points = _validate_points(points)
    tolerance = _finite("tolerance", tolerance)
    if tolerance < 0.0:
        raise SemanticOrbitalTrajectoryError("tolerance must be non-negative")
    segments = trajectory_segments(points, profile_id=profile_id)
    max_abs_residual = max(abs(s["phase_residual"]) for s in segments)
    consistency = "PASS" if max_abs_residual <= tolerance else "FAIL"
    body = {
        "schema": SCHEMA,
        "phase_rate_profile_id": profile_id,
        "kaku_id": points[0].binding.sample.kaku_id,
        "content_id": points[0].binding.sample.content_id,
        "points": [point.to_dict() for point in points],
        "segments": list(segments),
        "tolerance": tolerance,
        "max_abs_phase_residual": max_abs_residual,
        "phase_rate_consistency": consistency,
        "epistemic_state": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
    }
    return {
        **body,
        "receipt_sha256": hashlib.sha256(_canonical_bytes(body)).hexdigest(),
    }


def require_phase_rate_consistency(
    points: Sequence[SemanticOrbitalTrajectoryPoint],
    *,
    tolerance: float = 0.0,
    profile_id: str = TRAPEZOIDAL_PROFILE,
) -> dict[str, Any]:
    receipt = semantic_orbital_trajectory_receipt(
        points,
        tolerance=tolerance,
        profile_id=profile_id,
    )
    if receipt["phase_rate_consistency"] != "PASS":
        raise SemanticOrbitalTrajectoryError(
            "orbital trajectory failed phase-rate consistency"
        )
    return receipt
