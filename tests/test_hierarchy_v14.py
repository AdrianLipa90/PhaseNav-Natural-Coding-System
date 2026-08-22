from __future__ import annotations

import json
from pathlib import Path
import pytest

from phasenav_natural_code.definitions_v11 import DefinitionRegistry, define_predicate, define_branch
from phasenav_natural_code.classes_v12 import ClassRegistry, define_class
from phasenav_natural_code.paths_v13 import FileRegistry, ClusterRegistry, define_file, define_cluster
from phasenav_natural_code.hierarchy_v14 import (
    HierarchyRegistry, HierarchyV14Error,
    define_subsystem, define_daemon, define_low_orchestrator,
    define_high_orchestrator, define_system, verify_serialized_higher_record,
)

ROOT=Path(__file__).parents[1]
REGISTRY=ROOT/'hierarchy'/'PNCS_HIGHER_PATH_REGISTRY_V0_14.jsonl'
INDEX=ROOT/'hierarchy'/'PNCS_HIGHER_PATH_CONTENT_INDEX_V0_14.json'
PNV=ROOT/'native'/'PNCS_HIGHER_PATHS_V0_14.pnv'
ALLOWED_OPS={"IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION","QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT","SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY","MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY","SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL","PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR","SOFT_CLIP","RESOLVE","DERIVE"}


def _base():
    d=DefinitionRegistry()
    high=d.register(define_predicate('high_risk','risk ABOVE 0.8'))
    safety=d.register(define_predicate('safety_trigger','(risk ABOVE 0.8 OR memory_pressure ABOVE 0.9)'))
    phase=d.register(define_predicate('phase_ready','NOT phase_coherence BELOW 0.7'))
    system=d.register(define_predicate('system_guard','((risk ABOVE 0.8 OR memory_pressure ABOVE 0.9) AND NOT phase_coherence BELOW 0.7)',dependencies=(safety.content.content_id,phase.content.content_id)))
    branch=d.register(define_branch('safety_bifurcation','IF (risk ABOVE 0.8 OR memory_pressure ABOVE 0.9) THEN GO safety.pause ELSE GO runtime.continue',dependencies=(safety.content.content_id,)))
    defs={x.content.content_id:x.content for x in (high,safety,phase,system,branch)}
    c=ClassRegistry(defs)
    monitor=c.register(define_class('safety_monitor',(high.content.content_id,phase.content.content_id)))
    guard=c.register(define_class('guard_pipeline',(safety.content.content_id,phase.content.content_id)))
    controller=c.register(define_class('safety_controller',(system.content.content_id,branch.content.content_id)))
    full=c.register(define_class('phase_safety_pipeline',(phase.content.content_id,system.content.content_id,branch.content.content_id)))
    f=FileRegistry(c)
    runtime=f.register(define_file('safety_runtime_file',(monitor.content.content_id,controller.content.content_id)))
    phase_file=f.register(define_file('phase_guard_file',(guard.content.content_id,full.content.content_id)))
    monitor_file=f.register(define_file('monitor_file',(monitor.content.content_id,)))
    cl=ClusterRegistry(f)
    safety_cluster=cl.register(define_cluster('safety_cluster',(runtime.content.content_id,phase_file.content.content_id)))
    monitor_cluster=cl.register(define_cluster('monitor_cluster',(monitor_file.content.content_id,runtime.content.content_id)))
    return d,c,f,cl,safety_cluster,monitor_cluster


def _higher():
    *_,cl,safety_cluster,monitor_cluster=_base()
    h=HierarchyRegistry(cl)
    subsystem=h.register(define_subsystem('safety_subsystem',(safety_cluster.content.content_id,),projection_path='services/safety',provenance=('ss:a',)))
    h.register(define_subsystem('safety_subsystem_alias',(safety_cluster.content.content_id,),projection_path='runtime/services/safety',provenance=('ss:b',)))
    daemon=h.register(define_daemon('monitor_daemon',(monitor_cluster.content.content_id,),projection_path='daemons/monitor',provenance=('dm:a',)))
    low=h.register(define_low_orchestrator('safety_low',(subsystem.content.content_id,daemon.content.content_id),projection_path='orchestrators/low/safety',provenance=('lo:a',)))
    low_rev=h.register(define_low_orchestrator('monitor_low',(daemon.content.content_id,subsystem.content.content_id),projection_path='orchestrators/low/monitor',provenance=('lo:b',)))
    high=h.register(define_high_orchestrator('safety_high',(low.content.content_id,low_rev.content.content_id),projection_path='orchestrators/high/safety',provenance=('ho:a',)))
    high_single=h.register(define_high_orchestrator('monitor_high',(low_rev.content.content_id,),projection_path='orchestrators/high/monitor',provenance=('ho:b',)))
    system=h.register(define_system('pncs_safety_system',(high.content.content_id,high_single.content.content_id),projection_path='systems/pncs-safety',provenance=('sys:a',)))
    return h,subsystem,daemon,low,low_rev,high,high_single,system,safety_cluster,monitor_cluster


