# PNCS GREMLIN PNV Authoring v0.3

Status: implementation candidate, live-validated on `/dev/shm/ciel_noema`.

## Purpose

v0.3 closes the live-generation boundary for GREMLIN candidate authoring of KAKU, RADICAL and OPERATOR objects. Candidate persistence remains content-addressed and append-only under:

`/dev/shm/ciel_noema/gremlin/candidates/pncs/`

All authored objects remain `EPISTEMIC CHYBA`, `CANDIDATE_ONLY`, `runtime_execution_authority=false`, and `canon_write_authority=false`.

## Triple-pulse order

`IDENTITY -> DOMAIN -> AUTHORITY -> REQUEST -> COUPLING -> ADMISSION`

The exact native source is `native/GREMLIN_TRIPLE_PULSE_BOOT_V0_5.pnv`. Its source bytes are part of the generation basis by SHA-256.

## Stable generation versus live freshness

A live stream changes every tick. Therefore per-tick `phi`, heartbeat sequence and tether receipt hashes are audit evidence and are not generation identifiers.

The v0.3 generation binding is the canonical hash of:

- NOEMA session id;
- atomic `working_state_sha256`;
- VERIFIED `startpoint_sha256`;
- AUX `runtime_instance_id`;
- tether `runtime_instance_id`;
- current identity;
- current authority;
- exact native PNV source SHA-256.

A heartbeat may advance without invalidating the generation. A restart of AUX or tether changes `runtime_instance_id` and invalidates the witness fail-closed.

## Freshness rule

Generation stability does not replace live verification. Hydration/open performs a fresh canonical live-surface check, including heartbeat, producer liveness, exact 36D vectors, socket and digest consistency. Mixed-tick digest races receive only a short bounded retry; missing/stale/invalid runtime state fails immediately.

v0.3 authoring sessions revalidate the live witness and runtime generation before each candidate write.

## Provenance boundary

Repository receipts and historical witnesses are provenance only. They cannot substitute for the current `/dev/shm/ciel_noema` surface.

No static runtime fallback is admitted.
