from __future__ import annotations

import numpy as np
import pytest

from phasenav_natural_code.semantic_htri_drive_v32 import DriveSnapshot
from phasenav_natural_code.semantic_orbital_carrier_v01 import (
    DEFAULT_BANDS,
    OrbitQuantizerProfile,
    SemanticCarrierSample,
    bind_semantic_sample,
)
from phasenav_natural_code.semantic_orbital_htri_bounded_v01 import (
    SemanticOrbitalHTRIBoundedError,
    execute_bounded_semantic_orbital_htri_track,
)
from phasenav_natural_code.semantic_orbital_htri_bridge_v01 import (
    ASSIGN_SAMPLE_OMEGA,
    SemanticHTRILaneProfile,
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
        source_id="TEST_BOUNDED_SEMANTIC_ORBITAL_HTRI",
    )


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        "Q.BOUNDED.SEM.HTRI",
        (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
        DEFAULT_BANDS,
    )


def _binding():
    return bind_semantic_sample(
        SemanticCarrierSample(
            content_id="SEM.A",
            kaku_id="K.A",
            sample_time=0.0,
            B=2.0,
            omega=7.5,
            N=3.0,
            A_R=4.0,
            phi=1.25,
        ),
        _quantizer(),
    )


def _profile():
    return SemanticHTRILaneProfile(
        "LANE.BOUNDED.TEST",
        {"K.A": 7},
        ASSIGN_SAMPLE_OMEGA,
    )


def test_large_explicit_control_budget_reaches_semantic_target():
    result = execute_bounded_semantic_orbital_htri_track(
        _snapshot(),
        {"K.A": _binding()},
        _profile(),
        u_max=1.0e6,
        tolerance_rad=1.0e-9,
        max_ticks=4,
        settle_consecutive=2,
    )
    assert result["reachability_status"] == "PASS_TARGET_SETTLED"
    assert result["track_receipt"]["ticks_used"] <= 4
    assert result["max_control_abs"] <= 1.0e6
    assert result["track_receipt"]["last_max_target_residual_rad"] <= 1.0e-9


def test_tiny_control_budget_and_one_tick_preserves_timeout_failure():
    result = execute_bounded_semantic_orbital_htri_track(
        _snapshot(),
        {"K.A": _binding()},
        _profile(),
        u_max=1.0e-9,
        tolerance_rad=1.0e-12,
        max_ticks=1,
        settle_consecutive=1,
    )
    assert result["reachability_status"] == "FAIL_TARGET_SETTLING_TIMEOUT"
    assert result["track_receipt"]["ticks_used"] == 1
    assert result["max_control_abs"] <= 1.0e-9 + 1.0e-12


def test_source_snapshot_is_immutable_under_bounded_tracking_wrapper():
    snapshot = _snapshot()
    phi = snapshot.phi.copy()
    omega = snapshot.omega.copy()
    g = snapshot.g.copy()
    gravity = snapshot.gravity.copy()
    execute_bounded_semantic_orbital_htri_track(
        snapshot,
        {"K.A": _binding()},
        _profile(),
        u_max=1.0e6,
        tolerance_rad=1.0e-9,
        max_ticks=3,
        settle_consecutive=2,
    )
    assert np.array_equal(snapshot.phi, phi)
    assert np.array_equal(snapshot.omega, omega)
    assert np.array_equal(snapshot.g, g)
    assert np.array_equal(snapshot.gravity, gravity)


def test_receipt_preserves_semantic_and_bounded_control_provenance():
    result = execute_bounded_semantic_orbital_htri_track(
        _snapshot(),
        {"K.A": _binding()},
        _profile(),
        u_max=500.0,
        tolerance_rad=1.0e-6,
        max_ticks=8,
        settle_consecutive=2,
    )
    assignment = result["assignments"][0]
    assert assignment["kaku_id"] == "K.A"
    assert assignment["content_id"] == "SEM.A"
    assert assignment["lane"] == 7
    assert assignment["B"] == pytest.approx(2.0)
    assert assignment["omega"] == pytest.approx(7.5)
    assert result["u_max"] == pytest.approx(500.0)
    assert result["semantic_magnitude_to_htri_actuation"] == "OPEN_SOURCE_BINDING"
    assert result["epistemic_state"] == "CHYBA"
    assert result["promotion_state"] == "CANDIDATE_ONLY"
    assert result["runtime_execution_authority"] is False
    assert result["canon_write_authority"] is False
    assert result["live_surface_writes"] == 0


def test_receipt_identity_changes_with_control_budget():
    a = execute_bounded_semantic_orbital_htri_track(
        _snapshot(),
        {"K.A": _binding()},
        _profile(),
        u_max=500.0,
        tolerance_rad=1.0e-6,
        max_ticks=8,
        settle_consecutive=2,
    )
    b = execute_bounded_semantic_orbital_htri_track(
        _snapshot(),
        {"K.A": _binding()},
        _profile(),
        u_max=600.0,
        tolerance_rad=1.0e-6,
        max_ticks=8,
        settle_consecutive=2,
    )
    assert a["receipt_sha256"] != b["receipt_sha256"]


def test_invalid_bounded_parameters_fail_closed_before_parent_execution():
    kwargs = dict(
        snapshot=_snapshot(),
        bindings={"K.A": _binding()},
        profile=_profile(),
    )
    with pytest.raises(SemanticOrbitalHTRIBoundedError):
        execute_bounded_semantic_orbital_htri_track(**kwargs, u_max=0.0)
    with pytest.raises(SemanticOrbitalHTRIBoundedError):
        execute_bounded_semantic_orbital_htri_track(**kwargs, tolerance_rad=0.0)
    with pytest.raises(SemanticOrbitalHTRIBoundedError):
        execute_bounded_semantic_orbital_htri_track(**kwargs, max_ticks=0)
    with pytest.raises(SemanticOrbitalHTRIBoundedError):
        execute_bounded_semantic_orbital_htri_track(
            **kwargs,
            max_ticks=2,
            settle_consecutive=3,
        )


def test_bounded_real_parameters_reject_bool_string_and_objects():
    kwargs = dict(
        snapshot=_snapshot(),
        bindings={"K.A": _binding()},
        profile=_profile(),
        max_ticks=2,
        settle_consecutive=1,
    )
    for field in ("u_max", "tolerance_rad", "dt"):
        for bad in (True, "1.0", object()):
            params = {field: bad}
            with pytest.raises(
                SemanticOrbitalHTRIBoundedError,
                match=f"{field} must be positive finite real",
            ):
                execute_bounded_semantic_orbital_htri_track(
                    **kwargs,
                    **params,  # type: ignore[arg-type]
                )


def test_bounded_integer_parameters_reject_bool_and_strings():
    kwargs = dict(
        snapshot=_snapshot(),
        bindings={"K.A": _binding()},
        profile=_profile(),
        u_max=500.0,
        tolerance_rad=1.0e-6,
    )
    for field in ("max_ticks", "settle_consecutive"):
        for bad in (True, "2"):
            params = {field: bad}
            with pytest.raises(SemanticOrbitalHTRIBoundedError, match="positive integer"):
                execute_bounded_semantic_orbital_htri_track(
                    **kwargs,
                    **params,  # type: ignore[arg-type]
                )
