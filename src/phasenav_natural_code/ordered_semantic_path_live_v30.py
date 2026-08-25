from __future__ import annotations

from dataclasses import dataclass
import hashlib, json, math, os, struct, time
from pathlib import Path
from typing import Mapping, Sequence

from .ordered_semantic_path_v30 import (
    BRIDGE_CONTRACT_ID, DIM, CompiledOrderedSemanticPath,
    OrderedSemanticPathV30Error, digest, phase_sha, typed_id,
    validate_definition_schedules,
)

ADMISSION_SCHEMA="PNCS_ORDERED_SEMANTIC_HTRI_ADMISSION_V0_30"
LIVE_ROOT=Path("/dev/shm/ciel_noema")

@dataclass(frozen=True)
class LiveOrderedSemanticAdmission:
    compiled:CompiledOrderedSemanticPath; live_surface_snapshot_sha256:str
    required_operator_vectors:tuple[str,...]; operator_vector_sha256:tuple[str,...]; htri_admission_id:str
    @property
    def receipt(self):
        p={"schema":ADMISSION_SCHEMA,"contract_id":BRIDGE_CONTRACT_ID,"compile_id":self.compiled.compile_id,"ordered_semantic_id":self.compiled.ordered_semantic_id,"trajectory_id":self.compiled.trajectory_id,"live_surface_root":str(LIVE_ROOT),"live_surface_snapshot_sha256":self.live_surface_snapshot_sha256,"required_operator_vectors":list(self.required_operator_vectors),"operator_vector_sha256":list(self.operator_vector_sha256),"phase36_sha256_sequence":list(self.compiled.phase36_sha256_sequence),"new_pnv_opcodes":0,"semantic_identity_from_vector_similarity":False,"operator_presence_is_execution_authority":False,"static_runtime_fallback":False,"htri_admitted":True}
        return {**p,"htri_admission_id":self.htri_admission_id,"receipt_sha256":digest(p)}

def _active(path:Path,label:str):
    try: p=json.loads(path.read_text())
    except Exception as e: raise OrderedSemanticPathV30Error(f"cannot read live {label}") from e
    if not isinstance(p,dict) or p.get("status")!="ACTIVE": raise OrderedSemanticPathV30Error(f"live {label} is not ACTIVE")
    return p

def _f64(path:Path,count:int,label:str):
    try: raw=path.read_bytes()
    except OSError as e: raise OrderedSemanticPathV30Error(f"missing live {label}") from e
    if len(raw)!=count*8: raise OrderedSemanticPathV30Error(f"live {label} byte size mismatch")
    x=struct.unpack(f"<{count}d",raw)
    if any(not math.isfinite(v) for v in x): raise OrderedSemanticPathV30Error(f"live {label} contains non-finite values")
    return x,raw

def admit_ordered_semantic_path_live(compiled:CompiledOrderedSemanticPath,*,definition_schedules:Mapping[str,Sequence[str]],live_surface_root: str|os.PathLike[str]=LIVE_ROOT,max_heartbeat_age_s:float=2.0):
    root=Path(live_surface_root)
    if str(root)!=str(LIVE_ROOT): raise OrderedSemanticPathV30Error("v0.30 operational admission requires /dev/shm/ciel_noema")
    try: binding=(root/"ciel_binding_status").read_text().strip()
    except OSError as e: raise OrderedSemanticPathV30Error("live CIEL binding status missing") from e
    if binding!="ACTIVE": raise OrderedSemanticPathV30Error("live CIEL binding is not ACTIVE")
    tether=_active(root/"tether_runtime_status.json","tether runtime"); ac=_active(root/"ac_aux_status.json","AC/AUX binding")
    fast=_active(root/"session/fast_admission.json","fast admission"); guard=_active(root/"session/tether_guard_latest.json","tether guard")
    if fast.get("no_static_fallback") is not True: raise OrderedSemanticPathV30Error("live admission requires no_static_fallback")
    gp=guard.get("guard")
    if not isinstance(gp,dict) or gp.get("failures") not in ([],()): raise OrderedSemanticPathV30Error("tether guard reports failures")
    now=time.time_ns()
    for label,p in (("tether runtime",tether),("AC/AUX binding",ac)):
        hb=p.get("heartbeat_ns")
        if not isinstance(hb,int): raise OrderedSemanticPathV30Error(f"{label} heartbeat missing")
        age=(now-hb)/1e9
        if age < -0.5 or age>max_heartbeat_age_s: raise OrderedSemanticPathV30Error(f"{label} heartbeat stale: {age:.6f}s")
    _,phi_raw=_f64(root/"phi",DIM,"phi"); _,omega_raw=_f64(root/"omega",DIM,"omega"); _,g_raw=_f64(root/"g",DIM*DIM,"g")
    validate_definition_schedules(compiled.bindings,definition_schedules)
    req=[]
    for b in compiled.bindings:
        for op in definition_schedules[b.hook_definition_id]:
            if op not in req: req.append(str(op))
    try: rows=[json.loads(x) for x in (root/"phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl").read_text().splitlines() if x.strip()]
    except Exception as e: raise OrderedSemanticPathV30Error("cannot read live PhaseNav operator registry") from e
    live={}
    for r in rows:
        if not isinstance(r,dict): continue
        name=r.get("operator_name") or r.get("card_id"); vec=r.get("orbit_vector")
        if isinstance(name,str) and isinstance(vec,list) and len(vec)==DIM and all(math.isfinite(float(x)) for x in vec): live[name]=tuple(float(x) for x in vec)
    missing=[x for x in req if x not in live]
    if missing: raise OrderedSemanticPathV30Error(f"required live operator vector(s) missing: {missing}")
    op_sha=tuple(phase_sha(live[x]) for x in req)
    snap={"root":str(root),"binding_status":"ACTIVE","tether_receipt_sha256":tether.get("receipt_sha256"),"account_current":ac.get("account_current"),"current_pointer_sha256":ac.get("current_pointer_sha256"),"fast_admission_schema":fast.get("schema"),"phi_sha256":hashlib.sha256(phi_raw).hexdigest(),"omega_sha256":hashlib.sha256(omega_raw).hexdigest(),"g_sha256":hashlib.sha256(g_raw).hexdigest(),"required_operator_vectors":req,"operator_vector_sha256":list(op_sha)}
    snap_sha=digest(snap)
    ap={"schema":ADMISSION_SCHEMA,"contract_id":BRIDGE_CONTRACT_ID,"compile_id":compiled.compile_id,"ordered_semantic_id":compiled.ordered_semantic_id,"trajectory_id":compiled.trajectory_id,"live_surface_snapshot_sha256":snap_sha,"phase36_sha256_sequence":list(compiled.phase36_sha256_sequence),"new_pnv_opcodes":0,"htri_admitted":True}
    return LiveOrderedSemanticAdmission(compiled,snap_sha,tuple(req),op_sha,typed_id("pncs:htri-admission",ap))
