from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
import stat
import struct
import time

from .execution_v20_model import (
    BYTES_36D, DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT, DIM,
    EXECUTABLE_INTERNAL_OPERATORS, LiveSurfaceV20Error,
    _DIGEST_RE, _finite_scalar, _sha256_bytes, _sha256_json,
)

def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_vector(path: Path) -> tuple[tuple[float, ...], str]:
    if not path.is_file():
        raise LiveSurfaceV20Error(f"missing live 36D vector: {path}")
    raw = path.read_bytes()
    if len(raw) != BYTES_36D:
        raise LiveSurfaceV20Error(f"live 36D vector has {len(raw)} bytes, expected {BYTES_36D}: {path}")
    values = struct.unpack("<36d", raw)
    if not all(math.isfinite(x) for x in values):
        raise LiveSurfaceV20Error(f"non-finite live 36D vector: {path}")
    return tuple(values), _sha256_bytes(raw)


def _load_status(path: Path, schema: str, max_heartbeat_age_s: float) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LiveSurfaceV20Error(f"invalid live status: {path}") from exc
    if not isinstance(value, dict) or value.get("schema") != schema or value.get("status") != "ACTIVE":
        raise LiveSurfaceV20Error(f"live status not ACTIVE under expected schema: {path}")
    try:
        heartbeat_ns = int(value["heartbeat_ns"])
        pid = int(value["pid"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LiveSurfaceV20Error(f"invalid heartbeat fields: {path}") from exc
    age = (time.time_ns() - heartbeat_ns) / 1e9
    if age < -0.5 or age > max_heartbeat_age_s:
        raise LiveSurfaceV20Error(f"stale live heartbeat: {path}")
    if not _process_alive(pid):
        raise LiveSurfaceV20Error(f"live producer PID is not alive: {path}")
    return value


def _operator_registry(path: Path) -> tuple[dict[str, tuple[float, ...]], str]:
    if not path.is_file():
        raise LiveSurfaceV20Error(f"missing live PhaseNav operator registry: {path}")
    raw = path.read_bytes()
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise LiveSurfaceV20Error("operator registry is not UTF-8") from exc
    operators: dict[str, tuple[float, ...]] = {}
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LiveSurfaceV20Error(f"invalid operator JSONL line {line_no}") from exc
        if not isinstance(rec, dict) or rec.get("schema") != "PHASENAV_OPERATOR_VECTOR_V1":
            raise LiveSurfaceV20Error(f"unexpected operator registry schema at line {line_no}")
        op = str(rec.get("operator_name", rec.get("operator_id", rec.get("card_id", "")))).strip().upper()
        orbit = rec.get("orbit_vector", rec.get("vector_36d"))
        if not op or not isinstance(orbit, list) or len(orbit) != DIM:
            raise LiveSurfaceV20Error(f"operator {op!r} is not an exact 36D runtime entry")
        vec = tuple(_finite_scalar(x, f"operator {op} phase") for x in orbit)
        if op in operators:
            raise LiveSurfaceV20Error(f"duplicate live operator: {op}")
        operators[op] = vec
    if not operators:
        raise LiveSurfaceV20Error("live operator registry is empty")
    missing = sorted(EXECUTABLE_INTERNAL_OPERATORS - set(operators))
    if missing:
        raise LiveSurfaceV20Error(f"live operator registry missing v0.20 internal operators: {missing}")
    return operators, _sha256_bytes(raw)


@dataclass(frozen=True)
class LiveSurfaceSnapshot:
    root: str
    phi_sha256: str
    aux_phi_sha256: str
    aux_feedback_phi_sha256: str
    operator_registry_sha256: str
    tether_receipt_sha256: str
    operator_vectors: Mapping[str, tuple[float, ...]]

    @property
    def receipt_payload(self) -> dict[str, object]:
        return {
            "root": self.root,
            "phi_sha256": self.phi_sha256,
            "aux_phi_sha256": self.aux_phi_sha256,
            "aux_feedback_phi_sha256": self.aux_feedback_phi_sha256,
            "operator_registry_sha256": self.operator_registry_sha256,
            "tether_receipt_sha256": self.tether_receipt_sha256,
        }


def load_live_surface(
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    *,
    socket_path: Path | str = DEFAULT_SOCKET,
    require_socket: bool = True,
    max_heartbeat_age_s: float = 2.0,
) -> LiveSurfaceSnapshot:
    root = Path(surface_root)
    if not root.is_dir():
        raise LiveSurfaceV20Error(f"missing live NOEMA surface: {root}")
    binding = root / "ciel_binding_status"
    if not binding.is_file() or binding.read_text(encoding="utf-8", errors="strict").strip() != "ACTIVE":
        raise LiveSurfaceV20Error("NOEMA↔AUX binding is not ACTIVE")

    startpoint = root / "session/startpoint.json"
    system_message = root / "session/system_message.txt"
    try:
        start = json.loads(startpoint.read_text(encoding="utf-8"))
        message = system_message.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LiveSurfaceV20Error("verified session startpoint is unavailable") from exc
    if not isinstance(start, dict) or start.get("status") != "VERIFIED" or "status: VERIFIED" not in message:
        raise LiveSurfaceV20Error("session startpoint is not VERIFIED")

    aux_status = _load_status(root / "aux_stream_status.json", "noema.aux-stream-status/v2", max_heartbeat_age_s)
    tether_status = _load_status(root / "tether_runtime_status.json", "noema.tether-runtime-status/v1", max_heartbeat_age_s)
    _, phi_sha = _read_vector(root / "phi")
    _, aux_sha = _read_vector(root / "aux_phi")
    _, feedback_sha = _read_vector(root / "aux_feedback_phi")

    if aux_status.get("state_sha256") != aux_sha:
        raise LiveSurfaceV20Error("AUX status digest does not match live aux_phi")
    for field, actual in (
        ("phi_sha256", phi_sha),
        ("aux_phi_sha256", aux_sha),
        ("aux_feedback_phi_sha256", feedback_sha),
    ):
        if tether_status.get(field) != actual:
            raise LiveSurfaceV20Error(f"tether digest mismatch for {field}")

    if require_socket:
        sock = Path(socket_path)
        try:
            if not stat.S_ISSOCK(sock.stat().st_mode):
                raise LiveSurfaceV20Error(f"required NOEMA socket is not a Unix socket: {sock}")
        except FileNotFoundError as exc:
            raise LiveSurfaceV20Error(f"required NOEMA socket is missing: {sock}") from exc

    operators, operator_registry_sha = _operator_registry(
        root / "phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl"
    )
    receipt_sha = str(tether_status.get("receipt_sha256", ""))
    if not _DIGEST_RE.fullmatch(receipt_sha):
        raise LiveSurfaceV20Error("tether runtime does not expose a valid receipt SHA-256")
    return LiveSurfaceSnapshot(
        root=str(root),
        phi_sha256=phi_sha,
        aux_phi_sha256=aux_sha,
        aux_feedback_phi_sha256=feedback_sha,
        operator_registry_sha256=operator_registry_sha,
        tether_receipt_sha256=receipt_sha,
        operator_vectors=operators,
    )
