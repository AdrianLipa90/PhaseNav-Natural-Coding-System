from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from numbers import Real
from typing import Any, Mapping, Sequence

from .semantic_orbital_carrier_v01 import SemanticOrbitalBinding


SCHEMA = "PNCS_SEMANTIC_ORBITAL_TRAJECTORY_V0_1"
TRAPEZOIDAL_PROFILE = "TRAPEZOIDAL_PHASE_RATE_V0_1"


class SemanticOrbitalTrajectoryError(ValueError):
    pass


def _finite(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise SemanticOrbitalTrajectoryError(f"{name} must be finite real")
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise SemanticOrbitalTrajectoryError(f"{name} must be finite real") from exc
    if not math.isfinite(out):
        raise SemanticOrbitalTrajectoryError(f"{name} must be finite real")
    return out


def _profile(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise SemanticOrbitalTrajectoryError(
            "phase-rate profile id must be an exact non-empty string"
        )
    if value != TRAPEZOIDAL_PROFILE:
        raise SemanticOrbitalTrajectoryError(
            f"unsupported phase-rate profile: {value}"
        )
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
        return _finite(
            "lifted_phase",
            self.binding.sample.phi + (2.0 * math.pi * self.winding),
        )

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
        frozen_source = binding.body()["source_orbital_state"]
        if not isinstance(frozen_source, Mapping) or "winding" not in frozen_source:
            raise SemanticOrbitalTrajectoryError(
                "explicit winding or frozen source provenance winding is required"
            )
        winding = _finite("source winding", frozen_source["winding"])
    return SemanticOrbitalTrajectoryPoint(binding=binding, winding=winding)


def _validate_points(
    points: Sequence[SemanticOrbitalTrajectoryPoint],
) -> tuple[SemanticOrbitalTrajectoryPoint, ...]:
    if not isinstance(points, (tuple, list)):
        raise SemanticOrbitalTrajectoryError(
            "trajectory points must be an explicit list or tuple"
        )
    clean = tuple(points)
    if len(clean) < 2:
        raise SemanticOrbitalTrajectoryError(
            "trajectory requires at least two points"
        )
    if not all(isinstance(p, SemanticOrbitalTrajectoryPoint) for p in clean):
        raise SemanticOrbitalTrajectoryError(
            "trajectory points must be SemanticOrbitalTrajectoryPoint"
        )

    first = clean[0].binding.sample
    for point in clean[1:]:
        sample = point.binding.sample
        if sample.kaku_id != first.kaku_id:
            raise SemanticOrbitalTrajectoryError(
                "trajectory must preserve one KAKU id"
            )
        if sample.content_id != first.content_id:
            raise SemanticOrbitalTrajectoryError(
                "trajectory must preserve one content id"
            )

    times = [p.binding.sample.sample_time for p in clean]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise SemanticOrbitalTrajectoryError(
            "trajectory sample times must be strictly increasing"
        )
    return clean


def trajectory_segments(
    points: Sequence[SemanticOrbitalTrajectoryPoint],
    *,
    profile_id: str = TRAPEZOIDAL_PROFILE,
) -> tuple[dict[str, float], ...]:
    clean = _validate_points(points)
    profile = _profile(profile_id)

    out: list[dict[str, float]] = []
    for left, right in zip(clean, clean[1:]):
        l = left.binding.sample
        r = right.binding.sample
        delta_t = _finite("delta_t", r.sample_time - l.sample_time)
        delta_lifted_phase = _finite(
            "delta_lifted_phase", right.lifted_phase - left.lifted_phase
        )
        integrated_phase = _finite(
            "integrated_phase_from_omega",
            0.5 * (l.omega + r.omega) * delta_t,
        )
        residual = _finite(
            "phase_residual", delta_lifted_phase - integrated_phase
        )
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
    clean = _validate_points(points)
    tolerance_value = _finite("tolerance", tolerance)
    if tolerance_value < 0.0:
        raise SemanticOrbitalTrajectoryError("tolerance must be non-negative")
    profile = _profile(profile_id)
    segments = trajectory_segments(clean, profile_id=profile)
    max_abs_residual = _finite(
        "max_abs_phase_residual",
        max(abs(s["phase_residual"]) for s in segments),
    )
    consistency = "PASS" if max_abs_residual <= tolerance_value else "FAIL"
    body = {
        "schema": SCHEMA,
        "phase_rate_profile_id": profile,
        "kaku_id": clean[0].binding.sample.kaku_id,
        "content_id": clean[0].binding.sample.content_id,
        "points": [point.to_dict() for point in clean],
        "segments": list(segments),
        "tolerance": tolerance_value,
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
