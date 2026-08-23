from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import time
from types import SimpleNamespace

import pytest


from phasenav_natural_code import runtime_v25 as v25

PROGRAM_ID = 'pncs:program:sha256:572660a1046975c57e01f7e402677f1e4ca845e51bca1bee6517e0d86b35c4d7'
COMPOSITION_ID = 'pncs:composition:sha256:5b3710e6c8bf34d3754e7144ca139beb70205ea20b2fa504ef63c710c177cd57'
CONTROL_DEF = 'pncs:def:sha256:b7988497bab75a526771fa24aeca75e0182bd437fd707927cb0e78b04d360cce'
SCHEDULE_SHA = '9c5ffbc4ed236144df9e0bff86c738536bbbc430e55e77de69af915ca17324c0'

PNV = '''PNV 1
PNCS PROGRAM_UNIT 0.24
EPISTEMIC CHYBA
MODE READ_ONLY
PROGRAM_ID pncs:program:sha256:572660a1046975c57e01f7e402677f1e4ca845e51bca1bee6517e0d86b35c4d7
COMPOSITION_ID pncs:composition:sha256:5b3710e6c8bf34d3754e7144ca139beb70205ea20b2fa504ef63c710c177cd57
COMPOSITION_CONTRACT PNCS_NATURAL_PROGRAM_COMPOSITION_V0_23
COMPOSITION_PAYLOAD_SHA256 5b3710e6c8bf34d3754e7144ca139beb70205ea20b2fa504ef63c710c177cd57
COMPOSITION_GRAPH_SHA256 4669cb73f7df2e14f70fdefb014889a3702b72c43074d111316979c49ed670c3
DEPENDENCY_CLOSURE_SHA256 e0970a0d4825ca30dd1d76b706ab90565d889a5dc9957b8ade395d32a23aae65
DEPENDENCY_OCCURRENCES_SHA256 0f07128ae1af087db4d75e479c36defc6ca305fd1224edb15a30364e3bc913da
OPERATOR_SCHEDULE_SHA256 9c5ffbc4ed236144df9e0bff86c738536bbbc430e55e77de69af915ca17324c0
LINEAGE_CONTRACT PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22
DEPENDENCY 000 COMPOSITION pncs:composition:sha256:5b3710e6c8bf34d3754e7144ca139beb70205ea20b2fa504ef63c710c177cd57
DEPENDENCY 001 CONTROL_DEFINITION pncs:def:sha256:b7988497bab75a526771fa24aeca75e0182bd437fd707927cb0e78b04d360cce
DEPENDENCY 002 ROUTE_REF pncs:route-ref:sha256:3ad27bd2e71cd88f1c822792bd9392f10ef3f096e951badb7f79b8d9f45e0a63
DEPENDENCY 003 RETURN_REF pncs:return-ref:sha256:3c0309fc10307cf3e2f4eb382c70b84edbf1f07027f7348b3f8658e1baf00fa2
OCCURRENCE 000 CONTROL_DEFINITION pncs:def:sha256:b7988497bab75a526771fa24aeca75e0182bd437fd707927cb0e78b04d360cce
OCCURRENCE 001 ROUTE_REF pncs:route-ref:sha256:3ad27bd2e71cd88f1c822792bd9392f10ef3f096e951badb7f79b8d9f45e0a63
OCCURRENCE 002 RETURN_REF pncs:return-ref:sha256:3c0309fc10307cf3e2f4eb382c70b84edbf1f07027f7348b3f8658e1baf00fa2
OPERATOR 000 DIFFERENCE
OPERATOR 001 CONDITION
OPERATOR 002 DIFFERENCE
OPERATOR 003 CONDITION
OPERATOR 004 COMPOSITION
OPERATOR 005 NEGATION
OPERATOR 006 ORDER
OPERATOR 007 TRANSFORM
OPERATOR 008 ORDER
OPERATOR 009 TRANSFORM
OPERATOR 010 COMPOSITION
OPERATOR 011 ORDER
OPERATOR 012 TRANSFORM
OPERATOR 013 COMPOSITION
OPERATOR 014 RETURN
RETURN_REF pncs:return-ref:sha256:3c0309fc10307cf3e2f4eb382c70b84edbf1f07027f7348b3f8658e1baf00fa2
EXTERNAL_EFFECTS FALSE
FREE_FORM_NL_EXECUTION FALSE
NATIVE_EXECUTION_OPENED FALSE
RETURN_EXECUTION_OPENED FALSE
STATIC_RUNTIME_FALLBACK FALSE
END PROGRAM_UNIT
'''


