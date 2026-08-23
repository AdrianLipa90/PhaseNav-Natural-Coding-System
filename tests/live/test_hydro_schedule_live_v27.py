import hashlib
import json
import struct
from pathlib import Path
import pytest

from phasenav_natural_code import hydro_time_v27 as h
from phasenav_natural_code import hydro_schedule_v27 as s

FIXTURE_PATH=Path(__file__).parents[1]/"fixtures"/"v020"/"720598c087b889ec2fca407833241f08903f19d5f1a531c92d6cfb08ca711417.json"
RECEIPT=json.loads(FIXTURE_PATH.read_text("utf-8"))
THETA=tuple((i+1)*0.1 for i in range(36))
STATE=h.PhaseFlowState36(THETA)
GATE=h.HydrodynamicPhaseGate(.5,.2,steps=2)

def test_live_registry_has_required_ops():
    ops,_=s.load_live_operator_vectors(); assert {'DIFFERENCE','CONDITION','COMPOSITION','NEGATION','ORDER','TRANSFORM'}<=set(ops)
def test_live_vector_hashes_match_receipt():
    ops,_=s.load_live_operator_vectors()
    for st in RECEIPT['steps']:
        assert hashlib.sha256(struct.pack('<36d',*ops[st['operator_id']])).hexdigest()==st['operator_vector_sha256']
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
def test_occurrence_operator_substitution_rejected():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); e=list(sch.entries); first=e[0]; e[0]=s.HydrodynamicKakuScheduleEntry(first.step_index,'ORDER',first.operator_vector_sha256,first.gate); bad=s.HydrodynamicKakuSchedule(sch.execution_receipt_sha256,sch.program_content_id,tuple(e))
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='occurrence'): s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,bad)
def test_occurrence_hash_substitution_rejected():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); e=list(sch.entries); first=e[0]; e[0]=s.HydrodynamicKakuScheduleEntry(first.step_index,first.operator_id,'0'*64,first.gate); bad=s.HydrodynamicKakuSchedule(sch.execution_receipt_sha256,sch.program_content_id,tuple(e))
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='occurrence'): s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,bad)
