from pathlib import Path
import json, sys
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'src'))
from phasenav_natural_code.surface_v07 import normalize_control_surface, reference_predicate, SurfaceV07Error
PNV=ROOT/'native'/'PNCS_CONTROL_TRANSFER_V0_7.pnv'
LEDGER=ROOT/'mining'/'PNCS_CONTROL_TRANSFER_LEDGER_V0_7.json'
ALLOWED={"IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION","QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT","SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY","MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY","SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL","PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR","SOFT_CLIP","RESOLVE","DERIVE"}

def rows():
    out={}
    for raw in PNV.read_text(encoding='utf-8').splitlines():
        s=raw.strip()
        if not s or s.startswith('#'): continue
        p=s.split()
        if p[0]=='OP': out[p[1]]=p[2:]
    return out

def ledger(): return json.loads(LEDGER.read_text(encoding='utf-8'))

def test_no_new_opcode_v07():
    for key,val in rows().items(): assert val[0] in ALLOWED,(key,val)
    assert ledger()['new_opcodes']==[]

def test_go_is_internal_transform_not_action_request():
    r=rows()
    for name in ['EX.GRAVITY.ROUTE','EX.TEMP.ROUTE','EX.MEM.ROUTE','EX.PHASE.ROUTE','EX.RISK.ROUTE','EX.ERROR.ROUTE']:
        assert r[name][0]=='TRANSFORM'
        assert r[name][1]=='control_location'
        assert r[name][2]=='route'
    assert ledger()['internal_route_is_effect_request'] is False

def test_no_action_request_in_promoted_leaf_path():
    p=ledger()['radicals']['R.CONDITIONAL_ROUTE']['leaf_path']
    assert p==['DIFFERENCE','CONDITION','ORDER','TRANSFORM','COMPOSITION']
    assert 'ACTION_REQUEST' not in p

def test_control_radical_is_promoted_after_six_domains():
    d=ledger()['radicals']['R.CONDITIONAL_ROUTE']
    assert d['status']=='PROMOTED_CONTROL_RADICAL'
    assert len(d['transfer_domains'])==6

def test_comparison_specializations_share_one_leaf_path():
    d=ledger()['radicals']['R.COMPARISON']
    assert d['leaf_path']==['DIFFERENCE','CONDITION']
    assert d['bindings']=={'BELOW':'lt','ABOVE':'gt','EQUAL':'eq'}

def test_temperature_paraphrases_converge():
    xs=['IF temperature ABOVE 80 THEN GO cooling.emergency','IF temperature > 80 THEN GO cooling.emergency','temperature > 80 -> cooling.emergency']
    ys=[normalize_control_surface(x) for x in xs]
    assert ys[0]==ys[1]==ys[2]
    assert ys[0].canonical_tuple==('temperature','gt',80.0,'cooling.emergency')

def test_phase_coherence_paraphrases_converge():
    xs=['IF phase_coherence BELOW 0.7 THEN GO phasenav.phase.relock','IF phase_coherence < .70 THEN GO phasenav.phase.relock','phase_coherence < 0.700 -> phasenav.phase.relock']
    ys=[normalize_control_surface(x) for x in xs]
    assert ys[0]==ys[1]==ys[2]
    assert ys[0].canonical_tuple==('phase_coherence','lt',0.7,'phasenav.phase.relock')

def test_equal_paraphrases_converge():
    a=normalize_control_surface('IF phase_error EQUAL 0 THEN GO phasenav.locked')
    b=normalize_control_surface('IF phase_error == 0.0 THEN GO phasenav.locked')
    c=normalize_control_surface('phase_error == .0 -> phasenav.locked')
    assert a==b==c
    assert a.comparator=='eq'

def test_transfer_domains_all_share_same_leaf_path():
    xs=[
      'IF gravity BELOW 0.5 THEN GO physics.gravity.low',
      'IF temperature ABOVE 80 THEN GO cooling.emergency',
      'IF memory_pressure ABOVE .9 THEN GO runtime.memory.relief',
      'IF phase_coherence BELOW .7 THEN GO phasenav.phase.relock',
      'IF risk ABOVE .8 THEN GO safety.pause',
      'IF phase_error EQUAL 0 THEN GO phasenav.locked']
    ys=[normalize_control_surface(x) for x in xs]
    assert {y.leaf_path for y in ys}=={('DIFFERENCE','CONDITION','ORDER','TRANSFORM','COMPOSITION')}

def test_reference_predicates_all_comparators():
    lt=normalize_control_surface('IF gravity BELOW 0.5 THEN GO physics.gravity.low')
    gt=normalize_control_surface('IF risk ABOVE 0.8 THEN GO safety.pause')
    eq=normalize_control_surface('IF phase_error EQUAL 0 THEN GO phasenav.locked')
    assert reference_predicate(lt,0.49) and not reference_predicate(lt,0.5)
    assert reference_predicate(gt,0.81) and not reference_predicate(gt,0.8)
    assert reference_predicate(eq,0.0) and not reference_predicate(eq,1e-9)

def test_fail_closed_unsupported_operator():
    for text in ['IF gravity NEAR 0.5 THEN GO x','IF gravity <= 0.5 THEN GO x','gravity != 0.5 -> x']:
        try: normalize_control_surface(text)
        except SurfaceV07Error: pass
        else: raise AssertionError(text)

def test_surface_words_are_not_machine_opcodes_v07():
    kinds={v[0] for v in rows().values()}
    assert not ({'IF','BELOW','ABOVE','EQUAL','THEN','GO'} & kinds)

def test_native_file_obeys_reconstructed_line_contract_v07():
    allowed_instr={'PNV','EPISTEMIC','MODE','OP','VECTOR','EMIT'}
    for raw in PNV.read_text(encoding='utf-8').splitlines():
        s=raw.strip()
        if not s or s.startswith('#'): continue
        assert s.split()[0] in allowed_instr,s
