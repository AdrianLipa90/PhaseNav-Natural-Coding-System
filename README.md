# PhaseNav Natural Code System (PNCS)

Status: ORCHORBITAL_HYDRO_V0_27 / RELEASE GATE CLOSED / NEXT v0.28 FUZZING + EQUIVALENCE + ADVERSARIAL PARSING

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
v0.27 ORCHORBITAL × hydrodynamic T^36 direct execution side-car
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

## v0.27 ORCHORBITAL × Hydrodynamic T^36

v0.27 couples the frozen v0.20 internal transition chain to an authority-neutral ORCHORBITAL/T^36 side-car:

```text
original v0.20 KAKU transition
-> unchanged Sigma + unchanged ExecutionStep
-> exact live 36D operator-vector revalidation
-> dynamic ORCH occurrence / process sphere
-> subjective-time + hydrodynamic T^36 transition
-> OORP state update
-> return original v0.20 Sigma
```

Release-closure invariants:

```text
Sigma_base == Sigma_coupled
base v0.20 steps == coupled base steps
routing_authority_opened       = false
effect_authority_opened        = false
persistent_memory_write        = false
external_effects               = false
laboratory_time_modified       = false
static_runtime_fallback        = false
```

Fresh V56 direct-coupled closure:

```text
v0.20 receipt:
1b3ca3c311492e16d447a333e2d1a4f0381c9de77ec7ebfb293637e08021fbf4

direct trace:
pncs:orch-direct-trace:sha256:bac0af63fe8fe01a7138613555c266129108183e39b09b6a75ebe7a90b13f17b

receipt-bound trace:
pncs:orch-receipt-bound-trace:sha256:1d98527a6975bf82246e1fcb521c05b082b296c2ce79758f0e0c72184d945907

final Sigma:
pncs:sigma:sha256:fa551b6d741b73c4eb0988acbbe54e18ed2c0cccda77d78c93007f900a3dbbaf

full live witness SHA-256:
95072fcf3c10a82fb510cd2857bf497d885b79635536dd069e35394bdda58691

closure receipt SHA-256:
88710ab288eb759aeed0b151cc03ba85c0529f58fb8eaade65df17d1970d1a07
```

The inverse-provenance chain preserves evidence classes: the v0.27 trace and fresh v0.20 receipt are current V56 execution evidence; the existing v0.22 lineage and v0.25 dispatch/witness remain repository-verified historical closure evidence and are not relabeled as current live evidence.

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
v0.27 committed compact ORCH conformance: 18/18 PASS
v0.27 broader ORCH development harness: 33/33 PASS
v0.27 current-worker ORCH core harness: 51/51 PASS
v0.27 exact branch direct-executor tests: 9/9 PASS
v0.27 fresh V56 direct coupling: PASS
v0.27 post-witness tether guard: PASS / failures=[]
```

The complete historical repository suite was not replayed in the v0.27 closure and is not claimed. Current-head GitHub Actions CI PASS is also not claimed; a prior Actions run failed without a retrievable artifact/log and remains recorded separately.

## Repository additions for v0.27

```text
src/phasenav_natural_code/orchorbital_v27.py
src/phasenav_natural_code/orchorbital_hydro_v27.py
src/phasenav_natural_code/orchorbital_executor_v27.py
src/phasenav_natural_code/hydro_time_v27.py
src/phasenav_natural_code/hydro_schedule_v27.py
tests/test_orchorbital_v27.py
tests/test_orchorbital_foundation_constraints_v27.py
tests/test_orchorbital_executor_v27.py
tests/test_hydro_time_v27.py
tests/test_hydro_schedule_v27.py
spec/PNCS_ORCHORBITAL_HYDRO_COUPLING_V0_27.md
provenance/receipts/FOUNDATION_STATUS_V0_27_ORCHORBITAL.json
provenance/receipts/PNCS_V0_27_LIVE_DIRECT_COUPLED_CLOSURE_20260823.json
```

## Roadmap

The single authoritative roadmap is `spec/ROADMAP.md`.

Next gate: **v0.28 — Fuzzing / Equivalence / Adversarial Parsing**.

## Manifest status

`MANIFEST.sha256.json` remains fail-closed. A complete SHA-256 manifest must be regenerated from final release-tree bytes before final release packaging. Git blob SHA-1 values are not substituted for file SHA-256 values.
