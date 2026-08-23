import copy
import hashlib
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

import pytest

BASE=Path("/mnt/data/pncs_v027")
for name in ("hydro_time_v27","hydro_schedule_v27","orch_orbital_v27","orch_hydro_v27"):
    spec=importlib.util.spec_from_file_location(name, BASE/f"{name}.py")
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)

h=sys.modules["hydro_time_v27"]
s=sys.modules["hydro_schedule_v27"]
o=sys.modules["orch_orbital_v27"]
oh=sys.modules["orch_hydro_v27"]

RECEIPT_PATH=Path("/dev/shm/ciel_noema/pncs/v0.20/receipts/84d40f600a8aa9e59ebc6dc42c856bcffec9265d04f791e7f5c49cdba2d583ad.json")
RECEIPT=json.loads(RECEIPT_PATH.read_text("utf-8"))
THETA=tuple((i+1)*0.1 for i in range(36))
STATE=h.PhaseFlowState36(THETA)
ZERO=(0.0,)*36

ATTRS=(
    o.AttractorReport("AttractorEC",0.75,ZERO,0.5,"CONFORMANCE_EC"),
    o.AttractorReport("AttractorZS",0.80,ZERO,0.5,"CONFORMANCE_ZS"),
    o.AttractorReport("AttractorLLMTemp",0.0,ZERO,0.0,"DISABLED_IN_PNCS_RUNTIME"),
)
POT=o.TotalPotential(0,0,0,0,0,0)
TIME=o.SubjectiveTimeKernel(
    beta_radius=-0.1,
    beta_coherence=0.4,
    beta_defect=-0.4,
    beta_mass=-0.2,
    beta_attractor=0.2,
)
REDUCE_NEVER=o.ReductionKernel(1,1,1,1,10.0)
PROFILE=oh.OrchHydroControlProfile(
    TIME,1.0,ATTRS,POT,REDUCE_NEVER,1.0,0.0,
    coupling_scale=0.15,coupling_gain=0.05,attractor_force_gain=1.0,
)
GATE=h.HydrodynamicPhaseGate(.5,.2,steps=1,coordinate_dt=.01)
SCHEDULE=s.uniform_schedule_for_receipt(RECEIPT,GATE)

def state():
    return o.bind_t36_state(
        STATE,tick=0,program_content_id=RECEIPT["program"]["content_id"],
        semantic_mass=RECEIPT["program"]["semantic_mass"],
        attractor_reports=ATTRS,potential=POT,
    )

def test_foundation_repo_and_commit_bound():
    assert o.ORCHORBITAL_FOUNDATION_REPOSITORY=="AdrianLipa90/CIEL-Omega-ApokalypOS"
    assert o.ORCHORBITAL_FOUNDATION_COMMIT=="aa0da54ef29a1f80dd0390427935342225388950"
    assert len(o.ORCHORBITAL_FOUNDATION_PATHS)==6

def test_t36_binding_has_36_orbitals():
    assert len(state().orbitals)==36

def test_sphere_declares_required_fields():
    p=state().sphere.payload
    for k in ("sphere_id","parent_sphere_id","child_sphere_ids","internal_modes","leak_mode","effective_attractor_weight"):
        assert k in p

def test_projective_kahler_anchor_preserved():
    assert "Kahler" in state().sphere.payload["geometric_anchor"]
    assert state().sphere.payload["bloch_chart_role"]=="LOCAL_REDUCED_CHART_ONLY"

def test_global_coherence_bounds():
    c=state().observables.global_coherence
    assert 0<=c<=1

def test_defect_exact_one_minus_coherence():
    obs=state().observables
    assert obs.defect==pytest.approx(1-obs.global_coherence)

def test_holonomic_defect_formula():
    obs=o.compute_observables((0.0, math.pi))
    assert obs.holonomic_defect_real==pytest.approx(0,abs=1e-12)
    assert obs.holonomic_defect_imag==pytest.approx(0,abs=1e-12)
    assert obs.relational_decoherence==pytest.approx(0,abs=1e-12)

def test_phase_proximity_coupling_symmetric_zero_diag():
    K=state().couplings
    for i in range(36):
        assert K[i][i]==0
        for j in range(36):
            assert K[i][j]==pytest.approx(K[j][i])

def test_phase_proximity_exact_same_phase():
    K=o.phase_proximity_couplings((0.0,0.0),scale=.3)
    assert K[0][1]==pytest.approx(.3)

def test_phase_proximity_opposite_phase_zero():
    K=o.phase_proximity_couplings((0.0,math.pi),scale=.3)
    assert K[0][1]==pytest.approx(0)

def test_total_potential_exact_sum():
    p=o.TotalPotential(1,2,3,4,5,6)
    assert p.total==21
    assert p.payload["contract_expression"]=="V_tot=V_EC+V_ZS+V_rel+V_mem+V_def+V_ext"

