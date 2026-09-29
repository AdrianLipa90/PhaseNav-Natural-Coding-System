# PNCS Quantum Application Runtime v0.1

Status: `POST_V1_EXPERIMENTAL / NATIVE_PNV_CONTRACT / NO_EARLY_COLLAPSE / HARDWARE_REALIZATION_SEPARATE`

Date: 2026-09-29

## Objective

PNCS applications are not modeled as Boolean programs whose internal state is repeatedly reduced to true/false.

The native application state remains a multidimensional PhaseNav/relational state until an explicit observation boundary requests a classical result.

The central invariant is:

```text
NEVER_COLLAPSE_EARLY
```

A classical bit is an observation result, not the ontology of the running application.

## Quantum-application state

For an application with N active alternatives, the candidate native state is

\[
\boxed{
\mathcal Q =
(\Phi, C, T, s, \tau, \Sigma, P)
}
\]

with:

- \(\Phi\in T^{N\times 36}\): exact PhaseNav phase carrier for each active alternative;
- \(C=(c_1,\ldots,c_N)\): complex amplitude vector, normalized by \(\sum_k |c_k|^2=1\);
- \(T\): typed relational/dependency tensor;
- \(s\): bounded scalar control/admission field that does not replace the amplitudes;
- \(\tau\): internal runtime/evolution coordinate;
- \(\Sigma\): residual/uncertainty structure;
- \(P\): immutable provenance and operator lineage.

The exact 36D constraint remains unchanged. Every PhaseNav carrier contains exactly 36 finite coordinates.

## Evolution

Internal execution is an operator evolution

\[
\boxed{
\mathcal Q_{t+1}=\mathcal U_t(\mathcal Q_t)
}
\]

where \(\mathcal U_t\) may transform phase, relational tensor, amplitudes, residuals, or runtime coordinates while preserving the declared normalization/integrity contract.

Internal execution MUST NOT replace \(\mathcal Q\) with a Boolean solely because a predicate, scheduler eligibility check, validator gate, or worker status was evaluated.

## Observation boundary

A two-outcome observation is declared by projectors/operators

\[
\mathcal M_2=\{\Pi_0,\Pi_1\}.
\]

Only an explicit observation boundary may emit

\[
\boxed{
b\in\{0,1\}.
}
\]

For a physical quantum backend, probabilities are governed by the backend's validated quantum measurement law. For a digital PhaseNav realization, the projection/measurement kernel MUST be named in the receipt and MUST NOT be misrepresented as a hardware quantum measurement.

The observation receipt binds:

- pre-observation state identity;
- observable / measurement basis identity;
- backend realization class;
- returned classical result;
- post-observation state identity when the backend defines one;
- provenance and authority boundary.

## Classical metadata firewall

The following existing PNCS concepts remain valid, but are classical control metadata rather than the quantum-application state itself:

```text
PASS / FAIL
DONE / OPEN
ready / not-ready
release admitted / blocked
predicate true / false
effect authorized / denied
```

They may gate transport, release, safety, effects, or observation.

They MUST NOT silently overwrite the coherent application state.

In particular:

\[
\boxed{
\text{Boolean predicate result}
\neq
\text{application state}.
}
\]

## Relation to PNCS Boolean Algebra v0.10

`PNCS_BOOLEAN_ALGEBRA_V0_10` remains correct within its declared scope: pure predicate equivalence.

v0.10 is therefore reclassified architecturally as a classical predicate/projection algebra.

It is not the global state algebra for quantum applications.

No v0.10 law is revoked.

## Native execution hierarchy

\[
\boxed{
\text{PhaseNav state}
\to
\text{PNCS quantum application}
\to
\text{native operator evolution}
\to
\text{explicit observation boundary}
\to
\text{classical result}
}
\]

External classical systems are adapters around this path, not the semantic core.

## Runtime locality

The normative live surface remains:

```text
/dev/shm/ciel_noema
```

Repository artifacts provide source, recovery, validation and provenance. They are not a silent replacement for a missing live runtime.

## Hardware firewall

This contract defines a quantum-state application architecture.

It does not by itself establish execution on physical quantum hardware.

Backend classes MUST remain explicit, for example:

```text
PHASENAV_DIGITAL
PHASENAV_ANALOG_CANDIDATE
QPU_PHYSICAL
HYBRID
```

A backend change changes realization evidence, not the logical placement of the observation boundary.

## Release-train boundary

This v0.1 contract is post-v1 research and carries zero authority over the scope-frozen PNCS v1.0 release train until a later explicit promotion decision.

No existing release receipt is retroactively rewritten.

## Core invariants

1. exact 36D finite PhaseNav carriers;
2. normalized active amplitude vector;
3. typed relational tensor;
4. immutable provenance;
5. no Boolean replacement of the internal state;
6. explicit observation boundary;
7. two-outcome observation emits only 0 or 1;
8. control/release/safety booleans remain metadata;
9. backend realization class is explicit;
10. physical quantum claims require separate hardware evidence.
