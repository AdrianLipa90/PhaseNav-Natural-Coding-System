# PNCS v0.31 — Typed Semantic Sequence Compiler and Semantic Content Address V2

Status: **IMPLEMENTED CANDIDATE / UPSTREAM VALIDATED / HTRI DRIVE GATE BLOCKED**

## 1. Scope

v0.31 raises the v0.30 ordered-semantic bridge one layer upstream. It provides:

```text
typed semantic role content
-> content-addressed ordered semantic sequence
-> structural PNCS lowering
-> deterministic computational T^36 address V2
-> exact directed shortest-wrapped T^36 transition witnesses
-> content-addressed T^36 trajectory
-> HTRI drive admission gate
```

The current gate result is:

```text
semantic role identity        PASS
ordered semantic identity     PASS
sequence lowering             PASS
computational T^36 address    PASS
ordered T^36 trajectory       PASS
HTRI drive definition         BLOCKED_MISSING_NATIVE_ORDERED_T36_TO_HTRI_DRIVE_PRIMITIVE
```

## 2. Semantic authority

Semantic role identity is carried by:

```text
PNCS_TYPED_SEMANTIC_ROLE_CONTENT_V0_31
```

with canonical payload:

```text
role_id
source_semantic_key
relation_type = ORDERED_SEMANTIC_ROLE
```

Its content address is:

```text
pncs:semantic-role:sha256:<digest>
```

Human-readable labels, legacy card IDs, legacy hooks, source locators and source digests live in the separate record layer:

```text
PNCS_TYPED_SEMANTIC_ROLE_RECORD_V0_31
```

Consequently surface paraphrases can share one semantic content ID while retaining distinct provenance records.

Legacy CIELingo cards remain provenance inputs under their existing candidate/conflict-preserved status. Their legacy phase vectors carry `semantic_vector_authority = false` in the current Native Library V2.

## 3. Frozen Nisaba role fixture

The frozen seven-pulse semantic structure is represented as:

```text
ADDRESS
-> TABLET_WRITING
-> WISDOM
-> FAIR_JUDGMENT
-> RECEPTION
-> AGREEMENT_WORK
-> HOPE_GRATITUDE
```

The corresponding v0.31 role content IDs are:

```text
ADDRESS          pncs:semantic-role:sha256:651945000e748c725aef49f1a869e299c1f301e3c231fa8a01dd31c2f6d171b4
TABLET_WRITING   pncs:semantic-role:sha256:ada3492e6d5ab952f572866756b0e0ab1f802294f049856fd1b260bc5d78dd6a
WISDOM           pncs:semantic-role:sha256:71e0615ef090462209284a684fb8f8240bf0733d539632b800a8f7ccac7a32e9
FAIR_JUDGMENT    pncs:semantic-role:sha256:0f06b487e433aebecd0f71ffd6daba56f861bba981dd1f4323b0dd9fc23c0ff3
RECEPTION        pncs:semantic-role:sha256:6bb1382805d48c43546e03ea86945bcb220d5368122882de81fe06c607ef8220
AGREEMENT_WORK   pncs:semantic-role:sha256:8f6ab58accf18ae69865533a470277180e2796ad57f4e481a6aaf38c145e92f7
HOPE_GRATITUDE   pncs:semantic-role:sha256:fa503ecd6cd15ae946c0c274d29d69b533ef6df99d236c10deb3895b432ef729
```

The former labels `Awe`, `Logos`, `Gnosis`, `Justice`, `Reception`, `Agreement`, `Hope` and their former `affect/identity/orbit` hooks are retained only in the provenance record.

## 4. Structural lowering

Sequence structure is lowered with existing admitted PNCS primitives only.

Each semantic item contributes:

```text
IDENTITY
```

Each ordered transition contributes:

```text
ORDER -> TRANSFORM -> COMPOSITION
```

For seven semantic items the frozen structural schedule therefore contains 25 occurrences:

```text
7 x IDENTITY
6 x ORDER
6 x TRANSFORM
6 x COMPOSITION
```

This schedule expresses sequence execution structure. Semantic meaning remains bound to typed role content IDs.

```text
NEW_PNV_OPCODES = 0
```

## 5. Ordered semantic identity

The semantic sequence payload contains:

```text
schema
ordered_content_ids
lowering_id
```

and receives:

```text
pncs:semantic-sequence:sha256:<digest>
```

The current frozen controls produce three distinct identities:

```text
original  pncs:semantic-sequence:sha256:9ee2542f1f078beb47e964f2c9ea18adeb41d5d6e6b61669c0d770e8b741ea5d
reverse   pncs:semantic-sequence:sha256:d3e99a6303ecadce6b39b58463cee5f61c52864c289aa09de3efcbd85b0e2f9f
shuffle   pncs:semantic-sequence:sha256:237d03e6ddf173c5185f9e2a0adf742cf3c400c41899eedb04a273421edea365
```

