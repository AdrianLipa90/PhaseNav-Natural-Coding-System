# PhaseNav Natural Code System (PNCS)

Status: EFFECT_BOUNDARY_V0_26 / RELEASE GATE CLOSED / NEXT v0.27 FUZZING + ADVERSARIAL PARSING

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
v0.25 persistent resident runtime
v0.26 explicit bounded effect boundary
```

Operational 36D runtime remains `/dev/shm/ciel_noema`. Library and repository artifacts are provenance/persistence sources only and never an operational fallback.

## v0.25 execution closure

The release-closed v0.25 chain is:

```text
resident program
-> O(1) admission
-> v0.20 control execution
-> v0.22 inverse lineage
-> deterministic v0.25 dispatch receipt
```

Canonical dispatch witness:

```text
pncs:resident-dispatch:sha256:fd18f2d0296321d432a49e699d2f72a0a03313ed2dcc87b9aba647555f12c2e2
```

## v0.26 Effect Boundary

v0.26 does not make effects implicit. It adds a separate authority layer:

```text
v0.25 dispatch
-> EffectRequest
-> explicit AuthorizationGrant
-> registered bounded adapter
-> effect
-> deterministic EffectReceipt
-> inverse provenance
```

The executor starts **deny-all**: both the authorization registry and adapter registry are empty until the host explicitly registers exact authority. Authorization is independent of semantic mass, graph cost, route admission and program identity.

The first and only effect class opened in v0.26 is:

```text
NOEMA_RUNTIME_RECORD_WRITE
```

It can write only an immutable, content-addressed record below:

```text
/dev/shm/ciel_noema/pncs/v0.26/effects/records/
```

Hard bounds:

- max canonical payload: 4096 bytes;
- program-supplied paths are data, never path authority;
- append-only immutable records;
- exact replay is idempotent;
- directory-FD traversal with `O_NOFOLLOW` where supported;
- no arbitrary filesystem destination;
- no Git;
- no network;
- no subprocess/shell;
- no device I/O;
- no external connector/tool adapter;
- no static runtime fallback;
- no new PNV opcodes.

Live V56 witness:

```text
request:
pncs:effect-request:sha256:d6c3ef3801d64c7469650673efc7cbf56e01c896cbc235be98c113543fcea347

authorization:
pncs:effect-authorization:sha256:7a9397d86bc854d835559eb1d4f27af308962a68dad52a568263e878410f764c

adapter:
pncs:effect-adapter:sha256:dae04f919e137886c8775b337e5acb4a66775111e2a150fe5702d46032356339

effect:
pncs:effect:sha256:1fb02a1f9b068aab2b04a0faa453fecab3086fe61e22514d4b8b2b6a979220c7

receipt:
pncs:effect-receipt:sha256:f8f4aeee9ef26168579e883a508c0eb3cb9c4c551c25faa7a95c64b032efb4ea
```

Inverse provenance:

```text
EFFECT -> AUTHORIZATION -> EFFECT_REQUEST -> DISPATCH -> RESULT
       -> LINEAGE -> PROGRAM -> RESIDENT_HANDLE -> RUNTIME_GENERATION
```

The live payload was explicitly a conformance record, not a sensor/risk claim. Replaying the exact request after dirfd/`O_NOFOLLOW` hardening reproduced the same identities. Post-effect tether guard remained `ACTIVE` with `failures=[]`.

## Validation

Gate-scoped evidence:

```text
v0.19 historical foundation baseline: 377/377 PASS
v0.20 isolated execution-core harness: 14/14 PASS
v0.21 isolated cost harness: 14/14 PASS
v0.22 isolated inverse-lineage harness: 27/27 PASS
v0.23 isolated composition harness: 28/28 PASS
v0.24 isolated program-unit harness: 29/29 PASS
v0.25 isolated persistent-runtime harness: 25/25 PASS
v0.26 isolated effect-boundary harness: 28/28 PASS
v0.26 live bounded effect: PASS
v0.26 post-effect tether guard: PASS
```

The complete historical repository suite was not replayed in the v0.26 pass and is not claimed.

## Repository additions for v0.26

```text
src/phasenav_natural_code/effect_v26.py
src/phasenav_natural_code/effect_v26_core.py
src/phasenav_natural_code/effect_v26_fs.py
src/phasenav_natural_code/effect_v26_runtime.py
tests/test_effect_boundary_v26.py
spec/PNCS_EFFECT_BOUNDARY_V0_26.md
registry/effects/PNCS_EFFECT_ADAPTER_REGISTRY_V0_26.jsonl
native/PNCS_EFFECT_BOUNDARY_V0_26.pnv
provenance/ledgers/PNCS_EFFECT_BOUNDARY_LEDGER_V0_26.json
provenance/receipts/FOUNDATION_STATUS_V0_26.json
provenance/receipts/PNCS_V0_26_LIVE_EFFECT_BOUNDARY_20260823.json
```

## Roadmap

The single authoritative roadmap is `spec/ROADMAP.md`.

Next gate: **v0.27 — Fuzzing / Equivalence / Adversarial Parsing**.

## Manifest status

`MANIFEST.sha256.json` remains fail-closed after repository-layout canonicalization and feature-gate construction. A complete SHA-256 manifest must be regenerated from final release-tree bytes before release closure. Git blob SHA-1 values are not substituted for file SHA-256 values.
