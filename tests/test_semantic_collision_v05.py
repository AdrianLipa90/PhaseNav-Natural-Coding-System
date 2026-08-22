from pathlib import Path
import json

ROOT=Path(__file__).parents[1]
PNV=ROOT/'native'/'PNCS_SEMANTIC_COLLISION_REPAIR_V0_5.pnv'
LEDGER=ROOT/'mining'/'PNCS_SEMANTIC_COLLISION_LEDGER_V0_5.json'
ALLOWED_OPS={"IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION","QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT","SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY","MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY","SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL","PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR","SOFT_CLIP","RESOLVE","DERIVE"}

def active_lines():
    return [x.strip() for x in PNV.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#')]

def op_rows():
    rows={}
    for line in active_lines():
        p=line.split()
        if p[0]=='OP': rows[p[1]]=p[2:]
    return rows

def ledger(): return json.loads(LEDGER.read_text(encoding='utf-8'))

def test_v05_uses_only_recovered_pnv_opcodes():
    for line in active_lines():
        p=line.split()
        if p[0]=='OP': assert p[2] in ALLOWED_OPS,line

def test_derive_is_not_declared_as_kaku_in_v05():
    assert 'K.DERIVE' not in op_rows()
    assert ledger()['demotions']['DERIVE']['to']=='EXPANDABLE_RADICAL'

def test_resolve_is_not_declared_as_kaku_in_v05():
    assert 'K.RESOLVE' not in op_rows()
    assert ledger()['demotions']['RESOLVE']['to']=='NAMESPACE_SPLIT'

def test_derivation_expands_to_source_composition_transform():
    d=ledger()['radicals']['R.DERIVATION']
    assert d['leaf_path']==['SOURCE','COMPOSITION','TRANSFORM']
    assert op_rows()['PATH.DEF.DERIVATION']==['COMPOSITION','K.SOURCE','K.COMPOSE','K.TRANSFORM']

def test_name_resolution_expands_without_equation_solving():
    d=ledger()['demotions']['RESOLVE']
    assert d['leaf_path']==['SOURCE','COMPOSITION','IDENTITY']
    assert d['mathematical_solving_uses_unqualified_resolve'] is False

def test_fixed_point_collapses_to_invariant_leaf_path():
    d=ledger()['radicals']
    assert d['R.FIXED_POINT']['leaf_path']==d['R.INVARIANT']['leaf_path']
    assert d['R.FIXED_POINT']['status']=='SPECIALIZATION_OF_R.INVARIANT'
    assert d['R.FIXED_POINT']['binding']=='output == input'

def test_convergence_contains_no_atomic_derive_or_resolve():
    p=ledger()['radicals']['R.CONVERGENCE']['leaf_path']
    assert 'DERIVE' not in p and 'RESOLVE' not in p
    assert p==['SOURCE','COMPOSITION','TRANSFORM','COMPOSITION','IDENTITY']

def test_current_irreducible_set_is_six_plus_control_candidate():
    d=ledger()
    assert d['irreducible_kaku_current']==['SOURCE','ORDER','TRANSFORM','COMPOSITION','DIFFERENCE','IDENTITY']
    assert d['control_flow_candidates']==['CONDITION']

def test_no_duplicate_operator_ids_v05():
    ids=[x.split()[1] for x in active_lines() if x.startswith('OP ')]
    assert len(ids)==len(set(ids))