def test_attractor_effective_weight_explicit():
    assert o.effective_attractor_weight(ATTRS)==pytest.approx(.775)

def test_llm_temp_zero_weight_allowed():
    assert ATTRS[2].attractor_weight==0

def test_subjective_time_kernel_deterministic():
    a=TIME.evaluate(radius=1,coherence=.8,defect=.2,semantic_mass=.04,attractor_influence=.7)
    b=TIME.evaluate(radius=1,coherence=.8,defect=.2,semantic_mass=.04,attractor_influence=.7)
    assert a==b

def test_subjective_time_kernel_binds_all_contract_inputs():
    p=TIME.payload
    for k in ("beta_radius","beta_coherence","beta_defect","beta_mass","beta_attractor"):
        assert k in p

def test_subjective_time_no_physical_calibration_claim():
    assert TIME.payload["physical_calibration_claimed"] is False

def test_subjective_time_binding_formula():
    st=state()
    b=o.bind_subjective_time(st,TIME,orbital_radius=1.0,substrate_lapse=.5,coordinate_dt=.02)
    assert b.proper_dt==pytest.approx(.02*b.combined_g)
    assert b.payload["laboratory_time_modified"] is False

def test_winding_formula_exact():
    got=o.winding_increment(math.pi,.2,.1)
    assert got==pytest.approx(1.0)

def test_reduction_omega_formula():
    k=o.ReductionKernel(1,2,3,4,.5)
    got=k.omega(coherence=.7,relation_alignment=.8,defect=.3,xi=.1)
    assert got==pytest.approx(.7+1.6-.9-.4)

def test_no_selection_before_threshold():
    st=state()
    with pytest.raises(o.OrchOrbitalV27Error,match="before reduction"):
        o.decide_reduction(st,REDUCE_NEVER,relation_alignment=1,xi=0,selected_orbital_index=0)

def test_no_reduction_no_memory_update():
    st=state()
    d=o.decide_reduction(st,REDUCE_NEVER,relation_alignment=1,xi=0)
    assert d.reduce_ready is False
    assert o.memory_residue_after_reduction(st,d,identity_input_id="x") is None

def test_reduction_with_explicit_selection_yields_residue():
    st=state()
    k=o.ReductionKernel(1,1,0,0,-1)
    d=o.decide_reduction(st,k,relation_alignment=1,xi=0,selected_orbital_index=0)
    m=o.memory_residue_after_reduction(st,d,identity_input_id="receipt")
    assert d.reduce_ready is True
    assert m is not None and m.payload["memory_semantics"]=="REDUCTION_RESIDUE_NOT_RAW_INPUT_STORAGE"

def test_memory_residue_deterministic():
    st=state()
    k=o.ReductionKernel(1,1,0,0,-1)
    d=o.decide_reduction(st,k,relation_alignment=1,xi=0,selected_orbital_index=0)
    a=o.memory_residue_after_reduction(st,d,identity_input_id="receipt")
    b=o.memory_residue_after_reduction(st,d,identity_input_id="receipt")
    assert a.residue_id==b.residue_id

def test_orch_state_content_addressed():
    assert state().state_id==state().state_id

def test_orch_state_preserves_program_semantic_mass():
    st=state()
    assert st.semantic_mass==RECEIPT["program"]["semantic_mass"]

def test_profile_is_explicit_authority_not_mass_authority():
    assert PROFILE.payload["authority_semantics"]=="EXPLICIT_PROFILE_NOT_INFERRED_FROM_SEMANTIC_MASS"

def test_orchestrated_step_changes_state():
    vec=s.load_live_operator_vectors()[0]["DIFFERENCE"]
    step,after=oh.advance_orchestrated_phase_flow(
        STATE,GATE,vec,tick=0,program_content_id=RECEIPT["program"]["content_id"],
        semantic_mass=RECEIPT["program"]["semantic_mass"],profile=PROFILE,index=0,
    )
    assert step.after_phase_state.state_id!=STATE.state_id
    assert after.state_id==step.after_orch_state_id

def test_orchestrated_step_binds_winding():
    vec=s.load_live_operator_vectors()[0]["DIFFERENCE"]
    step,_=oh.advance_orchestrated_phase_flow(
        STATE,GATE,vec,tick=0,program_content_id=RECEIPT["program"]["content_id"],
        semantic_mass=RECEIPT["program"]["semantic_mass"],profile=PROFILE,index=0,
    )
    assert len(step.winding_rel)==36
    assert "w_rel" in step.payload["winding_components"]

def test_orchestrated_step_effects_closed():
    vec=s.load_live_operator_vectors()[0]["DIFFERENCE"]
    step,_=oh.advance_orchestrated_phase_flow(
        STATE,GATE,vec,tick=0,program_content_id=RECEIPT["program"]["content_id"],
        semantic_mass=RECEIPT["program"]["semantic_mass"],profile=PROFILE,index=0,
    )
    assert step.payload["external_effects"] is False
    assert step.payload["laboratory_time_modified"] is False

