from __future__ import annotations

import pytest

from phasenav_natural_code.composition_v23 import (
    NaturalProgramComposition,
    NaturalProgramV23Error,
    resolve_natural_program,
)
from phasenav_natural_code.full_program_executor_v01 import (
    FullProgramExecutionPlan,
    compile_full_program_plan,
)
from phasenav_natural_code.program_unit_v24 import NativeProgramUnit


PROGRAM = (
    "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) "
    "THEN GO safety pause ELSE GO runtime continue "
    "AND THEN GO cooling emergency "
    "AND THEN GO runtime memory relief "
    "RETURN control location"
)


def test_real_v023_to_v024_to_executor_plan_replay() -> None:
    resolution = resolve_natural_program(PROGRAM)
    composition = resolution.composition
    assert type(composition) is NaturalProgramComposition
    assert type(composition).__module__ == "phasenav_natural_code.composition_v23"

    unit = NativeProgramUnit.from_composition(composition)
    assert type(unit) is NativeProgramUnit
    assert type(unit).__module__ == "phasenav_natural_code.program_unit_v24"

    plan = compile_full_program_plan(unit, composition)
    assert type(plan) is FullProgramExecutionPlan
    assert plan.program_id == unit.program_id
    assert plan.composition_id == composition.composition_id == unit.composition_id
    assert plan.operator_schedule == unit.operator_schedule == composition.operator_schedule

    assert tuple(instruction.kind for instruction in plan.instructions) == (
        "CONTROL_DISPATCH",
        "CONTINUATION_ROUTE",
        "CONTINUATION_ROUTE",
        "RETURN",
    )
    assert tuple(instruction.pc for instruction in plan.instructions) == (0, 1, 2, 3)

    cursor = 0
    for instruction in plan.instructions:
        assert instruction.operator_start == cursor
        assert instruction.operator_stop > instruction.operator_start
        cursor = instruction.operator_stop
    assert cursor == len(plan.operator_schedule)

    for instruction in plan.instructions[1:-1]:
        assert plan.operator_schedule[instruction.operator_start:instruction.operator_stop] == (
            "ORDER",
            "TRANSFORM",
            "COMPOSITION",
        )
    terminal = plan.instructions[-1]
    assert plan.operator_schedule[terminal.operator_start:terminal.operator_stop] == ("RETURN",)
    assert terminal.target == "result.control_location"
    assert terminal.source_kind == "V0_20_RESULT"

    assert composition.payload["v0_20_executable"] is False
    assert composition.payload["external_effects"] is False
    assert composition.payload["free_form_nl_execution"] is False
    assert composition.payload["deterministic_fields_only"] is True
    assert unit.semantic_payload["native_execution_opened"] is False
    assert unit.semantic_payload["return_execution_opened"] is False
    assert unit.semantic_payload["external_effects"] is False
    assert unit.semantic_payload["static_runtime_fallback"] is False
    assert plan.payload["external_effects"] is False
    assert plan.payload["static_runtime_fallback"] is False
    assert plan.payload["deterministic_fields_only"] is True


def test_real_resolver_rejects_unregistered_continuation_before_executor() -> None:
    bad = (
        "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) "
        "THEN GO safety pause ELSE GO runtime continue "
        "AND THEN GO unregistered route "
        "RETURN control location"
    )
    with pytest.raises(NaturalProgramV23Error):
        resolve_natural_program(bad)


def test_real_resolver_rejects_unregistered_return_before_executor() -> None:
    bad = (
        "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) "
        "THEN GO safety pause ELSE GO runtime continue "
        "RETURN unregistered result"
    )
    with pytest.raises(NaturalProgramV23Error):
        resolve_natural_program(bad)
