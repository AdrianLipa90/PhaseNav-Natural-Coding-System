from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable, Mapping

from .runtime_v25_core import (
    ADMISSION_SCHEMA, DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT, DISPATCH_RECEIPT_SCHEMA,
    HANDLE_SCHEMA, LOAD_RECEIPT_SCHEMA, RUNTIME_CONTRACT_ID, UNLOAD_RECEIPT_SCHEMA,
    V20_EXECUTION_CONTRACT_ID, V20_EXECUTION_SCHEMA, V22_LINEAGE_CONTRACT_ID,
    LiveRuntimeGeneration, PersistentRuntimeV25Error, _BUILD_RE, _COMPOSITION_RE, _DEFINITION_RE, _HANDLE_RE, _LINEAGE_RE,
    _PROGRAM_RE, _RESULT_RE, _compact_json, _digest, _load_json, _sha256_json,
    _typed, _typed_id, read_live_generation,
)
from .runtime_v25_program import ProgramImage, program_image_from_artifacts

@dataclass(frozen=True)
class ResidentProgramHandle:
    image: ProgramImage
    generation: LiveRuntimeGeneration

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": HANDLE_SCHEMA,
            "runtime_contract_id": RUNTIME_CONTRACT_ID,
            "program_image_id": self.image.image_id,
            "program_id": self.image.program_id,
            "composition_id": self.image.composition_id,
            "build_id": self.image.build_id,
            "pnv_sha256": self.image.pnv_sha256,
            "operator_schedule_sha256": self.image.operator_schedule_sha256,
            "control_definition_id": self.image.control_definition_id,
            "required_result_lineage_contract_id": self.image.lineage_contract_id,
            "generation_id": self.generation.generation_id,
            "generation": self.generation.payload,
            "persistent_runtime_state": True,
            "external_effects": False,
            "continuation_execution_opened": False,
            "return_execution_opened": False,
            "static_runtime_fallback": False,
        }

    @property
    def handle_id(self) -> str:
        return _typed_id("pncs:resident", self.payload)


@dataclass(frozen=True)
class ResidentLoadReceipt:
    handle: ResidentProgramHandle

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": LOAD_RECEIPT_SCHEMA,
            "runtime_contract_id": RUNTIME_CONTRACT_ID,
            "action": "LOAD",
            "handle_id": self.handle.handle_id,
            "program_id": self.handle.image.program_id,
            "build_id": self.handle.image.build_id,
            "generation_id": self.handle.generation.generation_id,
            "resident_program_sha256": self.handle.image.pnv_sha256,
            "idempotent_same_generation_load": True,
            "process_reconstruction_required": False,
            "static_runtime_fallback": False,
            "deterministic_fields_only": True,
        }

    @property
    def receipt_id(self) -> str:
        return _typed_id("pncs:resident-load", self.payload)


@dataclass(frozen=True)
class ResidentAdmission:
    handle: ResidentProgramHandle

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": ADMISSION_SCHEMA,
            "runtime_contract_id": RUNTIME_CONTRACT_ID,
            "handle_id": self.handle.handle_id,
            "program_id": self.handle.image.program_id,
            "generation_id": self.handle.generation.generation_id,
            "scope": "CONTROL_ROOT_V0_20_ONLY",
            "continuation_execution_opened": False,
            "return_execution_opened": False,
            "external_effects": False,
            "static_runtime_fallback": False,
        }

    @property
    def admission_id(self) -> str:
        return _typed_id("pncs:resident-admission", self.payload)


@dataclass(frozen=True)
class ResidentDispatchReceipt:
    handle_id: str
    program_id: str
    generation_id: str
    resident_admission_id: str
    execution_receipt_sha256: str
    result_id: str
    lineage_id: str
    target: str
    branch_truth_state: str

    def __post_init__(self) -> None:
        _typed(self.handle_id, _HANDLE_RE, "handle_id")
        _typed(self.program_id, _PROGRAM_RE, "program_id")
        if not isinstance(self.generation_id, str) or not self.generation_id.startswith("pncs:runtime-generation:sha256:"):
            raise PersistentRuntimeV25Error("invalid generation_id")
        if not isinstance(self.resident_admission_id, str) or not self.resident_admission_id.startswith("pncs:resident-admission:sha256:"):
            raise PersistentRuntimeV25Error("invalid resident_admission_id")
        _digest(self.execution_receipt_sha256, "execution_receipt_sha256")
        _typed(self.result_id, _RESULT_RE, "result_id")
        _typed(self.lineage_id, _LINEAGE_RE, "lineage_id")
        if not self.target or self.branch_truth_state not in {"TRUE", "FALSE"}:
            raise PersistentRuntimeV25Error("invalid control dispatch result")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": DISPATCH_RECEIPT_SCHEMA,
            "runtime_contract_id": RUNTIME_CONTRACT_ID,
            "kernel_scope": "CONTROL_ROOT_V0_20",
            "handle_id": self.handle_id,
            "program_id": self.program_id,
            "generation_id": self.generation_id,
            "resident_admission_id": self.resident_admission_id,
            "execution_receipt_sha256": self.execution_receipt_sha256,
            "result_id": self.result_id,
            "lineage_id": self.lineage_id,
            "target": self.target,
            "branch_truth_state": self.branch_truth_state,
            "result_lineage_contract_id": V22_LINEAGE_CONTRACT_ID,
            "process_reconstruction_required": False,
            "continuation_execution_opened": False,
            "return_execution_opened": False,
            "external_effects": False,
            "static_runtime_fallback": False,
            "deterministic_fields_only": True,
        }

    @property
    def dispatch_id(self) -> str:
        return _typed_id("pncs:resident-dispatch", self.payload)


@dataclass(frozen=True)
class ResidentUnloadReceipt:
    handle: ResidentProgramHandle

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": UNLOAD_RECEIPT_SCHEMA,
            "runtime_contract_id": RUNTIME_CONTRACT_ID,
            "action": "UNLOAD",
            "handle_id": self.handle.handle_id,
            "program_id": self.handle.image.program_id,
            "generation_id": self.handle.generation.generation_id,
            "immutable_handle_record_retained": True,
            "active_pointer_removed": True,
            "external_effects": False,
            "static_runtime_fallback": False,
            "deterministic_fields_only": True,
        }

    @property
    def receipt_id(self) -> str:
        return _typed_id("pncs:resident-unload", self.payload)


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with tmp.open("wb") as fh:
        fh.write(raw)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _immutable_write(path: Path, raw: bytes) -> None:
    if path.exists():
        try:
            prior = path.read_bytes()
        except OSError as exc:
            raise PersistentRuntimeV25Error(f"cannot verify existing immutable runtime artifact: {path}") from exc
        if prior != raw:
            raise PersistentRuntimeV25Error(f"immutable runtime artifact collision: {path}")
        return
    _atomic_write(path, raw)


def _json_bytes(value: Mapping[str, object]) -> bytes:
    return (_compact_json(dict(value)) + "\n").encode("utf-8")


def _handle_digest(handle_id: str) -> str:
    _typed(handle_id, _HANDLE_RE, "handle_id")
    return handle_id.rsplit(":", 1)[-1]

