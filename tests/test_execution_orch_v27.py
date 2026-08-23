import copy, importlib.util, json, sys
from pathlib import Path
import pytest

BASE=Path("/mnt/data/pncs_v027")
for name in ("hydro_time_v27","hydro_schedule_v27","orch_orbital_v27","orch_hydro_v27","execution_orch_v27"):
    spec=importlib.util.spec_from_file_location(name,BASE/f"{name}.py")
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
h=sys.modules["hydro_time_v27"];o=sys.modules["orch_orbital_v27"];oh=sys.modules["orch_hydro_v27"];e=sys.modules["execution_orch_v27"]
R=json.loads(Path("/dev/shm/ciel_noema/pncs/v0.20/receipts/84d40f600a8aa9e59ebc6dc42c856bcffec9265d04f791e7f5c49cdba2d583ad.json").read_text())
GRAPH=("branch",("or",("comparison","memory_pressure","gt",0.9),("comparison","risk","gt",0.8)),"safety.pause","runtime.continue")
AUTH=e.ProgramAuthority.from_v20_receipt(R,GRAPH)

DISPATCH=json.loads(Path("/dev/shm/ciel_noema/pncs/v0.25/runtime/receipts/dispatch/fd18f2d0296321d432a49e699d2f72a0a03313ed2dcc87b9aba647555f12c2e2.json").read_text())
LINEAGE=json.loads(Path("/dev/shm/ciel_noema/pncs/v0.22/lineage/34bd13f534987989ab212b5a6906d0cfa762305ee9a87af7a058badd2b2bcfd6.json").read_text())
RESAUTH=e.ResidentCoupledAuthority.from_records(AUTH,DISPATCH,LINEAGE)
Z=(0.0,)*36
ATTRS=(o.AttractorReport("AttractorEC",.75,Z,.5,"EC"),o.AttractorReport("AttractorZS",.8,Z,.5,"ZS"),o.AttractorReport("AttractorLLMTemp",0,Z,0,"DISABLED"))
POT=o.TotalPotential(0,0,0,0,0,0)
RED=o.ReductionKernel(1,1,1,1,10)
PROFILE=oh.OrchHydroControlProfile(o.SubjectiveTimeKernel(),1,ATTRS,POT,RED,1,0)
GATE=h.HydrodynamicPhaseGate(.5,.2,steps=1,coordinate_dt=.01)

def run(profile=PROFILE,gate=GATE,persist=False):
    return e.execute_orchorbital_coupled(AUTH,{"memory_pressure":0.0,"risk":0.0},"runtime.continue",profile,{"*":gate},resident_authority=RESAUTH,persist=persist)

def test_authority_binds_exact_v20_receipt(): assert AUTH.source_v20_receipt_sha256==R["receipt_sha256"]
def test_authority_binds_exact_definition(): assert AUTH.content_id==R["program"]["content_id"]
def test_authority_recomputes_definition(): assert e.definition_content_id(GRAPH,R["canonical_leaf_path"])==R["program"]["content_id"]
def test_tampered_v20_receipt_rejected():
    x=copy.deepcopy(R);x["result"]["control_location"]="x"
    with pytest.raises(e.CoupledExecutionV27Error,match="digest"): e.ProgramAuthority.from_v20_receipt(x,GRAPH)
def test_wrong_graph_rejected():
    bad=("branch",("comparison","risk","gt",.8),"safety.pause","runtime.continue")
    with pytest.raises(e.CoupledExecutionV27Error): e.ProgramAuthority.from_v20_receipt(R,bad)
def test_false_branch_same_target(): 
    x=run(); assert x.branch_truth_state=="FALSE" and x.target=="runtime.continue"
def test_nine_semantic_steps():
    assert len(run().receipt["semantic_projection"]["steps"])==9
def test_nine_orch_occurrences():
    assert len(run().receipt["orch_occurrences"])==9
def test_operator_order_matches_frozen_v20():
    x=run().receipt["semantic_projection"]["steps"]
    assert [q["operator_id"] for q in x]==[q["operator_id"] for q in R["steps"]]
def test_operator_hashes_match_frozen_v20():
    x=run().receipt["semantic_projection"]["steps"]
    assert [q["operator_vector_sha256"] for q in x]==[q["operator_vector_sha256"] for q in R["steps"]]
def test_operator_bindings_match_frozen_v20():
    x=run().receipt["semantic_projection"]["steps"]
    assert [q["bindings"] for q in x]==[q["bindings"] for q in R["steps"]]
def test_semantic_projection_program_same():
    assert run().receipt["semantic_projection"]["program"]==R["program"]
def test_semantic_mass_not_authorization():
    assert run().receipt["semantic_projection"]["semantic_mass_is_authorization"] is False
