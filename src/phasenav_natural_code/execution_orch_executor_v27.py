from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import os
import struct
from pathlib import Path
from typing import Mapping

try:
    from .hydro_time_v27 import DEFAULT_SURFACE_ROOT, HydrodynamicPhaseGate, PhaseFlowState36, _compact_json, _sha256_bytes, _sha256_json
    from .hydro_schedule_v27 import load_live_operator_vectors
    from .orch_hydro_v27 import OrchHydroControlProfile, OrchHydroOccurrence, run_orchestrated_occurrence
    from .execution_orch_authority_v27 import (
        COUPLED_EXECUTION_CONTRACT_ID, COUPLED_RECEIPT_SCHEMA, EXECUTABLE_INTERNAL_OPERATORS,
        CoupledExecutionV27Error, ProgramAuthority, ResidentCoupledAuthority,
        _finite, _route, _normalize_values, expected_leaf_path,
    )
    from .execution_orch_state_v27 import SigmaState, SemanticExecutionStep, CoupledExecutionSession
except ImportError:  # isolated harness compatibility
    from hydro_time_v27 import DEFAULT_SURFACE_ROOT, HydrodynamicPhaseGate, PhaseFlowState36, _compact_json, _sha256_bytes, _sha256_json  # type: ignore
    from hydro_schedule_v27 import load_live_operator_vectors  # type: ignore
    from orch_hydro_v27 import OrchHydroControlProfile, OrchHydroOccurrence, run_orchestrated_occurrence  # type: ignore
    from execution_orch_authority_v27 import (  # type: ignore
        COUPLED_EXECUTION_CONTRACT_ID, COUPLED_RECEIPT_SCHEMA, EXECUTABLE_INTERNAL_OPERATORS,
        CoupledExecutionV27Error, ProgramAuthority, ResidentCoupledAuthority,
        _finite, _route, _normalize_values, expected_leaf_path,
    )
    from execution_orch_state_v27 import SigmaState, SemanticExecutionStep, CoupledExecutionSession  # type: ignore

