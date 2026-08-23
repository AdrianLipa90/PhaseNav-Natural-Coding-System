import hashlib
import pytest
from phasenav_natural_code.branch_session_collision_v28 import *

REPO = "AdrianLipa90/PhaseNav-Natural-Coding-System"
A = "a"*40
B = "b"*40
C = "c"*40
D = "d"*40
PAYLOAD = hashlib.sha256(b"payload").hexdigest()
NONCE = hashlib.sha256(b"nonce").hexdigest()
NOW = 200


def lease(session="s1", branch="feat/x", head=A, start=100, end=300):
    return SessionLease(session, REPO, branch, head, NONCE, start, end)

def write_intent(head=A):
    return WriteIntent("WRITE", "s1", REPO, "feat/x", head, PAYLOAD)

def merge_intent(base=A, src=B):
    return WriteIntent("MERGE", "s1", REPO, "main", base, PAYLOAD, "feat/x", src)


def test_valid_write_passes():
    a=evaluate_collision_gate(write_intent(), BranchSnapshot(REPO,"feat/x",A), [lease()], NOW)
    assert a.decision=="PASS" and a.reasons==()

def test_target_head_move_blocks():
    a=evaluate_collision_gate(write_intent(), BranchSnapshot(REPO,"feat/x",B), [lease()], NOW)
    assert "TARGET_HEAD_MOVED" in a.reasons

def test_foreign_session_blocks():
    a=evaluate_collision_gate(write_intent(), BranchSnapshot(REPO,"feat/x",A), [lease(),lease("s2")], NOW)
    assert "FOREIGN_ACTIVE_SESSION:feat/x" in a.reasons

def test_expired_foreign_session_does_not_block():
    a=evaluate_collision_gate(write_intent(), BranchSnapshot(REPO,"feat/x",A), [lease(),lease("s2",end=150)], NOW)
    assert a.decision=="PASS"

def test_missing_own_lease_blocks():
    a=evaluate_collision_gate(write_intent(), BranchSnapshot(REPO,"feat/x",A), [], NOW)
    assert "MISSING_ACTIVE_TARGET_LEASE" in a.reasons

def test_stale_own_lease_blocks():
    a=evaluate_collision_gate(write_intent(), BranchSnapshot(REPO,"feat/x",A), [lease(head=B)], NOW)
    assert "OWN_TARGET_LEASE_STALE" in a.reasons

def test_write_cannot_have_source():
    with pytest.raises(BranchSessionCollisionError): WriteIntent("WRITE","s1",REPO,"x",A,PAYLOAD,"y",B)

def test_merge_requires_source():
    with pytest.raises(BranchSessionCollisionError): WriteIntent("MERGE","s1",REPO,"main",A,PAYLOAD)

def test_valid_merge_passes_with_both_leases():
    i=merge_intent(); leases=[lease(branch="main",head=A),lease(branch="feat/x",head=B)]
    a=evaluate_collision_gate(i,BranchSnapshot(REPO,"main",A),leases,NOW,BranchSnapshot(REPO,"feat/x",B))
    assert a.decision=="PASS"

def test_merge_source_move_blocks():
    i=merge_intent(); leases=[lease(branch="main",head=A),lease(branch="feat/x",head=B)]
    a=evaluate_collision_gate(i,BranchSnapshot(REPO,"main",A),leases,NOW,BranchSnapshot(REPO,"feat/x",C))
    assert "SOURCE_HEAD_MOVED" in a.reasons

def test_merge_foreign_source_lease_blocks():
    i=merge_intent(); leases=[lease(branch="main",head=A),lease(branch="feat/x",head=B),lease("s2","feat/x",B)]
    a=evaluate_collision_gate(i,BranchSnapshot(REPO,"main",A),leases,NOW,BranchSnapshot(REPO,"feat/x",B))
    assert "FOREIGN_ACTIVE_SESSION:feat/x" in a.reasons

def test_merge_missing_source_lease_blocks():
    i=merge_intent(); leases=[lease(branch="main",head=A)]
    a=evaluate_collision_gate(i,BranchSnapshot(REPO,"main",A),leases,NOW,BranchSnapshot(REPO,"feat/x",B))
    assert "MISSING_ACTIVE_SOURCE_LEASE" in a.reasons

