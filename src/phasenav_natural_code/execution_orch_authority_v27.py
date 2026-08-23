from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

try:
    from .hydro_time_v27 import _sha256_json, _typed_id
except ImportError:  # isolated harness compatibility
    from hydro_time_v27 import _sha256_json, _typed_id  # type: ignore

COUPLED_EXECUTION_CONTRACT_ID = "PNCS_ORCHORBITAL_COUPLED_EXECUTION_V0_27"
COUPLED_RECEIPT_SCHEMA = "PNCS_ORCHORBITAL_COUPLED_EXECUTION_RECEIPT_V0_27"
SESSION_SCHEMA = "PNCS_ORCHORBITAL_COUPLED_EXECUTION_SESSION_V0_27"
SIGMA_SCHEMA = "PNCS_SIGMA_STATE_V0_20"
STEP_SCHEMA = "PNCS_KAKU_TRANSITION_V0_20"
V20_RECEIPT_SCHEMA = "PNCS_NATIVE_EXECUTION_RECEIPT_V0_20"
V20_CONTRACT_ID = "PNCS_NATIVE_EXECUTION_CORE_V0_20"
EXECUTABLE_INTERNAL_OPERATORS = frozenset(
    {"IDENTITY","DIFFERENCE","CONDITION","NEGATION","COMPOSITION","ORDER","TRANSFORM"}
)

class CoupledExecutionV27Error(ValueError):
    pass


def _finite(value: object, field: str) -> float:
    try:
        x=float(value)
    except (TypeError,ValueError) as exc:
        raise CoupledExecutionV27Error(f"{field} must be finite") from exc
    if not math.isfinite(x):
        raise CoupledExecutionV27Error(f"{field} must be finite")
    return x


def _route(value: object, field: str) -> str:
    if not isinstance(value,str) or not value:
        raise CoupledExecutionV27Error(f"{field} must be non-empty")
    allowed=set("abcdefghijklmnopqrstuvwxyz0123456789_.:-")
    if value[0] not in "abcdefghijklmnopqrstuvwxyz" or any(c not in allowed for c in value):
        raise CoupledExecutionV27Error(f"{field} must be canonical internal route")
    return value


def _predicate_leaf_path(node: object) -> tuple[str,...]:
    if not isinstance(node,tuple) or not node:
        raise CoupledExecutionV27Error("canonical predicate must be non-empty tuple")
    kind=node[0]
    if kind=="comparison":
        if len(node)!=4 or node[2] not in {"lt","gt","eq"}:
            raise CoupledExecutionV27Error("invalid comparison")
        _finite(node[3],"threshold")
        return ("DIFFERENCE","CONDITION")
    if kind=="not":
        if len(node)!=2:
            raise CoupledExecutionV27Error("invalid not")
        return _predicate_leaf_path(node[1])+("NEGATION",)
    if kind in {"and","or"}:
        if len(node)<3:
            raise CoupledExecutionV27Error("compound predicate requires two children")
        leaves=()
        for child in node[1:]:
            leaves += _predicate_leaf_path(child)
        return leaves + ("COMPOSITION",)*(len(node)-2)
    raise CoupledExecutionV27Error("unsupported predicate")


def expected_leaf_path(graph: tuple[object,...]) -> tuple[str,...]:
    if not isinstance(graph,tuple) or len(graph)!=4 or graph[0]!="branch":
        raise CoupledExecutionV27Error("v0.27 coupled executor requires branch graph")
    pred,true_target,false_target=graph[1],graph[2],graph[3]
    _route(true_target,"true_target")
    if false_target is not None:
        _route(false_target,"false_target")
    path=_predicate_leaf_path(pred)
    if false_target is None:
        return path+("ORDER","TRANSFORM","COMPOSITION")
    return path+("NEGATION","ORDER","TRANSFORM","ORDER","TRANSFORM","COMPOSITION")


def definition_content_id(graph: tuple[object,...], leaf_path: Sequence[str]) -> str:
    leaves=tuple(str(x) for x in leaf_path)
    if leaves!=expected_leaf_path(graph):
        raise CoupledExecutionV27Error("leaf path does not match graph")
    payload={"schema":"PNCS_DEFINITION_CONTENT_V1","kind":"INTERNAL_BRANCH","canonical_graph":graph,"leaf_path":list(leaves)}
    return "pncs:def:sha256:"+_sha256_json(payload)


