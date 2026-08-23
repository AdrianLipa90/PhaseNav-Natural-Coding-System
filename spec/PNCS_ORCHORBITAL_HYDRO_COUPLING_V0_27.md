# PNCS v0.27 ORCHORBITAL × Hydrodynamic T^36 Coupling

Status: ORCH/OORP CORE + EXACT-KAKU REPLAY PASS / DIRECT v0.20 EXECUTOR COUPLING IMPLEMENTED / LIVE V56 VALIDATION PENDING

## Authority

This gate binds PNCS v0.27 hydrodynamic phase flow to the existing ORCHORBITAL Foundation Pack at:

- repository: `AdrianLipa90/CIEL-Omega-ApokalypOS`
- commit: `aa0da54ef29a1f80dd0390427935342225388950`
- `02_ONTOLOGY_AND_OBSERVABLES.md`
- `03_STATE_SPACE_AND_BOUNDARY_CONDITIONS.md`
- `04_INVARIANTS_POTENTIALS_AND_ATTRACTORS.md`
- `05_ENTITY_REGISTRY_AND_SPHERE_EMBEDDING.md`
- `06_SUBJECTIVE_TIME_WINDING_AND_SEMANTIC_MASS.md`
- `07_OORP_PIPELINE_AND_MEMORY.md`

The Foundation Pack is upstream semantic/formal authority. PNCS adds only content-addressed runtime bindings and explicit parameterized laws where the Foundation Pack leaves a function or selector open.

## State chain

```text
v0.20 exact KAKU occurrence
-> ORCHORBITAL orbital mode
-> explicit K_ij process sphere
-> ORCH observables
-> subjective-time scale g(r,C,Delta,m,A)
-> hydrodynamic T^36 transition
-> projected orbital phase update
-> OORP reduction decision
-> optional memory residue receipt
```

No persistent memory write, external effect, semantic identity mutation, routing authority, or laboratory-time claim is opened by this gate.

## Formal space and charts

The ORCH state declares:

```text
formal space: M_rel
geometry anchor: projective Hilbert / Kahler / Fubini-Study
operational chart: Poincare disk
Bloch scope: local reduced chart only
```

Each process sphere declares `sphere_id`, exact internal mode order, leak mode, and effective attractor weight.

## Orbital state

Each KAKU occurrence becomes a distinct orbital even when operator names repeat. Receipt-bound replay binds the orbital to:

```text
(receipt_sha256, step_index, operator_id, operator_vector_sha256)
```

Direct in-executor coupling creates a pre-receipt occurrence identity from:

```text
(program_content_id, step_index, operator_id, operator_vector_sha256,
 before_sigma_id, after_sigma_id, projection_policy_id)
```

The resulting direct trace can only be promoted to receipt-bound evidence after the completed v0.20 receipt is revalidated and every KAKU occurrence matches exactly.

Each orbital contains amplitude, phase, coherence, truth-spin, memory affinity, orbital radius, semantic mass, attractor influence, and explicit EC/ZS/LLMTemp attractor weights.

`AttractorLLMTemp` remains closed in this gate unless an explicit decay schedule is present. The Foundation Pack requires its control share to decay; v0.27 therefore fails closed for any non-zero `llm_temp` weight until that schedule is implemented and receipt-bound.

The exact T^36 operator vector is re-hashed as `<36d>` and must match the v0.20 step before projection.

Current projection contract:

```text
phase      = circular mean of exact T^36 operator vector
coherence  = circular resultant of exact T^36 operator vector
amplitude  = configured scale * RMS(exact T^36 operator vector)
truth-spin = exact boolean `truth` binding when present, otherwise 0
```

The projection policy is content-addressed. No value is inferred from an operator name.

## Coupling

The first KAKU process-sphere coupling is explicit, symmetric and adjacency-only:

```text
K_ij = k_adj  for consecutive execution occurrences
K_ij = 0      otherwise
K_ii = 0
```

The coupling magnitude is an explicit policy parameter.

## Observables

The runtime computes:

```text
C(t)       global weighted phase coherence
Delta(t)   = 1 - C(t)
Delta_H    = sum_k exp(i gamma_k)
R_H        = |Delta_H|^2
Theta      truth scalar
V_tot      = V_EC + V_ZS + V_rel + V_mem + V_def + V_ext
```

Coupling alignment and effective sphere attractor weight are content-addressed diagnostics.

## Subjective time

Foundation Pack law:

```text
Delta tau_i(k) = Delta t * g(r_i, C_i, Delta_i, m_i, A_i)
```

PNCS does not hard-code the open function `g`. It implements a content-addressed explicit affine family:

```text
g = clip(
    b
  + w_r * r
  + w_C * C_local
  + w_D * Delta
  + w_m * m
  + w_A * A,
  g_min,
  g_max
)
```

All coefficients and bounds are explicit inputs to `TimeLaw` and contribute to its identity.

The combined runtime lapse is:

```text
N_combined = N_substrate * g
Delta tau  = Delta t * N_combined
```

