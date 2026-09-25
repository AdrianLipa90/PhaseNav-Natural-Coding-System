import pytest

from phasenav_natural_code.representation_arbiter_v03 import (
    BackendMeasurement,
    EquivalenceContract,
    RepresentationArbiter,
    RepresentationArbiterError,
)


def m(backend_id, family, error, *, storage=1, compile_time=1, update_time=1, query_time=1, sample_count=1, sequential_depth=1, evidence="FORMAL_ONLY", physical=False):
    return BackendMeasurement(
        backend_id, family, error, storage, compile_time, update_time,
        query_time, sample_count, sequential_depth, evidence, physical,
    )


def test_cheapest_equivalent_backend_wins_regardless_of_representation_label():
    contract = EquivalenceContract(0.01, 100, "trajectory_choice")
    arb = RepresentationArbiter(contract, (
        m("qnative", "QUANTUM_NATIVE", 0.001, query_time=10),
        m("binary", "BINARY", 0.001, query_time=2),
    ))
    d = arb.select({"query_time": 1})
    assert d.selected_backend_id == "binary"


def test_quantum_native_can_win_if_measured_cost_is_lower():
    contract = EquivalenceContract(0.01, 100, "trajectory_choice")
    arb = RepresentationArbiter(contract, (
        m("qnative", "QUANTUM_NATIVE", 0.001, query_time=1),
        m("binary", "BINARY", 0.001, query_time=9),
    ))
    assert arb.select({"query_time": 1}).selected_backend_id == "qnative"


def test_too_inaccurate_backend_is_excluded_even_if_free():
    contract = EquivalenceContract(0.01, 10, "observable")
    arb = RepresentationArbiter(contract, (
        m("bad_free", "BINARY", 0.5, query_time=0),
        m("good", "HYBRID", 0.001, query_time=5),
    ))
    d = arb.select({"query_time": 1})
    assert d.selected_backend_id == "good"
    assert "bad_free" not in d.admitted_backend_ids


def test_pareto_frontier_excludes_strictly_dominated_backend():
    contract = EquivalenceContract(0.01, 10, "observable")
    arb = RepresentationArbiter(contract, (
        m("a", "BINARY", 0.0, storage=1, query_time=5),
        m("b", "HYBRID", 0.0, storage=5, query_time=1),
        m("c", "QUANTUM_NATIVE", 0.0, storage=6, query_time=6),
    ))
    assert tuple(x.backend_id for x in arb.pareto_frontier()) == ("a", "b")


def test_no_equivalent_backend_fails_closed():
    arb = RepresentationArbiter(
        EquivalenceContract(0.001, 10, "observable"),
        (m("bad", "BINARY", 0.5),),
    )
    with pytest.raises(RepresentationArbiterError):
        arb.select({"query_time": 1})


def test_cost_ratio_requires_both_backends_to_pass_equivalence():
    arb = RepresentationArbiter(
        EquivalenceContract(0.01, 10, "observable"),
        (m("pn", "HYBRID", 0.0, query_time=1), m("qpu", "QUANTUM_NATIVE", 0.0, query_time=100)),
    )
    assert arb.cost_ratio("pn", "qpu", {"query_time": 1}) == pytest.approx(0.01)


def test_physical_substrate_is_not_inferred_from_quantum_native_family():
    x = m("qnative", "QUANTUM_NATIVE", 0.0)
    assert x.physical_substrate_claim is False
    assert x.to_dict()["representation_family"] == "quantum_native"


def test_physical_quantum_necessity_label_requires_explicit_physical_claim():
    with pytest.raises(RepresentationArbiterError):
        m("x", "QUANTUM_NATIVE", 0.0, evidence="PHYSICAL_QUANTUM_NECESSITY", physical=False)
