"""Latent-expression and explicit semantic-time decay for PNCS memory v0.3.

This module operationalizes two Memory Ontology distinctions without adding
wall-clock side effects:

- LATENT means a history-bearing memory exists but is not expressed under the
  current context. Activation changes expression, not the underlying memory.
- FORGETTING may occur by decay/loss of causal efficacy. Decay is applied only
  through an explicit semantic elapsed-time argument; no hidden timer is used.

Decay returns a new ProceduralMemoryRuntime plus a provenance receipt. The
input runtime is not mutated. Durable persistence remains outside this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Iterable, Mapping

from .procedural_memory_runtime_v03 import (
    ProceduralMemoryRuntime,
    ProceduralMemoryRuntimeError,
)

LATENT_SCHEMA = "PNCS_LATENT_MEMORY_GATE_V0_3"
DECAY_SCHEMA = "PNCS_MEMORY_DECAY_RECEIPT_V0_3"


class MemoryLifecycleError(ValueError):
    pass


def _finite_nonnegative(value: float, field: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out < 0:
        raise MemoryLifecycleError(f"{field} must be finite and non-negative")
    return out


def _context(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise MemoryLifecycleError("context must be non-empty")
    return value


@dataclass(frozen=True)
class LatentDecision:
    memory_id: str
    context: str
    expressed: bool
    selected_route_id: str | None
    memory_digest: str

    def to_dict(self) -> dict:
        return {
            "schema": LATENT_SCHEMA,
            "memory_id": self.memory_id,
            "context": self.context,
            "expressed": self.expressed,
            "selected_route_id": self.selected_route_id,
            "memory_digest": self.memory_digest,
            "memory_mutated_by_expression": False,
            "durable_write_performed": False,
        }


class LatentMemoryGate:
    """Expose implicit memory only in declared contexts; never mutate it."""

    def __init__(self, runtime: ProceduralMemoryRuntime, active_contexts: Iterable[str]) -> None:
        if not isinstance(runtime, ProceduralMemoryRuntime):
            raise MemoryLifecycleError("ProceduralMemoryRuntime required")
        contexts = tuple(sorted({_context(x) for x in active_contexts}))
        if not contexts:
            raise MemoryLifecycleError("at least one active context is required")
        self.runtime = runtime
        self.active_contexts = contexts

    @classmethod
    def from_hybrid_ir(
        cls,
        ir: Mapping[str, object],
        runtime: ProceduralMemoryRuntime,
        target_node_id: str,
    ) -> "LatentMemoryGate":
        try:
            operations = ir["memory_model"]["operations"]
        except Exception as exc:
            raise MemoryLifecycleError("missing v0.3 memory_model") from exc
        contexts = []
        for op in operations:
            if op.get("kind") != "GUIDE":
                continue
            attrs = op.get("attributes", {})
            if attrs.get("target_node_id") != target_node_id:
                continue
            if attrs.get("memory_id") != runtime.memory_id:
                continue
            ctx = attrs.get("activation_context")
            if ctx is not None:
                contexts.append(str(ctx))
        if not contexts:
            raise MemoryLifecycleError(
                "no conditional LATENT GUIDE binding for target and memory"
            )
        return cls(runtime, contexts)

    def evaluate(self, context: str, candidate_route_ids: Iterable[str] | None = None) -> LatentDecision:
        ctx = _context(context)
        before = self.runtime.digest
        expressed = ctx in self.active_contexts
        selected = None
        if expressed:
            try:
                selected = self.runtime.guide(candidate_route_ids)
            except ProceduralMemoryRuntimeError as exc:
                raise MemoryLifecycleError(str(exc)) from exc
        after = self.runtime.digest
        if after != before:
            raise MemoryLifecycleError("latent expression must not mutate underlying memory")
        return LatentDecision(
            memory_id=self.runtime.memory_id,
            context=ctx,
            expressed=expressed,
            selected_route_id=selected,
            memory_digest=before,
        )


@dataclass(frozen=True)
class DecayReceipt:
    memory_id: str
    delta_time: float
    tau: float
    factor: float
    extinction_threshold: float
    before_digest: str
    after_digest: str
    changed_routes: int
    extinguished_routes: int
    prior_choice: str
    next_choice: str

    @property
    def lost_choice_preference(self) -> bool:
        return self.prior_choice != self.next_choice

    def to_dict(self) -> dict:
        return {
            "schema": DECAY_SCHEMA,
            "memory_id": self.memory_id,
            "delta_time": self.delta_time,
            "tau": self.tau,
            "factor": self.factor,
            "extinction_threshold": self.extinction_threshold,
            "before_digest": self.before_digest,
            "after_digest": self.after_digest,
            "changed_routes": self.changed_routes,
            "extinguished_routes": self.extinguished_routes,
            "prior_choice": self.prior_choice,
            "next_choice": self.next_choice,
            "lost_choice_preference": self.lost_choice_preference,
            "explicit_semantic_time": True,
            "wall_clock_used": False,
            "durable_write_performed": False,
        }


@dataclass(frozen=True)
class DecayResult:
    runtime: ProceduralMemoryRuntime
    receipt: DecayReceipt


def decay_memory(
    runtime: ProceduralMemoryRuntime,
    *,
    delta_time: float,
    tau: float,
    extinction_threshold: float = 0.0,
) -> DecayResult:
    """Return an explicitly decayed clone; never mutate the supplied runtime.

    w' = w * exp(-delta_time/tau). Values with absolute magnitude below the
    declared extinction threshold are set to exactly zero. The threshold makes
    loss of causal efficacy testable rather than merely asymptotic.
    """
    if not isinstance(runtime, ProceduralMemoryRuntime):
        raise MemoryLifecycleError("ProceduralMemoryRuntime required")
    dt = _finite_nonnegative(delta_time, "delta_time")
    tau_v = float(tau)
    if not math.isfinite(tau_v) or tau_v <= 0:
        raise MemoryLifecycleError("tau must be finite and positive")
    threshold = _finite_nonnegative(extinction_threshold, "extinction_threshold")
    factor = math.exp(-dt / tau_v)

    before = runtime.digest
    try:
        prior_choice = runtime.guide()
    except ProceduralMemoryRuntimeError as exc:
        raise MemoryLifecycleError(str(exc)) from exc

    snapshot = runtime.snapshot()
    overrides: dict[str, float] = {}
    changed = 0
    extinguished = 0
    for item in snapshot["routes"]:
        old = float(item["weight"])
        new = old * factor
        if abs(new) < threshold:
            if new != 0.0:
                extinguished += 1
            new = 0.0
        if new != old:
            changed += 1
        overrides[str(item["route_id"])] = new

    try:
        decayed = runtime.counterfactual(overrides)
        next_choice = decayed.guide()
    except ProceduralMemoryRuntimeError as exc:
        raise MemoryLifecycleError(str(exc)) from exc

    if runtime.digest != before:
        raise MemoryLifecycleError("decay operation mutated factual input runtime")

    receipt = DecayReceipt(
        memory_id=runtime.memory_id,
        delta_time=dt,
        tau=tau_v,
        factor=factor,
        extinction_threshold=threshold,
        before_digest=before,
        after_digest=decayed.digest,
        changed_routes=changed,
        extinguished_routes=extinguished,
        prior_choice=prior_choice,
        next_choice=next_choice,
    )
    return DecayResult(decayed, receipt)


def decay_from_hybrid_ir(
    ir: Mapping[str, object],
    runtime: ProceduralMemoryRuntime,
    *,
    delta_time: float,
) -> DecayResult:
    try:
        operations = ir["memory_model"]["operations"]
    except Exception as exc:
        raise MemoryLifecycleError("missing v0.3 memory_model") from exc
    policies = []
    for op in operations:
        if op.get("kind") != "DECAY_POLICY":
            continue
        attrs = op.get("attributes", {})
        if attrs.get("memory_id") == runtime.memory_id:
            policies.append(attrs)
    if len(policies) != 1:
        raise MemoryLifecycleError(
            f"expected exactly one decay policy for {runtime.memory_id}; found {len(policies)}"
        )
    policy = policies[0]
    return decay_memory(
        runtime,
        delta_time=delta_time,
        tau=float(policy["tau"]),
        extinction_threshold=float(policy.get("extinction_threshold", 0.0)),
    )


def causal_efficacy_delta(
    runtime: ProceduralMemoryRuntime,
    *,
    neutral_weights: Mapping[str, float] | None = None,
) -> bool:
    """Deterministic intervention witness: does memory alter current routing?"""
    if not isinstance(runtime, ProceduralMemoryRuntime):
        raise MemoryLifecycleError("ProceduralMemoryRuntime required")
    factual = runtime.guide()
    if neutral_weights is None:
        neutral_weights = {item["route_id"]: 0.0 for item in runtime.snapshot()["routes"]}
    try:
        neutral = runtime.counterfactual(neutral_weights)
        control = neutral.guide()
    except ProceduralMemoryRuntimeError as exc:
        raise MemoryLifecycleError(str(exc)) from exc
    return factual != control


__all__ = [
    "LATENT_SCHEMA",
    "DECAY_SCHEMA",
    "MemoryLifecycleError",
    "LatentDecision",
    "LatentMemoryGate",
    "DecayReceipt",
    "DecayResult",
    "decay_memory",
    "decay_from_hybrid_ir",
    "causal_efficacy_delta",
]