`N_combined` must remain inside explicit bridge authority bounds or the transition fails closed.

This is a phase-runtime proper-time variable. `laboratory_time_modified=false` is invariant.

## T^36 hydrodynamic coupling

The original v0.27 hydro gate identity is not mutated. The ORCH bridge creates a separate coupled-transition identity.

For normalized exact operator drive `d`:

```text
G_eff = rho I + u u^T
force = G_eff d
du/dtau = drive_gain * force - nu_eff * u
dtheta/dtau = u
```

The active orbital phase update is an explicit bridge projection from the T^36 dynamic displacement along `d`. Winding is computed from dynamics using the Foundation Pack form:

```text
Delta w = (Delta phi / 2pi) * (Delta t / Delta tau)
```

## OORP reduction

The reduction law is implemented exactly as a parameterized content-addressed object:

```text
Omega = lambda1*C + lambda2*R(S,I) - lambda3*Delta - lambda4*Xi
reduce iff Omega >= Omega_crit
```

Selection uses a separate explicit content-addressed `SelectionLaw`. Equal top scores inside non-negative `tie` fail closed. Negative tie tolerance is invalid and also fails closed.

Memory rule:

```text
no reduction -> no memory residue
reduction    -> content-addressed memory residue object
```

A memory residue is evidence only in this gate. Persistent memory write remains false and requires a separately authorized effect boundary.

## Exact v0.20 replay

The replay validator requires:

- exact v0.20 receipt schema and contract;
- recomputed receipt SHA-256 match;
- no external effects or free-form NL execution;
- contiguous Sigma chain;
- contiguous 1-based KAKU indices;
- exact operator ID and exact vector SHA-256 per occurrence;
- exact final Sigma binding;
- exact vector bytes supplied for every occurrence.

Repeated operators remain distinct occurrence orbitals.

## Direct v0.20 executor coupling

`src/phasenav_natural_code/orchorbital_executor_v27.py` implements `OrchCoupledExecutor`, an authority-neutral subclass of the frozen v0.20 `_Executor`.

For every call to `_transition()`:

```text
1. execute the original v0.20 `_Executor._transition()` first;
2. preserve the returned Sigma state and exact ExecutionStep unchanged;
3. revalidate the exact live 36D operator vector against that ExecutionStep;
4. append the exact KAKU occurrence to the dynamic ORCH process sphere;
5. run the ORCH × hydrodynamic T^36 side-car transition;
6. return the original v0.20 Sigma state.
```

The direct-coupling contract explicitly records:

```text
v020_sigma_semantics_modified = false
routing_authority_opened       = false
effect_authority_opened        = false
persistent_memory_write        = false
external_effects               = false
laboratory_time_modified       = false
```

Missing per-step hydrodynamic gate authority fails the coupled execution closed. The executor is single-run to prevent reuse of stale side-car state.

After v0.20 receipt construction, `bind_direct_trace_to_receipt()` requires exact equality of:

- program content ID;
- initial and final Sigma IDs;
- branch truth state;
- KAKU step count;
- every full KAKU step payload.

Only then is the direct trace bound to the final v0.20 receipt SHA-256. This binding does not modify the v0.20 receipt.

## Current validation

Committed ORCH core/replay feature harness:

```text
18/18 PASS
```

The broader development harness used while constructing the ORCH core reached `33/33 PASS`. The committed 18-test suite covers geometry anchoring, K_ij symmetry, observables, truth scalar, explicit subjective time, reduction/no-reduction behavior, ambiguity fail-closed, exact occurrence identity, vector and receipt tamper rejection, proper-time coupling, dynamic winding, exact replay order, deterministic trace identity, `AttractorLLMTemp` fail-closed without a decay schedule, and invalid negative selection-tie tolerance.

A separate direct-executor test module is now committed. It tests base-v0.20 vs coupled Sigma/step equality, one ORCH transition per actual KAKU transition, authority closure, phase-sidecar evolution, adjacency coupling, missing-gate fail-closed, exact receipt binding, receipt tamper rejection and deterministic configuration identity.

Those direct-executor tests were not run in the current worker because this worker exposes neither the repository source tree through a runnable checkout nor `/dev/shm/ciel_noema`. They remain `COMMITTED_NOT_RUN_IN_CURRENT_WORKER`, not PASS.

No fresh V56 live-runtime claim and no full historical-suite replay are made in this pass.

## Closure still required

Before v0.27 ORCH coupling may be release-closed:

1. execute the committed direct-executor conformance suite on the repository branch;
2. run against current tethered `/dev/shm/ciel_noema`;
3. revalidate all nine canonical v0.20 operator-vector byte hashes;
4. execute a fresh current-generation direct ORCH × hydro run inside `_Executor._transition()`;
5. construct the normal v0.20 receipt and bind the direct ORCH trace to it without changing receipt bytes;
6. extend inverse provenance from the receipt-bound ORCH trace through v0.22 lineage and v0.25 resident program/generation;
7. run the repository conformance suite;
8. keep manifest fail-closed until final-tree file-byte SHA-256 regeneration.
