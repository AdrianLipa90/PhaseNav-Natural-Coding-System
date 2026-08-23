#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
import struct
import time
from pathlib import Path

N = 36
BYTES = N * 8


def check_f64_vector(path: Path) -> tuple[bool, str, bytes | None]:
    if not path.is_file():
        return False, f"MISSING:{path}", None
    try:
        data = path.read_bytes()
    except OSError as exc:
        return False, f"READ_ERROR:{path}:{type(exc).__name__}:{exc}", None
    if len(data) != BYTES:
        return False, f"BAD_SIZE:{path}:{len(data)}!=288", data
    try:
        vals = struct.unpack("<36d", data)
    except struct.error as exc:
        return False, f"UNPACK_ERROR:{path}:{exc}", data
    if not all(math.isfinite(x) for x in vals):
        return False, f"NONFINITE:{path}", data
    return True, "PASS", data


def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _load_status(path: Path, expected_schema: str, max_age: float) -> tuple[dict | None, str | None, float | None]:
    if not path.is_file():
        return None, f"MISSING:{path}", None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"INVALID_JSON:{path}:{type(exc).__name__}:{exc}", None
    if not isinstance(value, dict):
        return None, f"INVALID_ROOT:{path}:expected_object", None
    if value.get("schema") != expected_schema:
        return None, f"BAD_SCHEMA:{path}:{value.get('schema')!r}!={expected_schema!r}", None
    if value.get("status") != "ACTIVE":
        return value, f"STATUS_NOT_ACTIVE:{path}:{value.get('status')!r}", None
    try:
        heartbeat_ns = int(value["heartbeat_ns"])
        pid = int(value["pid"])
    except (KeyError, TypeError, ValueError) as exc:
        return value, f"BAD_HEARTBEAT_FIELDS:{path}:{type(exc).__name__}:{exc}", None
    age = (time.time_ns() - heartbeat_ns) / 1e9
    if age < -0.5 or age > max_age:
        return value, f"STALE_HEARTBEAT:{path}:age={age:.6f}s", age
    if not _process_alive(pid):
        return value, f"PID_NOT_ALIVE:{path}:pid={pid}", age
    return value, None, age


