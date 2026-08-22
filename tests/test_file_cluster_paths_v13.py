from __future__ import annotations

import json
from pathlib import Path
import pytest

from phasenav_natural_code.classes_v12 import ClassRegistry, define_class
from phasenav_natural_code.definitions_v11 import DefinitionRegistry, define_branch, define_predicate
from phasenav_natural_code.paths_v13 import (
    ClusterRegistry,
    FileRegistry,
    PathV13Error,
    define_cluster,
    define_file,
    verify_serialized_cluster_record,
    verify_serialized_file_record,
)

ROOT=Path(__file__).parents[1]
FILE_REGISTRY=ROOT/'files'/'PNCS_FILE_REGISTRY_V0_13.jsonl'
FILE_INDEX=ROOT/'files'/'PNCS_FILE_CONTENT_INDEX_V0_13.json'
CLUSTER_REGISTRY=ROOT/'clusters'/'PNCS_CLUSTER_REGISTRY_V0_13.jsonl'
CLUSTER_INDEX=ROOT/'clusters'/'PNCS_CLUSTER_CONTENT_INDEX_V0_13.json'
PNV_PATH=ROOT/'native'/'PNCS_FILE_CLUSTER_PATHS_V0_13.pnv'
ALLOWED_OPS={"IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION","QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT","SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY","MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY","SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL","PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR","SOFT_CLIP","RESOLVE","DERIVE"}


def _hierarchy():
    dreg=DefinitionRegistry()
    high=dreg.register(define_predicate('high_risk','risk ABOVE 0.8'))
    dreg.register(define_predicate('risk_guard','risk > .800'))
    safety=dreg.register(define_predicate('safety_trigger','(risk ABOVE 0.8 OR memory_pressure ABOVE 0.9)'))
    phase=dreg.register(define_predicate('phase_ready','NOT phase_coherence BELOW 0.7'))
    system=dreg.register(define_predicate('system_guard','((risk ABOVE 0.8 OR memory_pressure ABOVE 0.9) AND NOT phase_coherence BELOW 0.7)',dependencies=(safety.content.content_id,phase.content.content_id)))
    branch=dreg.register(define_branch('safety_bifurcation','IF (risk ABOVE 0.8 OR memory_pressure ABOVE 0.9) THEN GO safety.pause ELSE GO runtime.continue',dependencies=(safety.content.content_id,)))
    defs={x.content.content_id:x.content for x in (high,safety,phase,system,branch)}

    creg=ClassRegistry(defs)
    monitor=creg.register(define_class('safety_monitor',(high.content.content_id,phase.content.content_id)))
    creg.register(define_class('risk_phase_monitor',(high.content.content_id,phase.content.content_id)))
    guard=creg.register(define_class('guard_pipeline',(safety.content.content_id,phase.content.content_id)))
    controller=creg.register(define_class('safety_controller',(system.content.content_id,branch.content.content_id)))
    full=creg.register(define_class('phase_safety_pipeline',(phase.content.content_id,system.content.content_id,branch.content.content_id)))

    freg=FileRegistry(creg)
    runtime=freg.register(define_file('safety_runtime_file',(monitor.content.content_id,controller.content.content_id),projection_path='src/runtime/safety.pnv',provenance=('file:a',)))
    freg.register(define_file('runtime_safety_file',(monitor.content.content_id,controller.content.content_id),projection_path='modules/safety_runtime.pnv',provenance=('file:b',)))
    phase_file=freg.register(define_file('phase_guard_file',(guard.content.content_id,full.content.content_id),projection_path='src/phase/guard.pnv',provenance=('file:c',)))
    monitor_file=freg.register(define_file('monitor_file',(monitor.content.content_id,),projection_path='src/monitor.pnv',provenance=('file:d',)))

    clreg=ClusterRegistry(freg)
    cluster=clreg.register(define_cluster('safety_cluster',(runtime.content.content_id,phase_file.content.content_id),projection_path='clusters/safety',provenance=('cluster:a',)))
    clreg.register(define_cluster('runtime_cluster',(runtime.content.content_id,phase_file.content.content_id),projection_path='deploy/runtime-safety',provenance=('cluster:b',)))
    monitor_cluster=clreg.register(define_cluster('monitor_cluster',(monitor_file.content.content_id,runtime.content.content_id),projection_path='clusters/monitor',provenance=('cluster:c',)))
    return dreg,creg,freg,clreg,monitor,guard,controller,full,runtime,phase_file,monitor_file,cluster,monitor_cluster


def test_filesystem_projection_is_not_file_semantic_identity():
    *_,freg,clreg,monitor,guard,controller,full,runtime,phase_file,monitor_file,cluster,monitor_cluster=_hierarchy()
    assert freg.resolve_alias('safety_runtime_file')==freg.resolve_alias('runtime_safety_file')
    assert freg.record('safety_runtime_file').projection_path!=freg.record('runtime_safety_file').projection_path
    assert freg.record('safety_runtime_file').record_id!=freg.record('runtime_safety_file').record_id