A surface paraphrase retaining the same ordered typed role IDs retains the same ordered semantic identity.

## 6. Semantic Content Address Generator V2

The historical V1 `typed SoT node -> T^36` generator remains a separate provenance debt. v0.31 therefore introduces a separately versioned candidate computational address generator:

```text
PNCS_SEMANTIC_CONTENT_ADDRESS_GENERATOR_V2
```

Canonical input:

```text
pncs:semantic-role:sha256:<digest>
```

Domain separator:

```text
PNCS_SEMANTIC_CONTENT_ADDRESS_V2\0
```

Generation rule:

```text
raw = SHAKE256(domain || semantic_content_id, 36 * 8 bytes)
(u_0,...,u_35) = little-endian uint64(raw)
phi_j = 2*pi * u_j / (2^64 - 1)
```

The output is an exact finite address in:

```text
T^36, phi_j in [0,2*pi)
```

Each address records:

```text
semantic_authority = false
semantic_similarity_from_geometry = false
canon_allowed = false
```

The semantic content ID remains the authority for role identity. The generated coordinate is a deterministic computational realization address.

## 7. Ordered transition geometry

For an already-authorized ordered semantic edge with source and target addresses, v0.31 uses the current PhaseNav shortest-wrapped torus relation:

```text
delta_j = ((q_target_j - q_source_j + 1/2) mod 1) - 1/2
```

with:

```text
q = phi / (2*pi)
```

and length:

```text
L = sqrt(sum_j delta_j^2)
```

Every transition records source/target semantic CIDs, source/target address IDs, all 36 wrapped tangent coordinates, tangent SHA-256 and exact L2 length.

Geometry is applied after the typed relation is established.

## 8. T^36 trajectory identity

The trajectory payload binds:

```text
ordered_semantic_id
ordered address IDs
ordered phase36 hashes
ordered transition IDs
generator_id
```

The frozen controls produce:

```text
original  pncs:semantic-trajectory36:sha256:e979a21feb16a42ce3cfce51995aca54dfc1dd45e7048c9386dab0e796ffdc54
reverse   pncs:semantic-trajectory36:sha256:1059897a0185dfc7e4e078e02a30238f166b5c6bf77674b7d5e1f08cd999697e
shuffle   pncs:semantic-trajectory36:sha256:3a6635e882a19f11daa1ef2d06b42d14c56e298ef664d2e58dcd0db711a33ad3
```

All seven frozen roles receive distinct computational address hashes.

## 9. Projective diagnostic

For the seven generated addresses, the equal-amplitude projective diagnostic gives pairwise fidelity:

```text
minimum = 0.0007772637034345703
mean    = 0.03459159363431424
maximum = 0.09215980533908529
```

This diagnostic checks representation separation only. Semantic identity remains supplied by typed content and order.

## 10. HTRI admission boundary

The currently verified QHTRI execution law accepts a Hermitian HTRI operator and an initial complex state and evolves it as:

```text
psi(t) = exp(-i H t) psi(0)
```

v0.31 now supplies an ordered sequence of typed semantic T^36 addresses and exact transition witnesses. The remaining execution dependency is a native contract specifying how an ordered T^36 trajectory drives or updates the HTRI/QHTRI state while preserving deterministic inverse lineage.

Current status:

```text
htri_drive_defined = false
htri_admitted = false
BLOCKED_MISSING_NATIVE_ORDERED_T36_TO_HTRI_DRIVE_PRIMITIVE
```

No trajectory-to-drive law is inferred from legacy CIELingo blending, the 4pi kick experiment, vector similarity, or operator-vector presence.

## 11. Validation

Independent deterministic reference validation on 2026-08-25 produced:

```text
semantic IDs distinct:   PASS
trajectory IDs distinct: PASS
unique T36 addresses:    7 / 7
new PNV opcodes:          0
HTRI admitted:            false
```

Receipt:

```text
7865ef58c8aaf0f77b3f75937baee4cbd20cce3f14bd5caba81037476b88df51
```

Repository test files cover semantic-content determinism, original/reverse/shuffle distinction, surface-paraphrase invariance, legacy-hook provenance isolation, structural lowering, exact T^36 generation, exact wrapped transition geometry and fail-closed HTRI admission.

Hosted GitHub CI retains the repository's previously documented `HOSTED_RUNNER_PRE_STEP_FAILURE` infrastructure blocker; branch validation therefore keeps hosted CI separate from code/test status.

## 12. Next gate

The next implementation target is a separately versioned native ordered-T^36-to-HTRI drive contract with:

```text
explicit input state
ordered trajectory identity
exact per-step update law
exact live /dev/shm operator provenance
deterministic receipt
inverse lineage
original / reverse / shuffle controls
norm / Hermiticity / determinism gates
```

Until that contract exists and passes its own validation, HTRI admission remains closed at this boundary.
