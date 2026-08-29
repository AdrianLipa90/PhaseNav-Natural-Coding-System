# PNCS FPDG GREMLIN Pain Ingress v0.1

Status: `FPDG_EXACT_PAIN_WITNESS -> EXPLICIT_GRAMMAR_BINDING -> EXISTING_GREMLIN_RELATION_MINING / FAIL_CLOSED`

## Purpose

Connect the exact inconsistency-localization output from `Fundamental-Physics-Dependency-Graph` to the existing PNCS GREMLIN relation-mining and relational-isomorphism compiler.

The integration reuses the implemented PNCS contracts rather than creating a second GREMLIN compiler:

```text
FPDG_GREMLIN_PAIN_PACKET_V0_1
    -> reviewed witness-chain selection
    -> explicit claim_id -> grammar atom binding
    -> explicit source-domain binding when ambiguous
    -> explicit cross-chain alignment
    -> PNCS_RELATION_MINING_LEDGER_V0_3
    -> RelationMiningFinding
    -> PNCS_GREMLIN_KAKU_RESOLVER_V0_1
    -> PNCS_GREMLIN_RELATION_MINING_ADAPTER_V0_1
    -> PNCS_GREMLIN_RELATIONAL_ISOMORPHISM_COMPILER_V0_1
    -> RADICAL + native PNV OPERATORS
    -> READ_ONLY candidate program
```

## Authority firewall

The FPDG packet is admitted only when all of these fields are exact:

```text
epistemic = CHYBA
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
vector_guessing_allowed = false
candidate_edges_enter_canon = false
```

Any attempted authority escalation fails closed at ingress.

## Claim IDs are coordinates, not KAKU atoms

An FPDG identifier such as:

```text
RFC.E20.TETRA_CLOCK_MASS_SCALE
```

is a dependency-graph coordinate. It is never silently reinterpreted as a PNCS grammar atom or KAKU semantic identity.

Every selected claim occurrence must first receive an explicit reviewed binding:

```text
claim_id -> grammar atom
```

For example, a reviewer may explicitly bind two independently observed frontier roles to a shared historical grammar atom such as `BOUNDARY`. That binding is recorded in the ingress receipt. Missing bindings fail closed.

The next gate is still the canonical GREMLIN KAKU resolver. The ingress adapter never constructs or guesses a vector, phase, semantic mass, polarity or direction.

## Multiple incidents and domains

The adapter accepts a mapping of named FPDG pain packets. This allows a current incident and one or more reviewed historical incidents to be presented together without collapsing provenance.

Raw FPDG chain IDs are namespaced as:

```text
FPDG.<PACKET_ID>.<RAW_CHAIN_ID>
```

A chain may use its packet-declared domain only when the zone has exactly one domain. Zero or multiple domain hints require an explicit `chain_domains` binding.

The selected relation-mining set must contain at least two chains spanning at least two distinct source domains.

## Explicit alignment

Recurrence or signature similarity alone never becomes `ISOMORPHIC_TO`.

The reviewer/GREMLIN finding must identify exact chain positions:

```text
left_chain_id
left_claim_index
right_chain_id
right_claim_index
relation_type = ISOMORPHIC_TO
```

The adapter verifies both indices and verifies that the alignment crosses distinct domains before creating the existing `RelationMiningAlignment` object.

## Ingress receipt

`PNCS_FPDG_GREMLIN_PAIN_INGRESS_RECEIPT_V0_1` records:

```text
exact FPDG packet hashes
selected namespaced chain IDs
explicit chain-domain bindings
explicit claim_id -> grammar atom bindings
explicit cross-chain alignments
finding/invariant IDs
claim_ids_are_kaku_atoms = false
vector_guessing_allowed = false
canonical_kaku_resolution_required = true
single_exact_36d_basis_required = true
```

The receipt remains `CHYBA / CANDIDATE_ONLY` and carries no runtime or canon write authority.

## Integration-only pain

An FPDG incident localized only to integration metadata, for example `FPDG.SOURCE_HEAD_LOCK.RFC`, has no scientific claim witness chain. The adapter refuses to fabricate one.

Such incidents remain valid exact integration diagnostics and may be compared in FPDG incident memory, but they do not enter PNCS relational compilation until explicit relational evidence exists.

## Existing GREMLIN path

Once the explicit grammar binding and canonical KAKU resolution gates pass, the adapter calls the existing implementation:

```text
compile_relation_mining_with_resolver(...)
```

Therefore the final compilation inherits the current GREMLIN guarantees:

```text
one exact PNCS 36D basis
explicit relation lowering
RADICAL candidate
native PNV operator schedule
READ_ONLY candidate execution
external_effects = false in conformance execution
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
```
