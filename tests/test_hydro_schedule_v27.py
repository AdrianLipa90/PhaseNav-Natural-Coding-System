import importlib.util,sys,copy,json,hashlib,struct
from pathlib import Path
import pytest

for name in ("hydro_time_v27","hydro_schedule_v27"):
    spec=importlib.util.spec_from_file_location(name,f"/mnt/data/pncs_v027/{name}.py")
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod)
h=sys.modules["hydro_time_v27"]; s=sys.modules["hydro_schedule_v27"]

RECEIPT_PATH=Path('/dev/shm/ciel_noema/pncs/v0.20/receipts/84d40f600a8aa9e59ebc6dc42c856bcffec9265d04f791e7f5c49cdba2d583ad.json')
RECEIPT=json.loads(RECEIPT_PATH.read_text())
THETA=tuple((i+1)*0.1 for i in range(36))
STATE=h.PhaseFlowState36(THETA)
GATE=h.HydrodynamicPhaseGate(.5,.2,steps=2)

def test_receipt_validates(): assert s._validate_v20_receipt(RECEIPT)==RECEIPT['receipt_sha256']
def test_receipt_tamper_rejected():
    r=copy.deepcopy(RECEIPT); r['result']['control_location']='x'
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='digest'): s._validate_v20_receipt(r)
def test_step_index_discontinuity_rejected():
    r=copy.deepcopy(RECEIPT); r['steps'][0]['index']=2; body=dict(r); body.pop('receipt_sha256'); r['receipt_sha256']=h._sha256_json(body)
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='index'): s._validate_v20_receipt(r)
def test_sigma_discontinuity_rejected():
    r=copy.deepcopy(RECEIPT); r['steps'][1]['before_sigma_id']='bad'; body=dict(r); body.pop('receipt_sha256'); r['receipt_sha256']=h._sha256_json(body)
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='Sigma'): s._validate_v20_receipt(r)
def test_uniform_schedule_has_nine_entries(): assert len(s.uniform_schedule_for_receipt(RECEIPT,GATE).entries)==9
def test_schedule_preserves_definition(): assert s.uniform_schedule_for_receipt(RECEIPT,GATE).program_content_id==RECEIPT['program']['content_id']
def test_schedule_id_deterministic(): assert s.uniform_schedule_for_receipt(RECEIPT,GATE).schedule_id==s.uniform_schedule_for_receipt(RECEIPT,GATE).schedule_id
def test_schedule_external_effects_false(): assert s.uniform_schedule_for_receipt(RECEIPT,GATE).payload['external_effects'] is False
def test_live_registry_has_required_ops():
    ops,_=s.load_live_operator_vectors(); assert set(['DIFFERENCE','CONDITION','COMPOSITION','NEGATION','ORDER','TRANSFORM'])<=set(ops)
def test_live_vector_hashes_match_receipt():
    ops,_=s.load_live_operator_vectors()
    for st in RECEIPT['steps']:
        assert hashlib.sha256(struct.pack('<36d',*ops[st['operator_id']])).hexdigest()==st['operator_vector_sha256']
def test_noncanonical_root_rejected():
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='fixed'): s.load_live_operator_vectors('/tmp')
def test_replay_operator_order_exact():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); tr=s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,sch)
    assert tr.operator_names==tuple(st['operator_id'] for st in RECEIPT['steps'])
def test_replay_trace_count_exact():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); tr=s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,sch); assert len(tr.operator_trace_ids)==9
def test_replay_semantic_identity_unchanged():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); tr=s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,sch); assert tr.payload['program_content_id']==RECEIPT['program']['content_id'] and tr.payload['semantic_identity_modified'] is False
def test_replay_binds_execution_receipt():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); tr=s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,sch); assert tr.payload['execution_receipt_sha256']==RECEIPT['receipt_sha256']
def test_replay_effects_closed():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); tr=s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,sch); assert tr.payload['external_effects'] is False
def test_replay_no_lab_time_claim():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); tr=s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,sch); assert tr.payload['laboratory_time_modified'] is False
def test_different_substrates_same_semantic_identity_different_trace():
    a=s.uniform_schedule_for_receipt(RECEIPT,h.HydrodynamicPhaseGate(.25,1.0,steps=3)); b=s.uniform_schedule_for_receipt(RECEIPT,h.HydrodynamicPhaseGate(4.0,.1,steps=3)); ta=s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,a); tb=s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,b)
    assert ta.program_content_id==tb.program_content_id==RECEIPT['program']['content_id'] and ta.trace_id!=tb.trace_id and ta.phase_proper_time_advanced<tb.phase_proper_time_advanced
def test_schedule_length_mismatch_rejected():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); bad=s.HydrodynamicKakuSchedule(sch.execution_receipt_sha256,sch.program_content_id,sch.entries[:-1])
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='length'): s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,bad)
def test_occurrence_operator_substitution_rejected():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); e=list(sch.entries); first=e[0]; e[0]=s.HydrodynamicKakuScheduleEntry(first.step_index,'ORDER',first.operator_vector_sha256,first.gate); bad=s.HydrodynamicKakuSchedule(sch.execution_receipt_sha256,sch.program_content_id,tuple(e))
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='occurrence'): s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,bad)
def test_occurrence_hash_substitution_rejected():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); e=list(sch.entries); first=e[0]; e[0]=s.HydrodynamicKakuScheduleEntry(first.step_index,first.operator_id,'0'*64,first.gate); bad=s.HydrodynamicKakuSchedule(sch.execution_receipt_sha256,sch.program_content_id,tuple(e))
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='occurrence'): s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,bad)
