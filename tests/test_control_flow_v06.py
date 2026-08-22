from pathlib import Path
import json, sys
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'src'))
from phasenav_natural_code.surface_v06 import normalize_control_surface, reference_predicate, SurfaceV06Error
PNV=ROOT/'native'/'PNCS_CONTROL_FLOW_V0_6.pnv'
LEDGER=ROOT/'mining'/'PNCS_CONTROL_FLOW_LEDGER_V0_6.json'
ALLOWED={"IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION","QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT","SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY","MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY","SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL","PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR","SOFT_CLIP","RESOLVE","DERIVE"}

def ops():
    rows={}
    for raw in PNV.read_text().splitlines():
        s=raw.strip()
        if not s or s.startswith('#'): continue
        p=s.split()
        if p[0]=='OP': rows[p[1]]=p[2:]
    return rows

def ledger(): return json.loads(LEDGER.read_text())

def test_no_new_opcode():
    for k,v in ops().items(): assert v[0] in ALLOWED,(k,v)
    assert ledger()['new_opcodes']==[]

def test_surface_words_are_not_machine_opcodes():
    kinds={v[0] for v in ops().values()}
    assert not ({'IF','BELOW','THEN','GO'} & kinds)

def test_below_reduces_to_difference_condition():
    assert ledger()['radicals']['R.BELOW']['leaf_path']==['DIFFERENCE','CONDITION']

def test_conditional_route_leaf_path():
    assert ledger()['radicals']['R.CONDITIONAL_ROUTE']['leaf_path']==['DIFFERENCE','CONDITION','ORDER','ACTION_REQUEST','COMPOSITION']

def test_three_surface_forms_converge():
    xs=[
      'IF gravity BELOW 0.5 THEN GO physics.gravity.low',
      'if gravity < .5 then go physics.gravity.low',
      'gravity < 0.500 -> physics.gravity.low']
    ys=[normalize_control_surface(x) for x in xs]
    assert ys[0]==ys[1]==ys[2]
    assert ys[0].leaf_path==('DIFFERENCE','CONDITION','ORDER','ACTION_REQUEST','COMPOSITION')

def test_reference_truth_table_strict_below():
    p=normalize_control_surface('IF gravity BELOW 0.5 THEN GO physics.gravity.low')
    assert reference_predicate(p,0.49) is True
    assert reference_predicate(p,0.5) is False
    assert reference_predicate(p,0.51) is False

def test_fail_closed_unknown_surface():
    try: normalize_control_surface('maybe gravity sort of low then perhaps go somewhere')
    except SurfaceV06Error: pass
    else: raise AssertionError('must fail closed')

def test_action_request_is_not_hidden_execution():
    e=ledger()['execution_boundary']
    assert e['action_request_is_request_node'] is True
    assert e['hidden_execution'] is False
    assert e['historical_native_v01_mutating_executor'] is False

def test_name_resolution_remains_separate():
    assert ledger()['name_resolution_separate'] is True

def test_example_graph_uses_recovered_control_ops():
    r=ops()
    assert r['EX.GRAVITY.BELOW'][0]=='CONDITION'
    assert r['EX.GRAVITY.GO'][0]=='ACTION_REQUEST'
    assert r['EX.GRAVITY.ORDER'][0]=='ORDER'
    assert r['EX.GRAVITY.PROGRAM'][0]=='COMPOSITION'


def test_native_file_obeys_reconstructed_line_contract():
    allowed_instr={'PNV','EPISTEMIC','MODE','OP','VECTOR','EMIT'}
    for raw in PNV.read_text().splitlines():
        s=raw.strip()
        if not s or s.startswith('#'): continue
        assert s.split()[0] in allowed_instr,s
