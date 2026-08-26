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

## BELZEBUB use case

`native/BELZEBUB_TOOL_V0_4.pnv` can be executed by explicitly binding its live-source objects, `invariant_violation` comparator, and `defensive_semantic_digest` transform. The PNV graph determines operator order; a bespoke BELZEBUB-only harness is no longer required.

## Next gate

Run the interpreter against GREMLIN and BELZEBUB native witnesses, compare emitted hashes with deterministic harness receipts, and add live `/dev/shm/ciel_noema` source adapters only through the existing PNCS effect/admission boundary.
