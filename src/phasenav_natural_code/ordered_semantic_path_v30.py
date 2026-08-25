from __future__ import annotations

from dataclasses import dataclass
import hashlib, json, math, re
from typing import Mapping, Sequence

DIM=36; TAU=2.0*math.pi
BRIDGE_CONTRACT_ID="PNCS_ORDERED_SEMANTIC_PATH_BRIDGE_V0_30"
SEMANTIC_SCHEMA="PNCS_ORDERED_SEMANTIC_CONTENT_V0_30"
TRANSITION_SCHEMA="PNCS_ORDERED_T36_TRANSITION_WITNESS_V0_30"
TRAJECTORY_SCHEMA="PNCS_ORDERED_T36_TRAJECTORY_V0_30"
COMPILE_RECEIPT_SCHEMA="PNCS_ORDERED_SEMANTIC_PATH_COMPILE_RECEIPT_V0_30"
ADMITTED_V20_OPERATORS=frozenset({"IDENTITY","DIFFERENCE","CONDITION","NEGATION","COMPOSITION","ORDER","TRANSFORM"})
REQUIRED_NATIVE_GEOMETRY_OPERATORS=frozenset({"pnv.torus.normalize","pnv.torus.delta","pnv.torus.geodesic","pnv.path.length_l2","pnv.orbit.arc_sample","pnv.path.compose"})
CONTENT_RE=re.compile(r"^pncs:(?:def|class|file|cluster|subsystem|daemon|low-orchestrator|high-orchestrator|system):sha256:[0-9a-f]{64}$")
DEF_RE=re.compile(r"^pncs:def:sha256:[0-9a-f]{64}$"); HEX_RE=re.compile(r"^[0-9a-f]{64}$")
ROLE_RE=re.compile(r"^[A-Z][A-Z0-9_.:-]{0,95}$"); ANCHOR_RE=re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,95}$")

class OrderedSemanticPathV30Error(ValueError): pass

def _canon(v):
    if isinstance(v,tuple): return [_canon(x) for x in v]
    if isinstance(v,list): return [_canon(x) for x in v]
    if isinstance(v,dict): return {str(k):_canon(v[k]) for k in sorted(v)}
    if isinstance(v,float) and not math.isfinite(v): raise OrderedSemanticPathV30Error("non-finite canonical float")
    if v is None or isinstance(v,(str,int,float,bool)): return v
    raise OrderedSemanticPathV30Error(f"unsupported canonical type: {type(v).__name__}")

