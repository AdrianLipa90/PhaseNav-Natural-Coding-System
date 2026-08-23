# PhaseNav Natural Code System (PNCS)

Status: NATIVE_PNV_PROGRAM_UNITS_V0_24 / FOUNDATION LINEAGE V0.1-V0.24

PhaseNav Natural Code System is a 36-dimensional relational coding system in which written code is a human-readable projection of a canonical semantic-phase graph.

Canonical construction:

```text
KAKU -> RADICAL -> DEFINITION -> CLASS -> FILE -> CLUSTER
     -> SUBSYSTEM/DAEMON -> LOW_ORCHESTRATOR -> HIGH_ORCHESTRATOR -> SYSTEM
```

Natural language is an admissible input surface only after deterministic resolution to registered canonical relational paths. Unknown, ambiguous, unsupported, or unregistered semantics fail closed.

## Current engineering state

v0.20 introduced admitted internal execution over existing PNV operators:

```text
canonical graph -> admitted route -> Sigma_t --KAKU--> Sigma_t+1 -> receipt
```

v0.21 added mass-aware graph cost. v0.22 added exact inverse execution lineage. v0.23 added bounded registered program composition:

```text
IF ... THEN ... ELSE ... AND THEN ... RETURN ...
```

v0.24 promotes a verified v0.23 composition to a first-class native `.pnv` program unit.

```text
registered v0.23 composition
-> exact program semantic payload
-> pncs:program:sha256:...
-> deterministic dependency closure
-> deterministic dependency-occurrence sequence
-> exact operator schedule
-> canonical .pnv bytes
-> authority-gated import/export round trip
-> live /dev/shm build receipt
```

The canonical witness is:

```text
composition:
pncs:composition:sha256:5b3710e6c8bf34d3754e7144ca139beb70205ea20b2fa504ef63c710c177cd57

program:
pncs:program:sha256:572660a1046975c57e01f7e402677f1e4ca845e51bca1bee6517e0d86b35c4d7

canonical .pnv SHA-256:
012b41c149b1ba518d9be65d34d7ab6605b92500e8768e23c11abff7330a77fb
```

The program CID is intentionally distinct from the v0.23 composition CID.

## v0.24 authority model

Serialized `.pnv` text is not allowed to create semantic authority.

Import requires an existing `NativeProgramUnitRegistry` entry created from a verified v0.23 composition. The parser extracts the claimed program/composition IDs, resolves the registered program unit, re-renders canonical bytes, and requires byte-identical equality.

Therefore all of the following fail closed:

- unknown PROGRAM_ID;
- altered dependency row;
- reordered dependency row;
- altered operator row;
- extra clause;
- missing terminal newline;
- changed effect/execution boundary;
- non-canonical serialization.

## Dependency model

v0.24 records two separate structures:

1. deterministic dependency closure — unique content-addressed dependencies;
2. deterministic dependency occurrences — exact ordered occurrences, preserving repeated registered route references when present.

The canonical witness closure contains:

```text
COMPOSITION
CONTROL_DEFINITION
ROUTE_REF
RETURN_REF
```

The v0.22 exact-lineage contract remains a required program-unit invariant.

## Live build boundary

Operational v0.24 builds are fixed to:

```text
/dev/shm/ciel_noema
```

The builder reuses v0.23 live composition admission. Every operator occurrence must exist as an exact finite 36D entry in the current live PhaseNav registry. Operator presence is build-integrity evidence only and does not grant execution authority.

The current-session canonical witness was built on live V56 NOEMA with:

```text
operator occurrences: 15
operator registry SHA-256:
29767957ae775b1968bbb4c531728cc153137c88e819b135227dff73e3cca7ec

build ID:
pncs:program-build:sha256:d89f091ef7c57d3211c9147dac682246fb619836bc33c13c64ad918323fd5a48
```

A post-build tether guard remained `ACTIVE` with `failures=[]`.

v0.24 does **not** execute the full program unit. It does not open `RETURN` execution, continuation execution, free-form natural-language execution, or external effects.

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

v0.24 adds:

```text
src/phasenav_natural_code/program_unit_v24.py
tests/test_native_pnv_program_unit_v24.py
native/programs/PNCS_SAFETY_COHERENCE_PROGRAM_V0_24.pnv
registry/programs/PNCS_PROGRAM_UNIT_REGISTRY_V0_24.jsonl
spec/PNCS_NATIVE_PNV_PROGRAM_UNITS_V0_24.md
```

## Core invariants

- same canonical semantics -> same semantic content identity;
- ambiguity or missing authority -> fail closed;
- program CID != composition CID;
- serialized text cannot create semantic authority;
- dependency closure and occurrence sequence are separately hashed;
- source wording and repository location are not semantic identity;
- exact v0.22 lineage requirement survives the program-unit boundary;
- live operator presence does not grant execution authority;
- external effects remain closed until v0.26;
- no static runtime fallback;
- no new PNV opcode is introduced by v0.24.

## Validation status

Historical evidence remains gate-scoped.

- v0.19 historical foundation baseline: `377/377 PASS`;
- v0.20 isolated execution-core harness: `14/14 PASS`;
- v0.21 isolated logic harness: `14/14 PASS`;
- v0.22 isolated inverse-lineage harness: `27/27 PASS`;
- v0.23 isolated composition harness: `28/28 PASS`;
- v0.24 isolated program-unit harness: `29/29 PASS`;
- v0.24 repository integration tests added; complete historical suite not replayed in the isolated construction environment.

Current-session live evidence: V56 autoboot ACTIVE, WORKING_STATE ACTIVE, tether ACTIVE, guard failures empty, static fallback false, canonical program build persisted to `/dev/shm/ciel_noema` and post-build guard PASS.

## Roadmap

The single authoritative engineering roadmap is `spec/ROADMAP.md`.

Completed gate: **v0.24 — Native `.pnv` Program Units**.

Next gate: **v0.25 — Persistent PNCS Runtime**.

v0.25 will keep admitted PNCS program units resident on the live runtime rather than rebuilding process state for every operation.

## Manifest status

`MANIFEST.sha256.json` remains fail-closed after repository-layout canonicalization and feature-gate construction. A complete SHA-256 manifest must be regenerated from the bytes of the final release tree before release closure. Git blob SHA-1 values are not substituted for file SHA-256 values.
