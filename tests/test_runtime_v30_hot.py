from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from phasenav_natural_code.runtime_v25_core import PersistentRuntimeV25Error
from phasenav_natural_code.runtime_v25_resident import PersistentProgramRuntime
from phasenav_natural_code.runtime_v25_resident_model import _json_bytes
from phasenav_natural_code.runtime_v30_hot import FileStamp, PersistentHotRuntimeV30, ResidentHotAdmissionToken

H = "1" * 64
P = "2" * 64
D = "3" * 64
A = "4" * 64
E = "5" * 64


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")


def _fixture(tmp_path: Path, *, persist_token: bool = True):
    root = tmp_path / "surface"
    base = PersistentProgramRuntime(root, socket_path=tmp_path / "unused.sock", require_socket=False, require_canonical_root=False, max_heartbeat_age_s=2.0)
    hot = PersistentHotRuntimeV30(base)
    pid = os.getpid()
    handle_id = f"pncs:resident:sha256:{H}"
    program_id = f"pncs:program:sha256:{P}"
    generation_id = f"pncs:runtime-generation:sha256:{D}"
    admission_id = f"pncs:resident-admission:sha256:{A}"
    control_definition_id = f"pncs:def:sha256:{E}"
    generation = {
        "root": str(root), "socket_path": str(tmp_path / "unused.sock"),
        "account_current": "/NOEMA/CURRENT", "current_pointer_sha256": "a" * 64,
        "startpoint_packet_sha256": "b" * 64, "ac_current_sha256": "c" * 64,
        "ethics_field_sha256": "d" * 64, "operator_registry_sha256": "e" * 64,
        "aux_pid": pid, "tether_pid": pid, "ac_aux_pid": pid,
    }
    paths = hot._authority_paths(handle_id, program_id)
    paths["resident_program"].parent.mkdir(parents=True, exist_ok=True)
    paths["resident_program"].write_bytes(b"PNV 1\n")
    _write_json(paths["resident_handle"], {"handle_id": handle_id})
    _write_json(paths["active_pointer"], {"handle_id": handle_id, "generation_id": generation_id})
    _write_json(paths["session_startpoint"], {"packet_sha256": generation["startpoint_packet_sha256"]})
    _write_json(paths["current_memory"], {"account_current": generation["account_current"], "current_pointer_sha256": generation["current_pointer_sha256"]})
    _write_json(paths["fast_admission"], {
        "schema": "noema.fast-admission-seal/v2", "status": "ACTIVE", "no_static_fallback": True,
        **{k: generation[k] for k in ("account_current", "current_pointer_sha256", "startpoint_packet_sha256", "ac_current_sha256", "ethics_field_sha256", "aux_pid", "tether_pid", "ac_aux_pid")},
    })
    paths["operator_registry"].parent.mkdir(parents=True, exist_ok=True)
    paths["operator_registry"].write_text('{"op":"TEST"}\n', encoding="utf-8")
    (root / "ciel_binding_status").write_text("ACTIVE\n", encoding="utf-8")
    heartbeat = time.time_ns()
    _write_json(root / "aux_stream_status.json", {"schema": "noema.aux-stream-status/v2", "status": "ACTIVE", "pid": pid, "heartbeat_ns": heartbeat})
    _write_json(root / "tether_runtime_status.json", {"schema": "noema.tether-runtime-status/v1", "status": "ACTIVE", "pid": pid, "heartbeat_ns": heartbeat})
    _write_json(root / "ac_aux_status.json", {
        "schema": "noema.ac-aux-live-binding/v2", "status": "ACTIVE", "pid": pid, "heartbeat_ns": heartbeat,
        "ethics_field_status": "ACTIVE", "no_static_fallback": True,
        "account_current": generation["account_current"], "current_pointer_sha256": generation["current_pointer_sha256"],
        "ac_current_sha256": generation["ac_current_sha256"], "ethics_field_sha256": generation["ethics_field_sha256"],
        "aux_pid": pid, "tether_pid": pid,
    })
    stamps = {name: FileStamp.read(path) for name, path in paths.items()}
    token = ResidentHotAdmissionToken(handle_id, program_id, control_definition_id, generation_id, admission_id, generation, stamps)
    if persist_token:
        token_path = hot._token_path(token)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_bytes(_json_bytes({**token.payload, "token_id": token.token_id}))
    return hot, token, paths, root


