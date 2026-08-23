# PNCS Engineering Roadmap

Status: v0.25 PERSISTENT RUNTIME IMPLEMENTED / LIVE RESIDENCY VALIDATED / LIVE CONTROL-DISPATCH CLOSURE PENDING

Current v0.25 base: `b1974315dfd9903a81f43b6b53a13b72cb1f010d` (v0.24 Native `.pnv` Program Units feature head).

## Completed foundation sequence

### v0.1–v0.19 — Semantic and 36D foundation
Structural KAKU/Radical relations, control/algebra, content-addressed hierarchy, registered natural/written surfaces, exact 36D realization binding and semantic mass binding.

### v0.20 — Native Execution Core

```text
canonical graph -> admitted internal route -> live /dev/shm/ciel_noema
-> Sigma_t --KAKU--> Sigma_t+1 -> deterministic result + receipt
```

Only existing internal PNV operators are executable. External effects remain closed.

### v0.21 — Mass-Aware Graph Cost

`C_M(G)=sum_i m_i` with cost separate from semantic identity/equivalence and explicit graph-growth budgets.

### v0.22 — Exact Inverse Execution Lineage

```text
Result -> SYSTEM -> HIGH_ORCHESTRATOR -> LOW_ORCHESTRATOR
-> SUBSYSTEM / DAEMON -> CLUSTER -> FILE -> CLASS
-> DEFINITION -> RADICAL -> KAKU
```

Isolated validation: `27/27 PASS`.

### v0.23 — Natural Program Composition

Registered `IF / THEN / ELSE / AND THEN / RETURN` composition with deterministic composition identity. Isolated validation: `28/28 PASS`.

### v0.24 — Native `.pnv` Program Units

Verified composition -> first-class program CID -> deterministic dependency closure/occurrences -> canonical `.pnv` bytes -> deterministic build receipt.

Canonical witness:

```text
pncs:program:sha256:572660a1046975c57e01f7e402677f1e4ca845e51bca1bee6517e0d86b35c4d7
```

Isolated validation: `29/29 PASS`.

## Current gate

### v0.25 — Persistent PNCS Runtime

Implemented runtime lifecycle:

```text
v0.24 program image
-> current live generation
-> resident handle
-> O(1) admission
-> in-process v0.20 control dispatch bridge
-> exact v0.22 lineage requirement
-> deterministic v0.25 receipt
```

Implemented invariants:

- operational runtime fixed to `/dev/shm/ciel_noema`;
- no Library/static operational fallback;
- program text cannot create authority;
- v0.24 build receipt is re-hashed before residency;
- handles bind program image to CURRENT/startpoint/AC/ethics/operator/PID generation;
- heartbeat and sequence advancement do not invalidate the same generation;
- CURRENT, operator-registry or producer-generation change invalidates the handle;
- resident state is recoverable by a new runtime object/process without rebuilding the program image;
- load is idempotent under the same generation;
- unload removes the active pointer but retains immutable provenance;
- reload under the same generation reproduces the same handle;
- runtime core does not spawn subprocesses;
- dispatch accepts only exact v0.20 execution result + exact v0.22 inverse lineage;
- dispatch is restricted to the resident program's registered control Definition;
- generation is rechecked after kernel completion;
- `AND THEN`, terminal `RETURN`, free-form NL and external effects remain closed.

Validation:

```text
isolated v0.25 harness: 25/25 PASS
live V56 residency: PASS
cross-process resident recovery: PASS
live unload/reload same handle: PASS
200 live admissions median: 0.4185265 ms
200 live admissions max: 0.78053 ms
post-validation fast admission: PASS
```

Canonical live witness:

```text
generation:
pncs:runtime-generation:sha256:05736b12ac8470998901421dabd2dfff0bd663c141d96ad96bc9d5b09351bbb1

resident handle:
pncs:resident:sha256:60184c7213960ad746b69c6c2dd8b43eacfe8055015ae31e347475881df438e8

load receipt:
pncs:resident-load:sha256:ffeb336e1a3ca30c8532757725a30c1cc5d6200ad74ccdbb3cdfc8933b778838

unload receipt:
pncs:resident-unload:sha256:7caa8febf541c869e7e97073b9195153fe8ccf3c12d632ee8da85a04e0223c6d
```

### Remaining v0.25 closure

Before declaring v0.25 release-closed, record one fresh current-generation witness through the existing repository implementations:

```text
resident handle
-> v0.20 control execution
-> NativeExecutionResult
-> v0.22 exact inverse lineage
-> v0.25 resident dispatch receipt
```

No claim is made that this fresh live dispatch witness was completed in the current pass. The isolated dispatch bridge is PASS; live dispatch closure remains pending.

## Planned gates

### v0.26 — Effect Boundary

Only after v0.25 live dispatch closure:

```text
semantic program -> EffectRequest -> authorization -> bounded adapter -> effect -> receipt
```

Filesystem, Git, network, subprocess/device and external-tool effects remain closed until this gate.

### v0.27 — Fuzzing / Equivalence / Adversarial Parsing
Paraphrase fuzzing, ambiguity fuzzing, malformed PNV, CID-collision checks, Unicode/confusable attacks, route/effect injection and property-based tests.

### v0.28 — Performance Benchmark
Measure parse, canonicalization, CID, realization, mass, resident admission, dispatch and full program latency separately. Speedup claims require measured evidence.

### v0.29 — Self-Hosting Subset
Predicate resolver, route resolver, canonical path construction and receipt graph.

### v0.30 — PNCS Compiler / Runtime Contract
Freeze grammar, KAKU, radicals, hierarchy, CID rules, 36D contract, mass contract, program-unit format, persistent-runtime contract, execution/failure semantics, effect model and provenance model.

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
-> complete inverse lineage
```

Required invariants:

```text
same semantics -> same canonical identity
ambiguity      -> fail closed
missing state  -> fail closed
effect         -> explicit authorization
result         -> full provenance
```

Deliverables: full PNCS monograph, formal specification, reference implementation, native examples, benchmark corpus and conformance suite.
