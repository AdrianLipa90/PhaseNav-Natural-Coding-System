from __future__ import annotations

import math
from numbers import Real
from typing import Any

import numpy as np

from .semantic_htri_drive_v32 import DEFAULT_DT, DriveSnapshot, digest
from .semantic_orbital_carrier_v01 import SemanticOrbitalBinding
from .semantic_orbital_htri_bridge_v01 import (
    ASSIGN_SAMPLE_OMEGA,
    SemanticHTRILaneProfile,
    execute_semantic_orbital_htri_bridge,
)


SCHEMA = "PNCS_SEMANTIC_MAGNITUDE_ACTUATION_FIREWALL_V0_1"
FRONTIER = "SEMANTIC_MAGNITUDE_TO_HTRI_ACTUATION"


class SemanticMagnitudeActuationFirewallError(ValueError):
    pass


def _finite_real(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise SemanticMagnitudeActuationFirewallError(f"{name} must be finite real")
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise SemanticMagnitudeActuationFirewallError(f"{name} must be finite real") from exc
    if not math.isfinite(out):
        raise SemanticMagnitudeActuationFirewallError(f"{name} must be finite real")
    return out


def _positive_real(name: str, value: object) -> float:
    out = _finite_real(name, value)
    if out <= 0.0:
        raise SemanticMagnitudeActuationFirewallError(
            f"{name} must be positive finite real"
        )
    return out


def source_factor_q_bna(binding: SemanticOrbitalBinding) -> float:
    if not isinstance(binding, SemanticOrbitalBinding):
        raise SemanticMagnitudeActuationFirewallError(
            "binding must be SemanticOrbitalBinding"
        )
    sample = binding.sample
    try:
        value = (sample.B * sample.N) / sample.A_R
    except OverflowError as exc:
        raise SemanticMagnitudeActuationFirewallError(
            "Q_BNA must be finite real"
        ) from exc
    return _finite_real("Q_BNA", value)


def _require_magnitude_only_pair(
    left: SemanticOrbitalBinding,
    right: SemanticOrbitalBinding,
) -> None:
    if not isinstance(left, SemanticOrbitalBinding) or not isinstance(
        right, SemanticOrbitalBinding
    ):
        raise SemanticMagnitudeActuationFirewallError(
            "left and right must be SemanticOrbitalBinding"
        )
    a = left.sample
    b = right.sample
    if a.kaku_id != b.kaku_id:
        raise SemanticMagnitudeActuationFirewallError(
            "magnitude-only audit requires one KAKU id"
        )
    if a.content_id != b.content_id:
        raise SemanticMagnitudeActuationFirewallError(
            "magnitude-only audit requires one content id"
        )
    if a.phi != b.phi:
        raise SemanticMagnitudeActuationFirewallError(
            "magnitude-only audit requires identical phi"
        )
    if a.omega != b.omega:
        raise SemanticMagnitudeActuationFirewallError(
            "magnitude-only audit requires identical omega"
        )


def audit_magnitude_only_htri_invariance(
    snapshot: DriveSnapshot,
    left: SemanticOrbitalBinding,
    right: SemanticOrbitalBinding,
    *,
    lane: int,
    lane_profile_id: str = "PNCS.MAGNITUDE.ACTUATION.FIREWALL.V0_1",
    frequency_binding: str = ASSIGN_SAMPLE_OMEGA,
    dt: float = DEFAULT_DT,
) -> dict[str, Any]:
    if not isinstance(snapshot, DriveSnapshot):
        raise SemanticMagnitudeActuationFirewallError(
            "snapshot must be DriveSnapshot"
        )
    _require_magnitude_only_pair(left, right)
    dt_value = _positive_real("dt", dt)

    kaku_id = left.sample.kaku_id
    profile = SemanticHTRILaneProfile(
        lane_profile_id=lane_profile_id,
        kaku_to_lane={kaku_id: lane},
        frequency_binding=frequency_binding,
    )
    left_run = execute_semantic_orbital_htri_bridge(
        snapshot, {kaku_id: left}, profile, dt=dt_value
    )
    right_run = execute_semantic_orbital_htri_bridge(
        snapshot, {kaku_id: right}, profile, dt=dt_value
    )

    array_pairs = {
        "target36": (left_run.target36, right_run.target36),
        "drive_phi": (left_run.drive_snapshot.phi, right_run.drive_snapshot.phi),
        "drive_omega": (left_run.drive_snapshot.omega, right_run.drive_snapshot.omega),
        "drive_g": (left_run.drive_snapshot.g, right_run.drive_snapshot.g),
        "drive_flavor": (
            left_run.drive_snapshot.flavor,
            right_run.drive_snapshot.flavor,
        ),
        "drive_tau": (left_run.drive_snapshot.tau, right_run.drive_snapshot.tau),
        "drive_gravity": (
            left_run.drive_snapshot.gravity,
            right_run.drive_snapshot.gravity,
        ),
        "phi_next": (left_run.controlled.phi_next, right_run.controlled.phi_next),
        "g_next": (left_run.controlled.g_next, right_run.controlled.g_next),
        "gravity_next": (
            left_run.controlled.gravity_next,
            right_run.controlled.gravity_next,
        ),
        "control": (left_run.controlled.control, right_run.controlled.control),
        "qhtri_H": (left_run.controlled.H, right_run.controlled.H),
    }
    equality = {
        name: bool(np.array_equal(a, b)) for name, (a, b) in array_pairs.items()
    }
    all_numeric_equal = all(equality.values())

    body: dict[str, Any] = {
        "schema": SCHEMA,
        "frontier": FRONTIER,
        "frontier_status": "OPEN_SOURCE_BINDING",
        "source_snapshot_id": snapshot.snapshot_id,
        "lane_profile": profile.to_dict(),
        "left": {
            "semantic_carrier_receipt_sha256": left.deterministic_receipt()[
                "receipt_sha256"
            ],
            "B": left.sample.B,
            "N": left.sample.N,
            "A_R": left.sample.A_R,
            "Q_BNA": source_factor_q_bna(left),
            "semantic_value": left.sample.value,
            "orbital_band": left.orbital_band,
            "bridge_receipt_sha256": left_run.receipt["receipt_sha256"],
        },
        "right": {
            "semantic_carrier_receipt_sha256": right.deterministic_receipt()[
                "receipt_sha256"
            ],
            "B": right.sample.B,
            "N": right.sample.N,
            "A_R": right.sample.A_R,
            "Q_BNA": source_factor_q_bna(right),
            "semantic_value": right.sample.value,
            "orbital_band": right.orbital_band,
            "bridge_receipt_sha256": right_run.receipt["receipt_sha256"],
        },
        "numeric_htri_qhtri_equality": equality,
        "all_numeric_actuation_equal": all_numeric_equal,
        "semantic_values_equal": left.sample.value == right.sample.value,
        "orbital_bands_equal": left.orbital_band == right.orbital_band,
        "epistemic_state": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
    }
    return {**body, "receipt_sha256": digest(body)}
