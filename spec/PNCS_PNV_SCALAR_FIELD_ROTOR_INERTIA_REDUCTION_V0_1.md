# PNCS PNV Scalar-Field Rotor Inertia Reduction V0.1

Status: `IMPLEMENTED_CANDIDATE_REDUCTION_GATE`

Contract: `PNCS_PNV_SCALAR_FIELD_ROTOR_INERTIA_REDUCTION_V0_1`

Semantic loop: `SOURCE.PHASE_NOETHER.ROTOR_INERTIA.REDUCTION.ROUNDTRIP`

## Purpose

This law frame audits the collective reduction of the scalar-field phase kinetic term into the canonical phase rotor used by the IDT phase Hamiltonian. The gate keeps the scalar-field coefficient and the rotor inertia independently supplied until the reduction defect is evaluated.

## Field-side coefficient

For a common collective phase mode with cell amplitudes `A_a`, cell measures `V_a`, and covariant phase rate `D_tau chi`, the finite-cell phase kinetic contribution is

```text
L_phase^field = sum_a A_a^2 V_a (D_tau chi)^2.
```

Define

```text
C_A = sum_a A_a^2 V_a,
I_A = 2 C_A.
```

Then

```text
L_phase^field = (I_A/2) (D_tau chi)^2.
```

## Rotor-side coefficient

The canonical rotor contribution is

```text
L_phase^rotor = (I_phi/2) (D_tau chi)^2,
P_Phi = I_phi D_tau chi,
H_Phi = P_Phi^2/(2 I_phi).
```

The finite Noether collective charge induced by the same field mode is

```text
Q_theta = I_A D_tau chi.
```

The corresponding carrier energy coordinate is

```text
epsilon_N = H_Phi/Q_theta.
```

## Reduction defects

The executable gate computes

```text
Delta_I           = |I_phi-I_A|/I_A,
Delta_coefficient = |I_phi/2-C_A|/C_A,
Delta_Q           = |P_Phi-Q_theta|/Q_theta,
Delta_epsilon     = |epsilon_N-(D_tau chi)/2| / ((D_tau chi)/2).
```

For one common positive covariant phase rate these coordinates obey the exact identity

```text
Delta_I = Delta_coefficient = Delta_Q = Delta_epsilon.
```

The implementation records

```text
Delta_identity_residual = max pairwise defect mismatch
```

and fails closed if that identity is violated outside the numerical floor.

At the exact collective coefficient gate,

```text
I_phi = I_A,
P_Phi = Q_theta,
epsilon_N = (1/2) D_tau chi.
```

## Semantic admission gates

The roundtrip requires explicit equality of:

- scalar-field and rotor phase-mode IDs,
- scalar-field and rotor covariant-rate IDs,
- scalar-field and rotor measure IDs,
- ordered collective cell support.

`I_phi` remains an independent input. It is compared against `I_A=2 sum A_a^2 V_a`; the implementation does not construct the equality by assignment.

## Transforms

```text
scalar_field.bind_rotor_inertia
scalar_field.reconstruct_reduction_input
```

The reverse transform recomputes all derived coordinates and fails closed on tampering.

## Holonomy invariants

The loop preserves the collective reduction signature, field and rotor coefficients, both inertias, Noether charge, rotor momentum, rotor energy, finite-carrier energy coordinate, half phase rate, all reduction defects, and the exact defect-identity residual.

## Epistemic boundary

The executable theorem is conditional on the common phase-mode, covariant-rate, measure, and collective-support gates. Physical promotion of those cross-bindings remains an evidence-bearing step. GREMLIN outputs remain `CHYBA / CANDIDATE_ONLY` and have no canon or runtime execution authority.

## Paired formalism interfaces

- `IDT:formalism/01AB_scalar_field_rotor_inertia_reduction.md`
- `RFC:formalism/RFN1B2L_SCALAR_FIELD_ROTOR_INERTIA_REDUCTION.md`
