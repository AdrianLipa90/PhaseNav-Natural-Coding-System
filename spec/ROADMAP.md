# PNCS Engineering Roadmap

Status: v0.27 HYDRODYNAMIC PROPER-TIME + ORCHORBITAL OORP COUPLING IMPLEMENTED / LIVE COUPLED EXECUTOR CLOSURE PENDING

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

The existing ORCHORBITAL Foundation Pack is now the formal authority above the hydrodynamic substrate:

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
- subjective time uses an explicit content-addressed parameterization of the open Foundation function `g(r,C,Delta,m,A)`;
- reduction uses exactly `Omega=lambda1*C+lambda2*R-lambda3*Delta-lambda4*Xi` and `Omega>=Omega_crit`;
- no reduction means no memory residue;
- reduction produces evidence-only content-addressed residue, never a persistent memory write;
- ambiguous reduction selection fails closed;
- `AttractorLLMTemp` remains closed until an explicit decay schedule is implemented and receipt-bound;
- persistent memory writes, external effects, semantic identity mutation and laboratory-time claims remain closed.

Current ORCH validation:

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

The current worker does not expose `/dev/shm/ciel_noema`; therefore no new V56 live witness is claimed for this ORCH subgate.

### Remaining v0.27 release closure

1. run ORCHORBITAL × T^36 against a current tethered `/dev/shm/ciel_noema` generation;
2. revalidate all nine canonical v0.20 KAKU occurrence vector hashes against live operator bytes;
3. execute a fresh exact nine-occurrence ORCH × hydro run;
4. couple the same ORCH transition into current-generation `_Executor._transition()` rather than post-receipt replay;
5. ensure ORCH state may affect admitted runtime conditions only through a separately specified authority rule, never by semantic or effect-authority bypass;
6. bind inverse provenance `ORCH transition -> KAKU occurrence -> v0.20 receipt -> v0.22 lineage -> v0.25 resident program/generation`;
7. run the repository conformance suite;
8. keep `MANIFEST.sha256.json` fail-closed until final-tree file-byte SHA-256 regeneration.

No additional effect class opens in v0.27.

## Planned gates

### v0.28 — Fuzzing / Equivalence / Adversarial Parsing
Paraphrase/alias equivalence, ambiguity, malformed `.pnv`, typed-ID substitution, Unicode/confusable injection, hierarchy ambiguity, generation substitution, effect-request/authorization/adapter substitution, path traversal, tamper/replay, hydrodynamic-profile attacks, ORCH sphere/coupling substitution, reduction-law substitution and subjective-time-law adversarial cases.

### v0.29 — Performance Benchmark
Measure parsing, canonicalization, CID, realization, mass, resident admission, dispatch, ORCH observables/reduction, hydrodynamic integration, effect authorization and bounded effect latency separately. Speedup claims require measured evidence.

### v0.30 — Self-Hosting Subset
Predicate resolver, route resolver, canonical path construction, receipt graph, ORCH state/reduction validation, hydrodynamic schedule validation and effect-request validation.

### v0.31 — PNCS Compiler / Runtime Contract
Freeze grammar, KAKU, radicals, hierarchy, CID rules, 36D contract, mass contract, program format, persistent runtime, execution semantics, ORCHORBITAL/OORP state model, hydrodynamic phase-time model, effect model, failure semantics and provenance model.

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
-> hydrodynamic T^36 phase-flow when registered
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
hydrodynamics  -> execution substrate, not semantic/effect authority
effect         -> explicit separate authorization
result/effect  -> full provenance
```

Deliverables: full PNCS monograph, formal specification, reference implementation, native examples, benchmark corpus and conformance suite.
