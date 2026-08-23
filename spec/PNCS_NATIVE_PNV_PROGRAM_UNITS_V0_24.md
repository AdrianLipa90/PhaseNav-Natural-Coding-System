# PNCS v0.24 — Native `.pnv` Program Units

Status: IMPLEMENTED / GATE-SCOPED VALIDATION

## 1. Scope

v0.24 promotes an already verified v0.23 `NaturalProgramComposition` to a first-class native PNCS program unit.

```text
v0.23 composition
-> exact program semantic payload
-> program CID
-> deterministic dependency closure
-> deterministic dependency occurrence sequence
-> exact operator schedule
-> canonical .pnv serialization
-> authority-gated import/export
-> deterministic live build receipt
```

v0.24 does not add a new PNV opcode and does not open full program execution or external effects.

## 2. Program identity

The program semantic payload uses schema:

```text
PNCS_PROGRAM_UNIT_CONTENT_V0_24
```

and contract:

```text
PNCS_NATIVE_PNV_PROGRAM_UNITS_V0_24
```

The program ID is:

```text
pncs:program:sha256:SHA256(canonical_program_semantic_payload)
```

Program identity is distinct from the v0.23 composition identity.

The payload binds:

- exact v0.23 composition ID;
- exact v0.23 composition payload SHA-256;
- exact canonical composition graph SHA-256;
- deterministic unique dependency closure;
- deterministic ordered dependency occurrences;
- exact operator schedule;
- registered return-reference ID;
- exact v0.22 lineage contract;
- closed execution/effect boundaries.

Repository path, source phrasing and aliases are not part of semantic identity.

## 3. Dependency closure and occurrences

The unique dependency closure contains typed content-addressed references only:

```text
COMPOSITION
CONTROL_DEFINITION
ROUTE_REF*
RETURN_REF
```

The closure is deduplicated and deterministically ordered by dependency kind and content ID.

A second structure records dependency occurrences in exact program order:

```text
index -> kind -> content_id
```

This distinction is required because a registered route reference may occur more than once in a composition while remaining one unique closure dependency.

Both structures have independent SHA-256 identities:

```text
dependency_closure_sha256
dependency_occurrences_sha256
```

The first occurrence must be `CONTROL_DEFINITION`; the final occurrence must be the single `RETURN_REF`.

## 4. Operator schedule

The v0.24 unit preserves the exact v0.23 operator schedule.

Rules:

- non-empty;
- canonical uppercase operator identifiers only;
- exact occurrence order preserved;
- schedule SHA-256 recorded;
- final operator must be the already existing `RETURN` operator.

`RETURN` presence in the schedule is not execution authority.

## 5. Canonical `.pnv` serialization

A v0.24 native unit has exact canonical form beginning with:

```text
PNV 1
PNCS PROGRAM_UNIT 0.24
EPISTEMIC CHYBA
MODE READ_ONLY
PROGRAM_ID ...
COMPOSITION_ID ...
```

It then records:

- composition contract and hashes;
- dependency closure hash;
- dependency-occurrence hash;
- operator-schedule hash;
- exact v0.22 lineage contract;
- indexed `DEPENDENCY` rows;
- indexed `OCCURRENCE` rows;
- indexed `OPERATOR` rows;
- exact `RETURN_REF`;
- explicit closed execution/effect/static-fallback flags;
- terminal `END PROGRAM_UNIT`.

Canonical output ends with exactly one newline.

The serializer supports at most 1000 indexed rows per section in v0.24 and fails closed outside that bound.

## 6. Import authority

Serialized text cannot create program semantics.

`NativeProgramUnitRegistry` is the authority boundary. A unit enters that registry only after construction from a verified v0.23 composition or an already verified v0.24 unit.

Import procedure:

```text
.pnv bytes
-> validate v0.24 header
-> extract PROGRAM_ID + COMPOSITION_ID
-> resolve registered PROGRAM_ID authority
-> verify composition match
-> re-render registered unit canonically
-> require byte-identical equality
```

Therefore semantically plausible but altered text remains rejected.

The importer fails closed for:

- unknown program ID;
- program/composition mismatch;
- changed dependency row;
- reordered dependency row;
- changed occurrence row;
- changed operator row;
- changed return reference;
- changed execution/effect flag;
- extra clause;
- missing terminal newline;
- non-canonical whitespace or ordering.