def test_file_content_references_class_ids_only():
    *_,runtime,phase_file,monitor_file,cluster,monitor_cluster=_hierarchy()[8:]
    payload=runtime.content.semantic_payload
    assert set(payload)=={'schema','level','path_mode','class_ids'}
    assert payload['level']=='FILE'
    assert 'projection_path' not in payload and 'alias' not in payload


def test_file_order_is_semantic():
    _,creg,_,_,monitor,_,controller,*_=_hierarchy()
    a=define_file('a',(monitor.content.content_id,controller.content.content_id))
    b=define_file('b',(controller.content.content_id,monitor.content.content_id))
    assert a.content.content_id!=b.content.content_id


def test_file_alias_does_not_enter_semantic_identity():
    _,_,freg,*_=_hierarchy()
    assert freg.aliases_for(freg.resolve_alias('safety_runtime_file'))==('runtime_safety_file','safety_runtime_file')


def test_file_inverse_expansion_reaches_definition_and_kaku():
    _,_,freg,*_=_hierarchy()
    assert len(freg.expand_classes('safety_runtime_file'))==2
    assert len(freg.expand_definitions('safety_runtime_file'))>=4
    leaves=freg.expand_leaves('safety_runtime_file')
    assert 'DIFFERENCE' in leaves and 'CONDITION' in leaves and 'TRANSFORM' in leaves
    assert 'ACTION_REQUEST' not in leaves


def test_missing_class_dependency_fails_closed():
    _,creg,*_=_hierarchy()
    freg=FileRegistry(creg)
    missing='pncs:class:sha256:'+'0'*64
    with pytest.raises(PathV13Error,match='class dependency not registered'):
        freg.register(define_file('x',(missing,)))


def test_serialized_file_registry_verifies_and_projection_is_metadata():
    rows=[json.loads(x) for x in FILE_REGISTRY.read_text(encoding='utf-8').splitlines() if x.strip()]
    assert len(rows)==4
    for row in rows:
        verify_serialized_file_record(row)
        assert row['canon_allowed'] is False and row['epistemic_operator']=='CHYBA'
        assert 'projection_path' not in row['content']
    assert len({r['content_id'] for r in rows})==3


def test_serialized_file_tamper_detected():
    rows=[json.loads(x) for x in FILE_REGISTRY.read_text(encoding='utf-8').splitlines() if x.strip()]
    row=next(r for r in rows if len(r['content']['class_ids'])>1)
    row['content']['class_ids']=list(reversed(row['content']['class_ids']))
    with pytest.raises(PathV13Error,match='file content digest mismatch'):
        verify_serialized_file_record(row)


def test_file_content_index_matches_registry_aliases():
    index=json.loads(FILE_INDEX.read_text(encoding='utf-8'))
    rows=[json.loads(x) for x in FILE_REGISTRY.read_text(encoding='utf-8').splitlines() if x.strip()]
    by={}
    for r in rows: by.setdefault(r['content_id'],[]).append(r['alias'])
    assert index['file_content_count']==3 and index['file_alias_count']==4
    for item in index['files']:
        assert item['aliases']==sorted(by[item['content_id']])


def test_cluster_projection_is_not_semantic_identity():
    _,_,_,clreg,*_=_hierarchy()
    assert clreg.resolve_alias('safety_cluster')==clreg.resolve_alias('runtime_cluster')
    assert clreg.record('safety_cluster').projection_path!=clreg.record('runtime_cluster').projection_path
    assert clreg.record('safety_cluster').record_id!=clreg.record('runtime_cluster').record_id


def test_cluster_content_references_file_ids_only():
    *_,cluster,monitor_cluster=_hierarchy()
    payload=cluster.content.semantic_payload
    assert set(payload)=={'schema','level','path_mode','file_ids'}
    assert payload['level']=='CLUSTER'
    assert 'projection_path' not in payload and 'class_ids' not in payload


def test_cluster_order_is_semantic():
    _,_,freg,_,*rest=_hierarchy()
    a_id=freg.resolve_alias('safety_runtime_file')
    b_id=freg.resolve_alias('phase_guard_file')
    a=define_cluster('a',(a_id,b_id))
    b=define_cluster('b',(b_id,a_id))
    assert a.content.content_id!=b.content.content_id


def test_cluster_inverse_expansion_reaches_all_levels():
    _,_,_,clreg,*_=_hierarchy()
    assert len(clreg.expand_files('safety_cluster'))==2
    assert len(clreg.expand_classes('safety_cluster'))==4
    assert len(clreg.expand_definitions('safety_cluster'))>=8
    leaves=clreg.expand_leaves('safety_cluster')
    assert {'DIFFERENCE','CONDITION','ORDER','COMPOSITION','TRANSFORM'}.issubset(set(leaves))
    assert 'ACTION_REQUEST' not in leaves