def test_subsystem_alias_and_projection_not_semantic_identity():
    h,subsystem,*_=_higher()
    assert h.resolve_alias('safety_subsystem')==h.resolve_alias('safety_subsystem_alias')
    assert h.record('safety_subsystem').projection_path!=h.record('safety_subsystem_alias').projection_path
    assert h.record('safety_subsystem').record_id!=h.record('safety_subsystem_alias').record_id


def test_subsystem_and_daemon_same_child_are_different_semantic_levels():
    *_,cl,safety_cluster,monitor_cluster=_base()
    ss=define_subsystem('ss',(safety_cluster.content.content_id,))
    dm=define_daemon('dm',(safety_cluster.content.content_id,))
    assert ss.content.content_id!=dm.content.content_id
    assert ss.content.semantic_payload['level']=='SUBSYSTEM'
    assert dm.content.semantic_payload['level']=='DAEMON'


def test_low_orchestrator_accepts_subsystem_and_daemon():
    h,subsystem,daemon,low,*_=_higher()
    assert h.children('safety_low')==(subsystem.content.content_id,daemon.content.content_id)
    assert low.content.native_root_id.startswith('LO.')


def test_low_orchestrator_order_is_semantic():
    _,_,_,low,low_rev,*_=_higher()
    assert low.content.content_id!=low_rev.content.content_id


def test_high_orchestrator_requires_low_children():
    h,subsystem,*_=_higher()
    with pytest.raises(HierarchyV14Error,match='invalid high_orchestrator child'):
        define_high_orchestrator('bad',(subsystem.content.content_id,))


def test_system_requires_high_children():
    h,subsystem,daemon,low,*_=_higher()
    with pytest.raises(HierarchyV14Error,match='invalid system child'):
        define_system('bad',(low.content.content_id,))


def test_full_inverse_lineage_reaches_cluster_file_class_definition_kaku():
    h,*rest=_higher()
    system=rest[6]
    assert len(h.expand_clusters(system.content.content_id))>=4
    assert len(h.expand_files(system.content.content_id))>=8
    assert len(h.expand_classes(system.content.content_id))>=12
    assert len(h.expand_definitions(system.content.content_id))>=20
    leaves=h.expand_leaves(system.content.content_id)
    assert {'DIFFERENCE','CONDITION','ORDER','COMPOSITION','NEGATION','TRANSFORM'}.issubset(set(leaves))
    assert 'ACTION_REQUEST' not in leaves


def test_missing_cluster_dependency_fails_closed():
    *_,cl,_,_=_base()
    h=HierarchyRegistry(cl)
    missing='pncs:cluster:sha256:'+'0'*64
    with pytest.raises(HierarchyV14Error,match='child dependency not registered'):
        h.register(define_subsystem('x',(missing,)))


def test_registration_order_fails_closed_for_unregistered_low_dependency():
    *_,cl,safety_cluster,monitor_cluster=_base()
    h=HierarchyRegistry(cl)
    fake='pncs:subsystem:sha256:'+'1'*64
    with pytest.raises(HierarchyV14Error,match='child dependency not registered'):
        h.register(define_low_orchestrator('x',(fake,)))


def test_serialized_registry_verifies_all_levels():
    rows=[json.loads(x) for x in REGISTRY.read_text(encoding='utf-8').splitlines() if x.strip()]
    assert len(rows)==8
    assert {r['level'] for r in rows}=={'SUBSYSTEM','DAEMON','LOW_ORCHESTRATOR','HIGH_ORCHESTRATOR','SYSTEM'}
    for row in rows:
        verify_serialized_higher_record(row)
        assert row['canon_allowed'] is False and row['epistemic_operator']=='CHYBA'
        assert 'projection_path' not in row['content']


