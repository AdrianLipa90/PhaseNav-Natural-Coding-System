from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Callable, Mapping

FULL_EXECUTOR_CONTRACT_ID = "PNCS_FULL_PROGRAM_EXECUTOR_V0_1"
FULL_EXECUTOR_SCHEMA = "PNCS_FULL_PROGRAM_EXECUTION_RECEIPT_V0_1"
PLAN_SCHEMA = "PNCS_FULL_PROGRAM_EXECUTION_PLAN_V0_1"
TRACE_SCHEMA = "PNCS_FULL_PROGRAM_EXECUTION_TRACE_STEP_V0_1"
PROGRAM_SCHEMA = "PNCS_PROGRAM_UNIT_CONTENT_V0_24"
PROGRAM_CONTRACT_ID = "PNCS_NATIVE_PNV_PROGRAM_UNITS_V0_24"
COMPOSITION_SCHEMA = "PNCS_NATURAL_PROGRAM_COMPOSITION_V0_23"
RUNTIME_CONTRACT_ID = "PNCS_PERSISTENT_RUNTIME_V0_25"
DISPATCH_SCHEMA = "PNCS_RESIDENT_CONTROL_DISPATCH_RECEIPT_V0_25"
LINEAGE_CONTRACT_ID = "PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22"
EPISTEMIC_STATUS = "CHYBA"
MODE = "READ_ONLY"
PROMOTION_TRACK = "POST_V1_LANGUAGE_ENGINEERING"
MAX_PROGRAM_OPERATORS = 1000

HEX64 = r"[0-9a-f]{64}"
_PROGRAM_RE = re.compile(rf"^pncs:program:sha256:{HEX64}$")
_COMPOSITION_RE = re.compile(rf"^pncs:composition:sha256:{HEX64}$")
_DEFINITION_RE = re.compile(rf"^pncs:def:sha256:{HEX64}$")
_ROUTE_RE = re.compile(rf"^pncs:route-ref:sha256:{HEX64}$")
_RETURN_RE = re.compile(rf"^pncs:return-ref:sha256:{HEX64}$")
_DISPATCH_RE = re.compile(rf"^pncs:resident-dispatch:sha256:{HEX64}$")
_LINEAGE_RE = re.compile(rf"^pncs:lineage:sha256:{HEX64}$")
_RESULT_RE = re.compile(rf"^pncs:result:sha256:{HEX64}$")
_HANDLE_RE = re.compile(rf"^pncs:resident:sha256:{HEX64}$")
_GENERATION_RE = re.compile(rf"^pncs:runtime-generation:sha256:{HEX64}$")
_TYPED_VALUE_RE = re.compile(rf"^pncs:[a-z0-9-]+:sha256:{HEX64}$")


class FullProgramExecutorV01Error(RuntimeError):
    pass


def _jsonable(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_jsonable(v) for v in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise FullProgramExecutorV01Error("non-finite value is not canonical JSON")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise FullProgramExecutorV01Error(f"unsupported canonical value type: {type(value).__name__}")


def _compact_json(value: object) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_compact_json(value).encode()).hexdigest()


def _typed_id(prefix: str, payload: object) -> str:
    return f"{prefix}:sha256:{_sha256_json(payload)}"


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise FullProgramExecutorV01Error(f"{field} must be a mapping")
    return value


