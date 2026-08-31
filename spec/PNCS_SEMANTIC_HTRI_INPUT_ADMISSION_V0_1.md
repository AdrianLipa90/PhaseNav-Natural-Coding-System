# PNCS Semantic HTRI Input Admission v0.1

Status: `IMPLEMENTED_ON_DEBUG_BRANCH / HOSTED_CONFORMANCE_PENDING`

## Purpose

This contract defines the public input-admission boundary shared by:

```text
semantic_htri_drive_v32.py
semantic_htri_bounded_v33.py
semantic_orbital_htri_bridge_v01.py
semantic_orbital_htri_bounded_v01.py
```

The existing v0.32 inverse-dynamics and v0.33 bounded-control equations remain unchanged. Admission occurs before those equations are evaluated.

## Exact 36D state admission

HTRI phase/frequency/tau vectors are admitted as finite real numeric arrays with exact shape `(36,)`.

A supplied matrix with 36 total elements represents its own matrix shape and does not acquire 36D vector identity by flattening. The coupling matrix `g` is admitted as a finite real numeric array with exact shape `(36,36)`.

`flavor` and `gravity` are one-dimensional finite real numeric arrays with their declared minimum coordinate counts.

Boolean, string and object-typed arrays are outside the numeric admission domain. Integer and floating-point numeric arrays are converted to the internal `float64` representation after admission.

## Scalar admission

Public real-valued controls are admitted from finite `numbers.Real` values with boolean values rejected explicitly.

Positive domains are enforced where required:

```text
dt > 0
u_max > 0
tolerance_rad > 0
```

Bounded tick counters are exact integer values with boolean values rejected:

```text
max_ticks >= 1
max_ticks_per_target >= 1
settle_consecutive >= 1
```

The ordering gate additionally requires `settle_consecutive` not to exceed the corresponding tick budget.

## HTRI/QHTRI parent parameters

`qhtri_graph_hamiltonian()` admits exact finite real `coupling_strength` and `detuning_strength` values before constructing the Hamiltonian.

When `track_target()` receives an existing `U_total`, the supplied propagator is admitted only as a finite numeric array with exact shape `(36,36)` and is then represented internally as `complex128`.

## Content and receipt identity

`DriveSnapshot.source_id`, semantic lane profile identifiers, KAKU lane identities and frequency-binding modes are explicit string provenance fields.

The semantic bridge rejects normalized KAKU-key collisions. Its lane mapping therefore preserves one exact admitted KAKU identity per declared lane assignment.

Canonical receipt hashing admits mappings with string keys. Mapping-key identity is preserved directly in the commitment input.

## Regression gates

The parent and bridge corpora cover:

```text
bool-as-number rejection
numeric-string rejection
object coercion rejection
false 36D shape rejection
boolean/string array rejection
non-vector flavor admission rejection
non-string canonical mapping-key rejection
lane-profile normalized-key collision rejection
strict frequency-mode admission
strict bounded scalar/tick admission
strict prior U_total shape/dtype admission
```

The existing positive numerical regressions remain in the same corpora for target residuals, Hermiticity, unitarity, bounded-control reachability, deterministic receipts and ordered-trajectory identity.

Reference tests:

```text
tests/test_semantic_htri_drive_v32.py
tests/test_semantic_htri_bounded_v33.py
tests/test_semantic_orbital_htri_bridge_v01.py
tests/test_semantic_orbital_htri_bounded_v01.py
```
