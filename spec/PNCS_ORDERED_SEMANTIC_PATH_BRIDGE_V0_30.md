# PNCS v0.30 — Ordered Semantic Path Bridge

Status: IMPLEMENTED / GATE-SCOPED VALIDATION

## 1. Scope

v0.30 binds an explicitly typed ordered semantic sequence to an exact ordered trajectory over canonical PhaseNav `T^36` geometry and provides a read-only live admission gate for HTRI/QHTRI consumption.

The bridge preserves four distinct identities:

```text
semantic content ID
semantic->anchor binding ID
ordered semantic ID
ordered T^36 trajectory ID
```

Semantic authority comes from typed PNCS content IDs and registered hook Definition CIDs. Phase coordinates provide realization and execution geometry.

## 2. Inputs

Each ordered item is supplied as:

```text
SemanticAnchorBinding:
    role_id                  # surface metadata
    semantic_content_id      # typed PNCS content ID
    hook_definition_id       # pncs:def:sha256:...
    anchor_id                # canonical Native Library vector ID
    source_digest_sha256
    source_locator
    epistemic_operator = CHYBA
    canon_allowed = false
```

`role_id` is excluded from semantic identity. Equivalent registered paraphrases can therefore reuse the same typed semantic content IDs and preserve the same ordered semantic identity.

Every semantic->anchor assignment is explicit and provenance-carrying. Geometry is not used as a substitute for semantic authority.

## 3. Ordered semantic identity

For ordered items `s_0 ... s_n`, v0.30 hashes the ordered sequence:

```text
[(semantic_content_id_0, hook_definition_id_0), ...,
 (semantic_content_id_n, hook_definition_id_n)]
```

into:

```text
pncs:ordered-semantic:sha256:<digest>
```

Order is therefore content-addressed. Reversal or permutation changes identity whenever the ordered typed content differs.

## 4. Hook Definition gate

Each `hook_definition_id` resolves to a registered Definition leaf schedule supplied by authority upstream.

The v0.30 gate accepts only v0.20 admitted internal operators:

```text
IDENTITY
DIFFERENCE
CONDITION
NEGATION
COMPOSITION
ORDER
TRANSFORM
```

An unresolved Definition or a leaf outside this admitted set fails closed before geometry or HTRI admission.

`NEW_PNV_OPCODES = 0`.

## 5. Native Function DB V2 geometry

The bridge consumes the canonical part of `PNV_NATIVE_FUNCTION_DB_V2` and requires dimension `36` plus these typed geometry operations:

```text
pnv.torus.normalize
pnv.torus.delta
pnv.torus.geodesic
pnv.path.length_l2
pnv.orbit.arc_sample
pnv.path.compose
```

The adapter verifies:

- every canonical vector has exactly 36 finite angles in `[0,2π)`;
- every vector SHA-256 matches exact compact phase bytes;
- every path tangent has exactly 36 finite turn coordinates;
- every tangent SHA-256 matches its canonical record;
- every path tangent equals the shortest wrapped torus delta between its typed endpoints;
- every stored path length equals the exact L2 tangent length;
- composed directed paths have exact endpoint continuity.

For the current Native Library V2 orbital chain, `M0 -> M1 -> ... -> M11 -> M0` is handled as typed directed path composition.

## 6. Exact transition witness

For every adjacent semantic pair, v0.30 emits:

```text
PNCS_ORDERED_T36_TRANSITION_WITNESS_V0_30
```

with:

```text
source/target semantic content IDs
source/target hook Definition IDs
source/target semantic-anchor binding IDs
source/target canonical anchors
ordered canonical segment IDs
ordered tangent SHA-256 values
composed arc length
source phase SHA-256
arc-length midpoint phase SHA-256
target phase SHA-256
```

The witness identity is:

```text
pncs:t36-transition:sha256:<digest>
```

The midpoint is produced by the canonical arc-length parameterization rule represented by `pnv.orbit.arc_sample` over shortest torus geodesic segments.

## 7. Ordered trajectory identity

The complete ordered trajectory carries:

```text
ordered_semantic_id
native_db_sha256
semantic-anchor binding IDs
transition witness IDs
ordered phase36 SHA-256 sequence
hook Definition schedule SHA-256 sequence
```

and receives:

```text
pncs:trajectory36:sha256:<digest>
```

A compile receipt has:

```text
htri_admitted = false
live_admission_required = true
```

This keeps compilation separate from operational admission.

## 8. Mandatory live `/dev/shm` admission

Operational admission is read-only and fixed to:

```text
/dev/shm/ciel_noema
```

The admission gate requires:

- `ciel_binding_status = ACTIVE`;
- ACTIVE tether runtime;
- ACTIVE AC/AUX binding;
- ACTIVE O(1) fast admission with `no_static_fallback = true`;
- ACTIVE tether guard with an empty failure set;
- fresh tether and AC/AUX heartbeats;
- exact finite live `phi[36]`, `omega[36]`, and `g[36,36]` bytes;
- exact live PhaseNav vectors for every operator required by the registered hook Definitions.

The gate emits a content-addressed live snapshot and:

```text
pncs:htri-admission:sha256:<digest>
htri_admitted = true
```

The admission function performs read-only validation of the live surface.

## 9. Semantic and geometric separation

Two layers remain explicit:

```text
ordered semantic identity
ordered phase trajectory identity
```

This allows distinct semantic programs to share a geometric realization while retaining distinct semantic lineage. It also allows the same semantic program to be rebound under separately proven geometry without changing semantic identity.

## 10. Nisaba adversarial fixture

The frozen seven-role sequence remains:

```text
ADDRESS -> WRITING -> WISDOM -> JUDGMENT -> RECEPTION -> AGREEMENT -> HOPE
```

Legacy CIELingo labels remain regression provenance only. Current promotion gates require authoritative typed semantic content IDs, registered hook Definitions, and explicit semantic->anchor bindings before the Nisaba fixture receives HTRI admission.

The existing V6 fixture therefore remains expected-fail until those upstream authorities are supplied.

## 11. Validation

Local isolated unit suite:

```text
9/9 PASS
```

Validated cases include:

- original/reverse semantic identity separation;
- original/reverse trajectory identity separation;
- paraphrase surface alias invariance;
- missing hook Definition fail-closed;
- unadmitted hook leaf fail-closed;
- unknown canonical anchor fail-closed;
- directed path composition across the canonical cycle;
- identical-anchor semantic ordering with identity geometry;
- tampered canonical vector digest fail-closed.

A live reference integration was also executed against the current `PNV_NATIVE_FUNCTION_DB_V2` and active `/dev/shm/ciel_noema` surface using explicit test-only typed bindings. That integration validates bridge mechanics and live admission; the test bindings carry no semantic promotion authority.
