# PNCS Native PNV Exec Tool v0.1

Status: `POST_V1_EXPERIMENTAL / FAIL_CLOSED / ZERO_RELEASE_GATE_AUTHORITY`

## Purpose

Add an interpreter boundary for native `.pnv` source so PNCS can parse and execute admitted PNV1 relational programs instead of using a hand-written semantic harness for each native witness.

The tool is deliberately outside the frozen v0.29/v0.30/v1.0 release scope. It does not alter the v1 release train and carries zero release-gate authority.

## Supported PNV1 statements

Headers: `PNV 1`, `EPISTEMIC <state>`, `MODE <mode>`.

Execution statements: `SOURCE`, `IDENTITY`, `DIFFERENCE`, `CONDITION`, `ORDER`, `TRANSFORM`, `COMPOSITION`, `RETURN`, plus `ASSERT` and `EMIT`.

No new PNV opcode is introduced.

## Execution boundary

External semantics are admitted only through explicit `sources`, `comparators`, and `transforms` registries. Unknown tokens, comparators, transforms, opcodes, duplicate OP names, malformed headers, failed assertions, and dangling references fail closed.

The interpreter exposes no Python eval/exec, dynamic import, shell, subprocess, network, Git, device access, or arbitrary filesystem read.

## Receipt

Every successful execution returns a deterministic SHA-256 receipt binding source bytes, parsed program graph, ordered operator trace, assertion results, emitted object hashes, and the explicit effect boundary.

## GREMLIN / BELZEBUB live bridge

`gremlin_native_pnv_bridge_v01.py` binds the interpreter to the already-verified PNCS live-surface loader. Live use requires the canonical `/dev/shm/ciel_noema` surface and Unix socket admission. No static-state fallback is provided.

GREMLIN Triple Pulse binds `current.identity`, `current.domain`, `current.authority`, `user.request`, the same-generation pulse set, and the current live-surface receipt into the native PNV1 graph from `GREMLIN_TRIPLE_PULSE_BOOT_V0_5.pnv`.

BELZEBUB binds its content-addressed quarantine object and `CURRENT` pointer from its own namespace. `invariant_violation` and `defensive_semantic_digest` remain explicit admitted semantics; quarantined content remains data.

## Harness comparison rule

The old Triple Pulse object and the new native-executor receipt are different provenance schemas, so byte-for-byte receipt identity is neither expected nor asserted. The bridge instead performs an exact canonical semantic projection comparison over identity, domain surface, authority, request, generation binding, and admission result.

A mismatch is reported as a mismatch; it is never normalized away.

## Current gate

1. Pure native executor tests.
2. GREMLIN Triple Pulse native execution test.
3. Exact canonical semantic-projection comparison against the legacy Triple Pulse harness witness.
4. BELZEBUB content-addressed quarantine execution test.
5. Live `/dev/shm/ciel_noema` run only when the existing PNCS tether/live-surface guard passes.

The bridge remains post-v1 experimental until its live receipts and regression evidence are separately promoted.