def test_orch_occurrences_sigma_bound():
    x=run().receipt
    for sem,orch in zip(x["semantic_projection"]["steps"],x["orch_occurrences"]):
        assert orch["before_sigma_id"]==sem["before_sigma_id"]
        assert orch["after_sigma_id"]==sem["after_sigma_id"]
        assert orch["operator_id"]==sem["operator_id"]
def test_routing_feedback_remains_closed():
    assert run().receipt["routing_feedback_opened"] is False
def test_semantic_identity_unmodified():
    assert run().receipt["semantic_identity_modified"] is False
def test_external_effects_closed():
    assert run().receipt["external_effects"] is False
def test_no_laboratory_time_claim():
    assert run().receipt["laboratory_time_modified"] is False
def test_no_memory_without_reduction_selection():
    assert run().receipt["stable_memory_update_count"]==0
def test_phase_proper_time_advances():
    assert run().receipt["phase_proper_time_advanced"]>0
def test_profile_changes_phase_flow_not_semantic_operator_trace():
    fast=oh.OrchHydroControlProfile(o.SubjectiveTimeKernel(beta_coherence=1,beta_defect=-1),1,ATTRS,POT,RED,1,0)
    a=run(PROFILE).receipt;b=run(fast).receipt
    assert [q["operator_id"] for q in a["semantic_projection"]["steps"]]==[q["operator_id"] for q in b["semantic_projection"]["steps"]]
    assert a["semantic_projection"]["result"]==b["semantic_projection"]["result"]
    assert a["phase_proper_time_advanced"]!=b["phase_proper_time_advanced"] or a["final_phase_state_id"]!=b["final_phase_state_id"]
def test_admission_mismatch_fails_closed():
    with pytest.raises(e.CoupledExecutionV27Error,match="admission"): e.execute_orchorbital_coupled(AUTH,{"memory_pressure":0,"risk":0},"safety.pause",PROFILE,{"*":GATE},resident_authority=RESAUTH,persist=False)
def test_missing_gate_fails_closed():
    with pytest.raises(e.CoupledExecutionV27Error,match="no HydrodynamicPhaseGate"): e.execute_orchorbital_coupled(AUTH,{"memory_pressure":0,"risk":0},"runtime.continue",PROFILE,{},resident_authority=RESAUTH,persist=False)
def test_noncanonical_root_rejected(tmp_path):
    with pytest.raises(e.CoupledExecutionV27Error,match="fixed"): e.execute_orchorbital_coupled(AUTH,{"memory_pressure":0,"risk":0},"runtime.continue",PROFILE,{"*":GATE},resident_authority=RESAUTH,surface_root=tmp_path,persist=False)
def test_receipt_is_content_addressed():
    x=run().receipt
    body=dict(x);body.pop("receipt_sha256")
    assert h._sha256_json(body)==x["receipt_sha256"]

def test_resident_authority_binds_dispatch_lineage_and_handle():
    assert RESAUTH.dispatch_id==DISPATCH["dispatch_id"]
    assert RESAUTH.lineage_id==LINEAGE["lineage_id"]
    assert RESAUTH.handle_id==DISPATCH["handle_id"]

def test_resident_authority_active_pointer_passes():
    RESAUTH.validate_active_pointer(Path("/dev/shm/ciel_noema"))

def test_coupled_receipt_binds_resident_authority():
    x=run().receipt
    assert x["resident_authority_id"]==RESAUTH.authority_id
    assert x["resident_dispatch_id"]==DISPATCH["dispatch_id"]
    assert x["v22_lineage_id"]==LINEAGE["lineage_id"]

def test_missing_resident_authority_fails_closed():
    with pytest.raises(e.CoupledExecutionV27Error,match="resident"):
        e.execute_orchorbital_coupled(AUTH,{"memory_pressure":0,"risk":0},"runtime.continue",PROFILE,{"*":GATE},persist=False)

def test_tampered_dispatch_rejected():
    x=copy.deepcopy(DISPATCH);x["target"]="x"
    with pytest.raises(e.CoupledExecutionV27Error,match="digest"):
        e.ResidentCoupledAuthority.from_records(AUTH,x,LINEAGE)

def test_tampered_lineage_rejected():
    x=copy.deepcopy(LINEAGE);x["result_id"]="pncs:result:sha256:"+"0"*64
    with pytest.raises(e.CoupledExecutionV27Error,match="digest"):
        e.ResidentCoupledAuthority.from_records(AUTH,DISPATCH,x)

def test_persistence_stays_under_live_surface():
    x=run(persist=True)
    p=Path(x.receipt_path)
    assert p.is_file()
    assert str(p).startswith("/dev/shm/ciel_noema/pncs/v0.27/orch_execution/receipts/")
