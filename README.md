# PhaseNav Natural Code System (PNCS)

Status: MASS_AWARE_GRAPH_COST_V0_21 / FOUNDATION LINEAGE V0.1-V0.21

PhaseNav Natural Code System is a 36-dimensional relational coding system in which written code is a human-readable projection of a canonical semantic-phase graph.

Canonical construction:

```text
KAKU -> RADICAL -> DEFINITION -> CLASS -> FILE -> CLUSTER
     -> SUBSYSTEM/DAEMON -> LOW_ORCHESTRATOR -> HIGH_ORCHESTRATOR -> SYSTEM
```

Natural language is an admissible input surface only after deterministic resolution to registered canonical relational paths. Unknown, ambiguous, or unsupported semantics fail closed.

## Current engineering state

v0.20 closed the first admitted internal native-execution gate:

```text
canonical graph -> admitted route -> existing PNV operators
-> Sigma_t --KAKU--> Sigma_t+1 -> deterministic receipt
```

The normative operational surface is `/dev/shm/ciel_noema`; no static runtime fallback is authoritative.

v0.21 adds mass-aware graph cost over the already bound v0.19 semantic masses:

```text
C_M(G) = sum_i m_i
```

Cost is measured for RADICAL, PATH, PROGRAM, and pure PREDICATE scopes. Cost does not alter semantic identity and does not prove semantic equivalence. Distributive candidates require independent Boolean-equivalence evidence, exact source KAKU witness reuse, and explicit growth-budget admission. Default added-node and added-mass budgets are zero.

v0.19 recorded a 377/377 historical foundation baseline. The isolated v0.20 execution-core harness recorded 14/14 PASS. The isolated v0.21 logic harness recorded 14/14 PASS. The complete historical repository suite was not replayed in the isolated v0.21 construction environment, and PNCS does not claim otherwise.

## Canonical repository layout

```text
/
├── src/              reference implementation
├── tests/            conformance and gate tests
├── native/           native .pnv artifacts
├── registry/         semantic registries and content indexes
├── provenance/       ledgers and deterministic receipts
└── spec/             normative specifications and ROADMAP.md
```

`spec/REPOSITORY_LAYOUT.md` is the placement contract. Repository placement is provenance/projection metadata and is not semantic identity.

## Core invariants

- same canonical semantics -> same semantic content identity;
- ambiguity or missing runtime support -> fail closed;
- exact 36D realization identity remains separate from semantic identity;
- semantic mass and graph cost remain separate from semantic identity;
- equal mass or equal cost does not imply semantic equivalence;
- semantic mass and graph cost are not authorization;
- internal execution requires explicit route admission;
- external effects remain closed until the explicit Effect Boundary gate;
- execution and graph-cost results carry deterministic provenance;
- no new PNV opcode is introduced without an explicit gate.

## Roadmap

The single authoritative engineering roadmap is `spec/ROADMAP.md`.

Completed gate: **v0.21 — Mass-Aware Graph Cost**.

Next gate: **v0.22 — Exact Inverse Execution Lineage**.

The next requirement is exact result provenance:

```text
Result -> SYSTEM -> ... -> DEFINITION -> RADICAL -> KAKU
```

without relying on incidental process location or mutable runtime state.

## Provenance

Historical gate specifications remain under `spec/`. Native witnesses remain under `native/`. Semantic registries are under `registry/`; ledgers and deterministic receipts are under `provenance/`.

The repository SHA-256 manifest is fail-closed after repository-layout changes and must be regenerated before this canonicalization is release-closed.
