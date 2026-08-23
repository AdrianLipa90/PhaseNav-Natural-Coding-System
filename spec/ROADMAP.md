# PNCS Engineering Roadmap

Status: v0.27 HYDRODYNAMIC PROPER-TIME CORE IMPLEMENTED / LIVE T^36 PHASE-FLOW PASS / ROUTING INTEGRATION PENDING

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

Executable local phase-time substrate:

```text
state:    theta in T^36, flow u in R^36
substrate: density rho > 0, effective damping nu_eff >= 0
c_s:      sqrt(rho)
lapse:    N = clip(c_s/(1+nu_eff), N_min, N_max)
dtau:     N dt
G_eff:    rho I + outer(u,u)
flow:     du/dtau = gamma (G_eff @ normalized_drive) - nu_eff u
phase:    dtheta/dtau = u
```

Current invariants:

- all phase coordinates remain in `[0,2pi)`;
- `G_eff` is symmetric positive semidefinite for positive density;
- hydrodynamic trace/state/gate identities are deterministic and content-addressed;
- speed overflow fails closed;
- semantic CIDs and program IDs are not modified by hydrodynamic state;
- laboratory time modification is explicitly not claimed;
- external effects remain closed;
- operational live source remains `/dev/shm/ciel_noema` with no static/Library fallback.

Validation:

```text
pure-core v0.27 harness: 36/36 PASS
live current-session T^36 phase-flow witness: PASS
live operator: TRANSFORM
post-witness fast admission: PASS
post-witness tether guard: ACTIVE / failures=[]
```

Live conformance comparison under equal coordinate time (`2.0`):

```text
slow: rho=.25, nu_eff=1.0, N=.25,   Delta tau=.5,      phase displacement=.0013392237603397628
fast: rho=4.0, nu_eff=.1, N=1.818,  Delta tau=3.63636, phase displacement=1.20475831040832
```

Current evidence status:

`IMPLEMENTED_CORE_AND_LIVE_T36_VALIDATED_ROUTING_INTEGRATION_PENDING`

Remaining v0.27 closure:

1. bind hydrodynamic profiles to exact program/KAKU occurrences;
2. run a current-generation v0.20 control path with the hydrodynamic schedule active;
3. preserve exact semantic/program identity while producing different hydrodynamic traces;
4. define an admitted rule for hydrodynamic state to influence routing/effect conditions without bypassing authority;
5. record complete inverse provenance for schedule + trace + result.

No additional effect class opens in v0.27.

## Planned gates

### v0.28 — Fuzzing / Equivalence / Adversarial Parsing
Paraphrase/alias equivalence, ambiguity, malformed `.pnv`, typed-ID substitution, Unicode/confusable injection, hierarchy ambiguity, generation substitution, effect-request/authorization/adapter substitution, path traversal, tamper/replay and hydrodynamic-profile adversarial cases.

### v0.29 — Performance Benchmark
Measure parsing, canonicalization, CID, realization, mass, resident admission, dispatch, hydrodynamic integration, effect authorization and bounded effect latency separately. Speedup claims require measured evidence.

### v0.30 — Self-Hosting Subset
Predicate resolver, route resolver, canonical path construction, receipt graph, hydrodynamic schedule validation and effect-request validation.

### v0.31 — PNCS Compiler / Runtime Contract
Freeze grammar, KAKU, radicals, hierarchy, CID rules, 36D contract, mass contract, program format, persistent runtime, execution semantics, hydrodynamic phase-time model, effect model, failure semantics and provenance model.

## v1.0 — Natural Coding System

```text
natural intent
-> deterministic relation resolution
-> canonical PNV graph
-> content-addressed program
-> exact 36D realization
-> semantic mass
-> persistent admitted native execution
-> hydrodynamic T^36 phase-flow schedule when registered
-> deterministic result
-> explicit authorized bounded effect when requested
-> complete inverse provenance
```

Required invariants:

```text
same semantics -> same canonical identity
ambiguity      -> fail closed
missing state  -> fail closed
hydrodynamics  -> execution substrate, not semantic authority
effect         -> explicit separate authorization
result/effect  -> full provenance
```

Deliverables: full PNCS monograph, formal specification, reference implementation, native examples, benchmark corpus and conformance suite.
