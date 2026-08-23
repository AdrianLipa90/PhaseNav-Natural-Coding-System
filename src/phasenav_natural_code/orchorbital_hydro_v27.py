from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,math,struct
from typing import Mapping,Sequence
from .hydro_time_v27 import DIM,TAU,HydrodynamicPhaseGate,PhaseFlowState36,transport_tensor_sha256
from .orchorbital_v27 import AttractorWeights,OrchState,Orbital,Potentials,ProcessSphere,ReductionLaw,SelectionLaw,TimeLaw,orchestrate

BRIDGE_ID='PNCS_ORCHORBITAL_HYDRO_T36_BRIDGE_V0_27'; SCHEDULE_ID='PNCS_ORCHORBITAL_EXACT_KAKU_SCHEDULE_V0_27'; V20_SCHEMA='PNCS_NATIVE_EXECUTION_RECEIPT_V0_20'; V20_ID='PNCS_NATIVE_EXECUTION_CORE_V0_20'
class OrchHydroV27Error(ValueError): pass

def _j(v):
    if isinstance(v,dict): return {str(k):_j(v[k]) for k in sorted(v)}
    if isinstance(v,(tuple,list)): return [_j(x) for x in v]
    if isinstance(v,float):
        if not math.isfinite(v): raise OrchHydroV27Error('non-finite canonical value')
        return v
    if v is None or isinstance(v,(str,int,bool)): return v
    raise OrchHydroV27Error(f'unsupported canonical type: {type(v).__name__}')
