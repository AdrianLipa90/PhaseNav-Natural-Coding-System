import math

import pytest

from phasenav_natural_code.pnlf_orbital_memory_v01 import OrbitalState
from phasenav_natural_code.semantic_orbital_carrier_v01 import (
    DEFAULT_BANDS,
    OrbitQuantizerProfile,
    SemanticCarrierSample,
    bind_orbital_state_sample,
    bind_semantic_sample,
)
from phasenav_natural_code.semantic_orbital_trajectory_v01 import (
    TRAPEZOIDAL_PROFILE,
    SemanticOrbitalTrajectoryError,
    SemanticOrbitalTrajectoryPoint,
    point_from_binding,
    require_phase_rate_consistency,
    semantic_orbital_trajectory_receipt,
    trajectory_segments,
)


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        "Q.TRAJ.TEST",
        (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
        DEFAULT_BANDS,
    )


def _binding(*, t: float, phi: float, omega: float, kaku_id: str = "K.A", content_id: str = "SEM.A"):
    sample = SemanticCarrierSample(
        content_id=content_id,
        kaku_id=kaku_id,
        sample_time=t,
        B=1.0,
        omega=omega,
        N=1.0,
        A_R=1.0,
        phi=phi,
    )
    return bind_semantic_sample(sample, _quantizer())


def _exact_turn_points():
    omega = 2.0 * math.pi
    return (
        SemanticOrbitalTrajectoryPoint(_binding(t=0.0, phi=0.0, omega=omega), 0.0),
        SemanticOrbitalTrajectoryPoint(_binding(t=1.0, phi=0.0, omega=omega), 1.0),
        SemanticOrbitalTrajectoryPoint(_binding(t=2.0, phi=0.0, omega=omega), 2.0),
    )


def test_lifted_phase_preserves_full_turns_hidden_by_wrapped_phase():
    points = _exact_turn_points()
    assert points[0].binding.sample.phi == points[1].binding.sample.phi == 0.0
    assert points[0].lifted_phase == pytest.approx(0.0)
    assert points[1].lifted_phase == pytest.approx(2.0 * math.pi)
    assert points[2].lifted_phase == pytest.approx(4.0 * math.pi)


def test_constant_frequency_full_turns_are_exactly_phase_rate_consistent():
    segments = trajectory_segments(_exact_turn_points())
    assert len(segments) == 2
    for segment in segments:
        assert segment["delta_t"] == pytest.approx(1.0)
        assert segment["delta_lifted_phase"] == pytest.approx(2.0 * math.pi)
        assert segment["integrated_phase_from_omega"] == pytest.approx(2.0 * math.pi)
        assert segment["phase_residual"] == pytest.approx(0.0, abs=1e-15)

    receipt = require_phase_rate_consistency(_exact_turn_points(), tolerance=1e-14)
    assert receipt["phase_rate_consistency"] == "PASS"
    assert receipt["phase_rate_profile_id"] == TRAPEZOIDAL_PROFILE


def test_trapezoidal_frequency_profile_integrates_linear_rate_exactly():
    left = SemanticOrbitalTrajectoryPoint(_binding(t=0.0, phi=0.0, omega=2.0), 0.0)
    right = SemanticOrbitalTrajectoryPoint(_binding(t=1.0, phi=3.0, omega=4.0), 0.0)
    segment = trajectory_segments((left, right))[0]
    assert segment["integrated_phase_from_omega"] == pytest.approx(3.0)
    assert segment["delta_lifted_phase"] == pytest.approx(3.0)
    assert segment["phase_residual"] == pytest.approx(0.0)


def test_inconsistent_winding_or_frequency_is_reported_as_fail():
    omega = 2.0 * math.pi
    points = (
        SemanticOrbitalTrajectoryPoint(_binding(t=0.0, phi=0.0, omega=omega), 0.0),
        SemanticOrbitalTrajectoryPoint(_binding(t=1.0, phi=0.0, omega=omega), 0.0),
    )
    receipt = semantic_orbital_trajectory_receipt(points, tolerance=1e-12)
    assert receipt["phase_rate_consistency"] == "FAIL"
    assert receipt["max_abs_phase_residual"] == pytest.approx(2.0 * math.pi)
    with pytest.raises(SemanticOrbitalTrajectoryError):
        require_phase_rate_consistency(points, tolerance=1e-12)


