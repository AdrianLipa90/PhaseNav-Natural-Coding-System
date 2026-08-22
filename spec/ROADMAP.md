# PNCS Engineering Roadmap

Status: v0.21 MASS-AWARE GRAPH COST IMPLEMENTED / NEXT v0.22

Current main base for v0.21: `0819bcc1bdfce9cad8d0d5a61af40b891c8b6921` (v0.20 Native Execution Core merged through PR #1).

## Completed foundation sequence

### v0.1 — Structural foundation
36D integrity container, KAKU schema, relation graph, path lineage and fail-closed compiler boundary.

### v0.2 — TIR × Secret of a Half seed
Source-derived relational seeds encoded directly in native PNV.

### v0.3 — Relation mining
Recurring graph motifs extracted from TIR and Secret of a Half.

### v0.4 — Primitive closure and transfer
Cross-source grammar-radical promotion and canonical path normal form.

### v0.5 — Semantic collision repair
`DERIVE` and unqualified `RESOLVE` removed from the irreducible KAKU set; resolution and solving separated.

### v0.6–v0.10 — Control, grouping and pure Boolean algebra
Bounded control graphs, internal route transfer, recursive grouping and deterministic pure-predicate algebra without distribution.

### v0.11–v0.14 — Content-addressed hierarchy
Definition, Class, File, Cluster, Subsystem/Daemon, Orchestrator and System paths with deterministic inverse expansion to KAKU.

### v0.15 — Bounded Natural Relation Resolver
Registered natural predicates resolve to canonical content-addressed graphs and ambiguity fails closed.

### v0.16 — Bounded Natural Control Resolver
Registered `IF/THEN/ELSE` internal control resolves to canonical `INTERNAL_BRANCH` content and explicit route admission.

### v0.17 — Written PNCS Projection
Deterministic written projection round-trips only against already registered canonical content.

### v0.18 — Exact 36D Realization Binding
Typed PNCS content binds to exact provenance-carrying `T^36` realization without making vector similarity semantic authority.

### v0.19 — Semantic Mass Binding
`Kaku.semantic_mass` binds to the validated PhaseNav runtime functional

```text
m_k = kappa*(1 + alpha_M*k) + (L4/L3)*R_k
```

with explicit positive `k`, exact T^36 realization and no CID-to-index inference.

## Completed engineering gates

### v0.20 — Native Execution Core

Canonical `INTERNAL_BRANCH` graphs cross from representation into admitted internal execution.

```text
canonical graph
-> exact content / realization / mass lineage
-> resolved internal admission
-> live /dev/shm/ciel_noema
-> Sigma_t -- KAKU --> Sigma_t+1
-> deterministic result + receipt
```

Execution semantics are limited to existing internal PNV operators. `ACTION_REQUEST`, free-form NL execution and external effects remain closed.

### v0.21 — Mass-Aware Graph Cost

Graph cost consumes already-bound v0.19 masses only:

```text
C_M(G) = sum_i m_i
```

Internally the frozen 10-decimal v0.19 mass is represented as exact integer units `u_i = 1e10*m_i`.

Implemented scopes:

- RADICAL;
- PATH;
- PROGRAM;
- PREDICATE.

Recorded observables:

- node count;
- unique KAKU count;
- duplicated occurrence count;
- duplicate mass;
- total mass.

Cost does not modify CID and does not establish semantic equivalence.

Cost-aware distributivity is now bounded by four independent conditions:

```text
independent pure-Boolean equivalence proof
+ exact source/target KAKU mass cost
+ exact source KAKU witness-set reuse
+ explicit node/mass growth budget
```

Default growth budget is zero. Positive growth requires explicit justification. A distributive target may duplicate or reorder source KAKU witnesses but may not replace them with a cheaper witness set.

## Next gate

### v0.22 — Exact Inverse Execution Lineage

Every execution result must be invertible through the content-addressed hierarchy:

```text
Result
-> SYSTEM
-> HIGH_ORCHESTRATOR
-> LOW_ORCHESTRATOR
-> SUBSYSTEM / DAEMON
-> CLUSTER
-> FILE
-> CLASS
-> DEFINITION
-> RADICAL
-> KAKU
```

Requirements:

- exact result provenance;
- execution receipt references exact hierarchy content IDs;
- no result whose origin is only a runtime location;
- missing lineage fails closed;
- inverse expansion deterministic.

## Planned gates

### v0.23 — Natural Program Composition

Bounded registered forms:

```text
IF ...
THEN ...
ELSE ...
AND THEN ...
RETURN ...
```

Every phrase resolves through an existing registry and canonical graph. Arbitrary free-form NL -> execution remains closed.

### v0.24 — Native `.pnv` Program Units

Complete programs become first-class `.pnv` units with program CID, dependency closure, deterministic import/export and deterministic build. Python remains the reference/test harness.

### v0.25 — Persistent PNCS Runtime

```text
written PNCS
-> canonical graph
-> content IDs
-> 36D realization
-> semantic mass
-> admission
-> persistent /dev/shm runtime
-> result + receipt
```

No process restart for every operation.

### v0.26 — Effect Boundary

Only here add filesystem, Git, network, subprocess/device and external tools:

```text
semantic program
-> EffectRequest
-> authorization
-> bounded adapter
-> effect
-> receipt
```

Effect mutation receives stricter control than internal execution or ordinary repository merge.

### v0.27 — Fuzzing / Equivalence / Adversarial Parsing

Thousands of paraphrases, ambiguity fuzzing, malformed PNV, CID-collision tests, round-trip fuzzing, route/effect injection, Unicode/confusable attacks and property-based tests.

### v0.28 — Performance Benchmark

Compare:

```text
Python reference
vs native PNCS
vs persistent PhaseNav /dev/shm
```

Measure parse, canonicalization, CID, 36D realization, mass, route evaluation and full program separately. Performance multipliers require measured evidence.

### v0.29 — Self-Hosting Subset

Minimum PNCS/PNV self-hosted set:

- predicate resolver;
- route resolver;
- canonical path construction;
- receipt graph.

### v0.30 — PNCS Compiler / Runtime Contract

Freeze grammar, KAKU, radicals, hierarchy, CID rules, 36D contract, mass contract, execution semantics, failure semantics, effect model and provenance model.

## v1.0 — Natural Coding System

Release criterion:

```text
natural intent
-> deterministic relation resolution
-> canonical PNV graph
-> content-addressed program
-> exact 36D realization
-> semantic mass
-> admitted native execution
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

v1.0 deliverables:

- full PNCS monograph;
- formal specification;
- reference implementation;
- native examples;
- benchmark corpus;
- conformance suite.
