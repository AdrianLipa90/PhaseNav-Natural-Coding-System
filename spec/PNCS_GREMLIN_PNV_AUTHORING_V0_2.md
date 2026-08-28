# PNCS GREMLIN ↔ PNV Authoring v0.2

Status: `CANDIDATE_AUTHORING_IMPLEMENTED / RELATIONAL_COMPILER_ATTACHED / EXACT_KAKU_RESOLVER_ATTACHED / INVERSE_LINEAGE_ATTACHED / INFORMATION_HOLONOMY_ATTACHED / CANON_PROMOTION_GATED / LIVE_GREMLIN_HYDRATION_OPEN`

## Purpose

This contract extends the GREMLIN ↔ native PNV bridge with a bounded authoring plane for coding, relational discovery, inverse provenance, and executable information-holonomy audits.

GREMLIN may materialize three PNCS candidate object classes:

1. `KAKU` — an atomic 36D semantic stroke,
2. `RADICAL` — a directed graph whose nodes are content-addressed KAKU candidates,
3. `OPERATOR` — a native PNV operator candidate whose opcode belongs to the admitted PNV1 executor vocabulary.

The forward candidate chain is

```text
GREMLIN relation-mining finding
    -> exact KAKU resolution
    -> KAKU*
    -> RADICAL
    -> OPERATOR*
    -> native PNV candidate program
    -> pure result
```

The inverse chain is

```text
native PNV result
    -> reachable OPERATOR candidates
    -> RADICAL
    -> KAKU candidates
    -> explicit content IDs / evidence
```

The physical-law extension is

```text
LAW_FRAME
    -> KAKU law nodes
    -> RADICAL closed topology
    -> TRANSFORM OPERATOR transports
    -> PNV execution
    -> information-holonomy receipt
    -> inverse lineage
```

Promotion to canonical registries and admitted runtime execution remain separate gated actions.

## Live binding

The live authoring entry point is bound to:

```text
/dev/shm/ciel_noema
```

and requires the same live surface/socket freshness checks used by the native GREMLIN bridge. Identity, authority and generation binding are read from the active NOEMA surface.

The live candidate store is:

```text
/dev/shm/ciel_noema/gremlin/candidates/pncs/
  kaku/<sha256>.json
  radical/<sha256>.json
  operator/<sha256>.json
  compilation/<receipt_sha256>.json
  lineage/<lineage_sha256>.json
  holonomy/<receipt_sha256>.json
```

Each object is append-only and content-addressed. Byte-identical replay is idempotent. A path/content collision fails closed.

The repository implementation is complete at the candidate-authoring layer. Live GREMLIN persistence additionally requires the hydrated GREMLIN state/witness under the canonical NOEMA surface. Until that witness is hydrated, the live authoring entry remains an explicit OPEN gate.

## Candidate envelope

Every authored object carries:

```text
epistemic                    = CHYBA
promotion_state              = CANDIDATE_ONLY
runtime_execution_authority  = false
canon_write_authority        = false
```

and binds generation, identity, authority, evidence, dependencies and content into a content-addressed candidate ID.

## KAKU authoring and resolution

KAKU follows the PNCS contract:

```text
K = (v36, phase, mass, direction, polarity, role)
```

The authoring layer serializes exact `Vector36`, optional exact 36D phase, semantic mass, direction, polarity and role.

Relation-mining atoms are resolved by `PNCS_GREMLIN_KAKU_RESOLVER_V0_1` through:

```text
explicit atom/content binding
  -> exact RealizationBinding
  -> exact SemanticMassBinding
  -> exact Vector36 + provenance
  -> KAKU
```

Semantic identity enters through the explicit atom/content bridge. Vector, phase and mass are exact realization/integrity layers.

## RADICAL authoring

A RADICAL candidate binds exactly one candidate KAKU ID for every graph node and records its directed relations. `write_radical()` materializes constituent KAKU candidates first and then writes the content-addressed RADICAL that references them.

## OPERATOR authoring

An OPERATOR candidate has:

```text
(name, opcode, args, radical_candidate_id?)
```

The opcode belongs to the current native PNV1 executor vocabulary:

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

Historical grammar-mining atoms such as `DERIVE`, `RESOLVE`, `BOUNDARY` and `NEGATION` remain semantic KAKU nodes while generated executable PNV uses the admitted native vocabulary.

## Relational-isomorphism compilation

The v0.2 bridge exposes deterministic relational compilation and relation-mining adaptation.

A relation-mining isomorphism candidate requires explicit cross-chain alignments spanning at least two distinct source domains. The adapter consumes `PNCS_RELATION_MINING_LEDGER_V0_3`, resolves all referenced atoms to exact KAKU objects, builds the cross-domain RADICAL and lowers relations to admitted native PNV operators.

This cross-domain requirement belongs to the relational-isomorphism mining contract.

## Candidate inverse lineage

`PNCS_GREMLIN_CANDIDATE_INVERSE_LINEAGE_V0_1` traces a pure candidate result backward from `EMIT` roots through exact operator dependencies to the compiled RADICAL and KAKU candidates.

The inverse receipt binds native execution hashes, candidate IDs, result hashes, evidence refs and any explicitly carried PNCS content IDs.

An explicit content ID provides the candidate join key into `PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22` after the separate admission/promotion gate.

## Physical-law frame and information holonomy

`PNCS_PNV_INFORMATION_HOLONOMY_V0_1` represents a physical-law scaffold as an executable PNV connection.

Law nodes are KAKU candidates, ordered transports are RADICAL relations plus native `TRANSFORM` operators, and the closed path is executed through `HOL.START -> HOL.EDGE.* -> HOL.RETURN`.

The holonomy contract admits:

```text
single-node self-loop
single-domain multi-node loop
cross-domain loop
```

Therefore local normalization round trips can be audited before a larger IDT ↔ RFC loop is closed.

For state \(I\), the audit measures

```math
\Delta_\gamma=d\!\left(I,\mathcal H_\gamma(I)\right)
```

and independently measures declared invariant defects at every transport stage. The final audit receipt binds the inverse-lineage ID and receipt SHA, keeping every measured defect traceable to law KAKU candidates and evidence.

## Authority boundary

The coding/audit path is:

```text
GREMLIN relational mining
    -> explicit invariant/alignment candidate
    -> exact KAKU resolution
    -> RADICAL candidate
    -> OPERATOR candidates
    -> native PNV parse/conformance
    -> pure result
    -> inverse lineage
    -> optional LAW_FRAME / holonomy audit
    -> admission gate
    -> optional canonical promotion
    -> admitted runtime execution
```

GREMLIN remains the generator/auditor, PNV remains the executable language, and PNCS admission lineage remains the authority boundary.

## Coding use

A discovered relational isomorphism can be compiled incrementally rather than flattened immediately into source text. The same KAKU/RADICAL/OPERATOR mechanism now carries IDT/RFC/TIR law-frame paths and their measurable holonomy receipts.

## Conformance requirements

Repository-level construction is covered by focused tests for:

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
- exact candidate inverse lineage,
- emitted-value and trace provenance,
- forward↔inverse content-ID round trip,
- local self holonomy loops,
- cross-domain holonomy loops,
- state holonomy defects,
- intermediate invariant defects,
- holonomy inverse-lineage binding,
- fail-closed authority flags,
- live authoring entry bound to `/dev/shm/ciel_noema`.

GitHub Actions execution status is provenance-recorded separately from implementation status. Pre-test runner failures remain an unresolved CI execution state rather than a code verdict.
