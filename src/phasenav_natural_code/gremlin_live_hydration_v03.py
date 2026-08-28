from __future__ import annotations

"""Generation-bound GREMLIN live hydration for native PNV authoring.

The live witness is derived only from the current /dev/shm/ciel_noema runtime,
a VERIFIED startpoint, current working-state generation, fresh tether receipt,
current identity/authority and the exact native GREMLIN triple-pulse PNV bytes.
Historical/repository receipts are provenance only and are never accepted as a
current live witness.
"""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping

from .execution_v20_live import LiveSurfaceSnapshot, load_live_surface
from .execution_v20_model import DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT
from .gremlin_native_pnv_bridge_v01 import (
    LIVE_BRIDGE_SCHEMA,
    NativePNVLiveBridgeError,
    TriplePulseNativeRun,
    execute_gremlin_triple_pulse,
)
from .gremlin_pnv_authoring_v02 import (
    GremlinPNVAuthoringError,
    GremlinPNVAuthoringSession,
)

LIVE_WITNESS_SCHEMA = "PNCS_GREMLIN_TRIPLE_PULSE_LIVE_WITNESS_V0_3"
GENERATION_BASIS_SCHEMA = "PNCS_GREMLIN_LIVE_GENERATION_BASIS_V0_3"
DEFAULT_AUTHORING_RELATIVE_ROOT = Path("gremlin/candidates/pncs")
DEFAULT_WITNESS_RELATIVE_PATH = Path("gremlin/state/triple_pulse_conformance_witness.json")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class GremlinLiveHydrationError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GremlinLiveHydrationError(f"invalid required live JSON: {path}") from exc
    if not isinstance(value, dict):
        raise GremlinLiveHydrationError(f"required live JSON is not an object: {path}")
    return value


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temp.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, path)


def _require_digest(value: Any, label: str) -> str:
    text = str(value or "")
    if not _DIGEST_RE.fullmatch(text):
        raise GremlinLiveHydrationError(f"{label} is not a valid SHA-256")
    return text


def build_generation_basis(
    *,
    session_id: str,
    working_state_sha256: str,
    startpoint_sha256: str,
    tether_receipt_sha256: str,
    identity: str,
    authority: str,
    native_pnv_source_sha256: str,
) -> dict[str, str]:
    if not session_id or not identity or not authority:
        raise GremlinLiveHydrationError("session identity/authority binding is incomplete")
    return {
        "schema": GENERATION_BASIS_SCHEMA,
        "surface": str(DEFAULT_SURFACE_ROOT),
        "session_id": session_id,
        "working_state_sha256": _require_digest(working_state_sha256, "working_state_sha256"),
        "startpoint_sha256": _require_digest(startpoint_sha256, "startpoint_sha256"),
        "tether_receipt_sha256": _require_digest(tether_receipt_sha256, "tether_receipt_sha256"),
        "identity": identity,
        "authority": authority,
        "native_pnv_source_sha256": _require_digest(native_pnv_source_sha256, "native_pnv_source_sha256"),
    }


def generation_binding_from_basis(basis: Mapping[str, Any]) -> str:
    if basis.get("schema") != GENERATION_BASIS_SCHEMA:
        raise GremlinLiveHydrationError("unexpected GREMLIN generation-basis schema")
    return _sha256(dict(basis))


