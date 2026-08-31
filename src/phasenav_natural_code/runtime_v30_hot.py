from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Callable, Mapping

from .runtime_v25_core import (
    DEFAULT_SURFACE_ROOT,
    PersistentRuntimeV25Error,
    _active_status,
    _load_json,
    _socket_check,
    _typed_id,
)
from .runtime_v25_resident import (
    PersistentProgramRuntime,
    _validate_execution_result,
    _validate_lineage,
)
from .runtime_v25_resident_model import (
    ResidentAdmission,
    ResidentDispatchReceipt,
    _handle_digest,
    _immutable_write,
    _json_bytes,
)

HOTPATH_CONTRACT_ID = "PNCS_RESIDENT_HOTPATH_V0_30"
HOT_TOKEN_SCHEMA = "PNCS_RESIDENT_HOT_ADMISSION_TOKEN_V0_30"


@dataclass(frozen=True)
class FileStamp:
    dev: int
    ino: int
    size: int
    mtime_ns: int
    ctime_ns: int

    @classmethod
    def read(cls, path: Path) -> "FileStamp":
        try:
            st = path.stat()
        except OSError as exc:
            raise PersistentRuntimeV25Error(f"hotpath required file unavailable: {path}") from exc
        if not path.is_file():
            raise PersistentRuntimeV25Error(f"hotpath required path is not regular file: {path}")
        return cls(
            dev=int(st.st_dev),
            ino=int(st.st_ino),
            size=int(st.st_size),
            mtime_ns=int(st.st_mtime_ns),
            ctime_ns=int(st.st_ctime_ns),
        )

    @property
    def payload(self) -> dict[str, int]:
        return {
            "dev": self.dev,
            "ino": self.ino,
            "size": self.size,
            "mtime_ns": self.mtime_ns,
            "ctime_ns": self.ctime_ns,
        }


@dataclass(frozen=True)
class ResidentHotAdmissionToken:
    handle_id: str
    program_id: str
    control_definition_id: str
    generation_id: str
    resident_admission_id: str
    generation_payload: Mapping[str, object]
    source_stamps: Mapping[str, FileStamp]
    _generation_payload_snapshot_json: str = field(init=False, repr=False, compare=False)
    _source_stamps_snapshot: tuple[tuple[str, FileStamp], ...] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if not isinstance(self.generation_payload, Mapping):
            raise PersistentRuntimeV25Error("hot token generation_payload must be a mapping")
        try:
            raw = _json_bytes(dict(self.generation_payload))
            decoded = json.loads(raw)
        except (TypeError, ValueError, UnicodeError, PersistentRuntimeV25Error) as exc:
            raise PersistentRuntimeV25Error(
                "hot token generation_payload must be canonical JSON"
            ) from exc
        if not isinstance(decoded, dict):
            raise PersistentRuntimeV25Error("hot token generation_payload must be a JSON object")
        object.__setattr__(
            self,
            "_generation_payload_snapshot_json",
            json.dumps(decoded, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        )

        if not isinstance(self.source_stamps, Mapping) or not self.source_stamps:
            raise PersistentRuntimeV25Error("hot token source_stamps must be a non-empty mapping")
        stamp_rows: list[tuple[str, FileStamp]] = []
        for key, stamp in self.source_stamps.items():
            if not isinstance(key, str) or not key:
                raise PersistentRuntimeV25Error("hot token source stamp key must be non-empty")
            if not isinstance(stamp, FileStamp):
                raise PersistentRuntimeV25Error("hot token source stamp must be FileStamp")
            stamp_rows.append((key, stamp))
        if len({key for key, _ in stamp_rows}) != len(stamp_rows):
            raise PersistentRuntimeV25Error("hot token source stamp keys must be unique")
        object.__setattr__(self, "_source_stamps_snapshot", tuple(sorted(stamp_rows)))

    def _generation_snapshot(self) -> dict[str, object]:
        value = json.loads(self._generation_payload_snapshot_json)
        if not isinstance(value, dict):
            raise PersistentRuntimeV25Error("hot token generation snapshot is invalid")
        return value

    def _stamp_snapshot(self) -> dict[str, FileStamp]:
        return dict(self._source_stamps_snapshot)

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": HOT_TOKEN_SCHEMA,
            "contract_id": HOTPATH_CONTRACT_ID,
            "handle_id": self.handle_id,
            "program_id": self.program_id,
            "control_definition_id": self.control_definition_id,
            "generation_id": self.generation_id,
            "resident_admission_id": self.resident_admission_id,
            "generation_payload": self._generation_snapshot(),
            "source_stamps": {
                key: stamp.payload for key, stamp in self._source_stamps_snapshot
            },
            "scope": "CONTROL_ROOT_V0_20_ONLY",
            "external_effects": False,
            "static_runtime_fallback": False,
            "full_admission_required_to_issue": True,
            "automatic_fallback_to_full_admission": False,
        }

    @property
    def token_id(self) -> str:
        return _typed_id("pncs:resident-hot-token", self.payload)


