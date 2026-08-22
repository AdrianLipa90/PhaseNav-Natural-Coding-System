# PhaseNav Natural Code System (PNCS)

Status: EXACT_INVERSE_EXECUTION_LINEAGE_V0_22 / FOUNDATION LINEAGE V0.1-V0.22

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

v0.21 added mass-aware graph cost over already-bound v0.19 semantic masses:

```text
C_M(G) = sum_i m_i
```

Cost does not alter semantic identity or establish semantic equivalence. Graph-growing algebra requires independent equivalence evidence and explicit node/mass budget admission.

v0.22 closes exact inverse execution provenance:

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

The lineage stores exact hierarchy occurrence indexes, revalidates the v0.20 receipt and continuous Sigma transition trace, rebounds the receipt to the registered Definition graph/leaf path, and binds the Definition to one fully hashed RadicalGraph plus exact ordered KAKU schedule.

A reused CID at two hierarchy positions is not guessed away: zero matches fail closed; multiple matches fail closed unless one exact occurrence is explicitly selected.

The normative operational surface remains `/dev/shm/ciel_noema`; no static runtime fallback is authoritative.

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
- result provenance must recover one exact content-addressed hierarchy occurrence;
- execution transition trace must be continuous and deterministic;
- aliases, filesystem paths and runtime location are not semantic authority;
- Definition->Radical->KAKU role schedule must equal the canonical Definition leaf path;
- no new PNV opcode is introduced without an explicit gate.

## Validation status

Historical evidence remains gate-scoped. v0.19 recorded a 377/377 historical foundation baseline. The isolated v0.20 execution-core harness recorded 14/14 PASS; v0.21 recorded 14/14 PASS; v0.22 currently records 27/27 PASS in its isolated pure-core harness and includes repository integration tests using the real PNCS registries.

The complete historical repository suite was not replayed in the isolated v0.22 construction environment, and PNCS does not claim otherwise.

## Roadmap

The single authoritative engineering roadmap is `spec/ROADMAP.md`.

Completed gate: **v0.22 — Exact Inverse Execution Lineage**.

Next gate: **v0.23 — Natural Program Composition**.

```text
IF ...
THEN ...
ELSE ...
AND THEN ...
RETURN ...
```

Every executable phrase must resolve through registered canonical semantics; arbitrary free-form natural-language execution remains closed.

## Manifest status

`MANIFEST.sha256.json` remains fail-closed after the repository-layout canonicalization and v0.22 branch construction. A complete SHA-256 manifest must be regenerated from the bytes of the final branch tree before release closure. Git blob SHA-1 values are not substituted for file SHA-256 values.