def _typed(value: object, pattern: re.Pattern[str], field: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise FullProgramExecutorV01Error(f"invalid {field}")
    return value


def _closed(payload: Mapping[str, object], *fields: str) -> None:
    for field in fields:
        if payload.get(field) is not False:
            raise FullProgramExecutorV01Error(f"{field} must remain false")


def _deterministic(payload: Mapping[str, object]) -> None:
    if payload.get("deterministic_fields_only") is not True:
        raise FullProgramExecutorV01Error("deterministic_fields_only must remain true")


def _schedule(unit: object) -> tuple[str, ...]:
    raw = getattr(unit, "operator_schedule", None)
    if not isinstance(raw, (tuple, list)):
        raise FullProgramExecutorV01Error("NativeProgramUnit-compatible operator_schedule required")
    schedule = tuple(str(x) for x in raw)
    if not schedule or len(schedule) > MAX_PROGRAM_OPERATORS:
        raise FullProgramExecutorV01Error("operator schedule size outside v0.1 bound")
    if any(not op or op != op.upper() for op in schedule):
        raise FullProgramExecutorV01Error("operator schedule must use canonical uppercase IDs")
    if schedule[-1] != "RETURN":
        raise FullProgramExecutorV01Error("program must terminate with RETURN")
    return schedule


def _program_payload(unit: object) -> Mapping[str, object]:
    payload = _mapping(getattr(unit, "semantic_payload", None), "program semantic_payload")
    if payload.get("schema") != PROGRAM_SCHEMA or payload.get("program_contract_id") != PROGRAM_CONTRACT_ID:
        raise FullProgramExecutorV01Error("program unit schema/contract mismatch")
    _closed(payload, "native_execution_opened", "return_execution_opened", "external_effects", "free_form_nl_execution", "static_runtime_fallback")
    _deterministic(payload)
    if payload.get("required_result_lineage_contract_id") != LINEAGE_CONTRACT_ID:
        raise FullProgramExecutorV01Error("program unit lineage contract mismatch")
    program_id = _typed(getattr(unit, "program_id", None), _PROGRAM_RE, "program_id")
    if program_id != _typed_id("pncs:program", payload):
        raise FullProgramExecutorV01Error("program content-address identity mismatch")
    composition_id = _typed(getattr(unit, "composition_id", None), _COMPOSITION_RE, "composition_id")
    if payload.get("composition_id") != composition_id:
        raise FullProgramExecutorV01Error("program/composition identity mismatch")
    schedule = _schedule(unit)
    if list(payload.get("operator_schedule", [])) != list(schedule):
        raise FullProgramExecutorV01Error("program operator schedule/payload mismatch")
    return_ref = _typed(getattr(unit, "return_ref_id", None), _RETURN_RE, "return_ref_id")
    if payload.get("return_ref_id") != return_ref:
        raise FullProgramExecutorV01Error("program return_ref_id/payload mismatch")
    return payload


def _composition_payload(composition: object) -> Mapping[str, object]:
    payload = _mapping(getattr(composition, "payload", None), "composition payload")
    if payload.get("schema") != COMPOSITION_SCHEMA or payload.get("composition_contract_id") != COMPOSITION_SCHEMA:
        raise FullProgramExecutorV01Error("composition schema/contract mismatch")
    _closed(payload, "external_effects", "free_form_nl_execution")
    _deterministic(payload)
    if payload.get("required_result_lineage_contract_id") != LINEAGE_CONTRACT_ID:
        raise FullProgramExecutorV01Error("composition lineage contract mismatch")
    composition_id = _typed(getattr(composition, "composition_id", None), _COMPOSITION_RE, "composition_id")
    if composition_id != _typed_id("pncs:composition", payload):
        raise FullProgramExecutorV01Error("composition content-address identity mismatch")
    return payload


@dataclass(frozen=True, slots=True)
class FullProgramInstruction:
    pc: int
    kind: str
    operator_start: int
    operator_stop: int
    reference_id: str
    target: str | None = None
    source_kind: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.pc, int) or self.pc < 0:
            raise FullProgramExecutorV01Error("instruction pc must be non-negative")
        if self.kind not in {"CONTROL_DISPATCH", "CONTINUATION_ROUTE", "RETURN"}:
            raise FullProgramExecutorV01Error("unsupported instruction kind")
        if not isinstance(self.operator_start, int) or not isinstance(self.operator_stop, int) or self.operator_start < 0 or self.operator_stop <= self.operator_start:
            raise FullProgramExecutorV01Error("invalid operator span")
        if not isinstance(self.reference_id, str) or not self.reference_id:
            raise FullProgramExecutorV01Error("instruction reference_id required")
        if self.kind == "CONTINUATION_ROUTE":
            _typed(self.reference_id, _ROUTE_RE, "continuation route ref")
            if not self.target:
                raise FullProgramExecutorV01Error("continuation route target required")
        if self.kind == "RETURN":
            _typed(self.reference_id, _RETURN_RE, "return ref")
            if not self.target or self.source_kind not in {"V0_20_RESULT", "V0_20_FINAL_STATE", "V0_22_LINEAGE"}:
                raise FullProgramExecutorV01Error("return selector target/source_kind required")

    @property
    def payload(self) -> dict[str, object]:
        return {"pc": self.pc, "kind": self.kind, "operator_start": self.operator_start, "operator_stop": self.operator_stop, "reference_id": self.reference_id, "target": self.target, "source_kind": self.source_kind}


