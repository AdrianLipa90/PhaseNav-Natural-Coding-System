from __future__ import annotations

import math
from numbers import Real
from typing import Any, Mapping

import numpy as np

from .semantic_htri_bounded_v33 import (
    REFERENCE_MAX_TICKS_PER_TARGET,
    REFERENCE_SETTLE_CONSECUTIVE,
    REFERENCE_TOLERANCE_RAD,
    REFERENCE_U_MAX,
    TargetTrack,
    track_target,
)
from .semantic_htri_drive_v32 import DEFAULT_DT, DriveSnapshot, digest
from .semantic_orbital_carrier_v01 import SemanticOrbitalBinding
from .semantic_orbital_htri_bridge_v01 import (
    SemanticHTRILaneProfile,
    build_semantic_htri_snapshot,
    build_semantic_htri_target,
)


SCHEMA = "PNCS_SEMANTIC_ORBITAL_HTRI_BOUNDED_TRACK_V0_1"


class SemanticOrbitalHTRIBoundedError(ValueError):
    pass


def _positive_float(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise SemanticOrbitalHTRIBoundedError(f"{name} must be positive finite real")
    out = float(value)
    if not math.isfinite(out) or out <= 0.0:
        raise SemanticOrbitalHTRIBoundedError(f"{name} must be positive finite real")
    return out


def _positive_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise SemanticOrbitalHTRIBoundedError(f"{name} must be a positive integer")
    value = int(value)
    if value < 1:
        raise SemanticOrbitalHTRIBoundedError(f"{name} must be a positive integer")
    return value


def execute_bounded_semantic_orbital_htri_track(
    snapshot: DriveSnapshot,
    bindings: Mapping[str, SemanticOrbitalBinding],
    profile: SemanticHTRILaneProfile,
    *,
    u_max: float = REFERENCE_U_MAX,
    tolerance_rad: float = REFERENCE_TOLERANCE_RAD,
    max_ticks: int = REFERENCE_MAX_TICKS_PER_TARGET,
    settle_consecutive: int = REFERENCE_SETTLE_CONSECUTIVE,
    dt: float = DEFAULT_DT,
) -> dict[str, Any]:
    if not isinstance(snapshot, DriveSnapshot):
        raise SemanticOrbitalHTRIBoundedError("snapshot must be DriveSnapshot")
    u_max = _positive_float("u_max", u_max)
    tolerance_rad = _positive_float("tolerance_rad", tolerance_rad)
    dt = _positive_float("dt", dt)
    max_ticks = _positive_int("max_ticks", max_ticks)
    settle_consecutive = _positive_int("settle_consecutive", settle_consecutive)
    if settle_consecutive > max_ticks:
        raise SemanticOrbitalHTRIBoundedError(
            "settle_consecutive must not exceed max_ticks"
        )

    target = build_semantic_htri_target(snapshot, bindings, profile)
    drive_snapshot = build_semantic_htri_snapshot(snapshot, bindings, profile)
    tracked: TargetTrack = track_target(
        drive_snapshot,
        target,
        u_max=u_max,
        tolerance_rad=tolerance_rad,
        max_ticks=max_ticks,
        settle_consecutive=settle_consecutive,
        dt=dt,
    )

    ticks = tuple(tracked.receipt["ticks"])
    max_control = max((float(t["control_max_abs"]) for t in ticks), default=0.0)
    if max_control > u_max + 1e-12:
        raise SemanticOrbitalHTRIBoundedError(
            "parent bounded control exceeded declared u_max"
        )

    assignments = []
    for kaku_id in sorted(profile.kaku_to_lane):
        binding = bindings[kaku_id]
        assignments.append(
            {
                "kaku_id": kaku_id,
                "content_id": binding.sample.content_id,
                "lane": profile.kaku_to_lane[kaku_id],
                "orbital_band": binding.orbital_band,
                "semantic_carrier_receipt_sha256": binding.deterministic_receipt()[
                    "receipt_sha256"
                ],
                "B": binding.sample.B,
                "omega": binding.sample.omega,
                "N": binding.sample.N,
                "A_R": binding.sample.A_R,
                "phi": binding.sample.phi,
                "semantic_value": binding.sample.value,
            }
        )

    body: dict[str, Any] = {
        "schema": SCHEMA,
        "parent_contract": "PNCS_BOUNDED_MULTI_TICK_HTRI_DRIVE_V0_33",
        "source_snapshot_id": snapshot.snapshot_id,
        "drive_snapshot_id": drive_snapshot.snapshot_id,
        "lane_profile": profile.to_dict(),
        "assignments": assignments,
        "u_max": u_max,
        "tolerance_rad": tolerance_rad,
        "max_ticks": max_ticks,
        "settle_consecutive": settle_consecutive,
        "dt": dt,
        "track_receipt": dict(tracked.receipt),
        "reachability_status": tracked.receipt["status"],
        "max_control_abs": max_control,
        "semantic_magnitude_to_htri_actuation": "OPEN_SOURCE_BINDING",
        "epistemic_state": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "live_surface_writes": 0,
    }
    return {
        **body,
        "receipt_sha256": digest(body),
        "final_phi": tracked.state.phi.copy(),
        "final_g": tracked.state.g.copy(),
        "final_gravity": tracked.state.gravity.copy(),
        "U_total": tracked.U_total.copy(),
    }
