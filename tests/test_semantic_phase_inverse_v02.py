import math

import pytest

from phasenav_natural_code.semantic_orbital_carrier_v01 import KAPPA, OrbitQuantizerProfile
from phasenav_natural_code.semantic_phase_inverse_v02 import (
    INCONSISTENT_ZERO_CARRIER,
    NON_IDENTIFIABLE_PHASE,
    UNIQUE_LIFTED_PHASE,
    TAU,
    CanonicalPhaseSplit,
    SemanticPhaseInverseError,
    canonical_phase_split,
    encode_semantic_phase_placement,
    inverse_status,
    lifted_phase_from_semantic_value,
    lifted_phase_from_split,
    semantic_value_from_phase_code,
)


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        quantizer_id="Q.SEM.PHASE.TEST",
        boundaries=(-8.0, -4.0, -2.0, -1.0, 0.0, 1.0, 2.0, 4.0),
        bands=tuple(f"O{i}" for i in range(9)),
    )


@pytest.mark.parametrize(
    "target,B,omega,N,A_R",
    [
        (2.25, 2.0, 3.0, 4.0, 5.0),
        (-1.75, 2.0, -3.0, 4.0, 5.0),
        (0.125, -1.5, 2.0, 0.75, -3.0),
    ],
)
def test_exact_nonzero_carrier_inverse_roundtrip(target, B, omega, N, A_R):
    phase = lifted_phase_from_semantic_value(target, B, omega, N, A_R)
    prefactor = (B * omega * N) / A_R
    assert phase == pytest.approx((target / prefactor) - KAPPA)
    assert prefactor * (phase + KAPPA) == pytest.approx(target)
    assert inverse_status(target, B, omega, N, A_R) == UNIQUE_LIFTED_PHASE


@pytest.mark.parametrize(
    "lifted",
    [
        0.0,
        0.25,
        2.0 * math.pi,
        5.0 * math.pi + 0.3,
        -0.25,
        -2.0 * math.pi,
        -5.0 * math.pi - 0.3,
    ],
)
def test_canonical_phase_split_is_lossless(lifted):
    split = canonical_phase_split(lifted)
    assert 0.0 <= split.wrapped_phase < TAU
    assert isinstance(split.winding, int)
    assert lifted_phase_from_split(split.wrapped_phase, split.winding) == pytest.approx(
        lifted, rel=0.0, abs=2.0e-12
    )


def test_negative_small_phase_uses_negative_winding():
    split = canonical_phase_split(-0.25)
    assert split.winding == -1
    assert split.wrapped_phase == pytest.approx(TAU - 0.25)


def test_zero_carrier_identifiability_firewall():
    assert inverse_status(0.0, 0.0, 2.0, 3.0, 4.0) == NON_IDENTIFIABLE_PHASE
    assert inverse_status(1.0, 0.0, 2.0, 3.0, 4.0) == INCONSISTENT_ZERO_CARRIER
    assert inverse_status(0.0, 2.0, 0.0, 3.0, 4.0) == NON_IDENTIFIABLE_PHASE
    assert inverse_status(1.0, 2.0, 0.0, 3.0, 4.0) == INCONSISTENT_ZERO_CARRIER

    with pytest.raises(SemanticPhaseInverseError, match=NON_IDENTIFIABLE_PHASE):
        lifted_phase_from_semantic_value(0.0, 0.0, 2.0, 3.0, 4.0)
    with pytest.raises(SemanticPhaseInverseError, match=INCONSISTENT_ZERO_CARRIER):
        lifted_phase_from_semantic_value(1.0, 0.0, 2.0, 3.0, 4.0)


def test_phase_code_reconstructs_semantic_value_exactly():
    target = -3.25
    B, omega, N, A_R = 1.5, -2.0, 3.0, 4.0
    lifted = lifted_phase_from_semantic_value(target, B, omega, N, A_R)
    split = canonical_phase_split(lifted)
    reconstructed = semantic_value_from_phase_code(
        split.wrapped_phase,
        split.winding,
        B,
        omega,
        N,
        A_R,
    )
    assert reconstructed == pytest.approx(target)