def test_tolerance_is_explicit_and_non_negative():
    points = (
        SemanticOrbitalTrajectoryPoint(_binding(t=0.0, phi=0.0, omega=1.0), 0.0),
        SemanticOrbitalTrajectoryPoint(_binding(t=1.0, phi=1.0000001, omega=1.0), 0.0),
    )
    assert semantic_orbital_trajectory_receipt(points, tolerance=1e-6)["phase_rate_consistency"] == "PASS"
    assert semantic_orbital_trajectory_receipt(points, tolerance=1e-9)["phase_rate_consistency"] == "FAIL"
    with pytest.raises(SemanticOrbitalTrajectoryError):
        semantic_orbital_trajectory_receipt(points, tolerance=-1.0)


def test_times_must_be_strictly_increasing():
    points = (
        SemanticOrbitalTrajectoryPoint(_binding(t=1.0, phi=0.0, omega=1.0), 0.0),
        SemanticOrbitalTrajectoryPoint(_binding(t=1.0, phi=1.0, omega=1.0), 0.0),
    )
    with pytest.raises(SemanticOrbitalTrajectoryError):
        trajectory_segments(points)


def test_trajectory_preserves_one_kaku_and_content_identity():
    mixed_kaku = (
        SemanticOrbitalTrajectoryPoint(_binding(t=0.0, phi=0.0, omega=1.0), 0.0),
        SemanticOrbitalTrajectoryPoint(_binding(t=1.0, phi=1.0, omega=1.0, kaku_id="K.B"), 0.0),
    )
    with pytest.raises(SemanticOrbitalTrajectoryError):
        trajectory_segments(mixed_kaku)

    mixed_content = (
        SemanticOrbitalTrajectoryPoint(_binding(t=0.0, phi=0.0, omega=1.0), 0.0),
        SemanticOrbitalTrajectoryPoint(_binding(t=1.0, phi=1.0, omega=1.0, content_id="SEM.B"), 0.0),
    )
    with pytest.raises(SemanticOrbitalTrajectoryError):
        trajectory_segments(mixed_content)


def test_unsupported_phase_rate_profile_fails_closed():
    with pytest.raises(SemanticOrbitalTrajectoryError):
        trajectory_segments(_exact_turn_points(), profile_id="UNKNOWN")


def test_point_can_take_winding_from_pnlf_source_provenance():
    state = OrbitalState(
        attractor_id="A.TRAJ",
        orbital_band="O3",
        r_phase=0.2,
        phase=0.5,
        E_bind=-1.0,
        L_phase=0.25,
        semantic_mass=1.0,
        orbit_period=2.0,
        winding=3.0,
        proper_time=4.0,
        memory_affinity=0.7,
        mass_model_id="M.TRAJ",
        orbit_quantizer_id="Q.PNLF.TRAJ",
        proper_time_model_id="TAU.TRAJ",
    )
    binding = bind_orbital_state_sample(
        content_id="SEM.A",
        kaku_id="K.A",
        orbital_state=state,
        B=1.0,
        N=1.0,
        A_R=1.0,
        quantizer=_quantizer(),
    )
    point = point_from_binding(binding)
    assert point.winding == pytest.approx(3.0)
    assert point.lifted_phase == pytest.approx(0.5 + 6.0 * math.pi)


def test_point_requires_explicit_or_provenance_winding():
    binding = _binding(t=0.0, phi=0.0, omega=1.0)
    with pytest.raises(SemanticOrbitalTrajectoryError):
        point_from_binding(binding)


def test_trajectory_receipt_is_deterministic_and_candidate_only():
    a = semantic_orbital_trajectory_receipt(_exact_turn_points(), tolerance=1e-14)
    b = semantic_orbital_trajectory_receipt(_exact_turn_points(), tolerance=1e-14)
    assert a == b
    assert a["epistemic_state"] == "CHYBA"
    assert a["promotion_state"] == "CANDIDATE_ONLY"
    assert a["runtime_execution_authority"] is False
    assert a["canon_write_authority"] is False
    assert len(a["receipt_sha256"]) == 64