def test_missing_file_dependency_fails_closed():
    _,_,freg,*_=_hierarchy()
    reg=ClusterRegistry(freg)
    missing='pncs:file:sha256:'+'0'*64
    with pytest.raises(PathV13Error,match='file dependency not registered'):
        reg.register(define_cluster('x',(missing,)))


def test_serialized_cluster_registry_verifies():
    rows=[json.loads(x) for x in CLUSTER_REGISTRY.read_text(encoding='utf-8').splitlines() if x.strip()]
    assert len(rows)==3
    for row in rows:
        verify_serialized_cluster_record(row)
        assert row['canon_allowed'] is False and row['epistemic_operator']=='CHYBA'
        assert 'projection_path' not in row['content']
    assert len({r['content_id'] for r in rows})==2


def test_serialized_cluster_tamper_detected():
    row=json.loads(CLUSTER_REGISTRY.read_text(encoding='utf-8').splitlines()[0])
    row['content']['file_ids']=list(reversed(row['content']['file_ids']))
    with pytest.raises(PathV13Error,match='cluster content digest mismatch'):
        verify_serialized_cluster_record(row)


def test_cluster_content_index_matches_registry_aliases():
    index=json.loads(CLUSTER_INDEX.read_text(encoding='utf-8'))
    rows=[json.loads(x) for x in CLUSTER_REGISTRY.read_text(encoding='utf-8').splitlines() if x.strip()]
    by={}
    for r in rows: by.setdefault(r['content_id'],[]).append(r['alias'])
    assert index['cluster_content_count']==2 and index['cluster_alias_count']==3
    for item in index['clusters']:
        assert item['aliases']==sorted(by[item['content_id']])


def test_native_file_cluster_paths_use_only_recovered_opcodes():
    lines=[x.strip() for x in PNV_PATH.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#')]
    assert lines[:3]==['PNV 1','EPISTEMIC CHYBA','MODE READ_ONLY']
    for line in lines[3:]:
        p=line.split()
        if p[0]=='OP': assert p[2] in ALLOWED_OPS,line
        else: assert p[0] in {'VECTOR','EMIT'}


def test_native_semantics_do_not_contain_alias_or_filesystem_projection():
    active='\n'.join(x.strip() for x in PNV_PATH.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#'))
    for forbidden in ('safety_runtime_file','runtime_safety_file','phase_guard_file','monitor_file','safety_cluster','runtime_cluster','monitor_cluster','src/runtime/safety.pnv','deploy/runtime-safety'):
        assert forbidden not in active
    assert 'C.' in active and 'F.' in active and 'CL.' in active


def test_native_file_roots_reference_class_roots_and_cluster_roots_reference_file_roots():
    active='\n'.join(x.strip() for x in PNV_PATH.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#'))
    file_lines=[x for x in active.splitlines() if x.startswith('OP F.')]
    cluster_lines=[x for x in active.splitlines() if x.startswith('OP CL.')]
    assert file_lines and cluster_lines
    assert any(' C.' in x for x in file_lines)
    assert any(' F.' in x for x in cluster_lines)


def test_single_child_file_and_cluster_are_lossless():
    _,creg,freg,_,monitor,*rest=_hierarchy()
    one_file=freg.record('monitor_file')
    assert freg.expand_leaves(one_file.content.content_id)==creg.expand_leaves(monitor.content.content_id)
    reg=ClusterRegistry(freg)
    one_cluster=reg.register(define_cluster('one',(one_file.content.content_id,)))
    assert reg.expand_leaves(one_cluster.content.content_id)==freg.expand_leaves(one_file.content.content_id)


def test_projection_path_changes_record_digest_not_semantic_digest():
    _,_,freg,*_=_hierarchy()
    cid=freg.resolve_alias('safety_runtime_file')
    a=freg.record('safety_runtime_file')
    b=freg.record('runtime_safety_file')
    assert a.content.content_id==b.content.content_id==cid
    assert a.record_id!=b.record_id


def test_duplicate_file_and_cluster_aliases_fail_closed():
    _,creg,freg,_,monitor,*_=_hierarchy()
    f=FileRegistry(creg)
    f.register(define_file('same',(monitor.content.content_id,)))
    with pytest.raises(PathV13Error,match='duplicate file alias'):
        f.register(define_file('same',(monitor.content.content_id,)))
    c=ClusterRegistry(freg)
    fid=freg.resolve_alias('monitor_file')
    c.register(define_cluster('same',(fid,)))
    with pytest.raises(PathV13Error,match='duplicate cluster alias'):
        c.register(define_cluster('same',(fid,)))
