# PNCS GREMLIN Candidate Inverse Lineage v0.1

Status: `RESULT_TO_OPERATOR_RADICAL_KAKU_PASS / EXPLICIT_CONTENT_JOIN_AVAILABLE / V22_CANONICAL_JOIN_GATED / LIVE_GREMLIN_HYDRATION_OPEN`

## Purpose

This contract adds deterministic inverse provenance for GREMLIN-authored native PNV candidate programs.

The forward path is:

```text
GREMLIN finding
  -> KAKU candidates
  -> RADICAL candidate
  -> OPERATOR candidates
  -> native PNV candidate program
  -> pure conformance result
```

The inverse path is:

```text
native PNV result
  -> emitted root OPERATOR
  -> dependent OPERATOR candidates
  -> RADICAL candidate
  -> KAKU candidates
  -> explicit content IDs and evidence refs
```

The inverse receipt is content-addressed and remains under `CHYBA / CANDIDATE_ONLY` until a separate admission/promotion gate acts on the candidate material.

## Relation to PNCS v0.22

`PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22` is the canonical execution-lineage contract for admitted PNCS Definition execution and reconstructs:

```text
RESULT
  -> SYSTEM
  -> HIGH_ORCHESTRATOR
  -> LOW_ORCHESTRATOR
  -> SUBSYSTEM|DAEMON
  -> CLUSTER
  -> FILE
  -> CLASS
  -> DEFINITION
  -> RADICAL
  -> KAKU
```

GREMLIN candidate inverse lineage occupies the pre-promotion candidate layer. Its join key into v0.22 is an explicitly carried PNCS content ID.

```text
GREMLIN candidate lineage
    -> explicit content_id
    -> admission/promotion
    -> PNCS v0.22 canonical lineage
```

The receipt therefore reports one of:

```text
v22_join_state = CONTENT_ID_AVAILABLE
v22_join_state = CONTENT_ID_OPEN
```

This keeps the candidate and canonical lineage contracts distinct while providing an exact bridge when semantic provenance is already explicit.

## Execution binding

The inverse resolver accepts exactly:

```text
RelationalCompilation
NativePNVExecutionResult
```

It verifies the native execution receipt:

```text
schema = PNCS_NATIVE_PNV_EXEC_RECEIPT_V0_1
receipt_sha256 = SHA256(canonical receipt body)
program_source_sha256 == compilation.pnv_source_sha256
program_graph_sha256  == compilation.pnv_graph_sha256
external_effects      == false
```

The runtime trace must contain exactly the parsed PNV operator set and every trace row carries a valid result SHA-256.

## OPERATOR inverse graph

The inverse traversal begins at the program `EMIT` roots. For the relational compiler this is normally:

```text
ISO.RETURN
```

For every candidate OPERATOR the resolver verifies:

```text
candidate schema/kind
candidate content hash
CHYBA / CANDIDATE_ONLY state
runtime_execution_authority = false
canon_write_authority = false
radical_candidate_id = compiled RADICAL candidate id
candidate opcode/args = parsed native PNV opcode/args
```

Operator arguments that name another compiled OPERATOR form exact inverse edges. A depth-first dependency traversal reconstructs only the subgraph reachable from the emitted result roots.

The inverse receipt records result hashes from the native PNV trace for every reachable operator.

## RADICAL closure

The compiled RADICAL must satisfy exact candidate closure:

```text
RADICAL.content.kaku_candidate_ids.keys
    == compilation.kaku_candidates.keys
```

and for every node:

```text
RADICAL[node_id] == exact KAKU candidate_id
```

The RADICAL dependency list must equal the sorted set of referenced KAKU candidate IDs. The compiler receipt must carry the same RADICAL candidate ID and the same node-to-candidate mapping.

## KAKU provenance

Each KAKU row records:

```text
node_id
candidate_id
basis_id
role
evidence_refs
explicit_content_ids
```

`explicit_content_ids` are extracted only from provenance strings that already contain a typed PNCS SHA-256 content ID, for example the resolver-produced role:

```text
gremlin_relation_atom:<ATOM>:pncs:def:sha256:<digest>
```

The semantic join authority is therefore explicit provenance. Numeric 36D realization remains an integrity/realization layer.

## Result identity

The deterministic lineage payload contains:

```text
schema = PNCS_GREMLIN_CANDIDATE_INVERSE_LINEAGE_V0_1
compilation_receipt_sha256
execution_receipt_sha256
emit_roots
operator_rows
radical_row
kaku_rows
explicit_content_ids
v22_join_state
epistemic = CHYBA
promotion_state = CANDIDATE_ONLY
```

Its content ID is:

```text
pncs:gremlin-candidate-lineage:sha256:<payload digest>
```

and the receipt schema is:

```text
PNCS_GREMLIN_CANDIDATE_INVERSE_LINEAGE_RECEIPT_V0_1
```

## Persistence

Offline/conformance persistence accepts an explicit authoring root and stores:

```text
<authoring_root>/lineage/<lineage_digest>.json
```

using content-addressed idempotence.

The unified bridge additionally exposes:

```text
persist_gremlin_candidate_inverse_lineage_live()
```

which first resolves an admitted `GremlinPNVAuthoringSession`. Operational live persistence therefore stays bound to the canonical GREMLIN authoring surface under:

```text
/dev/shm/ciel_noema/gremlin/candidates/pncs
```

Current repository status keeps live GREMLIN hydration as an explicit OPEN gate until the canonical GREMLIN state witness is hydrated on the live surface.

## Fail-closed gates

The v0.1 resolver rejects:

- tampered compilation receipt,
- tampered native execution receipt,
- PNV source or graph hash mismatch,
- external-effect execution receipts,
- candidate content-hash mismatch,
- candidate authority-boundary mismatch,
- candidate/program OPERATOR mismatch,
- missing EMIT root,
- trace/program operator mismatch,
- RADICAL/KAKU closure mismatch,
- RADICAL dependency mismatch,
- compiler-receipt candidate mismatch,
- emitted-value receipt mismatch,
- content-addressed lineage collision.

## Coding consequence

GREMLIN can now compile a relational finding forward and audit the resulting computation backward:

```text
finding
  -> KAKU
  -> RADICAL
  -> OPERATORS
  -> PNV
  -> result
  -> OPERATORS
  -> RADICAL
  -> KAKU
  -> content/evidence
```

This provides the provenance backbone required for later PNV information-holonomy loops, because every measured loop result can retain an exact inverse path to the relational atoms and evidence that generated it.
