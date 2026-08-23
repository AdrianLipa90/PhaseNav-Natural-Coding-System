from __future__ import annotations

from dataclasses import replace

import pytest

from phasenav_natural_code.effect_v26 import (
    EFFECT_KIND_NOEMA_RUNTIME_RECORD_WRITE,
    EFFECT_TARGET_NOEMA_RUNTIME_RECORD,
    MAX_EFFECT_PAYLOAD_BYTES,
    NOEMA_RUNTIME_RECORD_ADAPTER,
    EffectAdapterDescriptor,
    EffectAdapterRegistry,
    EffectAuthorizationGrant,
    EffectAuthorizationRegistry,
    EffectBoundaryV26Error,
    EffectRequest,
    authorize_exact_request,
    make_effect_request,
    _typed_id,
)

GEN = "pncs:runtime-generation:sha256:" + "1" * 64
GEN_OTHER = "pncs:runtime-generation:sha256:" + "9" * 64
HANDLE = "pncs:resident:sha256:" + "2" * 64
PROGRAM = "pncs:program:sha256:" + "3" * 64
ADMISSION = "pncs:resident-admission:sha256:" + "4" * 64
RESULT = "pncs:result:sha256:" + "5" * 64
LINEAGE = "pncs:lineage:sha256:" + "6" * 64
EXEC = "7" * 64
FAKE_ADAPTER = "pncs:effect-adapter:sha256:" + "a" * 64
FAKE_REQUEST = "pncs:effect-request:sha256:" + "b" * 64


def dispatch_receipt(generation_id=GEN):
    body = {
        "schema": "PNCS_RESIDENT_CONTROL_DISPATCH_RECEIPT_V0_25",
        "runtime_contract_id": "PNCS_PERSISTENT_RUNTIME_V0_25",
        "kernel_scope": "CONTROL_ROOT_V0_20",
        "handle_id": HANDLE,
        "program_id": PROGRAM,
        "generation_id": generation_id,
        "resident_admission_id": ADMISSION,
        "execution_receipt_sha256": EXEC,
        "result_id": RESULT,
        "lineage_id": LINEAGE,
        "target": "runtime.continue",
        "branch_truth_state": "FALSE",
        "result_lineage_contract_id": "PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22",
        "process_reconstruction_required": False,
        "continuation_execution_opened": False,
        "return_execution_opened": False,
        "external_effects": False,
        "static_runtime_fallback": False,
        "deterministic_fields_only": True,
    }
    return {**body, "dispatch_id": _typed_id("pncs:resident-dispatch", body)}


def request(payload=None):
    return make_effect_request(dispatch_receipt(), payload or {"event": "v0.28-authority", "value": 1})


def grant(q=None, **updates):
    q = q or request()
    values = {
        "request_id": q.request_id,
        "generation_id": q.origin.generation_id,
        "adapter_id": q.adapter_id,
        "authority_id": "PNCS_V0_28_ADVERSARIAL_AUTHORITY",
        "effect_kind": q.effect_kind,
        "target": q.target,
        "max_payload_bytes": MAX_EFFECT_PAYLOAD_BYTES,
    }
    values.update(updates)
    return EffectAuthorizationGrant(**values)


def test_exact_request_grant_resolves():
    q = request()
    registry = EffectAuthorizationRegistry()
    g = registry.register(grant(q))
    assert registry.exact_grant(q).authorization_id == g.authorization_id


def test_payload_substitution_invalidates_old_grant():
    q = request()
    q2 = request({"event": "v0.28-authority", "value": 2})
    assert q.request_id != q2.request_id
    registry = EffectAuthorizationRegistry()
    registry.register(grant(q))
    with pytest.raises(EffectBoundaryV26Error, match="no explicit authorization"):
        registry.exact_grant(q2)


def test_origin_generation_substitution_invalidates_old_grant():
    q = request()
    q2_origin = replace(q.origin, generation_id=GEN_OTHER)
    q2 = EffectRequest(q2_origin, q.effect_kind, q.target, q.adapter_id, q.payload_data)
    registry = EffectAuthorizationRegistry()
    registry.register(grant(q))
    with pytest.raises(EffectBoundaryV26Error, match="no explicit authorization"):
        registry.exact_grant(q2)


def test_grant_generation_substitution_rejected():
    q = request()
    registry = EffectAuthorizationRegistry()
    registry.register(grant(q, generation_id=GEN_OTHER))
    with pytest.raises(EffectBoundaryV26Error, match="generation mismatch"):
        registry.exact_grant(q)


def test_request_adapter_substitution_invalidates_old_grant():
    q = request()
    q2 = EffectRequest(q.origin, q.effect_kind, q.target, FAKE_ADAPTER, q.payload_data)
    registry = EffectAuthorizationRegistry()
    registry.register(grant(q))
    with pytest.raises(EffectBoundaryV26Error, match="no explicit authorization"):
        registry.exact_grant(q2)


def test_grant_adapter_substitution_rejected():
    q = request()
    registry = EffectAuthorizationRegistry()
    registry.register(grant(q, adapter_id=FAKE_ADAPTER))
    with pytest.raises(EffectBoundaryV26Error, match="scope mismatch"):
        registry.exact_grant(q)


