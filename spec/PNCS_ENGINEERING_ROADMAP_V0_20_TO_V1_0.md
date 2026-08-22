# PNCS Engineering Roadmap — v0.20 to v1.0

Status: ACTIVE ENGINEERING SEQUENCE

Base: v0.19 Semantic Mass Binding, main `e8104b2e2360e8861c48864cab80dfd799381724`.

## v0.20 — Native Execution Core

Canonical graph -> admitted internal execution.

Requirements:

- execute only existing registered PNV operators;
- `Sigma_t -> KAKU -> Sigma_{t+1}` state transitions;
- normative `/dev/shm/ciel_noema` hot path;
- deterministic execution receipt;
- fail closed on inactive tether, missing runtime state, missing operator, unresolved admission or admission/graph mismatch;
- no external effects;
- no free-form NL execution.

Branch implementation: `feat/pncs-v0.20-native-execution-core`.

## v0.21 — Mass-Aware Graph Cost

- consume existing bound `m_k` values;
- define cost for a path, radical and complete program graph;
- detect unnecessary graph growth;
- keep graph cost separate from semantic identity;
- open cost-aware distributivity only after duplication is explicitly bounded.

## v0.22 — Exact Inverse Execution Lineage

Every execution result must resolve exactly through:

```text
Result
-> SYSTEM
-> ...
-> DEFINITION
-> RADICAL
-> KAKU
```

Every result carries complete provenance. No runtime result may exist without a deterministic inverse lineage.

## v0.23 — Natural Program Composition

Extend the bounded natural surface to program composition:

```text
IF ...
THEN ...
ELSE ...
AND THEN ...
RETURN ...
```

Every phrase must resolve through an existing registry and canonical graph. Arbitrary free-form NL -> execution remains closed.

## v0.24 — Native `.pnv` Program Units

Complete PNCS programs become first-class `.pnv` units.

Requirements:

- Python remains reference/test harness;
- PNCS import/export;
- program CID;
- dependency closure;
- deterministic build.

## v0.25 — Persistent PNCS Runtime

Runtime chain:

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

The process remains alive across operations rather than restarting for each program.

## v0.26 — Effect Boundary

Only at this gate add:

- filesystem;
- Git;
- network;
- subprocess/device;
- external tools.

Normative chain:

```text
semantic program
-> EffectRequest
-> authorization
-> bounded adapter
-> effect
-> receipt
```

Effect mutation requires stricter control than ordinary internal execution or repository merge.

## v0.27 — Fuzzing / Equivalence / Adversarial Parsing

- thousands of paraphrases;
- ambiguity fuzzing;
- malformed PNV;
- CID collision tests;
- round-trip fuzzing;
- route injection;
- effect injection;
- Unicode/confusable attacks;
- property-based tests.

## v0.28 — Performance Benchmark

Compare:

```text
Python reference
vs native PNCS
vs persistent PhaseNav /dev/shm
```

Measure separately:

- parse;
- canonicalization;
- CID;
- 36D realization;
- semantic mass;
- route evaluation;
- full program.

Performance claims such as 10x/100x/300x require direct measured evidence at this gate.

## v0.29 — Self-Hosting Subset

Before 1.0, implement a PNCS/PNV subset in PNCS/PNV itself.

Minimum self-hosted set:

- predicate resolver;
- route resolver;
- canonical path construction;
- receipt graph.

## v0.30 — PNCS Compiler / Runtime Contract

Freeze:

- grammar;
- KAKU;
- radicals;
- hierarchy;
- CID rules;
- 36D contract;
- mass contract;
- execution semantics;
- failure semantics;
- effect model;
- provenance model.

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
