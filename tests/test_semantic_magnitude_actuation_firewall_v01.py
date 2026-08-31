from __future__ import annotations

import numpy as np
import pytest

from phasenav_natural_code.semantic_htri_drive_v32 import DriveSnapshot
from phasenav_natural_code.semantic_magnitude_actuation_firewall_v01 import (
    SemanticMagnitudeActuationFirewallError,
    audit_magnitude_only_htri_invariance,
    source_factor_q_bna,
)
from phasenav_natural_code.semantic_orbital_carrier_v01 import (
    DEFAULT_BANDS,
    OrbitQuantizerProfile,
    SemanticCarrierSample,
    bind_semantic_sample,
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
        source_id="TEST_MAGNITUDE_ACTUATION_FIREWALL",
    )


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        "Q.MAGNITUDE.FIREWALL",
        (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
        DEFAULT_BANDS,
    )


def _binding(*, B: float, N: float = 1.0, A_R: float = 1.0, phi: float = 0.5, omega: float = 4.0, kaku_id: str = "K.A", content_id: str = "SEM.A"):
    return bind_semantic_sample(
        SemanticCarrierSample(
            content_id=content_id,
            kaku_id=kaku_id,
            sample_time=0.0,
            B=B,
            omega=omega,
            N=N,
            A_R=A_R,
            phi=phi,
        ),
        _quantizer(),
    )


def test_q_bna_is_exact_algebraic_factor():
    binding = _binding(B=6.0, N=5.0, A_R=3.0)
    assert source_factor_q_bna(binding) == pytest.approx(10.0)
    assert binding.sample.value == pytest.approx(
        source_factor_q_bna(binding)
        * binding.sample.omega
        * binding.sample.phase_kappa
    )


def test_magnitude_only_variation_changes_semantic_value_and_can_change_orbit():
    left = _binding(B=0.1)
    right = _binding(B=10.0)
    assert left.sample.phi == right.sample.phi
    assert left.sample.omega == right.sample.omega
    assert left.sample.value != right.sample.value
    assert left.orbital_band != right.orbital_band


def test_magnitude_only_variation_does_not_change_current_numeric_htri_qhtri_actuation():
    audit = audit_magnitude_only_htri_invariance(
        _snapshot(),
        _binding(B=0.1),
        _binding(B=10.0),
        lane=11,
    )
    assert audit["all_numeric_actuation_equal"] is True
    assert all(audit["numeric_htri_qhtri_equality"].values())
    assert audit["semantic_values_equal"] is False
    assert audit["orbital_bands_equal"] is False
    assert audit["frontier"] == "SEMANTIC_MAGNITUDE_TO_HTRI_ACTUATION"
    assert audit["frontier_status"] == "OPEN_SOURCE_BINDING"


def test_B_N_and_A_R_variations_are_all_inside_the_same_current_non_actuation_firewall():
    base = _binding(B=2.0, N=3.0, A_R=4.0)
    variants = (
        _binding(B=5.0, N=3.0, A_R=4.0),
        _binding(B=2.0, N=7.0, A_R=4.0),
        _binding(B=2.0, N=3.0, A_R=9.0),
    )
    for variant in variants:
        audit = audit_magnitude_only_htri_invariance(
            _snapshot(), base, variant, lane=5
        )
        assert audit["all_numeric_actuation_equal"] is True


def test_magnitude_only_audit_rejects_phase_frequency_or_identity_changes():
    base = _binding(B=1.0)
    with pytest.raises(SemanticMagnitudeActuationFirewallError):
        audit_magnitude_only_htri_invariance(
            _snapshot(), base, _binding(B=2.0, phi=0.6), lane=2
        )
    with pytest.raises(SemanticMagnitudeActuationFirewallError):
        audit_magnitude_only_htri_invariance(
            _snapshot(), base, _binding(B=2.0, omega=5.0), lane=2
        )
    with pytest.raises(SemanticMagnitudeActuationFirewallError):
        audit_magnitude_only_htri_invariance(
            _snapshot(), base, _binding(B=2.0, kaku_id="K.B"), lane=2
        )
    with pytest.raises(SemanticMagnitudeActuationFirewallError):
        audit_magnitude_only_htri_invariance(
            _snapshot(), base, _binding(B=2.0, content_id="SEM.B"), lane=2
        )


def test_audit_receipt_is_deterministic_and_keeps_candidate_authority():
    a = audit_magnitude_only_htri_invariance(
        _snapshot(), _binding(B=0.1), _binding(B=10.0), lane=11
    )
    b = audit_magnitude_only_htri_invariance(
        _snapshot(), _binding(B=0.1), _binding(B=10.0), lane=11
    )
    assert a == b
    assert a["receipt_sha256"] == b["receipt_sha256"]
    assert a["epistemic_state"] == "CHYBA"
    assert a["promotion_state"] == "CANDIDATE_ONLY"
    assert a["runtime_execution_authority"] is False
    assert a["canon_write_authority"] is False
