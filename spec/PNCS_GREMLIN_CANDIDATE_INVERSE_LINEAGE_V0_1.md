# PNCS GREMLIN Candidate Inverse Lineage v0.1

Status: `RESULT_TO_OPERATOR_RADICAL_KAKU_PASS / EFFECT_BOUNDARY_PROPAGATED / V22_CANONICAL_JOIN_GATED`

## Purpose

This contract reconstructs inverse provenance for GREMLIN-authored native PNV candidate programs:

```text
native result
-> emitted OPERATOR root
-> dependent OPERATOR candidates
-> RADICAL candidate
-> KAKU candidates
-> explicit content IDs and evidence refs
```

The lineage remains `CHYBA / CANDIDATE_ONLY` and provides no automatic runtime or canon-write authority.

## Relation to PNCS v0.22

The candidate lineage carries explicit PNCS content IDs when they already exist in provenance. Its join state is:

```text
CONTENT_ID_AVAILABLE
CONTENT_ID_OPEN
```

An available content ID is the exact bridge key for a later admitted PNCS v0.22 canonical execution lineage.

## Execution binding

The resolver accepts a `RelationalCompilation` and a `NativePNVExecutionResult` and verifies:

```text
native receipt schema and receipt_sha256
program_source_sha256 == compilation pnv_source_sha256
program_graph_sha256 == compilation pnv_graph_sha256
result.program source/graph hashes == native receipt hashes
```

The runtime trace must cover exactly the parsed PNV operator set, and emitted-value commitments must equal the actual emitted values.

## Effect-boundary rule

Inverse provenance requires the native interpreter boundary itself to remain closed:

```text
interpreter_external_effects = false
```

The global execution boundary may then be one of two admitted states.

Callback-free execution:

```text
external_effects = false
external_effects_status = VERIFIED_NONE_WITHIN_INTERPRETER_BOUNDARY
callback_effects_verified = true
callbacks_invoked = []
callback_determinism_verified = true
```

Execution containing admitted Python callbacks:

```text
external_effects = null
external_effects_status = UNVERIFIED_CALLBACK_BOUNDARY
callback_effects_verified = false
callbacks_invoked = [non-empty bindings]
callback_determinism_verified = false
```

A reported positive external effect, malformed effect provenance, or inconsistent callback-determinism flag fails closed.

The lineage payload carries the summarized execution effect boundary. `deterministic_serialization=true` records deterministic content-addressed serialization. `deterministic_fields_only` follows the verified callback-determinism state rather than being asserted unconditionally.

## OPERATOR graph

Traversal starts at every EMIT root. Each reachable OPERATOR must preserve candidate schema/kind, candidate content hash, authority boundary, RADICAL dependency, and exact opcode/args equality with the parsed PNV program.

Each lineage OPERATOR row carries the execution trace result hash.

## RADICAL and KAKU closure

The RADICAL node map must equal the compiled KAKU candidate map exactly. Every RADICAL node reference must point to the exact KAKU candidate ID, its dependency list must close over the same KAKU set, and the compiler receipt must carry the same RADICAL/KAKU identities.

KAKU rows preserve:

```text
node_id
candidate_id
basis_id
role
evidence_refs
explicit_content_ids
```

Typed PNCS SHA-256 content IDs are extracted only from explicit provenance strings already attached to the candidate material.

## Identity

The lineage content ID is:

```text
pncs:gremlin-candidate-lineage:sha256:<payload digest>
```

and its receipt schema is:

```text
PNCS_GREMLIN_CANDIDATE_INVERSE_LINEAGE_RECEIPT_V0_1
```

The content-addressed payload includes the execution effect-boundary summary, so changing callback-boundary status changes the lineage identity.

## Persistence

Conformance persistence stores `<authoring_root>/lineage/<lineage_digest>.json` with idempotent content-addressed writes. Live persistence is admitted only through the GREMLIN live authoring surface under `/dev/shm/ciel_noema/gremlin/candidates/pncs`.

## Fail-closed gates

The resolver rejects tampered compilation or execution receipts, source/graph mismatch, interpreter-boundary effects, malformed callback-boundary provenance, reported external effects, candidate content/authority mismatch, candidate/program operator mismatch, missing EMIT roots, trace mismatch, RADICAL/KAKU closure mismatch, emitted-value mismatch, and content-addressed persistence collisions.
