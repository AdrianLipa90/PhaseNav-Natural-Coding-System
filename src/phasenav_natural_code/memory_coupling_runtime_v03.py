"""Inter-layer memory coupling runtime candidate for PNCS v0.3.

Operationalizes a narrow subset of Memory Ontology coupling:
- fast -> slow consolidation transfers only previously-unseen trace deltas;
- slow -> active reactivation returns a route suggestion without mutating target;
- all coupling is deterministic, receipt-bearing, and in-memory only.

This is not a general theory of memory coupling and performs no durable write.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping

from .procedural_memory_runtime_v03 import (
    ProceduralMemoryRuntime,
    ProceduralMemoryRuntimeError,
)

SCHEMA = "PNCS_MEMORY_COUPLING_RUNTIME_V0_3"
RECEIPT_SCHEMA = "PNCS_MEMORY_COUPLING_RECEIPT_V0_3"


class MemoryCouplingRuntimeError(ValueError):
    pass


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise MemoryCouplingRuntimeError(f"{field} must be non-empty")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-")
    if value[0].isdigit() or any(ch not in allowed for ch in value):
        raise MemoryCouplingRuntimeError(f"invalid {field}: {value}")
    return value


def _fraction(value: float) -> float:
    out = float(value)
    if not math.isfinite(out) or out < 0 or out > 1:
        raise MemoryCouplingRuntimeError("transfer_fraction must be finite in [0,1]")
    return out


@dataclass(frozen=True)
class CouplingSpec:
    source_memory: str
    target_memory: str
    mode: str
    timescale: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_memory", _identifier(self.source_memory, "source_memory"))
        object.__setattr__(self, "target_memory", _identifier(self.target_memory, "target_memory"))
        mode = str(self.mode).upper()
        if mode not in {"CONSOLIDATE", "REACTIVATE"}:
            raise MemoryCouplingRuntimeError("v0.3 runtime supports CONSOLIDATE or REACTIVATE")
        object.__setattr__(self, "mode", mode)
        if self.source_memory == self.target_memory:
            raise MemoryCouplingRuntimeError("self-coupling is not admitted")

    @property
    def coupling_id(self) -> str:
        return f"{self.source_memory}->{self.target_memory}:{self.mode.lower()}"


@dataclass(frozen=True)
class CouplingReceipt:
    sequence: int
    coupling_id: str
    mode: str
    source_memory: str
    target_memory: str
    transferred_traces: int
    source_sequence_before: int
    source_sequence_after: int
    source_digest: str
    target_before_digest: str
    target_after_digest: str
    transfer_fraction: float

    def to_dict(self) -> dict:
        return {
            "schema": RECEIPT_SCHEMA,
            "sequence": self.sequence,
            "coupling_id": self.coupling_id,
            "mode": self.mode,
            "source_memory": self.source_memory,
            "target_memory": self.target_memory,
            "transferred_traces": self.transferred_traces,
            "source_sequence_before": self.source_sequence_before,
            "source_sequence_after": self.source_sequence_after,
            "source_digest": self.source_digest,
            "target_before_digest": self.target_before_digest,
            "target_after_digest": self.target_after_digest,
            "transfer_fraction": self.transfer_fraction,
            "durable_write_performed": False,
            "physical_quantum_claim": False,
        }


class MemoryCouplingRuntime:
    def __init__(
        self,
        *,
        runtimes: Mapping[str, ProceduralMemoryRuntime],
        couplings: tuple[CouplingSpec, ...],
    ) -> None:
        if not runtimes:
            raise MemoryCouplingRuntimeError("coupling runtime requires memory runtimes")
        self._runtimes = dict(runtimes)
        for memory_id, runtime in self._runtimes.items():
            _identifier(memory_id, "memory_id")
            if not isinstance(runtime, ProceduralMemoryRuntime):
                raise MemoryCouplingRuntimeError("all runtimes must be ProceduralMemoryRuntime")
            if runtime.memory_id != memory_id:
                raise MemoryCouplingRuntimeError("runtime memory_id mismatch")
        if not couplings:
            raise MemoryCouplingRuntimeError("at least one coupling is required")
        self._couplings: dict[str, CouplingSpec] = {}
        for spec in couplings:
            if not isinstance(spec, CouplingSpec):
                raise MemoryCouplingRuntimeError("couplings must contain CouplingSpec")
            if spec.source_memory not in self._runtimes or spec.target_memory not in self._runtimes:
                raise MemoryCouplingRuntimeError("coupling references missing runtime")
            if spec.coupling_id in self._couplings:
                raise MemoryCouplingRuntimeError(f"duplicate coupling {spec.coupling_id}")
            self._couplings[spec.coupling_id] = spec
        self._cursor = {cid: 0 for cid in self._couplings}
        self._sequence = 0
        self._receipts: list[CouplingReceipt] = []

    @classmethod
    def from_hybrid_ir(
        cls,
        ir: Mapping[str, object],
        *,
        runtimes: Mapping[str, ProceduralMemoryRuntime],
    ) -> "MemoryCouplingRuntime":
        try:
            operations = ir["memory_model"]["operations"]
        except Exception as exc:
            raise MemoryCouplingRuntimeError("missing v0.3 memory_model") from exc
        specs: list[CouplingSpec] = []
        for op in operations:
            if op.get("kind") != "COUPLE":
                continue
            attrs = op.get("attributes", {})
            mode = str(attrs.get("relation", "")).upper()
            if mode not in {"CONSOLIDATE", "REACTIVATE"}:
                continue
            specs.append(
                CouplingSpec(
                    source_memory=attrs["source_memory"],
                    target_memory=attrs["target_memory"],
                    mode=mode,
                    timescale=attrs.get("timescale"),
                )
            )
        if not specs:
            raise MemoryCouplingRuntimeError("hybrid IR has no executable coupling")
        return cls(runtimes=runtimes, couplings=tuple(specs))

    @property
    def receipts(self) -> tuple[CouplingReceipt, ...]:
        return tuple(self._receipts)

    def snapshot(self) -> dict:
        return {
            "schema": SCHEMA,
            "couplings": [
                {
                    "coupling_id": cid,
                    "source_memory": spec.source_memory,
                    "target_memory": spec.target_memory,
                    "mode": spec.mode,
                    "timescale": spec.timescale,
                    "source_cursor": self._cursor[cid],
                }
                for cid, spec in sorted(self._couplings.items())
            ],
            "sequence": self._sequence,
            "durable_persistence": False,
            "physical_quantum_claim": False,
        }

    @property
    def digest(self) -> str:
        return _sha256(self.snapshot())

    def consolidate(self, coupling_id: str, *, transfer_fraction: float = 1.0) -> CouplingReceipt:
        try:
            spec = self._couplings[coupling_id]
        except KeyError as exc:
            raise MemoryCouplingRuntimeError(f"unknown coupling {coupling_id}") from exc
        if spec.mode != "CONSOLIDATE":
            raise MemoryCouplingRuntimeError("consolidate requires CONSOLIDATE coupling")
        fraction = _fraction(transfer_fraction)
        source = self._runtimes[spec.source_memory]
        target = self._runtimes[spec.target_memory]
        source_receipts = source.receipts
        cursor = self._cursor[coupling_id]
        if cursor > len(source_receipts):
            raise MemoryCouplingRuntimeError("source receipt history moved backwards")
        pending = source_receipts[cursor:]
        before = target.digest
        transferred = 0
        for receipt in pending:
            try:
                target.route(receipt.route_id)
            except ProceduralMemoryRuntimeError as exc:
                raise MemoryCouplingRuntimeError(
                    f"target lacks route {receipt.route_id} required for consolidation"
                ) from exc
            if fraction == 0 or receipt.delta_weight == 0:
                transferred += 1
                continue
            magnitude = abs(receipt.delta_weight) * fraction / target.learning_rate
            target.apply_trace(
                receipt.route_id,
                outcome=receipt.outcome,
                magnitude=magnitude,
                event_id=f"consolidate:{receipt.sequence}",
            )
            transferred += 1
        self._cursor[coupling_id] = len(source_receipts)
        after = target.digest
        self._sequence += 1
        out = CouplingReceipt(
            sequence=self._sequence,
            coupling_id=coupling_id,
            mode=spec.mode,
            source_memory=spec.source_memory,
            target_memory=spec.target_memory,
            transferred_traces=transferred,
            source_sequence_before=cursor,
            source_sequence_after=len(source_receipts),
            source_digest=source.digest,
            target_before_digest=before,
            target_after_digest=after,
            transfer_fraction=fraction,
        )
        self._receipts.append(out)
        return out

    def reactivate(self, coupling_id: str, *, candidate_route_ids=None) -> str:
        try:
            spec = self._couplings[coupling_id]
        except KeyError as exc:
            raise MemoryCouplingRuntimeError(f"unknown coupling {coupling_id}") from exc
        if spec.mode != "REACTIVATE":
            raise MemoryCouplingRuntimeError("reactivate requires REACTIVATE coupling")
        source = self._runtimes[spec.source_memory]
        route_id = source.guide(candidate_route_ids)
        target = self._runtimes[spec.target_memory]
        try:
            target.route(route_id)
        except ProceduralMemoryRuntimeError as exc:
            raise MemoryCouplingRuntimeError(
                f"target cannot accept reactivated route {route_id}"
            ) from exc
        return route_id
