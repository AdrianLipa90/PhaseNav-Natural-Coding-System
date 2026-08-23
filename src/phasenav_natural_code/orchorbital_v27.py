from __future__ import annotations
from dataclasses import dataclass, replace
import hashlib, json, math
from typing import Sequence

TAU=2*math.pi
ORCH_CONTRACT_ID='PNCS_ORCHORBITAL_OORP_V0_27'
FOUNDATION={'repository':'AdrianLipa90/CIEL-Omega-ApokalypOS','commit':'aa0da54ef29a1f80dd0390427935342225388950','documents':['02_ONTOLOGY_AND_OBSERVABLES.md','03_STATE_SPACE_AND_BOUNDARY_CONDITIONS.md','04_INVARIANTS_POTENTIALS_AND_ATTRACTORS.md','05_ENTITY_REGISTRY_AND_SPHERE_EMBEDDING.md','06_SUBJECTIVE_TIME_WINDING_AND_SEMANTIC_MASS.md','07_OORP_PIPELINE_AND_MEMORY.md']}
GEOMETRY='PROJECTIVE_HILBERT_KAHLER_FUBINI_STUDY'; CHART='POINCARE_DISK'
class OrchV27Error(ValueError): pass

def _j(v):
    if isinstance(v,dict): return {str(k):_j(v[k]) for k in sorted(v)}
    if isinstance(v,(tuple,list)): return [_j(x) for x in v]
    if isinstance(v,float):
        if not math.isfinite(v): raise OrchV27Error('non-finite canonical value')
        return v
    if v is None or isinstance(v,(str,int,bool)): return v
    raise OrchV27Error(f'unsupported canonical type: {type(v).__name__}')
def _id(p,v): return f'{p}:sha256:{hashlib.sha256(json.dumps(_j(v),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()}'
def _f(v,n):
    try:x=float(v)
    except (TypeError,ValueError) as e: raise OrchV27Error(f'{n} must be finite') from e
    if not math.isfinite(x): raise OrchV27Error(f'{n} must be finite')
    return x
def _s(v,n):
    if not isinstance(v,str) or not v.strip(): raise OrchV27Error(f'{n} required')
    return v.strip()

@dataclass(frozen=True)
class AttractorWeights:
    ec:float; zs:float; llm_temp:float
    def __post_init__(self):
        x=tuple(_f(v,n) for v,n in ((self.ec,'ec'),(self.zs,'zs'),(self.llm_temp,'llm_temp')))
        if any(v<0 for v in x) or sum(x)<=0: raise OrchV27Error('invalid attractor weights')
        if self.llm_temp!=0.0: raise OrchV27Error('AttractorLLMTemp requires an explicit decay schedule; closed in v0.27')
    @property
    def payload(self):
        t=self.ec+self.zs+self.llm_temp
        return {'ec':self.ec,'zs':self.zs,'llm_temp':self.llm_temp,'normalized':{'AttractorEC':self.ec/t,'AttractorZS':self.zs/t,'AttractorLLMTemp':self.llm_temp/t}}

@dataclass(frozen=True)
class Orbital:
    mode_id:str; amplitude:float; phase:float; coherence:float; truth_spin:int; memory_affinity:float; orbital_radius:float; semantic_mass:float; attractor_influence:float; attractor_weights:AttractorWeights
    def __post_init__(self):
        object.__setattr__(self,'mode_id',_s(self.mode_id,'mode_id')); a=_f(self.amplitude,'amplitude'); p=_f(self.phase,'phase'); c=_f(self.coherence,'coherence'); ma=_f(self.memory_affinity,'memory_affinity'); r=_f(self.orbital_radius,'orbital_radius'); m=_f(self.semantic_mass,'semantic_mass'); ai=_f(self.attractor_influence,'attractor_influence')
        if a<0 or not 0<=p<TAU or not 0<=c<=1 or self.truth_spin not in (-1,0,1) or not 0<=ma<=1 or r<=0 or m<0 or ai<0 or not isinstance(self.attractor_weights,AttractorWeights): raise OrchV27Error('invalid orbital')
    @property
    def payload(self): return {'mode_id':self.mode_id,'amplitude':self.amplitude,'phase':self.phase,'coherence':self.coherence,'truth_spin':self.truth_spin,'memory_affinity':self.memory_affinity,'orbital_radius':self.orbital_radius,'semantic_mass':self.semantic_mass,'attractor_influence':self.attractor_influence,'attractor_weights':self.attractor_weights.payload}