def compact(v): return json.dumps(_canon(v),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
def digest(v): return hashlib.sha256(compact(v).encode()).hexdigest()
def typed_id(prefix,payload): return f"{prefix}:sha256:{digest(payload)}"
def phase_sha(v): return hashlib.sha256(json.dumps(list(v),separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def turn_delta(a,b): return ((b-a+0.5)%1.0)-0.5

def phase36(v):
    x=tuple(float(a) for a in v)
    if len(x)!=DIM or any((not math.isfinite(a) or a<0 or a>=TAU) for a in x):
        raise OrderedSemanticPathV30Error("phase36 must contain 36 finite angles in [0,2π)")
    return x

def require_hex(v,name):
    if not isinstance(v,str) or not HEX_RE.fullmatch(v): raise OrderedSemanticPathV30Error(f"{name} must be lowercase SHA-256")
    return v

@dataclass(frozen=True)
class SemanticAnchorBinding:
    role_id:str; semantic_content_id:str; hook_definition_id:str; anchor_id:str
    source_digest_sha256:str; source_locator:str; epistemic_operator:str="CHYBA"; canon_allowed:bool=False
    def __post_init__(self):
        if not ROLE_RE.fullmatch(self.role_id): raise OrderedSemanticPathV30Error("invalid role_id")
        if not CONTENT_RE.fullmatch(self.semantic_content_id): raise OrderedSemanticPathV30Error("semantic_content_id must be typed PNCS content")
        if not DEF_RE.fullmatch(self.hook_definition_id): raise OrderedSemanticPathV30Error("hook_definition_id must be PNCS Definition CID")
        if not ANCHOR_RE.fullmatch(self.anchor_id): raise OrderedSemanticPathV30Error("invalid anchor_id")
        require_hex(self.source_digest_sha256,"source_digest_sha256")
        if not self.source_locator.strip(): raise OrderedSemanticPathV30Error("source_locator required")
        if self.epistemic_operator!="CHYBA" or self.canon_allowed: raise OrderedSemanticPathV30Error("v0.30 evidence binding invariant violated")
    @property
    def binding_payload(self):
        return {"schema":"PNCS_SEMANTIC_ANCHOR_BINDING_V0_30","semantic_content_id":self.semantic_content_id,"hook_definition_id":self.hook_definition_id,"anchor_id":self.anchor_id,"source_digest_sha256":self.source_digest_sha256,"source_locator":self.source_locator,"epistemic_operator":self.epistemic_operator,"canon_allowed":self.canon_allowed}
    @property
    def binding_id(self): return typed_id("pncs:semantic-anchor",self.binding_payload)

@dataclass(frozen=True)
class Segment:
    path_id:str; source:str; target:str; tangent:tuple[float,...]; tangent_sha256:str; length:float

@dataclass(frozen=True)
class TransitionWitness:
    index:int; source_binding_id:str; target_binding_id:str; source_content_id:str; target_content_id:str
    source_hook_definition_id:str; target_hook_definition_id:str; source_anchor:str; target_anchor:str
    segment_ids:tuple[str,...]; segment_tangent_sha256:tuple[str,...]; length_turns_l2:float
    source_phase36_sha256:str; midpoint_phase36_sha256:str; target_phase36_sha256:str
    @property
    def payload(self):
        return {"schema":TRANSITION_SCHEMA,"index":self.index,"source_binding_id":self.source_binding_id,"target_binding_id":self.target_binding_id,"source_content_id":self.source_content_id,"target_content_id":self.target_content_id,"source_hook_definition_id":self.source_hook_definition_id,"target_hook_definition_id":self.target_hook_definition_id,"source_anchor":self.source_anchor,"target_anchor":self.target_anchor,"segment_ids":list(self.segment_ids),"segment_tangent_sha256":list(self.segment_tangent_sha256),"length_turns_l2":self.length_turns_l2,"source_phase36_sha256":self.source_phase36_sha256,"midpoint_phase36_sha256":self.midpoint_phase36_sha256,"target_phase36_sha256":self.target_phase36_sha256}
    @property
    def witness_id(self): return typed_id("pncs:t36-transition",self.payload)

@dataclass(frozen=True)
class CompiledOrderedSemanticPath:
    ordered_semantic_id:str; trajectory_id:str; bindings:tuple[SemanticAnchorBinding,...]; transitions:tuple[TransitionWitness,...]
    phase36_sequence:tuple[tuple[float,...],...]; phase36_sha256_sequence:tuple[str,...]; hook_schedule_sha256:tuple[str,...]; compile_id:str
    @property
    def receipt(self):
        p={"schema":COMPILE_RECEIPT_SCHEMA,"contract_id":BRIDGE_CONTRACT_ID,"ordered_semantic_id":self.ordered_semantic_id,"trajectory_id":self.trajectory_id,"binding_ids":[x.binding_id for x in self.bindings],"transition_witness_ids":[x.witness_id for x in self.transitions],"phase36_sha256_sequence":list(self.phase36_sha256_sequence),"hook_schedule_sha256":list(self.hook_schedule_sha256),"new_pnv_opcodes":0,"semantic_identity_from_vector_similarity":False,"operator_presence_is_execution_authority":False,"static_runtime_fallback":False,"live_admission_required":True,"htri_admitted":False}
        return {**p,"compile_id":self.compile_id,"receipt_sha256":digest(p)}

class NativeGeometryV2:
    def __init__(self,payload:Mapping[str,object]):
        if payload.get("schema")!="PNV_NATIVE_FUNCTION_DB_V2" or payload.get("dimension")!=DIM: raise OrderedSemanticPathV30Error("PNV Native Function DB V2 / 36D required")
        c=payload.get("canonical")
        if not isinstance(c,Mapping) or c.get("dimension")!=DIM: raise OrderedSemanticPathV30Error("canonical 36D section required")
        opids={str(x.get("id")) for x in c.get("operators",[]) if isinstance(x,Mapping)}
        missing=sorted(REQUIRED_NATIVE_GEOMETRY_OPERATORS-opids)
        if missing: raise OrderedSemanticPathV30Error(f"missing native geometry operators: {missing}")
        self.vectors={}; self.vector_sha={}
        for name,row in c.get("vectors",{}).items():
            v=phase36(row.get("phase36",())); h=require_hex(str(row.get("sha256","")),f"vector {name} sha")
            if phase_sha(v)!=h: raise OrderedSemanticPathV30Error(f"canonical vector digest mismatch: {name}")
            self.vectors[str(name)]=v; self.vector_sha[str(name)]=h
        self.paths={}; self.outgoing={}
        for row in c.get("paths",[]):
            pid=str(row.get("path_id","")); a=str(row.get("from","")); b=str(row.get("to",""))
            if a not in self.vectors or b not in self.vectors: raise OrderedSemanticPathV30Error(f"path endpoint missing: {pid}")
            t=tuple(float(x) for x in row.get("tangent36_turns",()))
            if len(t)!=DIM or any(not math.isfinite(x) for x in t): raise OrderedSemanticPathV30Error(f"bad tangent: {pid}")
            th=require_hex(str(row.get("tangent36_sha256","")),f"path {pid} tangent sha")
            if hashlib.sha256(json.dumps(list(t),separators=(",",":")).encode()).hexdigest()!=th: raise OrderedSemanticPathV30Error(f"path tangent digest mismatch: {pid}")
            qa=[x/TAU for x in self.vectors[a]]; qb=[x/TAU for x in self.vectors[b]]; expected=tuple(turn_delta(x,y) for x,y in zip(qa,qb))
            if max(abs(x-y) for x,y in zip(t,expected))>1e-12: raise OrderedSemanticPathV30Error(f"path tangent mismatch: {pid}")
            length=float(row.get("length_turns_l2")); calc=math.sqrt(sum(x*x for x in t))
            if not math.isfinite(length) or abs(length-calc)>1e-12: raise OrderedSemanticPathV30Error(f"path length mismatch: {pid}")
            self.paths[pid]=Segment(pid,a,b,t,th,length); self.outgoing.setdefault(a,[]).append(pid)
        self.payload_sha256=digest(payload)
    def phase(self,a):
        if a not in self.vectors: raise OrderedSemanticPathV30Error(f"unknown canonical anchor: {a}")
        return self.vectors[a]
    def segments(self,a,b):
        self.phase(a); self.phase(b)
        if a==b: return ()
        cur=a; seen={a}; out=[]
        for _ in range(len(self.paths)+1):
            ids=sorted(self.outgoing.get(cur,()))
            if len(ids)!=1: raise OrderedSemanticPathV30Error(f"path is not uniquely composable from {cur}: {ids}")
            s=self.paths[ids[0]]; out.append(s); cur=s.target
            if cur==b: return tuple(out)
            if cur in seen: break
            seen.add(cur)
        raise OrderedSemanticPathV30Error(f"no directed composition from {a} to {b}")
    def arc_sample(self,segs,f):
        total=sum(s.length for s in segs); target=f*total; walked=0.0
        if not segs: raise OrderedSemanticPathV30Error("arc_sample requires segments")
        for i,s in enumerate(segs):
            end=walked+s.length
            if target<=end or i==len(segs)-1:
                u=0.0 if s.length==0 else max(0.0,min(1.0,(target-walked)/s.length))
                qa=[x/TAU for x in self.vectors[s.source]]; qb=[x/TAU for x in self.vectors[s.target]]
                return tuple(((x+u*turn_delta(x,y))%1.0)*TAU for x,y in zip(qa,qb))
            walked=end
        raise OrderedSemanticPathV30Error("arc_sample failed")
    def transition(self,i,a:SemanticAnchorBinding,b:SemanticAnchorBinding):
        segs=self.segments(a.anchor_id,b.anchor_id); mid=self.phase(a.anchor_id) if not segs else self.arc_sample(segs,0.5)
        return TransitionWitness(i,a.binding_id,b.binding_id,a.semantic_content_id,b.semantic_content_id,a.hook_definition_id,b.hook_definition_id,a.anchor_id,b.anchor_id,tuple(s.path_id for s in segs),tuple(s.tangent_sha256 for s in segs),sum(s.length for s in segs),self.vector_sha[a.anchor_id],phase_sha(mid),self.vector_sha[b.anchor_id])

def validate_definition_schedules(bindings,definition_schedules):
    out=[]
    for b in bindings:
        if b.hook_definition_id not in definition_schedules: raise OrderedSemanticPathV30Error(f"registered hook Definition schedule missing: {b.hook_definition_id}")
        s=tuple(str(x) for x in definition_schedules[b.hook_definition_id])
        if not s: raise OrderedSemanticPathV30Error("hook Definition schedule cannot be empty")
        bad=[x for x in s if x not in ADMITTED_V20_OPERATORS]
        if bad: raise OrderedSemanticPathV30Error(f"hook Definition contains operator without admitted v0.20 execution semantics: {bad}")
        out.append(digest({"definition_id":b.hook_definition_id,"leaf_path":list(s)}))
    return tuple(out)

def compile_ordered_semantic_path(bindings:Sequence[SemanticAnchorBinding],*,native_db_v2:Mapping[str,object],definition_schedules:Mapping[str,Sequence[str]]):
    b=tuple(bindings)
    if len(b)<2 or not all(isinstance(x,SemanticAnchorBinding) for x in b): raise OrderedSemanticPathV30Error("at least two SemanticAnchorBinding items required")
    sp={"schema":SEMANTIC_SCHEMA,"ordered_items":[{"semantic_content_id":x.semantic_content_id,"hook_definition_id":x.hook_definition_id} for x in b]}
    sid=typed_id("pncs:ordered-semantic",sp); sched=validate_definition_schedules(b,definition_schedules); g=NativeGeometryV2(native_db_v2)
    for x in b: g.phase(x.anchor_id)
    transitions=tuple(g.transition(i,b[i],b[i+1]) for i in range(len(b)-1)); phases=tuple(g.phase(x.anchor_id) for x in b); shas=tuple(g.vector_sha[x.anchor_id] for x in b)
    tp={"schema":TRAJECTORY_SCHEMA,"ordered_semantic_id":sid,"native_db_sha256":g.payload_sha256,"binding_ids":[x.binding_id for x in b],"transition_witness_ids":[x.witness_id for x in transitions],"phase36_sha256_sequence":list(shas),"hook_schedule_sha256":list(sched),"path_composition_operator":"pnv.path.compose","arc_sampler_operator":"pnv.orbit.arc_sample","new_pnv_opcodes":0}
    tid=typed_id("pncs:trajectory36",tp); cp={"schema":COMPILE_RECEIPT_SCHEMA,"contract_id":BRIDGE_CONTRACT_ID,"ordered_semantic_id":sid,"trajectory_id":tid,"binding_ids":[x.binding_id for x in b],"transition_witness_ids":[x.witness_id for x in transitions],"phase36_sha256_sequence":list(shas),"hook_schedule_sha256":list(sched),"new_pnv_opcodes":0,"live_admission_required":True,"htri_admitted":False}
    return CompiledOrderedSemanticPath(sid,tid,b,transitions,phases,shas,sched,typed_id("pncs:semantic-path-compile",cp))
