# PNCS PNV Gauge-Covariant Phase Pullback V0.1

Contract: `PNCS_PNV_GAUGE_COVARIANT_PHASE_PULLBACK_V0_1`

Semantic loop: `SOURCE.PHASE.NOETHER.GAUGE_COVARIANT_PULLBACK.ROUNDTRIP`

Epistemic state: `CHYBA / CANDIDATE_ONLY`

## Purpose

This contract audits the conditional identification of the Euler–Noether scalar-field phase sector with the canonical relational rotor through one common `U(1)` bundle, one Aharonov–Bohm–Berry–Euler connection and one collective pullback.

It consumes the coefficient/inertia reduction from the preceding scalar-field↔rotor gate and resolves the connection-sign, phase-rate, normal-projection and finite-generator layers separately.

## Admitted gauge convention

The project Berry connection uses

\[
\mathcal A_B=i\langle u|du\rangle.
\]

For a section change

\[
|u\rangle\mapsto e^{i\lambda}|u\rangle,
\]

the connection transforms as

\[
\boxed{\mathcal A' = \mathcal A-d\lambda.}
\]

For

\[
\vartheta' = \vartheta+\lambda,
\]

the invariant phase one-form is

\[
\boxed{\mathscr D\vartheta=d\vartheta+\mathcal A.}
\]

The executable gauge probe evaluates

\[
\Delta_{gauge}
=\|\mathscr D\vartheta'-\mathscr D\vartheta\|_\infty
\]

and also records the opposite-sign residual as a sign-discrimination witness.

## Pullback theorem

On a relational trajectory \(q(\tau)\), the common local fiber coordinate satisfies

\[
\chi(\tau)=\vartheta(q(\tau))+\chi_0.
\]

Therefore

\[
\boxed{
q^*(\mathscr D\vartheta)
=D_\tau\chi\,d\tau.}
\]

The implementation derives the field pullback rate from independently supplied phase gradients, connection components and trajectory velocity:

\[
r_{field}
=\sum_a
(\partial_a\vartheta+\mathcal A_a)\dot q^a.
\]

The rotor rate \(r_{rotor}\) is supplied independently and compared through

\[
\boxed{
\Delta_{rate}
=\frac{|r_{field}-r_{rotor}|}{|r_{rotor}|}.}
\]

## Normal projection and Noether charge

For field amplitudes \(A_a\) and cell volumes \(V_a\),

\[
C_A=\sum_a A_a^2V_a,
\qquad
I_A=2C_A.
\]

The independently supplied normal-projected field rate \(r_n\) gives

\[
Q_\vartheta=I_A r_n.
\]

The normal alignment coordinate is

\[
\boxed{
\Delta_{normal}
=\frac{|r_n-r_{field}|}{|r_{field}|}.}
\]

## Rotor generator and moment-map factorization

The independent rotor inertia and rate give

\[
P_\Phi=I_\phi r_{rotor}.
\]

The generator defect is

\[
\boxed{
\Delta_Q
=\frac{|Q_\vartheta-P_\Phi|}{|P_\Phi|}.}
\]

The implementation also audits the exact factorization

\[
\boxed{
\frac{Q_\vartheta}{P_\Phi}
=
\frac{I_A}{I_\phi}
\frac{r_n}{r_{rotor}}.}
\]

Its residual is stored as `Delta_factorization`.

This separates inertia mismatch from normal/rate mismatch and prevents accidental equality of integrated generators from hiding an upstream defect.

## Action and energy coordinates

The field and rotor collective phase actions are

\[
L_{field}=C_A r_{field}^2,
\qquad
L_{rotor}=\frac{I_\phi}{2}r_{rotor}^2.
\]

The action reduction coordinate is

\[
\Delta_{action}
=\frac{|L_{field}-L_{rotor}|}{|L_{rotor}|}.
\]

With

\[
H_\Phi=\frac{P_\Phi^2}{2I_\phi},
\qquad
\epsilon_N=\frac{H_\Phi}{Q_\vartheta},
\]

the epsilon pullback coordinate is

\[
\Delta_\epsilon
=
\frac{|\epsilon_N-r_{rotor}/2|}{r_{rotor}/2}.
\]

On the exact common reduction surface,

\[
\boxed{
I_A=I_\phi,
\quad
r_n=r_{field}=r_{rotor},
\quad
Q_\vartheta=P_\Phi,
\quad
\epsilon_N=\frac12D_\tau\chi.}
\]

## Admission identities

The executable loop requires equality of the declared:

- `bundle_id`,
- local phase-patch ID,
- ABE connection ID,
- measure ID,
- ordered collective cell support.

A nontrivial gauge probe is required for sign discrimination.

## Executable transforms

Forward:

`gauge_phase.bind_common_u1_generator`

Reverse:

`gauge_phase.reconstruct_pullback_input`

The reverse transform recomputes all derived gauge, pullback, action, charge and epsilon coordinates and rejects changed derived values.

## Holonomy invariants

The loop carries invariant coordinates for:

- common bundle/patch/connection/measure/support signature,
- gauge-invariance defect,
- gauge-sign discrimination witness,
- field pullback rate,
- normal-projected field rate,
- rotor covariant rate,
- field and rotor inertia,
- finite Noether charge,
- rotor kinetic momentum,
- rate defect,
- normal-projection defect,
- moment-map defect,
- moment-map factorization residual,
- action reduction defect,
- epsilon pullback defect.

## Cross-repository bindings

Upstream paired formalism:

- IDT `formalism/01AC_gauge_covariant_phase_pullback_noether_generator.md`
- RFC `formalism/RFN1B2M_GAUGE_COVARIANT_PHASE_PULLBACK_NOETHER_GENERATOR.md`

Peer reference validation at introduction of this contract:

- IDT: `381/381 PASS`
- RFC: `73/73 PASS`

## Promotion frontier

The common-`U(1)` gauge-covariant field↔rotor reduction is an exact conditional theorem after its declared bundle/patch/connection/measure/support admissions.

The downstream measured promotion surface remains:

\[
J_Q^\mu\leftrightarrow J_\vartheta^\mu,
\qquad
Q_\Sigma\leftrightarrow Q_\vartheta,
\qquad
p_{IDT}\leftrightarrow p_Q,
\]

followed by RFC source coupling/universality tests.
