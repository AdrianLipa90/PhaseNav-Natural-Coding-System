from __future__ import annotations

import hashlib
from types import SimpleNamespace
import pytest
from phasenav_natural_code import full_program_executor_v01 as m


def tid(kind: str, label: str) -> str:
    return f"pncs:{kind}:sha256:{hashlib.sha256(label.encode()).hexdigest()}"


CONTROL = ("DIFFERENCE", "CONDITION", "DIFFERENCE", "CONDITION", "COMPOSITION", "NEGATION", "ORDER", "TRANSFORM", "COMPOSITION")


def make_program(routes=("runtime.audit", "runtime.finish"), selector="result.control_location", source_kind="V0_20_RESULT"):
    definition_id = tid("def", "control")
    route_objs = tuple(SimpleNamespace(ref_id=tid("route-ref", r), canonical=r, route_kind="INTERNAL_TRANSFORM") for r in routes)
    return_ref = tid("return-ref", selector + source_kind)
    ret = SimpleNamespace(ref_id=return_ref, canonical=selector, source_kind=source_kind)
    schedule = CONTROL + sum((("ORDER", "TRANSFORM", "COMPOSITION") for _ in route_objs), ()) + ("RETURN",)
    cp = {
        "schema": m.COMPOSITION_SCHEMA, "composition_contract_id": m.COMPOSITION_SCHEMA,
        "kind": "BOUNDED_NATURAL_PROGRAM_COMPOSITION", "control_definition_id": definition_id,
        "continuation_routes": [{"ref_id": r.ref_id, "canonical": r.canonical, "route_kind": r.route_kind} for r in route_objs],
        "return_selector": {"ref_id": return_ref, "canonical": selector, "source_kind": source_kind},
        "operator_schedule": list(schedule), "required_result_lineage_contract_id": m.LINEAGE_CONTRACT_ID,
        "external_effects": False, "free_form_nl_execution": False, "deterministic_fields_only": True,
    }
    cid = m._typed_id("pncs:composition", cp)
    comp = SimpleNamespace(composition_id=cid, control_content=SimpleNamespace(content_id=definition_id, leaf_path=CONTROL), continuation_routes=route_objs, return_spec=ret, operator_schedule=schedule, payload=cp)
    pp = {
        "schema": m.PROGRAM_SCHEMA, "program_contract_id": m.PROGRAM_CONTRACT_ID, "composition_id": cid,
        "operator_schedule": list(schedule), "return_ref_id": return_ref, "required_result_lineage_contract_id": m.LINEAGE_CONTRACT_ID,
        "native_execution_opened": False, "return_execution_opened": False, "external_effects": False,
        "free_form_nl_execution": False, "static_runtime_fallback": False, "deterministic_fields_only": True,
    }
    unit = SimpleNamespace(program_id=m._typed_id("pncs:program", pp), composition_id=cid, operator_schedule=schedule, return_ref_id=return_ref, semantic_payload=pp)
    return unit, comp


def rebind(unit, comp, schedule=None):
    if schedule is not None:
        unit.operator_schedule = tuple(schedule); comp.operator_schedule = tuple(schedule)
        comp.payload = dict(comp.payload, operator_schedule=list(schedule))
    comp.composition_id = m._typed_id("pncs:composition", comp.payload)
    unit.composition_id = comp.composition_id
    unit.semantic_payload = dict(unit.semantic_payload, composition_id=comp.composition_id, operator_schedule=list(unit.operator_schedule))
    unit.program_id = m._typed_id("pncs:program", unit.semantic_payload)


def make_dispatch(unit, target="runtime.continue", truth="FALSE", handle=None):
    payload = {
        "schema": m.DISPATCH_SCHEMA, "runtime_contract_id": m.RUNTIME_CONTRACT_ID, "kernel_scope": "CONTROL_ROOT_V0_20",
        "handle_id": handle or tid("resident", "handle"), "program_id": unit.program_id,
        "generation_id": tid("runtime-generation", "generation"), "resident_admission_id": tid("resident-admission", "admission"),
        "execution_receipt_sha256": hashlib.sha256(b"execution").hexdigest(), "result_id": tid("result", "result"),
        "lineage_id": tid("lineage", "lineage"), "target": target, "branch_truth_state": truth,
        "result_lineage_contract_id": m.LINEAGE_CONTRACT_ID, "process_reconstruction_required": False,
        "continuation_execution_opened": False, "return_execution_opened": False, "external_effects": False,
        "static_runtime_fallback": False, "deterministic_fields_only": True,
    }
    return SimpleNamespace(payload=payload, dispatch_id=m._typed_id("pncs:resident-dispatch", payload))


def test_plan_partitions_exact_schedule():
    u,c=make_program(); p=m.compile_full_program_plan(u,c)
    assert [i.kind for i in p.instructions] == ["CONTROL_DISPATCH","CONTINUATION_ROUTE","CONTINUATION_ROUTE","RETURN"]
    assert p.instructions[0].operator_stop == len(CONTROL)
    assert p.instructions[-1].operator_stop == len(u.operator_schedule)


