# PhaseNav Natural Code System (PNCS)

Status: PERSISTENT_RUNTIME_V0_25 / LIVE RESIDENCY PASS / LIVE CONTROL-DISPATCH CLOSURE PENDING

PhaseNav Natural Code System is a 36-dimensional relational coding system in which written code is a human-readable projection of a canonical semantic-phase graph.

Canonical construction:

```text
KAKU -> RADICAL -> DEFINITION -> CLASS -> FILE -> CLUSTER
     -> SUBSYSTEM/DAEMON -> LOW_ORCHESTRATOR -> HIGH_ORCHESTRATOR -> SYSTEM
```

Natural language is admitted only after deterministic resolution to registered canonical relations. Unknown, ambiguous, unsupported or unregistered semantics fail closed.

## Engineering state

The current closed foundation is:

```text
v0.20 native internal execution
v0.21 mass-aware graph cost
v0.22 exact inverse execution lineage
v0.23 bounded natural program composition
v0.24 first-class native .pnv program units
```

v0.25 adds a persistent runtime layer over v0.24 program units:

```text
v0.24 program + build receipt
-> live generation identity
-> resident program image
-> deterministic resident handle
-> O(1) live admission
-> in-process v0.20 control-kernel dispatch
-> v0.22 inverse lineage
-> v0.25 dispatch receipt
```

The operational 36D runtime remains `/dev/shm/ciel_noema`. Library and repository state are persistence/provenance inputs only and are never an operational fallback.

## v0.25 generation-bound residency

A handle is content-addressed from the program image plus the current live runtime generation. Generation identity binds CURRENT, startpoint, AC, relational ethics, operator-registry SHA-256 and live producer PID generations. Heartbeat timestamps, sequence counters and continuously evolving `phi` values are freshness/state variables, not generation identity.

A runtime-generation change invalidates an existing handle fail-closed.

Canonical live witness:

```text
program:
pncs:program:sha256:572660a1046975c57e01f7e402677f1e4ca845e51bca1bee6517e0d86b35c4d7

generation:
pncs:runtime-generation:sha256:05736b12ac8470998901421dabd2dfff0bd663c141d96ad96bc9d5b09351bbb1

resident handle:
pncs:resident:sha256:60184c7213960ad746b69c6c2dd8b43eacfe8055015ae31e347475881df438e8

load receipt:
pncs:resident-load:sha256:ffeb336e1a3ca30c8532757725a30c1cc5d6200ad74ccdbb3cdfc8933b778838

resident admission:
pncs:resident-admission:sha256:d30b22a3ee030e2fcf9c830225834ae946baa2f4bdca56ae8753bb11a9e233fa
```

Unload/reload under the same generation reproduces the same handle and load/admission identities.

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

The program and handle records are immutable. The active pointer represents current residency. A new runtime object/process can recover the same active handle directly from `/dev/shm` without rebuilding the v0.24 program image.

## Dispatch scope

v0.25 dispatch is deliberately limited to the already-defined **v0.20 control root**. It requires an exact v0.20 execution receipt and exact v0.22 inverse lineage bound to the same control Definition.

v0.25 does **not** invent execution semantics for v0.23/v0.24 `AND THEN` continuations or terminal `RETURN`.

Still closed:

- continuation execution;
- terminal `RETURN` execution;
- arbitrary free-form natural-language execution;
- filesystem/network/Git/device/subprocess effects;
- static/Library operational fallback;
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
- v0.25 isolated persistent-runtime harness: `25/25 PASS`.

Current-session V56 live residency evidence:

```text
200 repeated resident admissions
median 0.4185265 ms
min    0.393205 ms
max    0.78053 ms
```

A separate new Python process recovered and admitted the same resident handle from live `/dev/shm` without rebuilding the program image. Live unload/reload restored the same deterministic handle. Final fast admission remained PASS with tether/AC-AUX/ethics ACTIVE, no rehydration and no static fallback.

### Evidence boundary

The current pass did not execute a fresh live v0.20 control result and then resolve a fresh live v0.22 hierarchy lineage through the repository implementation. The v0.25 dispatch bridge is implemented and isolated-tested, but the **live control-dispatch closure remains pending**. The complete historical repository suite was not replayed.

## Repository additions

```text
src/phasenav_natural_code/runtime_v25.py
src/phasenav_natural_code/runtime_v25_core.py
src/phasenav_natural_code/runtime_v25_program.py
src/phasenav_natural_code/runtime_v25_resident.py
src/phasenav_natural_code/runtime_v25_resident_model.py
tests/test_persistent_runtime_v25.py
spec/PNCS_PERSISTENT_RUNTIME_V0_25.md
provenance/ledgers/PNCS_PERSISTENT_RUNTIME_LEDGER_V0_25.json
provenance/receipts/FOUNDATION_STATUS_V0_25.json
```

## Roadmap

The single authoritative roadmap is `spec/ROADMAP.md`.

Current gate: **v0.25 — Persistent PNCS Runtime**.

Next closure step: record one fresh live resident `v0.20 result -> v0.22 inverse lineage -> v0.25 dispatch receipt` witness. Only after that should the roadmap advance to **v0.26 — Effect Boundary**.

## Manifest status

`MANIFEST.sha256.json` remains fail-closed after repository-layout canonicalization and feature-gate construction. A complete SHA-256 manifest must be regenerated from the final release tree before release closure. Git blob SHA-1 values are not substituted for file SHA-256 values.
