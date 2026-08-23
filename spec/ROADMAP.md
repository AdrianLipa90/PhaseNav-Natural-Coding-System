# PNCS Engineering Roadmap

Status: v0.27 HYDRODYNAMIC PROPER-TIME + ORCHORBITAL OORP + DIRECT v0.20 SIDE-CAR IMPLEMENTED / CONFORMANCE + LIVE CLOSURE PENDING

## Completed foundation sequence

### v0.1–v0.19 — Semantic and 36D foundation
Structural KAKU/Radical relations, control/algebra, content-addressed hierarchy, registered natural/written surfaces, exact 36D realization binding and semantic mass binding.

### v0.20 — Native Execution Core

```text
canonical graph -> admitted internal route -> live /dev/shm/ciel_noema
-> Sigma_t --KAKU--> Sigma_t+1 -> deterministic result + receipt
```

### v0.21 — Mass-Aware Graph Cost
`C_M(G)=sum_i m_i`, separate from semantic identity/equivalence.

### v0.22 — Exact Inverse Execution Lineage
`Result -> SYSTEM -> ... -> DEFINITION -> RADICAL -> KAKU`. Isolated validation: `27/27 PASS`.

### v0.23 — Natural Program Composition
Registered bounded `IF / THEN / ELSE / AND THEN / RETURN`. Isolated validation: `28/28 PASS`.

### v0.24 — Native `.pnv` Program Units
First-class program CID, dependency closure, canonical `.pnv`, deterministic build receipt. Isolated validation: `29/29 PASS`.

### v0.25 — Persistent PNCS Runtime
Generation-bound residency, O(1) admission and exact live v0.20 -> v0.22 -> v0.25 dispatch closure. Isolated validation: `25/25 PASS`.

### v0.26 — Effect Boundary
Explicit `EffectRequest -> AuthorizationGrant -> bounded adapter -> EffectReceipt -> inverse provenance`. Isolated validation: `28/28 PASS`; first bounded `NOEMA_RUNTIME_RECORD_WRITE` effect class release-closed. Arbitrary filesystem, Git, network, subprocess/shell, device and external connectors remain closed.

## Current gate

### v0.27 — Hydrodynamic Proper-Time Runtime on T^36

Base substrate:

```text
state:      theta in T^36, flow u in R^36
substrate:  density rho > 0, effective damping nu_eff >= 0
c_s:        sqrt(rho)
lapse:      N_substrate = clip(c_s/(1+nu_eff), N_min, N_max)
dtau:       N_substrate dt
G_eff:      rho I + outer(u,u)
flow:       du/dtau = gamma (G_eff @ normalized_drive) - nu_eff u
phase:      dtheta/dtau = u
```

Base hydrodynamic validation already recorded:

```text
pure-core harness: 36/36 PASS
exact-KAKU schedule harness: 21/21 PASS
combined hydro harness: 57/57 PASS
previous live T^36 phase-flow witness: PASS
previous exact 9-occurrence v0.20 KAKU schedule witness: PASS
```

### v0.27 ORCHORBITAL × Hydrodynamic T^36 subgate

The existing ORCHORBITAL Foundation Pack is the formal authority above the hydrodynamic substrate:

```text
exact v0.20 KAKU occurrence
-> ORCHORBITAL orbital mode
-> explicit K_ij process sphere in M_rel
-> C / Delta / Delta_H / R_H / Theta / attractor observables
-> subjective-time g(r,C,Delta,m,A)
-> N_combined = N_substrate * g
-> hydrodynamic T^36 transition
-> orbital phase/winding update
-> OORP Omega reduction
-> optional memory residue
```

Foundation authority:

```text
repository: AdrianLipa90/CIEL-Omega-ApokalypOS
commit: aa0da54ef29a1f80dd0390427935342225388950
contracts: 02_ONTOLOGY_AND_OBSERVABLES.md
           03_STATE_SPACE_AND_BOUNDARY_CONDITIONS.md
           04_INVARIANTS_POTENTIALS_AND_ATTRACTORS.md
           05_ENTITY_REGISTRY_AND_SPHERE_EMBEDDING.md
           06_SUBJECTIVE_TIME_WINDING_AND_SEMANTIC_MASS.md
           07_OORP_PIPELINE_AND_MEMORY.md
```

ORCH invariants implemented:

- formal space is `M_rel` with projective Hilbert / Kähler / Fubini–Study anchor;
- Poincaré disk is operational chart, not ontology;
- Bloch is restricted to local reduced charts;
- every exact KAKU occurrence has a distinct orbital identity even when operator names repeat;
- exact operator-vector bytes are re-hashed as `<36d>` before orbital projection;
- `K_ij` is explicit, symmetric, bounded and currently adjacency-only for execution occurrences;
- `V_tot = V_EC + V_ZS + V_rel + V_mem + V_def + V_ext`;
- subjective time uses an explicit content-addressed parameterization of `g(r,C,Delta,m,A)`;
- reduction uses exactly `Omega=lambda1*C+lambda2*R-lambda3*Delta-lambda4*Xi` and `Omega>=Omega_crit`;
- no reduction means no memory residue;
- reduction produces evidence-only content-addressed residue, never a persistent memory write;
- ambiguous reduction selection fails closed;
- `AttractorLLMTemp` remains closed until an explicit decay schedule is implemented and receipt-bound;
- persistent memory writes, external effects, semantic identity mutation and laboratory-time claims remain closed.

Current validated ORCH core/replay evidence:

