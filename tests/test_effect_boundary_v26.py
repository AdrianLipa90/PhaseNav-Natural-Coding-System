from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pytest

from phasenav_natural_code.effect_v26 import (
    EFFECT_KIND_NOEMA_RUNTIME_RECORD_WRITE,
    EFFECT_TARGET_NOEMA_RUNTIME_RECORD,
    MAX_EFFECT_PAYLOAD_BYTES,
    NOEMA_RUNTIME_RECORD_ADAPTER,
    EffectAdapterDescriptor,
    EffectAuthorizationGrant,
    EffectBoundaryRuntime,
    EffectBoundaryV26Error,
    EffectRequest,
    NoemaRuntimeRecordAdapter,
    authorize_exact_request,
    make_effect_request,
    _typed_id,
)

GEN="pncs:runtime-generation:sha256:"+"1"*64
HANDLE="pncs:resident:sha256:"+"2"*64
PROGRAM="pncs:program:sha256:"+"3"*64
ADMISSION="pncs:resident-admission:sha256:"+"4"*64
RESULT="pncs:result:sha256:"+"5"*64
LINEAGE="pncs:lineage:sha256:"+"6"*64
EXEC="7"*64


def dispatch_receipt(**updates):
    body={
      "schema":"PNCS_RESIDENT_CONTROL_DISPATCH_RECEIPT_V0_25",
      "runtime_contract_id":"PNCS_PERSISTENT_RUNTIME_V0_25",
      "kernel_scope":"CONTROL_ROOT_V0_20",
      "handle_id":HANDLE,
      "program_id":PROGRAM,
      "generation_id":GEN,
      "resident_admission_id":ADMISSION,
      "execution_receipt_sha256":EXEC,
      "result_id":RESULT,
      "lineage_id":LINEAGE,
      "target":"runtime.continue",
      "branch_truth_state":"FALSE",
      "result_lineage_contract_id":"PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22",
      "process_reconstruction_required":False,
      "continuation_execution_opened":False,
      "return_execution_opened":False,
      "external_effects":False,
      "static_runtime_fallback":False,
      "deterministic_fields_only":True,
    }
    body.update(updates)
    return {**body,"dispatch_id":_typed_id("pncs:resident-dispatch",body)}

@dataclass(frozen=True)
class G:
    generation_id:str=GEN


def reader(*args, **kwargs): return G()

def runtime(tmp_path):
    r=EffectBoundaryRuntime(tmp_path,require_socket=False,require_canonical_root=False,generation_reader=reader)
    return r

def request(): return make_effect_request(dispatch_receipt(), {"event":"v0.26-conformance","value":1})

def authorized_runtime(tmp_path):
    r=runtime(tmp_path)
    r.register_adapter(NoemaRuntimeRecordAdapter())
    q=request(); g=authorize_exact_request(q,authority_id="PNCS_V0_26_CONFORMANCE_AUTHORITY")
    r.register_authorization(g)
    return r,q,g


def test_request_deterministic():
    assert request().request_id==request().request_id

def test_adapter_deterministic():
    assert NOEMA_RUNTIME_RECORD_ADAPTER.adapter_id.startswith("pncs:effect-adapter:sha256:")

def test_dispatch_digest_tamper_rejected():
    x=dispatch_receipt(); x["target"]="safety.pause"
    with pytest.raises(EffectBoundaryV26Error,match="digest mismatch"): make_effect_request(x,{"x":1})

def test_effectful_v25_origin_rejected():
    x=dispatch_receipt(external_effects=True)
    with pytest.raises(EffectBoundaryV26Error): make_effect_request(x,{"x":1})

def test_continuation_open_origin_rejected():
    x=dispatch_receipt(continuation_execution_opened=True)
    with pytest.raises(EffectBoundaryV26Error): make_effect_request(x,{"x":1})

def test_return_open_origin_rejected():
    x=dispatch_receipt(return_execution_opened=True)
    with pytest.raises(EffectBoundaryV26Error): make_effect_request(x,{"x":1})

def test_static_fallback_origin_rejected():
    x=dispatch_receipt(static_runtime_fallback=True)
    with pytest.raises(EffectBoundaryV26Error): make_effect_request(x,{"x":1})

def test_payload_too_large_rejected():
    with pytest.raises(EffectBoundaryV26Error,match="exceeds"): make_effect_request(dispatch_receipt(),{"x":"a"*(MAX_EFFECT_PAYLOAD_BYTES+1)})

def test_nonfinite_rejected():
    with pytest.raises(EffectBoundaryV26Error): make_effect_request(dispatch_receipt(),{"x":float("nan")})

def test_default_deny_without_grant(tmp_path):
    r=runtime(tmp_path); r.register_adapter(NoemaRuntimeRecordAdapter())
    with pytest.raises(EffectBoundaryV26Error,match="no explicit authorization"): r.execute(request())

def test_default_deny_without_adapter(tmp_path):
    r=runtime(tmp_path); q=request(); r.register_authorization(authorize_exact_request(q,authority_id="PNCS_TEST"))
    with pytest.raises(EffectBoundaryV26Error,match="not registered"): r.execute(q)

def test_exact_authorization_required(tmp_path):
    r=runtime(tmp_path); r.register_adapter(NoemaRuntimeRecordAdapter())
    q=request(); other=make_effect_request(dispatch_receipt(),{"event":"other"})
    r.register_authorization(authorize_exact_request(other,authority_id="PNCS_TEST"))
    with pytest.raises(EffectBoundaryV26Error,match="no explicit authorization"): r.execute(q)