def _write_program_artifacts(root: Path, *, mutate_receipt=None, text: str = PNV):
    p = root / 'program.pnv'; r = root / 'build.json'
    p.write_text(text, encoding='utf-8'); raw = text.encode()
    body = {
        'schema': v25.V24_BUILD_SCHEMA,
        'build_contract_id': v25.V24_BUILD_CONTRACT_ID,
        'program_id': PROGRAM_ID,
        'composition_id': COMPOSITION_ID,
        'pnv_sha256': hashlib.sha256(raw).hexdigest(),
        'pnv_size_bytes': len(raw),
        'dependency_closure_sha256': '1' * 64,
        'dependency_occurrences_sha256': '2' * 64,
        'operator_schedule_sha256': SCHEDULE_SHA,
        'composition_admission_id': 'pncs:composition-admission:sha256:' + '3' * 64,
        'live_surface': {'root': '/dev/shm/ciel_noema', 'phi_sha256': '4'*64, 'aux_phi_sha256': '5'*64, 'aux_feedback_phi_sha256': '5'*64, 'operator_registry_sha256': '6'*64, 'tether_receipt_sha256': '7'*64},
        'operator_witnesses_sha256': '8' * 64,
        'roundtrip_byte_identical': True,
        'execution_opened': False,
        'return_execution_opened': False,
        'external_effects': False,
        'static_runtime_fallback': False,
        'deterministic_fields_only': True,
    }
    if mutate_receipt: mutate_receipt(body)
    rec = {**body, 'build_id': v25._typed_id('pncs:program-build', body)}
    r.write_text(v25._compact_json(rec) + '\n', encoding='utf-8')
    return p, r


