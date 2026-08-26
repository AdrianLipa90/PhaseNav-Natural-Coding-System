from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from .execution_v20_live import LiveSurfaceSnapshot, load_live_surface
from .execution_v20_model import DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT
from .native_pnv_exec_v01 import NativePNVExecutionResult, execute_pnv

LIVE_BRIDGE_SCHEMA = "PNCS_GREMLIN_NATIVE_PNV_LIVE_BRIDGE_V0_1"
TRIPLE_PULSE_COMPARISON_SCHEMA = "PNCS_GREMLIN_TRIPLE_PULSE_COMPARISON_V0_1"


class NativePNVLiveBridgeError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NativePNVLiveBridgeError(f"invalid required live JSON: {path}") from exc
    if not isinstance(value, dict):
        raise NativePNVLiveBridgeError(f"required live JSON is not an object: {path}")
    return value


def _require_under(root: Path, path: Path) -> Path:
    root_abs = root.resolve()
    path_abs = path.resolve()
    try:
        path_abs.relative_to(root_abs)
    except ValueError as exc:
        raise NativePNVLiveBridgeError(f"path escapes live surface: {path}") from exc
    return path_abs


def _live_payload(live: LiveSurfaceSnapshot) -> dict[str, Any]:
    return {"schema": LIVE_BRIDGE_SCHEMA, **live.receipt_payload}


@dataclass(frozen=True)
class TriplePulseNativeRun:
    result: NativePNVExecutionResult
    generation_binding: str
    projection: Mapping[str, Any]


@dataclass(frozen=True)
class BelzebubNativeRun:
    result: NativePNVExecutionResult
    current: Mapping[str, Any]


def execute_gremlin_triple_pulse(
    pnv_text: str,
    *,
    identity: str,
    authority: str,
    domain: Mapping[str, Any],
    request: str,
    generation_binding: str,
    live_payload: Mapping[str, Any],
) -> TriplePulseNativeRun:
    if not identity or not authority or not request or not generation_binding:
        raise NativePNVLiveBridgeError("triple-pulse identity, authority, request, and generation binding are required")
    if domain.get("surface") != "/dev/shm/ciel_noema":
        raise NativePNVLiveBridgeError("triple-pulse domain must bind /dev/shm/ciel_noema")
    if live_payload.get("root") != "/dev/shm/ciel_noema":
        raise NativePNVLiveBridgeError("live payload is not bound to canonical NOEMA surface")

    pulse_receipts = (
        {"pulse": "IDENTITY", "status": "PASS", "generation_binding": generation_binding, "value": identity},
        {"pulse": "DOMAIN", "status": "PASS", "generation_binding": generation_binding, "value": dict(domain)},
        {"pulse": "AUTHORITY", "status": "PASS", "generation_binding": generation_binding, "value": authority},
    )

    def admitted_request_candidate(value: Any) -> dict[str, Any]:
        return {"request": value, "admitted": True, "generation_binding": generation_binding}

    def current_live_coupling(order: Any) -> dict[str, Any]:
        return {
            "order": order,
            "generation_binding": generation_binding,
            "pulse_receipts": [dict(x) for x in pulse_receipts],
            "live_surface": dict(live_payload),
        }

    def three_pulse_receipts_same_generation(value: Any) -> bool:
        if not isinstance(value, list) or len(value) != 2:
            return False
        request_candidate, coupling = value
        if not isinstance(request_candidate, dict) or not isinstance(coupling, dict):
            return False
        receipts = coupling.get("pulse_receipts")
        if not isinstance(receipts, list) or len(receipts) != 3:
            return False
        return (
            request_candidate.get("admitted") is True
            and request_candidate.get("generation_binding") == generation_binding
            and coupling.get("generation_binding") == generation_binding
            and all(
                isinstance(r, dict)
                and r.get("status") == "PASS"
                and r.get("generation_binding") == generation_binding
                for r in receipts
            )
        )

    result = execute_pnv(
        pnv_text,
        sources={
            "current.identity": identity,
            "verified_identity": True,
            "current.domain": dict(domain),
            "verified_domain": True,
            "current.authority": authority,
            "verified_authority": True,
            "user.request": request,
        },
        comparators={"three_pulse_receipts_same_generation": three_pulse_receipts_same_generation},
        transforms={
            "admitted_request_candidate": admitted_request_candidate,
            "current_live_coupling": current_live_coupling,
        },
    )
    if result.emitted.get("TP.ADMISSION.RETURN") is not True:
        raise NativePNVLiveBridgeError("native triple-pulse execution did not admit")
    projection = {
        "identity": identity,
        "domain": dict(domain),
        "authority": authority,
        "request": request,
        "generation_binding": generation_binding,
        "admission": True,
    }
    return TriplePulseNativeRun(result=result, generation_binding=generation_binding, projection=projection)


