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


SESSION = "chat-test-session"
WORKING_SHA = "1" * 64
STARTPOINT_SHA = "2" * 64
PNV_SHA = "3" * 64
AUX_INSTANCE = "4" * 32
TETHER_INSTANCE = "5" * 32
IDENTITY = "ZOSIA_NOEMA_FIRST"
AUTHORITY = "USER_EXPLICIT_TEST"


def _sha256(value):
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _basis(**overrides):
    values = {
        "session_id": SESSION,
        "working_state_sha256": WORKING_SHA,
        "startpoint_sha256": STARTPOINT_SHA,
        "aux_runtime_instance_id": AUX_INSTANCE,
        "tether_runtime_instance_id": TETHER_INSTANCE,
        "identity": IDENTITY,
        "authority": AUTHORITY,
        "native_pnv_source_sha256": PNV_SHA,
    }
    values.update(overrides)
    return build_generation_basis(**values)


def _witness(basis, *, admission_receipt):
    generation = generation_binding_from_basis(basis)
    domain = {
        "surface": "/dev/shm/ciel_noema",
        "aux_runtime_instance_id": basis["aux_runtime_instance_id"],
        "tether_runtime_instance_id": basis["tether_runtime_instance_id"],
        "admission_tether_receipt_sha256": admission_receipt,
    }
    body = {
        "schema": LIVE_WITNESS_SCHEMA,
        "status": "PASS_CONFORMANCE_ONLY",
        "generation_binding": generation,
        "generation_basis": basis,
        "pulses": [
            {
                "pulse": "IDENTITY",
                "status": "PASS",
                "generation_binding": generation,
                "value": basis["identity"],
            },
            {
                "pulse": "DOMAIN",
                "status": "PASS",
                "generation_binding": generation,
                "value": domain,
            },
            {
                "pulse": "AUTHORITY",
                "status": "PASS",
                "generation_binding": generation,
                "value": basis["authority"],
            },
        ],
        "request": "GREMLIN_PNV_AUTHORING_BOOT",
        "admission": "PASS_CONFORMANCE_ONLY",
        "native_pnv_source_sha256": basis["native_pnv_source_sha256"],
        "native_receipt_sha256": "6" * 64,
        "admission_tether_receipt_sha256": admission_receipt,
        "live_surface": {
            "root": "/dev/shm/ciel_noema",
            "tether_receipt_sha256": admission_receipt,
        },
        "session_id": basis["session_id"],
        "working_state_sha256": basis["working_state_sha256"],
        "startpoint_sha256": basis["startpoint_sha256"],
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "static_runtime_fallback": False,
    }
    return {**body, "witness_sha256": _sha256(body)}


def test_generation_basis_uses_stable_runtime_instances_not_heartbeat_receipt():
    basis = _basis()
    assert basis["schema"] == GENERATION_BASIS_SCHEMA

    first = _witness(basis, admission_receipt="7" * 64)
    second = _witness(basis, admission_receipt="8" * 64)

    assert first["admission_tether_receipt_sha256"] != second["admission_tether_receipt_sha256"]
    assert first["generation_binding"] == second["generation_binding"]
    assert validate_witness_against_basis(first, basis) == first["generation_binding"]
    assert validate_witness_against_basis(second, basis) == second["generation_binding"]


def test_runtime_instance_change_invalidates_existing_witness_fail_closed():
    basis = _basis()
    witness = _witness(basis, admission_receipt="7" * 64)
    restarted_basis = _basis(tether_runtime_instance_id="9" * 32)

    with pytest.raises(GremlinLiveHydrationError, match="stale or cross-generation"):
        validate_witness_against_basis(witness, restarted_basis)


def test_aux_runtime_instance_change_invalidates_existing_witness_fail_closed():
    basis = _basis()
    witness = _witness(basis, admission_receipt="7" * 64)
    restarted_basis = _basis(aux_runtime_instance_id="a" * 32)

    with pytest.raises(GremlinLiveHydrationError, match="stale or cross-generation"):
        validate_witness_against_basis(witness, restarted_basis)


def test_generation_basis_rejects_missing_or_malformed_runtime_instance_ids():
    with pytest.raises(GremlinLiveHydrationError, match="aux_runtime_instance_id"):
        _basis(aux_runtime_instance_id="not-an-instance")
    with pytest.raises(GremlinLiveHydrationError, match="tether_runtime_instance_id"):
        _basis(tether_runtime_instance_id="")


def test_witness_cannot_claim_execution_or_canon_authority():
    basis = _basis()
    witness = _witness(basis, admission_receipt="7" * 64)
    witness["runtime_execution_authority"] = True
    body = dict(witness)
    body.pop("witness_sha256")
    witness["witness_sha256"] = _sha256(body)

    with pytest.raises(GremlinLiveHydrationError, match="runtime execution authority"):
        validate_witness_against_basis(witness, basis)
