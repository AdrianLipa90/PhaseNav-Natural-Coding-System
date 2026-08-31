from __future__ import annotations

import hashlib

import pytest

from phasenav_natural_code import full_program_executor_v01 as m


def _tid(kind: str, label: str) -> str:
    return f"pncs:{kind}:sha256:{hashlib.sha256(label.encode()).hexdigest()}"


def _plan() -> m.FullProgramExecutionPlan:
    instructions = (
        m.FullProgramInstruction(0, "CONTROL_DISPATCH", 0, 1, _tid("def", "control")),
        m.FullProgramInstruction(
            1,
            "CONTINUATION_ROUTE",
            1,
            4,
            _tid("route-ref", "route"),
            target="runtime.finish",
        ),
        m.FullProgramInstruction(
            2,
            "RETURN",
            4,
            5,
            _tid("return-ref", "return"),
            target="result.control_location",
            source_kind="V0_20_RESULT",
        ),
    )
    return m.FullProgramExecutionPlan(
        _tid("program", "program"),
        _tid("composition", "composition"),
        ("DIFFERENCE", "ORDER", "TRANSFORM", "COMPOSITION", "RETURN"),
        instructions,
    )


def _trace(plan: m.FullProgramExecutionPlan) -> tuple[m.FullProgramTraceStep, ...]:
    return (
        m.FullProgramTraceStep(0, "CONTROL_DISPATCH", 0, 1, None, "runtime.start", plan.instructions[0].reference_id),
        m.FullProgramTraceStep(1, "CONTINUATION_ROUTE", 1, 4, "runtime.start", "runtime.finish", plan.instructions[1].reference_id),
        m.FullProgramTraceStep(2, "RETURN", 4, 5, "runtime.finish", "runtime.finish", plan.instructions[2].reference_id),
    )


def _receipt(*, trace=None, return_selector="result.control_location", return_value="runtime.finish"):
    plan = _plan()
    return m.FullProgramExecutionReceipt(
        plan=plan,
        control_dispatch_id=_tid("resident-dispatch", "dispatch"),
        generation_id=_tid("runtime-generation", "generation"),
        result_id=_tid("result", "result"),
        lineage_id=_tid("lineage", "lineage"),
        branch_truth_state="TRUE",
        trace=_trace(plan) if trace is None else trace,
        return_ref_id=plan.instructions[-1].reference_id,
        return_selector=return_selector,
        return_source_kind="V0_20_RESULT",
        return_value=return_value,
        final_control_location="runtime.finish",
    )


def test_valid_receipt_is_exact_plan_witness():
    receipt = _receipt()
    assert receipt.payload["final_control_location"] == "runtime.finish"
    assert receipt.execution_id.startswith("pncs:full-program-execution:sha256:")


def test_trace_reference_cannot_diverge_from_plan():
    plan = _plan()
    trace = list(_trace(plan))
    trace[1] = m.FullProgramTraceStep(
        1,
        "CONTINUATION_ROUTE",
        1,
        4,
        "runtime.start",
        "runtime.finish",
        _tid("route-ref", "forged"),
    )
    with pytest.raises(m.FullProgramExecutorV01Error, match="exactly witness plan instruction"):
        m.FullProgramExecutionReceipt(
            plan,
            _tid("resident-dispatch", "dispatch"),
            _tid("runtime-generation", "generation"),
            _tid("result", "result"),
            _tid("lineage", "lineage"),
            "TRUE",
            tuple(trace),
            plan.instructions[-1].reference_id,
            "result.control_location",
            "V0_20_RESULT",
            "runtime.finish",
            "runtime.finish",
        )


def test_trace_control_locations_must_be_contiguous():
    plan = _plan()
    trace = list(_trace(plan))
    trace[1] = m.FullProgramTraceStep(
        1,
        "CONTINUATION_ROUTE",
        1,
        4,
        "runtime.other",
        "runtime.finish",
        plan.instructions[1].reference_id,
    )
    with pytest.raises(m.FullProgramExecutorV01Error, match="control locations are not contiguous"):
        m.FullProgramExecutionReceipt(
            plan,
            _tid("resident-dispatch", "dispatch"),
            _tid("runtime-generation", "generation"),
            _tid("result", "result"),
            _tid("lineage", "lineage"),
            "TRUE",
            tuple(trace),
            plan.instructions[-1].reference_id,
            "result.control_location",
            "V0_20_RESULT",
            "runtime.finish",
            "runtime.finish",
        )


def test_return_metadata_must_match_terminal_instruction():
    with pytest.raises(m.FullProgramExecutorV01Error, match="return metadata does not match"):
        _receipt(return_selector="result.branch_truth_state")


def test_return_value_must_be_canonical_json():
    with pytest.raises(m.FullProgramExecutorV01Error, match="unsupported canonical value type"):
        _receipt(return_value=object())


def test_bool_instruction_coordinates_fail_closed():
    with pytest.raises(m.FullProgramExecutorV01Error, match="pc must be non-negative"):
        m.FullProgramInstruction(True, "CONTROL_DISPATCH", 0, 1, _tid("def", "control"))
    with pytest.raises(m.FullProgramExecutorV01Error, match="invalid operator span"):
        m.FullProgramInstruction(0, "CONTROL_DISPATCH", False, 1, _tid("def", "control"))
