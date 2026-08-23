from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

from .runtime_v25_core import (
    DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT, V20_EXECUTION_CONTRACT_ID, V20_EXECUTION_SCHEMA,
    V22_LINEAGE_CONTRACT_ID, LiveRuntimeGeneration, PersistentRuntimeV25Error,
    _BUILD_RE, _COMPOSITION_RE, _DEFINITION_RE, _LINEAGE_RE, _PROGRAM_RE, _RESULT_RE,
    _digest, _load_json, _sha256_json, _typed, _typed_id, read_live_generation,
)
from .runtime_v25_program import ProgramImage, program_image_from_artifacts
from .runtime_v25_resident_model import (
    ResidentAdmission, ResidentDispatchReceipt, ResidentLoadReceipt, ResidentProgramHandle,
    ResidentUnloadReceipt, _atomic_write, _handle_digest, _immutable_write, _json_bytes,
)

class PersistentProgramRuntime:
    def __init__(
        self,
        surface_root: Path | str = DEFAULT_SURFACE_ROOT,
        *,
        socket_path: Path | str = DEFAULT_SOCKET,
        max_heartbeat_age_s: float = 2.0,
        require_socket: bool = True,
        require_canonical_root: bool = True,
    ) -> None:
        self.root = Path(surface_root)
        self.socket_path = Path(socket_path)
        self.max_heartbeat_age_s = max_heartbeat_age_s
        self.require_socket = require_socket
        self.require_canonical_root = require_canonical_root
        if require_canonical_root and self.root != DEFAULT_SURFACE_ROOT:
            raise PersistentRuntimeV25Error("v0.25 operational runtime is fixed to /dev/shm/ciel_noema")
        self.runtime_root = self.root / "pncs/v0.25/runtime"

    def generation(self) -> LiveRuntimeGeneration:
        return read_live_generation(
            self.root,
            socket_path=self.socket_path,
            max_heartbeat_age_s=self.max_heartbeat_age_s,
            require_socket=self.require_socket,
            require_canonical_root=self.require_canonical_root,
        )

    def load(self, image: ProgramImage) -> tuple[ResidentProgramHandle, ResidentLoadReceipt]:
        if not isinstance(image, ProgramImage):
            raise PersistentRuntimeV25Error("ProgramImage required")
        generation = self.generation()
        handle = ResidentProgramHandle(image, generation)
        digest = _handle_digest(handle.handle_id)
        program_path = self.runtime_root / "programs" / f"{image.program_id.rsplit(':', 1)[-1]}.pnv"
        handle_path = self.runtime_root / "handles" / f"{digest}.json"
        active_path = self.runtime_root / "active" / f"{digest}.json"
        load_receipt = ResidentLoadReceipt(handle)
        load_path = self.runtime_root / "receipts/load" / f"{load_receipt.receipt_id.rsplit(':', 1)[-1]}.json"

        _immutable_write(program_path, image.pnv_bytes)
        _immutable_write(handle_path, _json_bytes({**handle.payload, "handle_id": handle.handle_id}))
        _immutable_write(load_path, _json_bytes({**load_receipt.payload, "receipt_id": load_receipt.receipt_id}))
        _atomic_write(active_path, _json_bytes({
            "schema": "PNCS_RESIDENT_ACTIVE_POINTER_V0_25",
            "handle_id": handle.handle_id,
            "program_id": image.program_id,
            "generation_id": generation.generation_id,
        }))
        return handle, load_receipt

    def load_from_artifacts(
        self,
        program_path: Path | str,
        build_receipt_path: Path | str,
        *,
        expected_program_id: str,
    ) -> tuple[ResidentProgramHandle, ResidentLoadReceipt]:
        image = program_image_from_artifacts(
            program_path,
            build_receipt_path,
            expected_program_id=expected_program_id,
        )
        return self.load(image)

    def _read_handle(self, handle_id: str) -> ResidentProgramHandle:
        digest = _handle_digest(handle_id)
        path = self.runtime_root / "handles" / f"{digest}.json"
        record = _load_json(path, "resident handle")
        if record.get("handle_id") != handle_id:
            raise PersistentRuntimeV25Error("resident handle file identity mismatch")
        generation_raw = record.get("generation")
        if not isinstance(generation_raw, Mapping):
            raise PersistentRuntimeV25Error("resident handle lacks generation payload")
        generation = LiveRuntimeGeneration(
            root=str(generation_raw.get("root", "")),
            socket_path=str(generation_raw.get("socket_path", "")),
            account_current=str(generation_raw.get("account_current", "")),
            current_pointer_sha256=str(generation_raw.get("current_pointer_sha256", "")),
            startpoint_packet_sha256=str(generation_raw.get("startpoint_packet_sha256", "")),
            ac_current_sha256=str(generation_raw.get("ac_current_sha256", "")),
            ethics_field_sha256=str(generation_raw.get("ethics_field_sha256", "")),
            operator_registry_sha256=str(generation_raw.get("operator_registry_sha256", "")),
            aux_pid=int(generation_raw.get("aux_pid", -1)),
            tether_pid=int(generation_raw.get("tether_pid", -1)),
            ac_aux_pid=int(generation_raw.get("ac_aux_pid", -1)),
        )
        program_id = _typed(record.get("program_id"), _PROGRAM_RE, "program_id")
        program_path = self.runtime_root / "programs" / f"{program_id.rsplit(':', 1)[-1]}.pnv"
        try:
            raw = program_path.read_bytes()
        except OSError as exc:
            raise PersistentRuntimeV25Error("resident program bytes unavailable") from exc
        image = ProgramImage(
            program_id=program_id,
            composition_id=_typed(record.get("composition_id"), _COMPOSITION_RE, "composition_id"),
            build_id=_typed(record.get("build_id"), _BUILD_RE, "build_id"),
            pnv_sha256=_digest(record.get("pnv_sha256"), "pnv_sha256"),
            pnv_size_bytes=len(raw),
            operator_schedule_sha256=_digest(record.get("operator_schedule_sha256"), "operator_schedule_sha256"),
            control_definition_id=_typed(record.get("control_definition_id"), _DEFINITION_RE, "control_definition_id"),
            lineage_contract_id=str(record.get("required_result_lineage_contract_id", "")),
            pnv_bytes=raw,
        )
        if record.get("program_image_id") != image.image_id:
            raise PersistentRuntimeV25Error("resident handle program image identity mismatch")
        handle = ResidentProgramHandle(image, generation)
        if handle.handle_id != handle_id:
            raise PersistentRuntimeV25Error("resident handle digest mismatch")
        return handle

    def admit(self, handle_id: str) -> ResidentAdmission:
        handle = self._read_handle(handle_id)
        digest = _handle_digest(handle_id)
        active = _load_json(self.runtime_root / "active" / f"{digest}.json", "resident active pointer")
        if active.get("handle_id") != handle_id or active.get("generation_id") != handle.generation.generation_id:
            raise PersistentRuntimeV25Error("resident handle is not active")
        current = self.generation()
        if current.generation_id != handle.generation.generation_id:
            raise PersistentRuntimeV25Error("resident handle is stale for current live runtime generation")
        if current.payload != handle.generation.payload:
            raise PersistentRuntimeV25Error("resident generation payload mismatch")
        return ResidentAdmission(handle)

    def unload(self, handle_id: str) -> ResidentUnloadReceipt:
        admission = self.admit(handle_id)
        handle = admission.handle
        digest = _handle_digest(handle_id)
        active_path = self.runtime_root / "active" / f"{digest}.json"
        try:
            active_path.unlink()
        except FileNotFoundError as exc:
            raise PersistentRuntimeV25Error("resident handle already unloaded") from exc
        receipt = ResidentUnloadReceipt(handle)
        path = self.runtime_root / "receipts/unload" / f"{receipt.receipt_id.rsplit(':', 1)[-1]}.json"
        _immutable_write(path, _json_bytes({**receipt.payload, "receipt_id": receipt.receipt_id}))
        return receipt

    def dispatch_control(
        self,
        handle_id: str,
        kernel: Callable[[], tuple[object, object]],
    ) -> ResidentDispatchReceipt:
        if not callable(kernel):
            raise PersistentRuntimeV25Error("in-process v0.20/v0.22 kernel callback required")
        before = self.admit(handle_id)
        result, lineage = kernel()
        after = self.admit(handle_id)
        if before.handle.generation.generation_id != after.handle.generation.generation_id:
            raise PersistentRuntimeV25Error("live generation changed during resident dispatch")
        execution_sha, target, truth = _validate_execution_result(
            result,
            before.handle.image.control_definition_id,
            expected_root=str(self.root),
        )
        result_id, lineage_id = _validate_lineage(
            lineage,
            execution_sha,
            before.handle.image.control_definition_id,
        )
        receipt = ResidentDispatchReceipt(
            handle_id=handle_id,
            program_id=before.handle.image.program_id,
            generation_id=before.handle.generation.generation_id,
            resident_admission_id=before.admission_id,
            execution_receipt_sha256=execution_sha,
            result_id=result_id,
            lineage_id=lineage_id,
            target=target,
            branch_truth_state=truth,
        )
        path = self.runtime_root / "receipts/dispatch" / f"{receipt.dispatch_id.rsplit(':', 1)[-1]}.json"
        _immutable_write(path, _json_bytes({**receipt.payload, "dispatch_id": receipt.dispatch_id}))
        return receipt


