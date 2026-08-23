# PhaseNav Natural Code System (PNCS)

Status: ORCHORBITAL_HYDRODYNAMIC_PROPER_TIME_V0_27 / RELEASE GATE CLOSED / NEXT v0.28 FUZZING + EQUIVALENCE + ADVERSARIAL PARSING

PhaseNav Natural Code System is a 36-dimensional relational coding system in which written code is a human-readable projection of a canonical semantic-phase graph.

```text
KAKU -> RADICAL -> DEFINITION -> CLASS -> FILE -> CLUSTER
     -> SUBSYSTEM/DAEMON -> LOW_ORCHESTRATOR -> HIGH_ORCHESTRATOR -> SYSTEM
```

Natural language is admitted only after deterministic resolution to registered canonical relations. Unknown, ambiguous, unsupported or unregistered semantics fail closed.

Operational 36D execution remains fixed to `/dev/shm/ciel_noema`. Repository/Library artifacts are persistence and provenance inputs only and are never an operational fallback.

## Closed engineering sequence

```text
v0.20 native internal execution
v0.21 mass-aware graph cost
v0.22 exact inverse execution lineage
v0.23 bounded natural program composition
v0.24 first-class native .pnv program units
v0.25 persistent resident runtime
v0.26 explicit bounded effect boundary
v0.27 ORCHORBITAL-coupled T^36 hydrodynamic proper-time runtime
```

## v0.25 resident execution authority

```text
resident program
-> O(1) admission
-> v0.20 control execution
-> exact v0.22 lineage
-> deterministic v0.25 dispatch receipt
```

Canonical dispatch:

```text
pncs:resident-dispatch:sha256:fd18f2d0296321d432a49e699d2f72a0a03313ed2dcc87b9aba647555f12c2e2
```

## v0.26 Effect Boundary

Effects remain a separate authority layer:

```text
v0.25 dispatch
-> EffectRequest
-> explicit AuthorizationGrant
-> registered bounded adapter
-> effect
-> EffectReceipt
-> inverse provenance
```

The only opened v0.26 effect class is `NOEMA_RUNTIME_RECORD_WRITE`, fixed to immutable content-addressed records below `/dev/shm/ciel_noema/pncs/v0.26/effects/records/`. Arbitrary filesystem, Git, network, subprocess/shell, device and external connector effects remain closed.

## v0.27 ORCHORBITAL + hydrodynamic proper time

v0.27 binds the existing ORCHORBITAL Foundation Pack to the PNCS `T^36` execution substrate. Normative ORCHORBITAL authority is pinned to `AdrianLipa90/CIEL-Omega-ApokalypOS` commit `aa0da54ef29a1f80dd0390427935342225388950`, Foundation Pack documents 02–07.

State-space binding:

```text
base relational manifold: M_rel
geometric anchor: projective Hilbert / Kahler / Fubini-Study
T^36: 36 internal phase modes of a process sphere
Psi_t = {o_i(t)} i=1..36
```

Each exact semantic transition now advances two separated but synchronously bound states:

```text
Sigma_t
-> exact semantic KAKU mutation
-> ORCHORBITAL bind / K_ij / attractor field
-> local subjective-time binding
-> hydrodynamic T^36 phase-flow
-> OORP observables + reduction readiness
-> Sigma_(t+1) + phase-state_(t+1)
```

Foundation observables retained by the implementation include global coherence `C(t)`, defect `Delta=1-C`, holonomic defect `Delta_H`, relational decoherence `R_H`, total potential `V_tot`, attractor weights, subjective time, winding and reduction readiness.

Subjective-time authority remains:

```text
Delta tau_i(k) = Delta t * g(r_i, C_i, Delta_i, m_i, A_i)
```

Because the Foundation Pack does not freeze a unique closed form for `g`, PNCS uses an explicit content-addressed parametric kernel whose coefficients and signs are receipt-bound policy. No physical calibration is claimed.

Hydrodynamic substrate:

```text
N_substrate = clip(sqrt(rho)/(1+nu_eff))
G_eff = rho I + outer(u,u)
g_combined = clip(N_substrate * g_orb)
Delta tau = Delta t * g_combined
```

OORP reduction remains explicit:

```text
Omega = lambda1*C + lambda2*R(S,I) - lambda3*Delta - lambda4*Xi
reduce_ready iff Omega >= Omega_crit
```

Reduction readiness does not select an orbital. Stable memory residue is emitted only after reduction plus explicit state selection. Raw input is not written as stable memory.

## v0.27 live release witness

```text
source v0.20 receipt:
84d40f600a8aa9e59ebc6dc42c856bcffec9265d04f791e7f5c49cdba2d583ad

v0.22 lineage:
pncs:lineage:sha256:34bd13f534987989ab212b5a6906d0cfa762305ee9a87af7a058badd2b2bcfd6

v0.25 dispatch:
pncs:resident-dispatch:sha256:fd18f2d0296321d432a49e699d2f72a0a03313ed2dcc87b9aba647555f12c2e2

resident coupled authority:
pncs:resident-coupled-authority:sha256:ce6193ec23511cca7ec363497240b88dc3a3755f07c09e8c01be84a2253b597b

v0.27 coupled receipt:
7c9191faa9534f431cb4907cad29b2028fab78a8284624702e53036e2bccbd5d

live witness:
e22472653144b75fc54eed550610a2d6f2026fe5aa347aea2a95ae0f776a129e
```

Independent alternate `g` profile witness:

```text
alternate coupled receipt:
10a616ae909b3eaf24744feafcf7d41c3eda60e9a7d9e3c29c519e8d5aa52b45

baseline phase proper time: 0.053033008588991064
alternate phase proper time: 0.02321325805214923
```

The semantic projection is identical across these two profiles; only the ORCHORBITAL/hydrodynamic phase-flow state and local phase proper time differ.

The live coupled execution contains 9 semantic KAKU transitions and 9 ORCHORBITAL occurrences. Its semantic projection matches the frozen v0.20 authority in operator order, exact operator-vector byte hashes, bindings, program provenance, branch truth and result location.

Validation:

```text
hydrodynamic pure core: 36/36 PASS
exact KAKU schedule: 21/21 PASS
full v0.27 harness: 134/134 PASS (130 isolated + 4 package regression)
live ORCHORBITAL-coupled execution: PASS
resident v0.25 authority binding: PASS
v0.22 lineage binding: PASS
semantic projection against frozen v0.20: PASS
post-witness fast admission: PASS
post-witness tether guard: ACTIVE / failures=[]
package-relative import regression: 4/4 PASS
```

## Closed boundaries

v0.27 does not open:

```text
ORCHORBITAL/hydrodynamic state -> semantic routing feedback
implicit reduction selection
raw-input stable memory update
external memory-store write
additional effect classes
physical laboratory-time dilation claim
static/Library operational fallback
```

The coupled model controls local phase/runtime evolution. It does not claim modification of laboratory time.

The complete historical repository suite was not replayed and is not claimed.

## Roadmap

The authoritative roadmap is `spec/ROADMAP.md`.

Next gate: **v0.28 — Fuzzing / Equivalence / Adversarial Parsing**.

## Manifest status

`MANIFEST.sha256.json` remains fail-closed. A complete file-byte SHA-256 manifest must be regenerated from the final release tree before release packaging. Git blob SHA-1 values are not substitutes for file SHA-256 values.