def validate_witness_against_basis(
    witness: Mapping[str, Any],
    expected_basis: Mapping[str, Any],
) -> str:
    if witness.get("schema") != LIVE_WITNESS_SCHEMA:
        raise GremlinLiveHydrationError("unexpected GREMLIN live-witness schema")
    if witness.get("status") != "PASS_CONFORMANCE_ONLY":
        raise GremlinLiveHydrationError("GREMLIN live witness is not PASS_CONFORMANCE_ONLY")
    if witness.get("runtime_execution_authority") is not False:
        raise GremlinLiveHydrationError("GREMLIN witness claims runtime execution authority")
    if witness.get("canon_write_authority") is not False:
        raise GremlinLiveHydrationError("GREMLIN witness claims canon write authority")
    if witness.get("static_runtime_fallback") is not False:
        raise GremlinLiveHydrationError("GREMLIN witness claims a static runtime fallback")

    stored_basis = witness.get("generation_basis")
    if not isinstance(stored_basis, dict) or stored_basis != dict(expected_basis):
        raise GremlinLiveHydrationError("GREMLIN live witness is stale or cross-generation")
    expected_binding = generation_binding_from_basis(expected_basis)
    if witness.get("generation_binding") != expected_binding:
        raise GremlinLiveHydrationError("GREMLIN generation binding does not match current live basis")

    pulses = witness.get("pulses")
    if not isinstance(pulses, list) or len(pulses) != 3:
        raise GremlinLiveHydrationError("GREMLIN live witness does not contain exactly three boot pulses")
    expected_pulses = ("IDENTITY", "DOMAIN", "AUTHORITY")
    for index, pulse_name in enumerate(expected_pulses):
        pulse = pulses[index]
        if (
            not isinstance(pulse, dict)
            or pulse.get("pulse") != pulse_name
            or pulse.get("status") != "PASS"
            or pulse.get("generation_binding") != expected_binding
        ):
            raise GremlinLiveHydrationError(f"GREMLIN {pulse_name} pulse is invalid or cross-generation")

    witness_body = dict(witness)
    witness_sha256 = witness_body.pop("witness_sha256", None)
    if witness_sha256 != _sha256(witness_body):
        raise GremlinLiveHydrationError("GREMLIN live witness content hash mismatch")
    return expected_binding


def _current_binding(
    root: Path,
    live: LiveSurfaceSnapshot,
    *,
    native_pnv_source_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, str]]:
    current_memory = _read_json(root / "current_memory.json")
    working_state = _read_json(root / "working_state.json")
    startpoint = _read_json(root / "session/startpoint.json")

    identity = str(current_memory.get("identity", ""))
    authority = str(current_memory.get("authority", ""))
    session_id = str(working_state.get("session_id", ""))
    working_state_sha256 = str(working_state.get("working_state_sha256", ""))
    if working_state.get("working_state") != "ACTIVE" and working_state.get("status") != "ACTIVE":
        raise GremlinLiveHydrationError("GREMLIN hydration requires ACTIVE working state")
    if startpoint.get("status") != "VERIFIED":
        raise GremlinLiveHydrationError("GREMLIN hydration requires a VERIFIED session startpoint")
    startpoint_sha256 = str(startpoint.get("packet_sha256", ""))

    basis = build_generation_basis(
        session_id=session_id,
        working_state_sha256=working_state_sha256,
        startpoint_sha256=startpoint_sha256,
        tether_receipt_sha256=live.tether_receipt_sha256,
        identity=identity,
        authority=authority,
        native_pnv_source_sha256=native_pnv_source_sha256,
    )
    return current_memory, working_state, startpoint, basis


@dataclass(frozen=True)
class GremlinLiveHydration:
    witness: Mapping[str, Any]
    native_run: TriplePulseNativeRun
    witness_path: Path