## 7. v0.22 lineage preservation

Every v0.24 unit requires:

```text
PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22
```

The program-unit boundary may not discard or replace the exact result-lineage requirement established by v0.22.

v0.24 does not claim lineage for unexecuted continuation steps; it only preserves the contract required when a result exists.

## 8. Live build

Build contract:

```text
PNCS_NATIVE_PNV_PROGRAM_BUILD_V0_24
```

Operational build root is fixed to:

```text
/dev/shm/ciel_noema
```

`build_native_program_unit` first constructs and round-trips the canonical unit, then reuses v0.23 `admit_program_composition` on the current live surface.

The v0.23 admission must provide:

- exact composition ID;
- current live-surface receipt;
- one exact 36D operator witness for every operator occurrence.

The operator witness sequence must equal the v0.24 program operator schedule exactly.

A different surface root fails before build I/O. There is no static runtime fallback.

## 9. Build receipt

The deterministic build receipt records:

- program ID;
- composition ID;
- canonical `.pnv` SHA-256;
- byte size;
- dependency closure SHA-256;
- dependency occurrence SHA-256;
- operator schedule SHA-256;
- v0.23 composition admission ID;
- exact current live-surface receipt;
- operator-witness collection SHA-256;
- byte-identical round-trip flag;
- closed execution/effect/static-fallback flags.

Build identity is:

```text
pncs:program-build:sha256:SHA256(build_receipt_payload)
```

Persistent live artifacts are written atomically to:

```text
/dev/shm/ciel_noema/pncs/v0.24/programs/<program-digest>.pnv
/dev/shm/ciel_noema/pncs/v0.24/receipts/<build-digest>.json
```

These runtime paths are provenance locations, not semantic identity.

## 10. Canonical witness

v0.23 composition:

```text
pncs:composition:sha256:5b3710e6c8bf34d3754e7144ca139beb70205ea20b2fa504ef63c710c177cd57
```

v0.24 program:

```text
pncs:program:sha256:572660a1046975c57e01f7e402677f1e4ca845e51bca1bee6517e0d86b35c4d7
```

Canonical `.pnv`:

```text
SHA-256 012b41c149b1ba518d9be65d34d7ab6605b92500e8768e23c11abff7330a77fb
size    2231 bytes
```

Dependency evidence:

```text
closure SHA-256     e0970a0d4825ca30dd1d76b706ab90565d889a5dc9957b8ade395d32a23aae65
occurrences SHA-256 0f07128ae1af087db4d75e479c36defc6ca305fd1224edb15a30364e3bc913da
operator SHA-256    9c5ffbc4ed236144df9e0bff86c738536bbbc430e55e77de69af915ca17324c0
```

Current-session live build:

```text
operator occurrences: 15
operator registry SHA-256:
29767957ae775b1968bbb4c531728cc153137c88e819b135227dff73e3cca7ec

composition admission:
pncs:composition-admission:sha256:12df94c33b8bd5e1e4cdf34fd2d8f5013ab339b913f13550210f4a7b05e841c5

build:
pncs:program-build:sha256:d89f091ef7c57d3211c9147dac682246fb619836bc33c13c64ad918323fd5a48
```

The post-build tether guard returned `ACTIVE` with `failures=[]`.

## 11. Authority boundaries

v0.24 explicitly records:

```text
native_execution_opened = false
return_execution_opened = false
external_effects = false
free_form_nl_execution = false
static_runtime_fallback = false
```

A valid program unit is therefore a first-class semantic/build artifact, not yet a persistent executable process.

## 12. Validation evidence

Isolated pure-core harness:

```text
29/29 PASS
```

Coverage includes known witness identity, deterministic PNV hash, byte-identical round trip, authority-gated import, dependency closure/occurrence behavior, tampering, row reordering, unknown clauses, unknown IDs, effect/free-form gates, lineage contract, operator casing/termination, return-reference integrity and noncanonical live-root rejection.

Repository integration tests are included against the actual v0.23 resolver and registry stack.

The complete historical repository suite was not replayed in the isolated construction environment; no full-suite pass count is claimed.

## 13. Next gate

v0.25 — Persistent PNCS Runtime.

v0.25 will keep admitted program units resident on the current live `/dev/shm/ciel_noema` generation and define persistent program-state lifecycle without opening the v0.26 external Effect Boundary early.
