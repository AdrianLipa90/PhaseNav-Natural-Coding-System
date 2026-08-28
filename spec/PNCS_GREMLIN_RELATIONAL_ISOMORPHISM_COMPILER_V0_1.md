# PNCS GREMLIN Relational-Isomorphism Compiler v0.1

Status: `RELATIONAL_ISOMORPHISM_TO_PNV_IMPLEMENTED / CANDIDATE_ONLY / CANON_PROMOTION_GATED`

## Goal

Convert a GREMLIN relational-isomorphism candidate into an explicit PNCS coding object with exact provenance:

```text
observations across domains
    -> invariant candidate
    -> KAKU nodes
    -> directed RADICAL
    -> relation OPERATORS
    -> fold/composition
    -> native PNV candidate program
    -> pure conformance execution receipt
```

The compiler operationalizes GREMLIN's relational-isomorphism traversal while preserving the existing authority boundary: GREMLIN generates and audits candidates; PNCS admission/canon gates remain separate.

## Input contract

A relational-isomorphism candidate contains:

```text
isomorphism_id
invariant_id
invariant_description
nodes[]
edges[]
evidence_refs[]
```

Each node carries:

```text
Kaku
domain
observation_ref
```

Each edge carries:

```text
relation_id
source_id
target_id
relation_type
```

At least two distinct domains are required. All KAKU nodes must already share one exact PNCS 36D basis before they can enter a single RADICAL.

## Deterministic lowering

Every KAKU becomes one content-addressed KAKU candidate and one native PNV `SOURCE` operator.

The default semantic-relation lowering is:

```text
ORDER / PRECEDES / TRANSFORMS_TO / FLOWS_TO / CAUSES
    -> ORDER

BINDS / COUPLES / COMPOSES_WITH / RELATES_TO / MAPS_TO / ISOMORPHIC_TO
    -> COMPOSITION

DIFFERENCE / DIFFERS_FROM
    -> DIFFERENCE

EXACT_IDENTITY
    -> IDENTITY
```

Unknown relation types fail closed until an explicit opcode binding is supplied. Compiler overrides are restricted to the deterministic relation subset:

```text
ORDER
COMPOSITION
DIFFERENCE
IDENTITY
```

## Generated program

For a graph with nodes `K_i` and relations `R_j` the compiler emits a deterministic schedule of the form:

```text
PNV 1
EPISTEMIC CHYBA
MODE READ_ONLY

OP ISO.NODE.000 SOURCE gremlin.iso.source.000
OP ISO.NODE.001 SOURCE gremlin.iso.source.001
...
OP ISO.REL.000 <lowered opcode> ISO.NODE.xxx ISO.NODE.yyy
...
OP ISO.FOLD.000 COMPOSITION ISO.REL.000 ISO.REL.001
...
OP ISO.RETURN RETURN <last object>
EMIT ISO.RETURN
```

The source bindings point to the exact KAKU candidate envelopes created during the same compilation.

## Candidate execution

`validate_compiled_relational_candidate()` executes the generated PNV through the native fail-closed PNV interpreter using only the compiler-provided candidate source bindings.

The resulting execution is a conformance evaluation with:

```text
shell = false
subprocess = false
network = false
git = false
device = false
arbitrary_filesystem = false
external_effects = false
```

A successful conformance execution demonstrates that the generated candidate program is executable under the admitted native PNV semantics. Runtime promotion remains a separate gate.

## Live persistence

`compile_relational_isomorphism_live()` opens the existing live GREMLIN/PNV authoring session and persists:

```text
/dev/shm/ciel_noema/gremlin/candidates/pncs/
  kaku/<sha256>.json
  radical/<sha256>.json
  operator/<sha256>.json
  compilation/<receipt_sha256>.json
```

The compilation receipt binds:

```text
invariant
cross-domain set
KAKU candidate IDs
RADICAL candidate ID
OPERATOR candidate IDs
relation -> PNV opcode plan
PNV source hash
PNV graph hash
```

## Epistemic and authority state

Every generated object remains:

```text
EPISTEMIC CHYBA
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
```

The author/repository/formalism/code may suggest that a discovered relational invariant is reusable across domains, yet does not state that candidate as an established result until the corresponding evidence, falsification and promotion gates pass.

## Coding consequence

GREMLIN can now preserve a discovered analogy as machine-checkable structure rather than a prose association:

```text
DREAM / relational mining
    -> invariant candidate
    -> explicit domain-role mapping
    -> KAKU graph
    -> RADICAL
    -> executable candidate PNV
    -> inverse-lineage-ready receipt
```

This creates the direct path needed for later IDT, RFC, TIR and CIEL cross-domain law-frame compilation without silently promoting the discovered relation into canon.