@dataclass(frozen=True)
class ProgramAuthority:
    source_v20_receipt_sha256: str
    content_id: str
    canonical_graph: tuple[object,...]
    leaf_path: tuple[str,...]
    realization_id: str
    realization_binding_id: str
    mass_binding_id: str
    phase36_sha256: str
    semantic_mass: float
    canonical_graph_sha256: str

    @classmethod
    def from_v20_receipt(cls, receipt: Mapping[str,object], canonical_graph: tuple[object,...]) -> "ProgramAuthority":
        if receipt.get("schema")!=V20_RECEIPT_SCHEMA or receipt.get("execution_contract_id")!=V20_CONTRACT_ID:
            raise CoupledExecutionV27Error("exact v0.20 receipt required")
        claimed=receipt.get("receipt_sha256")
        if not isinstance(claimed,str) or len(claimed)!=64:
            raise CoupledExecutionV27Error("v0.20 receipt SHA missing")
        body=dict(receipt); body.pop("receipt_sha256",None)
        if _sha256_json(body)!=claimed:
            raise CoupledExecutionV27Error("v0.20 receipt digest mismatch")
        program=receipt.get("program")
        if not isinstance(program,Mapping):
            raise CoupledExecutionV27Error("program provenance missing")
        leaf=tuple(str(x) for x in receipt.get("canonical_leaf_path",()))
        content_id=str(program.get("content_id",""))
        if definition_content_id(canonical_graph,leaf)!=content_id:
            raise CoupledExecutionV27Error("graph/content identity mismatch")
        graph_sha=_sha256_json(canonical_graph)
        if graph_sha!=receipt.get("canonical_graph_sha256"):
            raise CoupledExecutionV27Error("canonical graph SHA mismatch")
        return cls(
            str(claimed),content_id,canonical_graph,leaf,
            str(program["realization_id"]),str(program["realization_binding_id"]),
            str(program["mass_binding_id"]),str(program["phase36_sha256"]),
            _finite(program["semantic_mass"],"semantic_mass"),graph_sha,
        )

    @property
    def provenance_payload(self) -> dict[str,object]:
        return {
            "content_id":self.content_id,
            "realization_id":self.realization_id,
            "realization_binding_id":self.realization_binding_id,
            "mass_binding_id":self.mass_binding_id,
            "phase36_sha256":self.phase36_sha256,
            "semantic_mass":self.semantic_mass,
        }

    @property
    def authority_id(self) -> str:
        return _typed_id("pncs:coupled-program-authority",{
            "source_v20_receipt_sha256":self.source_v20_receipt_sha256,
            "program":self.provenance_payload,
            "canonical_graph_sha256":self.canonical_graph_sha256,
            "leaf_path":list(self.leaf_path),
        })


