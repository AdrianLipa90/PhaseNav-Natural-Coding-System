from __future__ import annotations

from dataclasses import dataclass, replace
import struct
from typing import Mapping

from .execution_v20_model import (
    BoundInternalProgram, NativeExecutionV20Error, EXECUTABLE_INTERNAL_OPERATORS, SIGMA_SCHEMA, STEP_SCHEMA, expected_leaf_path, _finite_scalar, _route,
    _sha256_bytes, _sha256_json, _typed_id,
)
from .execution_v20_live import LiveSurfaceSnapshot, LiveSurfaceV20Error

def _normalize_values(values: Mapping[str, object]) -> tuple[tuple[str, float], ...]:
    if not isinstance(values, Mapping):
        raise NativeExecutionV20Error("runtime values must be a mapping")
    out: list[tuple[str, float]] = []
    for key in sorted(values):
        if not isinstance(key, str) or not key:
            raise NativeExecutionV20Error("runtime value names must be non-empty strings")
        out.append((key, _finite_scalar(values[key], f"runtime value {key}")))
    return tuple(out)


@dataclass(frozen=True)
class SigmaState:
    content_id: str
    realization_id: str
    mass_binding_id: str
    phase36_sha256: str
    semantic_mass: float
    surface_phi_sha256: str
    input_values: tuple[tuple[str, float], ...]
    control_location: str
    step_index: int = 0
    accumulator: float | None = None
    truth_stack: tuple[bool, ...] = ()
    selected_route: str | None = None
    last_operator: str | None = None

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": SIGMA_SCHEMA,
            "content_id": self.content_id,
            "realization_id": self.realization_id,
            "mass_binding_id": self.mass_binding_id,
            "phase36_sha256": self.phase36_sha256,
            "semantic_mass": self.semantic_mass,
            "surface_phi_sha256": self.surface_phi_sha256,
            "input_values": [[k, v] for k, v in self.input_values],
            "control_location": self.control_location,
            "step_index": self.step_index,
            "accumulator": self.accumulator,
            "truth_stack": list(self.truth_stack),
            "selected_route": self.selected_route,
            "last_operator": self.last_operator,
        }

    @property
    def state_id(self) -> str:
        return _typed_id("pncs:sigma", self.payload)


@dataclass(frozen=True)
class ExecutionStep:
    index: int
    operator_id: str
    operator_vector_sha256: str
    before_sigma_id: str
    after_sigma_id: str
    bindings: Mapping[str, object]

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": STEP_SCHEMA,
            "index": self.index,
            "operator_id": self.operator_id,
            "operator_vector_sha256": self.operator_vector_sha256,
            "before_sigma_id": self.before_sigma_id,
            "after_sigma_id": self.after_sigma_id,
            "bindings": dict(self.bindings),
        }


@dataclass(frozen=True)
class NativeExecutionResult:
    target: str
    branch_truth_state: str
    final_state: SigmaState
    receipt: Mapping[str, object]
    receipt_path: str