def hydrate_gremlin_pnv_live(
    pnv_text: str,
    *,
    request: str = "GREMLIN_PNV_AUTHORING_BOOT",
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
) -> GremlinLiveHydration:
    root = Path(surface_root)
    if root != DEFAULT_SURFACE_ROOT:
        raise GremlinLiveHydrationError("GREMLIN live hydration must bind /dev/shm/ciel_noema")
    if not pnv_text.strip():
        raise GremlinLiveHydrationError("native GREMLIN triple-pulse PNV source is required")

    live = load_live_surface(
        root,
        socket_path=socket_path,
        require_socket=True,
        max_heartbeat_age_s=max_heartbeat_age_s,
    )
    native_source_sha256 = _sha256_text(pnv_text)
    current_memory, working_state, startpoint, basis = _current_binding(
        root,
        live,
        native_pnv_source_sha256=native_source_sha256,
    )
    generation_binding = generation_binding_from_basis(basis)
    identity = str(current_memory["identity"])
    authority = str(current_memory["authority"])
    domain = {
        "surface": str(root),
        "tether_receipt_sha256": live.tether_receipt_sha256,
    }

    try:
        native_run = execute_gremlin_triple_pulse(
            pnv_text,
            identity=identity,
            authority=authority,
            domain=domain,
            request=request,
            generation_binding=generation_binding,
            live_payload={"schema": LIVE_BRIDGE_SCHEMA, **live.receipt_payload},
        )
    except NativePNVLiveBridgeError as exc:
        raise GremlinLiveHydrationError(f"native GREMLIN triple-pulse execution blocked: {exc}") from exc

    pulses = [
        {"pulse": "IDENTITY", "status": "PASS", "generation_binding": generation_binding, "value": identity},
        {"pulse": "DOMAIN", "status": "PASS", "generation_binding": generation_binding, "value": domain},
        {"pulse": "AUTHORITY", "status": "PASS", "generation_binding": generation_binding, "value": authority},
    ]
    body: dict[str, Any] = {
        "schema": LIVE_WITNESS_SCHEMA,
        "status": "PASS_CONFORMANCE_ONLY",
        "generation_binding": generation_binding,
        "generation_basis": basis,
        "pulses": pulses,
        "request": request,
        "admission": "PASS_CONFORMANCE_ONLY",
        "native_pnv_source_sha256": native_source_sha256,
        "native_receipt_sha256": str(native_run.result.receipt["receipt_sha256"]),
        "live_surface": dict(live.receipt_payload),
        "session_id": str(working_state["session_id"]),
        "working_state_sha256": str(working_state["working_state_sha256"]),
        "startpoint_sha256": str(startpoint["packet_sha256"]),
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "static_runtime_fallback": False,
    }
    witness = {**body, "witness_sha256": _sha256(body)}
    witness_path = root / DEFAULT_WITNESS_RELATIVE_PATH
    _atomic_json(witness_path, witness)
    (root / DEFAULT_AUTHORING_RELATIVE_ROOT).mkdir(parents=True, exist_ok=True)
    return GremlinLiveHydration(
        witness=witness,
        native_run=native_run,
        witness_path=witness_path,
    )


def open_verified_gremlin_pnv_authoring_live(
    pnv_text: str,
    *,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
) -> GremlinPNVAuthoringSession:
    root = Path(surface_root)
    if root != DEFAULT_SURFACE_ROOT:
        raise GremlinPNVAuthoringError("live GREMLIN authoring must bind /dev/shm/ciel_noema")
    if not pnv_text.strip():
        raise GremlinPNVAuthoringError("exact native GREMLIN triple-pulse PNV source is required")

    live = load_live_surface(
        root,
        socket_path=socket_path,
        require_socket=True,
        max_heartbeat_age_s=max_heartbeat_age_s,
    )
    witness = _read_json(root / DEFAULT_WITNESS_RELATIVE_PATH)
    native_source_sha256 = _sha256_text(pnv_text)
    if witness.get("native_pnv_source_sha256") != native_source_sha256:
        raise GremlinPNVAuthoringError("GREMLIN witness is not bound to the supplied native PNV source")

    current_memory, _working_state, _startpoint, expected_basis = _current_binding(
        root,
        live,
        native_pnv_source_sha256=native_source_sha256,
    )
    try:
        generation_binding = validate_witness_against_basis(witness, expected_basis)
    except GremlinLiveHydrationError as exc:
        raise GremlinPNVAuthoringError(str(exc)) from exc

    identity = str(current_memory.get("identity", ""))
    authority = str(current_memory.get("authority", ""))
    if not identity or not authority:
        raise GremlinPNVAuthoringError("live GREMLIN authoring identity/authority binding is incomplete")
    authoring_root = root / DEFAULT_AUTHORING_RELATIVE_ROOT
    authoring_root.mkdir(parents=True, exist_ok=True)
    return GremlinPNVAuthoringSession(
        surface_root=root,
        authoring_root=authoring_root,
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        tether_receipt_sha256=live.tether_receipt_sha256,
    )
