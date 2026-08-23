from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import stat
import time
from typing import Callable, Mapping

RUNTIME_CONTRACT_ID = "PNCS_PERSISTENT_RUNTIME_V0_25"
GENERATION_SCHEMA = "PNCS_LIVE_RUNTIME_GENERATION_V0_25"
PROGRAM_IMAGE_SCHEMA = "PNCS_RESIDENT_PROGRAM_IMAGE_V0_25"
HANDLE_SCHEMA = "PNCS_RESIDENT_PROGRAM_HANDLE_V0_25"
LOAD_RECEIPT_SCHEMA = "PNCS_RESIDENT_PROGRAM_LOAD_RECEIPT_V0_25"
ADMISSION_SCHEMA = "PNCS_RESIDENT_PROGRAM_ADMISSION_V0_25"
DISPATCH_RECEIPT_SCHEMA = "PNCS_RESIDENT_CONTROL_DISPATCH_RECEIPT_V0_25"
UNLOAD_RECEIPT_SCHEMA = "PNCS_RESIDENT_PROGRAM_UNLOAD_RECEIPT_V0_25"

V24_BUILD_SCHEMA = "PNCS_NATIVE_PNV_PROGRAM_BUILD_RECEIPT_V0_24"
V24_BUILD_CONTRACT_ID = "PNCS_NATIVE_PNV_PROGRAM_BUILD_V0_24"
V22_LINEAGE_CONTRACT_ID = "PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22"
V20_EXECUTION_SCHEMA = "PNCS_NATIVE_EXECUTION_RECEIPT_V0_20"
V20_EXECUTION_CONTRACT_ID = "PNCS_NATIVE_EXECUTION_CORE_V0_20"

DEFAULT_SURFACE_ROOT = Path("/dev/shm/ciel_noema")
DEFAULT_SOCKET = Path("/run/user/1000/noema/ciel_headless.sock")

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_TYPED_RE = re.compile(r"^pncs:[a-z0-9-]+:sha256:[0-9a-f]{64}$")
_PROGRAM_RE = re.compile(r"^pncs:program:sha256:[0-9a-f]{64}$")
_COMPOSITION_RE = re.compile(r"^pncs:composition:sha256:[0-9a-f]{64}$")
_DEFINITION_RE = re.compile(r"^pncs:def:sha256:[0-9a-f]{64}$")
_BUILD_RE = re.compile(r"^pncs:program-build:sha256:[0-9a-f]{64}$")
_HANDLE_RE = re.compile(r"^pncs:resident:sha256:[0-9a-f]{64}$")
_RESULT_RE = re.compile(r"^pncs:result:sha256:[0-9a-f]{64}$")
_LINEAGE_RE = re.compile(r"^pncs:lineage:sha256:[0-9a-f]{64}$")


class PersistentRuntimeV25Error(RuntimeError):
    pass


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise PersistentRuntimeV25Error("non-finite value is not canonical JSON")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    raise PersistentRuntimeV25Error(f"unsupported canonical value type: {type(value).__name__}")


def _compact_json(value: object) -> str:
    return json.dumps(
        _jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_compact_json(value).encode("utf-8"))


def _typed_id(prefix: str, payload: object) -> str:
    return f"{prefix}:sha256:{_sha256_json(payload)}"


def _digest(value: object, field: str) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise PersistentRuntimeV25Error(f"{field} must be lowercase SHA-256")
    return value


def _typed(value: object, regex: re.Pattern[str], field: str) -> str:
    if not isinstance(value, str) or not regex.fullmatch(value):
        raise PersistentRuntimeV25Error(f"invalid {field}")
    return value


