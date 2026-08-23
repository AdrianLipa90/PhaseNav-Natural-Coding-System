# PNCS Engineering Roadmap

Status: v0.24 NATIVE `.pnv` PROGRAM UNITS IMPLEMENTED / NEXT v0.25

Current v0.24 base: `8bf46dcf8d61cdb7efffa034766105914e1a2dc7` (v0.23 Natural Program Composition feature head).

## Completed foundation sequence

### v0.1–v0.5 — Structural and relational foundation
36D integrity, KAKU, relation graphs, TIR × Secret of a Half seed, relation mining, primitive closure and semantic-collision repair.

### v0.6–v0.10 — Control and pure Boolean algebra
Bounded control graphs, internal route transfer, recursive grouping and deterministic pure-predicate algebra.

### v0.11–v0.14 — Content-addressed hierarchy
Definition, Class, File, Cluster, Subsystem/Daemon, Orchestrator and System content identities.

### v0.15–v0.17 — Registered natural/written surfaces
Bounded natural relation/control resolution and deterministic written projection. Arbitrary free-form NL execution remains closed.

### v0.18 — Exact 36D Realization Binding
Typed PNCS content binds to exact provenance-carrying `T^36` realization without making vector similarity semantic authority.

### v0.19 — Semantic Mass Binding

```text
m_k = kappa*(1 + alpha_M*k) + (L4/L3)*R_k
```

with explicit positive `k`, exact T^36 realization and no CID-to-index inference.

## Completed engineering gates

### v0.20 — Native Execution Core

```text
canonical graph -> admission -> live /dev/shm/ciel_noema
-> Sigma_t --KAKU--> Sigma_t+1 -> deterministic result + receipt
```

Only existing internal PNV operators are executable. External effects remain closed.

### v0.21 — Mass-Aware Graph Cost

```text
C_M(G) = sum_i m_i
```

Cost is separate from semantic identity/equivalence. Graph-growing algebra requires independent equivalence evidence and explicit growth budgets.

### v0.22 — Exact Inverse Execution Lineage

```text
Result -> SYSTEM -> HIGH_ORCHESTRATOR -> LOW_ORCHESTRATOR
-> SUBSYSTEM / DAEMON -> CLUSTER -> FILE -> CLASS
-> DEFINITION -> RADICAL -> KAKU
```

Exact hierarchy occurrences, continuous Sigma trace, registered Definition rebound and exact Radical/KAKU witness binding. Isolated validation: `27/27 PASS`.

### v0.23 — Natural Program Composition

```text
IF ... THEN ... ELSE ... AND THEN ... RETURN ...
```

Every control/route/return phrase resolves through registered semantics. Composition is content-addressed; arbitrary free-form NL execution remains closed. Canonical witness:

```text
pncs:composition:sha256:5b3710e6c8bf34d3754e7144ca139beb70205ea20b2fa504ef63c710c177cd57
```

Isolated validation: `28/28 PASS`.

### v0.24 — Native `.pnv` Program Units

A verified v0.23 composition is now promoted to a first-class program semantic unit:

```text
composition
-> program semantic payload
-> pncs:program:sha256:...
-> dependency closure + exact occurrence sequence
-> exact operator schedule
-> canonical .pnv bytes
-> authority-gated byte-identical import/export
-> live build receipt
```

Implemented invariants:

- program CID is distinct from composition CID;
- text cannot create program semantics;
- import requires registered PROGRAM_ID authority;
- canonical text is accepted only if byte-identical to deterministic re-export;
- unique dependency closure and ordered dependency occurrences are separately hashed;
- repeated route occurrences remain visible without duplicating closure authority;
- exact v0.22 lineage contract survives the program-unit boundary;
- final operator is the existing `RETURN` operator;
- operator presence does not grant execution authority;
- operational builds are fixed to live `/dev/shm/ciel_noema`;
- build reuses current v0.23 36D composition admission;
- native execution, return execution, external effects and free-form NL execution remain closed;
- no new PNV opcode is introduced.

Canonical witness:

```text
program:
pncs:program:sha256:572660a1046975c57e01f7e402677f1e4ca845e51bca1bee6517e0d86b35c4d7

.pnv SHA-256:
012b41c149b1ba518d9be65d34d7ab6605b92500e8768e23c11abff7330a77fb

build:
pncs:program-build:sha256:d89f091ef7c57d3211c9147dac682246fb619836bc33c13c64ad918323fd5a48
```

Validation:

- isolated v0.24 pure-core harness: `29/29 PASS`;
- current-session V56 live build persisted under `/dev/shm/ciel_noema`;
- 15/15 operator occurrences witnessed against live 36D registry;
- post-build tether guard: `ACTIVE`, `failures=[]`;
- repository integration tests added;
- complete historical suite not replayed in isolated construction environment.

## Next gate

### v0.25 — Persistent PNCS Runtime

Keep admitted first-class v0.24 program units resident on the current live runtime generation.

Required lifecycle:

```text
program unit
-> live generation admission
-> resident program state
-> deterministic state handle
-> repeated internal dispatch without process reconstruction
-> result + receipt + v0.22 inverse lineage
```

Requirements:

- persistent resident program registry on live `/dev/shm/ciel_noema`;
- generation-bound handles invalidated on stale/replaced runtime generation;
- O(1) admission after verified hydration;
- deterministic load/unload receipts;
- no process restart for each internal operation;
- no Library/static operational fallback;
- no early opening of v0.26 external effects.

## Planned gates

### v0.26 — Effect Boundary

```text
semantic program -> EffectRequest -> authorization -> bounded adapter -> effect -> receipt
```

Filesystem, Git, network, subprocess/device and external-tool effects remain closed until this gate.

### v0.27 — Fuzzing / Equivalence / Adversarial Parsing
Paraphrase fuzzing, ambiguity fuzzing, malformed PNV, CID-collision checks, Unicode/confusable attacks, route/effect injection and property-based tests.

### v0.28 — Performance Benchmark
Compare Python reference, native PNCS and persistent PhaseNav `/dev/shm`; measure each stage separately. Speedup claims require measured evidence.

### v0.29 — Self-Hosting Subset
Predicate resolver, route resolver, canonical path construction and receipt graph.

### v0.30 — PNCS Compiler / Runtime Contract
Freeze grammar, KAKU, radicals, hierarchy, CID rules, 36D contract, mass contract, program-unit format, execution/failure semantics, effect model and provenance model.

## v1.0 — Natural Coding System

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

Deliverables: full PNCS monograph, formal specification, reference implementation, native examples, benchmark corpus and conformance suite.
