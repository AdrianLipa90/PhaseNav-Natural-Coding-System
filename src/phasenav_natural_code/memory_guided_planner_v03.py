"""Memory-guided execution planner candidate for PNCS Hybrid Memory Grammar v0.3.

Binds implicit procedural memory to future route selection:
GUIDE -> plan -> execute/observe -> TRACE feedback -> changed future plan.

The planner is deterministic, in-memory, and fail-closed. It performs no
external effects, no durable write, and makes no quantum-substrate claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import json
from typing import Iterable, Mapping

from .procedural_memory_runtime_v03 import (
    ProceduralMemoryRuntime,
    ProceduralMemoryRuntimeError,
)

SCHEMA = "PNCS_MEMORY_GUIDED_PLANNER_V0_3"
DECISION_SCHEMA = "PNCS_MEMORY_GUIDED_DECISION_V0_3"
FEEDBACK_SCHEMA = "PNCS_MEMORY_GUIDED_FEEDBACK_V0_3"


class MemoryGuidedPlannerError(ValueError):
    pass


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise MemoryGuidedPlannerError(f"{field} must be non-empty")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-")
    if value[0].isdigit() or any(ch not in allowed for ch in value):
        raise MemoryGuidedPlannerError(f"invalid {field}: {value}")
    return value


@dataclass(frozen=True)
class PlanDecision:
    sequence: int
    target_node_id: str
    memory_id: str
    selected_route_id: str
    node_path: tuple[str, ...]
    current_condition_digest: str
    memory_digest: str

    def to_dict(self) -> dict:
        return {
            "schema": DECISION_SCHEMA,
            "sequence": self.sequence,
            "target_node_id": self.target_node_id,
            "memory_id": self.memory_id,
            "selected_route_id": self.selected_route_id,
            "node_path": list(self.node_path),
            "current_condition_digest": self.current_condition_digest,
            "memory_digest": self.memory_digest,
            "deterministic": True,
            "external_actuation_performed": False,
            "durable_write_performed": False,
        }


@dataclass(frozen=True)
class FeedbackReceipt:
    sequence: int
    target_node_id: str
    memory_id: str
    executed_route_id: str
    outcome: str
    current_condition_digest: str
    memory_before_digest: str
    memory_after_digest: str
    prior_choice: str
    next_choice: str
    trace_receipt: Mapping[str, object]

    @property
    def changed_future_choice(self) -> bool:
        return self.prior_choice != self.next_choice

    def to_dict(self) -> dict:
        return {
            "schema": FEEDBACK_SCHEMA,
            "sequence": self.sequence,
            "target_node_id": self.target_node_id,
            "memory_id": self.memory_id,
            "executed_route_id": self.executed_route_id,
            "outcome": self.outcome,
            "current_condition_digest": self.current_condition_digest,
            "memory_before_digest": self.memory_before_digest,
            "memory_after_digest": self.memory_after_digest,
            "prior_choice": self.prior_choice,
            "next_choice": self.next_choice,
            "changed_future_choice": self.changed_future_choice,
            "trace_receipt": dict(self.trace_receipt),
            "external_actuation_performed": False,
            "durable_write_performed": False,
        }


class MemoryGuidedPlanner:
    """Bind exactly one implicit procedural memory to each guided target."""

    def __init__(
        self,
        *,
        runtimes: Mapping[str, ProceduralMemoryRuntime],
        guide_bindings: Mapping[str, str],
    ) -> None:
        if not runtimes:
            raise MemoryGuidedPlannerError("planner requires at least one memory runtime")
        self._runtimes: dict[str, ProceduralMemoryRuntime] = {}
        for memory_id, runtime in runtimes.items():
            _identifier(memory_id, "memory_id")
            if not isinstance(runtime, ProceduralMemoryRuntime):
                raise MemoryGuidedPlannerError("runtime must be ProceduralMemoryRuntime")
            if runtime.memory_id != memory_id:
                raise MemoryGuidedPlannerError("runtime memory_id mismatch")
            self._runtimes[memory_id] = runtime

        self._guides: dict[str, str] = {}
        for target, memory_id in guide_bindings.items():
            _identifier(target, "guided target")
            _identifier(memory_id, "memory_id")
            if memory_id not in self._runtimes:
                raise MemoryGuidedPlannerError(
                    f"guide references unavailable runtime {memory_id}"
                )
            if target in self._guides:
                raise MemoryGuidedPlannerError(f"duplicate guide target {target}")
            self._guides[target] = memory_id

        if not self._guides:
            raise MemoryGuidedPlannerError("planner requires at least one GUIDE binding")

        self._decision_sequence = 0
        self._feedback_sequence = 0
        self._decisions: list[PlanDecision] = []
        self._feedback: list[FeedbackReceipt] = []

    @classmethod
    def from_hybrid_ir(
        cls,
        ir: Mapping[str, object],
        *,
        learning_rate: float = 0.1,
    ) -> "MemoryGuidedPlanner":
        try:
            model = ir["memory_model"]
            operations = model["operations"]
            objects = model["objects"]
        except Exception as exc:
            raise MemoryGuidedPlannerError("missing v0.3 memory_model") from exc

        object_by_id = {obj.get("memory_id"): obj for obj in objects}
        guide_pairs: list[tuple[str, str]] = []
        for op in operations:
            if op.get("kind") != "GUIDE":
                continue
            attrs = op.get("attributes", {})
            target = attrs.get("target_node_id")
            memory_id = attrs.get("memory_id")
            if not isinstance(target, str) or not isinstance(memory_id, str):
                raise MemoryGuidedPlannerError("malformed GUIDE operation")
            obj = object_by_id.get(memory_id)
            if obj is None:
                raise MemoryGuidedPlannerError(
                    f"GUIDE references unknown memory object {memory_id}"
                )
            effects = {str(x).lower() for x in obj.get("effects", [])}
            if "routing" not in effects:
                raise MemoryGuidedPlannerError(
                    f"current memory-guided planner requires ROUTING effect; "
                    f"memory {memory_id} declares {sorted(effects)}"
                )
            guide_pairs.append((target, memory_id))

        if not guide_pairs:
            raise MemoryGuidedPlannerError("hybrid IR contains no GUIDE operation")

        by_target: dict[str, list[str]] = {}
        for target, memory_id in guide_pairs:
            by_target.setdefault(target, []).append(memory_id)

        ambiguous = {
            target: memories
            for target, memories in by_target.items()
            if len(set(memories)) != 1 or len(memories) != 1
        }
        if ambiguous:
            raise MemoryGuidedPlannerError(
                f"v0.3 does not silently combine multiple memories for one target: {ambiguous}"
            )

        guide_bindings = {target: memories[0] for target, memories in by_target.items()}
        runtime_ids = sorted(set(guide_bindings.values()))
        runtimes: dict[str, ProceduralMemoryRuntime] = {}
        for memory_id in runtime_ids:
            try:
                runtimes[memory_id] = ProceduralMemoryRuntime.from_hybrid_ir(
                    ir, memory_id, learning_rate=learning_rate
                )
            except ProceduralMemoryRuntimeError as exc:
                raise MemoryGuidedPlannerError(str(exc)) from exc

        return cls(runtimes=runtimes, guide_bindings=guide_bindings)

    def snapshot(self) -> dict:
        return {
            "schema": SCHEMA,
            "guides": dict(sorted(self._guides.items())),
            "runtimes": {
                memory_id: self._runtimes[memory_id].snapshot()
                for memory_id in sorted(self._runtimes)
            },
            "decision_sequence": self._decision_sequence,
            "feedback_sequence": self._feedback_sequence,
            "external_actuation_performed": False,
            "durable_persistence": False,
            "physical_quantum_claim": False,
        }

    @property
    def digest(self) -> str:
        return _sha256(self.snapshot())

    @property
    def decisions(self) -> tuple[PlanDecision, ...]:
        return tuple(self._decisions)

    @property
    def feedback_receipts(self) -> tuple[FeedbackReceipt, ...]:
        return tuple(self._feedback)

    def memory_runtime(self, memory_id: str) -> ProceduralMemoryRuntime:
        try:
            return self._runtimes[memory_id]
        except KeyError as exc:
            raise MemoryGuidedPlannerError(f"unknown memory runtime {memory_id}") from exc

    def plan(
        self,
        target_node_id: str,
        *,
        current_condition_digest: str,
        candidate_route_ids: Iterable[str] | None = None,
    ) -> PlanDecision:
        target = _identifier(target_node_id, "target_node_id")
        condition = str(current_condition_digest)
        if not condition:
            raise MemoryGuidedPlannerError("current_condition_digest must be non-empty")
        try:
            memory_id = self._guides[target]
        except KeyError as exc:
            raise MemoryGuidedPlannerError(f"target {target} is not memory-guided") from exc

        runtime = self._runtimes[memory_id]
        try:
            selected = runtime.guide(candidate_route_ids)
            route = runtime.route(selected)
        except ProceduralMemoryRuntimeError as exc:
            raise MemoryGuidedPlannerError(str(exc)) from exc

        self._decision_sequence += 1
        decision = PlanDecision(
            sequence=self._decision_sequence,
            target_node_id=target,
            memory_id=memory_id,
            selected_route_id=selected,
            node_path=route.node_path,
            current_condition_digest=condition,
            memory_digest=runtime.digest,
        )
        self._decisions.append(decision)
        return decision

    def feedback(
        self,
        target_node_id: str,
        executed_route_id: str,
        *,
        outcome: str,
        current_condition_digest: str,
        magnitude: float = 1.0,
        event_id: str | None = None,
        candidate_route_ids: Iterable[str] | None = None,
    ) -> FeedbackReceipt:
        target = _identifier(target_node_id, "target_node_id")
        condition = str(current_condition_digest)
        if not condition:
            raise MemoryGuidedPlannerError("current_condition_digest must be non-empty")
        try:
            memory_id = self._guides[target]
        except KeyError as exc:
            raise MemoryGuidedPlannerError(f"target {target} is not memory-guided") from exc
        runtime = self._runtimes[memory_id]

        try:
            prior_choice = runtime.guide(candidate_route_ids)
            before = runtime.digest
            trace = runtime.apply_trace(
                executed_route_id,
                outcome=outcome,
                magnitude=magnitude,
                event_id=event_id,
            )
            after = runtime.digest
            next_choice = runtime.guide(candidate_route_ids)
        except ProceduralMemoryRuntimeError as exc:
            raise MemoryGuidedPlannerError(str(exc)) from exc

        self._feedback_sequence += 1
        receipt = FeedbackReceipt(
            sequence=self._feedback_sequence,
            target_node_id=target,
            memory_id=memory_id,
            executed_route_id=executed_route_id,
            outcome=str(outcome).upper(),
            current_condition_digest=condition,
            memory_before_digest=before,
            memory_after_digest=after,
            prior_choice=prior_choice,
            next_choice=next_choice,
            trace_receipt=trace.to_dict(),
        )
        self._feedback.append(receipt)
        return receipt

    def counterfactual_memory(
        self,
        memory_id: str,
        weight_overrides: Mapping[str, float],
    ) -> "MemoryGuidedPlanner":
        """Intervention clone for causal tests; factual planner is not mutated."""
        if memory_id not in self._runtimes:
            raise MemoryGuidedPlannerError(f"unknown memory runtime {memory_id}")
        clone = copy.deepcopy(self)
        clone._runtimes[memory_id] = self._runtimes[memory_id].counterfactual(
            weight_overrides
        )
        clone._decisions = list(self._decisions)
        clone._feedback = list(self._feedback)
        return clone