@dataclass(frozen=True)
class ResidentCoupledAuthority:
    program_authority: ProgramAuthority
    dispatch_id: str
    handle_id: str
    generation_id: str
    resident_admission_id: str
    resident_program_id: str
    result_id: str
    lineage_id: str

    @classmethod
    def from_records(
        cls,
        program_authority: ProgramAuthority,
        dispatch: Mapping[str,object],
        lineage: Mapping[str,object],
    ) -> "ResidentCoupledAuthority":
        if not isinstance(program_authority, ProgramAuthority):
            raise CoupledExecutionV27Error("ProgramAuthority required")
        if dispatch.get("schema")!="PNCS_RESIDENT_CONTROL_DISPATCH_RECEIPT_V0_25" or dispatch.get("runtime_contract_id")!="PNCS_PERSISTENT_RUNTIME_V0_25":
            raise CoupledExecutionV27Error("exact v0.25 resident dispatch required")
        dispatch_id=dispatch.get("dispatch_id")
        if not isinstance(dispatch_id,str):
            raise CoupledExecutionV27Error("resident dispatch id missing")
        body=dict(dispatch); body.pop("dispatch_id",None)
        if _typed_id("pncs:resident-dispatch",body)!=dispatch_id:
            raise CoupledExecutionV27Error("resident dispatch digest mismatch")
        if dispatch.get("execution_receipt_sha256")!=program_authority.source_v20_receipt_sha256:
            raise CoupledExecutionV27Error("resident dispatch/source v0.20 mismatch")
        for field in ("external_effects","continuation_execution_opened","return_execution_opened","static_runtime_fallback"):
            if dispatch.get(field) is not False:
                raise CoupledExecutionV27Error(f"resident authority crossed closed boundary: {field}")
        if dispatch.get("kernel_scope")!="CONTROL_ROOT_V0_20" or dispatch.get("deterministic_fields_only") is not True:
            raise CoupledExecutionV27Error("resident dispatch is outside exact control scope")
        if lineage.get("schema")!="PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22" or lineage.get("lineage_contract_id")!="PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22":
            raise CoupledExecutionV27Error("exact v0.22 lineage required")
        lineage_id=lineage.get("lineage_id")
        if not isinstance(lineage_id,str):
            raise CoupledExecutionV27Error("lineage id missing")
        lineage_body=dict(lineage); lineage_body.pop("lineage_id",None)
        if _typed_id("pncs:lineage",lineage_body)!=lineage_id:
            raise CoupledExecutionV27Error("v0.22 lineage digest mismatch")
        if lineage.get("execution_receipt_sha256")!=program_authority.source_v20_receipt_sha256:
            raise CoupledExecutionV27Error("lineage/source v0.20 mismatch")
        if dispatch.get("lineage_id")!=lineage_id or dispatch.get("result_id")!=lineage.get("result_id"):
            raise CoupledExecutionV27Error("dispatch/lineage identity mismatch")
        hierarchy=lineage.get("hierarchy")
        nodes=hierarchy.get("nodes") if isinstance(hierarchy,Mapping) else None
        if not isinstance(nodes,list) or not nodes or not isinstance(nodes[-1],Mapping) or nodes[-1].get("content_id")!=program_authority.content_id:
            raise CoupledExecutionV27Error("lineage does not terminate at program Definition")
        return cls(
            program_authority=program_authority,
            dispatch_id=dispatch_id,
            handle_id=str(dispatch.get("handle_id","")),
            generation_id=str(dispatch.get("generation_id","")),
            resident_admission_id=str(dispatch.get("resident_admission_id","")),
            resident_program_id=str(dispatch.get("program_id","")),
            result_id=str(dispatch.get("result_id","")),
            lineage_id=lineage_id,
        )

    @property
    def payload(self) -> dict[str,object]:
        return {
            "program_authority_id":self.program_authority.authority_id,
            "dispatch_id":self.dispatch_id,
            "handle_id":self.handle_id,
            "generation_id":self.generation_id,
            "resident_admission_id":self.resident_admission_id,
            "resident_program_id":self.resident_program_id,
            "result_id":self.result_id,
            "lineage_id":self.lineage_id,
            "external_effects":False,
            "static_runtime_fallback":False,
        }

    @property
    def authority_id(self) -> str:
        return _typed_id("pncs:resident-coupled-authority",self.payload)

    def validate_active_pointer(self, root: Path) -> None:
        digest=self.handle_id.rsplit(":",1)[-1]
        path=root/"pncs/v0.25/runtime/active"/f"{digest}.json"
        try:
            active=json.loads(path.read_text("utf-8"))
        except (OSError,json.JSONDecodeError) as exc:
            raise CoupledExecutionV27Error("resident active pointer unavailable") from exc
        if active.get("schema")!="PNCS_RESIDENT_ACTIVE_POINTER_V0_25":
            raise CoupledExecutionV27Error("invalid resident active pointer")
        if active.get("handle_id")!=self.handle_id or active.get("generation_id")!=self.generation_id or active.get("program_id")!=self.resident_program_id:
            raise CoupledExecutionV27Error("resident authority is not active on declared generation")


def _normalize_values(values: Mapping[str,object]) -> tuple[tuple[str,float],...]:
    if not isinstance(values,Mapping):
        raise CoupledExecutionV27Error("runtime values mapping required")
    out=[]
    for key in sorted(values):
        if not isinstance(key,str) or not key:
            raise CoupledExecutionV27Error("value names must be non-empty")
        out.append((key,_finite(values[key],f"value {key}")))
    return tuple(out)