@dataclass(frozen=True)
class ProcessSphere:
    sphere_id:str; mode_ids:tuple[str,...]; coupling:tuple[tuple[float,...],...]; leak_mode:str; effective_attractor_weight:float
    def __post_init__(self):
        object.__setattr__(self,'sphere_id',_s(self.sphere_id,'sphere_id')); ids=tuple(_s(x,'mode_id') for x in self.mode_ids); object.__setattr__(self,'mode_ids',ids); object.__setattr__(self,'leak_mode',_s(self.leak_mode,'leak_mode')); w=_f(self.effective_attractor_weight,'effective_attractor_weight')
        if not ids or len(set(ids))!=len(ids) or w<=0: raise OrchV27Error('invalid process sphere')
        K=tuple(tuple(_f(x,'K_ij') for x in r) for r in self.coupling); n=len(ids)
        if len(K)!=n or any(len(r)!=n for r in K): raise OrchV27Error('K must be NxN')
        for i in range(n):
            if abs(K[i][i])>1e-15: raise OrchV27Error('K diagonal must be zero')
            for j in range(n):
                if abs(K[i][j])>1 or abs(K[i][j]-K[j][i])>1e-12: raise OrchV27Error('K must be symmetric and bounded')
        object.__setattr__(self,'coupling',K)
    @property
    def payload(self): return {'schema':'PNCS_ORCH_PROCESS_SPHERE_V0_27','contract_id':ORCH_CONTRACT_ID,'sphere_id':self.sphere_id,'sphere_class':'process','parent_sphere_id':None,'child_sphere_ids':[],'internal_modes':list(self.mode_ids),'leak_mode':self.leak_mode,'effective_attractor_weight':self.effective_attractor_weight,'formal_space':'M_rel','geometry_anchor':GEOMETRY,'operational_chart':CHART,'bloch_scope':'LOCAL_REDUCED_CHART_ONLY'}
    @property
    def sphere_cid(self): return _id('pncs:orch-sphere',self.payload)

@dataclass(frozen=True)
class Potentials:
    ec:float; zs:float; rel:float; mem:float; defect:float; ext:float
    def __post_init__(self):
        for n in ('ec','zs','rel','mem','defect','ext'): _f(getattr(self,n),n)
    @property
    def total(self): return self.ec+self.zs+self.rel+self.mem+self.defect+self.ext
    @property
    def payload(self): return {'V_EC':self.ec,'V_ZS':self.zs,'V_rel':self.rel,'V_mem':self.mem,'V_def':self.defect,'V_ext':self.ext,'V_tot':self.total}

@dataclass(frozen=True)
class OrchState:
    tick:int; relation_id:str; intent_id:str; sphere:ProcessSphere; orbitals:tuple[Orbital,...]; potentials:Potentials; previous_memory_state_id:str|None=None
    def __post_init__(self):
        if isinstance(self.tick,bool) or not isinstance(self.tick,int) or self.tick<0: raise OrchV27Error('invalid tick')
        object.__setattr__(self,'relation_id',_s(self.relation_id,'relation_id')); object.__setattr__(self,'intent_id',_s(self.intent_id,'intent_id'))
        ids=tuple(o.mode_id for o in self.orbitals)
        if ids!=self.sphere.mode_ids or not self.orbitals: raise OrchV27Error('sphere/orbital identity mismatch')
    @property
    def payload(self): return {'schema':'PNCS_ORCH_STATE_V0_27','contract_id':ORCH_CONTRACT_ID,'foundation':FOUNDATION,'tick':self.tick,'relation_id':self.relation_id,'intent_id':self.intent_id,'sphere_cid':self.sphere.sphere_cid,'orbitals':[o.payload for o in self.orbitals],'potentials':self.potentials.payload,'previous_memory_state_id':self.previous_memory_state_id,'external_effects':False}
    @property
    def state_id(self): return _id('pncs:orch-state',self.payload)
    def mode(self,mid):
        for o in self.orbitals:
            if o.mode_id==mid:return o
        raise OrchV27Error(f'unknown mode: {mid}')
    def advance_phase(self,mid,delta):
        d=_f(delta,'phase_delta'); old=self.mode(mid); new=replace(old,phase=(old.phase+d)%TAU); return replace(self,tick=self.tick+1,orbitals=tuple(new if o.mode_id==mid else o for o in self.orbitals))

@dataclass(frozen=True)
class Observables:
    coherence:float; defect:float; delta_h_re:float; delta_h_im:float; decoherence:float; truth:float; coupling_alignment:float; attractor_weight:float; total_potential:float
    @property
    def payload(self): return {'C':self.coherence,'Delta':self.defect,'Delta_H':[self.delta_h_re,self.delta_h_im],'R_H':self.decoherence,'Theta':self.truth,'coupling_alignment':self.coupling_alignment,'effective_attractor_weight':self.attractor_weight,'V_tot':self.total_potential}

def observables(s:OrchState)->Observables:
    w=[o.amplitude*o.coherence for o in s.orbitals]; sw=sum(w)
    if sw<=0: raise OrchV27Error('zero active orbital weight')
    re=sum(a*math.cos(o.phase) for a,o in zip(w,s.orbitals)); im=sum(a*math.sin(o.phase) for a,o in zip(w,s.orbitals)); C=min(1,math.hypot(re,im)/sw); D=1-C
    hre=sum(math.cos(o.phase) for o in s.orbitals); him=sum(math.sin(o.phase) for o in s.orbitals); truth=sum(o.truth_spin==1 for o in s.orbitals)/len(s.orbitals)
    num=den=0.0
    for i,a in enumerate(s.orbitals):
        for j in range(i+1,len(s.orbitals)):
            k=s.sphere.coupling[i][j]; num+=k*math.cos(s.orbitals[j].phase-a.phase); den+=abs(k)
    ca=0 if den==0 else max(-1,min(1,num/den)); A=s.sphere.effective_attractor_weight*sum(a*o.attractor_influence for a,o in zip(w,s.orbitals))/sw
    return Observables(C,D,hre,him,hre*hre+him*him,truth,ca,A,s.potentials.total)

