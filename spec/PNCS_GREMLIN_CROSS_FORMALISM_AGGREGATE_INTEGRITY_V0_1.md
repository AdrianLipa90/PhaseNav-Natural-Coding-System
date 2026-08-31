# PNCS GREMLIN Cross-Formalism Aggregate Integrity v0.1

Status: `IMPLEMENTED_ON_DEBUG_BRANCH / HOSTED_CONFORMANCE_PENDING`

## Purpose

This contract binds the aggregate compilation manifest of the GREMLIN cross-formalism banks to the exact leaf `RelationalCompilation` objects that are presented for direct validation.

It applies to:

```text
gremlin_cross_formalism_bank_v02.py
gremlin_cross_formalism_round28_v01.py
```

The candidate state remains:

```text
epistemic = CHYBA
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
```

## Aggregate reconstruction

Compilation constructs the manifest from two exact components:

```text
source-pinned bank manifest
+
compiled_entries derived from current leaf compilations
```

Each `compiled_entries[isomorphism_id]` binds:

```text
receipt_sha256
radical_candidate_id
pnv_graph_sha256
```

Direct validation reconstructs this aggregate from the currently supplied leaf compilations and requires exact equality with the stored aggregate manifest before leaf execution validation begins.

## Keyset closure

The compilation mapping must contain exactly the isomorphism IDs declared by the corresponding source-pinned bank. Missing leaves, extra leaves, or non-`RelationalCompilation` values fail admission.

This prevents a caller from deleting or replacing a leaf and then presenting a rewritten aggregate that no longer represents the declared bank generation.

## Relationship to sealed bundles

The sealed-bundle layer already performs a deeper internal-holonomy audit over serialized candidate payloads, leaf receipts, PNV source/graph commitments and validation summaries.

The direct validator now enforces the same aggregate-to-leaf binding at the in-memory `CrossFormalismCompilation` / `Round28Compilation` boundary. Sealed-bundle validation remains an additional serialization and deterministic-replay boundary.

## Regression gates

The direct bank corpora include adversarial cases for:

```text
compiled_entries receipt/graph commitment tamper
missing leaf compilation
```

Both cases must fail before candidate execution validation can return a result set.

The existing bank formulas, source pins, classifications and falsification gates remain unchanged.
