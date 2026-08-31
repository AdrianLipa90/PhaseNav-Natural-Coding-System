import pytest

from phasenav_natural_code.semantic_orbital_carrier_v01 import DEFAULT_BANDS, OrbitQuantizerProfile
from phasenav_natural_code.semantic_phase_inverse_v02 import encode_semantic_phase_placement
from phasenav_natural_code.semantic_orbital_trajectory_v03 import (
    INTRABAND_PHASE_TRANSPORT,
    ORBIT_DEMOTE_CANDIDATE,
    ORBIT_PROMOTE_CANDIDATE,
    SemanticOrbitalTrajectoryError,
    build_semantic_orbital_trajectory,
    pnlf_verb_candidate,
    transition_class,
)


def _quantizer(quantizer_id: str = "Q.TRAJ") -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        quantizer_id=quantizer_id,
        boundaries=(-100.0, -10.0, -5.0, -1.0, 0.0, 10.0, 20.0, 30.0),
        bands=DEFAULT_BANDS,
    )


def _placement(t: float, target: float, *, quantizer=None, content_id="SEM.T", kaku_id="K.T"):
    return encode_semantic_phase_placement(
        content_id=content_id,
        kaku_id=kaku_id,
        sample_time=t,
        semantic_target=target,
        B=1.0,
        omega=1.0,
        N=1.0,
        A_R=1.0,
        quantizer=_quantizer() if quantizer is None else quantizer,
    )


def test_transition_class_uses_pnlf_band_strength_order():
    assert transition_class("O5", "O4") == ORBIT_PROMOTE_CANDIDATE
    assert transition_class("O4", "O5") == ORBIT_DEMOTE_CANDIDATE
    assert transition_class("O4", "O4") == INTRABAND_PHASE_TRANSPORT
    assert pnlf_verb_candidate(ORBIT_PROMOTE_CANDIDATE) == "PNLF.ORBIT_PROMOTE"
    assert pnlf_verb_candidate(ORBIT_DEMOTE_CANDIDATE) == "PNLF.ORBIT_DEMOTE"
    assert pnlf_verb_candidate(INTRABAND_PHASE_TRANSPORT) is None


def test_ordered_trajectory_records_exact_adjacent_differences():
    a = _placement(0.0, 0.5)
    b = _placement(2.0, -0.5)
    c = _placement(5.0, 0.25)
    trajectory = build_semantic_orbital_trajectory((a, b, c))
    assert len(trajectory.transitions) == 2

    first, second = trajectory.transitions
    assert first.delta_time == pytest.approx(2.0)
    assert first.delta_semantic == pytest.approx(-1.0)
    assert first.delta_lifted_phase == pytest.approx(
        b.phase_code.lifted_phase - a.phase_code.lifted_phase
    )
    assert first.delta_winding == b.phase_code.winding - a.phase_code.winding
    assert first.kind == ORBIT_PROMOTE_CANDIDATE

    assert second.delta_time == pytest.approx(3.0)
    assert second.delta_semantic == pytest.approx(0.75)
    assert second.kind == ORBIT_DEMOTE_CANDIDATE


def test_intraband_transport_keeps_phase_and_winding_change():
    a = _placement(1.0, 0.1)
    b = _placement(2.0, 7.0)
    assert a.orbital_band == b.orbital_band == "O5"
    transition = build_semantic_orbital_trajectory((a, b)).transitions[0]
    assert transition.kind == INTRABAND_PHASE_TRANSPORT
    assert transition.delta_lifted_phase == pytest.approx(6.9)
    assert transition.delta_winding != 0
    assert transition.to_dict()["pnlf_radical_candidate"] is None


def test_single_sample_trajectory_is_valid_and_has_no_transition():
    trajectory = build_semantic_orbital_trajectory((_placement(1.0, 2.0),))
    assert trajectory.transitions == ()
    receipt = trajectory.deterministic_receipt()
    assert receipt["transitions"] == []


def test_receipt_preserves_carrier_coordinates_and_authority_boundary():
    a = encode_semantic_phase_placement(
        content_id="SEM.WAVE",
        kaku_id="K.WAVE",
        sample_time=0.0,
        semantic_target=1.0,
        B=2.0,
        omega=3.0,
        N=4.0,
        A_R=5.0,
        quantizer=_quantizer(),
    )
    b = encode_semantic_phase_placement(
        content_id="SEM.WAVE",
        kaku_id="K.WAVE",
        sample_time=1.0,
        semantic_target=2.0,
        B=2.5,
        omega=3.5,
        N=4.5,
        A_R=5.5,
        quantizer=_quantizer(),
    )
    receipt = build_semantic_orbital_trajectory((a, b)).deterministic_receipt()
    transition = receipt["transitions"][0]
    assert transition["source_carrier"] == {"B": 2.0, "omega": 3.0, "N": 4.0, "A_R": 5.0}
    assert transition["target_carrier"] == {"B": 2.5, "omega": 3.5, "N": 4.5, "A_R": 5.5}
    assert receipt["epistemic_state"] == "CHYBA"
    assert receipt["promotion_state"] == "CANDIDATE_ONLY"
    assert receipt["runtime_execution_authority"] is False
    assert receipt["canon_write_authority"] is False
    assert receipt["state_memory_write_authority"] is False


def test_trajectory_hash_is_deterministic_and_content_sensitive():
    a = _placement(0.0, 0.5)
    b = _placement(1.0, 1.5)
    c = _placement(1.0, 1.6)
    r1 = build_semantic_orbital_trajectory((a, b)).deterministic_receipt()
    r2 = build_semantic_orbital_trajectory((a, b)).deterministic_receipt()
    r3 = build_semantic_orbital_trajectory((a, c)).deterministic_receipt()
    assert r1 == r2
    assert r1["trajectory_sha256"] != r3["trajectory_sha256"]


def test_nonmonotonic_or_duplicate_time_fails_closed():
    with pytest.raises(SemanticOrbitalTrajectoryError):
        build_semantic_orbital_trajectory((_placement(1.0, 0.5), _placement(1.0, 1.5)))
    with pytest.raises(SemanticOrbitalTrajectoryError):
        build_semantic_orbital_trajectory((_placement(2.0, 0.5), _placement(1.0, 1.5)))


def test_mixed_semantic_identity_fails_closed():
    a = _placement(0.0, 0.5)
    b = _placement(1.0, 1.5, content_id="SEM.OTHER")
    with pytest.raises(SemanticOrbitalTrajectoryError):
        build_semantic_orbital_trajectory((a, b))


def test_mixed_quantizer_provenance_fails_closed():
    a = _placement(0.0, 0.5, quantizer=_quantizer("Q.A"))
    b = _placement(1.0, 1.5, quantizer=_quantizer("Q.B"))
    with pytest.raises(SemanticOrbitalTrajectoryError):
        build_semantic_orbital_trajectory((a, b))


def test_invalid_band_or_transition_class_fails_closed():
    with pytest.raises(SemanticOrbitalTrajectoryError):
        transition_class("O9", "O1")
    with pytest.raises(SemanticOrbitalTrajectoryError):
        pnlf_verb_candidate("UNKNOWN")
    with pytest.raises(SemanticOrbitalTrajectoryError):
        build_semantic_orbital_trajectory(())