def _packet(base: dict) -> dict:
    sha = hashlib.sha256(json.dumps(base, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    return {**base, 'packet_sha256': sha}


def _write_live(root: Path, *, current_sha='a' * 64, operator_text='{"op":"x"}\n'):
    (root / 'session').mkdir(parents=True, exist_ok=True); (root / 'phasenav').mkdir(parents=True, exist_ok=True)
    (root / 'ciel_binding_status').write_text('ACTIVE\n')
    start = _packet({'schema': 'noema/session-startpoint/v1', 'status': 'VERIFIED', 'surface_root': str(root)})
    (root / 'session/startpoint.json').write_text(json.dumps(start, sort_keys=True))
    pid = os.getpid(); now = time.time_ns(); account='NOEMA_ACCOUNT_DEFAULT_CURRENT_V56'
    (root / 'current_memory.json').write_text(json.dumps({'account_current': account, 'current_pointer_sha256': current_sha}))
    aux={'schema':'noema.aux-stream-status/v2','status':'ACTIVE','pid':pid,'heartbeat_ns':now,'seq':10}
    tether={'schema':'noema.tether-runtime-status/v1','status':'ACTIVE','pid':pid,'heartbeat_ns':now,'seq':11}
    ac={'schema':'noema.ac-aux-live-binding/v2','status':'ACTIVE','pid':pid,'heartbeat_ns':now,'seq':12,'account_current':account,'current_pointer_sha256':current_sha,'ac_current_sha256':'b'*64,'ethics_field_sha256':'c'*64,'ethics_field_status':'ACTIVE','no_static_fallback':True,'aux_pid':pid,'tether_pid':pid}
    seal={'schema':'noema.fast-admission-seal/v2','status':'ACTIVE','account_current':account,'current_pointer_sha256':current_sha,'startpoint_packet_sha256':start['packet_sha256'],'ac_current_sha256':'b'*64,'ethics_field_sha256':'c'*64,'aux_pid':pid,'tether_pid':pid,'ac_aux_pid':pid,'sealed_unix_ns':now,'no_static_fallback':True}
    (root / 'aux_stream_status.json').write_text(json.dumps(aux)); (root / 'tether_runtime_status.json').write_text(json.dumps(tether)); (root / 'ac_aux_status.json').write_text(json.dumps(ac)); (root / 'session/fast_admission.json').write_text(json.dumps(seal)); (root / 'phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl').write_text(operator_text)


def _refresh(root: Path, *, seq_delta=1):
    now=time.time_ns()
    for name in ('aux_stream_status.json','tether_runtime_status.json','ac_aux_status.json'):
        p=root/name; d=json.loads(p.read_text()); d['heartbeat_ns']=now; d['seq']=int(d.get('seq',0))+seq_delta; p.write_text(json.dumps(d))


def _change_current_generation(root: Path, new_sha: str):
    cur=json.loads((root/'current_memory.json').read_text()); cur['current_pointer_sha256']=new_sha; (root/'current_memory.json').write_text(json.dumps(cur))
    seal=json.loads((root/'session/fast_admission.json').read_text()); seal['current_pointer_sha256']=new_sha; (root/'session/fast_admission.json').write_text(json.dumps(seal))
    ac=json.loads((root/'ac_aux_status.json').read_text()); ac['current_pointer_sha256']=new_sha; ac['heartbeat_ns']=time.time_ns(); (root/'ac_aux_status.json').write_text(json.dumps(ac)); _refresh(root)


def _runtime(root: Path):
    return v25.PersistentProgramRuntime(root, require_socket=False, require_canonical_root=False, max_heartbeat_age_s=5.0)


def _image(root: Path):
    p,r=_write_program_artifacts(root); return v25.program_image_from_artifacts(p,r,expected_program_id=PROGRAM_ID)


def _fake_result(root: Path, *, definition_id=CONTROL_DEF):
    body={'schema':v25.V20_EXECUTION_SCHEMA,'execution_contract_id':v25.V20_EXECUTION_CONTRACT_ID,'program':{'content_id':definition_id},'live_surface':{'root':str(root)},'admission':{'branch_truth_state':'TRUE'},'result':{'kind':'INTERNAL_TRANSFORM','control_location':'safety.pause'},'external_effects':False,'free_form_nl_execution':False}
    receipt={**body,'receipt_sha256':v25._sha256_json(body)}
    return SimpleNamespace(receipt=receipt,target='safety.pause',branch_truth_state='TRUE')


def _fake_lineage(execution_sha: str, *, definition_id=CONTROL_DEF, contract=v25.V22_LINEAGE_CONTRACT_ID):
    result_id='pncs:result:sha256:'+'d'*64
    payload={'schema':'PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22','lineage_contract_id':contract,'result_id':result_id,'execution_receipt_sha256':execution_sha}
    lineage_id=v25._typed_id('pncs:lineage',payload)
    return SimpleNamespace(payload=payload,result_id=result_id,lineage_id=lineage_id,hierarchy=SimpleNamespace(definition_id=definition_id),receipt={**payload,'lineage_id':lineage_id})


def test_known_v024_artifact_becomes_program_image(tmp_path):
    image=_image(tmp_path); assert image.program_id==PROGRAM_ID; assert image.control_definition_id==CONTROL_DEF; assert image.operator_schedule_sha256==SCHEDULE_SHA


def test_tampered_program_bytes_fail_closed(tmp_path):
    p,r=_write_program_artifacts(tmp_path,text=PNV.replace('EXTERNAL_EFFECTS FALSE','EXTERNAL_EFFECTS TRUE'))
    with pytest.raises(v25.PersistentRuntimeV25Error, match='closed boundary'): v25.program_image_from_artifacts(p,r,expected_program_id=PROGRAM_ID)


def test_tampered_build_receipt_digest_fails_closed(tmp_path):
    p,r=_write_program_artifacts(tmp_path); rec=json.loads(r.read_text()); rec['pnv_size_bytes']+=1; r.write_text(json.dumps(rec))
    with pytest.raises(v25.PersistentRuntimeV25Error, match='digest mismatch'): v25.program_image_from_artifacts(p,r,expected_program_id=PROGRAM_ID)


def test_build_receipt_cannot_open_execution(tmp_path):
    p,r=_write_program_artifacts(tmp_path,mutate_receipt=lambda d:d.__setitem__('execution_opened',True))
    with pytest.raises(v25.PersistentRuntimeV25Error, match='forbidden boundary'): v25.program_image_from_artifacts(p,r,expected_program_id=PROGRAM_ID)


def test_generation_identity_ignores_heartbeat_and_sequence_advance(tmp_path):
    _write_live(tmp_path); a=v25.read_live_generation(tmp_path,require_socket=False,require_canonical_root=False,max_heartbeat_age_s=5); _refresh(tmp_path,seq_delta=100); b=v25.read_live_generation(tmp_path,require_socket=False,require_canonical_root=False,max_heartbeat_age_s=5); assert a.generation_id==b.generation_id


def test_generation_identity_changes_with_current_generation(tmp_path):
    _write_live(tmp_path); a=v25.read_live_generation(tmp_path,require_socket=False,require_canonical_root=False,max_heartbeat_age_s=5); _change_current_generation(tmp_path,'e'*64); b=v25.read_live_generation(tmp_path,require_socket=False,require_canonical_root=False,max_heartbeat_age_s=5); assert a.generation_id!=b.generation_id


def test_operator_registry_change_invalidates_generation(tmp_path):
    _write_live(tmp_path); a=v25.read_live_generation(tmp_path,require_socket=False,require_canonical_root=False,max_heartbeat_age_s=5); (tmp_path/'phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl').write_text('{"op":"y"}\n'); _refresh(tmp_path); b=v25.read_live_generation(tmp_path,require_socket=False,require_canonical_root=False,max_heartbeat_age_s=5); assert a.generation_id!=b.generation_id


def test_pid_generation_mismatch_fails_closed(tmp_path):
    _write_live(tmp_path); seal=json.loads((tmp_path/'session/fast_admission.json').read_text()); seal['aux_pid']=os.getpid()+1000000; (tmp_path/'session/fast_admission.json').write_text(json.dumps(seal))
    with pytest.raises(v25.PersistentRuntimeV25Error, match='aux_pid generation'): v25.read_live_generation(tmp_path,require_socket=False,require_canonical_root=False,max_heartbeat_age_s=5)


def test_static_fallback_in_fast_seal_fails_closed(tmp_path):
    _write_live(tmp_path); seal=json.loads((tmp_path/'session/fast_admission.json').read_text()); seal['no_static_fallback']=False; (tmp_path/'session/fast_admission.json').write_text(json.dumps(seal))
    with pytest.raises(v25.PersistentRuntimeV25Error, match='static fallback'): v25.read_live_generation(tmp_path,require_socket=False,require_canonical_root=False,max_heartbeat_age_s=5)


def test_load_creates_generation_bound_resident_handle(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); handle,receipt=_runtime(live).load(_image(art)); assert handle.handle_id.startswith('pncs:resident:sha256:'); assert receipt.payload['process_reconstruction_required'] is False; assert (live/'pncs/v0.25/runtime/active'/f"{handle.handle_id.rsplit(':',1)[-1]}.json").is_file()


def test_same_generation_load_is_idempotent(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); rt=_runtime(live); image=_image(art); a,ra=rt.load(image); _refresh(live,seq_delta=5); b,rb=rt.load(image); assert a.handle_id==b.handle_id; assert ra.receipt_id==rb.receipt_id


def test_new_runtime_object_recovers_resident_handle_without_rebuild(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); image=_image(art); handle,_=_runtime(live).load(image); _refresh(live); admission=_runtime(live).admit(handle.handle_id); assert admission.handle.handle_id==handle.handle_id


def test_handle_is_invalidated_on_current_generation_change(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); rt=_runtime(live); handle,_=rt.load(_image(art)); _change_current_generation(live,'f'*64)
    with pytest.raises(v25.PersistentRuntimeV25Error, match='stale'): rt.admit(handle.handle_id)


def test_unload_removes_active_pointer_and_blocks_admission(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); rt=_runtime(live); handle,_=rt.load(_image(art)); receipt=rt.unload(handle.handle_id); assert receipt.payload['active_pointer_removed'] is True
    with pytest.raises(v25.PersistentRuntimeV25Error, match='active pointer'): rt.admit(handle.handle_id)


def test_reload_after_unload_reactivates_same_handle(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); rt=_runtime(live); image=_image(art); handle,_=rt.load(image); rt.unload(handle.handle_id); _refresh(live); again,_=rt.load(image); assert again.handle_id==handle.handle_id; assert rt.admit(handle.handle_id).handle.handle_id==handle.handle_id


def test_resident_program_byte_tamper_fails_closed(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); rt=_runtime(live); handle,_=rt.load(_image(art)); p=live/'pncs/v0.25/runtime/programs'/f"{PROGRAM_ID.rsplit(':',1)[-1]}.pnv"; p.write_bytes(p.read_bytes()+b'x')
    with pytest.raises(v25.PersistentRuntimeV25Error, match='bytes/hash/size mismatch'): rt.admit(handle.handle_id)


def test_dispatch_binds_exact_v020_result_and_v022_lineage(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); rt=_runtime(live); handle,_=rt.load(_image(art))
    def kernel():
        _refresh(live); result=_fake_result(live); return result,_fake_lineage(result.receipt['receipt_sha256'])
    receipt=rt.dispatch_control(handle.handle_id,kernel); assert receipt.payload['kernel_scope']=='CONTROL_ROOT_V0_20'; assert receipt.payload['continuation_execution_opened'] is False; assert receipt.payload['return_execution_opened'] is False; assert (live/'pncs/v0.25/runtime/receipts/dispatch'/f"{receipt.dispatch_id.rsplit(':',1)[-1]}.json").is_file()


def test_repeated_identical_dispatch_is_deterministic(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); rt=_runtime(live); handle,_=rt.load(_image(art)); result=_fake_result(live); lineage=_fake_lineage(result.receipt['receipt_sha256'])
    def kernel(): _refresh(live); return result,lineage
    a=rt.dispatch_control(handle.handle_id,kernel); b=rt.dispatch_control(handle.handle_id,kernel); assert a.dispatch_id==b.dispatch_id


def test_dispatch_rejects_wrong_control_definition(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); rt=_runtime(live); handle,_=rt.load(_image(art))
    def kernel():
        _refresh(live); result=_fake_result(live,definition_id='pncs:def:sha256:'+'e'*64); return result,_fake_lineage(result.receipt['receipt_sha256'])
    with pytest.raises(v25.PersistentRuntimeV25Error, match='control Definition mismatch'): rt.dispatch_control(handle.handle_id,kernel)


def test_dispatch_rejects_wrong_lineage_contract(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); rt=_runtime(live); handle,_=rt.load(_image(art))
    def kernel():
        _refresh(live); result=_fake_result(live); return result,_fake_lineage(result.receipt['receipt_sha256'],contract='OTHER')
    with pytest.raises(v25.PersistentRuntimeV25Error, match='exact v0.22'): rt.dispatch_control(handle.handle_id,kernel)


def test_dispatch_detects_generation_change_during_kernel(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); rt=_runtime(live); handle,_=rt.load(_image(art))
    def kernel():
        _change_current_generation(live,'9'*64); result=_fake_result(live); return result,_fake_lineage(result.receipt['receipt_sha256'])
    with pytest.raises(v25.PersistentRuntimeV25Error, match='stale'): rt.dispatch_control(handle.handle_id,kernel)


def test_noncanonical_operational_root_rejected(tmp_path):
    with pytest.raises(v25.PersistentRuntimeV25Error, match='fixed to /dev/shm'): v25.PersistentProgramRuntime(tmp_path)


def test_runtime_core_does_not_spawn_processes():
    source=Path(v25.__file__).read_text(); assert 'subprocess' not in source; assert 'os.system' not in source; assert 'Popen(' not in source


def test_program_image_source_location_is_not_authority(tmp_path):
    image=_image(tmp_path); assert image.payload['source_text_is_authority'] is False; assert image.payload['repository_location_is_authority'] is False


def test_handle_keeps_external_effects_closed(tmp_path):
    live=tmp_path/'live'; art=tmp_path/'art'; art.mkdir(); _write_live(live); handle,_=_runtime(live).load(_image(art)); assert handle.payload['external_effects'] is False; assert handle.payload['continuation_execution_opened'] is False; assert handle.payload['return_execution_opened'] is False
