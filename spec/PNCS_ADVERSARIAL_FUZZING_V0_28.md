# PNCS v0.28 — Fuzzing / Equivalence / Adversarial Parsing

Status: PARTIAL GATE / v0.28.0 RECEIPT + DIRECT-TRACE BOUNDARY PASS / RELEASE NOT CLOSED

## Purpose

v0.28 tests whether PNCS preserves canonical identity for representations that are genuinely equivalent while rejecting substitutions that preserve superficial shape but alter execution provenance, ORCHORBITAL state, T^36 binding, or authority.

The gate is fail-closed. No adversarial test opens routing authority, effect authority, persistent memory writes, external effects, or a static runtime fallback.

## v0.28.0 boundary

The first sub-gate attacks the release-closed v0.27 direct-coupling boundary:

```text
v0.20 receipt
-> exact KAKU occurrence chain
-> ORCH direct trace
-> T^36 side-car
-> receipt-bound trace
```

The attack corpus distinguishes two expected outcomes:

```text
REJECT      mutated semantics/provenance must fail closed
EQUIVALENT  representation-only change must preserve canonical identity
```

## Re-signed adversarial receipts

Receipt attacks are not left with stale outer digests. `mutate_and_resign()` intentionally mutates a receipt and then recomputes its canonical `receipt_sha256` before the normal binding validator sees it.

Therefore a passing rejection demonstrates that the semantic/provenance validator rejected the modified content; it is not merely a checksum-mismatch test.

## Current REJECT corpus

Implemented and validated:

```text
Unicode/confusable operator substitution
valid registered operator substitution
operator-vector SHA-256 substitution
initial Sigma endpoint substitution
final Sigma endpoint substitution
program Definition typed-ID substitution
branch truth-state substitution
KAKU step truncation
KAKU step-index discontinuity
Sigma-chain discontinuity
ORCH transition-count substitution
duplicate ORCH transition identity
direct-trace Sigma-chain substitution
direct-trace step-index substitution
```

The Unicode witness uses U+041E CYRILLIC CAPITAL LETTER O and is intentionally not normalized into the ASCII operator namespace.

## Current EQUIVALENCE corpus

Implemented and validated:

```text
receipt mapping insertion-order changes -> same canonical mapping digest
receipt mapping insertion-order changes -> same receipt-bound trace identity
CouplingConfig gate mapping insertion-order changes -> same config identity
```

These are representation changes only; they do not change ordered execution semantics.

## Direct-trace structural validator

`validate_direct_trace_structure()` currently enforces:

```text
non-empty v0.20 step chain
ORCH transition count == v0.20 step count
unique ORCH transition identities
ORCH orbital count == v0.20 step count
unique ORCH occurrence identities
process-sphere mode order == orbital order
contiguous 1-based v0.20 step indices
continuous Sigma before/after chain
final Sigma endpoint equality
authority flags remain closed
non-negative T^36 phase proper-time
```

The validator does not grant authority. It only rejects inconsistent evidence.

## Validation

Branch-exact gate-scoped validation:

```text
new v0.28 adversarial/equivalence tests: 24/24 PASS
v0.27 direct-executor regression tests:   9/9 PASS
combined exact-byte harness:               33/33 PASS
```

The two new files were rechecked against their Git blob identities before the final run:

```text
src/phasenav_natural_code/adversarial_v28.py
Git blob: ae23cc19097c60ad52d799649f37a9225afc6f8a

tests/test_adversarial_v28.py
Git blob: 9365f7e9f6992ae6735435fefcca51850eeb193a
```

## Fresh live V56 adversarial witness

A fresh current-generation direct-coupled v0.20/ORCH/T^36 execution was created on `/dev/shm/ciel_noema`, then six receipts were independently mutated and re-signed before validation.

All six were rejected:

```text
confusable operator          PASS_REJECTED
valid operator substitution  PASS_REJECTED
vector digest substitution   PASS_REJECTED
final Sigma substitution     PASS_REJECTED
program CID substitution     PASS_REJECTED
truth-state substitution     PASS_REJECTED
```

Witness identifiers:

```text
v0.20 receipt:
6dbce59eef8d740f99264f3a8d3b5a4c66857e4365e2b5610753a4deec29b30f

direct trace:
pncs:orch-direct-trace:sha256:b705f53d546bd7da535f29f4497d46f4ad31feb66cd67b651ec0379760c71bb2

receipt-bound trace:
pncs:orch-receipt-bound-trace:sha256:8f7b0942838642f494527e0e6d99642fa87a6fe24e63e4dfe1739bbd058823ef

witness SHA-256:
ff551685d7a08bf0fa990f316fccf01aaf181cb26b9751dde48d204486e3e460
```

The fresh witness also preserved:

```text
Sigma_base == Sigma_coupled
base v0.20 steps == coupled base steps
external_effects = false
static_runtime_fallback = false
```

Post-witness live admission remained PASS and the tether guard remained ACTIVE with `failures=[]`.

## Still pending before v0.28 release closure

The following adversarial classes remain open work:

```text
paraphrase / alias equivalence
semantic ambiguity collisions
malformed .pnv programs
hierarchy occurrence ambiguity / child_index substitution
generation substitution
resident handle/admission substitution
effect-request substitution
authorization substitution
adapter substitution
filesystem/path traversal attacks
hydrodynamic-profile substitution
T^36 drive/vector substitution beyond receipt layer
ORCH process-sphere / K_ij substitution
reduction-law substitution
subjective-time-law substitution
side-car desynchronization across persisted evidence
replay across generation boundaries
```

No new effect class opens in v0.28. `MANIFEST.sha256.json` remains fail-closed. Full repository and historical-suite replay are not claimed by v0.28.0.