def _sha(v): return hashlib.sha256(json.dumps(_j(v),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def _id(p,v): return f'{p}:sha256:{_sha(v)}'
def _norm(v):
    x=tuple(float(a) for a in v)
    if len(x)!=DIM or not all(math.isfinite(a) for a in x): raise OrchHydroV27Error('exact 36D vector required')
    n=math.sqrt(sum(a*a for a in x))
    if n<=0: raise OrchHydroV27Error('zero drive')
    return tuple(a/n for a in x)
def _delta(a,b): return (a-b+math.pi)%TAU-math.pi

def validate_receipt(r:Mapping[str,object])->str:
    if not isinstance(r,Mapping) or r.get('schema')!=V20_SCHEMA or r.get('execution_contract_id')!=V20_ID: raise OrchHydroV27Error('exact v0.20 receipt required')
    h=r.get('receipt_sha256'); body=dict(r); body.pop('receipt_sha256',None)
    if not isinstance(h,str) or len(h)!=64 or _sha(body)!=h: raise OrchHydroV27Error('v0.20 receipt digest mismatch')
    if r.get('external_effects') is not False or r.get('free_form_nl_execution') is not False: raise OrchHydroV27Error('closed boundary crossed')
    steps=r.get('steps'); prev=r.get('initial_sigma_id')
    if not isinstance(steps,list) or not steps: raise OrchHydroV27Error('steps missing')
    for i,s in enumerate(steps,1):
        if not isinstance(s,Mapping) or s.get('schema')!='PNCS_KAKU_TRANSITION_V0_20' or s.get('index')!=i or s.get('before_sigma_id')!=prev: raise OrchHydroV27Error('KAKU chain invalid')
        if not isinstance(s.get('operator_id'),str) or not isinstance(s.get('operator_vector_sha256'),str) or len(str(s.get('operator_vector_sha256')))!=64: raise OrchHydroV27Error('operator binding invalid')
        prev=s.get('after_sigma_id')
    if prev!=r.get('final_sigma_id'): raise OrchHydroV27Error('final Sigma mismatch')
    return h

@dataclass(frozen=True)
class ProjectionPolicy:
    adjacency_coupling:float; memory_affinity:float; orbital_radius:float; attractor_influence:float; attractor_weights:AttractorWeights; amplitude_scale:float=1.; sphere_attractor_weight:float=1.; leak_mode:str='parent_embedding'
    @property
    def payload(self): return {'schema':'PNCS_KAKU_ORBITAL_PROJECTION_POLICY_V0_27','adjacency_coupling':self.adjacency_coupling,'memory_affinity':self.memory_affinity,'orbital_radius':self.orbital_radius,'attractor_influence':self.attractor_influence,'attractor_weights':self.attractor_weights.payload,'amplitude_scale':self.amplitude_scale,'sphere_attractor_weight':self.sphere_attractor_weight,'leak_mode':self.leak_mode,'phase_projection':'CIRCULAR_MEAN_OF_EXACT_T36_OPERATOR_VECTOR','coherence_projection':'CIRCULAR_RESULTANT_OF_EXACT_T36_OPERATOR_VECTOR','amplitude_projection':'RMS_OF_EXACT_T36_OPERATOR_VECTOR'}
    @property
    def policy_id(self): return _id('pncs:kaku-orbital-policy',self.payload)

def build_orch_state(r:Mapping[str,object],vectors:Mapping[str,Sequence[float]],p:ProjectionPolicy,semantic_mass:float,relation_id:str,intent_id:str,potentials:Potentials,previous_memory_state_id:str|None=None)->OrchState:
    rh=validate_receipt(r); mass=float(semantic_mass)
    if mass<0 or not math.isfinite(mass) or not 0<=p.adjacency_coupling<=1 or not 0<=p.memory_affinity<=1 or p.orbital_radius<=0 or p.attractor_influence<0 or p.amplitude_scale<=0 or p.sphere_attractor_weight<=0: raise OrchHydroV27Error('invalid projection policy/input')
    modes=[]; ids=[]; steps=r['steps']; assert isinstance(steps,list)
    for s in steps:
        assert isinstance(s,Mapping); op=str(s['operator_id']).upper(); v=tuple(float(x) for x in vectors.get(op,()))
        if len(v)!=DIM or hashlib.sha256(struct.pack('<36d',*v)).hexdigest()!=s['operator_vector_sha256']: raise OrchHydroV27Error('operator vector bytes differ from receipt')
        re=sum(math.cos(x) for x in v); im=sum(math.sin(x) for x in v); phase=math.atan2(im,re)%TAU; coh=math.hypot(re,im)/DIM; amp=p.amplitude_scale*math.sqrt(sum(x*x for x in v)/DIM)
        b=s.get('bindings'); spin=(1 if b.get('truth') else -1) if isinstance(b,Mapping) and isinstance(b.get('truth'),bool) else 0
        mid=_id('pncs:kaku-orbital',{'receipt_sha256':rh,'step_index':s['index'],'operator_id':s['operator_id'],'operator_vector_sha256':s['operator_vector_sha256']}); ids.append(mid); modes.append(Orbital(mid,amp,phase,coh,spin,p.memory_affinity,p.orbital_radius,mass,p.attractor_influence,p.attractor_weights))
    n=len(ids); K=[[0.]*n for _ in range(n)]
    for i in range(n-1): K[i][i+1]=K[i+1][i]=p.adjacency_coupling
    sphere=ProcessSphere(_id('pncs:kaku-process-sphere',{'receipt_sha256':rh,'mode_ids':ids,'policy_id':p.policy_id}),tuple(ids),tuple(tuple(x) for x in K),p.leak_mode,p.sphere_attractor_weight)
    return OrchState(0,relation_id,intent_id,sphere,tuple(modes),potentials,previous_memory_state_id)

@dataclass(frozen=True)
class BridgePolicy:
    lapse_min:float; lapse_max:float
    @property
    def policy_id(self): return _id('pncs:orch-hydro-policy',{'lapse_min':self.lapse_min,'lapse_max':self.lapse_max,'phase_projection':'DRIVE_PROJECTION_T36_TO_ORBITAL_PHASE'})
@dataclass(frozen=True)
class Transition:
    mode_id:str; before_phase_id:str; after_phase:PhaseFlowState36; before_orch_id:str; after_orch:OrchState; pre_result_id:str; post_result_id:str; hydro_gate_id:str; bridge_policy_id:str; substrate_lapse:float; subjective_scale:float; combined_lapse:float; coordinate_dt:float; proper_dt:float; vector_sha256:str; tensor_sha256:str; phase_delta:float; winding_increment:float; memory_residue_id:str|None
    @property
    def payload(self): return {'schema':'PNCS_ORCH_HYDRO_TRANSITION_V0_27','contract_id':BRIDGE_ID,'mode_id':self.mode_id,'before_phase_id':self.before_phase_id,'after_phase_id':self.after_phase.state_id,'before_orch_id':self.before_orch_id,'after_orch_id':self.after_orch.state_id,'pre_result_id':self.pre_result_id,'post_result_id':self.post_result_id,'hydro_gate_id':self.hydro_gate_id,'bridge_policy_id':self.bridge_policy_id,'substrate_lapse':self.substrate_lapse,'subjective_scale':self.subjective_scale,'combined_lapse':self.combined_lapse,'coordinate_dt':self.coordinate_dt,'proper_dt':self.proper_dt,'vector_sha256':self.vector_sha256,'tensor_sha256':self.tensor_sha256,'phase_delta':self.phase_delta,'winding_increment':self.winding_increment,'memory_residue_id':self.memory_residue_id,'persistent_memory_write_performed':False,'external_effects':False,'laboratory_time_modified':False,'semantic_identity_modified':False}
    @property
    def transition_id(self): return _id('pncs:orch-hydro-transition',self.payload)

def transition(ps:PhaseFlowState36,g:HydrodynamicPhaseGate,vector:Sequence[float],os:OrchState,mode_id:str,tl:TimeLaw,rl:ReductionLaw,sl:SelectionLaw,bp:BridgePolicy,relation_alignment:float,contradiction_load:float)->Transition:
    pre=orchestrate(os,tl,rl,sl,relation_alignment,contradiction_load); scale=pre.scale(mode_id); lapse=g.lapse*scale
    if bp.lapse_min<=0 or bp.lapse_max<bp.lapse_min or not bp.lapse_min<=lapse<=bp.lapse_max: raise OrchHydroV27Error('combined lapse outside authority')
    d=_norm(vector); dt=lapse*g.coordinate_dt; u=ps.velocity; dot=sum(a*b for a,b in zip(u,d)); force=tuple(g.density*d[i]+u[i]*dot for i in range(DIM)); acc=tuple(g.drive_gain*force[i]-g.effective_viscosity*u[i] for i in range(DIM)); nu=tuple(u[i]+dt*acc[i] for i in range(DIM)); speed=math.sqrt(sum(x*x for x in nu))
    if not math.isfinite(speed) or speed>g.max_speed: raise OrchHydroV27Error('max_speed exceeded')
    theta=tuple((ps.theta[i]+dt*nu[i])%TAU for i in range(DIM)); aps=PhaseFlowState36(theta,nu,ps.phase_proper_time+dt); pd=sum(d[i]*_delta(aps.theta[i],ps.theta[i]) for i in range(DIM)); winding=(pd/TAU)*(g.coordinate_dt/dt); aos=os.advance_phase(mode_id,pd); post=orchestrate(aos,tl,rl,sl,relation_alignment,contradiction_load)
    return Transition(mode_id,ps.state_id,aps,os.state_id,aos,pre.result_id,post.result_id,g.gate_id,bp.policy_id,g.lapse,scale,lapse,g.coordinate_dt,dt,hashlib.sha256(struct.pack('<36d',*tuple(float(x) for x in vector))).hexdigest(),transport_tensor_sha256(ps,g),pd,winding,post.memory_residue_id)

@dataclass(frozen=True)
class ExecutionTrace:
    receipt_sha256:str; initial_phase_id:str; final_phase:PhaseFlowState36; initial_orch_id:str; final_orch:OrchState; transition_ids:tuple[str,...]; operator_names:tuple[str,...]; coordinate_time:float; proper_time:float; reduction_count:int; memory_residue_ids:tuple[str,...]
    @property
    def payload(self): return {'schema':'PNCS_ORCH_EXACT_KAKU_TRACE_V0_27','contract_id':SCHEDULE_ID,'receipt_sha256':self.receipt_sha256,'initial_phase_id':self.initial_phase_id,'final_phase_id':self.final_phase.state_id,'initial_orch_id':self.initial_orch_id,'final_orch_id':self.final_orch.state_id,'transition_ids':list(self.transition_ids),'operator_names':list(self.operator_names),'coordinate_time':self.coordinate_time,'proper_time':self.proper_time,'reduction_count':self.reduction_count,'memory_residue_ids':list(self.memory_residue_ids),'external_effects':False,'laboratory_time_modified':False,'semantic_identity_modified':False}
    @property
    def trace_id(self): return _id('pncs:orch-kaku-trace',self.payload)

def replay(r:Mapping[str,object],phase:PhaseFlowState36,orch:OrchState,vectors:Mapping[str,Sequence[float]],gates:Mapping[int,HydrodynamicPhaseGate],tl:TimeLaw,rl:ReductionLaw,sl:SelectionLaw,bp:BridgePolicy,relation_alignment:float,contradiction_load:float)->ExecutionTrace:
    rh=validate_receipt(r); steps=r['steps']; assert isinstance(steps,list)
    if len(orch.orbitals)!=len(steps): raise OrchHydroV27Error('orbital/occurrence count mismatch')
    ip=phase.state_id; io=orch.state_id; ids=[]; names=[]; residues=[]; coord=0.; start_tau=phase.phase_proper_time; reductions=0
    for pos,s in enumerate(steps):
        assert isinstance(s,Mapping); idx=int(s['index']); op=str(s['operator_id']).upper(); v=vectors.get(op); g=gates.get(idx)
        if v is None or g is None or hashlib.sha256(struct.pack('<36d',*tuple(float(x) for x in v))).hexdigest()!=s['operator_vector_sha256']: raise OrchHydroV27Error('exact occurrence vector/gate missing')
        t=transition(phase,g,v,orch,orch.orbitals[pos].mode_id,tl,rl,sl,bp,relation_alignment,contradiction_load); phase=t.after_phase; orch=t.after_orch; ids.append(t.transition_id); names.append(op); coord+=g.coordinate_dt
        if t.memory_residue_id: reductions+=1; residues.append(t.memory_residue_id)
    return ExecutionTrace(rh,ip,phase,io,orch,tuple(ids),tuple(names),coord,phase.phase_proper_time-start_tau,reductions,tuple(residues))
