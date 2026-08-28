# PNCS v0.31 — Typed Semantic Sequence Compiler and Semantic Content Address V2

Status: **IMPLEMENTED CANDIDATE / UPSTREAM VALIDATED / HTRI DRIVE GATE BLOCKED**

## 1. Scope

v0.31 raises the v0.30 ordered-semantic bridge one layer upstream:

```text
typed semantic role content
-> content-addressed ordered semantic sequence
-> structural PNCS lowering
-> deterministic computational T^36 address V2
-> exact directed shortest-wrapped T^36 transition witnesses
-> content-addressed T^36 trajectory
-> HTRI drive admission gate
```

Current gates:

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

Surface paraphrases therefore share semantic identity whenever they retain the same typed role content and order. Provenance records remain independently content-addressed.

Legacy CIELingo card material is retained with role:

```text
PROVENANCE_ONLY
```

Semantic authority source:

```text
TYPED_CONTENT_AND_ORDER
```

## 3. Frozen Nisaba role fixture

The frozen seven-pulse semantic structure is:

```text
ADDRESS
-> TABLET_WRITING
-> WISDOM
-> FAIR_JUDGMENT
-> RECEPTION
-> AGREEMENT_WORK
-> HOPE_GRATITUDE
```

v0.31 role content IDs:

```text
ADDRESS          pncs:semantic-role:sha256:651945000e748c725aef49f1a869e299c1f301e3c231fa8a01dd31c2f6d171b4
TABLET_WRITING   pncs:semantic-role:sha256:ada3492e6d5ab952f572866756b0e0ab1f802294f049856fd1b260bc5d78dd6a
WISDOM           pncs:semantic-role:sha256:71e0615ef090462209284a684fb8f8240bf0733d539632b800a8f7ccac7a32e9
FAIR_JUDGMENT    pncs:semantic-role:sha256:0f06b487e433aebecd0f71ffd6daba56f861bba981dd1f4323b0dd9fc23c0ff3
RECEPTION        pncs:semantic-role:sha256:6bb1382805d48c43546e03ea86945bcb220d5368122882de81fe06c607ef8220
AGREEMENT_WORK   pncs:semantic-role:sha256:8f6ab58accf18ae69865533a470277180e2796ad57f4e481a6aaf38c145e92f7
HOPE_GRATITUDE   pncs:semantic-role:sha256:fa503ecd6cd15ae946c0c274d29d69b533ef6df99d236c10deb3895b432ef729
```

Former labels `Awe`, `Logos`, `Gnosis`, `Justice`, `Reception`, `Agreement`, `Hope` and former hooks `affect/identity/orbit` are attached as provenance metadata.

## 4. Structural lowering

Sequence structure uses existing admitted PNCS primitives.

Each semantic item contributes:

```text
IDENTITY
```

Each ordered transition contributes:

```text
ORDER -> TRANSFORM -> COMPOSITION
```

The frozen seven-item schedule contains:

```text
7 x IDENTITY
6 x ORDER
6 x TRANSFORM
6 x COMPOSITION
```

Lowering identity:

```text
pncs:semantic-lowering:sha256:92b6b1605a3b31f696da9ee0d93c4aef28792f06ad1f8817c32278b2df7bfd7b
```

Semantic meaning remains bound to typed role content IDs.

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

Frozen controls:

```text
original  pncs:semantic-sequence:sha256:10bfff43632c51df63e8a9e0f0d414ddba13b3e5acb476d4be1eca5c86f17e0d
reverse   pncs:semantic-sequence:sha256:6710d44c3b522a35c2e8c88c1d35eec58aa410c5998d58fa58429b8aaa816e02
shuffle   pncs:semantic-sequence:sha256:8f3fb35a3cdab26ebbef81fa595e84189a1ec9f3eaa551677694bd2410265878
```

A surface paraphrase retaining the same ordered typed role IDs retains the same ordered semantic identity.

## 6. Semantic Content Address Generator V2

The historical V1 generator remains an immutable provenance dependency with status `OPEN_GENERATOR_NOT_RECOVERED`. v0.31 introduces a separately versioned candidate computational address generator:

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

