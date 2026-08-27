# PNCS GREMLIN KAKU Resolver v0.1

Status: `EXPLICIT_SEMANTIC_BINDING / EXACT_36D_RESOLUTION / CANDIDATE_ONLY`

## Purpose

This contract closes the gap between GREMLIN relation-mining atoms and the exact PNCS `Kaku` objects required by the relational-isomorphism compiler.

The resolver chain is:

```text
GREMLIN atom name
    -> explicit atom/content binding
    -> exact RealizationBinding (phase36)
    -> exact SemanticMassBinding
    -> exact Vector36 + provenance
    -> Kaku
    -> relation-mining adapter
    -> relational compiler
    -> native PNV candidate program
```

The semantic identity enters at the explicit `atom -> content_id` binding. Numeric realization layers verify that binding and carry its exact PNCS realization.

## Inputs

Each `GremlinAtomKakuBinding` binds:

```text
atom
content_id
realization_binding_id
mass_binding_id
Vector36
vector_source_ref
direction
polarity
role
```

The resolver also receives the existing PNCS registries:

```text
RealizationRegistry
SemanticMassRegistry
```

No parallel realization or mass registry is introduced.

## Exact resolution gates

For atom `A`, content `C`, realization binding `R`, mass binding `M` and vector `V`, resolution requires:

```text
R.content_id == C
M.realization.binding_id == R.binding_id
M.realization.content_id == C
V.basis_id == R.basis_id
```

Then `materialize_kaku_mass()` creates the KAKU and `verify_kaku_mass()` rechecks its exact phase/mass binding.

The resulting identifier is:

```text
K.GREMLIN.<ATOM>
```

while the semantic role retains the explicit content ID in provenance.

## Semantic authority

The resolver records:

```text
semantic_authority          = EXPLICIT_ATOM_CONTENT_BINDING
vector_semantic_authority   = false
phase_semantic_authority    = false
mass_semantic_authority     = false
nearest_neighbor_resolution = false
```

Vector, phase and mass equality remain realization/integrity facts. Semantic naming is supplied explicitly by the atom/content bridge.

## Relation-mining integration

`required_relation_mining_atoms()` extracts the exact union of atoms required by selected relation-mining chains.

`resolve_relation_mining_kaku()` resolves that set through one admitted resolver.

`compile_relation_mining_with_resolver()` then passes the resulting exact `atom -> Kaku` mapping into `PNCS_GREMLIN_RELATION_MINING_ADAPTER_V0_1`, which builds the cross-domain isomorphism graph and invokes the relational compiler.

Thus the normal path becomes:

```text
RelationMiningFinding
  -> required atoms
  -> exact KAKU resolution
  -> occurrence KAKU cloning
  -> explicit cross-domain alignments
  -> RADICAL
  -> native PNV OPERATOR schedule
  -> ISO.RETURN
```

## Fail-closed cases

Resolution is rejected for:

- duplicate atom bindings,
- unbound atoms,
- missing realization bindings,
- missing mass bindings,
- atom/content mismatch,
- mass binding attached to another realization,
- semantic content mismatch between mass and realization,
- `Vector36` / phase-realization basis mismatch,
- malformed relation-mining chain selection.

## Receipt

`GremlinKakuResolver.deterministic_receipt()` records:

- atom set,
- explicit content IDs,
- exact realization binding IDs,
- exact semantic-mass binding IDs,
- exact vector basis/hash/source reference,
- resulting KAKU IDs and semantic masses,
- phase hash,
- semantic-authority boundaries,
- `EPISTEMIC CHYBA`,
- `CANDIDATE_ONLY`.

The receipt is deterministic and content-addressed by SHA-256 over canonical JSON.

## Authority boundary

KAKU resolution supplies candidate material to GREMLIN/PNV authoring. Canonical promotion and runtime execution remain downstream admission actions.