def test_admission_id_deterministic():
    args=(write_intent(), BranchSnapshot(REPO,"feat/x",A), [lease()], NOW)
    assert evaluate_collision_gate(*args).admission_id==evaluate_collision_gate(*args).admission_id

def test_revalidation_same_snapshot_passes():
    a=evaluate_collision_gate(write_intent(),BranchSnapshot(REPO,"feat/x",A),[lease()],NOW)
    b=revalidate_immediately_before_effect(a,BranchSnapshot(REPO,"feat/x",A),[lease()],NOW+1)
    assert b.decision=="PASS"

def test_revalidation_moved_head_fails():
    a=evaluate_collision_gate(write_intent(),BranchSnapshot(REPO,"feat/x",A),[lease()],NOW)
    with pytest.raises(BranchSessionCollisionError): revalidate_immediately_before_effect(a,BranchSnapshot(REPO,"feat/x",B),[lease()],NOW+1)

def test_revalidation_new_foreign_lease_fails():
    a=evaluate_collision_gate(write_intent(),BranchSnapshot(REPO,"feat/x",A),[lease()],NOW)
    with pytest.raises(BranchSessionCollisionError): revalidate_immediately_before_effect(a,BranchSnapshot(REPO,"feat/x",A),[lease(),lease("s2")],NOW+1)

def test_write_finalize_requires_exact_parent():
    a=evaluate_collision_gate(write_intent(),BranchSnapshot(REPO,"feat/x",A),[lease()],NOW)
    f=finalize_effect(a,new_target_snapshot=BranchSnapshot(REPO,"feat/x",C),commit_parent_shas=[A])
    assert f.verified

def test_write_finalize_rejects_wrong_parent():
    a=evaluate_collision_gate(write_intent(),BranchSnapshot(REPO,"feat/x",A),[lease()],NOW)
    with pytest.raises(BranchSessionCollisionError): finalize_effect(a,new_target_snapshot=BranchSnapshot(REPO,"feat/x",C),commit_parent_shas=[B])

def test_write_finalize_rejects_no_advance():
    a=evaluate_collision_gate(write_intent(),BranchSnapshot(REPO,"feat/x",A),[lease()],NOW)
    with pytest.raises(BranchSessionCollisionError): finalize_effect(a,new_target_snapshot=BranchSnapshot(REPO,"feat/x",A),commit_parent_shas=[A])

def test_merge_finalize_requires_both_admitted_parents():
    i=merge_intent(); leases=[lease(branch="main",head=A),lease(branch="feat/x",head=B)]
    a=evaluate_collision_gate(i,BranchSnapshot(REPO,"main",A),leases,NOW,BranchSnapshot(REPO,"feat/x",B))
    f=finalize_effect(a,new_target_snapshot=BranchSnapshot(REPO,"main",C),commit_parent_shas=[A,B])
    assert f.verified

def test_merge_finalize_rejects_missing_source_parent():
    i=merge_intent(); leases=[lease(branch="main",head=A),lease(branch="feat/x",head=B)]
    a=evaluate_collision_gate(i,BranchSnapshot(REPO,"main",A),leases,NOW,BranchSnapshot(REPO,"feat/x",B))
    with pytest.raises(BranchSessionCollisionError): finalize_effect(a,new_target_snapshot=BranchSnapshot(REPO,"main",C),commit_parent_shas=[A,D])

def test_second_write_requires_new_admission_after_head_changes():
    a=evaluate_collision_gate(write_intent(),BranchSnapshot(REPO,"feat/x",A),[lease()],NOW)
    finalize_effect(a,new_target_snapshot=BranchSnapshot(REPO,"feat/x",C),commit_parent_shas=[A])
    with pytest.raises(BranchSessionCollisionError): revalidate_immediately_before_effect(a,BranchSnapshot(REPO,"feat/x",C),[lease()],NOW+1)

def test_payload_declares_no_force_and_no_effect():
    a=evaluate_collision_gate(write_intent(),BranchSnapshot(REPO,"feat/x",A),[lease()],NOW)
    assert a.payload["force_allowed"] is False and a.payload["external_effects"] is False

def test_bad_git_sha_rejected():
    with pytest.raises(BranchSessionCollisionError): BranchSnapshot(REPO,"x","f"*39)

def test_bad_payload_sha_rejected():
    with pytest.raises(BranchSessionCollisionError): WriteIntent("WRITE","s1",REPO,"x",A,"0"*63)
