import importlib.util, math, sys
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location("hydro_time_v27", "/mnt/data/pncs_v027/hydro_time_v27.py")
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)

THETA=tuple((i+1)*0.1 for i in range(36))
DRIVE=tuple(1.0 if i==0 else 0.0 for i in range(36))


def state(): return m.PhaseFlowState36(THETA)
def gate(**kw): return m.HydrodynamicPhaseGate(**({"density":1.0,"effective_viscosity":0.0}|kw))

def test_state_exact_36(): assert len(state().theta)==36
def test_state_rejects_35():
    with pytest.raises(m.HydrodynamicProperTimeV27Error): m.PhaseFlowState36(THETA[:-1])
def test_state_rejects_outside_torus():
    bad=list(THETA); bad[0]=m.TAU
    with pytest.raises(m.HydrodynamicProperTimeV27Error): m.PhaseFlowState36(bad)
def test_state_rejects_negative_tau():
    with pytest.raises(m.HydrodynamicProperTimeV27Error): m.PhaseFlowState36(THETA,phase_proper_time=-1)
def test_state_identity_deterministic(): assert state().state_id==state().state_id
def test_state_declares_no_lab_time_modification(): assert state().payload["laboratory_time_modified"] is False
def test_density_must_be_positive():
    with pytest.raises(m.HydrodynamicProperTimeV27Error): gate(density=0)
def test_viscosity_nonnegative():
    with pytest.raises(m.HydrodynamicProperTimeV27Error): gate(effective_viscosity=-0.1)
def test_dt_positive():
    with pytest.raises(m.HydrodynamicProperTimeV27Error): gate(coordinate_dt=0)
def test_steps_bounded():
    with pytest.raises(m.HydrodynamicProperTimeV27Error): gate(steps=0)
def test_sound_speed_density_relation(): assert gate(density=4).sound_speed==2.0
def test_lapse_density_viscosity_relation(): assert gate(density=4,effective_viscosity=1).lapse==1.0
def test_lapse_is_bounded_low(): assert gate(density=1e-12,effective_viscosity=1e6).lapse==gate().lapse_min
def test_lapse_is_bounded_high(): assert gate(density=1e6,effective_viscosity=0).lapse==gate().lapse_max
def test_gate_id_deterministic(): assert gate().gate_id==gate().gate_id
def test_tensor_is_36x36():
    G=m.effective_transport_tensor(state(),gate()); assert len(G)==36 and all(len(r)==36 for r in G)
def test_tensor_is_symmetric():
    s=m.PhaseFlowState36(THETA,[0.01*i for i in range(36)]); G=m.effective_transport_tensor(s,gate())
    assert all(G[i][j]==G[j][i] for i in range(36) for j in range(36))
def test_tensor_psd_on_probes():
    s=m.PhaseFlowState36(THETA,[0.01*i for i in range(36)]); g=gate(density=.25)
    for k in range(5):
        q=tuple(math.sin((i+1)*(k+1)) for i in range(36)); assert m.transport_quadratic_form(s,g,q)>=0
def test_zero_velocity_tensor_diag_density():
    G=m.effective_transport_tensor(state(),gate(density=2.5)); assert G[3][3]==2.5 and G[3][4]==0.0
def test_step_advances_tau_by_lapse_dt():
    g=gate(density=4,effective_viscosity=1,coordinate_dt=.02); st=m.advance_phase_flow(state(),g,DRIVE)
    assert st.proper_dt==pytest.approx(.02) and st.after_state.phase_proper_time==pytest.approx(.02)
def test_step_changes_phase(): assert m.advance_phase_flow(state(),gate(),DRIVE).after_state.theta!=state().theta
def test_step_keeps_phase_on_torus():
    s=m.PhaseFlowState36(tuple(m.TAU-1e-8 for _ in range(36)), tuple(1.0 for _ in range(36)))
    out=m.advance_phase_flow(s,gate(coordinate_dt=.1),DRIVE).after_state
    assert all(0<=x<m.TAU for x in out.theta)
def test_drive_normalization_makes_scale_invariant():
    a=m.advance_phase_flow(state(),gate(),DRIVE); b=m.advance_phase_flow(state(),gate(),tuple(7*x for x in DRIVE))
    assert a.step_id==b.step_id
def test_zero_drive_rejected():
    with pytest.raises(m.HydrodynamicProperTimeV27Error): m.advance_phase_flow(state(),gate(),(0.0,)*36)
def test_speed_bound_fails_closed():
    s=m.PhaseFlowState36(THETA,(100.0,)+(0.0,)*35)
    with pytest.raises(m.HydrodynamicProperTimeV27Error,match="max_speed"): m.advance_phase_flow(s,gate(max_speed=64),DRIVE)
def test_trace_step_count():
    t=m.run_hydrodynamic_gate(state(),gate(steps=11),DRIVE); assert len(t.step_ids)==11
def test_trace_coordinate_time():
    t=m.run_hydrodynamic_gate(state(),gate(steps=10,coordinate_dt=.02),DRIVE); assert t.coordinate_time==pytest.approx(.2)
def test_trace_proper_time_is_lapse_scaled():
    g=gate(density=.25,effective_viscosity=1,steps=20,coordinate_dt=.01); t=m.run_hydrodynamic_gate(state(),g,DRIVE)
    assert t.proper_time_advanced==pytest.approx(g.lapse*.2)
def test_same_inputs_same_trace():
    g=gate(steps=20); assert m.run_hydrodynamic_gate(state(),g,DRIVE).trace_id==m.run_hydrodynamic_gate(state(),g,DRIVE).trace_id
def test_density_viscosity_change_changes_trace():
    a=m.run_hydrodynamic_gate(state(),gate(density=.25,effective_viscosity=1,steps=50),DRIVE)
    b=m.run_hydrodynamic_gate(state(),gate(density=4,effective_viscosity=.1,steps=50),DRIVE)
    assert a.trace_id!=b.trace_id and a.proper_time_advanced<b.proper_time_advanced
def test_fast_substrate_larger_phase_displacement():
    a=m.run_hydrodynamic_gate(state(),gate(density=.25,effective_viscosity=1,steps=100),DRIVE)
    b=m.run_hydrodynamic_gate(state(),gate(density=4,effective_viscosity=.1,steps=100),DRIVE)
    da=m.torus_chord_distance(state().theta,a.final_state.theta); db=m.torus_chord_distance(state().theta,b.final_state.theta)
    assert db>da
def test_trace_declares_effects_closed(): assert m.run_hydrodynamic_gate(state(),gate(),DRIVE).payload["external_effects"] is False
def test_trace_declares_no_lab_time_modification(): assert m.run_hydrodynamic_gate(state(),gate(),DRIVE).payload["laboratory_time_modified"] is False
def test_noncanonical_live_root_rejected():
    with pytest.raises(m.HydrodynamicProperTimeV27Error,match="fixed"): m.load_live_phase_and_drive("TRANSFORM",Path("/tmp"))
def test_torus_distance_zero_for_same(): assert m.torus_chord_distance(THETA,THETA)==0.0
def test_torus_distance_wrap_short_path():
    a=list(THETA); b=list(THETA); a[0]=.01; b[0]=m.TAU-.01
    assert m.torus_chord_distance(a,b)==pytest.approx(.02)
