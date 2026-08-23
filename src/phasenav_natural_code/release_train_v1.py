from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Mapping


class ReleaseTrainError(RuntimeError):
    pass


class ReleaseStage(str, Enum):
    V028_CLOSURE = "V0_28_RELEASE_CLOSURE"
    V029_HARDENING = "V0_29_RELEASE_HARDENING"
    V030_RC = "V0_30_RELEASE_CANDIDATE"
    V1_RELEASED = "V1_0_RELEASED"


class ChangeClass(str, Enum):
    RELEASE_BLOCKER_FIX = "RELEASE_BLOCKER_FIX"
    CLOSURE_REQUIRED = "CLOSURE_REQUIRED"
    HARDENING_REQUIRED = "HARDENING_REQUIRED"
    DOC_PROVENANCE = "DOC_PROVENANCE"
    EXPERIMENTAL_IDEA = "EXPERIMENTAL_IDEA"


class Decision(str, Enum):
    ADMIT = "ADMIT_ACTIVE_RELEASE"
    QUARANTINE = "QUARANTINE_POST_V1"
    REJECT = "REJECT_STAGE_MISMATCH"

V028_GATES=("exact_adversarial_authority","exact_execution_orch_v27","orch_hydro_regressions","full_repository_conformance","live_v56_same_snapshot_witness","tests_live","final_manifest","foundation_status_v028")
V029_GATES=("clean_install","reproducible_package","deterministic_replay","public_api_freeze","documentation_freeze","live_soak","no_static_runtime_fallback","release_provenance_complete")
V030_GATES=("release_candidate_build","clean_room_replay","critical_regressions_zero","version_and_changelog_final","tag_payload_manifest_match")
_STAGE_GATES={ReleaseStage.V028_CLOSURE:V028_GATES,ReleaseStage.V029_HARDENING:V029_GATES,ReleaseStage.V030_RC:V030_GATES,ReleaseStage.V1_RELEASED:()}
_ALLOWED={ReleaseStage.V028_CLOSURE:frozenset({ChangeClass.RELEASE_BLOCKER_FIX,ChangeClass.CLOSURE_REQUIRED,ChangeClass.DOC_PROVENANCE}),ReleaseStage.V029_HARDENING:frozenset({ChangeClass.RELEASE_BLOCKER_FIX,ChangeClass.HARDENING_REQUIRED,ChangeClass.DOC_PROVENANCE}),ReleaseStage.V030_RC:frozenset({ChangeClass.RELEASE_BLOCKER_FIX,ChangeClass.DOC_PROVENANCE}),ReleaseStage.V1_RELEASED:frozenset()}
_POST_V1_IDEAS=("prime_temporal_hydro","radical_engine","1024ion_embedding","primeflow_v02","temporal_geometry_v02","non_coboundary_prime_interaction")

def canonical_digest(payload: Mapping[str, object]) -> str:
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")
    return sha256(raw).hexdigest()

@dataclass(frozen=True)
class AdmissionReceipt:
    change_id:str; change_class:ChangeClass; stage:ReleaseStage; decision:Decision; reason:str; evidence:tuple[str,...]; receipt_sha256:str

@dataclass(frozen=True)
class GateStatus:
    stage:ReleaseStage; required:tuple[str,...]; passed:tuple[str,...]; missing:tuple[str,...]
    @property
    def complete(self)->bool: return not self.missing

def classify_change(*,change_id:str,change_class:ChangeClass,stage:ReleaseStage,evidence:Iterable[str]=())->AdmissionReceipt:
    if not isinstance(change_id,str) or not change_id.strip(): raise ReleaseTrainError("non-empty change_id required")
    if not isinstance(change_class,ChangeClass): raise ReleaseTrainError("ChangeClass required")
    if not isinstance(stage,ReleaseStage): raise ReleaseTrainError("ReleaseStage required")
    ev=tuple(str(x) for x in evidence if str(x))
    if change_class is ChangeClass.EXPERIMENTAL_IDEA:
        decision=Decision.QUARANTINE; reason="new research is preserved but cannot block or enter the active v1.0 release train"
    elif change_class in _ALLOWED[stage]:
        decision=Decision.ADMIT; reason="change class is admitted by the current release stage"
    else:
        decision=Decision.REJECT; reason="change class is outside the frozen scope of the current release stage"
    body={"change_id":change_id.strip(),"change_class":change_class.value,"stage":stage.value,"decision":decision.value,"reason":reason,"evidence":ev}
    return AdmissionReceipt(body["change_id"],change_class,stage,decision,reason,ev,canonical_digest(body))

def gate_status(stage:ReleaseStage,passed:Iterable[str])->GateStatus:
    if not isinstance(stage,ReleaseStage): raise ReleaseTrainError("ReleaseStage required")
    required=_STAGE_GATES[stage]; seen=frozenset(str(x) for x in passed)
    return GateStatus(stage,required,tuple(g for g in required if g in seen),tuple(g for g in required if g not in seen))

def next_stage(stage:ReleaseStage,passed:Iterable[str])->ReleaseStage:
    status=gate_status(stage,passed)
    if not status.complete: raise ReleaseTrainError("stage cannot advance with missing gates: "+",".join(status.missing))
    if stage is ReleaseStage.V028_CLOSURE: return ReleaseStage.V029_HARDENING
    if stage is ReleaseStage.V029_HARDENING: return ReleaseStage.V030_RC
    if stage is ReleaseStage.V030_RC: return ReleaseStage.V1_RELEASED
    raise ReleaseTrainError("v1.0 is terminal for this release train")

def post_v1_idea_registry()->tuple[str,...]: return _POST_V1_IDEAS
