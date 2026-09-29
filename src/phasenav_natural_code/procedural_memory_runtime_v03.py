
"""Procedural-memory runtime candidate for PNCS Hybrid Memory Grammar v0.3.

Implements a minimal substrate-neutral history-bearing route memory:
history -> trace -> route-weight update -> changed future routing.

This is an in-memory candidate runtime. It performs no durable persistence and
makes no quantum-substrate claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import json
import math
from typing import Iterable, Mapping

SCHEMA = "PNCS_PROCEDURAL_MEMORY_RUNTIME_V0_3"
RECEIPT_SCHEMA = "PNCS_MEMORY_UPDATE_RECEIPT_V0_3"


class ProceduralMemoryRuntimeError(ValueError):
    pass


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProceduralMemoryRuntimeError(f"{field} must be non-empty")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-")
    if value[0].isdigit() or any(ch not in allowed for ch in value):
        raise ProceduralMemoryRuntimeError(f"invalid {field}: {value}")
    return value


def _finite(value: float, field: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ProceduralMemoryRuntimeError(f"{field} must be finite")
    return out


@dataclass
class RouteState:
    route_id: str
    node_path: tuple[str, ...]
    weight: float = 0.0
    traversals: int = 0
    positive_traces: int = 0
    negative_traces: int = 0

    def __post_init__(self) -> None:
        self.route_id = _identifier(self.route_id, "route_id")
        self.node_path = tuple(_identifier(x, "route node") for x in self.node_path)
        if len(self.node_path) < 2:
            raise ProceduralMemoryRuntimeError("route needs at least two nodes")
        self.weight = _finite(self.weight, "weight")
        if min(self.traversals, self.positive_traces, self.negative_traces) < 0:
            raise ProceduralMemoryRuntimeError("route counters cannot be negative")

    def to_dict(self) -> dict:
        return {
            "route_id": self.route_id,
            "node_path": list(self.node_path),
            "weight": self.weight,
            "traversals": self.traversals,
            "positive_traces": self.positive_traces,
            "negative_traces": self.negative_traces,
        }


@dataclass(frozen=True)
class UpdateReceipt:
    memory_id: str
    sequence: int
    route_id: str
    outcome: str
    magnitude: float
    delta_weight: float
    before_digest: str
    after_digest: str
    event_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "schema": RECEIPT_SCHEMA,
            "memory_id": self.memory_id,
            "sequence": self.sequence,
            "route_id": self.route_id,
            "outcome": self.outcome,
            "magnitude": self.magnitude,
            "delta_weight": self.delta_weight,
            "before_digest": self.before_digest,
            "after_digest": self.after_digest,
            "event_id": self.event_id,
            "durable_write_performed": False,
            "physical_quantum_claim": False,
        }


class ProceduralMemoryRuntime:
    """Minimal path/topology memory with deterministic route guidance."""

    def __init__(
        self,
        memory_id: str,
        routes: Iterable[RouteState],
        *,
        learning_rate: float = 0.1,
    ) -> None:
        self.memory_id = _identifier(memory_id, "memory_id")
        self.learning_rate = _finite(learning_rate, "learning_rate")
        if self.learning_rate <= 0:
            raise ProceduralMemoryRuntimeError("learning_rate must be positive")
        self._routes: dict[str, RouteState] = {}
        for route in routes:
            if not isinstance(route, RouteState):
                raise ProceduralMemoryRuntimeError("routes must contain RouteState")
            if route.route_id in self._routes:
                raise ProceduralMemoryRuntimeError(f"duplicate route {route.route_id}")
            self._routes[route.route_id] = copy.deepcopy(route)
        if not self._routes:
            raise ProceduralMemoryRuntimeError("runtime requires at least one route")
        self._sequence = 0
        self._receipts: list[UpdateReceipt] = []

    @classmethod
    def from_hybrid_ir(
        cls,
        ir: Mapping[str, object],
        memory_id: str,
        *,
        learning_rate: float = 0.1,
    ) -> "ProceduralMemoryRuntime":
        try:
            model = ir["memory_model"]
            objects = model["objects"]
            operations = model["operations"]
        except Exception as exc:
            raise ProceduralMemoryRuntimeError("missing v0.3 memory_model") from exc

        obj = next((x for x in objects if x.get("memory_id") == memory_id), None)
        if obj is None:
            raise ProceduralMemoryRuntimeError(f"unknown memory object {memory_id}")
        retained = set(obj.get("retained_objects", []))
        if "path" not in retained:
            raise ProceduralMemoryRuntimeError("procedural runtime requires PATH retention")

        paths: dict[str, tuple[str, ...]] = {}
        admitted: set[str] = set()
        for op in operations:
            kind = op.get("kind")
            attrs = op.get("attributes", {})
            if kind == "PATH":
                paths[attrs["route_id"]] = tuple(attrs["node_path"])
            elif kind == "REINFORCE" and attrs.get("memory_id") == memory_id:
                admitted.add(attrs["route_id"])

        missing = sorted(admitted - set(paths))
        if missing:
            raise ProceduralMemoryRuntimeError(
                f"reinforcement references missing path(s): {missing}"
            )
        if not admitted:
            raise ProceduralMemoryRuntimeError(
                "memory has no reinforced/admitted procedural routes"
            )
        routes = [RouteState(route_id, paths[route_id]) for route_id in sorted(admitted)]
        return cls(memory_id, routes, learning_rate=learning_rate)

    def snapshot(self) -> dict:
        return {
            "schema": SCHEMA,
            "memory_id": self.memory_id,
            "learning_rate": self.learning_rate,
            "sequence": self._sequence,
            "routes": [
                self._routes[key].to_dict() for key in sorted(self._routes)
            ],
            "durable_persistence": False,
            "physical_quantum_claim": False,
        }

    @property
    def digest(self) -> str:
        return _sha256(self.snapshot())

    @property
    def receipts(self) -> tuple[UpdateReceipt, ...]:
        return tuple(self._receipts)

    def route(self, route_id: str) -> RouteState:
        try:
            return copy.deepcopy(self._routes[route_id])
        except KeyError as exc:
            raise ProceduralMemoryRuntimeError(f"unknown route {route_id}") from exc

    def apply_trace(
        self,
        route_id: str,
        *,
        outcome: str,
        magnitude: float = 1.0,
        event_id: str | None = None,
    ) -> UpdateReceipt:
        try:
            route = self._routes[route_id]
        except KeyError as exc:
            raise ProceduralMemoryRuntimeError(f"unknown route {route_id}") from exc

        outcome_u = str(outcome).upper()
        if outcome_u not in {"POSITIVE", "NEGATIVE"}:
            raise ProceduralMemoryRuntimeError("outcome must be POSITIVE or NEGATIVE")
        mag = _finite(magnitude, "magnitude")
        if mag < 0:
            raise ProceduralMemoryRuntimeError("magnitude must be non-negative")
        if event_id is not None:
            event_id = _identifier(event_id, "event_id")

        before = self.digest
        sign = 1.0 if outcome_u == "POSITIVE" else -1.0
        delta = self.learning_rate * mag * sign

        route.weight = _finite(route.weight + delta, "updated weight")
        route.traversals += 1
        if outcome_u == "POSITIVE":
            route.positive_traces += 1
        else:
            route.negative_traces += 1

        self._sequence += 1
        after = self.digest
        receipt = UpdateReceipt(
            memory_id=self.memory_id,
            sequence=self._sequence,
            route_id=route_id,
            outcome=outcome_u,
            magnitude=mag,
            delta_weight=delta,
            before_digest=before,
            after_digest=after,
            event_id=event_id,
        )
        self._receipts.append(receipt)
        return receipt

    def guide(self, candidate_route_ids: Iterable[str] | None = None) -> str:
        if candidate_route_ids is None:
            ids = tuple(sorted(self._routes))
        else:
            ids = tuple(candidate_route_ids)
            if not ids:
                raise ProceduralMemoryRuntimeError("candidate route set cannot be empty")
            unknown = [x for x in ids if x not in self._routes]
            if unknown:
                raise ProceduralMemoryRuntimeError(
                    f"unknown candidate route(s): {unknown}"
                )

        # Deterministic: greatest weight, then route id for stable tie-break.
        return min(ids, key=lambda rid: (-self._routes[rid].weight, rid))

    def counterfactual(
        self,
        weight_overrides: Mapping[str, float],
    ) -> "ProceduralMemoryRuntime":
        """Return an intervention clone without mutating the factual memory."""
        clone = copy.deepcopy(self)
        clone._receipts = list(self._receipts)
        for route_id, weight in weight_overrides.items():
            if route_id not in clone._routes:
                raise ProceduralMemoryRuntimeError(f"unknown route {route_id}")
            clone._routes[route_id].weight = _finite(weight, "intervention weight")
        return clone
