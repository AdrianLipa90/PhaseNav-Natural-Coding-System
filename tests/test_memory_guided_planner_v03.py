import pytest

from procedural_memory_runtime_v03 import ProceduralMemoryRuntime, RouteState
from memory_guided_planner_v03 import (
    MemoryGuidedPlanner,
    MemoryGuidedPlannerError,
)


def _planner():
    runtime = ProceduralMemoryRuntime(
        "skill",
        [
            RouteState("route_a", ("input.x", "compute.a", "compute.rank")),
            RouteState("route_b", ("input.x", "compute.b", "compute.rank")),
        ],
        learning_rate=0.2,
    )
    return MemoryGuidedPlanner(
        runtimes={"skill": runtime},
        guide_bindings={"compute.rank": "skill"},
    )


def test_feedback_changes_future_plan_under_same_current_condition():
    planner = _planner()
    condition = "ctx:fixed"
    before = planner.plan("compute.rank", current_condition_digest=condition)
    assert before.selected_route_id == "route_a"

    receipt = planner.feedback(
        "compute.rank",
        "route_b",
        outcome="POSITIVE",
        current_condition_digest=condition,
        event_id="success",
    )
    after = planner.plan("compute.rank", current_condition_digest=condition)

    assert receipt.current_condition_digest == condition
    assert before.current_condition_digest == after.current_condition_digest
    assert after.selected_route_id == "route_b"
    assert receipt.memory_before_digest != receipt.memory_after_digest
    assert receipt.changed_future_choice is True


def test_counterfactual_memory_changes_choice_without_mutating_factual_planner():
    planner = _planner()
    for _ in range(3):
        planner.feedback(
            "compute.rank",
            "route_a",
            outcome="POSITIVE",
            current_condition_digest="ctx:same",
        )
    factual_digest = planner.digest
    assert planner.plan("compute.rank", current_condition_digest="ctx:same").selected_route_id == "route_a"

    counter = planner.counterfactual_memory(
        "skill", {"route_a": -10.0, "route_b": 10.0}
    )
    assert counter.plan("compute.rank", current_condition_digest="ctx:same").selected_route_id == "route_b"
    assert planner.plan("compute.rank", current_condition_digest="ctx:same").selected_route_id == "route_a"
    assert planner.digest != factual_digest  # planning receipts changed the planner snapshot, not memory
    assert planner.memory_runtime("skill").guide() == "route_a"


def test_unknown_target_fails_closed():
    planner = _planner()
    with pytest.raises(MemoryGuidedPlannerError):
        planner.plan("compute.unknown", current_condition_digest="ctx")


def test_multiple_guides_for_same_target_fail_closed():
    ir = {
        "memory_model": {
            "objects": [
                {"memory_id": "m1", "retained_objects": ["path"]},
                {"memory_id": "m2", "retained_objects": ["path"]},
            ],
            "operations": [
                {"kind": "PATH", "attributes": {"route_id": "a", "node_path": ["n0", "n1"]}},
                {"kind": "PATH", "attributes": {"route_id": "b", "node_path": ["n0", "n2"]}},
                {"kind": "REINFORCE", "attributes": {"route_id": "a", "memory_id": "m1"}},
                {"kind": "REINFORCE", "attributes": {"route_id": "b", "memory_id": "m2"}},
                {"kind": "GUIDE", "attributes": {"target_node_id": "n1", "memory_id": "m1"}},
                {"kind": "GUIDE", "attributes": {"target_node_id": "n1", "memory_id": "m2"}},
            ],
        }
    }
    with pytest.raises(MemoryGuidedPlannerError):
        MemoryGuidedPlanner.from_hybrid_ir(ir)


def test_from_hybrid_ir_builds_only_guided_memory_runtime():
    ir = {
        "memory_model": {
            "objects": [
                {"memory_id": "skill", "retained_objects": ["path", "topology"]},
                {"memory_id": "unused", "retained_objects": ["path"]},
            ],
            "operations": [
                {"kind": "PATH", "attributes": {"route_id": "a", "node_path": ["n0", "n1"]}},
                {"kind": "PATH", "attributes": {"route_id": "b", "node_path": ["n0", "n2"]}},
                {"kind": "REINFORCE", "attributes": {"route_id": "a", "memory_id": "skill"}},
                {"kind": "REINFORCE", "attributes": {"route_id": "b", "memory_id": "skill"}},
                {"kind": "GUIDE", "attributes": {"target_node_id": "n1", "memory_id": "skill"}},
            ],
        }
    }
    planner = MemoryGuidedPlanner.from_hybrid_ir(ir)
    assert planner.memory_runtime("skill").guide() == "a"
    with pytest.raises(MemoryGuidedPlannerError):
        planner.memory_runtime("unused")


def test_negative_feedback_can_demote_a_previously_preferred_route():
    planner = _planner()
    planner.feedback(
        "compute.rank", "route_a", outcome="POSITIVE",
        current_condition_digest="ctx", magnitude=2,
    )
    assert planner.plan("compute.rank", current_condition_digest="ctx").selected_route_id == "route_a"
    planner.feedback(
        "compute.rank", "route_a", outcome="NEGATIVE",
        current_condition_digest="ctx", magnitude=4,
    )
    assert planner.plan("compute.rank", current_condition_digest="ctx").selected_route_id == "route_b"


def test_feedback_receipts_chain_memory_digests():
    planner = _planner()
    r1 = planner.feedback(
        "compute.rank", "route_a", outcome="POSITIVE",
        current_condition_digest="ctx",
    )
    r2 = planner.feedback(
        "compute.rank", "route_b", outcome="POSITIVE",
        current_condition_digest="ctx",
    )
    assert r1.memory_after_digest == r2.memory_before_digest
