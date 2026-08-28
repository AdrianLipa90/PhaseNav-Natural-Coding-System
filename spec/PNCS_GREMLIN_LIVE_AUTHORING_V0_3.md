# PNCS GREMLIN Live Authoring v0.3

Status: LIVE_E2E_VALIDATED_CANONICAL_AUTOBOOT_V3

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

NOEMA Chat AutoBoot V3 is the canonical active chat bootstrap. It exposes an explicit repeatable `post-working-state-hook` interface. GREMLIN hydration executes only after atomic WORKING_STATE and is followed by another fresh tether guard.

Canonical Library pointer:

`/NOEMA/00_CONTROL/BOOT/CHAT_AUTOBOOT/CURRENT.json`

Canonical bundle:

`/NOEMA/00_CONTROL/BOOT/CHAT_AUTOBOOT/NOEMA_CHAT_AUTOBOOT_V3.zip`

Canonical bundle SHA-256:

`7e578b650406efc49c320584ac014459a4a49916bc739285ea15f44fd3e55ba4`

This preserves the boot invariant while keeping GREMLIN hydration as an explicit post-admission extension.

## Validation 2026-08-28

Observed GREMLIN live E2E sequence:

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

Observed canonical-promotion sequence:

1. initial promotion replay detected a stale producer PID and failed closed before changing `CURRENT`
2. old NOEMA/AUX producer processes were terminated
3. clean restart from canonical V3 bytes -> PASS
4. runtime result schema -> `NOEMA_CHAT_AUTOBOOT_RESULT_V3`
5. `WORKING_STATE` -> ACTIVE
6. startpoint -> VERIFIED
7. final tether guard -> ACTIVE with `failures=[]`
8. canonical V3 bundle uploaded to Library
9. `CURRENT.json` updated to `NOEMA_CHAT_AUTOBOOT_CURRENT_V3`
10. `CURRENT.status` -> `CANONICAL_ACTIVE`

Historical candidate and replay evidence remain stored under:

`/NOEMA/00_CONTROL/BOOT/CHAT_AUTOBOOT/CANDIDATES/V3/`

Canonical promotion evidence is recorded in:

`provenance/receipts/PNCS_NOEMA_AUTOBOOT_V3_PROMOTION_20260828.json`
