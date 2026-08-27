# PNCS PNV Source Holonomy Loops v0.1

Status: `SEVEN_REFERENCE_SOURCE_LOOPS_IMPLEMENTED / IDT_RFC_INTERFACE_EXPLICIT / PHYSICAL_PROMOTION_GATES_OPEN`

## Purpose

This contract instantiates `PNCS_PNV_INFORMATION_HOLONOMY_V0_1` for the source-factorization, phase-energy, Noether-carrier, conserved-current and scalar-field/rotor reduction layers at the IDT ↔ RFC interface.

Each reference loop compiles into explicit KAKU law gates, one RADICAL, native PNV OPERATOR candidates, a pure execution trace, an information-holonomy audit receipt and inverse lineage back to explicit content/evidence.

The canonical sequence is:

```text
1. SOURCE.CARRIER.NORMALIZATION.ROUNDTRIP
2. SOURCE.CARRIER.Q0_OCCUPATION.ROUNDTRIP
3. SOURCE.CARRIER.EPSILON_MASS_DENSITY.ROUNDTRIP
4. SOURCE.PHASE_INTENTION.EULER_CHARGE_ENERGY.ROUNDTRIP
5. SOURCE.PHASE_NOETHER.COLLECTIVE_CARRIER.ROUNDTRIP
6. SOURCE.PHASE_NOETHER.RFC_CONSERVED_CURRENT.ROUNDTRIP
7. SOURCE.PHASE_NOETHER.ROTOR_INERTIA.REDUCTION.ROUNDTRIP
```

## 1. Extensive carrier ↔ normalized profile

```text
Q_total = sum_a Q_a
p_a = Q_a/Q_total
Q'_a = Q_total p_a
```

The loop audits exact reconstruction and normalized profile support.

## 2. Conditional q0 occupation

For explicitly admitted positive `q0`,

```text
n_a = Q_a/q0
Q'_a = q0 n_a
```

`q0` remains a separately admitted quantization coordinate.

## 3. Conditional epsilon source-density consumer

For explicitly admitted positive `epsilon_Q`,

```text
rho_Q = (epsilon_Q/c^2) j_Q
j'_Q = (c^2/epsilon_Q) rho_Q
```

This loop consumes the energy-per-carrier normalization; it does not promote the physical carrier identity.

## 4. Euler/Berry phase-intention charge-energy loop

The Euler/Berry closure fixes the residual intention sector and the phase rotor supplies the energy coordinate:

```text
J_I^EB = hbar theta_I^EB
P_Phi^EB = J - J_I^EB
H_Phi^EB = (P_Phi^EB)^2/(2 I_phi)
```

The executable loop preserves the closure sector, intention action charge and rotor energy through exact forward/reverse transport.

## 5. Collective Noether carrier loop

The finite Noether carrier is typed as

```text
Q_theta = I_A D_tau chi
P_Phi^EB = I_phi D_tau chi
Delta_I_01Z = |I_A/I_phi - 1|
epsilon_N^EB = H_Phi^EB/Q_theta
```

This layer keeps the finite Noether charge distinct from both `J_I^EB` and `P_Phi^EB` until a coefficient reduction is admitted.

## 6. Noether ↔ RFC conserved-current loop

On one common slice, normal orientation and ordered cell support,

```text
Q_theta = sum_a V_theta,a j_theta,a
Q_Sigma = sum_a V_Q,a j_Q,a
```

with

```text
Delta_J = sum_a V_Q,a |j_Q,a-j_theta,a| / Q_theta
Delta_V = sum_a |V_Q,a-V_theta,a| |j_theta,a| / Q_theta
Delta_Sigma = |Q_Sigma-Q_theta| / Q_theta
Delta_F = |F_side|
```

The exact finite-cell theorem is

```text
Delta_Sigma <= Delta_J + Delta_V.
```

The executable bound coordinate is

```text
Delta_bound = max(0, Delta_Sigma-(Delta_J+Delta_V)).
```

Integrated equality alone is insufficient for local-current promotion. The canonical anti-false-positive witness

```text
V=(1,1)
j_theta=(1,3)
j_Q=(2,2)
```

has `Q_theta=Q_Sigma=4` and `Delta_Sigma=0`, but `Delta_J=0.5`.

## 7. Scalar-field ↔ canonical-rotor coefficient reduction

For the common scalar-field phase mode,

```text
C_A = sum_a A_a^2 V_a
I_A = 2 C_A
L_phase^field = C_A (D_tau chi)^2
              = (I_A/2)(D_tau chi)^2.
```

The independently supplied canonical rotor uses

```text
L_phase^rotor = (I_phi/2)(D_tau chi)^2
P_Phi = I_phi D_tau chi
H_Phi = P_Phi^2/(2 I_phi)
Q_theta = I_A D_tau chi
epsilon_N = H_Phi/Q_theta.
```

The executable reduction coordinates are

```text
Delta_I_reduction = |I_phi-I_A|/I_A
Delta_coefficient = |I_phi/2-C_A|/C_A
Delta_Q_reduction = |P_Phi-Q_theta|/Q_theta
Delta_epsilon_reduction = |epsilon_N-(D_tau chi)/2| / ((D_tau chi)/2).
```

For one common positive covariant phase rate they obey

```text
Delta_I_reduction
= Delta_coefficient
= Delta_Q_reduction
= Delta_epsilon_reduction.
```

At the exact collective reduction gate,

```text
I_phi = I_A
P_Phi = Q_theta
epsilon_N = (1/2) D_tau chi.
```

The implementation does not assign `I_phi=I_A`; `I_phi` is an independent input and the equality is audited against `I_A=2 sum A_a^2 V_a`.

Admission requires explicit equality of the field/rotor phase-mode ID, covariant-rate ID, measure ID and ordered collective support.

## Holonomy audit

All seven loops are compiled and audited through `PNCS_PNV_INFORMATION_HOLONOMY_V0_1`. Receipts contain state defect, invariant defects, native execution provenance and inverse lineage.

Exact round-trip controls target

```text
Delta_gamma = 0.
```

## GREMLIN authority

GREMLIN may generate and encode law candidates and their KAKU/RADICAL/OPERATOR structure. All authored objects remain `CHYBA / CANDIDATE_ONLY`. Physical cross-binding, canon promotion and runtime authority remain explicit admission steps.

## Current source frontier

The scalar-field/rotor coefficient equality is conditionally exact after the common collective phase/rate/measure/support reduction gate. The next physical promotion surface is therefore concentrated on:

```text
field phase mode <-> rotor chi mode
field covariant phase rate <-> rotor D_tau chi
common measure/support
J_Q^mu <-> J_theta^mu
Q_Sigma <-> Q_theta
p_IDT <-> p_Q
source coupling/universality
```