@dataclass(frozen=True, slots=True)
class FullProgramExecutionPlan:
    program_id: str
    composition_id: str
    operator_schedule: tuple[str, ...]
    instructions: tuple[FullProgramInstruction, ...]

    def __post_init__(self) -> None:
        _typed(self.program_id, _PROGRAM_RE, "program_id")
        _typed(self.composition_id, _COMPOSITION_RE, "composition_id")
        if not self.instructions:
            raise FullProgramExecutorV01Error("execution plan must contain instructions")
        if tuple(i.pc for i in self.instructions) != tuple(range(len(self.instructions))):
            raise FullProgramExecutorV01Error("instruction pcs must be contiguous")
        if self.instructions[0].kind != "CONTROL_DISPATCH" or self.instructions[-1].kind != "RETURN":
            raise FullProgramExecutorV01Error("plan must begin with CONTROL_DISPATCH and terminate with RETURN")
        cursor = 0
        for instruction in self.instructions:
            if instruction.operator_start != cursor:
                raise FullProgramExecutorV01Error("operator spans must be contiguous")
            cursor = instruction.operator_stop
        if cursor != len(self.operator_schedule):
            raise FullProgramExecutorV01Error("instruction spans do not cover operator schedule exactly")

    @property
    def payload(self) -> dict[str, object]:
        return {"schema": PLAN_SCHEMA, "executor_contract_id": FULL_EXECUTOR_CONTRACT_ID, "program_id": self.program_id, "composition_id": self.composition_id, "operator_schedule": list(self.operator_schedule), "operator_schedule_sha256": _sha256_json(list(self.operator_schedule)), "instructions": [i.payload for i in self.instructions], "instruction_count": len(self.instructions), "external_effects": False, "static_runtime_fallback": False, "deterministic_fields_only": True}

    @property
    def plan_id(self) -> str:
        return _typed_id("pncs:full-program-plan", self.payload)


def compile_full_program_plan(unit: object, composition: object) -> FullProgramExecutionPlan:
    program = _program_payload(unit)
    comp = _composition_payload(composition)
    program_id = str(getattr(unit, "program_id"))
    composition_id = str(getattr(unit, "composition_id"))
    if getattr(composition, "composition_id", None) != composition_id:
        raise FullProgramExecutorV01Error("unit/composition ID mismatch")
    if program.get("composition_id") != composition_id:
        raise FullProgramExecutorV01Error("program payload composition mismatch")
    schedule = _schedule(unit)
    if tuple(getattr(composition, "operator_schedule", ())) != schedule or list(comp.get("operator_schedule", [])) != list(schedule):
        raise FullProgramExecutorV01Error("program/composition operator schedule mismatch")

    control = getattr(composition, "control_content", None)
    control_id = _typed(getattr(control, "content_id", None), _DEFINITION_RE, "control Definition ID")
    control_leaf = tuple(str(x) for x in getattr(control, "leaf_path", ()))
    if not control_leaf or schedule[:len(control_leaf)] != control_leaf:
        raise FullProgramExecutorV01Error("control leaf path is not exact prefix of program schedule")
    instructions = [FullProgramInstruction(0, "CONTROL_DISPATCH", 0, len(control_leaf), control_id)]
    cursor = len(control_leaf)

    for route in tuple(getattr(composition, "continuation_routes", ())):
        ref_id = _typed(getattr(route, "ref_id", None), _ROUTE_RE, "route ref")
        target = getattr(route, "canonical", None)
        if not isinstance(target, str) or not target:
            raise FullProgramExecutorV01Error("route canonical target required")
        if getattr(route, "route_kind", None) != "INTERNAL_TRANSFORM":
            raise FullProgramExecutorV01Error("continuation route must remain INTERNAL_TRANSFORM")
        if schedule[cursor:cursor + 3] != ("ORDER", "TRANSFORM", "COMPOSITION"):
            raise FullProgramExecutorV01Error("continuation operator span mismatch")
        instructions.append(FullProgramInstruction(len(instructions), "CONTINUATION_ROUTE", cursor, cursor + 3, ref_id, target=target))
        cursor += 3

    ret = getattr(composition, "return_spec", None)
    return_ref = _typed(getattr(ret, "ref_id", None), _RETURN_RE, "return ref")
    if cursor != len(schedule) - 1 or schedule[cursor] != "RETURN":
        raise FullProgramExecutorV01Error("terminal RETURN operator position mismatch")
    if return_ref != getattr(unit, "return_ref_id", None):
        raise FullProgramExecutorV01Error("unit/composition return reference mismatch")
    instructions.append(FullProgramInstruction(len(instructions), "RETURN", cursor, cursor + 1, return_ref, target=getattr(ret, "canonical", None), source_kind=getattr(ret, "source_kind", None)))
    return FullProgramExecutionPlan(program_id, composition_id, schedule, tuple(instructions))


