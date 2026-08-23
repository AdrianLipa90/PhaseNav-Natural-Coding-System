from pathlib import Path
import pytest
from phasenav_natural_code.release_train_v1 import (
    ChangeClass, Decision, ReleaseStage, ReleaseTrainError,
    V028_GATES, V029_GATES, V030_GATES, classify_change, gate_status, next_stage,
    post_v1_idea_registry,
)

def test_new_idea_never_interrupts_release():
    for stage in ReleaseStage:
        r=classify_change(change_id="new-idea",change_class=ChangeClass.EXPERIMENTAL_IDEA,stage=stage)
        assert r.decision is Decision.QUARANTINE

def test_v028_admits_only_closure_classes():
    assert classify_change(change_id="fix",change_class=ChangeClass.RELEASE_BLOCKER_FIX,stage=ReleaseStage.V028_CLOSURE).decision is Decision.ADMIT
    assert classify_change(change_id="close",change_class=ChangeClass.CLOSURE_REQUIRED,stage=ReleaseStage.V028_CLOSURE).decision is Decision.ADMIT
    assert classify_change(change_id="hardening",change_class=ChangeClass.HARDENING_REQUIRED,stage=ReleaseStage.V028_CLOSURE).decision is Decision.REJECT

def test_v029_is_hardening_only():
    assert classify_change(change_id="hardening",change_class=ChangeClass.HARDENING_REQUIRED,stage=ReleaseStage.V029_HARDENING).decision is Decision.ADMIT
    assert classify_change(change_id="closure",change_class=ChangeClass.CLOSURE_REQUIRED,stage=ReleaseStage.V029_HARDENING).decision is Decision.REJECT

def test_v030_only_blockers_and_provenance():
    assert classify_change(change_id="fix",change_class=ChangeClass.RELEASE_BLOCKER_FIX,stage=ReleaseStage.V030_RC).decision is Decision.ADMIT
    assert classify_change(change_id="hardening",change_class=ChangeClass.HARDENING_REQUIRED,stage=ReleaseStage.V030_RC).decision is Decision.REJECT

def test_v1_is_terminal():
    assert classify_change(change_id="fix",change_class=ChangeClass.RELEASE_BLOCKER_FIX,stage=ReleaseStage.V1_RELEASED).decision is Decision.REJECT
    with pytest.raises(ReleaseTrainError): next_stage(ReleaseStage.V1_RELEASED,())

@pytest.mark.parametrize("stage,gates,next_expected",[
    (ReleaseStage.V028_CLOSURE,V028_GATES,ReleaseStage.V029_HARDENING),
    (ReleaseStage.V029_HARDENING,V029_GATES,ReleaseStage.V030_RC),
    (ReleaseStage.V030_RC,V030_GATES,ReleaseStage.V1_RELEASED),
])
def test_stage_advances_only_with_all_gates(stage,gates,next_expected):
    assert next_stage(stage,gates) is next_expected
    with pytest.raises(ReleaseTrainError): next_stage(stage,gates[:-1])

def test_gate_status_is_deterministic_and_ordered():
    s=gate_status(ReleaseStage.V028_CLOSURE,reversed(V028_GATES))
    assert s.complete
    assert s.passed==V028_GATES

def test_receipt_digest_is_content_deterministic():
    a=classify_change(change_id="x",change_class=ChangeClass.EXPERIMENTAL_IDEA,stage=ReleaseStage.V028_CLOSURE,evidence=("b","a"))
    b=classify_change(change_id="x",change_class=ChangeClass.EXPERIMENTAL_IDEA,stage=ReleaseStage.V028_CLOSURE,evidence=("b","a"))
    assert a.receipt_sha256==b.receipt_sha256

def test_current_research_program_is_preserved_post_v1():
    ideas=set(post_v1_idea_registry())
    assert {"prime_temporal_hydro","radical_engine","1024ion_embedding","primeflow_v02","temporal_geometry_v02","non_coboundary_prime_interaction"} <= ideas

def test_invalid_inputs_fail_closed():
    with pytest.raises(ReleaseTrainError): classify_change(change_id="",change_class=ChangeClass.CLOSURE_REQUIRED,stage=ReleaseStage.V028_CLOSURE)
