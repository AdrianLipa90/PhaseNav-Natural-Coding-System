# PNCS PNV Source Holonomy Loops v0.1

Status: `REFERENCE_SOURCE_LOOPS_IMPLEMENTED / IDT_RFC_INTERFACE_EXPLICIT / Q0_CONDITIONAL / EPSILON_Q_CONDITIONAL`

## Purpose

This contract instantiates `PNCS_PNV_INFORMATION_HOLONOMY_V0_1` for the first source-factorization loops at the IDT ↔ RFC interface.

The reference loops are executable PNV law-frame objects. Each loop compiles into KAKU candidates, one RADICAL, native PNV OPERATOR candidates, a pure execution trace, an information-holonomy audit receipt, and inverse lineage back to explicit content/evidence.

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

The PNV law nodes are:

```text
LAW.RFC.CARRIER_EXTENSIVE
LAW.IDT.NORMALIZED_PROFILE
```

and the admitted transport names are:

```text
carrier.normalize_profile
carrier.reconstruct_extensive
```

The declared audit invariants are:

```text
SOURCE.TOTAL_Q
SOURCE.PROFILE_NORM
```

This loop supplies the executable form of the factorization

```math
Q_a=Q_\Sigma p_a.
```

It is the first exact bridge between extensive carrier amount and normalized IDT distributional shape.

## 2. Conditional q0 occupation loop

For an explicitly supplied positive carrier quantum `q0`, the second loop implements

```math
Q_a
\xrightarrow{\;n_a=Q_a/q_0\;}
n_a
\xrightarrow{\;Q'_a=q_0n_a\;}
Q'_a.
```

The law nodes are:

```text
LAW.RFC.CARRIER_EXTENSIVE
LAW.CARRIER.QUANTIZED_OCCUPATION
```

and the transport names are:

```text
carrier.to_occupation
carrier.from_occupation
```

The loop records the explicit gate:

```text
gate:q0:CONDITIONAL
```

and audits preservation of:

```text
SOURCE.TOTAL_Q
```

The physical derivation/admission of `q0` remains a separate source-normalization gate. Once an admitted value is supplied, the round-trip itself is executable and auditable.

## 3. Conditional epsilon_Q source-density loop

For an explicitly supplied positive energy-per-carrier-charge `epsilon_Q`, the third loop implements

```math
j_Q
\xrightarrow{\;\rho_Q=(\epsilon_Q/c^2)j_Q\;}
\rho_Q
\xrightarrow{\;j'_Q=(c^2/\epsilon_Q)\rho_Q\;}
j'_Q.
```

The law nodes are:

```text
LAW.CARRIER.CURRENT_DENSITY
LAW.RFC.PHYSICAL_SOURCE_DENSITY
```

and the transport names are:

```text
source.to_mass_density
source.from_mass_density
```

The loop records:

```text
gate:epsilon_Q:CONDITIONAL
```

and audits the representation-independent equivalent current norm:

```text
SOURCE.EQUIVALENT_CURRENT_NORM
```

The supplied `epsilon_Q` and `c` values are carried explicitly through the transformed state so the inverse transport can verify that the same normalization is used on both sides of the loop.

## State contracts

### Extensive carrier

```text
schema         = PNCS_EXTENSIVE_CARRIER_STATE_V0_1
representation = EXTENSIVE_CARRIER
Q_cells
Q_total
```

The positive-source sector requires finite non-negative `Q_cells` and `Q_total > 0`.

### Normalized carrier profile

```text
schema         = PNCS_NORMALIZED_CARRIER_STATE_V0_1
representation = NORMALIZED_PROFILE
p_cells
Q_total
```

with normalized profile tolerance controlled at the reference level.

### Occupation profile

```text
schema         = PNCS_CARRIER_OCCUPATION_STATE_V0_1
representation = OCCUPATION_PROFILE
n_cells
q0
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

## Holonomy audit

Every reference loop is compiled and audited through the generic law-frame contract:

```text
PNCS_PNV_INFORMATION_HOLONOMY_V0_1
```

so the final receipt contains:

```text
state_defect = Delta_gamma
invariant_results
native execution receipt
inverse-lineage receipt
KAKU/RADICAL/OPERATOR provenance
```

The intended control condition is

```math
\Delta_\gamma=0
```

for exact round-trip fixtures, or an explicitly declared tolerance for numerical/instrumental states.

## GREMLIN integration

The unified GREMLIN ↔ PNV bridge exports the builders, state constructors, transform registries and invariant evaluators for all three loops.

The coding path is therefore:

```text
GREMLIN relation / physical-law candidate
  -> admitted law-gate KAKU
  -> source-loop template
  -> RADICAL
  -> TRANSFORM operators
  -> PNV execution
  -> holonomy receipt
  -> inverse lineage
```

GREMLIN can propose which admitted law gates should be connected. PNV executes the resulting connection and measures its information-holonomy defect before any later promotion gate.

## Next source-loop frontier

The next larger loop is the multi-law source frame:

```text
J_Q^mu
  -> continuity
  -> Q_Sigma
  -> normalization
  -> p_Q
  -> IDT transport
  -> phase/energy normalization
  -> RFC source density
  -> relational field dynamics
  -> reconstructed J_Q^mu
```

Its edges should be added incrementally as their individual transport contracts become admitted, with OPEN edges represented as explicit gates rather than filled by an implicit normalization.