def _load_json(path: Path, field: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text("utf-8"))
    except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PersistentRuntimeV25Error(f"invalid {field}: {path}") from exc
    if not isinstance(value, dict):
        raise PersistentRuntimeV25Error(f"{field} must be a JSON object")
    return value


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _active_status(path: Path, schema: str, max_age_s: float) -> dict[str, object]:
    value = _load_json(path, path.name)
    if value.get("schema") != schema or value.get("status") != "ACTIVE":
        raise PersistentRuntimeV25Error(f"inactive or wrong-schema live status: {path}")
    try:
        pid = int(value["pid"])
        heartbeat_ns = int(value["heartbeat_ns"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PersistentRuntimeV25Error(f"invalid heartbeat fields: {path}") from exc
    age = (time.time_ns() - heartbeat_ns) / 1e9
    if age < -0.5 or age > max_age_s:
        raise PersistentRuntimeV25Error(f"stale live heartbeat: {path}")
    if not _alive(pid):
        raise PersistentRuntimeV25Error(f"dead live producer PID: {path}")
    return value


def _verify_startpoint(path: Path) -> dict[str, object]:
    value = _load_json(path, "session startpoint")
    if value.get("schema") != "noema/session-startpoint/v1" or value.get("status") != "VERIFIED":
        raise PersistentRuntimeV25Error("session startpoint is not VERIFIED")
    expected = _digest(value.get("packet_sha256"), "startpoint.packet_sha256")
    base = dict(value)
    base.pop("packet_sha256", None)
    actual = _sha256_bytes(
        json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    if actual != expected:
        raise PersistentRuntimeV25Error("startpoint packet SHA mismatch")
    return value


def _socket_check(path: Path) -> None:
    try:
        mode = path.stat().st_mode
    except FileNotFoundError as exc:
        raise PersistentRuntimeV25Error(f"required live socket missing: {path}") from exc
    if not stat.S_ISSOCK(mode):
        raise PersistentRuntimeV25Error(f"required live socket is not Unix socket: {path}")


@dataclass(frozen=True)
class LiveRuntimeGeneration:
    root: str
    socket_path: str
    account_current: str
    current_pointer_sha256: str
    startpoint_packet_sha256: str
    ac_current_sha256: str
    ethics_field_sha256: str
    operator_registry_sha256: str
    aux_pid: int
    tether_pid: int
    ac_aux_pid: int

    def __post_init__(self) -> None:
        if not self.root:
            raise PersistentRuntimeV25Error("generation root is empty")
        if not self.socket_path:
            raise PersistentRuntimeV25Error("generation socket path is empty")
        if not self.account_current:
            raise PersistentRuntimeV25Error("generation account_current is empty")
        for field in (
            "current_pointer_sha256",
            "startpoint_packet_sha256",
            "ac_current_sha256",
            "ethics_field_sha256",
            "operator_registry_sha256",
        ):
            _digest(getattr(self, field), field)
        for field in ("aux_pid", "tether_pid", "ac_aux_pid"):
            if not isinstance(getattr(self, field), int) or getattr(self, field) <= 0:
                raise PersistentRuntimeV25Error(f"{field} must be positive PID")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": GENERATION_SCHEMA,
            "runtime_contract_id": RUNTIME_CONTRACT_ID,
            "root": self.root,
            "socket_path": self.socket_path,
            "account_current": self.account_current,
            "current_pointer_sha256": self.current_pointer_sha256,
            "startpoint_packet_sha256": self.startpoint_packet_sha256,
            "ac_current_sha256": self.ac_current_sha256,
            "ethics_field_sha256": self.ethics_field_sha256,
            "operator_registry_sha256": self.operator_registry_sha256,
            "aux_pid": self.aux_pid,
            "tether_pid": self.tether_pid,
            "ac_aux_pid": self.ac_aux_pid,
            "sequence_counters_are_generation_identity": False,
            "continuous_phi_is_generation_identity": False,
            "static_runtime_fallback": False,
        }

    @property
    def generation_id(self) -> str:
        return _typed_id("pncs:runtime-generation", self.payload)


def read_live_generation(
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    *,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
    require_socket: bool = True,
    require_canonical_root: bool = True,
) -> LiveRuntimeGeneration:
    root = Path(surface_root)
    sock = Path(socket_path)
    if require_canonical_root and root != DEFAULT_SURFACE_ROOT:
        raise PersistentRuntimeV25Error("v0.25 operational runtime is fixed to /dev/shm/ciel_noema")
    if not root.is_dir():
        raise PersistentRuntimeV25Error(f"missing live runtime root: {root}")
    binding = root / "ciel_binding_status"
    try:
        binding_value = binding.read_text("utf-8").strip()
    except (FileNotFoundError, OSError, UnicodeError) as exc:
        raise PersistentRuntimeV25Error("missing live binding status") from exc
    if binding_value != "ACTIVE":
        raise PersistentRuntimeV25Error("NOEMA↔AUX binding is not ACTIVE")

    start = _verify_startpoint(root / "session/startpoint.json")
    current = _load_json(root / "current_memory.json", "current memory")
    seal = _load_json(root / "session/fast_admission.json", "fast admission seal")
    if seal.get("schema") != "noema.fast-admission-seal/v2" or seal.get("status") != "ACTIVE":
        raise PersistentRuntimeV25Error("fast admission seal is not ACTIVE v2")
    if seal.get("no_static_fallback") is not True:
        raise PersistentRuntimeV25Error("fast admission seal permits static fallback")

    aux = _active_status(root / "aux_stream_status.json", "noema.aux-stream-status/v2", max_heartbeat_age_s)
    tether = _active_status(root / "tether_runtime_status.json", "noema.tether-runtime-status/v1", max_heartbeat_age_s)
    ac = _active_status(root / "ac_aux_status.json", "noema.ac-aux-live-binding/v2", max_heartbeat_age_s)
    if ac.get("ethics_field_status") != "ACTIVE" or ac.get("no_static_fallback") is not True:
        raise PersistentRuntimeV25Error("live AC↔AUX ethics hardpath is not ACTIVE/no-fallback")

    account_current = str(current.get("account_current", ""))
    current_sha = _digest(current.get("current_pointer_sha256"), "current_memory.current_pointer_sha256")
    start_sha = _digest(start.get("packet_sha256"), "startpoint.packet_sha256")
    ac_sha = _digest(ac.get("ac_current_sha256"), "ac_aux.ac_current_sha256")
    ethics_sha = _digest(ac.get("ethics_field_sha256"), "ac_aux.ethics_field_sha256")

    if seal.get("account_current") != account_current or ac.get("account_current") != account_current:
        raise PersistentRuntimeV25Error("CURRENT identity mismatch across live admission set")
    if seal.get("current_pointer_sha256") != current_sha or ac.get("current_pointer_sha256") != current_sha:
        raise PersistentRuntimeV25Error("CURRENT SHA mismatch across live admission set")
    if seal.get("startpoint_packet_sha256") != start_sha:
        raise PersistentRuntimeV25Error("startpoint generation differs from fast seal")
    if seal.get("ac_current_sha256") != ac_sha:
        raise PersistentRuntimeV25Error("AC generation differs from fast seal")
    if seal.get("ethics_field_sha256") != ethics_sha:
        raise PersistentRuntimeV25Error("ethics generation differs from fast seal")

    aux_pid, tether_pid, ac_aux_pid = int(aux["pid"]), int(tether["pid"]), int(ac["pid"])
    for field, expected in (
        ("aux_pid", aux_pid),
        ("tether_pid", tether_pid),
        ("ac_aux_pid", ac_aux_pid),
    ):
        if int(seal.get(field, -1)) != expected:
            raise PersistentRuntimeV25Error(f"{field} generation differs from fast seal")
    if int(ac.get("aux_pid", -1)) != aux_pid or int(ac.get("tether_pid", -1)) != tether_pid:
        raise PersistentRuntimeV25Error("AC↔AUX producer PID binding mismatch")

    operator_path = root / "phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl"
    try:
        operator_raw = operator_path.read_bytes()
    except OSError as exc:
        raise PersistentRuntimeV25Error("live operator registry is unavailable") from exc
    if not operator_raw:
        raise PersistentRuntimeV25Error("live operator registry is empty")
    operator_sha = _sha256_bytes(operator_raw)

    if require_socket:
        _socket_check(sock)

    return LiveRuntimeGeneration(
        root=str(root),
        socket_path=str(sock),
        account_current=account_current,
        current_pointer_sha256=current_sha,
        startpoint_packet_sha256=start_sha,
        ac_current_sha256=ac_sha,
        ethics_field_sha256=ethics_sha,
        operator_registry_sha256=operator_sha,
        aux_pid=aux_pid,
        tether_pid=tether_pid,
        ac_aux_pid=ac_aux_pid,
    )
