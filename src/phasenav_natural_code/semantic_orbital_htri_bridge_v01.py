from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Any, Mapping

import numpy as np

from .semantic_htri_drive_v32 import (
    DEFAULT_DT,
    N as HTRI_N,
    TAU,
    ControlledStep,
    DriveSnapshot,
    array_sha,
    controlled_step,
    digest,
)
from .semantic_orbital_carrier_v01 import SemanticOrbitalBinding


SCHEMA = "PNCS_SEMANTIC_ORBITAL_HTRI_BRIDGE_V0_1"
ASSIGN_SAMPLE_OMEGA = "ASSIGN_SAMPLE_OMEGA"
PRESERVE_SNAPSHOT_OMEGA = "PRESERVE_SNAPSHOT_OMEGA"
_FREQUENCY_MODES = frozenset({ASSIGN_SAMPLE_OMEGA, PRESERVE_SNAPSHOT_OMEGA})


class SemanticOrbitalHTRIBridgeError(ValueError):
    pass


def _text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticOrbitalHTRIBridgeError(f"{name} must be a non-empty string")
    return value.strip()


def _positive_real(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise SemanticOrbitalHTRIBridgeError(f"{name} must be positive finite real")
    out = float(value)
    if not math.isfinite(out) or out <= 0.0:
        raise SemanticOrbitalHTRIBridgeError(f"{name} must be positive finite real")
    return out


@dataclass(frozen=True)
class SemanticHTRILaneProfile:
    lane_profile_id: str
    kaku_to_lane: Mapping[str, int]
    frequency_binding: str = ASSIGN_SAMPLE_OMEGA

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "lane_profile_id",
            _text("lane_profile_id", self.lane_profile_id),
        )
        if not isinstance(self.kaku_to_lane, Mapping):
            raise SemanticOrbitalHTRIBridgeError("kaku_to_lane must be a mapping")
        mapping: dict[str, int] = {}
        for raw_kaku, raw_lane in self.kaku_to_lane.items():
            kaku = _text("kaku_id", raw_kaku)
            if kaku in mapping:
                raise SemanticOrbitalHTRIBridgeError(
                    f"duplicate normalized KAKU id in lane profile: {kaku}"
                )
            if isinstance(raw_lane, bool) or not isinstance(raw_lane, (int, np.integer)):
                raise SemanticOrbitalHTRIBridgeError(
                    f"lane for {kaku} must be an integer"
                )
            lane = int(raw_lane)
            if not 0 <= lane < HTRI_N:
                raise SemanticOrbitalHTRIBridgeError(
                    f"lane for {kaku} must be in [0,{HTRI_N - 1}]"
                )
            mapping[kaku] = lane
        if not mapping:
            raise SemanticOrbitalHTRIBridgeError("at least one KAKU lane is required")
        if len(set(mapping.values())) != len(mapping):
            raise SemanticOrbitalHTRIBridgeError("HTRI lane collisions are rejected in v0.1")
        mode = _text("frequency_binding", self.frequency_binding).upper()
        if mode not in _FREQUENCY_MODES:
            raise SemanticOrbitalHTRIBridgeError(
                f"unsupported frequency_binding: {self.frequency_binding}"
            )
        object.__setattr__(self, "kaku_to_lane", mapping)
        object.__setattr__(self, "frequency_binding", mode)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane_profile_id": self.lane_profile_id,
            "frequency_binding": self.frequency_binding,
            "kaku_to_lane": {
                k: self.kaku_to_lane[k] for k in sorted(self.kaku_to_lane)
            },
        }


def _validate_bindings(
    bindings: Mapping[str, SemanticOrbitalBinding],
    profile: SemanticHTRILaneProfile,
) -> dict[str, SemanticOrbitalBinding]:
    if not isinstance(profile, SemanticHTRILaneProfile):
        raise SemanticOrbitalHTRIBridgeError("profile must be SemanticHTRILaneProfile")
    if not isinstance(bindings, Mapping):
        raise SemanticOrbitalHTRIBridgeError("bindings must be a mapping")
    expected = set(profile.kaku_to_lane)
    supplied = set(bindings)
    if expected != supplied:
        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        raise SemanticOrbitalHTRIBridgeError(
            f"semantic lane binding coverage mismatch: missing={missing}, extra={extra}"
        )
    out: dict[str, SemanticOrbitalBinding] = {}
    for kaku_id in sorted(expected):
        binding = bindings[kaku_id]
        if not isinstance(binding, SemanticOrbitalBinding):
            raise SemanticOrbitalHTRIBridgeError(
                f"binding for {kaku_id} must be SemanticOrbitalBinding"
            )
        if binding.sample.kaku_id != kaku_id:
            raise SemanticOrbitalHTRIBridgeError(
                f"binding KAKU id mismatch for lane assignment {kaku_id}"
            )
        out[kaku_id] = binding
    return out


def build_semantic_htri_target(
    snapshot: DriveSnapshot,
    bindings: Mapping[str, SemanticOrbitalBinding],
    profile: SemanticHTRILaneProfile,
) -> np.ndarray:
    if not isinstance(snapshot, DriveSnapshot):
        raise SemanticOrbitalHTRIBridgeError("snapshot must be DriveSnapshot")
    clean = _validate_bindings(bindings, profile)
    target = snapshot.phi.copy()
    for kaku_id, binding in clean.items():
        target[profile.kaku_to_lane[kaku_id]] = binding.sample.phi % TAU
    return target


