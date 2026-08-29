import math

import pytest

from phasenav_natural_code.pnlf_orbital_memory_v01 import OrbitalState
from phasenav_natural_code.semantic_orbital_carrier_v01 import (
    KAPPA,
    OrbitQuantizerProfile,
    SemanticCarrierSample,
    SemanticOrbitalCarrierError,
    bind_orbital_state_sample,
    bind_semantic_sample,
    carrier_prefactor,
    sample_from_orbital_state,
    semantic_value,
    shifted_phase,
)


def _quantizer(*, quantizer_id: str = "Q.SEM.TEST") -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        quantizer_id=quantizer_id,
        boundaries=(-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
    )


def _orbital_state(*, period: float = 4.0, phase: float = 0.75, winding: float = 2.0) -> OrbitalState:
    return OrbitalState(
        attractor_id="A.SEM.TEST",
        orbital_band="O2",
        r_phase=0.25,
        phase=phase,
        E_bind=-1.5,
        L_phase=0.5,
        semantic_mass=3.0,
        orbit_period=period,
        winding=winding,
        proper_time=7.0,
        memory_affinity=0.8,
        mass_model_id="M.SEM.TEST",
        orbit_quantizer_id="Q.PNLF.TEST",
        proper_time_model_id="TAU.TEST",
    )


def test_canonical_kappa():
    assert KAPPA == pytest.approx(math.log(2.0) / (24.0 * math.pi), rel=0.0, abs=1e-16)


def test_exact_user_formula_and_factorization():
    B = 2.5
    omega = -3.0
    N = 4.0
    A_R = 5.0
    phi = 0.7
    expected_prefactor = (B * omega * N) / A_R
    expected = expected_prefactor * (phi + KAPPA)
    assert carrier_prefactor(B, omega, N, A_R) == pytest.approx(expected_prefactor)
    assert shifted_phase(phi) == pytest.approx(phi + KAPPA)
    assert semantic_value(B, omega, N, A_R, phi) == pytest.approx(expected)


def test_sample_preserves_explicit_semantic_identity():
    sample = SemanticCarrierSample(
        content_id="SEM.CONCEPT.A",
        kaku_id="K.GREMLIN.CONCEPT_A",
        sample_time=1.25,
        B=2.0,
        omega=3.0,
        N=4.0,
        A_R=8.0,
        phi=0.5,
    )
    body = sample.to_dict()
    assert body["content_id"] == "SEM.CONCEPT.A"
    assert body["kaku_id"] == "K.GREMLIN.CONCEPT_A"
    assert body["semantic_value"] == pytest.approx((2.0 * 3.0 * 4.0 / 8.0) * (0.5 + KAPPA))


def test_signed_omega_is_preserved_as_formula_coordinate():
    positive = semantic_value(1.0, 2.0, 1.0, 1.0, 0.3)
    negative = semantic_value(1.0, -2.0, 1.0, 1.0, 0.3)
    assert negative == pytest.approx(-positive)


def test_zero_reference_denominator_and_nonfinite_values_fail_closed():
    with pytest.raises(SemanticOrbitalCarrierError):
        semantic_value(1.0, 1.0, 1.0, 0.0, 0.0)
    with pytest.raises(SemanticOrbitalCarrierError):
        SemanticCarrierSample("C", "K", 0.0, math.nan, 1.0, 1.0, 1.0, 0.0)
    with pytest.raises(SemanticOrbitalCarrierError):
        shifted_phase(math.inf)


def test_nine_band_quantizer_is_explicit_and_deterministic():
    q = _quantizer()
    assert q.quantize(-10.0) == "O0"
    assert q.quantize(-4.0) == "O1"
    assert q.quantize(-0.1) == "O4"
    assert q.quantize(0.0) == "O5"
    assert q.quantize(10.0) == "O8"


