# PNCS PNV Source Holonomy Loops v0.1

Status: `REFERENCE_SOURCE_LOOPS_IMPLEMENTED / EULER_CHARGE_ENERGY_LOOP_IMPLEMENTED / IDT_RFC_INTERFACE_EXPLICIT / Q0_CONDITIONAL / EPSILON_Q_DOWNSTREAM_CONDITIONAL`

## Purpose

This contract instantiates `PNCS_PNV_INFORMATION_HOLONOMY_V0_1` for source-factorization and source-normalization loops at the IDT ↔ RFC interface.

Each reference loop compiles into KAKU candidates, one RADICAL, native PNV OPERATOR candidates, a pure execution trace, an information-holonomy audit receipt, and inverse lineage back to explicit content/evidence.

The normalization order is now explicit:

```text
Euler/Berry closure
  -> intention phase residual
  -> action charge J_I
  -> canonical rotor energy H_Phi
  -> energy per action-charge epsilon_I
  -> effective Floquet step
  -> later RFC epsilon_Q binding
```

The downstream `epsilon_Q` source-density loop therefore consumes an admitted normalization; it does not derive that normalization itself.

## 1. Extensive carrier ↔ normalized profile

The first control loop implements

```math
Q_a
\xrightarrow{\;p_a=Q_a/Q_\Sigma\;}
(Q_\Sigma,p_a)
\xrightarrow{\;Q'_a=Q_\Sigma p_a\;}
Q'_a.
```

with

```math
Q_\Sigma=\sum_a Q_a,
\qquad
\sum_a p_a=1.
```

Law nodes:

```text
LAW.RFC.CARRIER_EXTENSIVE
LAW.IDT.NORMALIZED_PROFILE
```

Transport names:

```text
carrier.normalize_profile
carrier.reconstruct_extensive
```

Invariants:

```text
SOURCE.TOTAL_Q
SOURCE.PROFILE_NORM
```

This is the executable form of `Q_a = Q_Sigma p_a`.

## 2. Conditional q0 occupation loop

For explicitly supplied positive `q0`,

```math
Q_a
\xrightarrow{\;n_a=Q_a/q_0\;}
n_a
\xrightarrow{\;Q'_a=q_0n_a\;}
Q'_a.
```

Law nodes:

```text
LAW.RFC.CARRIER_EXTENSIVE
LAW.CARRIER.QUANTIZED_OCCUPATION
```

Transport names:

```text
carrier.to_occupation
carrier.from_occupation
```

The loop records

```text
gate:q0:CONDITIONAL
```

and preserves

```text
SOURCE.TOTAL_Q
```

The derivation/admission of `q0` remains a separate gate.

## 3. Conditional epsilon_Q source-density consumer

For an explicitly supplied positive energy-per-carrier-charge `epsilon_Q`,

```math
j_Q
\xrightarrow{\;\rho_Q=(\epsilon_Q/c^2)j_Q\;}
\rho_Q
\xrightarrow{\;j'_Q=(c^2/\epsilon_Q)\rho_Q\;}
j'_Q.
```

Law nodes:

```text
LAW.CARRIER.CURRENT_DENSITY
LAW.RFC.PHYSICAL_SOURCE_DENSITY
```

Transport names:

```text
source.to_mass_density
source.from_mass_density
```

The loop records

```text
gate:epsilon_Q:CONDITIONAL
```

and audits

```text
SOURCE.EQUIVALENT_CURRENT_NORM
```

This loop is a downstream consumer. The candidate source of `epsilon_Q` is the Euler-closed phase-intention loop below, followed by the still-open physical carrier/current binding.

## 4. Euler/Berry → action charge → rotor energy → epsilon loop

The fourth loop implements the normalization sequence demanded by IDT 01Y and RFC RF-N1B2I.

### 4.1 Closure residual

The input closure law is

```math
\Phi_{tot}
=\Phi_{AB}+\Phi_B+\Phi_E+\Theta_I
=2\pi(D+\epsilon_{EB}).
```

For the next intention step,

```math
\theta_{I,k}^{EB}
=2\pi(D+\epsilon_{EB})
-\Phi_{AB}-\Phi_B-\Phi_E-\Theta_I^{<k}.
```

The first transport is

```text
euler.resolve_intention_charge
```

and produces

```math
J_{I,k}^{EB}=\hbar\theta_{I,k}^{EB}.
```

### 4.2 Rotor energy

The second transport is

```text
rotor.derive_energy_per_charge
```

and uses

```math
H_{\Phi,k}^{EB}
=\frac{(J_k-J_{I,k}^{EB})^2}{2I_\phi}.
```

On the positive non-degenerate sector it then derives