def test_no_continuation_plan():
    u,c=make_program(routes=()); assert [i.kind for i in m.compile_full_program_plan(u,c).instructions] == ["CONTROL_DISPATCH","RETURN"]


def test_dispatch_called_once_and_routes_execute_in_order():
    u,c=make_program(routes=("r.one","r.two","r.three")); d=make_dispatch(u,target="r.zero"); calls=[]
    x=m.execute_full_program(u,c,lambda: calls.append(1) or d)
    assert calls == [1]
    assert [s.control_location_after for s in x.trace] == ["r.zero","r.one","r.two","r.three","r.three"]
    assert x.final_control_location == x.return_value == "r.three"


@pytest.mark.parametrize("selector,source,expected", [
    ("result.control_location","V0_20_RESULT","runtime.continue"),
    ("result.branch_truth_state","V0_20_RESULT","TRUE"),
    ("result.lineage_id","V0_22_LINEAGE","LINEAGE"),
])
def test_registered_returns(selector,source,expected):
    u,c=make_program(routes=(),selector=selector,source_kind=source); d=make_dispatch(u,truth="TRUE")
    x=m.execute_full_program(u,c,lambda:d)
    value=d.payload["lineage_id"] if expected == "LINEAGE" else expected
    assert x.return_value == value


def test_final_sigma_binding_is_explicit():
    u,c=make_program(selector="result.final_sigma_id",source_kind="V0_20_FINAL_STATE"); d=make_dispatch(u)
    with pytest.raises(m.FullProgramExecutorV01Error,match="explicit typed return binding"): m.execute_full_program(u,c,lambda:d)
    sigma=tid("sigma","final"); assert m.execute_full_program(u,c,lambda:d,return_bindings={"result.final_sigma_id":sigma}).return_value == sigma


def test_receipt_boundaries_and_replay():
    u,c=make_program(); d=make_dispatch(u); a=m.execute_full_program(u,c,lambda:d); b=m.execute_full_program(u,c,lambda:d); p=a.payload
    assert a.execution_id == b.execution_id and a.payload == b.payload
    assert p["continuation_execution_opened"] and p["return_execution_opened"] and p["full_current_bounded_program_execution"]
    assert not p["loops_opened"] and not p["function_calls_opened"] and not p["external_effects"] and not p["static_runtime_fallback"]


def test_prepared_hot_path_is_semantically_identical():
    u,c=make_program(); d=make_dispatch(u); plan=m.compile_full_program_plan(u,c)
    assert m.execute_prepared_program(plan,lambda:d).payload == m.execute_full_program(u,c,lambda:d).payload
    with pytest.raises(m.FullProgramExecutorV01Error,match="FullProgramExecutionPlan required"): m.execute_prepared_program(object(),lambda:d)


def test_valid_but_different_composition_rejected():
    u,_=make_program(routes=("r.a",)); _,c=make_program(routes=("r.b",))
    with pytest.raises(m.FullProgramExecutorV01Error,match="unit/composition ID mismatch"): m.compile_full_program_plan(u,c)


@pytest.mark.parametrize("which", ["program","composition"])
def test_content_address_tamper_rejected(which):
    u,c=make_program()
    if which == "program": u.program_id=tid("program","forged"); msg="program content-address"
    else: c.composition_id=tid("composition","forged"); msg="composition content-address"
    with pytest.raises(m.FullProgramExecutorV01Error,match=msg): m.compile_full_program_plan(u,c)


@pytest.mark.parametrize("field", ["native_execution_opened","return_execution_opened","external_effects","free_form_nl_execution","static_runtime_fallback"])
def test_v24_closed_boundaries(field):
    u,c=make_program(); u.semantic_payload=dict(u.semantic_payload,**{field:True})
    with pytest.raises(m.FullProgramExecutorV01Error,match=f"{field} must remain false"): m.compile_full_program_plan(u,c)


@pytest.mark.parametrize("field", ["external_effects","free_form_nl_execution"])
def test_v23_closed_boundaries(field):
    u,c=make_program(); c.payload=dict(c.payload,**{field:True})
    with pytest.raises(m.FullProgramExecutorV01Error,match=f"{field} must remain false"): m.compile_full_program_plan(u,c)


def test_route_kind_and_span_fail_closed():
    u,c=make_program(routes=("r",)); r=c.continuation_routes[0]
    c.continuation_routes=(SimpleNamespace(ref_id=r.ref_id,canonical=r.canonical,route_kind="EXTERNAL_EFFECT"),)
    with pytest.raises(m.FullProgramExecutorV01Error,match="INTERNAL_TRANSFORM"): m.compile_full_program_plan(u,c)
    u,c=make_program(routes=("r",)); s=list(u.operator_schedule); s[len(CONTROL)+1]="NEGATION"; rebind(u,c,s)
    with pytest.raises(m.FullProgramExecutorV01Error,match="continuation operator span mismatch"): m.compile_full_program_plan(u,c)


