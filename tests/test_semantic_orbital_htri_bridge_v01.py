from __future__ import annotations

import math

import numpy as np
import pytest

from phasenav_natural_code.semantic_htri_drive_v32 import DriveSnapshot
from phasenav_natural_code.semantic_orbital_carrier_v01 import (
    OrbitQuantizerProfile,
    SemanticCarrierSample,
    bind_semantic_sample,
)
from phasenav_natural_code.semantic_orbital_htri_bridge_v01 import (
    ASSIGN_SAMPLE_OMEGA,
    PRESERVE_SNAPSHOT_OMEGA,
    SemanticHTRILaneProfile,
    SemanticOrbitalHTRIBridgeError,
    build_semantic_htri_snapshot,
    build_semantic_htri_target,
    execute_semantic_orbital_htri_bridge,
)


def _snapshot() -> DriveSnapshot:
    phi = np.linspace(0.07, 5.91, 36, dtype=np.float64)
    omega = 39.6 + np.linspace(-0.12, 0.12, 36, dtype=np.float64)
    i = np.arange(36, dtype=np.float64)
    g = 0.18 * np.cos((i[:, None] - i[None, :]) * np.pi / 18.0)
    g = 0.5 * (g + g.T)
    np.fill_diagonal(g, 0.0)
    flavor = np.array([0.31, 0.72, 0.23, 0.56, 0.48, 0.5], dtype=np.float64)
    tau = np.linspace(0.21, 0.49, 36, dtype=np.float64)
    gravity = np.array([0.0, 1.17, 0.3, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float64)
    return DriveSnapshot.build(
        phi=phi,
        omega=omega,
        g=g,
        flavor=flavor,
        tau=tau,
        gravity=gravity,
        source_id="TEST_SEMANTIC_ORBITAL_HTRI_BRIDGE",
    )


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        "Q.SEM.HTRI.TEST",
        (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
    )


def _binding(kaku_id: str, content_id: str, *, phi: float, omega: float, B: float = 2.0):
    return bind_semantic_sample(
        SemanticCarrierSample(
            content_id=content_id,
            kaku_id=kaku_id,
            sample_time=1.0,
            B=B,
            omega=omega,
            N=3.0,
            A_R=4.0,
            phi=phi,
        ),
        _quantizer(),
    )


def _bindings():
    return {
        "K.A": _binding("K.A", "SEM.A", phi=-0.25, omega=7.5, B=2.0),
        "K.B": _binding("K.B", "SEM.B", phi=7.10, omega=-3.25, B=5.0),
    }


def _profile(mode: str = ASSIGN_SAMPLE_OMEGA, *, profile_id: str = "LANE.TEST"):
    return SemanticHTRILaneProfile(
        lane_profile_id=profile_id,
        kaku_to_lane={"K.A": 3, "K.B": 27},
        frequency_binding=mode,
    )


def test_explicit_lane_profile_rejects_collisions_and_invalid_lanes():
    with pytest.raises(SemanticOrbitalHTRIBridgeError):
        SemanticHTRILaneProfile("LANE.BAD", {"K.A": 3, "K.B": 3})
    with pytest.raises(SemanticOrbitalHTRIBridgeError):
        SemanticHTRILaneProfile("LANE.BAD", {"K.A": 36})
    with pytest.raises(SemanticOrbitalHTRIBridgeError):
        SemanticHTRILaneProfile("LANE.BAD", {"K.A": -1})
    with pytest.raises(SemanticOrbitalHTRIBridgeError):
        SemanticHTRILaneProfile("LANE.BAD", {"K.A": 1.5})


def test_lane_profile_requires_exact_semantic_binding_coverage():
    snapshot = _snapshot()
    bindings = _bindings()
    profile = _profile()
    with pytest.raises(SemanticOrbitalHTRIBridgeError):
        build_semantic_htri_target(snapshot, {"K.A": bindings["K.A"]}, profile)
    with pytest.raises(SemanticOrbitalHTRIBridgeError):
        build_semantic_htri_target(
            snapshot,
            {**bindings, "K.EXTRA": bindings["K.A"]},
            profile,
        )


def test_assigned_phase_targets_are_wrapped_and_unassigned_lanes_are_exactly_preserved():
    snapshot = _snapshot()
    bindings = _bindings()
    target = build_semantic_htri_target(snapshot, bindings, _profile())
    assert target[3] == pytest.approx(bindings["K.A"].sample.phi % (2.0 * math.pi))
    assert target[27] == pytest.approx(bindings["K.B"].sample.phi % (2.0 * math.pi))
    unassigned = [i for i in range(36) if i not in {3, 27}]
    assert np.array_equal(target[unassigned], snapshot.phi[unassigned])


def test_assign_sample_omega_changes_only_explicit_frequency_lanes():
    snapshot = _snapshot()
    bindings = _bindings()
    derived = build_semantic_htri_snapshot(snapshot, bindings, _profile(ASSIGN_SAMPLE_OMEGA))
    assert derived.omega[3] == pytest.approx(7.5)
    assert derived.omega[27] == pytest.approx(-3.25)
    unassigned = [i for i in range(36) if i not in {3, 27}]
    assert np.array_equal(derived.omega[unassigned], snapshot.omega[unassigned])
    assert np.array_equal(derived.phi, snapshot.phi)
    assert np.array_equal(derived.g, snapshot.g)
    assert np.array_equal(derived.flavor, snapshot.flavor)
    assert np.array_equal(derived.tau, snapshot.tau)
    assert np.array_equal(derived.gravity, snapshot.gravity)


def test_preserve_snapshot_omega_mode_keeps_complete_frequency_vector():
    snapshot = _snapshot()
    derived = build_semantic_htri_snapshot(
        snapshot,
        _bindings(),
        _profile(PRESERVE_SNAPSHOT_OMEGA),
    )
    assert np.array_equal(derived.omega, snapshot.omega)


def test_existing_v032_controlled_step_hits_semantic_target36():
    result = execute_semantic_orbital_htri_bridge(
        _snapshot(),
        _bindings(),
        _profile(ASSIGN_SAMPLE_OMEGA),
    )
    assert result.receipt["max_target_residual_rad"] < 1e-12
    residual = np.angle(np.exp(1j * (result.target36 - result.controlled.phi_next)))
    assert np.max(np.abs(residual)) < 1e-12
    assert result.receipt["parent_controlled_step_receipt"]["drive_role"] == "EXACT_ONE_STEP_INVERSE_DYNAMICS_REFERENCE"


def test_source_snapshot_is_not_mutated_by_bridge_execution():
    snapshot = _snapshot()
    phi = snapshot.phi.copy()
    omega = snapshot.omega.copy()
    g = snapshot.g.copy()
    flavor = snapshot.flavor.copy()
    tau = snapshot.tau.copy()
    gravity = snapshot.gravity.copy()
    execute_semantic_orbital_htri_bridge(snapshot, _bindings(), _profile())
    assert np.array_equal(snapshot.phi, phi)
    assert np.array_equal(snapshot.omega, omega)
    assert np.array_equal(snapshot.g, g)
    assert np.array_equal(snapshot.flavor, flavor)
    assert np.array_equal(snapshot.tau, tau)
    assert np.array_equal(snapshot.gravity, gravity)


def test_receipt_preserves_semantic_coordinates_and_candidate_authority():
    result = execute_semantic_orbital_htri_bridge(_snapshot(), _bindings(), _profile())
    rec = result.receipt
    by_id = {x["kaku_id"]: x for x in rec["assignments"]}
    assert by_id["K.A"]["content_id"] == "SEM.A"
    assert by_id["K.A"]["lane"] == 3
    assert by_id["K.A"]["B"] == pytest.approx(2.0)
    assert by_id["K.A"]["omega"] == pytest.approx(7.5)
    assert by_id["K.A"]["N"] == pytest.approx(3.0)
    assert by_id["K.A"]["A_R"] == pytest.approx(4.0)
    assert by_id["K.A"]["semantic_value"] == pytest.approx(_bindings()["K.A"].sample.value)
    assert rec["semantic_authority"] == "EXPLICIT_KAKU_CONTENT_AND_LANE_BINDING"
    assert rec["epistemic_state"] == "CHYBA"
    assert rec["promotion_state"] == "CANDIDATE_ONLY"
    assert rec["runtime_execution_authority"] is False
    assert rec["canon_write_authority"] is False
    assert rec["live_surface_writes"] == 0


def test_receipt_is_deterministic_and_lane_or_frequency_profile_changes_identity():
    snapshot = _snapshot()
    bindings = _bindings()
    a = execute_semantic_orbital_htri_bridge(snapshot, bindings, _profile()).receipt
    b = execute_semantic_orbital_htri_bridge(snapshot, bindings, _profile()).receipt
    assert a == b

    changed_id = execute_semantic_orbital_htri_bridge(
        snapshot,
        bindings,
        _profile(profile_id="LANE.OTHER"),
    ).receipt
    preserve_omega = execute_semantic_orbital_htri_bridge(
        snapshot,
        bindings,
        _profile(PRESERVE_SNAPSHOT_OMEGA),
    ).receipt
    assert a["receipt_sha256"] != changed_id["receipt_sha256"]
    assert a["receipt_sha256"] != preserve_omega["receipt_sha256"]


def test_invalid_frequency_mode_and_dt_fail_closed():
    with pytest.raises(SemanticOrbitalHTRIBridgeError):
        SemanticHTRILaneProfile("LANE.BAD", {"K.A": 0}, "MAGIC")
    with pytest.raises(SemanticOrbitalHTRIBridgeError):
        execute_semantic_orbital_htri_bridge(
            _snapshot(),
            _bindings(),
            _profile(),
            dt=0.0,
        )
