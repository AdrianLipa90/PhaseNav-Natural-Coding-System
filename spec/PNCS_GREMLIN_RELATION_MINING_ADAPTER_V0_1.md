# PNCS GREMLIN Relation-Mining Adapter v0.1

Status: `RELATION_MINING_TO_KAKU_GRAPH_IMPLEMENTED / EXPLICIT_ALIGNMENT_REQUIRED / VECTOR_GUESSING_BLOCKED`

## Purpose

Bind the existing PNCS relation-mining ledger to the GREMLIN relational-isomorphism compiler without inventing a second mining format.

The path is:

```text
PNCS_RELATION_MINING_LEDGER_V0_3
    + GREMLIN explicit finding/alignment
    + canonical KAKU resolver
    -> RelationalIsomorphism
    -> KAKU occurrences
    -> RADICAL
    -> native PNV OPERATORS
    -> PNV candidate program
```

## Existing mining authority

The adapter consumes the established ledger schema:

```text
PNCS_RELATION_MINING_LEDGER_V0_3
```

Each selected chain contributes its declared:

```text
id
source
status
atoms[]
```

The ledger remains evidence/provenance for mined recurrence. Recurrence remains separate from semantic mass.

## Explicit GREMLIN finding

A finding contains:

```text
finding_id
invariant_id
invariant_description
chain_ids[]
alignments[]
evidence_refs[]
```

An alignment is explicit:

```text
left_chain_id
left_atom_index
right_chain_id
right_atom_index
relation_type = ISOMORPHIC_TO
```

The adapter requires at least two selected chains, at least two distinct source domains, and at least one explicit cross-domain alignment.

Shared recurrence alone is insufficient for an isomorphism edge. GREMLIN must identify the candidate correspondence explicitly.

## KAKU resolution gate

Every atom appearing in every selected source chain must resolve through an explicit `atom -> Kaku` mapping before compilation.

```text
missing atom mapping -> FAIL CLOSED
mixed 36D basis      -> FAIL CLOSED
non-KAKU mapping     -> FAIL CLOSED
```

The adapter never fabricates a 36D vector, phase, semantic mass, direction or polarity.

For each resolved atom occurrence, the exact KAKU realization is preserved while the occurrence receives a unique lineage ID:

```text
RM.<CHAIN>.<INDEX>.<ATOM>
```

This allows one canonical grammar atom to occur in multiple source chains without collapsing provenance.

## Historical grammar atoms and native execution

The v0.3 grammar-mining layer contains semantic atoms such as:

```text
DERIVE
RESOLVE
BOUNDARY
NEGATION
```

These remain legitimate KAKU/grammar atoms. The current native PNV executor has a smaller executable opcode set.

The adapter therefore represents historical grammar atoms as KAKU nodes and encodes graph structure using the admitted native PNV operators. It does not expand the executor opcode vocabulary as a side effect of mining.

Intra-chain succession becomes:

```text
ORDER(node_i, node_i+1)
```

Cross-domain GREMLIN alignment becomes, by default:

```text
COMPOSITION(node_left, node_right)
```

through the relational compiler's `ISOMORPHIC_TO -> COMPOSITION` lowering.

## Resulting graph

For two mined chains:

```text
A0 -> A1 -> A2
           |
           | ISOMORPHIC_TO
           v
B0 -> B1 -> B2
```

the adapter generates occurrence KAKU nodes, `ORDER` edges within each source chain, and an explicit cross-domain alignment edge. The relational compiler then materializes the RADICAL and native PNV operator schedule.

## Epistemic discipline

Generated objects remain:

```text
EPISTEMIC CHYBA
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
```

The author/repository/formalism/code may suggest that two mined source paths share an invariant relational structure, yet does not state that correspondence as an established result until the explicit alignment and its evidence pass the relevant validation and promotion gates.

## Live state

Repository-level adapter and compiler logic are implemented. The current live `/dev/shm/ciel_noema` hydration must expose the GREMLIN state/witness required by `open_gremlin_pnv_authoring_live()` before the live persistence path can be admitted.

Static or repository artifacts remain provenance inputs and are not substituted for a missing live GREMLIN state.