```math
\epsilon_{I,k}^{EB}
=\frac{H_{\Phi,k}^{EB}}{J_{I,k}^{EB}},
\qquad
\Delta\tau_{k,eff}^{EB}
=\frac{J_{I,k}^{EB}}{H_{\Phi,k}^{EB}}
=\frac1{\epsilon_{I,k}^{EB}}.
```

The effective Floquet step is therefore an output of the Euler-closed rotor sector rather than the primary normalization input.

### 4.3 Reverse transport

The third transport

```text
rotor.reconstruct_euler_input
```

verifies the same Euler action charge, rotor energy, energy-per-charge and Floquet relation, then reconstructs the exact initial closure state.

The loop ID is

```text
PNV_SOURCE_EULER_PHASE_INTENTION_ENERGY_LOOP_V0_1
```

and the cross-repository semantic alias is

```text
SOURCE.PHASE_INTENTION.EULER_CHARGE_ENERGY.ROUNDTRIP
```

Law nodes:

```text
LAW.EULER.BERRY_CLOSURE
LAW.PHASE.INTENTION_ACTION_CHARGE
LAW.PHASE.ROTOR_ENERGY_PER_CHARGE
```

Required invariants:

```text
SOURCE.EULER_CLOSURE_SECTOR
SOURCE.INTENTION_ACTION_CHARGE
SOURCE.ROTOR_PHASE_ENERGY
SOURCE.ENERGY_PER_ACTION_CHARGE
```

Explicit evidence gates include

```text
gate:epsilon_Q:AFTER_EULER
gate:Q_Sigma_to_J_I:OPEN
```

Ratio evaluation fails closed unless

```text
I_phi > 0
J_I^EB > 0
H_Phi^EB > 0
all closure data finite
```

Zero/degenerate sectors retain their lower-level closure/action-charge equations without forcing a finite ratio.

## 5. State contracts

### Extensive carrier

```text
schema         = PNCS_EXTENSIVE_CARRIER_STATE_V0_1
representation = EXTENSIVE_CARRIER
Q_cells
Q_total
```

### Normalized carrier profile

```text
schema         = PNCS_NORMALIZED_CARRIER_STATE_V0_1
representation = NORMALIZED_PROFILE
p_cells
Q_total
```

### Occupation profile

```text
schema         = PNCS_CARRIER_OCCUPATION_STATE_V0_1
representation = OCCUPATION_PROFILE
n_cells
q0
Q_total
```

### Carrier current density

```text
schema         = PNCS_CARRIER_CURRENT_DENSITY_STATE_V0_1
representation = CARRIER_CURRENT_DENSITY
j_Q
```

### Physical source density

```text
schema         = PNCS_PHYSICAL_SOURCE_DENSITY_STATE_V0_1
representation = PHYSICAL_SOURCE_DENSITY
rho_Q
epsilon_Q
c
```

### Euler-closed phase-intention state

```text
schema         = PNCS_EULER_PHASE_INTENTION_STATE_V0_1
representation = EULER_BERRY_CLOSURE_INPUT
D
epsilon_EB
phi_AB
phi_Berry
phi_Euler
theta_prior
hbar
J_total
I_phi
```

Intermediate representations add

```text
theta_I_EB
J_I_EB
H_Phi_EB
epsilon_I_EB
Delta_tau_eff_EB
```

and are removed by exact reverse reconstruction.

## 6. Holonomy audit

All loops are compiled and audited through

```text
PNCS_PNV_INFORMATION_HOLONOMY_V0_1
```

so receipts contain

```text
state_defect = Delta_gamma
invariant_results
native execution receipt
inverse-lineage receipt
KAKU/RADICAL/OPERATOR provenance
```

Exact round-trip controls target

```math
\Delta_\gamma=0.
```

## 7. GREMLIN integration

The unified GREMLIN ↔ PNV bridge exports builders, state constructors, transforms and invariant evaluators for all four source loops.

The coding path is

```text
GREMLIN law/isomorphism candidate
  -> explicit KAKU law gates
  -> source-loop template
  -> RADICAL
  -> TRANSFORM operators
  -> native PNV execution
  -> holonomy receipt
  -> inverse lineage
```

GREMLIN remains candidate-only; admission and canon promotion are separate gates.

## 8. Coupled frontier

The next source law frame is

```text
Euler/Berry closure
  -> J_I^EB
  -> H_Phi^EB
  -> epsilon_I^EB
  -> [J_I^EB <-> Q_Sigma] OPEN
  -> [J_I^EB <-> integral j_I dV_h] OPEN
  -> epsilon_Q
  -> RFC source density
  -> RF-N1C coupling/universality audit
```

OPEN transport edges remain explicit gates rather than implicit normalizations.