def test_serialized_tamper_detected():
    rows=[json.loads(x) for x in REGISTRY.read_text(encoding='utf-8').splitlines() if x.strip()]
    row=next(r for r in rows if len(r['content']['child_ids'])>1)
    row['content']['child_ids']=list(reversed(row['content']['child_ids']))
    with pytest.raises(HierarchyV14Error,match='content digest mismatch'):
        verify_serialized_higher_record(row)


def test_content_index_counts_and_alias_sets():
    index=json.loads(INDEX.read_text(encoding='utf-8'))
    rows=[json.loads(x) for x in REGISTRY.read_text(encoding='utf-8').splitlines() if x.strip()]
    assert index['record_count']==8
    assert index['content_count']==7
    assert index['counts_by_level']=={'DAEMON':1,'HIGH_ORCHESTRATOR':2,'LOW_ORCHESTRATOR':2,'SUBSYSTEM':1,'SYSTEM':1}
    by={}
    for r in rows: by.setdefault(r['content_id'],[]).append(r['alias'])
    for item in index['contents']:
        assert item['aliases']==sorted(by[item['content_id']])


def test_native_file_uses_only_recovered_opcodes():
    lines=[x.strip() for x in PNV.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#')]
    assert lines[:3]==['PNV 1','EPISTEMIC CHYBA','MODE READ_ONLY']
    for line in lines[3:]:
        p=line.split()
        if p[0]=='OP': assert p[2] in ALLOWED_OPS,line
        else: assert p[0] in {'VECTOR','EMIT'}


def test_native_roots_follow_level_chain():
    active='\n'.join(x.strip() for x in PNV.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#'))
    assert 'OP SS.' in active and ' CL.' in active
    assert 'OP DM.' in active and ' CL.' in active
    assert 'OP LO.' in active and (' SS.' in active or ' DM.' in active)
    assert 'OP HO.' in active and ' LO.' in active
    assert 'OP SYS.' in active and ' HO.' in active


def test_native_semantics_exclude_aliases_and_projection_paths():
    active='\n'.join(x.strip() for x in PNV.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#'))
    for forbidden in ('safety_subsystem','monitor_daemon','safety_low','monitor_low','safety_high','monitor_high','pncs_safety_system','services/safety','systems/pncs-safety'):
        assert forbidden not in active


def test_system_root_is_content_derived():
    *_,system,_,_=_higher()
    assert system.content.native_root_id.startswith('SYS.') and system.content.native_root_id.endswith('.ROOT')
    assert system.content.content_id.startswith('pncs:system:sha256:')


def test_projection_changes_record_not_semantic_digest():
    h,subsystem,*_=_higher()
    alias=h.record('safety_subsystem_alias')
    assert subsystem.content.content_id==alias.content.content_id
    assert subsystem.record_id!=alias.record_id


def test_duplicate_alias_across_levels_fails_closed():
    *_,cl,safety_cluster,monitor_cluster=_base()
    h=HierarchyRegistry(cl)
    h.register(define_subsystem('same',(safety_cluster.content.content_id,)))
    with pytest.raises(HierarchyV14Error,match='duplicate higher-path alias'):
        h.register(define_daemon('same',(monitor_cluster.content.content_id,)))


def test_single_child_each_level_is_lossless_except_level_wrappers():
    *_,cl,safety_cluster,monitor_cluster=_base()
    h=HierarchyRegistry(cl)
    ss=h.register(define_subsystem('ss',(safety_cluster.content.content_id,)))
    lo=h.register(define_low_orchestrator('lo',(ss.content.content_id,)))
    ho=h.register(define_high_orchestrator('ho',(lo.content.content_id,)))
    sy=h.register(define_system('sy',(ho.content.content_id,)))
    assert h.expand_leaves(sy.content.content_id)==cl.expand_leaves(safety_cluster.content.content_id)


def test_same_children_different_level_never_hash_equal():
    *_,cl,safety_cluster,monitor_cluster=_base()
    ss=define_subsystem('ss',(safety_cluster.content.content_id,))
    dm=define_daemon('dm',(safety_cluster.content.content_id,))
    assert ss.content.semantic_payload['child_ids']==dm.content.semantic_payload['child_ids']
    assert ss.content.content_id!=dm.content.content_id
