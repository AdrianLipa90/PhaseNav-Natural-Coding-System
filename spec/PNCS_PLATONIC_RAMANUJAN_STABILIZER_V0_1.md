# PNCS Platonic–Ramanujan Stabilizer v0.1

Status: **CANDIDATE / NON-ACTUATING / READ-ONLY REFERENCE / RUNTIME INTEGRATION OFF**

Parents: `PNCS_36D_BASIS_V0_1`, `PNCS_ORDERED_T36_TO_HTRI_DRIVE_V0_32`, `PNCS_SEMANTIC_ORBITAL_HTRI_BRIDGE_V0_1`.

## Purpose

This candidate adds a deterministic sparse spectral topology for the existing 36 PhaseNav lanes without changing semantic identity, coordinate order, typed-content authority, or parent v0.32 dynamics.

The current v0.32 implementation already groups the 36 lanes as twelve consecutive local blocks of three. The candidate therefore uses

\[
\boxed{G_{36}=I_{12}\square K_3},
\qquad
\boxed{A_{36}=A_I\otimes I_3+I_{12}\otimes A_{K_3}}.
\]

Channel \(c\) remains lanes \((3c,3c+1,3c+2)\). No semantic names are inferred for channels or axes.

## Exact graph properties

The icosahedral factor has degree 5 and the local \(K_3\) factor degree 2, so

\[
\deg G_{36}=5+2=7.
\]

The carrier has 36 vertices and 126 undirected edges. Its adjacency spectrum is

\[
\begin{aligned}
\{&7^{(1)},(2+\sqrt5)^{(3)},4^{(2)},(\sqrt5-1)^{(6)},1^{(5)},\\
&(2-\sqrt5)^{(3)},(-2)^{(10)},(-1-\sqrt5)^{(6)}\}.
\end{aligned}
\]

Thus

\[
\rho_{nt}=2+\sqrt5<2\sqrt6,
\]

so the graph is Ramanujan, and the normalized Laplacian gap is

\[
\boxed{\gamma_{36}=\frac{5-\sqrt5}{7}\approx0.3948474318}.
\]

This is a graph property, not a claim that the full live runtime is already Ramanujan-stable.

## Candidate stabilizing term

The reference module exposes `stabilizing_coupling(phi, beta)` implementing

\[
\boxed{C_i^{PR}=-\frac{\beta}{7}\sum_j(A_{36})_{ij}\sin(\phi_i-\phi_j),\qquad\beta\ge0.}
\]

This term is deliberately separate from the parent v0.32 coupling. No default v0.32 path calls it, so merely merging this module changes no runtime behaviour.

Around a synchronized state the isolated candidate linearizes to

\[
\dot\delta=-\frac{\beta}{7}L_{36}\delta+O(\|\delta\|^3).
\]

On the mean-zero subspace the slowest linear decay rate is bounded below by

\[
\boxed{\beta\gamma_{36}=\beta\frac{5-\sqrt5}{7}}.
\]

For explicit Euler applied to the isolated linearized term, a sufficient non-expansive condition is

\[
\Delta t\,\beta\le\frac{14}{8+\sqrt5}\approx1.3677126833.
\]

## Global Lyapunov property of the isolated regularizer

Define the graph disagreement energy

\[
\boxed{V(\phi)=\sum_{(i,j)\in E(G_{36})}\left[1-\cos(\phi_i-\phi_j)\right]}.
\]

Its gradient is

\[
\frac{\partial V}{\partial\phi_i}=\sum_j(A_{36})_{ij}\sin(\phi_i-\phi_j).
\]

Therefore the candidate is exactly the negative gradient flow

\[
\dot\phi=-\frac{\beta}{7}\nabla V.
\]

For the isolated continuous-time regularizer,

\[
\boxed{\dot V=-\frac{\beta}{7}\|\nabla V\|^2\le0}.
\]

This is a global Lyapunov monotonicity theorem for the isolated candidate term. It does **not** imply global convergence to the synchronized state, because other stationary phase configurations can exist, and it does not imply stability after adding the complete v0.32/QHTRI dynamics. Those remain benchmark gates.

## Exact invariants

The module preserves the existing `12 x 3` lane order, uses a simple symmetric zero-diagonal 7-regular graph, has seven neighbours per lane, and is deterministic. The regularizer is zero on uniform phase, globally phase covariant, and has zero net common-phase injection:

\[
\sum_i C_i^{PR}=0.
\]

Input arrays are not mutated.

## Sparse support mode

`support_mask()` and `apply_support_mask(g)` expose a research-only sparse transform. A complete 36-node graph has 630 undirected off-diagonal edges; this carrier has 126, exactly one fifth of that support. This gives five times fewer candidate pair interactions at the combinatorial level. No wall-clock speedup is claimed before benchmark.

Masking the parent adaptive `g` is not enabled by default and remains a separate experiment.

## TIR L-constant relation

The carrier degree satisfies

\[
\boxed{7=5+2=L_5+L_4=L_3}.
\]

Operationally, the icosahedral inter-channel degree contributes 5 and each existing three-lane complete block contributes 2. This is a structural crosscheck, not a replacement for the independent TIR finite-group derivation of \((L_3,L_4,L_5)=(7,2,5)\).

## Orbital value

The icosahedral factor has multiplicity blocks \(1,3,5,3\); the first three align with dimensions of the low-angular-momentum \(s,p,d\) sectors. This makes the same finite factor a candidate for the existing semantic-orbital bridge while preserving the radial Hamiltonian. Full orbital equivalence still requires Wigner/Gaunt benchmarks.

## Benefits to test

1. **Stability:** positive spectral gap gives a quantitative local contraction scale, while \(V\) gives a global non-increasing disagreement potential for the isolated regularizer.
2. **Sparse conditioning:** every lane has equal degree; no graph-induced hubs.
3. **Deterministic routing:** fixed topology independent of natural-language interpretation.
4. **Orbital compatibility:** icosahedral symmetry provides finite low-\(\ell\) representation blocks.

None is promoted to production before comparative validation.

## Integration boundary

```text
runtime_default_enabled = false
parent_v0_32_modified = false
live_surface_writes = 0
semantic_axis_meanings_added = 0
effect_authority_added = 0
```

A future runtime gate must compare baseline v0.32 against v0.32 plus additive \(C^{PR}\), and treat support-masked coupling as a separate experiment. Required metrics include phase-dispersion and disagreement-energy decay, perturbation recovery, target error, ordered-path distinguishability, control effort, QHTRI Hermiticity/unitarity, latency, and adversarial/noisy robustness.

## Reference implementation

`src/phasenav_natural_code/platonic_ramanujan_stabilizer_v01.py`

Tests:

`tests/test_platonic_ramanujan_stabilizer_v01.py`

Local repo-style reference gate before commit: **10/10 PASS**. Tests include exact graph spectrum, Ramanujan bound, normalized gap, lane-order preservation, sparsity, global phase covariance, local contraction, finite-difference gradient verification, exact Lyapunov derivative identity, and discrete small-step energy decrease.

Hosted CI and live-derived comparative runtime validation remain pending.