def execute_gremlin_triple_pulse_live(
    pnv_text: str,
    *,
    request: str,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
) -> TriplePulseNativeRun:
    root = Path(surface_root)
    live = load_live_surface(root, socket_path=socket_path, require_socket=True, max_heartbeat_age_s=max_heartbeat_age_s)
    current_memory = _read_json(_require_under(root, root / "current_memory.json"))
    witness = _read_json(_require_under(root, root / "gremlin/state/triple_pulse_conformance_witness.json"))
    identity = str(current_memory.get("identity", ""))
    authority = str(current_memory.get("authority", ""))
    generation_binding = str(witness.get("generation_binding", ""))
    domain = {"surface": str(root), "tether_receipt_sha256": live.tether_receipt_sha256}
    return execute_gremlin_triple_pulse(
        pnv_text,
        identity=identity,
        authority=authority,
        domain=domain,
        request=request,
        generation_binding=generation_binding,
        live_payload=_live_payload(live),
    )


def compare_triple_pulse_harness(native: TriplePulseNativeRun, harness: Mapping[str, Any]) -> dict[str, Any]:
    pulses = harness.get("pulses")
    if not isinstance(pulses, list) or len(pulses) != 3:
        raise NativePNVLiveBridgeError("harness witness has invalid pulse set")
    harness_projection = {
        "identity": pulses[0].get("value"),
        "domain_surface": pulses[1].get("value", {}).get("surface") if isinstance(pulses[1].get("value"), dict) else None,
        "authority": pulses[2].get("value"),
        "request": harness.get("request"),
        "generation_binding": harness.get("generation_binding"),
        "admission": harness.get("admission") == "PASS_CONFORMANCE_ONLY",
    }
    native_projection = {
        "identity": native.projection.get("identity"),
        "domain_surface": native.projection.get("domain", {}).get("surface") if isinstance(native.projection.get("domain"), dict) else None,
        "authority": native.projection.get("authority"),
        "request": native.projection.get("request"),
        "generation_binding": native.projection.get("generation_binding"),
        "admission": native.projection.get("admission"),
    }
    exact_projection_match = native_projection == harness_projection
    payload = {
        "schema": TRIPLE_PULSE_COMPARISON_SCHEMA,
        "comparison_mode": "EXACT_CANONICAL_SEMANTIC_PROJECTION",
        "native_projection": native_projection,
        "harness_projection": harness_projection,
        "exact_projection_match": exact_projection_match,
        "native_receipt_sha256": native.result.receipt["receipt_sha256"],
        "harness_sha256": _sha256(dict(harness)),
        "receipt_bytes_equal": False,
        "receipt_bytes_equal_reason": "schemas differ: native executor receipt and legacy harness witness are distinct provenance objects",
    }
    return {**payload, "comparison_sha256": _sha256(payload)}


def execute_belzebub(
    pnv_text: str,
    *,
    current: Mapping[str, Any],
    quarantine: Mapping[str, Any],
    baseline: Mapping[str, Any],
    live_payload: Mapping[str, Any],
    defensive_semantic_digest: Callable[[Any], Any],
) -> BelzebubNativeRun:
    expected_object_sha = str(current.get("object_sha256", ""))
    actual_object_sha = str(quarantine.get("object_sha256", ""))
    content_addressed = bool(expected_object_sha and expected_object_sha == actual_object_sha)
    result = execute_pnv(
        pnv_text,
        sources={
            "/dev/shm/ciel_noema": dict(live_payload),
            "/dev/shm/ciel_noema/gremlin/tools/belzebub/meta/CURRENT.json": dict(current),
            "belzebub.quarantine.object": dict(quarantine),
            "content_addressed_quarantine": content_addressed,
            "verified_semantic_baseline": dict(baseline),
        },
        comparators={"invariant_violation": lambda delta: isinstance(delta, dict) and delta.get("equal") is False},
        transforms={"defensive_semantic_digest": defensive_semantic_digest},
    )
    return BelzebubNativeRun(result=result, current=dict(current))


def execute_belzebub_live(
    pnv_text: str,
    *,
    baseline: Mapping[str, Any],
    defensive_semantic_digest: Callable[[Any], Any],
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
) -> BelzebubNativeRun:
    root = Path(surface_root)
    live = load_live_surface(root, socket_path=socket_path, require_socket=True, max_heartbeat_age_s=max_heartbeat_age_s)
    current = _read_json(_require_under(root, root / "gremlin/tools/belzebub/meta/CURRENT.json"))
    object_sha = str(current.get("object_sha256", ""))
    if len(object_sha) != 64 or any(ch not in "0123456789abcdef" for ch in object_sha):
        raise NativePNVLiveBridgeError("BELZEBUB CURRENT does not expose a valid object SHA-256")
    quarantine = _read_json(_require_under(root, root / f"gremlin/tools/belzebub/objects/{object_sha}.json"))
    return execute_belzebub(
        pnv_text,
        current=current,
        quarantine=quarantine,
        baseline=baseline,
        live_payload=_live_payload(live),
        defensive_semantic_digest=defensive_semantic_digest,
    )