@dataclass(frozen=True, slots=True)
class FullProgramTraceStep:
    pc: int
    kind: str
    operator_start: int
    operator_stop: int
    control_location_before: str | None
    control_location_after: str | None
    reference_id: str

    @property
    def payload(self) -> dict[str, object]:
        return {"schema": TRACE_SCHEMA, "pc": self.pc, "kind": self.kind, "operator_start": self.operator_start, "operator_stop": self.operator_stop, "control_location_before": self.control_location_before, "control_location_after": self.control_location_after, "reference_id": self.reference_id}


@dataclass(frozen=True, slots=True)
class FullProgramExecutionReceipt:
    plan: FullProgramExecutionPlan
    control_dispatch_id: str
    generation_id: str
    result_id: str
    lineage_id: str
    branch_truth_state: str
    trace: tuple[FullProgramTraceStep, ...]
    return_ref_id: str
    return_selector: str
    return_source_kind: str
    return_value: object
    final_control_location: str

    def __post_init__(self) -> None:
        _typed(self.control_dispatch_id, _DISPATCH_RE, "control_dispatch_id")
        _typed(self.generation_id, _GENERATION_RE, "generation_id")
        _typed(self.result_id, _RESULT_RE, "result_id")
        _typed(self.lineage_id, _LINEAGE_RE, "lineage_id")
        _typed(self.return_ref_id, _RETURN_RE, "return_ref_id")
        if self.branch_truth_state not in {"TRUE", "FALSE"}:
            raise FullProgramExecutorV01Error("invalid branch_truth_state")
        if not self.final_control_location:
            raise FullProgramExecutorV01Error("final control location required")
        if len(self.trace) != len(self.plan.instructions) or tuple(s.pc for s in self.trace) != tuple(range(len(self.trace))):
            raise FullProgramExecutorV01Error("trace must cover contiguous instruction pc sequence")

    @property
    def payload(self) -> dict[str, object]:
        return {"schema": FULL_EXECUTOR_SCHEMA, "executor_contract_id": FULL_EXECUTOR_CONTRACT_ID, "epistemic_status": EPISTEMIC_STATUS, "mode": MODE, "promotion_track": PROMOTION_TRACK, "plan_id": self.plan.plan_id, "program_id": self.plan.program_id, "composition_id": self.plan.composition_id, "control_dispatch_id": self.control_dispatch_id, "generation_id": self.generation_id, "result_id": self.result_id, "lineage_id": self.lineage_id, "branch_truth_state": self.branch_truth_state, "trace": [s.payload for s in self.trace], "return_ref_id": self.return_ref_id, "return_selector": self.return_selector, "return_source_kind": self.return_source_kind, "return_value": self.return_value, "final_control_location": self.final_control_location, "halted": True, "continuation_execution_opened": True, "return_execution_opened": True, "full_current_bounded_program_execution": True, "loops_opened": False, "function_calls_opened": False, "external_effects": False, "free_form_nl_execution": False, "static_runtime_fallback": False, "deterministic_fields_only": True}

    @property
    def execution_id(self) -> str:
        return _typed_id("pncs:full-program-execution", self.payload)


def _dispatch_payload(dispatch: object, program_id: str, handle_id: str | None) -> Mapping[str, object]:
    payload = _mapping(getattr(dispatch, "payload", None), "resident dispatch payload")
    if payload.get("schema") != DISPATCH_SCHEMA or payload.get("runtime_contract_id") != RUNTIME_CONTRACT_ID:
        raise FullProgramExecutorV01Error("resident dispatch schema/contract mismatch")
    if payload.get("program_id") != program_id:
        raise FullProgramExecutorV01Error("resident dispatch program mismatch")
    if payload.get("kernel_scope") != "CONTROL_ROOT_V0_20":
        raise FullProgramExecutorV01Error("resident dispatch kernel scope mismatch")
    _closed(payload, "continuation_execution_opened", "return_execution_opened", "external_effects", "static_runtime_fallback")
    _deterministic(payload)
    if payload.get("result_lineage_contract_id") != LINEAGE_CONTRACT_ID:
        raise FullProgramExecutorV01Error("resident dispatch lineage contract mismatch")
    dispatch_id = _typed(getattr(dispatch, "dispatch_id", None), _DISPATCH_RE, "dispatch_id")
    if handle_id is not None:
        _typed(handle_id, _HANDLE_RE, "expected_handle_id")
        if payload.get("handle_id") != handle_id:
            raise FullProgramExecutorV01Error("resident dispatch handle mismatch")
    _typed(payload.get("generation_id"), _GENERATION_RE, "generation_id")
    _typed(payload.get("result_id"), _RESULT_RE, "result_id")
    _typed(payload.get("lineage_id"), _LINEAGE_RE, "lineage_id")
    if payload.get("branch_truth_state") not in {"TRUE", "FALSE"} or not isinstance(payload.get("target"), str) or not payload.get("target"):
        raise FullProgramExecutorV01Error("invalid resident control result")
    if dispatch_id != _typed_id("pncs:resident-dispatch", payload):
        raise FullProgramExecutorV01Error("resident dispatch content-address identity mismatch")
    return payload


