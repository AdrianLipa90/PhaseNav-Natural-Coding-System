"""Representation-equivalence arbiter for PNCS memory/runtime candidates.

Implements the Memory Ontology separation:
memory law != representation != physical substrate.

Backends are admitted only if they satisfy a declared behavioral equivalence
contract. Cost optimization happens only inside the admitted set.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

SCHEMA = "PNCS_MEMORY_REPRESENTATION_ARBITER_V0_3"
FAMILIES = {"QUANTUM_NATIVE", "BINARY", "HYBRID", "SUBSTRATE_NEUTRAL"}
EVIDENCE = {
    "FORMAL_ONLY",
    "PARITY",
    "CLASSICAL_COMPRESSION",
    "CANDIDATE_Q_NATIVE_ADVANTAGE",
    "EMPIRICAL_Q_NATIVE_ADVANTAGE",
    "THEORETICAL_SEPARATION",
    "PHYSICAL_QUANTUM_NECESSITY",
}
METRICS = (
    "storage",
    "compile_time",
    "update_time",
    "query_time",
    "sample_count",
    "sequential_depth",
)


class RepresentationArbiterError(ValueError):
    pass


def _finite_nonnegative(value: float, field: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out < 0:
        raise RepresentationArbiterError(f"{field} must be finite and non-negative")
    return out


@dataclass(frozen=True)
class EquivalenceContract:
    epsilon: float
    horizon: int | str
    observable_contract: str
    distance: str = "declared_output_distance"

    def __post_init__(self) -> None:
        object.__setattr__(self, "epsilon", _finite_nonnegative(self.epsilon, "epsilon"))
        if isinstance(self.horizon, int):
            if self.horizon < 1:
                raise RepresentationArbiterError("horizon must be positive")
        elif not isinstance(self.horizon, str) or not self.horizon:
            raise RepresentationArbiterError("invalid horizon")
        if not isinstance(self.observable_contract, str) or not self.observable_contract:
            raise RepresentationArbiterError("observable_contract must be non-empty")
        if not isinstance(self.distance, str) or not self.distance:
            raise RepresentationArbiterError("distance must be non-empty")


@dataclass(frozen=True)
class BackendMeasurement:
    backend_id: str
    representation_family: str
    behavioral_error: float
    storage: float
    compile_time: float
    update_time: float
    query_time: float
    sample_count: float
    sequential_depth: float
    evidence_status: str = "FORMAL_ONLY"
    physical_substrate_claim: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.backend_id, str) or not self.backend_id:
            raise RepresentationArbiterError("backend_id must be non-empty")
        family = str(self.representation_family).upper()
        if family not in FAMILIES:
            raise RepresentationArbiterError("unsupported representation family")
        object.__setattr__(self, "representation_family", family)
        object.__setattr__(self, "behavioral_error", _finite_nonnegative(self.behavioral_error, "behavioral_error"))
        for field in METRICS:
            object.__setattr__(self, field, _finite_nonnegative(getattr(self, field), field))
        evidence = str(self.evidence_status).upper()
        if evidence not in EVIDENCE:
            raise RepresentationArbiterError("unsupported evidence status")
        object.__setattr__(self, "evidence_status", evidence)
        if evidence == "PHYSICAL_QUANTUM_NECESSITY" and not self.physical_substrate_claim:
            raise RepresentationArbiterError(
                "PHYSICAL_QUANTUM_NECESSITY evidence requires an explicit physical substrate claim"
            )

    def cost_vector(self) -> tuple[float, ...]:
        return tuple(getattr(self, field) for field in METRICS)

    def to_dict(self) -> dict:
        return {
            "backend_id": self.backend_id,
            "representation_family": self.representation_family.lower(),
            "behavioral_error": self.behavioral_error,
            "cost": {field: getattr(self, field) for field in METRICS},
            "evidence_status": self.evidence_status.lower(),
            "physical_substrate_claim": self.physical_substrate_claim,
        }


@dataclass(frozen=True)
class ArbitrationDecision:
    selected_backend_id: str
    admitted_backend_ids: tuple[str, ...]
    pareto_backend_ids: tuple[str, ...]
    scalar_costs: Mapping[str, float]
    epsilon: float
    horizon: int | str
    observable_contract: str

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "selected_backend_id": self.selected_backend_id,
            "admitted_backend_ids": list(self.admitted_backend_ids),
            "pareto_backend_ids": list(self.pareto_backend_ids),
            "scalar_costs": dict(self.scalar_costs),
            "equivalence_contract": {
                "epsilon": self.epsilon,
                "horizon": self.horizon,
                "observable_contract": self.observable_contract,
            },
            "selection_after_equivalence_only": True,
            "physical_substrate_inferred_from_representation": False,
        }


class RepresentationArbiter:
    def __init__(
        self,
        contract: EquivalenceContract,
        measurements: tuple[BackendMeasurement, ...],
    ) -> None:
        if not measurements:
            raise RepresentationArbiterError("at least one backend measurement is required")
        ids = [m.backend_id for m in measurements]
        if len(ids) != len(set(ids)):
            raise RepresentationArbiterError("backend_id values must be unique")
        self.contract = contract
        self.measurements = {m.backend_id: m for m in measurements}

    def admitted(self) -> tuple[BackendMeasurement, ...]:
        return tuple(
            self.measurements[key]
            for key in sorted(self.measurements)
            if self.measurements[key].behavioral_error <= self.contract.epsilon
        )

    def pareto_frontier(self) -> tuple[BackendMeasurement, ...]:
        admitted = self.admitted()
        frontier = []
        for candidate in admitted:
            c = candidate.cost_vector()
            dominated = False
            for other in admitted:
                if other.backend_id == candidate.backend_id:
                    continue
                o = other.cost_vector()
                if all(a <= b for a, b in zip(o, c)) and any(a < b for a, b in zip(o, c)):
                    dominated = True
                    break
            if not dominated:
                frontier.append(candidate)
        return tuple(sorted(frontier, key=lambda m: m.backend_id))

    def scalar_cost(self, backend_id: str, weights: Mapping[str, float]) -> float:
        try:
            m = self.measurements[backend_id]
        except KeyError as exc:
            raise RepresentationArbiterError(f"unknown backend {backend_id}") from exc
        unknown = sorted(set(weights) - set(METRICS))
        if unknown:
            raise RepresentationArbiterError(f"unknown cost weights: {unknown}")
        total = 0.0
        for field in METRICS:
            w = _finite_nonnegative(weights.get(field, 0.0), f"weight:{field}")
            total += w * getattr(m, field)
        return total

    def select(self, weights: Mapping[str, float]) -> ArbitrationDecision:
        admitted = self.admitted()
        if not admitted:
            raise RepresentationArbiterError("no backend satisfies behavioral equivalence contract")
        if not any(float(weights.get(field, 0.0)) > 0 for field in METRICS):
            raise RepresentationArbiterError("at least one positive cost weight is required")
        costs = {m.backend_id: self.scalar_cost(m.backend_id, weights) for m in admitted}
        selected = min(costs, key=lambda backend_id: (costs[backend_id], backend_id))
        frontier = self.pareto_frontier()
        return ArbitrationDecision(
            selected_backend_id=selected,
            admitted_backend_ids=tuple(m.backend_id for m in admitted),
            pareto_backend_ids=tuple(m.backend_id for m in frontier),
            scalar_costs=costs,
            epsilon=self.contract.epsilon,
            horizon=self.contract.horizon,
            observable_contract=self.contract.observable_contract,
        )

    def cost_ratio(
        self,
        numerator_backend_id: str,
        denominator_backend_id: str,
        weights: Mapping[str, float],
    ) -> float:
        admitted = {m.backend_id for m in self.admitted()}
        if numerator_backend_id not in admitted or denominator_backend_id not in admitted:
            raise RepresentationArbiterError("cost ratio requires two equivalent/admitted backends")
        numerator = self.scalar_cost(numerator_backend_id, weights)
        denominator = self.scalar_cost(denominator_backend_id, weights)
        if denominator == 0:
            raise RepresentationArbiterError("denominator scalar cost is zero")
        return numerator / denominator
