"""Content-addressed checkpoint codec for PNCS procedural memory v0.3.

A checkpoint is a representation of memory state, not the ontology of memory
itself. This module serializes/restores state and provenance but performs no
durable write. Persistence to external storage remains an explicit capability
boundary handled by PNCS PERSIST.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping

from .procedural_memory_runtime_v03 import (
    ProceduralMemoryRuntime,
    ProceduralMemoryRuntimeError,
    RouteState,
    UpdateReceipt,
    SCHEMA as RUNTIME_SCHEMA,
    RECEIPT_SCHEMA,
)

CHECKPOINT_SCHEMA = "PNCS_PROCEDURAL_MEMORY_CHECKPOINT_V0_3"


class MemoryCheckpointError(ValueError):
    pass


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class CheckpointEnvelope:
    raw: bytes
    sha256: str
    memory_id: str
    state_digest: str
    receipt_count: int

    def to_dict(self) -> dict:
        return {
            "schema": CHECKPOINT_SCHEMA,
            "sha256": self.sha256,
            "memory_id": self.memory_id,
            "state_digest": self.state_digest,
            "receipt_count": self.receipt_count,
            "durable_write_performed": False,
            "physical_quantum_claim": False,
        }


def export_checkpoint(runtime: ProceduralMemoryRuntime) -> CheckpointEnvelope:
    if not isinstance(runtime, ProceduralMemoryRuntime):
        raise MemoryCheckpointError("ProceduralMemoryRuntime required")
    snapshot = runtime.snapshot()
    receipts = [receipt.to_dict() for receipt in runtime.receipts]
    payload = {
        "schema": CHECKPOINT_SCHEMA,
        "runtime_schema": RUNTIME_SCHEMA,
        "memory_id": runtime.memory_id,
        "state_digest": runtime.digest,
        "runtime_snapshot": snapshot,
        "receipts": receipts,
        "receipt_count": len(receipts),
        "representation_role": "STATE_AND_PROVENANCE_CHECKPOINT",
        "durable_write_performed": False,
        "physical_quantum_claim": False,
    }
    raw = _canonical_json(payload)
    return CheckpointEnvelope(
        raw=raw,
        sha256=_sha256_bytes(raw),
        memory_id=runtime.memory_id,
        state_digest=runtime.digest,
        receipt_count=len(receipts),
    )


def _expect_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise MemoryCheckpointError(f"{field} must be an object")
    return value


def restore_checkpoint(raw: bytes | bytearray) -> ProceduralMemoryRuntime:
    if not isinstance(raw, (bytes, bytearray)):
        raise MemoryCheckpointError("checkpoint must be bytes")
    try:
        payload = json.loads(bytes(raw).decode("utf-8"))
    except Exception as exc:
        raise MemoryCheckpointError("invalid checkpoint JSON") from exc
    payload = _expect_mapping(payload, "checkpoint")

    if payload.get("schema") != CHECKPOINT_SCHEMA:
        raise MemoryCheckpointError("unsupported checkpoint schema")
    if payload.get("runtime_schema") != RUNTIME_SCHEMA:
        raise MemoryCheckpointError("runtime schema mismatch")
    if payload.get("durable_write_performed") is not False:
        raise MemoryCheckpointError("checkpoint cannot claim an implicit durable write")
    if payload.get("physical_quantum_claim") is not False:
        raise MemoryCheckpointError("checkpoint cannot claim a physical quantum substrate")

    snap = _expect_mapping(payload.get("runtime_snapshot"), "runtime_snapshot")
    if snap.get("schema") != RUNTIME_SCHEMA:
        raise MemoryCheckpointError("embedded runtime snapshot schema mismatch")
    memory_id = payload.get("memory_id")
    if snap.get("memory_id") != memory_id:
        raise MemoryCheckpointError("memory_id mismatch")
    if snap.get("durable_persistence") is not False:
        raise MemoryCheckpointError("runtime snapshot has invalid persistence authority")
    if snap.get("physical_quantum_claim") is not False:
        raise MemoryCheckpointError("runtime snapshot has invalid physical claim")

    routes_raw = snap.get("routes")
    if not isinstance(routes_raw, list) or not routes_raw:
        raise MemoryCheckpointError("checkpoint has no routes")
    routes = []
    try:
        for item in routes_raw:
            item = _expect_mapping(item, "route")
            routes.append(
                RouteState(
                    route_id=item["route_id"],
                    node_path=tuple(item["node_path"]),
                    weight=item["weight"],
                    traversals=int(item["traversals"]),
                    positive_traces=int(item["positive_traces"]),
                    negative_traces=int(item["negative_traces"]),
                )
            )
        runtime = ProceduralMemoryRuntime(
            str(memory_id),
            routes,
            learning_rate=float(snap["learning_rate"]),
        )
        runtime._sequence = int(snap["sequence"])
    except (KeyError, TypeError, ValueError, ProceduralMemoryRuntimeError) as exc:
        raise MemoryCheckpointError("invalid runtime state") from exc

    if runtime.digest != payload.get("state_digest"):
        raise MemoryCheckpointError("state digest mismatch")

    receipts_raw = payload.get("receipts")
    if not isinstance(receipts_raw, list):
        raise MemoryCheckpointError("receipts must be a list")
    if int(payload.get("receipt_count", -1)) != len(receipts_raw):
        raise MemoryCheckpointError("receipt_count mismatch")

    restored_receipts: list[UpdateReceipt] = []
    previous_after = None
    for index, item in enumerate(receipts_raw, start=1):
        item = _expect_mapping(item, "receipt")
        if item.get("schema") != RECEIPT_SCHEMA:
            raise MemoryCheckpointError("receipt schema mismatch")
        if item.get("memory_id") != memory_id:
            raise MemoryCheckpointError("receipt memory_id mismatch")
        if int(item.get("sequence", -1)) != index:
            raise MemoryCheckpointError("receipt sequence is not append-only")
        before = item.get("before_digest")
        after = item.get("after_digest")
        if previous_after is not None and before != previous_after:
            raise MemoryCheckpointError("receipt digest chain is broken")
        previous_after = after
        try:
            restored_receipts.append(
                UpdateReceipt(
                    memory_id=str(memory_id),
                    sequence=index,
                    route_id=str(item["route_id"]),
                    outcome=str(item["outcome"]),
                    magnitude=float(item["magnitude"]),
                    delta_weight=float(item["delta_weight"]),
                    before_digest=str(before),
                    after_digest=str(after),
                    event_id=item.get("event_id"),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise MemoryCheckpointError("invalid receipt") from exc

    if restored_receipts:
        if restored_receipts[-1].after_digest != runtime.digest:
            raise MemoryCheckpointError("last receipt does not bind current memory state")
        if runtime._sequence != len(restored_receipts):
            raise MemoryCheckpointError("runtime sequence and receipt count diverge")
    elif runtime._sequence != 0:
        raise MemoryCheckpointError("nonzero sequence without receipts")

    runtime._receipts = restored_receipts
    return runtime
