# PNCS Engineering Roadmap

Status: v0.27 ORCHORBITAL × HYDRODYNAMIC T^36 RELEASE GATE CLOSED / CURRENT GATE v0.28 FUZZING + EQUIVALENCE + ADVERSARIAL PARSING

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

### v0.27 — Hydrodynamic Proper-Time Runtime + ORCHORBITAL OORP

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

ORCHORBITAL direct-coupling chain:

```text
exact v0.20 KAKU occurrence
-> unchanged v0.20 Sigma + ExecutionStep
-> exact live operator-vector byte revalidation
-> ORCHORBITAL occurrence / K_ij process sphere
-> C / Delta / Delta_H / R_H / Theta / attractor observables
-> subjective-time g(r,C,Delta,m,A)
-> N_combined = N_substrate * g
-> hydrodynamic T^36 transition
-> orbital phase/winding update
-> OORP Omega reduction
-> optional evidence-only memory residue
-> return unchanged v0.20 Sigma
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

Release-closure evidence:

```text
committed compact ORCH conformance: 18/18 PASS
broader ORCH development harness:    33/33 PASS
current-worker ORCH core harness:     51/51 PASS
exact branch direct-executor tests:   9/9 PASS
fresh live V56 direct coupling:       PASS
Sigma_base == Sigma_coupled:          PASS
base steps == coupled base steps:     PASS
fresh direct trace -> v0.20 receipt:  PASS
post-witness fast admission:          PASS
post-witness tether guard:            PASS / failures=[]
```

Fresh closure identities:

```text
v0.20 receipt:
1b3ca3c311492e16d447a333e2d1a4f0381c9de77ec7ebfb293637e08021fbf4

v0.27 direct trace:
pncs:orch-direct-trace:sha256:bac0af63fe8fe01a7138613555c266129108183e39b09b6a75ebe7a90b13f17b

v0.27 receipt-bound trace:
pncs:orch-receipt-bound-trace:sha256:1d98527a6975bf82246e1fcb521c05b082b296c2ce79758f0e0c72184d945907

full live witness SHA-256:
95072fcf3c10a82fb510cd2857bf497d885b79635536dd069e35394bdda58691

closure receipt SHA-256:
88710ab288eb759aeed0b151cc03ba85c0529f58fb8eaade65df17d1970d1a07
```

v0.27 keeps all of these boundaries closed:

```text
routing authority from ORCHORBITAL
new effect authority
persistent memory write from ORCHORBITAL
external effects from the side-car
semantic identity mutation
laboratory-time modification
continuation execution opening
RETURN execution opening
static/Library operational fallback
```

`AttractorLLMTemp` remains closed until an explicit decay schedule is implemented and receipt-bound.

The complete historical repository suite was not replayed and current-head GitHub Actions CI PASS is not claimed. A prior Actions failure without retrievable artifact/log remains recorded separately.

## Current gate

### v0.28 — Fuzzing / Equivalence / Adversarial Parsing

Required attack and equivalence classes:

```text
paraphrase / alias equivalence
ambiguity collisions
malformed .pnv
canonical typed-ID substitution
Unicode / confusable injection
hierarchy occurrence ambiguity
generation substitution
effect-request substitution
authorization substitution
adapter substitution
path traversal
tamper / replay
hydrodynamic-profile substitution
ORCH process-sphere / K_ij substitution
reduction-law substitution
subjective-time-law substitution
direct-executor side-car desynchronization
operator-vector byte substitution
Sigma endpoint substitution
receipt-bound trace substitution
```

Required invariants:

```text
same admitted semantics -> same canonical identity
ambiguous semantics -> fail closed
wrong typed identity -> fail closed
wrong generation -> fail closed
wrong exact KAKU occurrence -> fail closed
side-car desynchronization -> fail closed
ORCH/T^36 state must not acquire routing or effect authority
Effect Boundary authorization remains separate
no static runtime fallback
```

No new effect class opens automatically in v0.28.

## Planned gates

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

## Manifest status

`MANIFEST.sha256.json` remains fail-closed. Complete final-tree file-byte SHA-256 regeneration is required before final release packaging. Git blob SHA-1 values are not substitutes for file SHA-256 values.
