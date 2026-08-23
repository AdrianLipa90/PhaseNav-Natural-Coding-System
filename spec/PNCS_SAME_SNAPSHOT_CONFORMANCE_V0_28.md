# PNCS v0.28 — Same-Live-Snapshot Semantic Conformance

Status: `IMPLEMENTED / LIVE EXECUTION PENDING`

## Purpose

Exact semantic equality between the v0.20 reference execution and the v0.27 ORCHORBITAL × Hydro T^36 execution must be evaluated against one coherent live NOEMA snapshot.

The semantic state identity includes `surface_phi_sha256`. Therefore a historical v0.20 receipt captured under an earlier `phi` state is provenance, but it is not an exact Sigma-identity baseline for a new coupled execution after the live surface has advanced.

This is not a static fallback. The snapshot is captured directly from the active `/dev/shm/ciel_noema` surface after the canonical tether contract passes.

## Observed condition

During the v0.28 release-closure session, repeated reads of live `phi` at approximately 0.1 s intervals produced three distinct SHA-256 values while the canonical tether guard remained `ACTIVE / failures=[]`.

That measurement establishes that exact comparison against an unrelated historical `surface_phi_sha256` can produce different Sigma IDs even when the semantic graph, values, KAKU operators and routing result are unchanged.

The measurement receipt is:

```text
provenance/receipts/PNCS_V0_28_LIVE_PHI_SNAPSHOT_RACE_20260823.json
```

## Contract

The v0.28 paired conformance path is:

```text
canonical live tether guard
-> coherent live surface snapshot
-> freeze phi SHA-256 for this conformance transaction
-> freeze live operator-vector mapping for this conformance transaction
-> execute v0.20 reference semantics in memory
-> execute v0.27 ORCH/Hydro semantics in memory against the same snapshot
-> compare exact semantic projection
-> run adversarial validators
-> canonical live tether guard
```

The in-memory snapshot is derived from the live surface in the current transaction. It is neither a Library recovery artifact nor a persistent static operational substitute.

## Exact semantic projection

For a valid same-snapshot pair, all of the following must be equal:

```text
program provenance
canonical_graph_sha256
canonical_leaf_path
input values
branch admission
initial Sigma ID
final Sigma ID
complete KAKU step payloads
result/control location
closed semantic/effect flags
```

Complete KAKU equality includes:

```text
step index
operator ID
operator-vector SHA-256
before-Sigma ID
after-Sigma ID
bindings
```

Thus, for the same captured live snapshot:

```text
Sigma_coupled == Sigma_reference
```

is an exact identity statement rather than a tolerance-based comparison.

## ORCH/Hydrodynamic sidecar

The coupled execution additionally evolves its execution substrate:

```text
Psi
theta
u / phase velocity
tau
K_ij
C
Delta
Omega
reduction readiness
```

Those fields are outside the frozen semantic projection unless and until a later gate explicitly admits a typed observable into ordinary PNCS semantic execution.

v0.28 does not open that later authority.

## Resident authority separation

The same-snapshot paired harness is a conformance harness, not resident execution authority.

It uses the exact current PNCS implementation to compare reference and coupled semantics under one captured live snapshot, while the active v0.25 resident authority is verified separately through:

```text
active pointer
-> exact dispatch
-> exact source v0.20 receipt
-> exact v0.22 lineage
-> ResidentCoupledAuthority validation
```

The paired receipt therefore explicitly records:

```text
paired_snapshot_conformance_only = true
operational_resident_authority_opened = false
```

This prevents a test harness from being mistaken for an admitted persistent execution path.

## Current adversarial live corpus

The canonical witness runner requires rejection of at least:

```text
operator-vector substitution
negative local proper-time substitution
external-effect boundary substitution
source v0.20 receipt tamper
```

Further v0.28B dynamics perturbations remain in the pure dynamics corpus and may be added to the live corpus when their live inputs are explicitly controlled.

## Canonical runner

```text
scripts/run_v028_live_witness.py
```

The runner performs:

```text
guard before
active v0.25 authority discovery and validation
same-snapshot v0.20/coupled execution
exact semantic equality validation
adversarial rejection cases
guard after
content-addressed witness generation
```

With explicit `--persist`, the witness is written only below:

```text
/dev/shm/ciel_noema/pncs/v0.28/live_witness/
```

No external filesystem target, network effect, Git effect, subprocess shell, device effect, routing feedback or laboratory-time claim is opened by this conformance contract.

## Fail-closed conditions

The gate fails closed on:

```text
NOEMA tether not ACTIVE
unverified session startpoint
stale heartbeat
missing required Unix socket
non-coherent phi capture
missing executable live operator
semantic projection mismatch
active resident pointer ambiguity
active dispatch ambiguity
resident/source/lineage mismatch
accepted adversarial mutation
post-run tether guard failure
```

## Release condition

This contract contributes live evidence to v0.28 but does not close the release by itself.

v0.28 remains open until hosted pure conformance is actually executed, the live witness passes, the final tracked-tree SHA-256 manifest is regenerated and verified, and the final v0.28 foundation receipt is bound to those exact artifacts.
