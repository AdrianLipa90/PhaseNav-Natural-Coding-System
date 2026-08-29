import math

import pytest

from phasenav_natural_code.model import Kaku, RadicalGraph, Relation, Vector36
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


def _vector() -> Vector36:
    return Vector36(tuple(0.0 for _ in range(36)), "BASIS.SEM.TEST")


def _radical() -> RadicalGraph:
    graph = RadicalGraph("R.SEM.TEST", "BASIS.SEM.TEST")
    graph.add_kaku(Kaku("K.A", _vector(), 1.0, "OUT", 1.0, "SOURCE"))
    graph.add_kaku(Kaku("K.B", _vector(), 2.0, "IN", -1.0, "TARGET"))
    graph.add_relation(Relation("REL.AB", "K.A", "K.B", "RELATES_TO"))
    return graph


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        "Q.SEM.RADICAL.TEST",
        (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
        DEFAULT_BANDS,
    )


def _binding(kaku_id: str, content_id: str, *, phi: float, omega: float):
    sample = SemanticCarrierSample(
        content_id=content_id,
        kaku_id=kaku_id,
        sample_time=0.0,
        B=2.0,
        omega=omega,
        N=3.0,
        A_R=4.0,
        phi=phi,
    )
    return bind_semantic_sample(sample, _quantizer())


def _bindings():
    return {
        "K.A": _binding("K.A", "SEM.A", phi=0.25, omega=2.0),
        "K.B": _binding("K.B", "SEM.B", phi=1.00, omega=5.0),
    }


def test_exact_binding_coverage_is_required():
    graph = _radical()
    bindings = _bindings()
    validate_radical_bindings(graph, bindings)
    with pytest.raises(SemanticRadicalOscillatorError):
        validate_radical_bindings(graph, {"K.A": bindings["K.A"]})
    with pytest.raises(SemanticRadicalOscillatorError):
        validate_radical_bindings(graph, {**bindings, "K.EXTRA": bindings["K.A"]})


def test_binding_key_must_match_carrier_kaku_id():
    graph = _radical()
    bindings = _bindings()
    bad = {"K.A": bindings["K.B"], "K.B": bindings["K.A"]}
    with pytest.raises(SemanticRadicalOscillatorError):
        validate_radical_bindings(graph, bad)


def test_relation_deltas_are_directed_and_common_kappa_cancels():
    graph = _radical()
    bindings = _bindings()
    deltas = relation_oscillator_deltas(graph, bindings)
    assert len(deltas) == 1
    edge = deltas[0]
    assert edge["relation_id"] == "REL.AB"
    assert edge["source_id"] == "K.A"
    assert edge["target_id"] == "K.B"
    assert edge["delta_phi"] == pytest.approx(0.75)
    assert edge["delta_phase_plus_kappa"] == pytest.approx(0.75)
    assert edge["delta_omega"] == pytest.approx(3.0)
    assert edge["delta_semantic_value"] == pytest.approx(
        bindings["K.B"].sample.value - bindings["K.A"].sample.value
    )
    assert edge["source_orbital_band"] == bindings["K.A"].orbital_band
    assert edge["target_orbital_band"] == bindings["K.B"].orbital_band


def test_relation_orientation_reversal_reverses_all_signed_deltas():
    forward = _radical()
    bindings = _bindings()
    f = relation_oscillator_deltas(forward, bindings)[0]

    reverse = RadicalGraph("R.SEM.REVERSE", "BASIS.SEM.TEST")
    reverse.add_kaku(forward.nodes["K.A"])
    reverse.add_kaku(forward.nodes["K.B"])
    reverse.add_relation(Relation("REL.BA", "K.B", "K.A", "RELATES_TO"))
    r = relation_oscillator_deltas(reverse, bindings)[0]

    assert r["delta_phi"] == pytest.approx(-f["delta_phi"])
    assert r["delta_omega"] == pytest.approx(-f["delta_omega"])
    assert r["delta_semantic_value"] == pytest.approx(-f["delta_semantic_value"])


def test_explicit_none_normalized_linear_aggregate():
    graph = _radical()
    bindings = _bindings()
    profile = RadicalAggregationProfile(
        "AGG.TEST.LINEAR",
        {"K.A": 2.0, "K.B": -0.5},
        "NONE",
    )
    expected = 2.0 * bindings["K.A"].sample.value - 0.5 * bindings["K.B"].sample.value
    assert aggregate_radical_semantic_value(graph, bindings, profile) == pytest.approx(expected)


def test_unit_sum_aggregation_is_explicit_and_checked():
    graph = _radical()
    bindings = _bindings()
    profile = RadicalAggregationProfile(
        "AGG.TEST.UNIT",
        {"K.A": 0.25, "K.B": 0.75},
        "UNIT_SUM",
    )
    expected = 0.25 * bindings["K.A"].sample.value + 0.75 * bindings["K.B"].sample.value
    assert aggregate_radical_semantic_value(graph, bindings, profile) == pytest.approx(expected)
    with pytest.raises(SemanticRadicalOscillatorError):
        aggregate_radical_semantic_value(
            graph,
            bindings,
            RadicalAggregationProfile(
                "AGG.BAD.UNIT",
                {"K.A": 0.25, "K.B": 0.50},
                "UNIT_SUM",
            ),
        )


def test_aggregation_requires_exact_weight_coverage_and_finite_weights():
    graph = _radical()
    bindings = _bindings()
    with pytest.raises(SemanticRadicalOscillatorError):
        aggregate_radical_semantic_value(
            graph,
            bindings,
            RadicalAggregationProfile("AGG.MISSING", {"K.A": 1.0}),
        )
    with pytest.raises(SemanticRadicalOscillatorError):
        RadicalAggregationProfile("AGG.NAN", {"K.A": math.nan, "K.B": 1.0})
    with pytest.raises(SemanticRadicalOscillatorError):
        aggregate_radical_semantic_value(graph, bindings, None)  # type: ignore[arg-type]


def test_receipt_without_aggregation_preserves_vector_of_node_values():
    receipt = radical_semantic_receipt(_radical(), _bindings())
    assert receipt["aggregate"] is None
    assert tuple(receipt["node_bindings"]) == ("K.A", "K.B")
    assert receipt["aggregation_authority"] == "EXPLICIT_PROFILE_ONLY"
    assert receipt["epistemic_state"] == "CHYBA"
    assert receipt["promotion_state"] == "CANDIDATE_ONLY"
    assert receipt["runtime_execution_authority"] is False
    assert receipt["canon_write_authority"] is False
    assert len(receipt["receipt_sha256"]) == 64


def test_receipt_is_deterministic_and_aggregation_profile_changes_hash():
    graph = _radical()
    bindings = _bindings()
    plain_a = radical_semantic_receipt(graph, bindings)
    plain_b = radical_semantic_receipt(graph, bindings)
    assert plain_a == plain_b

    profile_a = RadicalAggregationProfile(
        "AGG.A",
        {"K.A": 0.5, "K.B": 0.5},
        "UNIT_SUM",
    )
    profile_b = RadicalAggregationProfile(
        "AGG.B",
        {"K.A": 0.5, "K.B": 0.5},
        "UNIT_SUM",
    )
    agg_a = radical_semantic_receipt(graph, bindings, aggregation_profile=profile_a)
    agg_b = radical_semantic_receipt(graph, bindings, aggregation_profile=profile_b)
    assert agg_a["aggregate"]["semantic_value"] == pytest.approx(
        agg_b["aggregate"]["semantic_value"]
    )
    assert agg_a["receipt_sha256"] != agg_b["receipt_sha256"]
