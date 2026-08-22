# PNCS v0.21 — Mass-Aware Graph Cost

Status: IMPLEMENTED / GATE-SCOPED VALIDATION

## 1. Scope

v0.21 adds a deterministic cost layer over already stabilized PNCS KAKU graphs. It consumes the exact semantic-mass binding introduced in v0.19 and does not modify semantic identity, canonical content IDs, 36D realization identity, execution admission, or effect authorization.

The cost layer is an optimization/admission observable only.

```text
canonical graph
-> explicit KAKU schedule
-> exact v0.19 mass witnesses
-> live /dev/shm/ciel_noema runtime provenance
-> graph cost
-> optional rewrite cost comparison
-> deterministic cost receipt
```

No semantic mass is inferred from CID, surface wording, vector similarity, operator name, node position, or graph topology.

## 2. Exact KAKU mass witness

Every costed KAKU must carry an explicit v0.19 `SemanticMassBinding` compatible witness.

For KAKU `q_i`, v0.21 verifies:

```text
q_i.phase == mass_binding_i.realization.phase
q_i.vector.basis_id == mass_binding_i.realization.basis_id
q_i.semantic_mass == mass_binding_i.semantic_mass
mass_binding_i.verify() == PASS
```

The KAKU `role` is the canonical PNV operator ID used by the expanded graph leaf schedule.

A missing witness fails closed. v0.21 never derives PhaseNav index `k` from a semantic content ID.

## 3. Exact mass units

v0.19 freezes semantic mass to ten decimal places. v0.21 therefore stores cost internally in exact integer mass units:

\[
    u_i = 10^{10} m_i
\]

where `u_i` must be an integer. The graph mass cost is

\[
    U_M(G) = \sum_{i=1}^{N(G)} u_i
\]

and the exposed scalar is

\[
    C_M(G) = 10^{-10} U_M(G).
\]

No extra coefficient, penalty constant, heuristic weight, or learned term is introduced in v0.21.

## 4. Cost scopes

The same mass functional is applied to four explicit scopes.

### RADICAL

All KAKU nodes present in a `RadicalGraph` are costed exactly once. Receipt ordering is deterministic by `kaku_id`; edge data is included in the graph digest but does not add mass because no relation-mass contract exists.

### PATH

A `CanonicalPath` is costed in exact `node_ids` order. Repeated KAKU IDs are repeated cost occurrences.

### PROGRAM

A content-addressed Definition program is costed against its exact expanded `leaf_path`. The caller supplies an ordered KAKU-ID schedule, and every witness `operator_id` must match the corresponding canonical leaf operator exactly.

### PREDICATE

Pure Boolean predicate graphs are costed in exact expanded leaf order. This scope is used by the v0.21 distributivity gate.

## 5. Duplication observables

For an ordered costed graph with KAKU IDs `q_1,...,q_N`, v0.21 records:

```text
node_count
unique_kaku_count
duplicate_node_count
duplicate_mass_units
total_mass_units
total_mass
```

The duplication mass is the sum of masses of repeated occurrences after the first occurrence of each exact KAKU ID.

This observable detects graph expansion without declaring that every repetition is semantically unnecessary. Growth becomes `UNJUSTIFIED_GROWTH` only when an equivalent rewrite increases nodes or mass and no explicit growth budget authorizes it.

## 6. Semantic identity boundary

Graph cost is not part of semantic identity.

```text
semantic_identity_affected = false
semantic_equivalence_from_cost = false
```

Two graphs with equal cost are not thereby semantically equivalent. Two semantically equivalent graphs may have different cost.

`cost_id` addresses only the cost record. It does not replace or modify a PNCS content ID.

## 7. Live PhaseNav runtime boundary

The operational cost surface is fixed to:

```text
/dev/shm/ciel_noema
```

`live_cost_context()` reuses the v0.20 live-surface admission contract and records:

- live PhaseNav operator-registry SHA-256;
- live tether receipt SHA-256;
- exact live operator-ID set;
- `static_runtime_fallback = false`.

Every costed KAKU role must exist in the live PhaseNav operator registry. Reference tests may inject a deterministic `CostRuntimeContext`, but this is not an operational static fallback.

## 8. Pure Boolean equivalence evidence

Cost never proves a rewrite correct.

For the pure predicate subset, v0.21 provides an independent complete Boolean truth-table proof over canonical comparison atoms. Each comparison canonical tuple is treated as a Boolean atom. This is conservative and sufficient for Boolean identities such as distributivity.

The evidence record binds:

