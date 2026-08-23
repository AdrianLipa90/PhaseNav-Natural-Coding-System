# PNCS v0.28 — Fuzzing / Equivalence / Adversarial Parsing

Status: CURRENT-MAIN INTEGRATION GATE / RELEASE NOT CLOSED

## Purpose

v0.28 tests whether PNCS preserves identity for representation-only equivalences while rejecting substitutions that alter execution semantics, provenance, T^36/ORCH coupling, resident/effect authority, or typed identities.

This document describes the v0.28 port rebased onto the release-closed v0.27 implementation currently on `main`. The older parallel `orchorbital_*` draft is not authoritative and is not imported into this gate.

## Current boundary

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

## Current REJECT corpus

The current-main gate covers:

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

## Current EQUIVALENCE corpus

```text
mapping insertion-order changes -> same canonical digest
mapping insertion-order changes -> same validated receipt identity
effect payload mapping insertion-order changes -> same effect request identity
```

These are representation changes only and do not reorder execution semantics.

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

## Evidence boundary

This rebase deliberately does **not** carry forward the old PR #12 live witness because that witness refers to the superseded parallel `DirectCoupledTrace` implementation. A fresh current-main live witness must be produced before v0.28 release closure if live evidence is required.

The gate does not claim:

- full historical-suite replay,
- current-main live V56 adversarial replay,
- v0.28 release closure,
- new routing/effect authority,
- laboratory-time modification,
- a static runtime fallback.

`MANIFEST.sha256.json` remains fail-closed until complete final-tree file-byte SHA-256 regeneration.