```text
committed compact conformance: 18/18 PASS
broader development harness: 33/33 PASS
exact occurrence identity: PASS
receipt tamper: FAIL-CLOSED PASS
operator-vector byte tamper: FAIL-CLOSED PASS
subjective-time parameterization: PASS
OORP reduction formula: PASS
no-reduction/no-memory-residue: PASS
ambiguous selection: FAIL-CLOSED PASS
AttractorLLMTemp without decay schedule: FAIL-CLOSED PASS
negative tie tolerance: FAIL-CLOSED PASS
T^36 coupled phase flow: PASS_ISOLATED
dynamic winding: PASS_ISOLATED
```

### Direct v0.20 transition coupling

`OrchCoupledExecutor` is now implemented as an authority-neutral subclass of the frozen v0.20 `_Executor`.

Each coupled transition executes in this order:

```text
original v0.20 `_Executor._transition()`
-> unchanged Sigma + unchanged ExecutionStep
-> exact live vector byte revalidation
-> dynamic ORCH occurrence/sphere append
-> ORCH × T^36 side-car transition
-> return original v0.20 Sigma
```

Direct-coupling invariants:

```text
v020_sigma_semantics_modified = false
routing_authority_opened       = false
effect_authority_opened        = false
persistent_memory_write        = false
external_effects               = false
laboratory_time_modified       = false
```

The executor requires an explicit hydrodynamic gate for every actual v0.20 step and fails closed if one is missing. It is single-run to prevent stale ORCH/T^36 state reuse.

A receipt-binding layer is also implemented. After normal v0.20 receipt construction it requires exact equality of program ID, Sigma endpoints, truth state, step count and every full KAKU step payload before binding the ORCH direct trace to the receipt SHA-256. The v0.20 receipt itself is never modified.

Direct-executor tests are committed for:

```text
base-v0.20 vs coupled Sigma/step equality
one ORCH transition per actual KAKU transition
authority closure
phase-sidecar evolution
adjacency-only dynamic sphere coupling
missing-gate fail-closed
exact v0.20 receipt binding
receipt tamper rejection
deterministic coupling configuration identity
```

These direct-executor tests are `COMMITTED_NOT_RUN_IN_CURRENT_WORKER`; the current worker has no runnable repository checkout and no `/dev/shm/ciel_noema` live surface. They are not reported as PASS.

### Remaining v0.27 release closure

1. run the committed direct-executor conformance tests on the real branch source tree;
2. run ORCHORBITAL × T^36 against a current tethered `/dev/shm/ciel_noema` generation;
3. revalidate all nine canonical v0.20 KAKU occurrence vector hashes against live operator bytes;
4. execute a fresh current-generation direct ORCH × hydro run inside `_Executor._transition()`;
5. construct the normal v0.20 receipt and bind the direct ORCH trace to it byte-exactly;
6. ensure ORCH state may affect admitted runtime conditions only through a separately specified authority rule, never by semantic/routing/effect-authority bypass;
7. bind inverse provenance `ORCH direct trace -> KAKU occurrence -> v0.20 receipt -> v0.22 lineage -> v0.25 resident program/generation`;
8. run the repository conformance suite;
9. keep `MANIFEST.sha256.json` fail-closed until final-tree file-byte SHA-256 regeneration.

No additional effect class opens in v0.27.

## Planned gates

### v0.28 — Fuzzing / Equivalence / Adversarial Parsing
Paraphrase/alias equivalence, ambiguity, malformed `.pnv`, typed-ID substitution, Unicode/confusable injection, hierarchy ambiguity, generation substitution, effect-request/authorization/adapter substitution, path traversal, tamper/replay, hydrodynamic-profile attacks, ORCH sphere/coupling substitution, reduction-law substitution, subjective-time-law adversarial cases and direct-executor side-car desynchronization.

### v0.29 — Performance Benchmark
Measure parsing, canonicalization, CID, realization, mass, resident admission, dispatch, ORCH observables/reduction, hydrodynamic integration, direct side-car overhead, effect authorization and bounded effect latency separately. Speedup claims require measured evidence.

### v0.30 — Self-Hosting Subset
Predicate resolver, route resolver, canonical path construction, receipt graph, ORCH state/reduction validation, hydrodynamic schedule validation and effect-request validation.

### v0.31 — PNCS Compiler / Runtime Contract
Freeze grammar, KAKU, radicals, hierarchy, CID rules, 36D contract, mass contract, program format, persistent runtime, execution semantics, ORCHORBITAL/OORP state model, hydrodynamic phase-time model, direct side-car contract, effect model, failure semantics and provenance model.

## v1.0 — Natural Coding System

```text
natural intent
-> deterministic relation resolution
-> canonical PNV graph
-> content-addressed program
-> exact 36D realization
-> semantic mass
-> persistent admitted native execution
-> ORCHORBITAL orchestration/reduction state
-> hydrodynamic T^36 phase-flow coupled per KAKU when registered
-> deterministic result
-> optional reduction residue
-> explicit authorized bounded effect when requested
-> complete inverse provenance
```

Required invariants:

```text
same semantics -> same canonical identity
ambiguity      -> fail closed
missing state  -> fail closed
ORCH reduction -> explicit content-addressed law
memory residue -> only after reduction
hydrodynamics  -> execution substrate, not semantic/routing/effect authority
effect         -> explicit separate authorization
result/effect  -> full provenance
```

Deliverables: full PNCS monograph, formal specification, reference implementation, native examples, benchmark corpus and conformance suite.