def test_semantic_target_selects_orbit_and_phase_code():
    placement = encode_semantic_phase_placement(
        content_id="SEM.VALUE.A",
        kaku_id="K.GREMLIN.VALUE_A",
        sample_time=7.5,
        semantic_target=1.75,
        B=2.0,
        omega=3.0,
        N=4.0,
        A_R=5.0,
        quantizer=_quantizer(),
    )
    assert placement.orbital_band == _quantizer().quantize(1.75)
    assert semantic_value_from_phase_code(
        placement.phase_code.wrapped_phase,
        placement.phase_code.winding,
        placement.B,
        placement.omega,
        placement.N,
        placement.A_R,
    ) == pytest.approx(1.75)

    receipt = placement.deterministic_receipt()
    assert receipt["phase_profile_id"] == "SEMANTIC_VALUE_UNIQUE_LIFTED_PHASE_V0_2"
    assert receipt["orbit_assignment"]["orbital_band"] == placement.orbital_band
    assert receipt["roundtrip_semantic_value"] == pytest.approx(1.75)
    assert receipt["semantic_authority"] == "EXPLICIT_KAKU_CONTENT_BINDING"
    assert receipt["epistemic_state"] == "CHYBA"
    assert receipt["promotion_state"] == "CANDIDATE_ONLY"
    assert receipt["runtime_execution_authority"] is False
    assert receipt["canon_write_authority"] is False


def test_parent_forward_receipt_matches_target():
    placement = encode_semantic_phase_placement(
        content_id="SEM.VALUE.B",
        kaku_id="K.GREMLIN.VALUE_B",
        sample_time=2.0,
        semantic_target=-0.75,
        B=1.0,
        omega=-2.0,
        N=3.0,
        A_R=4.0,
        quantizer=_quantizer(),
    )
    parent = placement.parent_binding_receipt()
    assert parent["sample"]["semantic_value"] == pytest.approx(-0.75)
    assert parent["orbit_assignment"]["orbital_band"] == placement.orbital_band


def test_receipt_is_deterministic():
    kwargs = dict(
        content_id="SEM.DET",
        kaku_id="K.DET",
        sample_time=1.0,
        semantic_target=0.6,
        B=2.0,
        omega=1.5,
        N=3.0,
        A_R=2.5,
        quantizer=_quantizer(),
    )
    a = encode_semantic_phase_placement(**kwargs).deterministic_receipt()
    b = encode_semantic_phase_placement(**kwargs).deterministic_receipt()
    assert a == b
    assert len(a["receipt_sha256"]) == 64


@pytest.mark.parametrize(
    "content_id,kaku_id",
    [
        ("", "K.VALID"),
        ("   ", "K.VALID"),
        ("SEM.VALID", ""),
        ("SEM.VALID", "   "),
    ],
)
def test_empty_semantic_identity_fails_closed(content_id, kaku_id):
    with pytest.raises(SemanticPhaseInverseError, match="must be non-empty"):
        encode_semantic_phase_placement(
            content_id=content_id,
            kaku_id=kaku_id,
            sample_time=1.0,
            semantic_target=0.6,
            B=2.0,
            omega=1.5,
            N=3.0,
            A_R=2.5,
            quantizer=_quantizer(),
        )


def test_invalid_phase_code_inputs_fail_closed():
    with pytest.raises(SemanticPhaseInverseError):
        CanonicalPhaseSplit(0.0, -0.1, 0)
    with pytest.raises(SemanticPhaseInverseError):
        CanonicalPhaseSplit(0.0, 0.0, True)
    with pytest.raises(SemanticPhaseInverseError):
        lifted_phase_from_split(TAU, 0)
    with pytest.raises(SemanticPhaseInverseError):
        lifted_phase_from_split(0.2, 1.5)  # type: ignore[arg-type]
    with pytest.raises(SemanticPhaseInverseError):
        lifted_phase_from_semantic_value(math.nan, 1.0, 1.0, 1.0, 1.0)
    with pytest.raises(SemanticPhaseInverseError):
        inverse_status(1.0, 1.0, 1.0, 1.0, 0.0)
