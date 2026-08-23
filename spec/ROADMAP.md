# PNCS Engineering Roadmap

Status: v0.26 EFFECT BOUNDARY RELEASE CLOSED / NEXT v0.27 FUZZING + EQUIVALENCE + ADVERSARIAL PARSING

## Completed foundation sequence

### v0.1–v0.19 — Semantic and 36D foundation
Structural KAKU/Radical relations, control/algebra, content-addressed hierarchy, registered natural/written surfaces, exact 36D realization binding and semantic mass binding.

### v0.20 — Native Execution Core

```text
canonical graph -> admitted internal route -> live /dev/shm/ciel_noema
-> Sigma_t --KAKU--> Sigma_t+1 -> deterministic result + receipt
```

External effects remained closed.

### v0.21 — Mass-Aware Graph Cost

`C_M(G)=sum_i m_i`, with graph cost separate from semantic identity/equivalence and explicit growth budgets.

### v0.22 — Exact Inverse Execution Lineage

```text
Result -> SYSTEM -> HIGH_ORCHESTRATOR -> LOW_ORCHESTRATOR
-> SUBSYSTEM/DAEMON -> CLUSTER -> FILE -> CLASS
-> DEFINITION -> RADICAL -> KAKU
```

Isolated validation: `27/27 PASS`.

### v0.23 — Natural Program Composition
Registered bounded `IF / THEN / ELSE / AND THEN / RETURN` composition. Isolated validation: `28/28 PASS`.

### v0.24 — Native `.pnv` Program Units
Verified composition -> first-class program CID -> exact dependency closure -> canonical `.pnv` bytes -> deterministic build receipt. Isolated validation: `29/29 PASS`.

### v0.25 — Persistent PNCS Runtime
Release-closed generation-bound residency and O(1) admission:

```text
v0.24 program image
-> resident handle
-> O(1) admission
-> v0.20 control dispatch
-> exact v0.22 lineage
-> deterministic v0.25 dispatch receipt
```

Evidence:

```text
isolated v0.25 harness: 25/25 PASS
live V56 residency: PASS
cross-process recovery: PASS
live unload/reload same handle: PASS
200 admissions median: 0.4185265 ms
200 admissions max: 0.78053 ms
live v0.20 -> v0.22 -> v0.25 dispatch closure: PASS
```

Canonical dispatch:

```text
pncs:resident-dispatch:sha256:fd18f2d0296321d432a49e699d2f72a0a03313ed2dcc87b9aba647555f12c2e2
```

### v0.26 — Effect Boundary

Release-closed bounded effect model:

```text
v0.25 dispatch
-> explicit EffectRequest
-> explicit AuthorizationGrant
-> registered bounded adapter
-> effect
-> deterministic EffectReceipt
-> inverse provenance
```

Core invariants:

- default policy is deny;
- executor does not create authorization;
- authorization is exact-request, generation-bound, adapter-bound and no-delegation;
- semantic mass/cost/route/program identity do not authorize effects;
- adapter registry starts empty;
- effect classes open individually only after conformance;
- program-supplied paths are not operational path authority;
- retries are exact-idempotent or fail loudly;
- generation is re-admitted before, immediately before commit and after effect;
- operational path remains `/dev/shm/ciel_noema`;
- no static fallback;
- no new PNV opcodes.

First admitted effect class:

```text
NOEMA_RUNTIME_RECORD_WRITE
```

Fixed subtree:

```text
/dev/shm/ciel_noema/pncs/v0.26/effects/records/
```

The adapter is append-only, content-addressed, max 4096 canonical payload bytes and traverses fixed directories using dirfds with `O_NOFOLLOW` where supported.

Still closed:

```text
arbitrary filesystem targets
Git writes
network requests
subprocess / shell
device I/O
external tool / connector adapters
```

Validation:

```text
isolated v0.26 harness: 28/28 PASS
live bounded effect: PASS
exact replay after dirfd/O_NOFOLLOW hardening: PASS
post-effect tether guard: ACTIVE / failures=[]
```

Live witness identities:

```text
request:       pncs:effect-request:sha256:d6c3ef3801d64c7469650673efc7cbf56e01c896cbc235be98c113543fcea347
authorization: pncs:effect-authorization:sha256:7a9397d86bc854d835559eb1d4f27af308962a68dad52a568263e878410f764c
adapter:       pncs:effect-adapter:sha256:dae04f919e137886c8775b337e5acb4a66775111e2a150fe5702d46032356339
effect:        pncs:effect:sha256:1fb02a1f9b068aab2b04a0faa453fecab3086fe61e22514d4b8b2b6a979220c7
receipt:       pncs:effect-receipt:sha256:f8f4aeee9ef26168579e883a508c0eb3cb9c4c551c25faa7a95c64b032efb4ea
```

The complete historical suite was not replayed and is not claimed.

## Current gate

### v0.27 — Fuzzing / Equivalence / Adversarial Parsing

Required corpus:

- paraphrase and alias equivalence;
- ambiguity fuzzing;
- malformed `.pnv`;
- typed-ID and CID substitution;
- Unicode/confusable operator and route injection;
- graph-cost edge cases;
- hierarchy occurrence ambiguity;
- resident generation substitution;
- effect-request injection;
- payload fields named like paths/commands/URLs;
- symlink/path traversal attempts;
- authorization ambiguity/substitution;
- adapter registry substitution;
- exact-replay and immutable-effect tamper;
- property-based deterministic identity tests.

No additional effect class should open as part of v0.27.

## Planned gates

### v0.28 — Performance Benchmark
Measure parsing, canonicalization, CID, realization, mass, resident admission, dispatch, effect authorization and bounded effect latency separately. Speedup claims require measured evidence.

### v0.29 — Self-Hosting Subset
Predicate resolver, route resolver, canonical path construction, receipt graph and effect-request validation.

### v0.30 — PNCS Compiler / Runtime Contract
Freeze grammar, KAKU, radicals, hierarchy, CID rules, 36D contract, mass contract, program format, persistent runtime, execution semantics, effect model, failure semantics and provenance model.

## v1.0 — Natural Coding System

```text
natural intent
-> deterministic relation resolution
-> canonical PNV graph
-> content-addressed program
-> exact 36D realization
-> semantic mass
-> persistent admitted native execution
-> deterministic result
-> explicit authorized bounded effect when requested
-> complete inverse provenance
```

Required invariants:

```text
same semantics -> same canonical identity
ambiguity      -> fail closed
missing state  -> fail closed
effect         -> explicit separate authorization
result/effect  -> full provenance
```

Deliverables: full PNCS monograph, formal specification, reference implementation, native examples, benchmark corpus and conformance suite.
