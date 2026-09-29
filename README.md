# PhaseNav Natural Coding System (PNCS)

PhaseNav Natural Coding System is a 36-dimensional relational coding system in which written code is a human-readable projection of a canonical semantic-phase graph.

```text
KAKU -> RADICAL -> DEFINITION -> CLASS -> FILE -> CLUSTER
     -> SUBSYSTEM/DAEMON -> LOW_ORCHESTRATOR -> HIGH_ORCHESTRATOR -> SYSTEM
```

Natural-language admission resolves deterministically to registered canonical relations. Unknown, ambiguous, unsupported, or unregistered semantics fail closed.

## Release authority

The release-critical state is governed by:

- `spec/PNCS_V1_RELEASE_TRAIN_V0_1.md`
- `src/phasenav_natural_code/release_train_v1.py`
- `native/PNCS_V1_RELEASE_TRAIN_V0_1.pnv`
- `provenance/receipts/FOUNDATION_STATUS_V0_28.json` for the v0.28 promotion verdict
- `MANIFEST.sha256.json` for the tracked-tree file-byte SHA-256 authority

Absence or failure of a preregistered gate blocks stage advancement.

Current release train:

```text
v0.28 release closure
-> v0.29 release hardening
-> v0.30 release candidate
-> v1.0
```

The v1.0 train is scope-frozen. Research artifacts remain preserved through the post-v1 quarantine registry and carry zero release-gate authority unless a later explicit release contract admits them.

## Operational 36D authority

Operational 36D execution authority is the live `/dev/shm/ciel_noema` surface. Repository and Library artifacts provide persistence, recovery, specification, and provenance. Live admission is fail-closed and requires the canonical tether guard.

## Closed engineering foundation

```text
v0.1-v0.19 semantic + exact 36D foundation
v0.20 native internal execution
v0.21 mass-aware graph cost
v0.22 exact inverse execution lineage
v0.23 bounded natural program composition
v0.24 first-class native .pnv program units
v0.25 persistent resident runtime
v0.26 explicit bounded effect boundary
v0.27 ORCHORBITAL-coupled T^36 hydrodynamic proper-time runtime
```

`v0.27` has canonical status `PASS_RELEASE_CLOSED` in `provenance/receipts/FOUNDATION_STATUS_V0_27.json`.

The v0.27 live authority binds the frozen v0.20 semantic execution to v0.22 inverse lineage, v0.25 residency, ORCHORBITAL state, and the hydrodynamic `T^36` phase substrate. Semantic projection equality is verified against the frozen v0.20 operator order, operator-vector byte hashes, bindings, program provenance, branch truth, and result location.

Canonical v0.27 evidence includes:

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

## v0.28 release closure

The v0.28 release gate closes the already-implemented adversarial/conformance layer. It adds no release feature scope.

Required gate set:

```text
exact_adversarial_authority
exact_execution_orch_v27
orch_hydro_regressions
full_repository_conformance
live_v56_same_snapshot_witness
tests_live
final_manifest
foundation_status_v028
```

The repository contains the pure structural/authority, semantic-equivalence, ORCHORBITAL × Hydro adversarial-dynamics, branch/session collision, manifest-tool, repository-conformance, and live-test suites.

The existing live-gate receipt records a V56 same-snapshot adversarial PASS, semantic projection equality, four rejected adversarial mutations, and exact release-critical Git blob identities. Release-critical runtime blobs are rechecked against the current repository head during closure.

Final promotion authority is `provenance/receipts/FOUNDATION_STATUS_V0_28.json`, bound to the complete tracked-tree SHA-256 manifest and exact closure evidence.

## v0.29 release hardening

After v0.28 closure, v0.29 is reserved for release hardening:

```text
clean installation
reproducible package
deterministic replay
public API freeze
documentation freeze
live soak
no-static-fallback proof
complete release provenance
```

The repository also preserves research artifacts whose internal contract names contain `V0_29`. Their epistemic/read-only ledgers remain authoritative for those artifacts; release-stage promotion authority comes only from the frozen v1.0 release train.

## v0.30 release candidate

The release-candidate gate is limited to:

```text
release-candidate build
clean-room replay
zero critical regressions
final version + changelog
tag payload / manifest identity match
```

Passing the complete v0.30 gate advances the frozen train to `V1_0_RELEASED`.

## Post-v1 quantum application runtime candidate

The post-v1 research branch now defines a native quantum-application state contract:

- `spec/PNCS_QUANTUM_APPLICATION_RUNTIME_V0_1.md`
- `native/PNCS_QUANTUM_APPLICATION_RUNTIME_V0_1.pnv`

The application state remains multidimensional PhaseNav/relational state until an explicit observation boundary. Existing Boolean predicates, PASS/FAIL, readiness and release gates remain classical control/projection metadata and do not replace the running application state.

For a declared two-outcome observable, only the explicit observation boundary may emit `0` or `1`.

This work is post-v1 research and carries zero authority over the scope-frozen v1.0 release train.

## Post-v1 research registry

The current release policy preserves research work including Prime-Temporal Hydro, Radical Engine, 1024-ion embedding, PrimeFlow v0.2, Temporal Geometry v0.2, and non-coboundary prime-interaction work under the post-v1 registry.

Temporal Geometry v0.2 is retained as `POST_V1_EXPERIMENTAL`, `READ_ONLY`, with `PURE_MEASUREMENT_PROJECTION` authority. Its evidence ledger remains separate from release-stage evidence.

## Repository layout

```text
src/          Python reference implementation
native/       PNCS-native .pnv contracts
spec/         normative specifications and release policy
registry/     canonical registries
tests/        pure and live conformance suites
scripts/      tether, live-witness, and manifest tooling
provenance/   content-addressed ledgers and release receipts
docs/         monograph and supporting documentation
```

## Manifest discipline

`scripts/regenerate_manifest.py` computes SHA-256 over every Git-tracked regular file in lexicographic path order, excluding only the manifest itself and the v0.28 foundation receipt. The resulting `MANIFEST.sha256.json` binds the declared source commit/tree, file count, per-file byte hashes, and aggregate entries hash.

Release packaging requires an authoritative manifest generated from the final release tree and verified by the same tool.

## Roadmap

The authoritative release sequence is `spec/PNCS_V1_RELEASE_TRAIN_V0_1.md`. Engineering status and stage-specific gates are summarized in `spec/ROADMAP.md`.
