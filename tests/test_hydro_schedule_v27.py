import copy
import json
from pathlib import Path
import pytest

from phasenav_natural_code import hydro_time_v27 as h
from phasenav_natural_code import hydro_schedule_v27 as s

FIXTURE_PATH=Path(__file__).parent/"fixtures"/"v020"/"720598c087b889ec2fca407833241f08903f19d5f1a531c92d6cfb08ca711417.json"
RECEIPT=json.loads(FIXTURE_PATH.read_text("utf-8"))
THETA=tuple((i+1)*0.1 for i in range(36))
STATE=h.PhaseFlowState36(THETA)
GATE=h.HydrodynamicPhaseGate(.5,.2,steps=2)

def test_fixture_is_content_addressed(): assert RECEIPT["receipt_sha256"]==FIXTURE_PATH.stem
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
def test_noncanonical_root_rejected():
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='fixed'): s.load_live_operator_vectors('/tmp')
def test_schedule_length_mismatch_rejected_before_live_access():
    sch=s.uniform_schedule_for_receipt(RECEIPT,GATE); bad=s.HydrodynamicKakuSchedule(sch.execution_receipt_sha256,sch.program_content_id,sch.entries[:-1])
    with pytest.raises(s.HydrodynamicScheduleV27Error,match='length'): s.replay_v20_hydrodynamic_schedule(RECEIPT,STATE,bad)
