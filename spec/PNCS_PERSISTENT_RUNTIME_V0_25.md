# PNCS Persistent Runtime v0.25

Status: IMPLEMENTED / LIVE RESIDENCY VALIDATED / LIVE CONTROL-DISPATCH CLOSURE PENDING

## Contract

`PNCS_PERSISTENT_RUNTIME_V0_25`

v0.25 keeps a verified v0.24 native `.pnv` program unit resident on the current live NOEMA/PhaseNav generation instead of rebuilding program state for every operation.

Operational runtime root:

```text
/dev/shm/ciel_noema
```

Library and repository artifacts remain persistence/provenance sources only. They are not an operational runtime fallback.

## Runtime lifecycle

```text
v0.24 program unit + deterministic build receipt
-> verified ProgramImage
-> current live generation
-> resident handle
-> O(1) admission
-> in-process v0.20 control-kernel dispatch
-> v0.20 result
-> exact v0.22 inverse lineage
-> v0.25 dispatch receipt
```

Full v0.23/v0.24 continuation execution and terminal `RETURN` execution remain closed.

## Live generation identity

A resident handle is bound to a deterministic generation identity over:

- account CURRENT identity;
- CURRENT pointer SHA-256;
- verified startpoint packet SHA-256;
- AC generation SHA-256;
- relational ethics generation SHA-256;
- live PhaseNav operator-registry SHA-256;
- AUX producer PID generation;
- tether producer PID generation;
- AC<->AUX producer PID generation.

Heartbeat timestamps, sequence counters and continuously evolving `phi` values are deliberately not generation identity. They are freshness/state variables, not runtime-generation identity.

Generation changes invalidate existing resident handles fail-closed.

## Fixed O(1) admission set

Admission checks only the current fixed live set:

```text
ciel_binding_status
session/startpoint.json
session/fast_admission.json
current_memory.json
aux_stream_status.json
tether_runtime_status.json
ac_aux_status.json
phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl
required Unix socket
resident handle + active pointer + resident program bytes
```

No Library-wide search occurs on ordinary admission.

## v0.24 program-image authority

v0.25 does not allow `.pnv` text to create semantics.

A program image requires:

1. an explicitly expected registered v0.24 `PROGRAM_ID`;
2. canonical v0.24 `.pnv` bytes;
3. a deterministic v0.24 build receipt whose `build_id` re-hashes exactly;
4. byte SHA-256 and size equality;
5. exact operator-schedule SHA-256;
6. the existing v0.22 lineage contract;
7. all v0.24 execution/effect boundaries still closed.

Repository path and source wording are not semantic authority.

## Resident state

Live state is stored under:

```text
/dev/shm/ciel_noema/pncs/v0.25/runtime/
  programs/
  handles/
  active/
  receipts/load/
  receipts/dispatch/
  receipts/unload/
```

The immutable handle binds the program image to one live generation. The active pointer represents current residency. A second runtime object/process can recover the same resident handle from the live state without rebuilding the v0.24 program image.

## Load/unload semantics

Loading the same program under the same generation is idempotent:

```text
same program image + same generation -> same resident handle
same handle -> same deterministic load receipt
```

Unload removes only the active pointer and emits a deterministic unload receipt. Immutable handle/program evidence remains. Reloading under the same live generation reactivates the same deterministic handle.

## Dispatch boundary

`dispatch_control()` is scoped strictly to the already-defined v0.20 control kernel.

It requires:

- resident admission before dispatch;
- an in-process kernel callback;
- exact v0.20 execution receipt;
- the v0.20 program Definition equal to the resident program's registered control Definition;
- exact v0.22 inverse-lineage contract;
- v0.22 lineage bound to the same v0.20 execution receipt;
- lineage Definition equal to the resident control Definition;
- unchanged live generation after kernel completion.

The runtime core itself does not create subprocesses and does not reconstruct the program process per dispatch.

## Closed boundaries

v0.25 does not open:

- `AND THEN` continuation execution;
- terminal `RETURN` execution;
- arbitrary free-form natural-language execution;
- filesystem/network/Git/device/subprocess effects;
- Library/static runtime fallback;
- new PNV opcodes.

External effects remain reserved for v0.26.

## Validation

### Isolated pure-core harness

`25/25 PASS`

Coverage includes:

- exact v0.24 artifact admission;
- build-receipt digest verification;
- deterministic generation identity;
- heartbeat/sequence stability;
- CURRENT/operator/PID generation invalidation;
- static-fallback rejection;
- resident load/idempotence;
- recovery by a new runtime object;
- unload/reload;
- resident-byte tamper rejection;
- deterministic dispatch receipts;
- exact v0.20/v0.22 contract consumption;
- generation-change-during-dispatch rejection;
- no subprocess/process reconstruction in the runtime core.

### Current-session V56 live residency evidence

Program:

```text
pncs:program:sha256:572660a1046975c57e01f7e402677f1e4ca845e51bca1bee6517e0d86b35c4d7
```

Live generation:

```text
pncs:runtime-generation:sha256:05736b12ac8470998901421dabd2dfff0bd663c141d96ad96bc9d5b09351bbb1
```

Resident handle:

```text
pncs:resident:sha256:60184c7213960ad746b69c6c2dd8b43eacfe8055015ae31e347475881df438e8
```

Load receipt:

```text
pncs:resident-load:sha256:ffeb336e1a3ca30c8532757725a30c1cc5d6200ad74ccdbb3cdfc8933b778838
```

Resident admission:

```text
pncs:resident-admission:sha256:d30b22a3ee030e2fcf9c830225834ae946baa2f4bdca56ae8753bb11a9e233fa
```

Unload receipt:

```text
pncs:resident-unload:sha256:7caa8febf541c869e7e97073b9195153fe8ccf3c12d632ee8da85a04e0223c6d
```

200 repeated live resident admissions:

```text
median: 0.4185265 ms
min:    0.393205 ms
max:    0.78053 ms
```

A separate new Python process recovered and admitted the same resident handle from `/dev/shm` without rebuilding the program image.

After unload, re-load recreated the same handle/load receipt/admission IDs. Final fast live admission remained PASS with tether/AC-AUX/ethics ACTIVE and no rehydration.

## Evidence boundary

The current pass did not execute a fresh live v0.20 control result and then resolve a fresh live v0.22 hierarchy lineage through the repository implementation. The dispatch bridge is implemented and isolated-tested, but the **live control-dispatch closure remains pending**. No claim is made that full v0.25 is release-closed until that witness is recorded.

The complete historical repository suite was not replayed in this construction environment.