def test_terminal_return_and_return_ref_fail_closed():
    u,c=make_program(routes=()); rebind(u,c,CONTROL+("COMPOSITION",))
    with pytest.raises(m.FullProgramExecutorV01Error,match="terminate with RETURN"): m.compile_full_program_plan(u,c)
    u,c=make_program(); c.return_spec=SimpleNamespace(ref_id=tid("return-ref","other"),canonical=c.return_spec.canonical,source_kind=c.return_spec.source_kind)
    with pytest.raises(m.FullProgramExecutorV01Error,match="return reference mismatch"): m.compile_full_program_plan(u,c)


@pytest.mark.parametrize("field", ["continuation_execution_opened","return_execution_opened","external_effects","static_runtime_fallback"])
def test_dispatch_must_arrive_from_closed_v25(field):
    u,c=make_program(); d=make_dispatch(u); d.payload=dict(d.payload,**{field:True}); d.dispatch_id=m._typed_id("pncs:resident-dispatch",d.payload)
    with pytest.raises(m.FullProgramExecutorV01Error,match=f"{field} must remain false"): m.execute_full_program(u,c,lambda:d)


@pytest.mark.parametrize("field,value,msg", [
    ("schema","WRONG","schema/contract"),("runtime_contract_id","WRONG","schema/contract"),
    ("kernel_scope","WRONG","kernel scope"),("result_lineage_contract_id","WRONG","lineage contract"),
])
def test_dispatch_contract_tamper(field,value,msg):
    u,c=make_program(); d=make_dispatch(u); d.payload=dict(d.payload,**{field:value}); d.dispatch_id=m._typed_id("pncs:resident-dispatch",d.payload)
    with pytest.raises(m.FullProgramExecutorV01Error,match=msg): m.execute_full_program(u,c,lambda:d)


def test_dispatch_program_handle_digest_and_truth_tamper():
    u,c=make_program(); d=make_dispatch(u); d.payload=dict(d.payload,program_id=tid("program","wrong")); d.dispatch_id=m._typed_id("pncs:resident-dispatch",d.payload)
    with pytest.raises(m.FullProgramExecutorV01Error,match="program mismatch"): m.execute_full_program(u,c,lambda:d)
    expected=tid("resident","expected"); d=make_dispatch(u,handle=tid("resident","actual"))
    with pytest.raises(m.FullProgramExecutorV01Error,match="handle mismatch"): m.execute_full_program(u,c,lambda:d,expected_handle_id=expected)
    d=make_dispatch(u); d.dispatch_id=tid("resident-dispatch","wrong")
    with pytest.raises(m.FullProgramExecutorV01Error,match="content-address identity mismatch"): m.execute_full_program(u,c,lambda:d)
    d=make_dispatch(u); d.payload=dict(d.payload,branch_truth_state="MAYBE"); d.dispatch_id=m._typed_id("pncs:resident-dispatch",d.payload)
    with pytest.raises(m.FullProgramExecutorV01Error,match="invalid resident control result"): m.execute_full_program(u,c,lambda:d)


def test_resident_runtime_delegation():
    u,c=make_program(); h=tid("resident","handle"); d=make_dispatch(u,handle=h); kernel=lambda:(object(),object())
    class R:
        def __init__(self): self.calls=[]
        def dispatch_control(self,handle,callback): self.calls.append((handle,callback)); return d
    r=R(); x=m.execute_resident_program(r,h,u,c,kernel); assert r.calls == [(h,kernel)] and x.control_dispatch_id == d.dispatch_id
    with pytest.raises(m.FullProgramExecutorV01Error,match="dispatch_control"): m.execute_resident_program(object(),h,u,c,kernel)


def test_plan_instruction_and_schedule_bounds():
    pid=tid("program","p"); cid=tid("composition","c")
    a=m.FullProgramInstruction(0,"CONTROL_DISPATCH",0,1,tid("def","d")); b=m.FullProgramInstruction(1,"RETURN",2,3,tid("return-ref","r"),target="result.control_location",source_kind="V0_20_RESULT")
    with pytest.raises(m.FullProgramExecutorV01Error,match="spans must be contiguous"): m.FullProgramExecutionPlan(pid,cid,("TRANSFORM","ORDER","RETURN"),(a,b))
    with pytest.raises(m.FullProgramExecutorV01Error,match="pc must be non-negative"): m.FullProgramInstruction(-1,"CONTROL_DISPATCH",0,1,tid("def","d"))
    u,c=make_program(routes=()); s=("TRANSFORM",)*m.MAX_PROGRAM_OPERATORS+("RETURN",); rebind(u,c,s)
    with pytest.raises(m.FullProgramExecutorV01Error,match="schedule size outside"): m.compile_full_program_plan(u,c)
