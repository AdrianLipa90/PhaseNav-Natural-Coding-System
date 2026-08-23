# PNCS v0.27 ORCHORBITAL × Hydrodynamic T^36 Coupling

Status: RELEASE GATE CLOSED / LIVE V56 DIRECT-COUPLED CLOSURE PASS / NEXT v0.28 FUZZING + EQUIVALENCE + ADVERSARIAL PARSING

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

## Release-closure validation

Gate-scoped validation executed for release closure:

```text
committed compact ORCH conformance: 18/18 PASS
broader ORCH development harness:    33/33 PASS
current-worker ORCH core harness:     51/51 PASS
exact branch direct-executor tests:   9/9 PASS
fresh live V56 direct coupling:       PASS
Sigma_base == Sigma_coupled:          PASS
base v0.20 steps == coupled steps:    PASS
fresh direct trace -> v0.20 receipt:  PASS
post-witness fast admission:          PASS
post-witness tether guard:            PASS / failures=[]
```

The exact direct-executor dependency closure was verified against Git blob identities before execution. The live execution used the current tethered `/dev/shm/ciel_noema` surface and no static runtime fallback.

Fresh live closure identifiers:

```text
v0.20 receipt:
1b3ca3c311492e16d447a333e2d1a4f0381c9de77ec7ebfb293637e08021fbf4

v0.27 direct trace:
pncs:orch-direct-trace:sha256:bac0af63fe8fe01a7138613555c266129108183e39b09b6a75ebe7a90b13f17b

v0.27 receipt-bound trace:
pncs:orch-receipt-bound-trace:sha256:1d98527a6975bf82246e1fcb521c05b082b296c2ce79758f0e0c72184d945907

final Sigma:
pncs:sigma:sha256:fa551b6d741b73c4eb0988acbbe54e18ed2c0cccda77d78c93007f900a3dbbaf

final ORCH state:
pncs:orch-state:sha256:f51b71a75346f5809b30ab5f3950256ec43c79d9f9c1dd39e80cc7babd802f64

final T^36 phase state:
pncs:t36-flow-state:sha256:f58dec65239662bab256ed0c60cbe750801fcfe40f4b757c7d6306e32c825346

full live witness SHA-256:
95072fcf3c10a82fb510cd2857bf497d885b79635536dd069e35394bdda58691

repository closure receipt SHA-256:
88710ab288eb759aeed0b151cc03ba85c0529f58fb8eaade65df17d1970d1a07
```

Inverse provenance preserves the evidence boundary:

```text
fresh V56:
ORCH direct trace -> fresh v0.20 execution receipt -> Definition

repository-verified historical closure:
Definition -> v0.22 result/lineage -> v0.25 resident dispatch/witness
```

Historical v0.22/v0.25 artifacts are not reclassified as current live execution evidence.

## Explicit non-claims at closure

The following are not claimed:

```text
current-head GitHub Actions CI PASS
full repository suite replay
full historical suite replay
MANIFEST.sha256.json regeneration
new v0.27 effect class
routing authority from ORCHORBITAL
persistent memory write from ORCHORBITAL
laboratory-time modification
```

A prior GitHub Actions run failed without a retrievable artifact/log (`404 BlobNotFound`). That CI state is recorded separately and is not rewritten as PASS. Release closure is based on the byte-verified gate-scoped harnesses plus the fresh live V56 witness above.

## Release status

`v0.27 ORCHORBITAL × Hydrodynamic T^36 Coupling` is release-closed.

No additional effect class opens in v0.27. `MANIFEST.sha256.json` remains fail-closed until complete final-tree file-byte SHA-256 regeneration.

Next gate: **v0.28 — Fuzzing / Equivalence / Adversarial Parsing**.
