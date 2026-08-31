import math

import pytest

from phasenav_natural_code.semantic_orbital_carrier_v01 import (
    DEFAULT_BANDS,
    OrbitQuantizerProfile,
    SemanticCarrierSample,
    bind_semantic_sample,
)
from phasenav_natural_code.semantic_orbital_trajectory_v01 import (
    SemanticOrbitalTrajectoryError,
    SemanticOrbitalTrajectoryPoint,
    point_from_binding,
    semantic_orbital_trajectory_receipt,
    trajectory_segments,
)


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        "Q.TRAJ.STRICT",
        (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
        DEFAULT_BANDS,
    )


def _binding(
    *,
    t: float,
    phi: float,
    omega: float,
    B: float = 0.0,
    source=None,
):
    sample = SemanticCarrierSample(
        "SEM.TRAJ.STRICT",
        "K.TRAJ.STRICT",
        t,
        B,
        omega,
        1.0,
        1.0,
        phi,
    )
    return bind_semantic_sample(
        sample,
        _quantizer(),
        source_orbital_state=source,
    )


def _points():
    return (
        SemanticOrbitalTrajectoryPoint(
            _binding(t=0.0, phi=0.0, omega=2.0 * math.pi), 0.0
        ),
        SemanticOrbitalTrajectoryPoint(
            _binding(t=1.0, phi=0.0, omega=2.0 * math.pi), 1.0
        ),
    )


def test_default_winding_uses_frozen_carrier_provenance_snapshot():
    source = {"winding": 3.0, "nested": {"marker": "A"}}
    binding = _binding(t=0.0, phi=0.25, omega=1.0, source=source)
    receipt_before = binding.deterministic_receipt()

    source["winding"] = 99.0
    source["nested"]["marker"] = "MUTATED"

    point = point_from_binding(binding)
    receipt_after = binding.deterministic_receipt()
    assert point.winding == pytest.approx(3.0)
    assert receipt_after == receipt_before
    assert receipt_after["source_orbital_state"]["winding"] == pytest.approx(3.0)


def test_explicit_winding_rejects_bool_numeric_string_and_object():
    binding = _binding(t=0.0, phi=0.0, omega=1.0)
    for bad in (True, "1.0", object()):
        with pytest.raises(SemanticOrbitalTrajectoryError, match="winding"):
            SemanticOrbitalTrajectoryPoint(binding, bad)  # type: ignore[arg-type]


def test_frozen_source_winding_is_revalidated_as_exact_real():
    binding = _binding(
        t=0.0,
        phi=0.0,
        omega=1.0,
        source={"winding": "3.0"},
    )
    with pytest.raises(SemanticOrbitalTrajectoryError, match="source winding"):
        point_from_binding(binding)


def test_trajectory_requires_explicit_point_container():
    generator = (point for point in _points())
    with pytest.raises(SemanticOrbitalTrajectoryError, match="explicit list or tuple"):
        trajectory_segments(generator)  # type: ignore[arg-type]


def test_tolerance_and_profile_reject_implicit_coercion():
    for bad in (True, "1e-6", object()):
        with pytest.raises(SemanticOrbitalTrajectoryError, match="tolerance"):
            semantic_orbital_trajectory_receipt(_points(), tolerance=bad)  # type: ignore[arg-type]
    for bad in (True, 123, object()):
        with pytest.raises(SemanticOrbitalTrajectoryError, match="profile"):
            trajectory_segments(_points(), profile_id=bad)  # type: ignore[arg-type]


def test_lifted_phase_overflow_fails_before_receipt_hash():
    point = SemanticOrbitalTrajectoryPoint(
        _binding(t=0.0, phi=0.0, omega=0.0),
        1.0e308,
    )
    with pytest.raises(SemanticOrbitalTrajectoryError, match="lifted_phase"):
        _ = point.lifted_phase


def test_integrated_phase_overflow_fails_before_receipt_hash():
    points = (
        SemanticOrbitalTrajectoryPoint(
            _binding(t=0.0, phi=0.0, omega=1.0e308), 0.0
        ),
        SemanticOrbitalTrajectoryPoint(
            _binding(t=1.0, phi=0.0, omega=1.0e308), 0.0
        ),
    )
    with pytest.raises(
        SemanticOrbitalTrajectoryError,
        match="integrated_phase_from_omega",
    ):
        trajectory_segments(points)
