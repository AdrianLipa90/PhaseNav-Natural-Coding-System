# PNCS Branch / Session Collision Gate v0.28

Status: `IMPLEMENTED / PURE-CORE VALIDATED / FAIL-CLOSED / GIT-ADAPTER ENFORCEMENT REQUIRED`

## Purpose

Every repository write and merge must be admitted against an exact branch/session snapshot immediately before the external Git effect. A semantic program, ORCHORBITAL state, PhaseNav phase state, model confidence, semantic mass, route admission, or prior authorization never waives this gate.

The gate exists to prevent two sessions, agents, terminals, or user actions from silently writing to a branch whose head changed after planning began.

## Mandatory sequence

```text
read exact target/source refs
-> acquire/verify session lease(s)
-> build content-addressed WriteIntent
-> evaluate Branch/Session Collision Gate
-> immediately re-read refs + active leases
-> revalidate same admission
-> perform ONE non-force Git write/merge effect
-> verify new commit parents against admitted refs
-> emit FinalizeReceipt
```

For a normal branch write:

```text
new_commit.parent == admitted_target_head
```

For a merge:

```text
admitted_target_head in merge_commit.parents
admitted_source_head in merge_commit.parents
```

A second write requires a new intent and a new admission. An old admission cannot be replayed after the branch advances.

## Session lease rules

A lease binds session ID, repository, branch, the head observed at acquisition, a content-addressed nonce, and acquisition/expiry timestamps. An active lease from a different session on either the target branch or merge source branch blocks the operation. Expired foreign leases do not block. The calling session must hold an active lease for every branch it intends to mutate or merge from.

The lease itself is not execution authority. It is collision evidence only.

## Optimistic ref collision rules

The `WriteIntent` binds exact expected Git SHA-1 heads. Admission fails closed if either source or target moved. Immediately before the write, the adapter must re-read the refs and re-run the gate. The Git ref update must be non-force.

This gives two independent collision barriers:

1. active-session collision detection;
2. exact-ref optimistic concurrency detection.

## Closed boundaries

- `force push = false`;
- no hidden retry on a moved ref;
- no automatic rebase after a collision;
- no automatic merge after a collision;
- no stale-admission replay;
- no semantic-mass authorization;
- no ORCHORBITAL/time-law bypass;
- no static-state fallback for live session ownership;
- no write is considered complete until parent verification passes.

## Integration point

The collision gate sits after effect authorization but before any Git adapter invocation:

```text
EffectRequest
-> AuthorizationDecision
-> Branch/Session Collision Admission
-> bounded Git adapter
-> Git effect
-> Collision FinalizeReceipt
-> EffectReceipt
```

Git remains a separately authorized effect class. This gate does not itself open Git authority.

## Validation

Pure-core conformance: `25/25 PASS`.

The development run that motivated this gate observed a real branch-head collision before a planned write: the working ORCHORBITAL branch advanced from a previously observed head to a different head in another session. The planned write was aborted before mutation. This observation is evidence for the collision model; it is not used as a substitute for adapter-level tests.

## Remaining integration gate

Before release closure, every PhaseNav Git write/merge adapter must call this gate and prove:

1. ref read before admission;
2. lease acquisition/verification;
3. immediate pre-effect revalidation;
4. non-force ref update;
5. exact parent verification;
6. deterministic collision receipt on `BLOCKED`;
7. no write after any `BLOCKED` verdict.
