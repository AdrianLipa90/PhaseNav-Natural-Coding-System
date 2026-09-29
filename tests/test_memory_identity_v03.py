import pytest

from phasenav_natural_code.procedural_memory_runtime_v03 import ProceduralMemoryRuntime, RouteState
from phasenav_natural_code.memory_identity_v03 import (
    MemoryIdentityError,
    compare_procedural_memories,
    project_runtime_to_stella3,
)


def runtime(weights):
    routes=[]
    for i,(rid,w) in enumerate(weights.items()):
        routes.append(RouteState(rid, ("start", f"node{i}", "target"), weight=w, traversals=3, positive_traces=2, negative_traces=1))
    return ProceduralMemoryRuntime("m", routes)


def test_identical_runtime_has_zero_behavioral_distance():
    a=runtime({"a":0.1,"b":0.5,"c":0.9})
    b=a.counterfactual({"a":0.1,"b":0.5,"c":0.9})
    w=compare_procedural_memories(a,b)
    assert w.queries_tested == 7
    assert w.choice_mismatches == 0
    assert w.mismatch_rate == 0
    assert w.behaviorally_equivalent is True


def test_stella_projection_preserves_clear_route_ordering_on_all_subsets():
    a=runtime({"a":-0.8,"b":0.1,"c":0.55,"d":0.95})
    b=project_runtime_to_stella3(a)
    w=compare_procedural_memories(a,b,epsilon=0)
    assert w.queries_tested == 15
    assert w.choice_mismatches == 0
    assert w.max_weight_abs_error > 0
    assert w.behaviorally_equivalent is True


def test_near_tie_stella_projection_can_fail_exact_memory_identity_contract():
    a=runtime({"a":0.89,"b":0.90})
    b=project_runtime_to_stella3(a,scale=1.0)
    w=compare_procedural_memories(a,b,epsilon=0)
    assert w.choice_mismatches == 1
    assert w.mismatch_rate == pytest.approx(1/3)
    assert w.behaviorally_equivalent is False
    assert compare_procedural_memories(a,b,epsilon=0.34).behaviorally_equivalent is True


def test_topology_mismatch_fails_even_if_route_weights_match():
    a=runtime({"a":0.1,"b":0.9})
    b=runtime({"a":0.1,"b":0.9})
    b._routes["b"].node_path=("start","different","target")
    w=compare_procedural_memories(a,b,epsilon=1)
    assert w.topology_equal is False
    assert w.behaviorally_equivalent is False


def test_provenance_counter_mismatch_fails_identity_contract():
    a=runtime({"a":0.1,"b":0.9})
    b=runtime({"a":0.1,"b":0.9})
    b._routes["b"].traversals += 1
    w=compare_procedural_memories(a,b,epsilon=1)
    assert w.provenance_counters_equal is False
    assert w.behaviorally_equivalent is False


def test_exact_subset_witness_fails_closed_above_declared_limit():
    a=runtime({f"r{i}":i/20 for i in range(13)})
    with pytest.raises(MemoryIdentityError):
        compare_procedural_memories(a,a,max_exact_routes=12)