```text
source_graph_sha256
target_graph_sha256
equivalent
method = PURE_BOOLEAN_COMPLETE_TRUTH_TABLE_V0_21
atom_count
valuation_count
counterexample (if any)
```

The default proof limit is 12 distinct Boolean atoms. Larger graphs fail closed rather than silently sampling valuations.

## 9. One-step distributive candidate

v0.21 admits a deterministic one-step candidate generator for pure predicate roots:

\[
A \land (B \lor C)
\rightarrow
(A \land B) \lor (A \land C)
\]

and its dual:

\[
A \lor (B \land C)
\rightarrow
(A \lor B) \land (A \lor C).
\]

The candidate generator itself does not authorize the rewrite.

## 10. Exact KAKU reuse rule for distributivity

A distributive rewrite may reorder or duplicate existing exact KAKU witnesses, but it may not introduce or substitute a different KAKU witness set merely to change cost.

For source witness set `W_s` and target witness set `W_t`:

\[
    W_t = W_s
\]

as sets of exact KAKU IDs.

Multiplicity may increase. This is where distributive graph growth becomes measurable.

A target that replaces a source KAKU with a cheaper KAKU fails closed before budget evaluation.

## 11. Rewrite deltas

For source graph `G` and independently proven-equivalent candidate `G'`:

\[
    \Delta N = N(G') - N(G)
\]

\[
    \Delta U_M = U_M(G') - U_M(G).
\]

The default growth budget is

\[
    B_N = 0, \qquad B_M = 0.
\]

Therefore any positive graph growth is rejected by default.

## 12. Explicit growth budget

A positive budget is represented by:

```text
max_added_nodes
max_added_mass_units
justification
```

Any positive budget requires a non-empty explicit justification. There is no implicit optimization budget.

An equivalent rewrite is admitted only when:

\[
    \Delta N \le B_N
\]

and

\[
    \Delta U_M \le B_M.
\]

Classification is deterministic:

```text
NON_EQUIVALENT
NON_GROWING_EQUIVALENT
BUDGETED_GROWTH
UNJUSTIFIED_GROWTH
BUDGET_EXCEEDED
```

## 13. Algebraic safety rule

The v0.21 invariant is:

```text
algebraic graph growth
-> independent semantic-equivalence evidence
-> exact source/target KAKU mass cost
-> exact witness-set check for distributivity
-> explicit growth budget
-> admission or fail closed
```

No algebraic transformation may increase the graph merely because it is symbolically legal.

## 14. Deterministic receipts

Every graph-cost record has:

```text
pncs:graph-cost:sha256:<digest>
```

and a deterministic receipt containing:

- scope;
- subject ID;
- graph SHA-256;
- ordered mass witness IDs;
- ordered KAKU IDs;
- operator IDs;
- exact integer mass units;
- duplication observables;
- total mass;
- live runtime provenance;
- explicit non-authority flags.

Rewrite admission has an independent SHA-256 receipt over source/target cost IDs, equivalence evidence, deltas, budget, classification and verdict.

## 15. Failure semantics

v0.21 fails closed for at least:

- missing explicit KAKU mass witness;
- mass/phase/basis mismatch;
- mass precision outside the frozen v0.19 ten-decimal contract;
- KAKU role not equal to a canonical PNV operator ID;
- operator absent from the live PhaseNav registry;
- path/program witness-count mismatch;
- canonical leaf/operator schedule mismatch;
- Boolean equivalence proof above the configured atom bound;
- non-equivalent rewrite;
- equivalence evidence not bound to the exact source/target graph digests;
- source/target costs from different runtime snapshots;
- distributive target with a substituted/new KAKU witness set;
- positive growth without explicit budget;
- growth exceeding node or mass budget.

## 16. Validation evidence

During branch construction:

- isolated v0.21 logic harness: `14/14 PASS`;
- module/test syntax compilation: PASS;
- NOEMA/AUX tether guard: `ACTIVE`, `failures=[]`;
- live PhaseNav operator registry: 36 operators;
- required PNCS leaf operators present on the live surface;
- static runtime fallback: false;
- new PNV opcodes: 0.

A repository integration test file using the real v0.18/v0.19 binding classes is included. The complete historical repository suite has not been replayed in the isolated construction environment, so no full-suite pass count is claimed by this receipt.

## 17. Next gate

v0.22 — Exact Inverse Execution Lineage.

The execution result must become exactly traceable through the content-addressed hierarchy back to Definition, Radical and KAKU without relying on runtime location or incidental process state.