def _validate_execution_result(result: object, control_definition_id: str, *, expected_root: str) -> tuple[str, str, str]:
    receipt = getattr(result, "receipt", None)
    if not isinstance(receipt, Mapping):
        raise PersistentRuntimeV25Error("NativeExecutionResult-compatible object required")
    if receipt.get("schema") != V20_EXECUTION_SCHEMA or receipt.get("execution_contract_id") != V20_EXECUTION_CONTRACT_ID:
        raise PersistentRuntimeV25Error("resident dispatch requires exact v0.20 execution receipt")
    execution_sha = _digest(receipt.get("receipt_sha256"), "execution receipt SHA")
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    if _sha256_json(body) != execution_sha:
        raise PersistentRuntimeV25Error("v0.20 execution receipt digest mismatch")
    program = receipt.get("program")
    if not isinstance(program, Mapping) or program.get("content_id") != control_definition_id:
        raise PersistentRuntimeV25Error("resident program/control Definition mismatch")
    live = receipt.get("live_surface")
    if not isinstance(live, Mapping) or live.get("root") != expected_root:
        raise PersistentRuntimeV25Error("v0.20 execution escaped resident live surface")
    if receipt.get("external_effects") is not False or receipt.get("free_form_nl_execution") is not False:
        raise PersistentRuntimeV25Error("v0.20 result crossed closed authority boundary")
    result_payload = receipt.get("result")
    if not isinstance(result_payload, Mapping) or result_payload.get("kind") != "INTERNAL_TRANSFORM":
        raise PersistentRuntimeV25Error("resident kernel result is not INTERNAL_TRANSFORM")
    target = str(result_payload.get("control_location", ""))
    admission = receipt.get("admission")
    truth = str(admission.get("branch_truth_state", "")) if isinstance(admission, Mapping) else ""
    if getattr(result, "target", None) != target or getattr(result, "branch_truth_state", None) != truth:
        raise PersistentRuntimeV25Error("v0.20 result object/receipt mismatch")
    if truth not in {"TRUE", "FALSE"} or not target:
        raise PersistentRuntimeV25Error("invalid v0.20 resident control result")
    return execution_sha, target, truth


