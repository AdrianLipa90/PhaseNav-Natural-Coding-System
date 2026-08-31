import numpy as np
import pytest

from phasenav_natural_code.model import Kaku, RadicalGraph, Relation, Vector36
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
from phasenav_natural_code.semantic_radical_oscillator_v01 import (
    RadicalAggregationProfile,
    SemanticRadicalOscillatorError,
    aggregate_radical_semantic_value,
    radical_semantic_receipt,
    relation_oscillator_deltas,
    validate_radical_bindings,
)


def _snapshot() -> DriveSnapshot:
    phi = np.linspace(0.07, 5.91, 36, dtype=np.float64)
    omega = 39.6 + np.linspace(-0.12, 0.12, 36, dtype=np.float64)
    i = np.arange(36, dtype=np.float64)
    g = 0.18 * np.cos((i[:, None] - i[None, :]) * np.pi / 18.0)
    g = 0.5 * (g + g.T)
    np.fill_diagonal(g, 0.0)
    return DriveSnapshot.build(
        phi=phi,
        omega=omega,
        g=g,
        flavor=np.array([0.31, 0.72, 0.23, 0.56, 0.48, 0.5]),
        tau=np.linspace(0.21, 0.49, 36),
        gravity=np.array([0.0, 1.17, 0.3, 0.0, 0.0, 1.0, 0.0, 0.0]),
        source_id="STRICT_SEMANTIC_ACTUATION",
    )


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        "Q.STRICT.SEM",
        (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
        DEFAULT_BANDS,
    )


def _binding(
    kaku_id: str,
    content_id: str,
    *,
    B: float = 1.0,
    omega: float = 1.0,
    N: float = 1.0,
    A_R: float = 1.0,
    phi: float = 0.5,
):
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


def _radical() -> RadicalGraph:
    vector = Vector36(tuple(0.0 for _ in range(36)), "BASIS.STRICT.SEM")
    graph = RadicalGraph("R.STRICT.SEM", "BASIS.STRICT.SEM")
    graph.add_kaku(Kaku("K.A", vector, 1.0, "OUT", 1.0, "SOURCE"))
    graph.add_kaku(Kaku("K.B", vector, 2.0, "IN", -1.0, "TARGET"))
    graph.add_relation(Relation("REL.AB", "K.A", "K.B", "RELATES_TO"))
    return graph


def _bindings():
    return {
        "K.A": _binding("K.A", "SEM.A", phi=0.25, omega=2.0),
        "K.B": _binding("K.B", "SEM.B", phi=1.0, omega=5.0),
    }


def test_firewall_dt_rejects_bool_numeric_string_and_object():
    left = _binding("K.A", "SEM.A", B=0.1, omega=4.0)
    right = _binding("K.A", "SEM.A", B=10.0, omega=4.0)
    for bad in (True, "0.01", object()):
        with pytest.raises(SemanticMagnitudeActuationFirewallError, match="dt"):
            audit_magnitude_only_htri_invariance(
                _snapshot(), left, right, lane=3, dt=bad  # type: ignore[arg-type]
            )


def test_firewall_q_bna_fails_closed_on_finite_input_overflow():
    binding = _binding(
        "K.A",
        "SEM.A",
        B=1.0e308,
        omega=0.0,
        N=1.0e308,
        A_R=1.0,
        phi=0.0,
    )
    assert binding.sample.value == 0.0
    with pytest.raises(SemanticMagnitudeActuationFirewallError, match="Q_BNA"):
        source_factor_q_bna(binding)


def test_radical_profile_rejects_implicit_identity_and_numeric_coercion():
    with pytest.raises(SemanticRadicalOscillatorError, match="aggregation_profile_id"):
        RadicalAggregationProfile(1, {"K.A": 1.0})  # type: ignore[arg-type]
    with pytest.raises(SemanticRadicalOscillatorError, match="normalization"):
        RadicalAggregationProfile("AGG.BAD", {"K.A": 1.0}, object())  # type: ignore[arg-type]
    for bad in (True, "1.0", object()):
        with pytest.raises(SemanticRadicalOscillatorError, match="finite real"):
            RadicalAggregationProfile("AGG.BAD", {"K.A": bad})  # type: ignore[dict-item]


class _LooksLikeKaku:
    def __str__(self) -> str:
        return "K.A"


def test_radical_weight_and_binding_keys_require_exact_strings():
    with pytest.raises(SemanticRadicalOscillatorError, match="exact non-empty string"):
        RadicalAggregationProfile("AGG.BAD", {_LooksLikeKaku(): 1.0})  # type: ignore[dict-item]
    bindings = _bindings()
    bad = {_LooksLikeKaku(): bindings["K.A"], "K.B": bindings["K.B"]}
    with pytest.raises(SemanticRadicalOscillatorError, match="binding keys"):
        validate_radical_bindings(_radical(), bad)  # type: ignore[arg-type]


def test_relation_delta_overflow_fails_before_receipt_hash():
    bindings = {
        "K.A": _binding("K.A", "SEM.A", B=0.0, phi=-1.0e308),
        "K.B": _binding("K.B", "SEM.B", B=0.0, phi=1.0e308),
    }
    with pytest.raises(SemanticRadicalOscillatorError, match="delta_phi"):
        relation_oscillator_deltas(_radical(), bindings)


def test_aggregate_product_overflow_fails_before_receipt_hash():
    bindings = {
        "K.A": _binding("K.A", "SEM.A", B=1.0e308, omega=1.0, phi=0.5),
        "K.B": _binding("K.B", "SEM.B", B=0.0, omega=1.0, phi=0.0),
    }
    profile = RadicalAggregationProfile(
        "AGG.OVERFLOW",
        {"K.A": 2.0, "K.B": 0.0},
        "NONE",
    )
    with pytest.raises(SemanticRadicalOscillatorError, match="products must be finite"):
        aggregate_radical_semantic_value(_radical(), bindings, profile)


def test_radical_receipt_requires_typed_aggregation_profile():
    with pytest.raises(SemanticRadicalOscillatorError, match="aggregation_profile"):
        radical_semantic_receipt(
            _radical(),
            _bindings(),
            aggregation_profile=object(),  # type: ignore[arg-type]
        )
