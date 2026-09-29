import pytest

from phasenav_natural_code.representation_planner_v03 import (
    EquivalenceContract,
    RepresentationCandidate,
    RepresentationPlannerError,
    ResourceVector,
    economic_cost_ratio,
    pareto_frontier,
    select_representation,
)


def c(eps=1e-3, horizon=100, obs="trajectory_choice"):
    return EquivalenceContract(eps, horizon, obs, "bounded_output_distance")


def r(storage, compile_time, update_time, query_time, sample_count, sequential_depth):
    return ResourceVector(storage, compile_time, update_time, query_time, sample_count, sequential_depth)


def test_cheapest_semantically_invalid_backend_is_rejected_before_cost():
    requested = c()
    candidates = [
        RepresentationCandidate("wrong", "BINARY", c(obs="different_output"), r(0,0,0,0,0,0), "PARITY"),
        RepresentationCandidate("valid", "HYBRID", c(), r(10,1,1,1,1,1), "FORMAL_ONLY"),
    ]
    decision = select_representation(candidates, requested, weights={"query_time": 1})
    assert decision.selected.candidate_id == "valid"
    assert "wrong" not in decision.eligible_ids


def test_stricter_epsilon_and_longer_horizon_are_admissible():
    requested = c(eps=1e-3, horizon=100)
    strong = RepresentationCandidate("strong", "BINARY", c(eps=1e-4, horizon=200), r(1,1,1,1,1,1), "PARITY")
    weak = RepresentationCandidate("weak", "BINARY", c(eps=1e-2, horizon=200), r(0,0,0,0,0,0), "PARITY")
    decision = select_representation([weak,strong], requested, weights={"storage":1})
    assert decision.selected.candidate_id == "strong"
    assert decision.eligible_ids == ("strong",)


def test_pareto_frontier_removes_componentwise_dominated_candidate():
    a = RepresentationCandidate("a", "BINARY", c(), r(1,1,1,1,1,1), "PARITY")
    b = RepresentationCandidate("b", "HYBRID", c(), r(2,2,2,2,2,2), "FORMAL_ONLY")
    cnd = RepresentationCandidate("c", "QUANTUM_NATIVE", c(), r(0.5,4,0.5,4,0.5,4), "FORMAL_ONLY")
    ids = tuple(x.candidate_id for x in pareto_frontier([a,b,cnd]))
    assert ids == ("a","c")


def test_declared_weights_choose_between_non_dominated_candidates():
    a = RepresentationCandidate("storage_light", "BINARY", c(), r(1,10,10,10,10,10), "PARITY")
    b = RepresentationCandidate("query_light", "HYBRID", c(), r(10,10,10,1,10,10), "PARITY")
    x = select_representation([a,b], c(), weights={"storage":1})
    y = select_representation([a,b], c(), weights={"query_time":1})
    assert x.selected.candidate_id == "storage_light"
    assert y.selected.candidate_id == "query_light"


def test_quantum_native_label_does_not_assert_physical_qpu_or_advantage():
    q = RepresentationCandidate("q", "QUANTUM_NATIVE", c(), r(1,1,1,1,1,1), "FORMAL_ONLY")
    d = select_representation([q], c(), weights={"query_time":1})
    payload = d.to_dict()
    assert payload["selected"]["physical_quantum_claim"] is False
    assert payload["quantum_advantage_claim"] is False


def test_physical_quantum_claim_fails_closed():
    with pytest.raises(RepresentationPlannerError):
        RepresentationCandidate("q", "QUANTUM_NATIVE", c(), r(1,1,1,1,1,1), "FORMAL_ONLY", physical_quantum_claim=True)


def test_economic_ratio_is_separate_from_quantum_advantage():
    cheap = RepresentationCandidate("cheap", "HYBRID", c(), r(0,0,0,1,0,0), "PARITY")
    expensive = RepresentationCandidate("expensive", "QUANTUM_NATIVE", c(), r(0,0,0,1e7,0,0), "FORMAL_ONLY")
    assert economic_cost_ratio(cheap, expensive, weights={"query_time":1}) == pytest.approx(1e-7)


def test_zero_denominator_cost_fails_closed():
    a = RepresentationCandidate("a", "BINARY", c(), r(1,1,1,1,1,1), "PARITY")
    z = RepresentationCandidate("z", "HYBRID", c(), r(0,0,0,0,0,0), "PARITY")
    with pytest.raises(RepresentationPlannerError):
        economic_cost_ratio(a, z, weights={"query_time":1})


def test_no_equivalent_backend_fails_closed():
    wrong = RepresentationCandidate("wrong", "BINARY", c(obs="x"), r(0,0,0,0,0,0), "PARITY")
    with pytest.raises(RepresentationPlannerError):
        select_representation([wrong], c(obs="y"), weights={"storage":1})
