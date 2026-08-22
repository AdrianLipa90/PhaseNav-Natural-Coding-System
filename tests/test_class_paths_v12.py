from __future__ import annotations

import json
from pathlib import Path
import pytest

from phasenav_natural_code.classes_v12 import ClassRegistry, ClassV12Error, define_class, verify_serialized_class_record
from phasenav_natural_code.definitions_v11 import DefinitionRegistry, define_branch, define_predicate

ROOT=Path(__file__).parents[1]
REGISTRY_PATH=ROOT/'classes'/'PNCS_CLASS_REGISTRY_V0_12.jsonl'
INDEX_PATH=ROOT/'classes'/'PNCS_CLASS_CONTENT_INDEX_V0_12.json'
PNV_PATH=ROOT/'native'/'PNCS_CLASS_PATHS_V0_12.pnv'

ALLOWED_OPS={"IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION","QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT","SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY","MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY","SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL","PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR","SOFT_CLIP","RESOLVE","DERIVE"}


def _defs():
    reg=DefinitionRegistry()
    high=reg.register(define_predicate('high_risk','risk ABOVE 0.8'))
    reg.register(define_predicate('risk_guard','risk > .800'))
    safety=reg.register(define_predicate('safety_trigger','(risk ABOVE 0.8 OR memory_pressure ABOVE 0.9)'))
    phase=reg.register(define_predicate('phase_ready','NOT phase_coherence BELOW 0.7'))
    system=reg.register(define_predicate('system_guard','((risk ABOVE 0.8 OR memory_pressure ABOVE 0.9) AND NOT phase_coherence BELOW 0.7)',dependencies=(safety.content.content_id,phase.content.content_id)))
    branch=reg.register(define_branch('safety_bifurcation','IF (risk ABOVE 0.8 OR memory_pressure ABOVE 0.9) THEN GO safety.pause ELSE GO runtime.continue',dependencies=(safety.content.content_id,)))
    contents={x.content.content_id:x.content for x in (high,safety,phase,system,branch)}
    return reg,contents,high,safety,phase,system,branch


def _classes():
    _,contents,high,safety,phase,system,branch=_defs()
    reg=ClassRegistry(contents)
    monitor=reg.register(define_class('safety_monitor',(high.content.content_id,phase.content.content_id),provenance=('class:a',)))
    reg.register(define_class('risk_phase_monitor',(high.content.content_id,phase.content.content_id),provenance=('class:b',)))
    guard=reg.register(define_class('guard_pipeline',(safety.content.content_id,phase.content.content_id),provenance=('class:c',)))
    controller=reg.register(define_class('safety_controller',(system.content.content_id,branch.content.content_id),provenance=('class:d',)))
    full=reg.register(define_class('phase_safety_pipeline',(phase.content.content_id,system.content.content_id,branch.content.content_id),provenance=('class:e',)))
    return reg,monitor,guard,controller,full,contents


def test_alias_not_semantic_identity():
    reg,monitor,*_= _classes()
    assert reg.resolve_alias('safety_monitor')==reg.resolve_alias('risk_phase_monitor')
    assert reg.aliases_for(monitor.content.content_id)==('risk_phase_monitor','safety_monitor')


def test_class_content_references_definition_ids_only():
    _,monitor,*_= _classes()
    payload=monitor.content.semantic_payload
    assert payload['level']=='CLASS'
    assert set(payload)=={'schema','level','path_mode','definition_ids'}
    assert 'canonical_graph' not in payload and 'leaf_path' not in payload


def test_order_is_semantic_at_class_level():
    _,contents,high,_,phase,_,_=_defs()
    a=define_class('a',(high.content.content_id,phase.content.content_id))
    b=define_class('b',(phase.content.content_id,high.content.content_id))
    assert a.content.content_id!=b.content.content_id


def test_definition_alias_does_not_enter_class_identity():
    dreg,contents,high,_,phase,_,_=_defs()
    assert dreg.resolve_alias('high_risk')==dreg.resolve_alias('risk_guard')
    a=define_class('a',(dreg.resolve_alias('high_risk'),phase.content.content_id))
    b=define_class('b',(dreg.resolve_alias('risk_guard'),phase.content.content_id))
    assert a.content.content_id==b.content.content_id


