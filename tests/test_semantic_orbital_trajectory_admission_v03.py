import pytest

from phasenav_natural_code.semantic_orbital_carrier_v01 import (
    DEFAULT_BANDS,
    OrbitQuantizerProfile,
)
from phasenav_natural_code.semantic_phase_inverse_v02 import encode_semantic_phase_placement
from phasenav_natural_code.semantic_orbital_trajectory_v03 import (
    SemanticOrbitalTrajectory,
    SemanticOrbitalTrajectoryError,
    build_semantic_orbital_trajectory,
    transition_class,
)


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        quantizer_id="Q.TRAJ.ADMISSION.V03",
        boundaries=(-100.0, -10.0, -5.0, -1.0, 0.0, 10.0, 20.0, 30.0),
        bands=DEFAULT_BANDS,
    )


def _placement(t: float, target: float):
    return encode_semantic_phase_placement(
        content_id="SEM.TRAJ.ADMISSION",
        kaku_id="K.TRAJ.ADMISSION",
        sample_time=t,
        semantic_target=target,
        B=1.0,
        omega=1.0,
        N=1.0,
        A_R=1.0,
        quantizer=_quantizer(),
    )


class _LooksLikeBand:
    def __str__(self):
        return "O4"


def test_transition_band_identity_rejects_string_like_objects():
    with pytest.raises(SemanticOrbitalTrajectoryError, match="exact string"):
        transition_class(_LooksLikeBand(), "O4")
    with pytest.raises(SemanticOrbitalTrajectoryError, match="exact string"):
        transition_class("O4", _LooksLikeBand())


def test_direct_trajectory_snapshots_mutable_placement_list_before_receipt():
    a = _placement(0.0, 0.5)
    b = _placement(1.0, 1.5)
    c = _placement(2.0, 2.5)
    source = [a, b]

    trajectory = SemanticOrbitalTrajectory(source)
    before = trajectory.deterministic_receipt()

    source.append(c)

    assert trajectory.placements == (a, b)
    assert len(trajectory.placements) == 2
    assert trajectory.deterministic_receipt() == before
    assert len(before["samples"]) == 2


def test_direct_trajectory_requires_explicit_list_or_tuple_container():
    a = _placement(0.0, 0.5)
    for bad in ((p for p in (a,)), "placement"):
        with pytest.raises(SemanticOrbitalTrajectoryError, match="list or tuple"):
            SemanticOrbitalTrajectory(bad)


def test_builder_snapshots_input_sequence():
    a = _placement(0.0, 0.5)
    b = _placement(1.0, 1.5)
    c = _placement(2.0, 2.5)
    source = [a, b]

    trajectory = build_semantic_orbital_trajectory(source)
    receipt = trajectory.deterministic_receipt()
    source.append(c)

    assert trajectory.placements == (a, b)
    assert trajectory.deterministic_receipt() == receipt


def test_legal_tuple_receipt_remains_deterministic():
    samples = (_placement(0.0, 0.5), _placement(1.0, 1.5))
    a = SemanticOrbitalTrajectory(samples).deterministic_receipt()
    b = SemanticOrbitalTrajectory(samples).deterministic_receipt()
    assert a == b
    assert len(a["trajectory_sha256"]) == 64
