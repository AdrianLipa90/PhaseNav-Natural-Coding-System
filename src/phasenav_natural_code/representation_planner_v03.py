"""Representation-aware planner for PNCS Hybrid Memory Grammar v0.3.

Implements the Memory-Ontology separation between memory object and
representation. Candidates are admitted only if they satisfy a declared
behavioral equivalence contract. Cost comparison happens after equivalence,
never before it.

No physical-QPU or quantum-advantage claim is inferred from a representation
family label.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Mapping

SCHEMA = "PNCS_REPRESENTATION_PLANNER_V0_3"
CANDIDATE_SCHEMA = "PNCS_REPRESENTATION_CANDIDATE_V0_3"
DECISION_SCHEMA = "PNCS_REPRESENTATION_DECISION_V0_3"

FAMILIES = frozenset({"BINARY", "HYBRID", "QUANTUM_NATIVE", "SUBSTRATE_NEUTRAL", "TERNARY_BALANCED", "TERNARY_STELLA"})
EVIDENCE = frozenset({
    "FORMAL_ONLY",
    "PARITY",
    "CLASSICAL_COMPRESSION",
    "CANDIDATE_Q_NATIVE_ADVANTAGE",
    "EMPIRICAL_Q_NATIVE_ADVANTAGE",
    "THEORETICAL_SEPARATION",
})
COST_FIELDS = (
    "storage",
    "compile_time",
    "update_time",
    "query_time",
    "sample_count",
    "sequential_depth",
)


class RepresentationPlannerError(ValueError):
    pass


def _finite_nonnegative(value: float, field: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out < 0:
        raise RepresentationPlannerError(f"{field} must be finite and non-negative")
    return out


@dataclass(frozen=True)
class EquivalenceContract:
    epsilon: float
    horizon: int | str
    observable_contract: str
    distance: str = "declared_output_distance"

    def __post_init__(self) -> None:
        object.__setattr__(self, "epsilon", _finite_nonnegative(self.epsilon, "epsilon"))
        if isinstance(self.horizon, bool):
            raise RepresentationPlannerError("horizon cannot be boolean")
        if isinstance(self.horizon, int):
            if self.horizon < 1:
                raise RepresentationPlannerError("integer horizon must be positive")
        elif not isinstance(self.horizon, str) or not self.horizon.strip():
            raise RepresentationPlannerError("horizon must be positive integer or non-empty label")
        if not isinstance(self.observable_contract, str) or not self.observable_contract.strip():
            raise RepresentationPlannerError("observable_contract must be non-empty")
        if not isinstance(self.distance, str) or not self.distance.strip():
            raise RepresentationPlannerError("distance must be non-empty")

    def admits(self, requested: "EquivalenceContract") -> bool:
        if self.observable_contract != requested.observable_contract:
            return False
        if self.distance != requested.distance:
            return False
        if self.epsilon > requested.epsilon:
            return False
        if isinstance(requested.horizon, int):
            return isinstance(self.horizon, int) and self.horizon >= requested.horizon
        return self.horizon == requested.horizon

    def to_dict(self) -> dict:
        return {
            "epsilon": self.epsilon,
            "horizon": self.horizon,
            "observable_contract": self.observable_contract,
            "distance": self.distance,
        }


@dataclass(frozen=True)
class ResourceVector:
    storage: float
    compile_time: float
    update_time: float
    query_time: float
    sample_count: float
    sequential_depth: float

    def __post_init__(self) -> None:
        for field in COST_FIELDS:
            object.__setattr__(self, field, _finite_nonnegative(getattr(self, field), field))

    def to_dict(self) -> dict:
        return {field: getattr(self, field) for field in COST_FIELDS}

    def weighted(self, weights: Mapping[str, float]) -> float:
        unknown = sorted(set(weights) - set(COST_FIELDS))
        if unknown:
            raise RepresentationPlannerError(f"unknown cost weight(s): {unknown}")
        total = 0.0
        for field in COST_FIELDS:
            weight = _finite_nonnegative(weights.get(field, 0.0), f"weight.{field}")
            total += weight * getattr(self, field)
        if all(float(weights.get(field, 0.0)) == 0.0 for field in COST_FIELDS):
            raise RepresentationPlannerError("at least one cost weight must be positive")
        return total

    def dominates(self, other: "ResourceVector") -> bool:
        le = all(getattr(self, f) <= getattr(other, f) for f in COST_FIELDS)
        lt = any(getattr(self, f) < getattr(other, f) for f in COST_FIELDS)
        return le and lt


@dataclass(frozen=True)
class RepresentationCandidate:
    candidate_id: str
    family: str
    contract: EquivalenceContract
    cost: ResourceVector
    evidence_status: str
    available: bool = True
    physical_quantum_claim: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, str) or not self.candidate_id.strip():
            raise RepresentationPlannerError("candidate_id must be non-empty")
        family = str(self.family).upper()
        object.__setattr__(self, "family", family)
        if family not in FAMILIES:
            raise RepresentationPlannerError(f"unsupported representation family {family}")
        evidence = str(self.evidence_status).upper()
        object.__setattr__(self, "evidence_status", evidence)
        if evidence not in EVIDENCE:
            raise RepresentationPlannerError(f"unsupported evidence status {evidence}")
        if self.physical_quantum_claim:
            raise RepresentationPlannerError(
                "representation planner cannot self-assert physical quantum substrate"
            )

    def to_dict(self) -> dict:
        return {
            "schema": CANDIDATE_SCHEMA,
            "candidate_id": self.candidate_id,
            "family": self.family.lower(),
            "contract": self.contract.to_dict(),
            "cost": self.cost.to_dict(),
            "evidence_status": self.evidence_status.lower(),
            "available": self.available,
            "physical_quantum_claim": False,
        }


@dataclass(frozen=True)
class RepresentationDecision:
    requested_contract: EquivalenceContract
    selected: RepresentationCandidate
    eligible_ids: tuple[str, ...]
    pareto_ids: tuple[str, ...]
    weights: Mapping[str, float]
    weighted_cost: float

    def to_dict(self) -> dict:
        return {
            "schema": DECISION_SCHEMA,
            "requested_contract": self.requested_contract.to_dict(),
            "selected": self.selected.to_dict(),
            "eligible_ids": list(self.eligible_ids),
            "pareto_ids": list(self.pareto_ids),
            "weights": dict(self.weights),
            "weighted_cost": self.weighted_cost,
            "semantic_equivalence_checked_before_cost": True,
            "quantum_advantage_claim": False,
            "physical_quantum_claim": False,
        }


def eligible_candidates(
    candidates: Iterable[RepresentationCandidate],
    requested: EquivalenceContract,
) -> tuple[RepresentationCandidate, ...]:
    seen: set[str] = set()
    out: list[RepresentationCandidate] = []
    for candidate in candidates:
        if candidate.candidate_id in seen:
            raise RepresentationPlannerError(f"duplicate candidate_id {candidate.candidate_id}")
        seen.add(candidate.candidate_id)
        if candidate.available and candidate.contract.admits(requested):
            out.append(candidate)
    return tuple(sorted(out, key=lambda c: c.candidate_id))


def pareto_frontier(
    candidates: Iterable[RepresentationCandidate],
) -> tuple[RepresentationCandidate, ...]:
    items = tuple(candidates)
    out = []
    for candidate in items:
        if not any(other.cost.dominates(candidate.cost) for other in items if other is not candidate):
            out.append(candidate)
    return tuple(sorted(out, key=lambda c: c.candidate_id))


def select_representation(
    candidates: Iterable[RepresentationCandidate],
    requested: EquivalenceContract,
    *,
    weights: Mapping[str, float],
) -> RepresentationDecision:
    eligible = eligible_candidates(candidates, requested)
    if not eligible:
        raise RepresentationPlannerError("no representation satisfies requested equivalence contract")
    frontier = pareto_frontier(eligible)
    scored = [(candidate.cost.weighted(weights), candidate.candidate_id, candidate) for candidate in frontier]
    score, _, selected = min(scored, key=lambda x: (x[0], x[1]))
    return RepresentationDecision(
        requested_contract=requested,
        selected=selected,
        eligible_ids=tuple(c.candidate_id for c in eligible),
        pareto_ids=tuple(c.candidate_id for c in frontier),
        weights=dict(weights),
        weighted_cost=score,
    )


def economic_cost_ratio(
    numerator: RepresentationCandidate,
    denominator: RepresentationCandidate,
    *,
    weights: Mapping[str, float],
) -> float:
    a = numerator.cost.weighted(weights)
    b = denominator.cost.weighted(weights)
    if b == 0:
        raise RepresentationPlannerError("denominator weighted cost is zero")
    return a / b