def test_inverse_expansion_to_definitions_and_kaku():
    reg,monitor,_,controller,full,_=_classes()
    assert len(reg.expand_definitions('safety_monitor'))==2
    assert reg.expand_leaves('safety_monitor')==('DIFFERENCE','CONDITION','ORDER','DIFFERENCE','CONDITION','NEGATION','COMPOSITION')
    leaves=reg.expand_leaves(controller.content.content_id)
    assert 'ORDER' in leaves and 'COMPOSITION' in leaves and 'ACTION_REQUEST' not in leaves
    assert reg.expand_leaves('phase_safety_pipeline')==reg.expand_leaves(full.content.content_id)


def test_missing_definition_fails_closed():
    _,contents,*_=_defs()
    reg=ClassRegistry(contents)
    missing='pncs:def:sha256:'+'0'*64
    with pytest.raises(ClassV12Error,match='dependency not registered'):
        reg.register(define_class('x',(missing,)))


def test_duplicate_alias_fails_closed():
    _,contents,high,*_=_defs()
    reg=ClassRegistry(contents)
    reg.register(define_class('same',(high.content.content_id,)))
    with pytest.raises(ClassV12Error,match='duplicate class alias'):
        reg.register(define_class('same',(high.content.content_id,)))


def test_provenance_changes_record_not_content():
    _,_,high,_,phase,_,_=_defs()
    a=define_class('a',(high.content.content_id,phase.content.content_id),provenance=('A',))
    b=define_class('b',(high.content.content_id,phase.content.content_id),provenance=('B',))
    assert a.content.content_id==b.content.content_id
    assert a.record_id!=b.record_id


def test_serialized_registry_verifies():
    rows=[json.loads(x) for x in REGISTRY_PATH.read_text(encoding='utf-8').splitlines() if x.strip()]
    assert len(rows)==5
    for row in rows:
        verify_serialized_class_record(row)
        assert row['canon_allowed'] is False and row['epistemic_operator']=='CHYBA'
    assert len({r['content_id'] for r in rows})==4


def test_serialized_tamper_detected():
    row=json.loads(REGISTRY_PATH.read_text(encoding='utf-8').splitlines()[0])
    row['content']['definition_ids']=list(reversed(row['content']['definition_ids']))
    with pytest.raises(ClassV12Error,match='content digest mismatch'):
        verify_serialized_class_record(row)


def test_content_index_alias_sets_match_registry():
    index=json.loads(INDEX_PATH.read_text(encoding='utf-8'))
    rows=[json.loads(x) for x in REGISTRY_PATH.read_text(encoding='utf-8').splitlines() if x.strip()]
    by={}
    for r in rows: by.setdefault(r['content_id'],[]).append(r['alias'])
    assert index['class_content_count']==4 and index['class_alias_count']==5
    for item in index['classes']:
        assert item['aliases']==sorted(by[item['content_id']])


def test_native_class_file_uses_only_recovered_opcodes():
    lines=[x.strip() for x in PNV_PATH.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#')]
    assert lines[:3]==['PNV 1','EPISTEMIC CHYBA','MODE READ_ONLY']
    for line in lines[3:]:
        p=line.split()
        if p[0]=='OP': assert p[2] in ALLOWED_OPS,line
        else: assert p[0] in {'VECTOR','EMIT'}


def test_native_classes_reference_definition_roots_not_aliases():
    active='\n'.join(x.strip() for x in PNV_PATH.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#'))
    for alias in ('safety_monitor','risk_phase_monitor','guard_pipeline','safety_controller','phase_safety_pipeline'):
        assert alias not in active
    assert 'D.' in active and '.ROOT' in active and 'C.' in active
    assert 'ACTION_REQUEST' not in active


def test_class_root_is_content_derived():
    _,monitor,*_= _classes()
    assert monitor.content.level=='CLASS'
    assert monitor.content.native_root_id.startswith('C.') and monitor.content.native_root_id.endswith('.ROOT')


def test_single_definition_class_is_valid_and_lossless():
    _,contents,high,*_=_defs()
    reg=ClassRegistry(contents)
    one=reg.register(define_class('one',(high.content.content_id,)))
    assert reg.expand_leaves(one.content.content_id)==high.content.leaf_path


def test_class_semantic_identity_changes_when_definition_changes():
    _,_,high,safety,phase,_,_=_defs()
    a=define_class('a',(high.content.content_id,phase.content.content_id))
    b=define_class('b',(safety.content.content_id,phase.content.content_id))
    assert a.content.content_id!=b.content.content_id