def test_hot_guard_accepts_unchanged_live_generation(tmp_path: Path):
    hot, token, _, _ = _fixture(tmp_path)
    hot.guard(token)


def test_hot_guard_rejects_unissued_forged_token(tmp_path: Path):
    hot, token, _, _ = _fixture(tmp_path, persist_token=False)
    with pytest.raises(PersistentRuntimeV25Error, match="no persisted full-admission issuance record"):
        hot.guard(token)


def test_hot_guard_rejects_persisted_token_record_tamper(tmp_path: Path):
    hot, token, _, _ = _fixture(tmp_path)
    hot._token_path(token).write_text('{"tampered":true}\n', encoding="utf-8")
    with pytest.raises(PersistentRuntimeV25Error, match="persisted hot token record mismatch"):
        hot.guard(token)


def test_hot_token_snapshots_mutable_generation_payload(tmp_path: Path):
    hot, token, _, _ = _fixture(tmp_path)
    before = token.token_id
    token.generation_payload["account_current"] = "/MUTATED"  # type: ignore[index]
    token.generation_payload["current_pointer_sha256"] = "f" * 64  # type: ignore[index]
    assert token.token_id == before
    hot.guard(token)


def test_hot_guard_ignores_mutated_stamp_mapping_and_still_detects_authority_change(tmp_path: Path):
    hot, token, paths, _ = _fixture(tmp_path)
    paths["operator_registry"].write_text('{"op":"TAMPER"}\n', encoding="utf-8")
    token.source_stamps["operator_registry"] = FileStamp.read(paths["operator_registry"])  # type: ignore[index]
    with pytest.raises(PersistentRuntimeV25Error, match="authority-file change: operator_registry"):
        hot.guard(token)


def test_hot_guard_rejects_operator_registry_change(tmp_path: Path):
    hot, token, paths, _ = _fixture(tmp_path)
    paths["operator_registry"].write_text('{"op":"TAMPER"}\n', encoding="utf-8")
    with pytest.raises(PersistentRuntimeV25Error, match="authority-file change: operator_registry"):
        hot.guard(token)


def test_hot_guard_rejects_current_change(tmp_path: Path):
    hot, token, paths, _ = _fixture(tmp_path)
    _write_json(paths["current_memory"], {"account_current": "/OTHER", "current_pointer_sha256": "f" * 64})
    with pytest.raises(PersistentRuntimeV25Error, match="authority-file change: current_memory"):
        hot.guard(token)


def test_hot_guard_rejects_stale_heartbeat(tmp_path: Path):
    hot, token, _, root = _fixture(tmp_path)
    data = json.loads((root / "aux_stream_status.json").read_text("utf-8"))
    data["heartbeat_ns"] = time.time_ns() - 10_000_000_000
    _write_json(root / "aux_stream_status.json", data)
    with pytest.raises(PersistentRuntimeV25Error, match="stale live heartbeat"):
        hot.guard(token)


def test_hot_guard_rejects_inactive_binding(tmp_path: Path):
    hot, token, _, root = _fixture(tmp_path)
    (root / "ciel_binding_status").write_text("BLOCKED\n", encoding="utf-8")
    with pytest.raises(PersistentRuntimeV25Error, match="binding is not ACTIVE"):
        hot.guard(token)


def test_token_identity_is_deterministic(tmp_path: Path):
    _, token, _, _ = _fixture(tmp_path)
    assert token.token_id == token.token_id
    assert token.token_id.startswith("pncs:resident-hot-token:sha256:")