class _Executor:
    def __init__(self, program: BoundInternalProgram, live: LiveSurfaceSnapshot):
        self.program = program
        self.live = live
        self.steps: list[ExecutionStep] = []

    def _transition(self, state: SigmaState, operator_id: str, *, bindings: Mapping[str, object], **changes: object) -> SigmaState:
        if operator_id not in EXECUTABLE_INTERNAL_OPERATORS:
            raise NativeExecutionV20Error(f"operator has no v0.20 internal execution semantics: {operator_id}")
        vector = self.live.operator_vectors.get(operator_id)
        if vector is None:
            raise LiveSurfaceV20Error(f"operator is not present in live PhaseNav registry: {operator_id}")
        raw = struct.pack("<36d", *vector)
        before = state.state_id
        allowed = {
            "accumulator",
            "truth_stack",
            "selected_route",
            "control_location",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise NativeExecutionV20Error(f"unsupported Sigma mutation fields: {sorted(unknown)}")
        after = replace(
            state,
            step_index=state.step_index + 1,
            last_operator=operator_id,
            **changes,
        )
        self.steps.append(
            ExecutionStep(
                index=after.step_index,
                operator_id=operator_id,
                operator_vector_sha256=_sha256_bytes(raw),
                before_sigma_id=before,
                after_sigma_id=after.state_id,
                bindings=dict(bindings),
            )
        )
        return after

    def _eval(self, node: tuple[object, ...], state: SigmaState) -> SigmaState:
        kind = node[0]
        values = dict(state.input_values)
        if kind == "comparison":
            subject = str(node[1])
            comparator = str(node[2])
            threshold = _finite_scalar(node[3], "comparison threshold")
            if subject not in values:
                raise NativeExecutionV20Error(f"missing runtime value for {subject}")
            value = values[subject]
            delta = value - threshold
            state = self._transition(
                state,
                "DIFFERENCE",
                accumulator=delta,
                bindings={"subject": subject, "value": value, "threshold": threshold},
            )
            if comparator == "lt":
                truth = delta < 0.0
            elif comparator == "gt":
                truth = delta > 0.0
            elif comparator == "eq":
                truth = delta == 0.0
            else:
                raise NativeExecutionV20Error(f"unsupported comparator: {comparator}")
            return self._transition(
                state,
                "CONDITION",
                truth_stack=state.truth_stack + (truth,),
                bindings={"comparator": comparator, "difference": delta, "truth": truth},
            )

        if kind == "not":
            state = self._eval(node[1], state)  # type: ignore[arg-type]
            if not state.truth_stack:
                raise NativeExecutionV20Error("NEGATION requires a predicate truth value")
            truth = not state.truth_stack[-1]
            return self._transition(
                state,
                "NEGATION",
                truth_stack=state.truth_stack[:-1] + (truth,),
                bindings={"truth": truth},
            )

        if kind in {"and", "or"}:
            children = node[1:]
            state = self._eval(children[0], state)  # type: ignore[arg-type]
            for child in children[1:]:
                state = self._eval(child, state)  # type: ignore[arg-type]
                if len(state.truth_stack) < 2:
                    raise NativeExecutionV20Error("COMPOSITION requires two predicate truth values")
                left, right = state.truth_stack[-2], state.truth_stack[-1]
                truth = (left and right) if kind == "and" else (left or right)
                state = self._transition(
                    state,
                    "COMPOSITION",
                    truth_stack=state.truth_stack[:-2] + (truth,),
                    bindings={"mode": "all" if kind == "and" else "any", "left": left, "right": right, "truth": truth},
                )
            return state
        raise NativeExecutionV20Error(f"unsupported predicate execution node: {kind!r}")

    def run(self, initial: SigmaState, admitted_target: str) -> tuple[SigmaState, str]:
        graph = self.program.canonical_graph
        expected_leaf_path(graph)
        predicate = graph[1]
        true_target = _route(graph[2], "true_target")
        false_target = None if graph[3] is None else _route(graph[3], "false_target")
        state = self._eval(predicate, initial)  # type: ignore[arg-type]
        if len(state.truth_stack) != 1:
            raise NativeExecutionV20Error("predicate execution did not reduce to exactly one truth value")
        raw_truth = state.truth_stack[-1]
        truth_state = "TRUE" if raw_truth else "FALSE"
        expected_target = true_target if raw_truth else false_target
        if expected_target is None:
            raise NativeExecutionV20Error("canonical branch produced no admitted internal route")
        admitted = _route(admitted_target, "admitted_target")
        if admitted != expected_target:
            raise NativeExecutionV20Error(
                f"admission/graph mismatch: admitted={admitted!r}, evaluated={expected_target!r}"
            )

        # The false arm is represented by NEGATION(primary_predicate) in the frozen
        # v0.8+ graph. Execute that KAKU only when the false arm is selected.
        if not raw_truth and false_target is not None:
            state = self._transition(
                state,
                "NEGATION",
                truth_stack=state.truth_stack[:-1] + (True,),
                bindings={"branch": "FALSE", "source_truth": False, "admission_truth": True},
            )
        state = self._transition(
            state,
            "ORDER",
            selected_route=expected_target,
            bindings={"branch": truth_state, "target": expected_target},
        )
        state = self._transition(
            state,
            "TRANSFORM",
            control_location=expected_target,
            bindings={"domain": "control_location", "target": expected_target},
        )
        state = self._transition(
            state,
            "COMPOSITION",
            bindings={"mode": "branch_close", "target": expected_target},
        )
        return state, truth_state
