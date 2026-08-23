from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Literal, Mapping, Sequence

COLLISION_GATE_ID = "PNCS_BRANCH_SESSION_COLLISION_GATE_V0_28"
LEASE_SCHEMA = "PNCS_BRANCH_SESSION_LEASE_V0_28"
INTENT_SCHEMA = "PNCS_BRANCH_WRITE_INTENT_V0_28"
ADMISSION_SCHEMA = "PNCS_BRANCH_SESSION_COLLISION_ADMISSION_V0_28"
FINALIZE_SCHEMA = "PNCS_BRANCH_SESSION_COLLISION_FINALIZE_V0_28"

Operation = Literal["WRITE", "MERGE"]


class BranchSessionCollisionError(ValueError):
    pass


def _canonical(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(k): _canonical(value[k]) for k in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_canonical(x) for x in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise BranchSessionCollisionError("non-finite canonical value")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise BranchSessionCollisionError(f"unsupported canonical type: {type(value).__name__}")


def _sha256_json(value: object) -> str:
    raw = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _typed_id(prefix: str, value: object) -> str:
    return f"{prefix}:sha256:{_sha256_json(value)}"


def _git_sha(value: str, label: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise BranchSessionCollisionError(f"{label} must be lowercase Git SHA-1")
    return value


def _sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise BranchSessionCollisionError(f"{label} must be lowercase SHA-256")
    return value


def _name(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BranchSessionCollisionError(f"{label} required")
    return value.strip()


@dataclass(frozen=True)
class BranchSnapshot:
    repository: str
    branch: str
    head_sha: str

    def __post_init__(self) -> None:
        _name(self.repository, "repository")
        _name(self.branch, "branch")
        _git_sha(self.head_sha, "head_sha")

    @property
    def payload(self) -> dict[str, object]:
        return {"repository": self.repository, "branch": self.branch, "head_sha": self.head_sha}

    @property
    def snapshot_id(self) -> str:
        return _typed_id("pncs:branch-snapshot", self.payload)


@dataclass(frozen=True)
class SessionLease:
    session_id: str
    repository: str
    branch: str
    acquired_head_sha: str
    nonce_sha256: str
    acquired_unix_ns: int
    expires_unix_ns: int

    def __post_init__(self) -> None:
        _name(self.session_id, "session_id")
        _name(self.repository, "repository")
        _name(self.branch, "branch")
        _git_sha(self.acquired_head_sha, "acquired_head_sha")
        _sha256(self.nonce_sha256, "nonce_sha256")
        if isinstance(self.acquired_unix_ns, bool) or not isinstance(self.acquired_unix_ns, int) or self.acquired_unix_ns < 0:
            raise BranchSessionCollisionError("acquired_unix_ns must be non-negative integer")
        if isinstance(self.expires_unix_ns, bool) or not isinstance(self.expires_unix_ns, int) or self.expires_unix_ns <= self.acquired_unix_ns:
            raise BranchSessionCollisionError("expires_unix_ns must be > acquired_unix_ns")

    @property
    def payload(self) -> dict[str, object]:
        return {"schema": LEASE_SCHEMA, "gate_id": COLLISION_GATE_ID, "session_id": self.session_id, "repository": self.repository, "branch": self.branch, "acquired_head_sha": self.acquired_head_sha, "nonce_sha256": self.nonce_sha256, "acquired_unix_ns": self.acquired_unix_ns, "expires_unix_ns": self.expires_unix_ns, "execution_authority": False}

    @property
    def lease_id(self) -> str:
        return _typed_id("pncs:branch-session-lease", self.payload)

    def active_at(self, now_unix_ns: int) -> bool:
        return self.acquired_unix_ns <= now_unix_ns < self.expires_unix_ns


@dataclass(frozen=True)
class WriteIntent:
    operation: Operation
    session_id: str
    repository: str
    target_branch: str
    expected_target_head_sha: str
    payload_sha256: str
    source_branch: str | None = None
    expected_source_head_sha: str | None = None

    def __post_init__(self) -> None:
        if self.operation not in ("WRITE", "MERGE"):
            raise BranchSessionCollisionError("operation must be WRITE or MERGE")
        _name(self.session_id, "session_id"); _name(self.repository, "repository"); _name(self.target_branch, "target_branch")
        _git_sha(self.expected_target_head_sha, "expected_target_head_sha"); _sha256(self.payload_sha256, "payload_sha256")
        if self.operation == "WRITE":
            if self.source_branch is not None or self.expected_source_head_sha is not None:
                raise BranchSessionCollisionError("WRITE cannot declare merge source")
        else:
            _name(self.source_branch or "", "source_branch"); _git_sha(self.expected_source_head_sha or "", "expected_source_head_sha")
            if self.source_branch == self.target_branch:
                raise BranchSessionCollisionError("merge source and target must differ")

    @property
    def payload(self) -> dict[str, object]:
        return {"schema": INTENT_SCHEMA, "gate_id": COLLISION_GATE_ID, "operation": self.operation, "session_id": self.session_id, "repository": self.repository, "target_branch": self.target_branch, "expected_target_head_sha": self.expected_target_head_sha, "source_branch": self.source_branch, "expected_source_head_sha": self.expected_source_head_sha, "payload_sha256": self.payload_sha256, "force_allowed": False}

    @property
    def intent_id(self) -> str:
        return _typed_id("pncs:branch-write-intent", self.payload)


@dataclass(frozen=True)
class CollisionAdmission:
    intent: WriteIntent
    target_snapshot: BranchSnapshot
    source_snapshot: BranchSnapshot | None
    lease_ids: tuple[str, ...]
    observed_unix_ns: int
    decision: Literal["PASS", "BLOCKED"]
    reasons: tuple[str, ...]

    @property
    def payload(self) -> dict[str, object]:
        return {"schema": ADMISSION_SCHEMA, "gate_id": COLLISION_GATE_ID, "intent_id": self.intent.intent_id, "target_snapshot_id": self.target_snapshot.snapshot_id, "source_snapshot_id": self.source_snapshot.snapshot_id if self.source_snapshot else None, "lease_ids": list(self.lease_ids), "observed_unix_ns": self.observed_unix_ns, "decision": self.decision, "reasons": list(self.reasons), "force_allowed": False, "write_or_merge_performed": False, "external_effects": False}

    @property
    def admission_id(self) -> str:
        return _typed_id("pncs:branch-collision-admission", self.payload)

    def require_pass(self) -> None:
        if self.decision != "PASS":
            raise BranchSessionCollisionError("collision admission BLOCKED: " + ",".join(self.reasons))


@dataclass(frozen=True)
class FinalizeReceipt:
    admission_id: str
    operation: Operation
    old_target_head_sha: str
    new_target_head_sha: str
    commit_parent_shas: tuple[str, ...]
    verified: bool

    @property
    def payload(self) -> dict[str, object]:
        return {"schema": FINALIZE_SCHEMA, "gate_id": COLLISION_GATE_ID, "admission_id": self.admission_id, "operation": self.operation, "old_target_head_sha": self.old_target_head_sha, "new_target_head_sha": self.new_target_head_sha, "commit_parent_shas": list(self.commit_parent_shas), "verified": self.verified, "force_used": False}

    @property
    def finalize_id(self) -> str:
        return _typed_id("pncs:branch-collision-finalize", self.payload)


def _active_collisions(*, intent: WriteIntent, leases: Sequence[SessionLease], now_unix_ns: int, branches: set[str]) -> tuple[list[str], list[str]]:
    active_ids: list[str] = []; reasons: list[str] = []; own_target = False; own_source = intent.operation == "WRITE"
    for lease in leases:
        if lease.repository != intent.repository or lease.branch not in branches or not lease.active_at(now_unix_ns):
            continue
        active_ids.append(lease.lease_id)
        if lease.session_id != intent.session_id:
            reasons.append(f"FOREIGN_ACTIVE_SESSION:{lease.branch}"); continue
        if lease.branch == intent.target_branch:
            own_target = True
            if lease.acquired_head_sha != intent.expected_target_head_sha: reasons.append("OWN_TARGET_LEASE_STALE")
        if intent.operation == "MERGE" and lease.branch == intent.source_branch:
            own_source = True
            if lease.acquired_head_sha != intent.expected_source_head_sha: reasons.append("OWN_SOURCE_LEASE_STALE")
    if not own_target: reasons.append("MISSING_ACTIVE_TARGET_LEASE")
    if not own_source: reasons.append("MISSING_ACTIVE_SOURCE_LEASE")
    return active_ids, reasons


def evaluate_collision_gate(intent: WriteIntent, target_snapshot: BranchSnapshot, leases: Sequence[SessionLease], now_unix_ns: int, source_snapshot: BranchSnapshot | None = None) -> CollisionAdmission:
    if isinstance(now_unix_ns, bool) or not isinstance(now_unix_ns, int) or now_unix_ns < 0:
        raise BranchSessionCollisionError("now_unix_ns must be non-negative integer")
    reasons: list[str] = []
    if target_snapshot.repository != intent.repository or target_snapshot.branch != intent.target_branch: reasons.append("TARGET_SNAPSHOT_IDENTITY_MISMATCH")
    if target_snapshot.head_sha != intent.expected_target_head_sha: reasons.append("TARGET_HEAD_MOVED")
    branches = {intent.target_branch}
    if intent.operation == "MERGE":
        branches.add(intent.source_branch or "")
        if source_snapshot is None: reasons.append("MISSING_SOURCE_SNAPSHOT")
        else:
            if source_snapshot.repository != intent.repository or source_snapshot.branch != intent.source_branch: reasons.append("SOURCE_SNAPSHOT_IDENTITY_MISMATCH")
            if source_snapshot.head_sha != intent.expected_source_head_sha: reasons.append("SOURCE_HEAD_MOVED")
    elif source_snapshot is not None: reasons.append("WRITE_HAS_UNEXPECTED_SOURCE_SNAPSHOT")
    lease_ids, lease_reasons = _active_collisions(intent=intent, leases=leases, now_unix_ns=now_unix_ns, branches=branches)
    reasons.extend(lease_reasons); reasons = sorted(set(reasons))
    return CollisionAdmission(intent, target_snapshot, source_snapshot, tuple(sorted(lease_ids)), now_unix_ns, "PASS" if not reasons else "BLOCKED", tuple(reasons))


def revalidate_immediately_before_effect(admission: CollisionAdmission, target_snapshot: BranchSnapshot, leases: Sequence[SessionLease], now_unix_ns: int, source_snapshot: BranchSnapshot | None = None) -> CollisionAdmission:
    admission.require_pass(); fresh = evaluate_collision_gate(admission.intent, target_snapshot, leases, now_unix_ns, source_snapshot)
    if fresh.target_snapshot.snapshot_id != admission.target_snapshot.snapshot_id: raise BranchSessionCollisionError("target snapshot changed after admission")
    if (fresh.source_snapshot.snapshot_id if fresh.source_snapshot else None) != (admission.source_snapshot.snapshot_id if admission.source_snapshot else None): raise BranchSessionCollisionError("source snapshot changed after admission")
    if fresh.decision != "PASS": raise BranchSessionCollisionError("collision appeared after admission: " + ",".join(fresh.reasons))
    return fresh


def finalize_effect(admission: CollisionAdmission, *, new_target_snapshot: BranchSnapshot, commit_parent_shas: Sequence[str]) -> FinalizeReceipt:
    admission.require_pass()
    if new_target_snapshot.repository != admission.intent.repository or new_target_snapshot.branch != admission.intent.target_branch: raise BranchSessionCollisionError("post-write target identity mismatch")
    if new_target_snapshot.head_sha == admission.target_snapshot.head_sha: raise BranchSessionCollisionError("target head did not advance")
    parents = tuple(_git_sha(x, "commit_parent_sha") for x in commit_parent_shas)
    if admission.intent.operation == "WRITE":
        if parents != (admission.target_snapshot.head_sha,): raise BranchSessionCollisionError("write commit parent must equal admitted target head exactly")
    else:
        if admission.source_snapshot is None: raise BranchSessionCollisionError("merge admission missing source snapshot")
        expected = {admission.target_snapshot.head_sha, admission.source_snapshot.head_sha}
        if len(parents) < 2 or not expected.issubset(set(parents)): raise BranchSessionCollisionError("merge commit parents must include admitted target and source heads")
    return FinalizeReceipt(admission.admission_id, admission.intent.operation, admission.target_snapshot.head_sha, new_target_snapshot.head_sha, parents, True)
