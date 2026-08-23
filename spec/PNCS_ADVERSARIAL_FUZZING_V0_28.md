# PNCS v0.28 — Fuzzing / Equivalence / Adversarial Parsing

Status: CURRENT-MAIN INTEGRATION GATE / RELEASE NOT CLOSED

## Purpose

v0.28 tests whether PNCS preserves identity for representation-only equivalences while rejecting substitutions that alter execution semantics, provenance, T^36/ORCH coupling, resident/effect authority, typed identities, or branch/session write safety.

This document describes the v0.28 release-closure port based on the release-closed v0.27 implementation currently on `main`. The older parallel `orchorbital_*` draft is not authoritative and is not imported into this gate.

## Gate decomposition

v0.28 is split into three independent fail-closed sub-gates:

```text
v0.28A  semantic / receipt / authority adversarial conformance
v0.28B  ORCHORBITAL x Hydro T^36 adversarial dynamics
v0.28C  branch / session collision safety
```

Release closure requires all three pure gates, the separate live `/dev/shm/ciel_noema` replay, and regeneration of the complete final-tree manifest.

## v0.28A — Current semantic and authority boundary

The current validator targets the official v0.27 coupled execution receipt:

```text
trusted v0.20 execution receipt
-> exact semantic projection
-> KAKU step chain
-> official v0.27 ORCH hydrodynamic occurrences
-> content-addressed coupled receipt
```

A mutation helper recomputes both the semantic-projection digest and the outer coupled-receipt digest. A rejection therefore cannot pass merely because the attacker left a stale outer checksum.

When a trusted v0.20 source receipt is supplied, `validate_coupled_receipt_structure()` requires the coupled semantic projection to remain exactly equal to the source v0.20 program, graph identity, leaf path, input values, admission, Sigma endpoints, KAKU steps, result, and closed authority flags.

### REJECT corpus

```text
Unicode/confusable operator substitution
registered-operator substitution
operator-vector SHA-256 substitution
initial Sigma substitution
final Sigma substitution
program Definition/CID substitution
branch truth-state substitution
KAKU truncation
KAKU step-index discontinuity
Sigma-chain discontinuity
ORCH occurrence-count substitution
duplicate ORCH occurrence identity
ORCH/KAKU operator mismatch
ORCH/KAKU vector mismatch
external-effect boundary substitution
negative/non-finite local proper-time rejection
program-authority identity substitution
source v0.20 receipt tamper
```

The Unicode witness uses U+041E CYRILLIC CAPITAL LETTER O and is intentionally not normalized into the ASCII operator namespace.

### Representation-equivalence corpus

```text
mapping insertion-order changes -> same canonical digest
mapping insertion-order changes -> same validated receipt identity
effect payload mapping insertion-order changes -> same effect request identity
```

These are representation changes only and do not reorder execution semantics.

## v0.28B — ORCHORBITAL x Hydro T^36 adversarial dynamics

The dynamics gate exercises the actual pure v0.27 ORCH/Hydro transition substrate rather than inventing additional authority fields in the outer execution receipt.

For two occurrences bound to the same semantic KAKU occurrence, the semantic projection is frozen as:

```text
(step_index,
 operator_id,
 operator_vector_sha256,
 before_sigma_id,
 after_sigma_id)
```

A bounded substrate perturbation may change phase state, ORCH state, coupling matrix, proper-time advance, or the content-addressed dynamics witness, but it must not change that semantic projection.

The current pure adversarial dynamics corpus covers:

```text
density rho perturbation
effective-viscosity nu_eff perturbation
coupling-scale / K_ij perturbation
bounded T^36 phase noise
non-finite or wrong-dimensional phase noise
negative density
negative effective viscosity
non-finite phase state
negative local proper time
non-finite subjective-time kernel
max-speed instability
asymmetric K_ij injection
non-finite K_ij injection
out-of-range coupling scale
false reduction-ready injection
selection before reduction threshold
residue injection without reduction
selected-orbital residue substitution
operator substitution
operator-vector substitution
Sigma endpoint substitution
explicit subjective-time-kernel variation
```

The required invariants are:

```text
K_ij is 36x36, finite, symmetric, zero diagonal, bounded in [0,1]
C in [0,1]
Delta in [0,1]
Delta = 1-C
Omega matches the explicit reduction kernel
reduce_ready iff Omega >= Omega_crit
no reduction -> no stable memory residue
no explicit selected orbital -> no stable memory residue
reduction + explicit selection -> exactly bound residue
substrate perturbation -> no implicit routing/effect authority
```

## v0.28C — Branch / Session Collision Gate

The collision gate is pure-core and remains separate from Git authorization. It binds exact target/source refs and live session leases before an external Git adapter may be invoked.

Required sequence:

```text
read exact target/source refs
-> acquire/verify session lease(s)
-> content-addressed WriteIntent
-> collision admission
-> immediately re-read refs and leases
-> revalidate same admission
-> one non-force Git write/merge effect
-> exact parent verification
-> FinalizeReceipt
```

A moved ref, active foreign lease, stale admission, or parent mismatch is `BLOCKED`. No hidden retry, automatic rebase, force push, or automatic merge is permitted after a blocked verdict.

The gate does not itself open Git authority.

## Effect authorization adversarial corpus

The v0.26 Effect Boundary is regression-tested for:

```text
payload substitution
generation substitution
request-ID substitution
adapter substitution
payload-size scope substitution
multiple explicit grants / ambiguity
unknown adapter rejection
network/Git-capable adapter rejection
path-looking payload remains data only
target/effect-kind substitution
DENY/delegating/non-exact/lowercase authority rejection
exact helper binding to request + generation + adapter
```

No new effect class is opened.

## CI separation

Hosted CI is split into independent pure jobs:

```text
structural-authority
dynamics-pure
concurrency-pure
```

Live NOEMA evidence is a separate manual self-hosted gate:

```text
canonical tether guard
-> /dev/shm/ciel_noema ACTIVE
-> exact current v0.20 + v0.27 authority replay
-> in-memory adversarial mutations
-> fail-closed v0.28 validation
```

Hosted CI must not fail merely because a live NOEMA surface is absent.

## Evidence boundary

The old PR #12 live witness is not carried forward because it refers to the superseded parallel `DirectCoupledTrace` implementation. A fresh current-main live witness is required before v0.28 release closure.

The gate does not currently claim:

- full historical-suite replay,
- current-main live V56 adversarial replay PASS,
- Git-adapter enforcement of the collision gate,
- v0.28 release closure,
- new routing/effect authority,
- laboratory-time modification,
- a static runtime fallback.

## Release-closure conditions

`PASS_RELEASE_CLOSED` is permitted only after all of the following are established:

```text
v0.28A pure structural/authority corpus PASS
v0.28B pure adversarial dynamics corpus PASS
v0.28C pure collision corpus PASS
fresh current-main live V56 adversarial witness PASS
canonical tether guard ACTIVE / failures=[]
complete final-tree SHA-256 manifest regenerated and verified
foundation receipt bound to exact source commit/tree and evidence IDs
```

`MANIFEST.sha256.json` remains fail-closed until complete final-tree file-byte SHA-256 regeneration.
