# PNCS Platonic–Ramanujan Canonical Status v0.1

Status: `CANONICAL_STRUCTURAL_COMPONENT / RUNTIME_DEFAULT_OFF / ADDITIVE_ACTIVATION_REJECTED_V0_1`

Date: 2026-09-11

The 36-node topology

\[
G_{36}=I_{12}\square K_3
\]

is admitted as the canonical deterministic sparse spectral carrier for the existing ordered `12 x 3` PhaseNav lane decomposition. This admission does not assign semantic names to the 36 coordinates and does not alter typed-content authority.

Canonical exact properties:

```text
vertices = 36
degree = 7
undirected_edges = 126
nontrivial_spectral_radius = 2 + sqrt(5)
Ramanujan_bound = 2*sqrt(6)
normalized_Laplacian_gap = (5-sqrt(5))/7
lane_order = preserved
```

The implementation surface

`src/phasenav_natural_code/platonic_ramanujan_stabilizer_v01.py`

is admitted as a disabled optional structural component. Its graph constructors, support mask, spectral metrics, disagreement-energy function and isolated phase operator are canonical APIs at the software/reference level.

The isolated operator obeys

\[
\dot V=-\frac{\beta}{7}\|\nabla V\|^2\le0,
\]

and the repository gate passes `10/10` tests.

## Runtime activation verdict

The fresh live-derived comparative benchmark did **not** support enabling

\[
C_i^{PR}=-\frac{\beta}{7}\sum_jA_{ij}\sin(\phi_i-\phi_j)
\]

as an additive default term in parent v0.32. Although graph disagreement energy decreased and exact target hitting remained at floating-point residual, paired perturbation recovery worsened for every tested positive beta.

Therefore:

```text
runtime_default_enabled = false
parent_v0_32_modified = false
additive_C_PR_activation = REJECTED_V0_1
support_mask_parent_g_activation = OPEN_SEPARATE_GATE
live_surface_writes = 0
```

This rejection is part of the canonical evidence record and must not be silently removed by later revisions.

Reference benchmark receipt:

`provenance/receipts/PNCS_PLATONIC_RAMANUJAN_LIVE_COMPARATIVE_BENCHMARK_20260911.json`

Reference structural validation receipt:

`provenance/receipts/PNCS_PLATONIC_RAMANUJAN_STABILIZER_VALIDATION_V0_1.json`

A later runtime proposal must use a new version and beat the preserved v0.1 benchmark on perturbation recovery without regressing target accuracy, ordered-path identity, Hermiticity, unitarity, provenance or effect boundaries.