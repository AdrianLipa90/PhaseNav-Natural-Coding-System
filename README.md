# PhaseNav Natural Code System (PNCS)

Status: NATURAL_PROGRAM_COMPOSITION_V0_23 / FOUNDATION LINEAGE V0.1-V0.23

PhaseNav Natural Code System is a 36-dimensional relational coding system in which written code is a human-readable projection of a canonical semantic-phase graph.

Canonical construction:

```text
KAKU -> RADICAL -> DEFINITION -> CLASS -> FILE -> CLUSTER
     -> SUBSYSTEM/DAEMON -> LOW_ORCHESTRATOR -> HIGH_ORCHESTRATOR -> SYSTEM
```

Natural language is an admissible input surface only after deterministic resolution to registered canonical relational paths. Unknown, ambiguous, unsupported, or unregistered semantics fail closed.

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

Cost does not alter semantic identity or establish semantic equivalence.

v0.22 added exact inverse execution provenance:

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

Hierarchy occurrences are exact, indexed, content-addressed, and ambiguity fails closed.

v0.23 adds bounded Natural Program Composition:

```text
IF ...
THEN ...
ELSE ...
AND THEN ...
RETURN ...
```

The control root must resolve to an already registered Definition CID. `AND THEN` accepts registered internal routes only. `RETURN` accepts registered result selectors only. Equivalent registered paraphrases converge to one deterministic composition identity.

The default v0.23 authority reuses the existing v0.11 `safety_bifurcation` Definition:

```text
pncs:def:sha256:b7988497bab75a526771fa24aeca75e0182bd437fd707927cb0e78b04d360cce
```

The canonical v0.23 witness is:

```text
pncs:composition:sha256:5b3710e6c8bf34d3754e7144ca139beb70205ea20b2fa504ef63c710c177cd57
```

v0.23 does not execute the composed program. `RETURN` exists in the live 36D operator registry, but operator presence is not execution authority. Full native program-unit execution remains closed.

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

`spec/REPOSITORY_LAYOUT.md` is the placement contract. Repository placement and aliases are provenance/projection metadata, not semantic identity.

## Core invariants

- same canonical semantics -> same semantic content identity;
- ambiguity or missing authority -> fail closed;
- exact 36D realization identity remains separate from semantic identity;
- semantic mass and graph cost remain separate from semantic identity;
- semantic mass and graph cost are not authorization;
- internal execution requires explicit route admission;
- external effects remain closed until the explicit Effect Boundary gate;
- result provenance recovers one exact content-addressed hierarchy occurrence;
- execution transition traces are continuous and deterministic;
- Definition->Radical->KAKU schedules match canonical Definition leaves exactly;
- natural program control must already exist in the Definition registry;
- `AND THEN` resolves only through registered internal routes;
- `RETURN` resolves only through the registered return-selector registry;
- source wording, aliases, case and whitespace do not alter composition identity;
- live operator presence does not grant execution authority;
- no new PNV opcode is introduced without an explicit gate.

## v0.23 return-selector registry

Stored at:

```text
registry/returns/PNCS_RETURN_SELECTOR_REGISTRY_V0_23.jsonl
```

Default selectors:

```text
result.control_location
result.branch_truth_state
result.final_sigma_id
result.lineage_id
```

Aliases are surface metadata. Return reference IDs are content-addressed from canonical selector semantics.

## Validation status

Historical evidence remains gate-scoped.

- v0.19 historical foundation baseline: `377/377 PASS`;
- v0.20 isolated execution-core harness: `14/14 PASS`;
- v0.21 isolated logic harness: `14/14 PASS`;
- v0.22 isolated inverse-lineage harness: `27/27 PASS`;
- v0.23 isolated composition harness: `28/28 PASS`;
- v0.23 repository integration tests added: `19`.

The complete historical repository suite was not replayed in the isolated v0.23 construction environment, and PNCS does not claim otherwise.

Live v0.23 validation confirmed the canonical 15-operator composition schedule on `/dev/shm/ciel_noema`, including the existing `RETURN` operator. The operator registry SHA-256 was:

```text
29767957ae775b1968bbb4c531728cc153137c88e819b135227dff73e3cca7ec
```

## Roadmap

The single authoritative engineering roadmap is `spec/ROADMAP.md`.

Completed gate: **v0.23 — Natural Program Composition**.

Next gate: **v0.24 — Native `.pnv` Program Units**.

v0.24 promotes a v0.23 composition to a first-class native unit with program CID, dependency closure, deterministic import/export, and deterministic build. Python remains the reference/test harness.

## Manifest status

`MANIFEST.sha256.json` remains fail-closed after repository-layout canonicalization and feature-gate construction. A complete SHA-256 manifest must be regenerated from the bytes of the final release tree before release closure. Git blob SHA-1 values are not substituted for file SHA-256 values.
