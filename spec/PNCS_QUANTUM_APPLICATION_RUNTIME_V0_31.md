# PNCS Quantum Application Runtime v0.31 — No Early Collapse

Status: `CANDIDATE / NATIVE_PNV_CONTRACT / LOCAL_FIRST / NO_EARLY_COLLAPSE / CLASSICAL_BOUNDARY_EXPLICIT`

## Purpose

PNCS treats an application as an evolving PhaseNav state, not as a sequence of Boolean machine states.

The canonical application state is

$
\Psi_{app}=(\Phi_{36},\mathcal A,\mathcal T,s,\tau,\Sigma,\mathcal P),
$

where:

- \(\Phi_{36}\in T^{36}\) is the PhaseNav carrier;
- \(\mathcal A\) is an amplitude/coefficient field;
- \(\mathcal T\) is the typed relation tensor/graph state;
- \(s\) is the scalar field bundle used for readiness, confidence, risk, admission and other continuous quantities;
- \(\tau\) is internal ordering/evolution state;
- \(\Sigma\) is residual/uncertainty structure;
- \(\mathcal P\) is immutable provenance.

No component is implicitly reduced to a Boolean merely because a later interface expects a Boolean answer.

## Core invariant

$
\boxed{\text{NEVER COLLAPSE EARLY}}
$

Internal operators transform the full state:

$
\Psi_{t+1}=\mathcal U_k(\Psi_t).
$

The operator may be phase, relational, orbital, tensor, scalar or mixed. A classical result is produced only by an explicit observation boundary

$
\mathcal M_c:\Psi\rightarrow y_c.
$

For a two-outcome boundary,

$
y_c\in\{0,1\}.
$

For a multi-outcome or continuous observation, PNCS must preserve the declared outcome space rather than force it into 0/1.

## Boolean algebra scope

`PNCS_BOOLEAN_ALGEBRA_V0_10` remains valid, but its architectural role is now explicit:

- Boolean predicates are boundary projections and fail-closed safety/protocol gates;
- they are not the ontological state model of a quantum application;
- unresolved phase/tensor/scalar state must not be silently replaced by FALSE;
- PASS/FAIL is legal only where the contract explicitly declares a measurement/admission boundary.

Thus

$
\text{Boolean layer}\subset\text{observation/protocol boundary},
$

not

$
\text{application state}\equiv\text{Boolean layer}.
$

## Local-first execution

The normative execution target is local PNCS/PhaseNav capacity. Remote services are optional adapters, never required runtime authority.

$
\boxed{\text{LOCAL FIRST} > \text{REMOTE OPTIONAL}}
$

Workers are represented by capabilities rather than server identity:

$
C_j=(\Phi_j^{cap},CPU,GPU,RAM,toolchain,trust,latency).
$

Task placement is a multidimensional matching problem over application state and capability state. FIFO or flat service selection is not primary.

## Measurement boundary

Every observation must declare:

- source state digest;
- measurement channel;
- outcome space;
- whether post-measurement state is retained;
- provenance;
- whether the result is only protocol/safety authority or also semantic output.

For a binary release gate:

$
\mathcal M_{release}(\Psi)=
\begin{cases}
1 & \text{RELEASE},\\
0 & \text{QUARANTINE}.
\end{cases}
$

This bit is the boundary result. It is not the internal state that produced it.

## Backend firewall

This contract is quantum-state / quantum-application semantics. It does not claim that a CPU/GPU execution is physically quantum.

Backends must declare one of:

- `CLASSICAL_PHASE_SIMULATION`;
- `ANALOG_PHASE_RUNTIME`;
- `QPU_PHYSICAL`.

A physical quantum claim requires the `QPU_PHYSICAL` backend plus its own evidence.

## Native representation

Canonical native surface:

`native/PNCS_QUANTUM_APPLICATION_RUNTIME_V0_31.pnv`

Python modules may remain reference, parser, compatibility and test adapters only. They are not the semantic authority of v0.31.

## Compatibility

v0.31 does not invalidate existing fail-closed gates. Existing `ready`, `PASS`, `FAIL`, `allow`, `deny` and predicate values remain legal when they are explicitly typed as projections.

Existing runtime versions remain historical/executable provenance. v0.31 changes the architectural interpretation of state flow and defines the next native runtime contract.

## Required downstream behavior

GREMLIN and other PNCS applications must:

1. preserve the richest available state until an observation boundary;
2. expose residuals and uncertainty instead of prematurely converting them to FAIL;
3. retain provenance across measurement;
4. distinguish measurement output from pre-measurement state;
5. keep high-consequence safety/admission gates fail-closed;
6. never infer physical quantum execution from quantum-state semantics alone.