def test_exact_schedule_replay_has_nine_occurrences():
    tr=oh.replay_v20_orchorbital_hydrodynamic_schedule(RECEIPT,STATE,SCHEDULE,PROFILE)
    assert len(tr.occurrence_ids)==9

def test_exact_schedule_operator_order_preserved():
    tr=oh.replay_v20_orchorbital_hydrodynamic_schedule(RECEIPT,STATE,SCHEDULE,PROFILE)
    assert tr.operator_names==tuple(st["operator_id"] for st in RECEIPT["steps"])

def test_exact_schedule_receipt_bound():
    tr=oh.replay_v20_orchorbital_hydrodynamic_schedule(RECEIPT,STATE,SCHEDULE,PROFILE)
    assert tr.execution_receipt_sha256==RECEIPT["receipt_sha256"]

def test_exact_schedule_semantic_identity_preserved():
    tr=oh.replay_v20_orchorbital_hydrodynamic_schedule(RECEIPT,STATE,SCHEDULE,PROFILE)
    assert tr.program_content_id==RECEIPT["program"]["content_id"]
    assert tr.payload["semantic_identity_modified"] is False

def test_exact_schedule_semantic_mass_preserved():
    tr=oh.replay_v20_orchorbital_hydrodynamic_schedule(RECEIPT,STATE,SCHEDULE,PROFILE)
    assert tr.semantic_mass==RECEIPT["program"]["semantic_mass"]

def test_exact_schedule_effects_closed():
    tr=oh.replay_v20_orchorbital_hydrodynamic_schedule(RECEIPT,STATE,SCHEDULE,PROFILE)
    assert tr.payload["external_effects"] is False

def test_exact_schedule_executor_coupling_still_pending():
    tr=oh.replay_v20_orchorbital_hydrodynamic_schedule(RECEIPT,STATE,SCHEDULE,PROFILE)
    assert tr.payload["executor_coupling"]=="PENDING"

def test_no_stable_memory_without_selection():
    tr=oh.replay_v20_orchorbital_hydrodynamic_schedule(RECEIPT,STATE,SCHEDULE,PROFILE)
    assert tr.stable_memory_update_count==0

def test_different_explicit_time_kernels_change_proper_time_not_identity():
    slow=o.SubjectiveTimeKernel(beta_coherence=-1.0,beta_defect=1.0)
    fast=o.SubjectiveTimeKernel(beta_coherence=1.0,beta_defect=-1.0)
    pa=oh.OrchHydroControlProfile(slow,1,ATTRS,POT,REDUCE_NEVER,1,0)
    pb=oh.OrchHydroControlProfile(fast,1,ATTRS,POT,REDUCE_NEVER,1,0)
    a=oh.replay_v20_orchorbital_hydrodynamic_schedule(RECEIPT,STATE,SCHEDULE,pa)
    b=oh.replay_v20_orchorbital_hydrodynamic_schedule(RECEIPT,STATE,SCHEDULE,pb)
    assert a.program_content_id==b.program_content_id==RECEIPT["program"]["content_id"]
    assert a.proper_time_advanced!=b.proper_time_advanced
    assert a.trace_id!=b.trace_id

def test_attractor_force_changes_effective_drive():
    force=list(ZERO); force[0]=1.0
    attrs=(
      o.AttractorReport("AttractorEC",1.0,tuple(force),1.0,"FORCE"),
      o.AttractorReport("AttractorZS",0.0,ZERO,0.0,"ZERO"),
      o.AttractorReport("AttractorLLMTemp",0.0,ZERO,0.0,"DISABLED"),
    )
    p=oh.OrchHydroControlProfile(TIME,1,attrs,POT,REDUCE_NEVER,1,0,attractor_force_gain=.5)
    vec=s.load_live_operator_vectors()[0]["DIFFERENCE"]
    step,_=oh.advance_orchestrated_phase_flow(
        STATE,GATE,vec,tick=0,program_content_id=RECEIPT["program"]["content_id"],
        semantic_mass=RECEIPT["program"]["semantic_mass"],profile=p,index=0,
    )
    assert step.drive_sha256!=step.effective_drive_sha256

def test_live_operator_hashes_still_exact():
    ops,_=s.load_live_operator_vectors()
    for st in RECEIPT["steps"]:
        assert hashlib.sha256(struct.pack("<36d",*ops[st["operator_id"]])).hexdigest()==st["operator_vector_sha256"]

def test_tampered_receipt_rejected():
    r=copy.deepcopy(RECEIPT); r["result"]["control_location"]="x"
    with pytest.raises(Exception):
        oh.replay_v20_orchorbital_hydrodynamic_schedule(r,STATE,SCHEDULE,PROFILE)
