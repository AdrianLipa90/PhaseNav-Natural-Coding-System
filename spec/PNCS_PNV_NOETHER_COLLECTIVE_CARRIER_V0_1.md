# PNCS PNV Noether Collective Carrier v0.1

Status: `IMPLEMENTED_CONDITIONAL_COLLECTIVE_BINDING / RFC_CARRIER_PROMOTION_GATED`

## Purpose

This contract follows `PNCS_PNV_SOURCE_HOLONOMY_LOOPS_V0_1` after the Euler-closed intention charge has been resolved. It tests a local conserved U(1) phase current against the dynamical rotor carrier

\[
\boxed{P_\Phi^{EB}=J-J_I^{EB}.}
\]

The executable semantic loop is

```text
SOURCE.PHASE_NOETHER.COLLECTIVE_CARRIER.ROUNDTRIP
```

and is used directly as the law-frame loop ID.

## 1. Source current

For

\[
\psi=Ae^{i\vartheta},
\]

the admitted algebraic Noether-current form is

\[
\boxed{J_\vartheta^\mu=2A^2\partial^\mu\vartheta.}
\]

On a slice \(\Sigma\), the finite charge is

\[
Q_\vartheta
=2\int_\Sigma A^2\nu_\vartheta\,dV_h,
\qquad
\nu_\vartheta=n_\mu\partial^\mu\vartheta.
\]

## 2. Collective phase reduction

In a candidate collective sector,

\[
\nu_\vartheta=D_\tau\chi.
\]

Define

\[
\boxed{I_A=2\int_\Sigma A^2\,dV_h.}
\]

Then

\[
\boxed{Q_\vartheta=I_A D_\tau\chi.}
\]

The rotor relation is

\[
P_\Phi=J-J_I=I_\phi D_\tau\chi.
\]

The normalization defect is therefore

\[
\boxed{
\Delta_I
=\frac{|Q_\vartheta-P_\Phi|}{|P_\Phi|}
=\left|\frac{I_A}{I_\phi}-1\right|
}
\]

for nonzero common phase rate.

Exact candidate binding is \(I_A=I_\phi\). Numerical candidate work may declare a nonzero tolerance, but that tolerance is carried explicitly by the transform gate.

## 3. Euler-closed energy per Noether carrier

The prior Euler loop supplies

\[
J_I^{EB}=\hbar\theta_I^{EB}.
\]

Hence

\[
P_\Phi^{EB}=J-\hbar\theta_I^{EB}
\]

and

\[
H_\Phi^{EB}=\frac{(P_\Phi^{EB})^2}{2I_\phi}.
\]

The finite Noether carrier is

\[
Q_\vartheta=\frac{I_A}{I_\phi}P_\Phi^{EB}.
\]

Therefore its correctly typed energy-per-carrier coordinate is

\[
\boxed{
\epsilon_N^{EB}
=\frac{H_\Phi^{EB}}{Q_\vartheta}.
}
\]

On the exact collective inertia-binding sector \(I_A=I_\phi\),

\[
Q_\vartheta=P_\Phi^{EB}
\]

and the expression reduces to

\[
\boxed{
\epsilon_N^{EB}
=\frac{H_\Phi^{EB}}{P_\Phi^{EB}}
=\frac{P_\Phi^{EB}}{2I_\phi}
=\frac12D_\tau\chi.
}
\]

Thus `epsilon_N_EB` remains typed by the actual finite Noether charge even when a small explicit numerical binding tolerance is being audited. The exact half-phase-rate identity is recovered precisely at zero inertia defect.

`epsilon_N_EB` remains distinct from the intention-charge ratio `epsilon_I_EB=H_Phi_EB/J_I_EB`.

## 4. Executable state

Schema:

```text
PNCS_NOETHER_COLLECTIVE_CARRIER_STATE_V0_1
```

Initial fields:

```text
D
epsilon_EB
theta_I_EB
hbar
J_total
I_phi
I_A
```

Derived audit fields:

```text
J_I_EB
P_Phi_EB
phase_rate
Q_theta
H_Phi_EB
epsilon_N_EB = H_Phi_EB / Q_theta
Delta_I
```

RFC-bound candidate fields:

```text
Q_RFC = Q_theta
epsilon_Q_candidate = epsilon_N_EB
```

## 5. Transport chain

```text
noether.resolve_rotor_carrier
  -> P_Phi_EB, phase_rate, Q_theta, H_Phi_EB, epsilon_N_EB, Delta_I

noether.bind_rfc_carrier
  -> require Delta_I <= binding_tolerance
  -> Q_RFC=Q_theta
  -> epsilon_Q_candidate=H_Phi_EB/Q_theta

noether.reconstruct_rotor_input
  -> verify the same Q_theta and epsilon_N_EB
  -> reconstruct exact initial state
```

## 6. Law frame

Law nodes:

```text
LAW.PHASE.ROTOR_KINETIC_CHARGE
LAW.NOETHER.COLLECTIVE_PHASE_CHARGE
LAW.RFC.CONSERVED_CARRIER_CANDIDATE
```

Domains:

```text
PHASE_TIME_HAMILTONIAN
EULER_NOETHER_FIELD
RFC_SOURCE_CARRIER
```

## 7. Invariants

```text
SOURCE.EULER_CLOSURE_SECTOR
SOURCE.ROTOR_KINETIC_CHARGE
SOURCE.NOETHER_FINITE_CHARGE
SOURCE.ROTOR_PHASE_ENERGY
SOURCE.NOETHER_ENERGY_PER_CHARGE
SOURCE.NOETHER_INERTIA_BINDING_DEFECT
```

## 8. Evidence gates

Every compiled loop records

```text
gate:collective_phase_rate:CONDITIONAL
gate:I_A_to_I_phi:CONDITIONAL
gate:Q_Sigma_to_Q_theta:OPEN
```

The first two are explicit candidate assumptions tested by the binding defect. The RFC physical carrier promotion remains a separate gate.

## 9. Fail-closed conditions

```text
D integer
hbar > 0
I_phi > 0
I_A > 0
P_Phi_EB > 0
Q_theta > 0
finite Euler/rotor inputs
Delta_I <= binding_tolerance before RFC candidate binding
reverse RFC candidate must preserve Q_theta and epsilon_N_EB
```

A mismatch is surfaced as `PNVNoetherCollectiveError` with the measured `Delta_I` where applicable.

## 10. Authority boundary

All generated KAKU/RADICAL/OPERATOR material remains

```text
EPISTEMIC CHYBA
CANDIDATE_ONLY
runtime_execution_authority=false
canon_write_authority=false
```

Admission of the field/rotor inertia binding and RFC carrier identity is external to candidate authoring.