def test_quantizer_accepts_explicit_band_order():
    reversed_bands = tuple(reversed(tuple(f"O{i}" for i in range(9))))
    q = OrbitQuantizerProfile(
        quantizer_id="Q.REVERSED",
        boundaries=(-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
        bands=reversed_bands,
    )
    assert q.quantize(-10.0) == "O8"
    assert q.quantize(10.0) == "O0"


def test_invalid_quantizer_profiles_fail_closed():
    with pytest.raises(SemanticOrbitalCarrierError):
        OrbitQuantizerProfile("Q.BAD", (0.0, 1.0))
    with pytest.raises(SemanticOrbitalCarrierError):
        OrbitQuantizerProfile("Q.BAD", (0, 1, 2, 3, 4, 5, 6, 6))
    with pytest.raises(SemanticOrbitalCarrierError):
        OrbitQuantizerProfile(
            "Q.BAD",
            (0, 1, 2, 3, 4, 5, 6, 7),
            bands=("O0",) * 9,
        )


def test_binding_quantizes_the_semantic_value_and_is_candidate_only():
    sample = SemanticCarrierSample("SEM.A", "K.A", 0.0, 1.0, 1.0, 1.0, 1.0, 0.0)
    binding = bind_semantic_sample(sample, _quantizer())
    assert binding.orbital_band == _quantizer().quantize(sample.value)
    receipt = binding.deterministic_receipt()
    assert receipt["semantic_authority"] == "EXPLICIT_KAKU_CONTENT_BINDING"
    assert receipt["epistemic_state"] == "CHYBA"
    assert receipt["promotion_state"] == "CANDIDATE_ONLY"
    assert receipt["runtime_execution_authority"] is False
    assert receipt["canon_write_authority"] is False
    assert len(receipt["receipt_sha256"]) == 64


def test_receipt_is_deterministic_and_quantizer_provenance_changes_hash():
    sample = SemanticCarrierSample("SEM.A", "K.A", 0.0, 1.0, 2.0, 3.0, 4.0, 0.5)
    a = bind_semantic_sample(sample, _quantizer(quantizer_id="Q.A")).deterministic_receipt()
    b = bind_semantic_sample(sample, _quantizer(quantizer_id="Q.A")).deterministic_receipt()
    c = bind_semantic_sample(sample, _quantizer(quantizer_id="Q.B")).deterministic_receipt()
    assert a == b
    assert a["receipt_sha256"] != c["receipt_sha256"]


def test_pnlf_orbit_period_projects_to_angular_frequency_and_phase():
    state = _orbital_state(period=4.0, phase=0.75, winding=2.0)
    sample, source = sample_from_orbital_state(
        content_id="SEM.ORBIT",
        kaku_id="K.ORBIT",
        orbital_state=state,
        B=2.0,
        N=3.0,
        A_R=4.0,
    )
    assert sample.omega == pytest.approx(math.pi / 2.0)
    assert sample.phi == pytest.approx(0.75)
    assert sample.sample_time == pytest.approx(state.proper_time)
    assert source["phase"] == pytest.approx(0.75)
    assert source["winding"] == pytest.approx(2.0)
    assert source["omega_projection"] == "2*pi/orbit_period"


def test_pnlf_binding_keeps_source_orbit_and_new_semantic_orbit_distinct():
    state = _orbital_state()
    binding = bind_orbital_state_sample(
        content_id="SEM.ORBIT",
        kaku_id="K.ORBIT",
        orbital_state=state,
        B=1.5,
        N=2.0,
        A_R=3.0,
        quantizer=_quantizer(),
    )
    receipt = binding.deterministic_receipt()
    assert receipt["source_orbital_state"]["orbital_band"] == "O2"
    assert receipt["orbit_assignment"]["orbital_band"] == binding.orbital_band
    assert receipt["source_orbital_state"]["orbit_quantizer_id"] == "Q.PNLF.TEST"
    assert receipt["orbit_assignment"]["quantizer"]["quantizer_id"] == "Q.SEM.TEST"