class _CoupledExecutor:
    def __init__(
        self,
        authority: ProgramAuthority,
        operators: Mapping[str,tuple[float,...]],
        live_phi_sha256: str,
        phase_state: PhaseFlowState36,
        profile: OrchHydroControlProfile,
        gate_policy: Mapping[str,object],
        session_id: str,
    ):
        self.authority=authority
        self.operators=operators
        self.live_phi_sha256=live_phi_sha256
        self.phase_state=phase_state
        self.profile=profile
        self.gate_policy=gate_policy
        self.session_id=session_id
        self.steps:list[SemanticExecutionStep]=[]
        self.occurrences:list[OrchHydroOccurrence]=[]

    def _gate(self, operator_id: str):
        gate=self.gate_policy.get(operator_id)
        if gate is None:
            gate=self.gate_policy.get("*")
        if not isinstance(gate,HydrodynamicPhaseGate):
            raise CoupledExecutionV27Error(f"no HydrodynamicPhaseGate for {operator_id}")
        return gate

    def _transition(self,state:SigmaState,operator_id:str,*,bindings:Mapping[str,object],**changes:object)->SigmaState:
        if operator_id not in EXECUTABLE_INTERNAL_OPERATORS:
            raise CoupledExecutionV27Error("operator not executable")
        vec=self.operators.get(operator_id)
        if vec is None:
            raise CoupledExecutionV27Error(f"live operator missing: {operator_id}")
        vector_sha=hashlib.sha256(struct.pack("<36d",*vec)).hexdigest()
        before=state.state_id
        allowed={"accumulator","truth_stack","selected_route","control_location"}
        if set(changes)-allowed:
            raise CoupledExecutionV27Error("unsupported Sigma mutation")
        after=replace(state,step_index=state.step_index+1,last_operator=operator_id,**changes)
        semantic_step=SemanticExecutionStep(after.step_index,operator_id,vector_sha,before,after.state_id,dict(bindings))
        occurrence=run_orchestrated_occurrence(
            self.phase_state,self._gate(operator_id),vec,
            occurrence_step_index=after.step_index,
            operator_id=operator_id,
            operator_vector_sha256=vector_sha,
            before_sigma_id=before,
            after_sigma_id=after.state_id,
            tick_start=sum(len(x.inner_step_ids) for x in self.occurrences),
            program_content_id=self.authority.content_id,
            semantic_mass=self.authority.semantic_mass,
            profile=self.profile,
            identity_input_id=self.session_id,
        )
        self.phase_state=occurrence.final_phase_state
        self.steps.append(semantic_step)
        self.occurrences.append(occurrence)
        return after

    def _eval(self,node:tuple[object,...],state:SigmaState)->SigmaState:
        kind=node[0]; values=dict(state.input_values)
        if kind=="comparison":
            subject=str(node[1]); comparator=str(node[2]); threshold=_finite(node[3],"threshold")
            if subject not in values:
                raise CoupledExecutionV27Error(f"missing runtime value for {subject}")
            value=values[subject]; delta=value-threshold
            state=self._transition(state,"DIFFERENCE",accumulator=delta,bindings={"subject":subject,"value":value,"threshold":threshold})
            if comparator=="lt": truth=delta<0
            elif comparator=="gt": truth=delta>0
            elif comparator=="eq": truth=delta==0
            else: raise CoupledExecutionV27Error("unsupported comparator")
            return self._transition(state,"CONDITION",truth_stack=state.truth_stack+(truth,),bindings={"comparator":comparator,"difference":delta,"truth":truth})
        if kind=="not":
            state=self._eval(node[1],state)
            if not state.truth_stack:
                raise CoupledExecutionV27Error("NEGATION requires truth value")
            truth=not state.truth_stack[-1]
            return self._transition(state,"NEGATION",truth_stack=state.truth_stack[:-1]+(truth,),bindings={"truth":truth})
        if kind in {"and","or"}:
            children=node[1:]
            state=self._eval(children[0],state)
            for child in children[1:]:
                state=self._eval(child,state)
                if len(state.truth_stack)<2:
                    raise CoupledExecutionV27Error("COMPOSITION requires two values")
                left,right=state.truth_stack[-2],state.truth_stack[-1]
                truth=(left and right) if kind=="and" else (left or right)
                state=self._transition(state,"COMPOSITION",truth_stack=state.truth_stack[:-2]+(truth,),bindings={"mode":"all" if kind=="and" else "any","left":left,"right":right,"truth":truth})
            return state
        raise CoupledExecutionV27Error("unsupported predicate node")

    def run(self,initial:SigmaState,admitted_target:str)->tuple[SigmaState,str]:
        graph=self.authority.canonical_graph
        if expected_leaf_path(graph)!=self.authority.leaf_path:
            raise CoupledExecutionV27Error("authority leaf path mismatch")
        predicate=graph[1]; true_target=_route(graph[2],"true_target"); false_target=None if graph[3] is None else _route(graph[3],"false_target")
        state=self._eval(predicate,initial)
        if len(state.truth_stack)!=1:
            raise CoupledExecutionV27Error("predicate did not reduce to one truth")
        raw_truth=state.truth_stack[-1]; truth_state="TRUE" if raw_truth else "FALSE"
        expected_target=true_target if raw_truth else false_target
        if expected_target is None:
            raise CoupledExecutionV27Error("no target")
        admitted=_route(admitted_target,"admitted_target")
        if admitted!=expected_target:
            raise CoupledExecutionV27Error("admission/graph mismatch")
        if not raw_truth and false_target is not None:
            state=self._transition(state,"NEGATION",truth_stack=state.truth_stack[:-1]+(True,),bindings={"branch":"FALSE","source_truth":False,"admission_truth":True})
        state=self._transition(state,"ORDER",selected_route=expected_target,bindings={"branch":truth_state,"target":expected_target})
        state=self._transition(state,"TRANSFORM",control_location=expected_target,bindings={"domain":"control_location","target":expected_target})
        state=self._transition(state,"COMPOSITION",bindings={"mode":"branch_close","target":expected_target})
        return state,truth_state


@dataclass(frozen=True)
class CoupledExecutionResult:
    target: str
    branch_truth_state: str
    final_sigma_state: SigmaState
    final_phase_state: PhaseFlowState36
    receipt: Mapping[str,object]
    receipt_path: str


def _atomic_write(path:Path,raw:bytes)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with tmp.open("wb") as fh:
        fh.write(raw); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp,path)