def test_grant_request_id_substitution_rejected():
    q = request()
    registry = EffectAuthorizationRegistry()
    registry.register(grant(q, request_id=FAKE_REQUEST))
    with pytest.raises(EffectBoundaryV26Error, match="no explicit authorization"):
        registry.exact_grant(q)


def test_payload_bound_substitution_rejected():
    q = request({"event": "v0.28-authority", "value": "abcdef"})
    registry = EffectAuthorizationRegistry()
    registry.register(grant(q, max_payload_bytes=q.payload_size_bytes - 1))
    with pytest.raises(EffectBoundaryV26Error, match="exceeds authorization bound"):
        registry.exact_grant(q)


def test_ambiguous_authority_substitution_rejected():
    q = request()
    registry = EffectAuthorizationRegistry()
    registry.register(grant(q, authority_id="PNCS_V0_28_AUTHORITY_A"))
    registry.register(grant(q, authority_id="PNCS_V0_28_AUTHORITY_B"))
    with pytest.raises(EffectBoundaryV26Error, match="ambiguous"):
        registry.exact_grant(q)


def test_request_payload_mapping_order_is_equivalent():
    a = request({"alpha": 1, "beta": 2, "gamma": 3})
    b = request({"gamma": 3, "beta": 2, "alpha": 1})
    assert a.request_id == b.request_id
    assert a.payload_sha256 == b.payload_sha256


def test_authorization_identity_is_deterministic():
    q = request()
    assert grant(q).authorization_id == grant(q).authorization_id


def test_authority_identity_change_changes_grant_identity():
    q = request()
    a = grant(q, authority_id="PNCS_V0_28_AUTHORITY_A")
    b = grant(q, authority_id="PNCS_V0_28_AUTHORITY_B")
    assert a.authorization_id != b.authorization_id


def test_unregistered_fake_adapter_id_rejected():
    registry = EffectAdapterRegistry()
    with pytest.raises(EffectBoundaryV26Error, match="not registered"):
        registry.adapter(FAKE_ADAPTER)


def test_dangerous_network_adapter_substitution_rejected():
    with pytest.raises(EffectBoundaryV26Error):
        EffectAdapterDescriptor(
            EFFECT_KIND_NOEMA_RUNTIME_RECORD_WRITE,
            EFFECT_TARGET_NOEMA_RUNTIME_RECORD,
            "pncs/v0.26/effects/records",
            MAX_EFFECT_PAYLOAD_BYTES,
            network_allowed=True,
        )


def test_dangerous_git_adapter_substitution_rejected():
    with pytest.raises(EffectBoundaryV26Error):
        EffectAdapterDescriptor(
            EFFECT_KIND_NOEMA_RUNTIME_RECORD_WRITE,
            EFFECT_TARGET_NOEMA_RUNTIME_RECORD,
            "pncs/v0.26/effects/records",
            MAX_EFFECT_PAYLOAD_BYTES,
            git_allowed=True,
        )


def test_program_path_remains_payload_not_authority():
    q = request({"path": "../../etc/passwd", "event": "path-injection"})
    assert q.target == EFFECT_TARGET_NOEMA_RUNTIME_RECORD
    assert q.adapter_id == NOEMA_RUNTIME_RECORD_ADAPTER.adapter_id
    assert q.payload["program_supplied_path"] is False


def test_target_substitution_rejected_at_construction():
    q = request()
    with pytest.raises(EffectBoundaryV26Error):
        EffectRequest(q.origin, q.effect_kind, "other.target", q.adapter_id, q.payload_data)


def test_effect_kind_substitution_rejected_at_construction():
    q = request()
    with pytest.raises(EffectBoundaryV26Error):
        EffectRequest(q.origin, "NETWORK_WRITE", q.target, q.adapter_id, q.payload_data)


def test_deny_grant_cannot_enter_registry():
    q = request()
    with pytest.raises(EffectBoundaryV26Error):
        grant(q, decision="DENY")


def test_delegating_grant_rejected():
    q = request()
    with pytest.raises(EffectBoundaryV26Error):
        grant(q, no_delegation=False)


def test_non_exact_grant_rejected():
    q = request()
    with pytest.raises(EffectBoundaryV26Error):
        grant(q, exact_request_only=False)


def test_lowercase_authority_id_rejected():
    q = request()
    with pytest.raises(EffectBoundaryV26Error):
        grant(q, authority_id="pncs_lowercase_authority")


def test_generation_substitution_changes_request_identity():
    a = make_effect_request(dispatch_receipt(GEN), {"event": "same"})
    b = make_effect_request(dispatch_receipt(GEN_OTHER), {"event": "same"})
    assert a.request_id != b.request_id
    assert a.origin.generation_id != b.origin.generation_id


def test_exact_authorize_helper_binds_request_generation_and_adapter():
    q = request()
    g = authorize_exact_request(q, authority_id="PNCS_V0_28_HELPER_AUTHORITY")
    assert g.request_id == q.request_id
    assert g.generation_id == q.origin.generation_id
    assert g.adapter_id == q.adapter_id
