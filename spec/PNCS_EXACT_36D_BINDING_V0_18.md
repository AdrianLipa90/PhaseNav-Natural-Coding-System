# PNCS v0.18 — Exact 36D Realization Binding

## Scope

v0.18 binds an existing typed PNCS semantic content ID to an exact, provenance-carrying PhaseNav coordinate vector in `T^36`.

The binding does not derive semantic identity from vector equality or vector similarity.

## Recovered PhaseNav constraints

The recovered PNV/1 language specification fixes:

- phase dimension `36`;
- `κ = ln(2)/(24π)`;
- default epistemic operator `CHYBA`;
- default execution mode `READ_ONLY`;
- `VECTOR`, `BERRY`, `HOLONOMY`, and `ORDER_PARAMETER` as 36D instructions;
- the coarse `VECTOR` family as stable BLAKE2b input hashing + bounded Collatz + 36 phase components.

The exact executable PNV/1 generator source and its canonicalization/iteration parameters remain unrecovered. The frozen-generator recovery ledger explicitly records `OPEN_GENERATOR_NOT_RECOVERED` / `SPEC_PRESENT_IMPLEMENTATION_UNLOCATED`.

Therefore v0.18 does **not** implement a replacement PNCS content-ID -> 36D generator and does not claim historical runtime replay.

## Exact phase object

```text
PhaseVector36:
    angles[36]
    space = T^36
    coordinate_semantics = phase_angles_radians
    range = [0,2π)
    phase36_sha256 = SHA256(compact_json(angles))
```

The vector must contain exactly 36 finite angles, each in the half-open interval `[0,2π)`.

The phase digest convention follows the recovered frozen-vector integrity evidence: `sha256(compact_json(phase36))`.

## Binding

```text
RealizationBinding:
    content_id
    PhaseVector36
    basis_id
    derivation_id
    source_digest_sha256
    source_locator
    epistemic_operator = CHYBA
    canon_allowed = false
```

`content_id` must be a typed PNCS content address from the already established hierarchy.

The realization identity is:

```text
pncs:realization36:sha256:
    SHA256(canonical realization payload)
```

The provenance binding identity is:

```text
pncs:binding36:sha256:
    SHA256(canonical binding payload)
```

This deliberately separates semantic content identity, phase realization identity, and provenance binding identity.

## Registry invariant

For the same:

```text
(content_id, basis_id, derivation_id)
```

two different exact 36D vectors are a conflict and fail closed.

Multiple independent provenance records may bind the same exact realization.

Two distinct semantic content IDs may carry the same exact 36D vector. They remain distinct semantic objects.

Likewise, arbitrarily close phase vectors do not imply semantic equivalence.

v0.18 exposes no nearest-neighbour-to-semantics or similarity-to-semantics admission rule.

## Recovered phase-marker formula

Recovered glossary records preserve a compatible phase-marker formula:

```text
(κτ + α_Mτ(i mod 7) + (2/7)τ floor(i/7) + (q_k mod 5)τ/7) mod τ
```

with `alpha_m = 0.0072973113787402075`.

Those records also carry a `quark_prime` field. The current provenance does not establish a canonical PNCS content-ID -> `q_k` mapping. Therefore this formula is not used by v0.18 to generate PNCS realizations.

## Runtime validation

Reference validation is executed on the live `/dev/shm/ciel_noema` project surface when available.

This validates the binding implementation and invariants. It is not a replay of the missing historical native PNV/1 VECTOR implementation.

## Non-goals

v0.18 does not:

- invent 36 semantic axis labels;
- truncate 36D vectors;
- infer semantic identity from phase equality/similarity;
- regenerate frozen anchors from an undocumented formula;
- self-promote any binding to canon;
- enable generic natural-language execution;
- add a PNV opcode.
