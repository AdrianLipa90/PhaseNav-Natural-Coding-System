import hashlib,struct,math,json,pytest
from phasenav_natural_code.orchorbital_v27 import *
from phasenav_natural_code.orchorbital_hydro_v27 import *
from phasenav_natural_code.hydro_time_v27 import PhaseFlowState36,HydrodynamicPhaseGate

def mk():
 ids=('a','b','c'); aw=AttractorWeights(.6,.4,0); K=((0,.4,0),(.4,0,.4),(0,.4,0)); sp=ProcessSphere('s',ids,K,'leak',1.2); os=OrchState(0,'rel','intent',sp,(Orbital('a',1,0,.9,1,.4,1,.2,.7,aw),Orbital('b',1,.3,.8,-1,.4,1,.2,.7,aw),Orbital('c',1,.6,.7,0,.4,1,.2,.7,aw)),Potentials(0,0,0,0,0,0),'m0'); return os
def laws(crit=.5): return TimeLaw(1,0,.2,-.1,0,.2,.1,3),ReductionLaw(1,.5,.5,.2,crit),SelectionLaw(.1,.5,.2,.1,0,.2)
def test_geometry(): assert mk().sphere.payload['geometry_anchor']==GEOMETRY and mk().sphere.payload['bloch_scope']=='LOCAL_REDUCED_CHART_ONLY'
def test_k_symmetric_fail():
 with pytest.raises(OrchV27Error): ProcessSphere('s',('a','b'),((0,.2),(.1,0)),'l',1)
def test_observables():
 x=observables(mk()); assert 0<=x.coherence<=1 and x.defect==pytest.approx(1-x.coherence) and x.decoherence==pytest.approx(x.delta_h_re**2+x.delta_h_im**2)
def test_truth_scalar(): assert observables(mk()).truth==pytest.approx(1/3)
def test_time_explicit():
 o=mk(); t,r,s=laws(); a=orchestrate(o,t,r,s,.7,.1); assert a.time_law_id==t.law_id and a.scale('a')>0
def test_no_reduction_no_memory():
 o=mk(); t,r,s=laws(999); a=orchestrate(o,t,r,s,.2,1); assert not a.reduce and a.memory_residue_id is None
def test_reduction_residue():
 o=mk(); t,r,s=laws(-999); a=orchestrate(o,t,r,s,1,0); assert a.reduce and a.memory_residue_id
def test_ambiguous_fail():
 o=mk(); t=TimeLaw(1,0,0,0,0,0,.1,2); r=ReductionLaw(0,0,0,0,-1); s=SelectionLaw(0,0,0,0,0,0)
 with pytest.raises(OrchV27Error): orchestrate(o,t,r,s,0,0)
def sh(v): return hashlib.sha256(struct.pack('<36d',*v)).hexdigest()
def rec():
 vs={'DIFFERENCE':tuple(.01*i for i in range(36)),'CONDITION':tuple(.02*i for i in range(36)),'TRANSFORM':tuple(.03*i for i in range(36))}; prev='s0'; steps=[]
 for i,op in enumerate(vs,1):
  aft=f's{i}'; steps.append({'schema':'PNCS_KAKU_TRANSITION_V0_20','index':i,'operator_id':op,'operator_vector_sha256':sh(vs[op]),'before_sigma_id':prev,'after_sigma_id':aft,'bindings':{'truth':False} if op=='CONDITION' else {}}); prev=aft
 b={'schema':V20_SCHEMA,'execution_contract_id':V20_ID,'initial_sigma_id':'s0','final_sigma_id':'s3','steps':steps,'external_effects':False,'free_form_nl_execution':False}; b['receipt_sha256']=hashlib.sha256(json.dumps(b,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest(); return b,vs
def proj(): return ProjectionPolicy(.4,.2,1,.7,AttractorWeights(.6,.4,0),1,1.2,'leak')
def test_exact_occurrence_orbitals():
 r,v=rec(); o=build_orch_state(r,v,proj(),.2,'rel','intent',Potentials(0,0,0,0,0,0)); assert len({x.mode_id for x in o.orbitals})==3 and o.sphere.coupling[0][2]==0
def test_truth_from_binding():
 r,v=rec(); o=build_orch_state(r,v,proj(),.2,'rel','intent',Potentials(0,0,0,0,0,0)); assert o.orbitals[1].truth_spin==-1
def test_vector_tamper():
 r,v=rec(); v=dict(v); v['CONDITION']=tuple(.9 for _ in range(36))
 with pytest.raises(OrchHydroV27Error): build_orch_state(r,v,proj(),.2,'r','i',Potentials(0,0,0,0,0,0))
def test_receipt_tamper():
 r,v=rec(); r['steps'][0]['operator_id']='ORDER'
 with pytest.raises(OrchHydroV27Error): validate_receipt(r)
def test_transition_proper_time():
 r,v=rec(); o=build_orch_state(r,v,proj(),.2,'r','i',Potentials(0,0,0,0,0,0)); t,rl,sl=laws(999); g=HydrodynamicPhaseGate(1,0,coordinate_dt=.1); x=transition(PhaseFlowState36([.01*i for i in range(36)]),g,v['DIFFERENCE'],o,o.orbitals[0].mode_id,t,rl,sl,BridgePolicy(.01,10),.5,.1); assert x.proper_dt==pytest.approx(g.coordinate_dt*x.combined_lapse)
def test_winding_dynamic():
 r,v=rec(); o=build_orch_state(r,v,proj(),.2,'r','i',Potentials(0,0,0,0,0,0)); t,rl,sl=laws(999); g=HydrodynamicPhaseGate(1,0,coordinate_dt=.1); x=transition(PhaseFlowState36([.01*i for i in range(36)]),g,v['DIFFERENCE'],o,o.orbitals[0].mode_id,t,rl,sl,BridgePolicy(.01,10),.5,.1); assert x.winding_increment==pytest.approx((x.phase_delta/TAU)*(x.coordinate_dt/x.proper_dt))
def test_replay_order():
 r,v=rec(); o=build_orch_state(r,v,proj(),.2,'r','i',Potentials(0,0,0,0,0,0)); t,rl,sl=laws(999); gates={i:HydrodynamicPhaseGate(1,.1) for i in (1,2,3)}; x=replay(r,PhaseFlowState36([.01*i for i in range(36)]),o,v,gates,t,rl,sl,BridgePolicy(.01,10),.5,.1); assert x.operator_names==('DIFFERENCE','CONDITION','TRANSFORM') and x.reduction_count==0
def test_deterministic_trace():
 r,v=rec(); o=build_orch_state(r,v,proj(),.2,'r','i',Potentials(0,0,0,0,0,0)); t,rl,sl=laws(999); gates={i:HydrodynamicPhaseGate(1,.1) for i in (1,2,3)}; args=(r,PhaseFlowState36([.01*i for i in range(36)]),o,v,gates,t,rl,sl,BridgePolicy(.01,10)); assert replay(*args,.5,.1).trace_id==replay(*args,.5,.1).trace_id
