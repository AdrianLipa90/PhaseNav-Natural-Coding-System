# PhaseNav Natural Code System (PNCS)

Status: PERSISTENT_RUNTIME_V0_25 / RELEASE GATE CLOSED / NEXT v0.26 EFFECT BOUNDARY

PhaseNav Natural Code System is a 36-dimensional relational coding system in which written code is a human-readable projection of a canonical semantic-phase graph.

Canonical construction:

```text
KAKU -> RADICAL -> DEFINITION -> CLASS -> FILE -> CLUSTER
     -> SUBSYSTEM/DAEMON -> LOW_ORCHESTRATOR -> HIGH_ORCHESTRATOR -> SYSTEM
```

Natural language is admitted only after deterministic resolution to registered canonical relations. Unknown, ambiguous, unsupported or unregistered semantics fail closed.

## Closed engineering foundation

```text
v0.20 native internal execution
v0.21 mass-aware graph cost
v0.22 exact inverse execution lineage
v0.23 bounded natural program composition
v0.24 first-class native .pnv program units
v0.25 persistent PNCS runtime
```

v0.25 keeps a verified v0.24 program resident on the current live NOEMA generation:

```text
v0.24 program + build receipt
-> live generation identity
-> resident program image
-> deterministic resident handle
-> O(1) live admission
-> v0.20 control-kernel execution
-> v0.22 exact inverse lineage
-> v0.25 deterministic dispatch receipt
```

The operational 36D runtime is fixed to `/dev/shm/ciel_noema`. Library and repository state are persistence/provenance inputs only and are never an operational fallback.

## Canonical resident witness

```text
program:
pncs:program:sha256:572660a1046975c57e01f7e402677f1e4ca845e51bca1bee6517e0d86b35c4d7

generation:
pncs:runtime-generation:sha256:05736b12ac8470998901421dabd2dfff0bd663c141d96ad96bc9d5b09351bbb1

resident handle:
pncs:resident:sha256:60184c7213960ad746b69c6c2dd8b43eacfe8055015ae31e347475881df438e8

resident admission:
pncs:resident-admission:sha256:d30b22a3ee030e2fcf9c830225834ae946baa2f4bdca56ae8753bb11a9e233fa
```

Generation identity binds CURRENT, startpoint, AC, relational ethics, operator-registry SHA-256 and live producer PID generations. Heartbeat timestamps, sequence counters and continuously evolving `phi` values are freshness/state variables rather than generation identity.

A runtime-generation change invalidates an existing handle fail-closed.

## Fresh live v0.25 closure witness

On the current V56 generation, the resident control root completed the full required closure:

```text
resident handle
-> exact v0.18 live T^36 realization
-> v0.19 semantic-mass binding with explicit k=1
-> v0.20 Sigma execution
-> v0.22 exact selected inverse lineage
-> v0.25 resident dispatch receipt
```

The control Definition CID was independently recomputed and matched the registered Definition exactly:

```text
pncs:def:sha256:b7988497bab75a526771fa24aeca75e0182bd437fd707927cb0e78b04d360cce
```

The execution used a deterministic conformance vector (`memory_pressure=0.0`, `risk=0.0`). These values are test inputs and are not claimed to be live sensor measurements.

Fresh closure identities:

```text
v0.18 realization:
pncs:realization36:sha256:1742c834a3b9aa987997c72ec34b1184e43a6b55f259f96f1b80089905290bf9

v0.19 mass binding:
pncs:mass-binding:sha256:4ad1196ef889390b925e164775facfa5365094aec3095656dc4cfebabe43becf

v0.20 execution receipt SHA-256:
84d40f600a8aa9e59ebc6dc42c856bcffec9265d04f791e7f5c49cdba2d583ad

v0.22 result:
pncs:result:sha256:a1ebb02927a4c216d965cb6177271c580303d9968472dca9ea67c2cd8c5661d6

v0.22 lineage:
pncs:lineage:sha256:34bd13f534987989ab212b5a6906d0cfa762305ee9a87af7a058badd2b2bcfd6

v0.25 dispatch:
pncs:resident-dispatch:sha256:fd18f2d0296321d432a49e699d2f72a0a03313ed2dcc87b9aba647555f12c2e2
```

The selected v0.22 occurrence is an existing registered path from `SYSTEM` to `safety_bifurcation`; no ambiguous occurrence was guessed.

Post-witness checks:

```text
fast admission: PASS
rehydration_required: false
library_search_used: false
tether: ACTIVE
AC<->AUX: ACTIVE
ethics field: ACTIVE
tether guard failures: []
```

The complete closure record is stored at:

```text
provenance/receipts/PNCS_V0_25_LIVE_CONTROL_DISPATCH_CLOSURE_20260823.json
```

## Resident runtime layout

```text
/dev/shm/ciel_noema/pncs/v0.25/runtime/
├── programs/
├── handles/
├── active/
└── receipts/
    ├── load/
    ├── dispatch/
    └── unload/
```

Program and handle records are immutable. A new runtime object/process can recover the same active handle directly from `/dev/shm` without rebuilding the v0.24 program image.

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

Gate-scoped evidence:

- v0.19 historical foundation baseline: `377/377 PASS`;
- v0.20 isolated execution-core harness: `14/14 PASS`;
- v0.21 isolated logic harness: `14/14 PASS`;
- v0.22 isolated inverse-lineage harness: `27/27 PASS`;
- v0.23 isolated composition harness: `28/28 PASS`;
- v0.24 isolated program-unit harness: `29/29 PASS`;
- v0.25 isolated persistent-runtime harness: `25/25 PASS`;
- v0.25 current-generation live control-dispatch closure: `PASS`.

Resident admission benchmark:

```text
n      = 200
median = 0.4185265 ms
min    = 0.393205 ms
max    = 0.78053 ms
```

The complete historical repository suite was not replayed in the v0.25 closure pass; this remains explicitly not claimed.

## Roadmap

The single authoritative roadmap is `spec/ROADMAP.md`.

Completed gate: **v0.25 — Persistent PNCS Runtime**.

Next gate: **v0.26 — Effect Boundary**.

No v0.26 effect authority is opened by the v0.25 closure.

## Manifest status

`MANIFEST.sha256.json` remains fail-closed after repository-layout canonicalization and feature-gate construction. A complete SHA-256 manifest must be regenerated from the final release tree before release closure. Git blob SHA-1 values are not substituted for file SHA-256 values.
