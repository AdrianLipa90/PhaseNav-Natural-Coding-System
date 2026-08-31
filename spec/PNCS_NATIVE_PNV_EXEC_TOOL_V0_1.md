# PNCS Native PNV Exec Tool v0.1

Status: `POST_V1_EXPERIMENTAL / FAIL_CLOSED / ZERO_RELEASE_GATE_AUTHORITY`

## Purpose

Add an interpreter boundary for native `.pnv` source so PNCS can parse and execute admitted PNV1 relational programs instead of using a hand-written semantic harness for each native witness.

The tool is deliberately outside the frozen v0.29/v0.30/v1.0 release scope. It does not alter the v1 release train and carries zero release-gate authority.

## Supported PNV1 statements

Headers are admitted fail-closed:

- `PNV 1`;
- `EPISTEMIC CHYBA`;
- `MODE READ_ONLY` or `MODE INTERNAL_EXECUTION`.

Execution statements: `SOURCE`, `IDENTITY`, `DIFFERENCE`, `CONDITION`, `ORDER`, `TRANSFORM`, `COMPOSITION`, `RETURN`, plus `ASSERT` and `EMIT`.

No new PNV opcode is introduced.

## Execution boundary

External semantics are admitted only through explicit `sources`, `comparators`, and `transforms` registries. Unknown tokens, comparators, transforms, opcodes, duplicate OP names, malformed or unsupported headers, failed assertions, dangling references, non-canonical values, and non-finite numeric results fail closed.

The interpreter implementation itself exposes no Python eval/exec, dynamic import, shell, subprocess, network, Git, device access, or arbitrary filesystem read.

Python comparator and transform callbacks are an explicit boundary beyond what the interpreter can observe. When no callback is invoked, the successful receipt records `external_effects=false` with status `VERIFIED_NONE_WITHIN_INTERPRETER_BOUNDARY`. When a comparator or transform callback is invoked, the receipt records `external_effects=null` with status `UNVERIFIED_CALLBACK_BOUNDARY`, preserves the interpreter-local no-effect measurements separately, and lists the invoked callback bindings. A callback-bearing execution therefore never claims globally verified zero external effects from the interpreter alone.

## Receipt

Every successful execution returns a deterministic SHA-256 receipt binding source bytes, parsed program graph, ordered operator trace, assertion results, emitted object hashes, the explicit interpreter effect boundary, and the callback-boundary status.

Runtime values entering the receipt must be canonical finite JSON. Numerical operations that overflow to non-finite values are rejected before receipt construction.

## GREMLIN / BELZEBUB live bridge

`gremlin_native_pnv_bridge_v01.py` binds the interpreter to the already-verified PNCS live-surface loader. Live use requires the canonical `/dev/shm/ciel_noema` surface and Unix socket admission. No static-state fallback is provided.

GREMLIN Triple Pulse binds `current.identity`, `current.domain`, `current.authority`, `user.request`, the same-generation pulse set, and the current live-surface receipt into the native PNV1 graph from `GREMLIN_TRIPLE_PULSE_BOOT_V0_5.pnv`.

BELZEBUB binds its content-addressed quarantine object and `CURRENT` pointer from its own namespace. `invariant_violation` and `defensive_semantic_digest` remain explicit admitted semantics; quarantined content remains data. Their Python callback effects are reported through the callback boundary described above rather than being inferred as absent.

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
