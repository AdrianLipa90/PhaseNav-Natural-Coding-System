"""Measured-backend adapter for the canonical PNCS representation planner v0.3.

This module is intentionally thin. The canonical admission/Pareto/cost logic
lives in representation_planner_v03.py. Here we translate empirical backend
measurements into RepresentationCandidate objects under one requested contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .representation_planner_v03 import (
    COST_FIELDS,
    EquivalenceContract,
    RepresentationCandidate,
    RepresentationDecision,
    RepresentationPlannerError,
    ResourceVector,
    economic_cost_ratio,
    pareto_frontier,
    select_representation,
)

SCHEMA = "PNCS_MEMORY_REPRESENTATION_ARBITER_V0_3"


class RepresentationArbiterError(RepresentationPlannerError):
    pass


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

    def to_candidate(self, requested: EquivalenceContract) -> RepresentationCandidate:
        if self.physical_substrate_claim:
            raise RepresentationArbiterError(
                "measured-backend adapter cannot self-assert physical quantum substrate"
            )
        contract = EquivalenceContract(
            self.behavioral_error,
            requested.horizon,
            requested.observable_contract,
            requested.distance,
        )
        cost = ResourceVector(
            self.storage,
            self.compile_time,
            self.update_time,
            self.query_time,
            self.sample_count,
            self.sequential_depth,
        )
        try:
            return RepresentationCandidate(
                self.backend_id,
                self.representation_family,
                contract,
                cost,
                self.evidence_status,
                physical_quantum_claim=False,
            )
        except RepresentationPlannerError as exc:
            raise RepresentationArbiterError(str(exc)) from exc


@dataclass(frozen=True)
class ArbitrationDecision:
    decision: RepresentationDecision

    @property
    def selected_backend_id(self) -> str:
        return self.decision.selected.candidate_id

    @property
    def admitted_backend_ids(self) -> tuple[str, ...]:
        return self.decision.eligible_ids

    @property
    def pareto_backend_ids(self) -> tuple[str, ...]:
        return self.decision.pareto_ids

    @property
    def scalar_costs(self) -> Mapping[str, float]:
        return {self.decision.selected.candidate_id: self.decision.weighted_cost}

    def to_dict(self) -> dict:
        payload = self.decision.to_dict()
        payload["schema"] = SCHEMA
        payload["canonical_planner"] = "PNCS_REPRESENTATION_PLANNER_V0_3"
        payload["measured_backend_adapter"] = True
        return payload


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
        self.measurements = measurements

    def candidates(self) -> tuple[RepresentationCandidate, ...]:
        return tuple(m.to_candidate(self.contract) for m in self.measurements)

    def admitted(self) -> tuple[RepresentationCandidate, ...]:
        candidates = self.candidates()
        return tuple(c for c in candidates if c.contract.admits(self.contract))

    def pareto_frontier(self) -> tuple[RepresentationCandidate, ...]:
        return pareto_frontier(self.admitted())

    def select(self, weights: Mapping[str, float]) -> ArbitrationDecision:
        try:
            decision = select_representation(
                self.candidates(), self.contract, weights=weights
            )
        except RepresentationPlannerError as exc:
            raise RepresentationArbiterError(str(exc)) from exc
        return ArbitrationDecision(decision)

    def cost_ratio(
        self,
        numerator_backend_id: str,
        denominator_backend_id: str,
        weights: Mapping[str, float],
    ) -> float:
        admitted = {c.candidate_id: c for c in self.admitted()}
        if numerator_backend_id not in admitted or denominator_backend_id not in admitted:
            raise RepresentationArbiterError(
                "cost ratio requires two equivalent/admitted backends"
            )
        try:
            return economic_cost_ratio(
                admitted[numerator_backend_id],
                admitted[denominator_backend_id],
                weights=weights,
            )
        except RepresentationPlannerError as exc:
            raise RepresentationArbiterError(str(exc)) from exc