class PersistentHotRuntimeV30:
    """Fail-closed resident hot dispatch for a fully admitted v0.25 handle."""

    def __init__(self, base: PersistentProgramRuntime) -> None:
        if not isinstance(base, PersistentProgramRuntime):
            raise PersistentRuntimeV25Error("PersistentProgramRuntime required")
        self.base = base
        self.root = base.root
        self.socket_path = base.socket_path
        self.max_heartbeat_age_s = base.max_heartbeat_age_s
        self.require_socket = base.require_socket
        self.runtime_root = self.root / "pncs/v0.30/runtime"

    def _authority_paths(self, handle_id: str, program_id: str) -> dict[str, Path]:
        digest = _handle_digest(handle_id)
        return {
            "resident_program": self.base.runtime_root / "programs" / f"{program_id.rsplit(':', 1)[-1]}.pnv",
            "resident_handle": self.base.runtime_root / "handles" / f"{digest}.json",
            "active_pointer": self.base.runtime_root / "active" / f"{digest}.json",
            "session_startpoint": self.root / "session/startpoint.json",
            "current_memory": self.root / "current_memory.json",
            "fast_admission": self.root / "session/fast_admission.json",
            "operator_registry": self.root / "phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl",
        }

    def _token_path(self, token: ResidentHotAdmissionToken) -> Path:
        return self.runtime_root / "tokens" / f"{token.token_id.rsplit(':', 1)[-1]}.json"

    def _token_record_bytes(self, token: ResidentHotAdmissionToken) -> bytes:
        return _json_bytes({**token.payload, "token_id": token.token_id})

    def _verify_issued_token(self, token: ResidentHotAdmissionToken) -> None:
        path = self._token_path(token)
        try:
            observed = path.read_bytes()
        except OSError as exc:
            raise PersistentRuntimeV25Error(
                "hot token has no persisted full-admission issuance record"
            ) from exc
        if observed != self._token_record_bytes(token):
            raise PersistentRuntimeV25Error("persisted hot token record mismatch")

    def issue(self, handle_id: str) -> ResidentHotAdmissionToken:
        admission: ResidentAdmission = self.base.admit(handle_id)
        handle = admission.handle
        paths = self._authority_paths(handle_id, handle.image.program_id)
        stamps = {name: FileStamp.read(path) for name, path in paths.items()}
        token = ResidentHotAdmissionToken(
            handle_id=handle.handle_id,
            program_id=handle.image.program_id,
            control_definition_id=handle.image.control_definition_id,
            generation_id=handle.generation.generation_id,
            resident_admission_id=admission.admission_id,
            generation_payload=handle.generation.payload,
            source_stamps=stamps,
        )
        _immutable_write(self._token_path(token), self._token_record_bytes(token))
        return token

    def _check_stamps(self, token: ResidentHotAdmissionToken) -> None:
        paths = self._authority_paths(token.handle_id, token.program_id)
        stamps = token._stamp_snapshot()
        if set(paths) != set(stamps):
            raise PersistentRuntimeV25Error("hot token authority-file set mismatch")
        for name, path in paths.items():
            if FileStamp.read(path) != stamps[name]:
                raise PersistentRuntimeV25Error(
                    f"hot token invalidated by authority-file change: {name}"
                )

    def guard(self, token: ResidentHotAdmissionToken) -> None:
        if not isinstance(token, ResidentHotAdmissionToken):
            raise PersistentRuntimeV25Error("ResidentHotAdmissionToken required")
        if self.root != DEFAULT_SURFACE_ROOT and self.base.require_canonical_root:
            raise PersistentRuntimeV25Error(
                "v0.30 operational runtime is fixed to /dev/shm/ciel_noema"
            )

        self._verify_issued_token(token)
        try:
            binding = (self.root / "ciel_binding_status").read_text("utf-8").strip()
        except (OSError, UnicodeError) as exc:
            raise PersistentRuntimeV25Error("hotpath missing live binding status") from exc
        if binding != "ACTIVE":
            raise PersistentRuntimeV25Error("hotpath NOEMA↔AUX binding is not ACTIVE")

        self._check_stamps(token)
        expected = token._generation_snapshot()

        current = _load_json(self.root / "current_memory.json", "hot current memory")
        seal = _load_json(self.root / "session/fast_admission.json", "hot fast admission")
        active = _load_json(
            self.base.runtime_root / "active" / f"{_handle_digest(token.handle_id)}.json",
            "hot resident active pointer",
        )

        if active.get("handle_id") != token.handle_id or active.get("generation_id") != token.generation_id:
            raise PersistentRuntimeV25Error("hot token resident pointer mismatch")
        if seal.get("schema") != "noema.fast-admission-seal/v2" or seal.get("status") != "ACTIVE":
            raise PersistentRuntimeV25Error("hot fast admission seal is not ACTIVE v2")
        if seal.get("no_static_fallback") is not True:
            raise PersistentRuntimeV25Error("hot fast admission seal permits static fallback")

        for field in (
            "account_current",
            "current_pointer_sha256",
            "startpoint_packet_sha256",
            "ac_current_sha256",
            "ethics_field_sha256",
            "aux_pid",
            "tether_pid",
            "ac_aux_pid",
        ):
            if seal.get(field) != expected.get(field):
                raise PersistentRuntimeV25Error(f"hot generation mismatch at {field}")

        if current.get("account_current") != expected.get("account_current"):
            raise PersistentRuntimeV25Error("hot CURRENT account mismatch")
        if current.get("current_pointer_sha256") != expected.get("current_pointer_sha256"):
            raise PersistentRuntimeV25Error("hot CURRENT pointer mismatch")

        aux = _active_status(
            self.root / "aux_stream_status.json",
            "noema.aux-stream-status/v2",
            self.max_heartbeat_age_s,
        )
        tether = _active_status(
            self.root / "tether_runtime_status.json",
            "noema.tether-runtime-status/v1",
            self.max_heartbeat_age_s,
        )
        ac = _active_status(
            self.root / "ac_aux_status.json",
            "noema.ac-aux-live-binding/v2",
            self.max_heartbeat_age_s,
        )

        live_pids = {
            "aux_pid": int(aux["pid"]),
            "tether_pid": int(tether["pid"]),
            "ac_aux_pid": int(ac["pid"]),
        }
        for field, value in live_pids.items():
            if value != int(expected.get(field, -1)):
                raise PersistentRuntimeV25Error(f"hot producer PID mismatch at {field}")

        if ac.get("ethics_field_status") != "ACTIVE" or ac.get("no_static_fallback") is not True:
            raise PersistentRuntimeV25Error("hot AC↔AUX ethics hardpath inactive")
        for field in (
            "account_current",
            "current_pointer_sha256",
            "ac_current_sha256",
            "ethics_field_sha256",
        ):
            if ac.get(field) != expected.get(field):
                raise PersistentRuntimeV25Error(f"hot AC generation mismatch at {field}")
        if int(ac.get("aux_pid", -1)) != live_pids["aux_pid"] or int(ac.get("tether_pid", -1)) != live_pids["tether_pid"]:
            raise PersistentRuntimeV25Error("hot AC↔AUX producer binding mismatch")

        if self.require_socket:
            _socket_check(self.socket_path)

    def dispatch_control(
        self,
        token: ResidentHotAdmissionToken,
        kernel: Callable[[], tuple[object, object]],
    ) -> ResidentDispatchReceipt:
        if not callable(kernel):
            raise PersistentRuntimeV25Error(
                "in-process v0.20/v0.22 kernel callback required"
            )
        self.guard(token)
        result, lineage = kernel()
        self.guard(token)

        execution_sha, target, truth = _validate_execution_result(
            result,
            token.control_definition_id,
            expected_root=str(self.root),
        )
        result_id, lineage_id = _validate_lineage(
            lineage,
            execution_sha,
            token.control_definition_id,
        )
        receipt = ResidentDispatchReceipt(
            handle_id=token.handle_id,
            program_id=token.program_id,
            generation_id=token.generation_id,
            resident_admission_id=token.resident_admission_id,
            execution_receipt_sha256=execution_sha,
            result_id=result_id,
            lineage_id=lineage_id,
            target=target,
            branch_truth_state=truth,
        )
        path = self.runtime_root / "receipts/dispatch" / f"{receipt.dispatch_id.rsplit(':', 1)[-1]}.json"
        _immutable_write(path, _json_bytes({**receipt.payload, "dispatch_id": receipt.dispatch_id}))
        return receipt
