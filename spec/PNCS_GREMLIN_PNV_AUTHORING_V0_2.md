# PNCS GREMLIN ↔ PNV Authoring v0.2

Status: `CANDIDATE_AUTHORING_IMPLEMENTED / RELATIONAL_COMPILER_ATTACHED / CANON_PROMOTION_GATED / LIVE_GREMLIN_HYDRATION_OPEN`

## Purpose

This contract extends the existing GREMLIN ↔ native PNV bridge with a bounded authoring plane for coding and relational discovery.

GREMLIN may materialize three PNCS candidate object classes:

1. `KAKU` — an atomic 36D semantic stroke,
2. `RADICAL` — a directed graph whose nodes are content-addressed KAKU candidates,
3. `OPERATOR` — a native PNV operator candidate whose opcode belongs to the admitted PNV1 executor vocabulary.

The candidate dependency chain is

```text
GREMLIN relation-mining finding
    -> KAKU*
    -> RADICAL
    -> OPERATOR*
    -> rendered PNV candidate program
```

Promotion to canonical registries and runtime execution remain separate gated actions.

## Live binding

The live authoring entry point is bound to:

```text
/dev/shm/ciel_noema
```

and requires the same live surface/socket freshness checks used by the native GREMLIN bridge. Identity, authority and the GREMLIN triple-pulse generation binding are read from the active NOEMA surface.

The live candidate store is:

```text
/dev/shm/ciel_noema/gremlin/candidates/pncs/
  kaku/<sha256>.json
  radical/<sha256>.json
  operator/<sha256>.json
  compilation/<receipt_sha256>.json
```

Each object is append-only and content-addressed. An already existing byte-identical object is an idempotent write. A path/content collision fails closed.

The repository implementation is complete at the candidate-authoring layer. A live call to `open_gremlin_pnv_authoring_live()` additionally requires the hydrated GREMLIN state/witness under the canonical NOEMA surface. If that state is absent, the live authoring entry remains blocked rather than substituting repository/static state.

## Candidate envelope

Every authored object carries:

```text
epistemic                    = CHYBA
promotion_state              = CANDIDATE_ONLY
runtime_execution_authority  = false
canon_write_authority        = false
```

and binds generation, identity, authority, evidence, dependencies and content into a content-addressed candidate ID.

## KAKU authoring

KAKU follows the existing PNCS KAKU contract:

```text
K = (v36, phase, mass, direction, polarity, role)
```

The authoring layer serializes the exact 36D vector and optional exact 36D phase vector together with `basis_id`, semantic mass, direction, polarity and role. Existing `Kaku` / `Vector36` integrity checks remain authoritative for dimensionality and finiteness.

GREMLIN relation-mining adapters resolve semantic atoms through explicit canonical KAKU objects. Missing or invalid mappings fail closed; 36D realizations are never fabricated by the adapter.

## RADICAL authoring

A RADICAL candidate binds exactly one candidate KAKU ID for every graph node and records its directed relations. `write_radical()` materializes constituent KAKU candidates first and then writes the content-addressed RADICAL that references them.

## OPERATOR authoring

An OPERATOR candidate has:

```text
(name, opcode, args, radical_candidate_id?)
```

The opcode must belong to the current native PNV1 executor vocabulary:

```text
SOURCE
IDENTITY
DIFFERENCE
CONDITION
ORDER
TRANSFORM
COMPOSITION
RETURN
```

Historical grammar-mining atoms such as `DERIVE`, `RESOLVE`, `BOUNDARY` and `NEGATION` may remain semantic KAKU nodes. They do not become executable opcodes as a side effect of GREMLIN mining.

Multiple OPERATOR candidates can be rendered into native PNV text and are passed through the canonical native `parse_pnv()` parser before return.

## Relational-isomorphism compilation

The v0.2 bridge exposes:

```text
compile_relational_isomorphism()
compile_relational_isomorphism_live()
validate_compiled_relational_candidate()
```

A GREMLIN finding supplies an invariant candidate, domain-tagged KAKU nodes and explicit relational edges. The compiler deterministically lowers those relations into the native PNV subset, builds the RADICAL and OPERATOR schedule, and records a content-addressed compilation receipt.

The relation-mining adapter additionally exposes:

```text
relation_mining_finding_to_isomorphism()
compile_relation_mining_finding()
```

which consume `PNCS_RELATION_MINING_LEDGER_V0_3` together with explicit cross-domain alignments and an exact `atom -> Kaku` resolver.

## Authority boundary

The coding path is:

```text
GREMLIN relational mining
    -> explicit invariant/alignment candidate
    -> exact KAKU resolution
    -> RADICAL candidate
    -> OPERATOR candidates
    -> native PNV parse/conformance
    -> admission gate
    -> optional canonical promotion
    -> runtime execution
```

This preserves GREMLIN as the generator/auditor while PNV remains the executable language and the existing PNCS admission lineage remains the authority boundary.

## Coding use

A discovered relational isomorphism can now be compiled incrementally rather than flattened immediately into source text. The same mechanism can carry IDT/RFC/TIR law-frame paths with explicit KAKU/RADICAL/OPERATOR provenance.

## Conformance requirements

Repository-level construction is covered by tests for:

- exact 36D KAKU validation,
- content-addressed append-only persistence,
- idempotent replay,
- hash-tamper rejection,
- exact RADICAL node dependency closure,
- deterministic relation serialization,
- native PNV opcode restriction,
- valid native PNV rendering/parsing,
- explicit cross-domain relation-mining alignment,
- fail-closed missing/invalid KAKU resolution,
- fail-closed basis mismatch,
- pure conformance execution with `external_effects=false`,
- fail-closed authority flags,
- live authoring entry bound to `/dev/shm/ciel_noema`.

GitHub Actions execution status is provenance recorded separately from implementation status. A pre-run infrastructure failure is not promoted to either code PASS or code FAIL.
