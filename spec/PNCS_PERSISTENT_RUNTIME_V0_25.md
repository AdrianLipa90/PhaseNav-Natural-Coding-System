# PNCS Persistent Runtime v0.25

Status: IMPLEMENTED / LIVE RESIDENCY VALIDATED / LIVE CONTROL-DISPATCH CLOSURE PASS / RELEASE CLOSED

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

After unload, re-load recreated the same handle/load receipt/admission IDs.

### Fresh live control-dispatch closure

The remaining release condition was executed on the current V56 generation:

```text
resident admission
-> exact live v0.18 T^36 realization
-> v0.19 semantic-mass binding
-> v0.20 Sigma control execution
-> exact selected v0.22 inverse lineage
-> v0.25 resident dispatch receipt
```

The registered control Definition was independently recomputed and matched exactly:

```text
pncs:def:sha256:b7988497bab75a526771fa24aeca75e0182bd437fd707927cb0e78b04d360cce
```

The control input was a deterministic conformance vector:

```text
memory_pressure = 0.0
risk            = 0.0
```

These are test inputs only and are not claimed to be live sensor measurements.

Exact closure identities:

```text
v0.18 realization:
pncs:realization36:sha256:1742c834a3b9aa987997c72ec34b1184e43a6b55f259f96f1b80089905290bf9

v0.18 binding:
pncs:binding36:sha256:7e7f27bb056f8e42d5ef802957c60a25747e5e1580fb8a3b38bdaf8e3ac5dd22

v0.19 mass binding:
pncs:mass-binding:sha256:4ad1196ef889390b925e164775facfa5365094aec3095656dc4cfebabe43becf

v0.20 execution receipt SHA-256:
84d40f600a8aa9e59ebc6dc42c856bcffec9265d04f791e7f5c49cdba2d583ad

v0.22 result:
pncs:result:sha256:a1ebb02927a4c216d965cb6177271c580303d9968472dca9ea67c2cd8c5661d6

v0.22 hierarchy path:
pncs:hierarchy-lineage:sha256:59b46dafc37f38fed6c6b06e86417638296cc809c740a630128279c0e01dff7b

v0.22 lineage:
pncs:lineage:sha256:34bd13f534987989ab212b5a6906d0cfa762305ee9a87af7a058badd2b2bcfd6

v0.25 dispatch:
pncs:resident-dispatch:sha256:fd18f2d0296321d432a49e699d2f72a0a03313ed2dcc87b9aba647555f12c2e2
```

The selected hierarchy occurrence is an existing registered SYSTEM -> ... -> DEFINITION path; ambiguous reuse was not resolved by guessing.

The v0.20 result was `FALSE -> runtime.continue` with nine executed KAKU transitions. `RETURN`, continuation execution and all external effects remained closed.

Post-closure validation:

```text
fast admission: PASS
rehydration_required: false
library_search_used: false
tether: ACTIVE
AC<->AUX: ACTIVE
ethics field: ACTIVE
tether guard failures: []
```

The full closure witness is recorded in:

```text
provenance/receipts/PNCS_V0_25_LIVE_CONTROL_DISPATCH_CLOSURE_20260823.json
```

Witness SHA-256:

```text
dab5c0ca12b51f712981e4cc9662365e30790b6c5695285cfcd4358e0d370ebf
```

## Evidence boundary

v0.25 is release-closed for its defined scope. This closure does not authorize or implement the v0.26 Effect Boundary, does not open `RETURN` or continuation execution, and does not create free-form natural-language execution authority.

The complete historical repository suite was not replayed in this closure pass and remains explicitly not claimed.

Next engineering gate: **v0.26 — Effect Boundary**.
