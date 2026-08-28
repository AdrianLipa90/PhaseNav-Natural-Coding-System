# PNCS GREMLIN Live Authoring v0.3

Status: CANDIDATE_IMPLEMENTATION_LIVE_E2E_VALIDATED

## Purpose

GREMLIN may generate bounded PNCS authoring candidates for `KAKU`, `RADICAL`, and `OPERATOR` objects on the canonical live NOEMA surface:

`/dev/shm/ciel_noema`

The authoring path is content-addressed, append-only per candidate digest, generation-bound, and fail-closed.

## Boot and admission order

The admitted path is:

`NOEMA bootstrap -> fresh tether guard -> atomic WORKING_STATE -> GREMLIN triple pulse -> candidate authoring`

GREMLIN triple pulse preserves the ordered contract:

`IDENTITY -> DOMAIN -> AUTHORITY -> REQUEST -> COUPLING -> ADMISSION`

All three pulse receipts bind one generation.

## Stable generation basis

`generation_binding` is SHA-256 over the canonical generation basis:

- NOEMA `session_id`
- `working_state_sha256`
- VERIFIED `startpoint_sha256`
- AUX `runtime_instance_id`
- tether `runtime_instance_id`
- current identity
- current authority
- exact native triple-pulse PNV source SHA-256

Heartbeat timestamps, phase samples, and per-tick tether receipts remain freshness/audit evidence. Runtime instance identity determines generation continuity.

A producer restart changes its runtime instance identifier and invalidates the admitted generation.

## Freshness

Every live admission loads the current live surface and verifies:

- `ciel_binding_status == ACTIVE`
- exact finite 36D `phi`, `aux_phi`, and `aux_feedback_phi`
- fresh AUX and tether heartbeats
- current producer PIDs
- stable AUX/tether runtime instance identifiers during the snapshot
- VERIFIED session startpoint
- atomic working-state content hash
- required Unix socket
- current PhaseNav operator registry

Transient vector/status races receive a small bounded retry window. All other failures close the path immediately.

## Witness

Canonical live witness path:

`/dev/shm/ciel_noema/gremlin/state/triple_pulse_conformance_witness.json`

The witness contains:

- exact generation basis and binding
- ordered IDENTITY / DOMAIN / AUTHORITY pulse receipts
- native PNV source SHA-256
- native execution receipt SHA-256
- admission tether receipt SHA-256
- live-surface receipt payload
- session and working-state bindings

Witness authority fields are fixed to:

- `promotion_state = CANDIDATE_ONLY`
- `runtime_execution_authority = false`
- `canon_write_authority = false`
- `static_runtime_fallback = false`

## Candidate store

Canonical authoring root:

`/dev/shm/ciel_noema/gremlin/candidates/pncs/`

Candidate kinds:

- `kaku/`
- `radical/`
- `operator/`
- `compilation/`

Each candidate identifier terminates in the SHA-256 of its canonical candidate envelope. Existing bytes at the same content address must match exactly; otherwise the write fails closed.

## Per-write revalidation

`GremlinPNVAuthoringSessionV03` revalidates the admitted live generation before every `KAKU`, `RADICAL`, or `OPERATOR` write.

Relational-isomorphism compilation performs generation verification before compilation and again before persisting its compilation receipt. If runtime generation changes during compilation, previously written objects remain candidate evidence and the compilation receipt is withheld.

## AutoBoot integration

NOEMA Chat AutoBoot V3 candidate exposes an explicit repeatable `post-working-state-hook` interface. The GREMLIN hook executes only after atomic WORKING_STATE and is followed by another fresh tether guard.

This preserves the boot invariant while keeping GREMLIN hydration as an explicit post-admission extension.

## Validation 2026-08-28

Observed live E2E sequence:

1. fresh AutoBoot V3 candidate -> PASS
2. tether guard -> ACTIVE
3. GREMLIN triple-pulse hydration -> PASS_CONFORMANCE_ONLY
4. live KAKU write -> PASS
5. live RADICAL write -> PASS
6. live OPERATOR writes -> PASS
7. repeated KAKU content address -> IDEMPOTENT
8. deliberately corrupted generation binding -> BLOCKED
9. fresh live rehydration -> PASS
10. final tether guard -> ACTIVE
11. exact ZIP replay of AutoBoot V3 candidate with GREMLIN post hook -> PASS

The exact AutoBoot V3 candidate and replay receipt are stored in NOEMA Library under:

`/NOEMA/00_CONTROL/BOOT/CHAT_AUTOBOOT/CANDIDATES/V3/`
