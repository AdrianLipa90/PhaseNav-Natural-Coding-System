
from phasenav_natural_code.procedural_memory_runtime_v03 import (
    ProceduralMemoryRuntime,
    ProceduralMemoryRuntimeError,
    RouteState,
)


def test_history_changes_memory_and_future_routing():
    rt = ProceduralMemoryRuntime(
        "skill",
        [
            RouteState("route_a", ("input.x", "compute.a")),
            RouteState("route_b", ("input.x", "compute.b")),
        ],
        learning_rate=0.1,
    )
    initial = rt.digest
    assert rt.guide() == "route_a"  # deterministic tie break

    for i in range(6):
        rt.apply_trace("route_b", outcome="POSITIVE", event_id=f"b{i}")
    assert rt.digest != initial
    assert rt.route("route_b").weight == 0.6
    assert rt.guide() == "route_b"


def test_persistence_without_new_trace():
    rt = ProceduralMemoryRuntime(
        "skill",
        [RouteState("a", ("n0", "n1")), RouteState("b", ("n0", "n2"))],
    )
    rt.apply_trace("b", outcome="POSITIVE")
    digest = rt.digest
    for _ in range(100):
        assert rt.guide() == "b"
    assert rt.digest == digest


def test_intervention_changes_future_choice_without_changing_factual_state():
    rt = ProceduralMemoryRuntime(
        "skill",
        [RouteState("a", ("n0", "n1")), RouteState("b", ("n0", "n2"))],
    )
    for _ in range(4):
        rt.apply_trace("a", outcome="POSITIVE")
    factual_digest = rt.digest
    assert rt.guide() == "a"

    cf = rt.counterfactual({"a": -1.0, "b": 1.0})
    assert cf.guide() == "b"
    assert rt.guide() == "a"
    assert rt.digest == factual_digest


def test_negative_trace_can_reverse_route_preference():
    rt = ProceduralMemoryRuntime(
        "skill",
        [RouteState("a", ("n0", "n1")), RouteState("b", ("n0", "n2"))],
        learning_rate=0.25,
    )
    rt.apply_trace("a", outcome="POSITIVE")
    assert rt.guide() == "a"
    rt.apply_trace("a", outcome="NEGATIVE", magnitude=2)
    assert rt.route("a").weight == -0.25
    assert rt.guide() == "b"


def test_receipts_chain_state_digests():
    rt = ProceduralMemoryRuntime(
        "skill",
        [RouteState("a", ("n0", "n1")), RouteState("b", ("n0", "n2"))],
    )
    r1 = rt.apply_trace("a", outcome="POSITIVE")
    r2 = rt.apply_trace("b", outcome="POSITIVE")
    assert r1.after_digest == r2.before_digest
    assert r2.after_digest == rt.digest
    assert r2.to_dict()["durable_write_performed"] is False


def test_from_hybrid_ir_uses_only_routes_admitted_for_memory():
    ir = {
        "memory_model": {
            "objects": [
                {"memory_id": "skill", "retained_objects": ["path", "topology"]}
            ],
            "operations": [
                {
                    "kind": "PATH",
                    "attributes": {
                        "route_id": "a",
                        "node_path": ["n0", "n1"],
                    },
                },
                {
                    "kind": "PATH",
                    "attributes": {
                        "route_id": "b",
                        "node_path": ["n0", "n2"],
                    },
                },
                {
                    "kind": "REINFORCE",
                    "attributes": {"route_id": "b", "memory_id": "skill"},
                },
            ],
        }
    }
    rt = ProceduralMemoryRuntime.from_hybrid_ir(ir, "skill")
    assert rt.guide() == "b"
    try:
        rt.route("a")
        assert False
    except ProceduralMemoryRuntimeError:
        pass
