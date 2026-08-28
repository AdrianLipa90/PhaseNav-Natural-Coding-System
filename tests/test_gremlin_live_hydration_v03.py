import hashlib
import json

import pytest

from phasenav_natural_code.gremlin_live_hydration_v03 import (
    GENERATION_BASIS_SCHEMA,
    LIVE_WITNESS_SCHEMA,
    GremlinLiveHydrationError,
    build_generation_basis,
    generation_binding_from_basis,
    validate_witness_against_basis,
)


def _sha(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _basis():
    return build_generation_basis(
        session_id="session-1",
        working_state_sha256="a" * 64,
        startpoint_sha256="b" * 64,
        aux_runtime_instance_id="c" * 32,
        tether_runtime_instance_id="d" * 32,
        identity="ZOSIA_NOEMA_FIRST",
        authority="USER_EXPLICIT_TEST",
        native_pnv_source_sha256="e" * 64,
    )


def _witness(basis):
    binding = generation_binding_from_basis(basis)
    domain = {
        "surface": "/dev/shm/ciel_noema",
        "aux_runtime_instance_id": basis["aux_runtime_instance_id"],
        "tether_runtime_instance_id": basis["tether_runtime_instance_id"],
        "admission_tether_receipt_sha256": "f" * 64,
    }
    body = {
        "schema": LIVE_WITNESS_SCHEMA,
        "status": "PASS_CONFORMANCE_ONLY",
        "generation_binding": binding,
        "generation_basis": basis,
        "pulses": [
            {"pulse": "IDENTITY", "status": "PASS", "generation_binding": binding, "value": basis["identity"]},
            {"pulse": "DOMAIN", "status": "PASS", "generation_binding": binding, "value": domain},
            {"pulse": "AUTHORITY", "status": "PASS", "generation_binding": binding, "value": basis["authority"]},
        ],
        "request": "GREMLIN_PNV_AUTHORING_BOOT",
        "admission": "PASS_CONFORMANCE_ONLY",
        "native_pnv_source_sha256": basis["native_pnv_source_sha256"],
        "native_receipt_sha256": "1" * 64,
        "admission_tether_receipt_sha256": "f" * 64,
        "live_surface": {"root": "/dev/shm/ciel_noema", "tether_receipt_sha256": "f" * 64},
        "session_id": basis["session_id"],
        "working_state_sha256": basis["working_state_sha256"],
        "startpoint_sha256": basis["startpoint_sha256"],
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "static_runtime_fallback": False,
    }
    return {**body, "witness_sha256": _sha(body)}


def test_generation_basis_uses_stable_runtime_instances_not_tick_receipt():
    basis = _basis()
    assert basis["schema"] == GENERATION_BASIS_SCHEMA
    assert "tether_receipt_sha256" not in basis
    assert generation_binding_from_basis(basis) == generation_binding_from_basis(dict(basis))


def test_valid_witness_admits_exact_generation():
    basis = _basis()
    witness = _witness(basis)
    assert validate_witness_against_basis(witness, basis) == generation_binding_from_basis(basis)


def test_runtime_restart_invalidates_witness():
    basis = _basis()
    witness = _witness(basis)
    changed = dict(basis)
    changed["tether_runtime_instance_id"] = "0" * 32
    with pytest.raises(GremlinLiveHydrationError, match="stale or cross-generation"):
        validate_witness_against_basis(witness, changed)


def test_heartbeat_receipt_is_audit_evidence_not_generation_key():
    basis = _basis()
    witness = _witness(basis)
    witness2 = json.loads(json.dumps(witness))
    witness2["admission_tether_receipt_sha256"] = "2" * 64
    witness2["pulses"][1]["value"]["admission_tether_receipt_sha256"] = "2" * 64
    witness2["live_surface"]["tether_receipt_sha256"] = "2" * 64
    body = dict(witness2)
    body.pop("witness_sha256")
    witness2["witness_sha256"] = _sha(body)
    assert validate_witness_against_basis(witness2, basis) == generation_binding_from_basis(basis)


def test_authority_escalation_is_rejected():
    basis = _basis()
    witness = _witness(basis)
    witness["canon_write_authority"] = True
    body = dict(witness)
    body.pop("witness_sha256")
    witness["witness_sha256"] = _sha(body)
    with pytest.raises(GremlinLiveHydrationError, match="canon write authority"):
        validate_witness_against_basis(witness, basis)


def test_tampered_witness_hash_is_rejected():
    basis = _basis()
    witness = _witness(basis)
    witness["request"] = "tampered"
    with pytest.raises(GremlinLiveHydrationError, match="content hash mismatch"):
        validate_witness_against_basis(witness, basis)