def build_semantic_htri_snapshot(
    snapshot: DriveSnapshot,
    bindings: Mapping[str, SemanticOrbitalBinding],
    profile: SemanticHTRILaneProfile,
) -> DriveSnapshot:
    if not isinstance(snapshot, DriveSnapshot):
        raise SemanticOrbitalHTRIBridgeError("snapshot must be DriveSnapshot")
    clean = _validate_bindings(bindings, profile)
    omega = snapshot.omega.copy()
    if profile.frequency_binding == ASSIGN_SAMPLE_OMEGA:
        for kaku_id, binding in clean.items():
            omega[profile.kaku_to_lane[kaku_id]] = binding.sample.omega

    source_id = "pncs:semantic-htri-bridge:sha256:" + digest(
        {
            "source_snapshot_id": snapshot.snapshot_id,
            "lane_profile": profile.to_dict(),
            "semantic_binding_receipts": {
                k: clean[k].deterministic_receipt()["receipt_sha256"]
                for k in sorted(clean)
            },
        }
    )
    return DriveSnapshot.build(
        phi=snapshot.phi,
        omega=omega,
        g=snapshot.g,
        flavor=snapshot.flavor,
        tau=snapshot.tau,
        gravity=snapshot.gravity,
        source_id=source_id,
    )


@dataclass(frozen=True)
class SemanticOrbitalHTRIBridgeResult:
    source_snapshot: DriveSnapshot
    drive_snapshot: DriveSnapshot
    target36: np.ndarray
    controlled: ControlledStep
    receipt: Mapping[str, Any]


def execute_semantic_orbital_htri_bridge(
    snapshot: DriveSnapshot,
    bindings: Mapping[str, SemanticOrbitalBinding],
    profile: SemanticHTRILaneProfile,
    *,
    dt: float = DEFAULT_DT,
) -> SemanticOrbitalHTRIBridgeResult:
    clean = _validate_bindings(bindings, profile)
    dt_value = _positive_real("dt", dt)

    target = build_semantic_htri_target(snapshot, clean, profile)
    drive_snapshot = build_semantic_htri_snapshot(snapshot, clean, profile)
    step = controlled_step(drive_snapshot, target, dt=dt_value)

    assigned_lanes = set(profile.kaku_to_lane.values())
    unassigned = np.asarray(
        [lane for lane in range(HTRI_N) if lane not in assigned_lanes],
        dtype=np.intp,
    )
    if unassigned.size:
        if not np.array_equal(target[unassigned], snapshot.phi[unassigned]):
            raise SemanticOrbitalHTRIBridgeError(
                "unassigned target phase lanes must preserve source snapshot"
            )
        if not np.array_equal(
            drive_snapshot.omega[unassigned], snapshot.omega[unassigned]
        ):
            raise SemanticOrbitalHTRIBridgeError(
                "unassigned frequency lanes must preserve source snapshot"
            )

    if not np.array_equal(drive_snapshot.g, snapshot.g):
        raise SemanticOrbitalHTRIBridgeError("derived snapshot g changed during binding")
    if not np.array_equal(drive_snapshot.flavor, snapshot.flavor):
        raise SemanticOrbitalHTRIBridgeError("derived snapshot flavor changed during binding")
    if not np.array_equal(drive_snapshot.tau, snapshot.tau):
        raise SemanticOrbitalHTRIBridgeError("derived snapshot tau changed during binding")
    if not np.array_equal(drive_snapshot.gravity, snapshot.gravity):
        raise SemanticOrbitalHTRIBridgeError("derived snapshot gravity changed during binding")

    assignments: list[dict[str, Any]] = []
    for kaku_id in sorted(clean):
        binding = clean[kaku_id]
        lane = profile.kaku_to_lane[kaku_id]
        semantic_receipt = binding.deterministic_receipt()
        assignments.append(
            {
                "kaku_id": kaku_id,
                "content_id": binding.sample.content_id,
                "lane": lane,
                "orbital_band": binding.orbital_band,
                "B": binding.sample.B,
                "omega": binding.sample.omega,
                "N": binding.sample.N,
                "A_R": binding.sample.A_R,
                "phi": binding.sample.phi,
                "semantic_value": binding.sample.value,
                "semantic_carrier_receipt_sha256": semantic_receipt["receipt_sha256"],
                "target_phase": float(target[lane]),
                "drive_omega": float(drive_snapshot.omega[lane]),
            }
        )

    body: dict[str, Any] = {
        "schema": SCHEMA,
        "parent_drive_contract": "PNCS_ORDERED_T36_TO_HTRI_DRIVE_V0_32",
        "source_snapshot_id": snapshot.snapshot_id,
        "drive_snapshot_id": drive_snapshot.snapshot_id,
        "lane_profile": profile.to_dict(),
        "assignments": assignments,
        "target36_sha256": array_sha(target),
        "source_phi_sha256": array_sha(snapshot.phi),
        "source_omega_sha256": array_sha(snapshot.omega),
        "drive_omega_sha256": array_sha(drive_snapshot.omega),
        "unassigned_lanes_preserved": True,
        "g_preserved": True,
        "flavor_preserved": True,
        "tau_preserved": True,
        "gravity_preserved": True,
        "parent_controlled_step_receipt": dict(step.receipt),
        "max_target_residual_rad": step.receipt["max_target_residual_rad"],
        "semantic_authority": "EXPLICIT_KAKU_CONTENT_AND_LANE_BINDING",
        "epistemic_state": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "live_surface_writes": 0,
    }
    receipt = {**body, "receipt_sha256": digest(body)}
    return SemanticOrbitalHTRIBridgeResult(
        source_snapshot=snapshot,
        drive_snapshot=drive_snapshot,
        target36=target,
        controlled=step,
        receipt=receipt,
    )
