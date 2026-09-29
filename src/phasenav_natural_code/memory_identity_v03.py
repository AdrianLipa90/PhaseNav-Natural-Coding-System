"""Behavioral identity witness for procedural memory representations v0.3.

Memory Ontology permits two manifestations to count as the same underlying
memory when a common history-bearing structure is preserved under an
admissible mapping and equivalent causal constraints on future transitions are
retained.

This module implements only a narrow procedural-memory witness:
- route IDs and node paths must match exactly;
- traversal/provenance counters must match exactly;
- route-choice behavior is compared over every non-empty candidate-route subset
  for small memories (<= 12 routes);
- internal weight coordinates may differ.

This is a contract witness, not a universal ontological identity theorem.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
import math

from .procedural_memory_runtime_v03 import ProceduralMemoryRuntime
from .ternary_stella_v03 import route_choice_stella3

SCHEMA = "PNCS_PROCEDURAL_MEMORY_IDENTITY_WITNESS_V0_3"


class MemoryIdentityError(ValueError):
    pass


@dataclass(frozen=True)
class MemoryIdentityWitness:
    source_memory_id: str
    target_memory_id: str
    route_count: int
    topology_equal: bool
    provenance_counters_equal: bool
    queries_tested: int
    choice_mismatches: int
    mismatch_rate: float
    max_weight_abs_error: float
    epsilon: float
    observable_contract: str = "route_choice"
    distance: str = "exhaustive_subset_choice_mismatch_rate"

    @property
    def behaviorally_equivalent(self) -> bool:
        return (
            self.topology_equal
            and self.provenance_counters_equal
            and self.mismatch_rate <= self.epsilon
        )

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "source_memory_id": self.source_memory_id,
            "target_memory_id": self.target_memory_id,
            "route_count": self.route_count,
            "topology_equal": self.topology_equal,
            "provenance_counters_equal": self.provenance_counters_equal,
            "queries_tested": self.queries_tested,
            "choice_mismatches": self.choice_mismatches,
            "mismatch_rate": self.mismatch_rate,
            "max_weight_abs_error": self.max_weight_abs_error,
            "epsilon": self.epsilon,
            "observable_contract": self.observable_contract,
            "distance": self.distance,
            "behaviorally_equivalent": self.behaviorally_equivalent,
            "internal_coordinate_equality_required": False,
            "universal_identity_claim": False,
        }


def _route_map(runtime: ProceduralMemoryRuntime) -> dict[str, dict]:
    if not isinstance(runtime, ProceduralMemoryRuntime):
        raise MemoryIdentityError("ProceduralMemoryRuntime required")
    return {str(x["route_id"]): x for x in runtime.snapshot()["routes"]}


def compare_procedural_memories(
    source: ProceduralMemoryRuntime,
    target: ProceduralMemoryRuntime,
    *,
    epsilon: float = 0.0,
    max_exact_routes: int = 12,
) -> MemoryIdentityWitness:
    eps = float(epsilon)
    if not math.isfinite(eps) or eps < 0 or eps > 1:
        raise MemoryIdentityError("epsilon must be finite in [0,1]")
    if isinstance(max_exact_routes, bool) or not isinstance(max_exact_routes, int) or max_exact_routes < 1:
        raise MemoryIdentityError("max_exact_routes must be a positive integer")

    a = _route_map(source)
    b = _route_map(target)
    route_ids = tuple(sorted(set(a) | set(b)))
    if len(route_ids) > max_exact_routes:
        raise MemoryIdentityError(
            f"exact subset witness limited to {max_exact_routes} routes; got {len(route_ids)}"
        )

    same_ids = set(a) == set(b)
    topology_equal = same_ids and all(tuple(a[r]["node_path"]) == tuple(b[r]["node_path"]) for r in route_ids)
    provenance_equal = same_ids and all(
        all(a[r][field] == b[r][field] for field in ("traversals", "positive_traces", "negative_traces"))
        for r in route_ids
    )

    max_error = 0.0
    if same_ids:
        max_error = max((abs(float(a[r]["weight"]) - float(b[r]["weight"])) for r in route_ids), default=0.0)

    mismatches = 0
    queries = 0
    if same_ids:
        for size in range(1, len(route_ids) + 1):
            for subset in itertools.combinations(route_ids, size):
                queries += 1
                if source.guide(subset) != target.guide(subset):
                    mismatches += 1
    else:
        queries = 0
        mismatches = 0

    rate = (mismatches / queries) if queries else (0.0 if same_ids else 1.0)
    return MemoryIdentityWitness(
        source_memory_id=source.memory_id,
        target_memory_id=target.memory_id,
        route_count=len(route_ids),
        topology_equal=topology_equal,
        provenance_counters_equal=provenance_equal,
        queries_tested=queries,
        choice_mismatches=mismatches,
        mismatch_rate=rate,
        max_weight_abs_error=max_error,
        epsilon=eps,
    )


def project_runtime_to_stella3(
    runtime: ProceduralMemoryRuntime,
    *,
    scale: float | None = None,
) -> ProceduralMemoryRuntime:
    """Return a Stella-3 coarse projection while preserving topology/provenance."""
    routes = runtime.snapshot()["routes"]
    weights = {str(x["route_id"]): float(x["weight"]) for x in routes}
    _, quantized = route_choice_stella3(weights, scale=scale)
    overrides = {rid: q.reconstructed for rid, q in quantized.items()}
    return runtime.counterfactual(overrides)


__all__ = [
    "SCHEMA",
    "MemoryIdentityError",
    "MemoryIdentityWitness",
    "compare_procedural_memories",
    "project_runtime_to_stella3",
]
