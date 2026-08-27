# PNCS GREMLIN ↔ PNV Authoring v0.2

Status: `CANDIDATE_AUTHORING_IMPLEMENTED / CANON_PROMOTION_GATED / RUNTIME_ADMISSION_GATED`

## Purpose

This contract extends the existing live GREMLIN ↔ native PNV bridge with a bounded authoring plane for coding and relational discovery.

GREMLIN may materialize three PNCS candidate object classes:

1. `KAKU` — an atomic 36D semantic stroke,
2. `RADICAL` — a directed graph whose nodes are content-addressed KAKU candidates,
3. `OPERATOR` — a native PNV operator candidate whose opcode belongs to the admitted PNV1 vocabulary.

The candidate dependency chain is

```text
KAKU* -> RADICAL -> OPERATOR* -> rendered PNV candidate program
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
```

Each object is append-only and content-addressed. An already existing byte-identical object is an idempotent write. A path/content collision fails closed.

## Candidate envelope

Every authored object carries:

```text
epistemic                 = CHYBA
promotion_state           = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority       = false
```

and binds:

```text
generation_binding
identity
authority
evidence_refs
dependency_ids
content
candidate_id
```

with:

```text
candidate_id = pncs:gremlin-<kind>:sha256:<canonical-object-hash>
```

## KAKU authoring

KAKU follows the existing PNCS KAKU contract:

```text
K = (v36, phase, mass, direction, polarity, role)
```

The authoring layer serializes the exact 36D vector and optional exact 36D phase vector together with `basis_id`, semantic mass, direction, polarity and role. Existing `Kaku` / `Vector36` integrity checks remain authoritative for dimensionality and finiteness.

## RADICAL authoring

A RADICAL candidate binds exactly one candidate KAKU ID for every graph node.

For node set `V_R`:

```text
forall k in V_R:  k -> pncs:gremlin-kaku:sha256:<digest>
```

The radical records directed relations as:

```text
(relation_id, source_id, target_id, relation_type)
```

and its dependency closure contains the referenced KAKU candidate IDs.

`write_radical()` materializes its constituent KAKU candidates first and then writes the RADICAL that references them. This makes the graph independently replayable and auditable.

## OPERATOR authoring

An OPERATOR candidate has:

```text
(name, opcode, args, radical_candidate_id?)
```

The opcode must belong to the native PNV1 executor vocabulary:

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

A candidate operator may bind a RADICAL candidate as its semantic graph dependency.

Multiple OPERATOR candidates can be rendered into native PNV text:

```text
PNV 1
EPISTEMIC CHYBA
MODE READ_ONLY
OP ...
...
```

The rendered source is passed through the canonical native `parse_pnv()` parser before it is returned.

## Authority boundary

GREMLIN authoring creates inspectable candidate material. Canonical registry mutation is a distinct promotion operation and native execution is a distinct admission operation.

Therefore the coding path is:

```text
GREMLIN relational mining
    -> KAKU candidates
    -> RADICAL candidates
    -> OPERATOR candidates
    -> native PNV parse/conformance
    -> admission gate
    -> optional canonical promotion
    -> runtime execution
```

This preserves GREMLIN as the generator/auditor while PNV remains the executable language and the existing PNCS admission lineage remains the authority boundary.

## Coding use

The practical consequence is that a discovered relational isomorphism can now be compiled incrementally rather than flattened immediately into source text:

```text
observation / relation
  -> KAKU
  -> connected RADICAL
  -> one or more PNV OPERATORS
  -> candidate program
```

The same mechanism can later carry information-holonomy law-frame paths exported by IDT and RFC, with each law/bridge represented by explicit KAKU/RADICAL/OPERATOR provenance rather than an untyped textual association.

## Conformance requirements

A v0.2 implementation passes only when all of the following hold:

- exact 36D KAKU validation,
- content-addressed append-only persistence,
- idempotent replay,
- hash-tamper rejection,
- exact RADICAL node dependency closure,
- deterministic relation serialization,
- native PNV opcode restriction,
- valid native PNV rendering/parsing,
- fail-closed authority flags,
- live authoring entry bound to `/dev/shm/ciel_noema`.