def _select_return(selector: str, source_kind: str, control_location: str, dispatch: Mapping[str, object], bindings: Mapping[str, object]) -> object:
    if selector == "result.control_location" and source_kind == "V0_20_RESULT":
        return control_location
    if selector == "result.branch_truth_state" and source_kind == "V0_20_RESULT":
        return dispatch["branch_truth_state"]
    if selector == "result.lineage_id" and source_kind == "V0_22_LINEAGE":
        return dispatch["lineage_id"]
    if selector == "result.final_sigma_id" and source_kind == "V0_20_FINAL_STATE":
        value = bindings.get(selector)
        if not isinstance(value, str) or not _TYPED_VALUE_RE.fullmatch(value):
            raise FullProgramExecutorV01Error("result.final_sigma_id requires explicit typed return binding")
        return value
    raise FullProgramExecutorV01Error("unsupported or mismatched return selector/source kind")


def execute_prepared_program(plan: FullProgramExecutionPlan, control_dispatch: Callable[[], object], *, expected_handle_id: str | None = None, return_bindings: Mapping[str, object] | None = None) -> FullProgramExecutionReceipt:
    if not isinstance(plan, FullProgramExecutionPlan):
        raise FullProgramExecutorV01Error("FullProgramExecutionPlan required")
    if not callable(control_dispatch):
        raise FullProgramExecutorV01Error("control_dispatch callback required")
    dispatch_obj = control_dispatch()
    dispatch = _dispatch_payload(dispatch_obj, plan.program_id, expected_handle_id)
    control_location = str(dispatch["target"])
    trace: list[FullProgramTraceStep] = []
    for instruction in plan.instructions:
        before = None if instruction.kind == "CONTROL_DISPATCH" and not trace else control_location
        if instruction.kind == "CONTINUATION_ROUTE":
            control_location = str(instruction.target)
        trace.append(FullProgramTraceStep(instruction.pc, instruction.kind, instruction.operator_start, instruction.operator_stop, before, control_location, instruction.reference_id))
    ret = plan.instructions[-1]
    return_value = _select_return(str(ret.target), str(ret.source_kind), control_location, dispatch, dict(return_bindings or {}))
    return FullProgramExecutionReceipt(plan, str(getattr(dispatch_obj, "dispatch_id")), str(dispatch["generation_id"]), str(dispatch["result_id"]), str(dispatch["lineage_id"]), str(dispatch["branch_truth_state"]), tuple(trace), ret.reference_id, str(ret.target), str(ret.source_kind), return_value, control_location)


def execute_full_program(unit: object, composition: object, control_dispatch: Callable[[], object], *, expected_handle_id: str | None = None, return_bindings: Mapping[str, object] | None = None) -> FullProgramExecutionReceipt:
    plan = compile_full_program_plan(unit, composition)
    return execute_prepared_program(plan, control_dispatch, expected_handle_id=expected_handle_id, return_bindings=return_bindings)


def execute_resident_program(runtime: object, handle_id: str, unit: object, composition: object, kernel: Callable[[], tuple[object, object]], *, return_bindings: Mapping[str, object] | None = None) -> FullProgramExecutionReceipt:
    dispatch_control = getattr(runtime, "dispatch_control", None)
    if not callable(dispatch_control):
        raise FullProgramExecutorV01Error("PersistentProgramRuntime-compatible dispatch_control required")
    _typed(handle_id, _HANDLE_RE, "handle_id")
    return execute_full_program(unit, composition, lambda: dispatch_control(handle_id, kernel), expected_handle_id=handle_id, return_bindings=return_bindings)