Output space:

```text
T^36
phi_j in [0,2*pi)
```

Each address declares:

```text
semantic_authority = TYPED_CONTENT_ID
geometry_role = COMPUTATIONAL_ADDRESS
promotion_status = CANDIDATE_CHYBA
```

## 7. Ordered transition geometry

An established ordered semantic edge with source and target computational addresses receives the current shortest-wrapped torus realization:

```text
delta_j = ((q_target_j - q_source_j + 1/2) mod 1) - 1/2
q = phi / (2*pi)
L = sqrt(sum_j delta_j^2)
```

Every transition records:

```text
source semantic CID
target semantic CID
source address ID
target address ID
36-component wrapped tangent
tangent SHA-256
L2 path length
relation_authority = TYPED_ORDERED_SEMANTIC_EDGE
geometry_role = SHORTEST_WRAPPED_T36_REALIZATION
```

## 8. T^36 trajectory identity

The trajectory payload binds:

```text
ordered_semantic_id
ordered address IDs
ordered phase36 hashes
ordered transition IDs
generator_id
```

Frozen controls:

```text
original  pncs:semantic-trajectory36:sha256:72a6f4a94fa21ca8d646b856cb1ade22ffcd52d1fa1f28b870204222f36e585f
reverse   pncs:semantic-trajectory36:sha256:eaacd5a31daf821f11b8542a0b0cf87df615d116da86b5266f464bb722ce0bf6
shuffle   pncs:semantic-trajectory36:sha256:e045801ca49cb638aae9de625f93c46dfddbbee348f3a911e1429d2d11ad54f8
```

All seven frozen roles receive distinct computational address hashes.

## 9. Projective representation diagnostic

For the seven generated addresses, the equal-amplitude projective diagnostic gives pairwise fidelity:

```text
minimum = 0.0007772637034345703
mean    = 0.03459159363431424
maximum = 0.09215980533908529
```

Diagnostic role:

```text
REPRESENTATION_SEPARATION_CHECK
```

Semantic authority remains `TYPED_CONTENT_AND_ORDER`.

## 10. HTRI admission boundary

The verified QHTRI execution law consumes a Hermitian HTRI operator and an initial complex state:

```text
psi(t) = exp(-i H t) psi(0)
```

v0.31 supplies an ordered typed-semantic T^36 trajectory and exact transition witnesses. The remaining execution dependency is a native contract for ordered T^36 trajectory application to HTRI/QHTRI with deterministic inverse lineage.

Current status:

```text
htri_drive_status = BLOCKED_MISSING_NATIVE_ORDERED_T36_TO_HTRI_DRIVE_PRIMITIVE
htri_admission_status = BLOCKED_UPSTREAM_DRIVE
```

Inputs from legacy CIELingo blend recurrence, the 4pi kick experiment and vector proximity retain their existing independent evidence classes.

## 11. Validation

Independent deterministic reference validation on 2026-08-25 produced:

```text
semantic IDs distinct:   PASS
trajectory IDs distinct: PASS
unique T36 addresses:    7 / 7
new PNV opcodes:          0
HTRI drive gate:          BLOCKED_MISSING_NATIVE_ORDERED_T36_TO_HTRI_DRIVE_PRIMITIVE
```

Validation receipt SHA-256:

```text
9244c2aaf877fa2c2be892e85d75481d700fee15ef8b459be74c1b6435ae8bd5
```

Repository test files cover semantic-content determinism, original/reverse/shuffle distinction, surface-paraphrase invariance, legacy-hook provenance isolation, structural lowering, exact T^36 generation, exact wrapped transition geometry and HTRI gate status.

Hosted GitHub CI retains the repository's documented `HOSTED_RUNNER_PRE_STEP_FAILURE` infrastructure state. Branch validation records hosted CI as `BLOCKED_INFRASTRUCTURE`.

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

Current admission boundary remains:

```text
BLOCKED_MISSING_NATIVE_ORDERED_T36_TO_HTRI_DRIVE_PRIMITIVE
```