def test_authorization_bound_cannot_be_smaller():
    q=request()
    with pytest.raises(EffectBoundaryV26Error): authorize_exact_request(q,authority_id="PNCS_TEST",max_payload_bytes=q.payload_size_bytes-1)

def test_ambiguous_authorization_rejected(tmp_path):
    r=runtime(tmp_path); r.register_adapter(NoemaRuntimeRecordAdapter()); q=request()
    r.register_authorization(authorize_exact_request(q,authority_id="PNCS_A"))
    r.register_authorization(authorize_exact_request(q,authority_id="PNCS_B"))
    with pytest.raises(EffectBoundaryV26Error,match="ambiguous"): r.execute(q)

def test_stale_generation_rejected(tmp_path):
    @dataclass(frozen=True)
    class X: generation_id:str="pncs:runtime-generation:sha256:"+"9"*64
    r=EffectBoundaryRuntime(tmp_path,require_socket=False,require_canonical_root=False,generation_reader=lambda *a,**k:X())
    r.register_adapter(NoemaRuntimeRecordAdapter()); q=request(); r.register_authorization(authorize_exact_request(q,authority_id="PNCS_TEST"))
    with pytest.raises(EffectBoundaryV26Error,match="stale"): r.execute(q)

def test_generation_change_before_commit_rejected(tmp_path):
    calls=[GEN,"pncs:runtime-generation:sha256:"+"9"*64]
    @dataclass(frozen=True)
    class X: generation_id:str
    def rr(*a,**k): return X(calls.pop(0) if calls else GEN)
    r=EffectBoundaryRuntime(tmp_path,require_socket=False,require_canonical_root=False,generation_reader=rr)
    r.register_adapter(NoemaRuntimeRecordAdapter()); q=request(); r.register_authorization(authorize_exact_request(q,authority_id="PNCS_TEST"))
    with pytest.raises(EffectBoundaryV26Error,match="before effect commit"): r.execute(q)

def test_successful_effect(tmp_path):
    r,q,g=authorized_runtime(tmp_path); out=r.execute(q)
    p=Path(out.receipt_path); assert p.is_file()
    assert out.receipt.request.request_id==q.request_id
    assert out.receipt.grant.authorization_id==g.authorization_id
    assert out.receipt.payload["bounded_external_effect"] is True

def test_effect_record_is_under_fixed_root(tmp_path):
    r,q,_=authorized_runtime(tmp_path); out=r.execute(q)
    rel=out.receipt.effect_relative_path
    assert rel.startswith("pncs/v0.26/effects/records/")
    assert (tmp_path/rel).is_file()

def test_exact_replay_idempotent(tmp_path):
    r,q,_=authorized_runtime(tmp_path); a=r.execute(q); b=r.execute(q)
    assert a.receipt.receipt_id==b.receipt.receipt_id
    assert Path(a.receipt_path).read_bytes()==Path(b.receipt_path).read_bytes()

def test_effect_record_tamper_rejected(tmp_path):
    r,q,_=authorized_runtime(tmp_path); a=r.execute(q)
    p=tmp_path/a.receipt.effect_relative_path; p.write_text("tamper")
    with pytest.raises(EffectBoundaryV26Error,match="collision"): r.execute(q)

def test_symlink_in_bounded_path_rejected(tmp_path):
    (tmp_path/"pncs").symlink_to(tmp_path/"elsewhere",target_is_directory=True)
    r,q,_=authorized_runtime(tmp_path)
    with pytest.raises(EffectBoundaryV26Error,match="symlink"): r.execute(q)

def test_program_cannot_supply_path():
    q=make_effect_request(dispatch_receipt(),{"path":"../../etc/passwd"})
    assert q.payload["program_supplied_path"] is False
    assert q.target==EFFECT_TARGET_NOEMA_RUNTIME_RECORD

def test_adapter_rejects_network_git_subprocess_device_open():
    with pytest.raises(EffectBoundaryV26Error):
      EffectAdapterDescriptor(EFFECT_KIND_NOEMA_RUNTIME_RECORD_WRITE,EFFECT_TARGET_NOEMA_RUNTIME_RECORD,"pncs/v0.26/effects/records",4096,network_allowed=True)

def test_wrong_target_rejected():
    q=request()
    with pytest.raises(EffectBoundaryV26Error): EffectRequest(q.origin,q.effect_kind,"other",q.adapter_id,q.payload_data)

def test_wrong_adapter_id_scope_rejected():
    q=request(); fake="pncs:effect-adapter:sha256:"+"a"*64
    q2=EffectRequest(q.origin,q.effect_kind,q.target,fake,q.payload_data)
    r=runtime(Path("/tmp")); r.register_adapter(NoemaRuntimeRecordAdapter()); r.register_authorization(authorize_exact_request(q2,authority_id="PNCS_TEST"))
    with pytest.raises(EffectBoundaryV26Error,match="not registered"): r.execute(q2)

def test_inverse_provenance_complete(tmp_path):
    r,q,_=authorized_runtime(tmp_path); out=r.execute(q)
    levels=[x["level"] for x in out.receipt.inverse_provenance]
    assert levels==["EFFECT","AUTHORIZATION","EFFECT_REQUEST","DISPATCH","RESULT","LINEAGE","PROGRAM","RESIDENT_HANDLE","RUNTIME_GENERATION"]

def test_receipt_id_deterministic(tmp_path):
    r,q,_=authorized_runtime(tmp_path); out=r.execute(q)
    assert out.receipt.receipt_id.startswith("pncs:effect-receipt:sha256:")

def test_canonical_root_required_by_default(tmp_path):
    with pytest.raises(EffectBoundaryV26Error,match="fixed"): EffectBoundaryRuntime(tmp_path,require_socket=False,generation_reader=reader)