def _validate_lineage(lineage: object, execution_sha: str, control_definition_id: str) -> tuple[str, str]:
    payload = getattr(lineage, "payload", None)
    if not isinstance(payload, Mapping):
        raise PersistentRuntimeV25Error("ExactInverseLineage-compatible object required")
    if payload.get("schema") != "PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22" or payload.get("lineage_contract_id") != V22_LINEAGE_CONTRACT_ID:
        raise PersistentRuntimeV25Error("resident dispatch requires exact v0.22 inverse lineage")
    if payload.get("execution_receipt_sha256") != execution_sha:
        raise PersistentRuntimeV25Error("v0.22 lineage does not bind resident execution receipt")
    result_id = _typed(getattr(lineage, "result_id", None), _RESULT_RE, "result_id")
    if payload.get("result_id") != result_id:
        raise PersistentRuntimeV25Error("v0.22 lineage result ID mismatch")
    lineage_id = _typed(getattr(lineage, "lineage_id", None), _LINEAGE_RE, "lineage_id")
    if _typed_id("pncs:lineage", payload) != lineage_id:
        raise PersistentRuntimeV25Error("v0.22 lineage digest mismatch")
    hierarchy = getattr(lineage, "hierarchy", None)
    definition_id = getattr(hierarchy, "definition_id", None)
    if definition_id != control_definition_id:
        raise PersistentRuntimeV25Error("v0.22 lineage Definition differs from resident control Definition")
    receipt = getattr(lineage, "receipt", None)
    if not isinstance(receipt, Mapping) or receipt.get("lineage_id") != lineage_id:
        raise PersistentRuntimeV25Error("v0.22 lineage receipt identity mismatch")
    return result_id, lineage_id