def execute_orchorbital_coupled(
    authority: ProgramAuthority,
    values: Mapping[str,object],
    admitted_target: str,
    profile: OrchHydroControlProfile,
    gate_policy: Mapping[str,object],
    *,
    resident_authority: ResidentCoupledAuthority | None = None,
    require_resident_authority: bool = True,
    surface_root: Path|str=DEFAULT_SURFACE_ROOT,
    control_location: str="pncs.entry",
    persist: bool=True,
)->CoupledExecutionResult:
    root=Path(surface_root)
    if root!=DEFAULT_SURFACE_ROOT:
        raise CoupledExecutionV27Error("coupled operational runtime is fixed to /dev/shm/ciel_noema")
    if (root/"ciel_binding_status").read_text("utf-8").strip()!="ACTIVE":
        raise CoupledExecutionV27Error("live NOEMA binding is not ACTIVE")
    if resident_authority is None:
        if require_resident_authority:
            raise CoupledExecutionV27Error("active resident v0.25 authority required")
        resident_authority_id="UNBOUND_TEST_ONLY"
    else:
        if not isinstance(resident_authority,ResidentCoupledAuthority):
            raise CoupledExecutionV27Error("ResidentCoupledAuthority required")
        if resident_authority.program_authority.authority_id!=authority.authority_id:
            raise CoupledExecutionV27Error("resident/program authority mismatch")
        resident_authority.validate_active_pointer(root)
        resident_authority_id=resident_authority.authority_id
    phi_raw=(root/"phi").read_bytes()
    if len(phi_raw)!=36*8:
        raise CoupledExecutionV27Error("live phi must contain 36 doubles")
    theta=struct.unpack("<36d",phi_raw)
    phase_state=PhaseFlowState36(theta)
    operators,registry_sha=load_live_operator_vectors(root)
    normalized=_normalize_values(values)
    session=CoupledExecutionSession(
        authority.authority_id,resident_authority_id,authority.content_id,_sha256_bytes(phi_raw),registry_sha,
        normalized,_route(admitted_target,"admitted_target"),profile.profile_id
    )
    initial=SigmaState(
        authority.content_id,authority.realization_id,authority.mass_binding_id,
        authority.phase36_sha256,authority.semantic_mass,_sha256_bytes(phi_raw),
        normalized,control_location,
    )
    executor=_CoupledExecutor(authority,operators,_sha256_bytes(phi_raw),phase_state,profile,gate_policy,session.session_id)
    final,truth=executor.run(initial,admitted_target)
    target=final.control_location
    semantic_projection={
        "program":authority.provenance_payload,
        "canonical_graph_sha256":authority.canonical_graph_sha256,
        "canonical_leaf_path":list(authority.leaf_path),
        "input_values":[[k,v] for k,v in normalized],
        "admission":{"branch_truth_state":truth,"admitted_target":target,"epistemic_operator":None},
        "initial_sigma_id":initial.state_id,
        "final_sigma_id":final.state_id,
        "steps":[x.payload for x in executor.steps],
        "result":{"kind":"INTERNAL_TRANSFORM","control_location":target},
        "external_effects":False,
        "semantic_mass_is_authorization":False,
        "free_form_nl_execution":False,
        "deterministic_fields_only":True,
    }
    payload={
        "schema":COUPLED_RECEIPT_SCHEMA,
        "execution_contract_id":COUPLED_EXECUTION_CONTRACT_ID,
        "source_v20_authority_receipt_sha256":authority.source_v20_receipt_sha256,
        "program_authority_id":authority.authority_id,
        "resident_authority_id":resident_authority_id,
        "resident_dispatch_id":None if resident_authority is None else resident_authority.dispatch_id,
        "resident_handle_id":None if resident_authority is None else resident_authority.handle_id,
        "runtime_generation_id":None if resident_authority is None else resident_authority.generation_id,
        "resident_program_id":None if resident_authority is None else resident_authority.resident_program_id,
        "v22_result_id":None if resident_authority is None else resident_authority.result_id,
        "v22_lineage_id":None if resident_authority is None else resident_authority.lineage_id,
        "session_id":session.session_id,
        "profile_id":profile.profile_id,
        "live_surface":{"root":str(root),"phi_sha256":_sha256_bytes(phi_raw),"operator_registry_sha256":registry_sha},
        "semantic_projection":semantic_projection,
        "semantic_projection_sha256":_sha256_json(semantic_projection),
        "orch_occurrences":[x.payload for x in executor.occurrences],
        "orch_occurrence_ids":[x.occurrence_id for x in executor.occurrences],
        "final_phase_state_id":executor.phase_state.state_id,
        "phase_proper_time_advanced":executor.phase_state.phase_proper_time-phase_state.phase_proper_time,
        "stable_memory_update_count":sum(int(x.memory_residue is not None) for x in executor.occurrences),
        "routing_feedback_opened":False,
        "semantic_identity_modified":False,
        "external_effects":False,
        "laboratory_time_modified":False,
        "deterministic_fields_only":True,
    }
    receipt_sha=_sha256_json(payload)
    receipt={**payload,"receipt_sha256":receipt_sha}
    receipt_path=root/"pncs/v0.27/orch_execution/receipts"/f"{receipt_sha}.json"
    if persist:
        _atomic_write(receipt_path,(_compact_json(receipt)+"\n").encode("utf-8"))
    return CoupledExecutionResult(target,truth,final,executor.phase_state,receipt,str(receipt_path))