def _check_startpoint(root: Path) -> list[str]:
    failures: list[str] = []
    startpoint = root / "session/startpoint.json"
    system_message = root / "session/system_message.txt"
    if not startpoint.is_file():
        failures.append(f"MISSING:{startpoint}")
        return failures
    try:
        packet = json.loads(startpoint.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        failures.append(f"INVALID_JSON:{startpoint}:{type(exc).__name__}:{exc}")
        return failures
    if not isinstance(packet, dict):
        failures.append(f"INVALID_ROOT:{startpoint}:expected_object")
        return failures
    if packet.get("status") != "VERIFIED":
        failures.append(f"STARTPOINT_NOT_VERIFIED:{packet.get('status')!r}")
    expected_sha = packet.get("packet_sha256")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        failures.append("STARTPOINT_BAD_PACKET_SHA256")
    else:
        base = dict(packet)
        base.pop("packet_sha256", None)
        actual_sha = hashlib.sha256(json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        if actual_sha != expected_sha:
            failures.append(f"STARTPOINT_SHA_MISMATCH:{actual_sha}!={expected_sha}")
    if not system_message.is_file():
        failures.append(f"MISSING:{system_message}")
    else:
        try:
            msg = system_message.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            failures.append(f"INVALID_TEXT:{system_message}:{type(exc).__name__}:{exc}")
        else:
            if not msg.strip():
                failures.append(f"EMPTY:{system_message}")
            if expected_sha and f"packet_sha256: {expected_sha}" not in msg:
                failures.append("SYSTEM_MESSAGE_STARTPOINT_SHA_MISMATCH")
            if "status: VERIFIED" not in msg:
                failures.append("SYSTEM_MESSAGE_NOT_VERIFIED")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/dev/shm/ciel_noema")
    ap.add_argument("--socket", default="/run/user/1000/noema/ciel_headless.sock")
    ap.add_argument("--require-socket", action="store_true")
    ap.add_argument("--max-heartbeat-age", type=float, default=2.0)
    args = ap.parse_args()

    root = Path(args.root)
    failures: list[str] = []
    heartbeat_age_s: dict[str, float] = {}

    if not root.is_dir():
        failures.append(f"MISSING_ROOT:{root}")

    binding = root / "ciel_binding_status"
    if not binding.is_file():
        failures.append(f"MISSING:{binding}")
    else:
        try:
            value = binding.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError) as exc:
            failures.append(f"INVALID_BINDING_TEXT:{type(exc).__name__}:{exc}")
        else:
            if value != "ACTIVE":
                failures.append(f"BINDING_NOT_ACTIVE:{value!r}")

    vectors: dict[str, bytes] = {}
    aux_status = tether_status = None
    aux_age = tether_age = None
    snapshot_error = None
    deadline = time.monotonic() + min(1.5, max(0.25, args.max_heartbeat_age))
    while time.monotonic() < deadline:
        local_failures: list[str] = []
        local_vectors: dict[str, bytes] = {}
        a_status, a_error, a_age = _load_status(root / "aux_stream_status.json", "noema.aux-stream-status/v2", args.max_heartbeat_age)
        t_status, t_error, t_age = _load_status(root / "tether_runtime_status.json", "noema.tether-runtime-status/v1", args.max_heartbeat_age)
        if a_error:
            local_failures.append(a_error)
        if t_error:
            local_failures.append(t_error)
        for name in ("phi", "aux_phi", "aux_feedback_phi"):
            ok, detail, raw = check_f64_vector(root / name)
            if not ok:
                local_failures.append(detail)
            elif raw is not None:
                local_vectors[name] = raw
        if not local_failures and local_vectors.get("aux_phi") != local_vectors.get("aux_feedback_phi"):
            local_failures.append("AUX_FEEDBACK_NOT_LOSSLESS_IDENTITY")
        if not local_failures and a_status is not None:
            actual = hashlib.sha256(local_vectors["aux_phi"]).hexdigest()
            if a_status.get("state_sha256") != actual:
                local_failures.append("AUX_STATUS_SNAPSHOT_RACE")
        if not local_failures and t_status is not None:
            for field, name in (("phi_sha256", "phi"), ("aux_phi_sha256", "aux_phi"), ("aux_feedback_phi_sha256", "aux_feedback_phi")):
                actual = hashlib.sha256(local_vectors[name]).hexdigest()
                if t_status.get(field) != actual:
                    local_failures.append(f"TETHER_STATUS_SNAPSHOT_RACE:{field}")
                    break
        if not local_failures:
            vectors = local_vectors
            aux_status = a_status
            tether_status = t_status
            aux_age = a_age
            tether_age = t_age
            snapshot_error = None
            break
        snapshot_error = local_failures
        time.sleep(0.01)
    if snapshot_error is not None:
        failures.extend(snapshot_error)
    if aux_age is not None:
        heartbeat_age_s["aux"] = aux_age
    if tether_age is not None:
        heartbeat_age_s["tether"] = tether_age

    failures.extend(_check_startpoint(root))

    if args.require_socket:
        sock_path = Path(args.socket)
        try:
            if not stat.S_ISSOCK(sock_path.stat().st_mode):
                failures.append(f"NOT_UNIX_SOCKET:{sock_path}")
        except FileNotFoundError:
            failures.append(f"MISSING_SOCKET:{sock_path}")
        except OSError as exc:
            failures.append(f"SOCKET_STAT_ERROR:{sock_path}:{type(exc).__name__}:{exc}")

    status = {
        "schema": "noema.aux-tether-guard/v2",
        "root": str(root),
        "tether_status": "ACTIVE" if not failures else "BLOCKED",
        "failures": failures,
        "heartbeat_age_s": heartbeat_age_s,
        "max_heartbeat_age_s": args.max_heartbeat_age,
        "fail_closed": True,
    }
    print(json.dumps(status, sort_keys=True, ensure_ascii=False))
    return 0 if not failures else 23


if __name__ == "__main__":
    raise SystemExit(main())