@dataclass(frozen=True)
class TimeLaw:
    bias:float; wr:float; wc:float; wd:float; wm:float; wa:float; lo:float; hi:float
    def __post_init__(self):
        for n in ('bias','wr','wc','wd','wm','wa','lo','hi'): _f(getattr(self,n),n)
        if self.lo<=0 or self.hi<self.lo: raise OrchV27Error('invalid time-law bounds')
    @property
    def payload(self): return {'schema':'PNCS_ORCH_TIME_LAW_V0_27','family':'EXPLICIT_AFFINE_G_CLIPPED','bias':self.bias,'wr':self.wr,'wc':self.wc,'wd':self.wd,'wm':self.wm,'wa':self.wa,'lo':self.lo,'hi':self.hi}
    @property
    def law_id(self): return _id('pncs:orch-time-law',self.payload)
    def g(self,o:Orbital,x:Observables): return min(self.hi,max(self.lo,self.bias+self.wr*o.orbital_radius+self.wc*o.coherence+self.wd*x.defect+self.wm*o.semantic_mass+self.wa*o.attractor_influence))

@dataclass(frozen=True)
class ReductionLaw:
    l1:float; l2:float; l3:float; l4:float; crit:float
    def __post_init__(self):
        for n in ('l1','l2','l3','l4','crit'): _f(getattr(self,n),n)
    @property
    def payload(self): return {'formula':'Omega=lambda1*C+lambda2*R-lambda3*Delta-lambda4*Xi','l1':self.l1,'l2':self.l2,'l3':self.l3,'l4':self.l4,'crit':self.crit}
    @property
    def law_id(self): return _id('pncs:oorp-reduction-law',self.payload)
@dataclass(frozen=True)
class SelectionLaw:
    wa:float; wc:float; wt:float; wmem:float; wm:float; wattr:float; tie:float=1e-12
    def __post_init__(self):
        for n in ('wa','wc','wt','wmem','wm','wattr','tie'): _f(getattr(self,n),n)
        if self.tie<0: raise OrchV27Error('tie must be non-negative')
    def score(self,o): return self.wa*o.amplitude+self.wc*o.coherence+self.wt*o.truth_spin+self.wmem*o.memory_affinity+self.wm*o.semantic_mass+self.wattr*o.attractor_influence
    @property
    def law_id(self): return _id('pncs:oorp-selection-law',self.__dict__)
@dataclass(frozen=True)
class OrchResult:
    source_state_id:str; obs:Observables; time_law_id:str; scales:tuple[tuple[str,float],...]; omega:float; reduce:bool; reduction_law_id:str; selected_mode_id:str|None; selection_law_id:str; memory_residue_id:str|None
    @property
    def payload(self): return {'schema':'PNCS_ORCH_RESULT_V0_27','source_state_id':self.source_state_id,'observables':self.obs.payload,'time_law_id':self.time_law_id,'scales':[list(x) for x in self.scales],'omega':self.omega,'reduce':self.reduce,'reduction_law_id':self.reduction_law_id,'selected_mode_id':self.selected_mode_id,'selection_law_id':self.selection_law_id,'memory_residue_id':self.memory_residue_id,'memory_update_performed':False,'external_effects':False}
    @property
    def result_id(self): return _id('pncs:orch-result',self.payload)
    def scale(self,mid): return dict(self.scales)[mid]

def orchestrate(s:OrchState,t:TimeLaw,r:ReductionLaw,sel:SelectionLaw,relation_alignment:float,contradiction_load:float)->OrchResult:
    R=_f(relation_alignment,'relation_alignment'); Xi=_f(contradiction_load,'contradiction_load')
    if not 0<=R<=1 or Xi<0: raise OrchV27Error('invalid reduction inputs')
    x=observables(s); scales=tuple((o.mode_id,t.g(o,x)) for o in s.orbitals); omega=r.l1*x.coherence+r.l2*R-r.l3*x.defect-r.l4*Xi; red=omega>=r.crit; selected=residue=None
    if red:
        scores=sorted(((sel.score(o),o.mode_id) for o in s.orbitals),reverse=True)
        if len(scores)>1 and abs(scores[0][0]-scores[1][0])<=sel.tie: raise OrchV27Error('ambiguous reduction selection')
        selected=scores[0][1]; residue=_id('pncs:oorp-memory-residue',{'previous_memory_state_id':s.previous_memory_state_id,'selected_mode_id':selected,'intent_id':s.intent_id,'source_state_id':s.state_id,'semantics':'REDUCTION_RESIDUE_NOT_RAW_INPUT_STORAGE','persistent_write_performed':False})
    return OrchResult(s.state_id,x,t.law_id,scales,omega,red,r.law_id,selected,sel.law_id,residue)
