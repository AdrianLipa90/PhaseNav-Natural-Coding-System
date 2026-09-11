# PNCS 600-cell S3 candidate status v0.1

Status: `CANDIDATE / ACTIVE_WORKING_IMPLEMENTATION / RUNTIME_DEFAULT_OFF / PHYSICAL_BINDING_OPEN`

Date: 2026-09-11

## Candidate policy

`CANDIDATE` is an executable working version. It is not dead code, a placeholder, or a documentation-only artifact. Candidate APIs MAY be executed, benchmarked, composed in candidate routes, and used to generate evidence. They MUST preserve their candidate provenance and MUST NOT be reported as canonical until their promotion gates pass.

`QUARANTINED` or `FAILED` is the status for code that must not participate in working candidate routes except for diagnosis.

## Working carrier

The candidate module

`src/phasenav_natural_code/cell600_s3_candidate_v01.py`

constructs the 120 vertices of the regular 600-cell on the unit 3-sphere, its 12-regular / 720-edge graph, and spectral projectors for the first six S3 angular sectors.

For hyperspherical harmonics on S3,

\[
\dim H_\ell(S^3)=(\ell+1)^2,
\qquad
-\Delta_{S^3}Y_\ell=\ell(\ell+2)Y_\ell.
\]

The 600-cell adjacency spectrum contains the multiplicities

```text
ell = 0 : 1
ell = 1 : 4
ell = 2 : 9
ell = 3 : 16
ell = 4 : 25
ell = 5 : 36
```

on the adjacency eigenvalues

```text
12, 6*phi, 4*phi, 3, 0, -2
```

respectively.

The working candidate therefore defines

\[
L_{600}^{candidate}=\sum_{\ell=0}^{5}\ell(\ell+2)\Pi_\ell.
\]

It is directly executable through `apply_angular_laplacian_candidate`. Inputs containing unsupported graph sectors fail closed rather than silently aliasing them into the supported carrier.

## Exactness boundary

The 120 vertices form a spherical 11-design on S3. The test surface explicitly verifies all 1365 coordinate monomials of total degree <= 11 against the analytic S3 moments.

The repository also preserves a degree-12 nonexact witness:

\[
\langle x_1^{12}\rangle_{600}-\langle x_1^{12}\rangle_{S^3}=\frac{1}{4096}.
\]

Accordingly the working operator is limited to the verified `ell <= 5` carrier. No `ell >= 6` physical or orbital equivalence is promoted by this version.

## Execution semantics

```text
status = CANDIDATE
candidate_api_callable = true
candidate_routes_allowed = true
candidate_benchmarks_allowed = true
runtime_default_enabled = false
canonical_parent_mutated = false
physical_binding = OPEN
unsupported_sector_policy = FAIL_CLOSED
```

This status deliberately differs from the preserved `C_PR v0.1` rejection. That rejected additive runtime term remains historical evidence and is not overwritten. The 600-cell candidate is a new working surface with a new scope.

## Promotion gates

Promotion to a canonical orbital/angular carrier requires, at minimum:

1. repository CI PASS for the candidate tests;
2. byte/provenance receipt for the executed implementation;
3. comparison against an independent hyperspherical-harmonic reference implementation;
4. no regression of existing PNCS ordered-path identity, Hermiticity, unitarity or typed-content authority;
5. an explicit decision on whether any physical binding is being claimed. Structural promotion does not imply physical promotion.
