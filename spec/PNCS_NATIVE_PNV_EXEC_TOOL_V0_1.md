# PNCS Native PNV Exec Tool v0.1

Status: `POST_V1_EXPERIMENTAL / FAIL_CLOSED / ZERO_RELEASE_GATE_AUTHORITY`

## Purpose

This contract defines the native PNV1 interpreter boundary used by PNCS relational witnesses. A successful execution is bound to the exact source text, the exact parsed operator graph, the ordered execution trace, emitted-value commitments, and the observed effect boundary.

## Admitted headers and statements

The parser admits exactly:

```text
PNV 1
EPISTEMIC CHYBA
MODE READ_ONLY | INTERNAL_EXECUTION
```

Admitted execution statements are:

```text
SOURCE
IDENTITY
DIFFERENCE
CONDITION
ORDER
TRANSFORM
COMPOSITION
RETURN
ASSERT
EMIT
```

`TRUE`, `FALSE`, and `NONE` are reserved literals and cannot be shadowed by OP names. OP names are unique. ASSERT and EMIT references are valid, unique operator references.

## Exact source-to-graph binding

`PNVProgram` stores the exact `source_text` and derives:

```text
source_sha256 = SHA256(exact source bytes)
```

Before executing a public `PNVProgram` object, the interpreter reparses its stored source and requires exact structural equality of:

```text
version
epistemic
mode
ops
assertions
emits
metadata
```

A caller therefore cannot attach a valid source hash to a different in-memory operator graph.

## Canonical runtime-value domain

Every source, operation result, final value, emitted value, and hashed value is normalized into one canonical finite JSON domain.

Rules:

- JSON object keys are strings;
- tuples and lists share one canonical JSON-array representation;
- finite floats are admitted;
- non-finite floats fail closed;
- unsupported Python objects fail closed;
- numeric operations that overflow to non-finite values fail closed before receipt construction.

This prevents Python-object distinctions from creating ambiguous JSON commitments.

## External semantics and effect boundary

External semantics are admitted only through explicit `sources`, `comparators`, and `transforms` registries. Unknown tokens or callbacks fail closed. Callback exceptions are converted to controlled PNCS resolution errors.

The interpreter-local implementation performs no shell, subprocess, network, Git, device, or arbitrary-filesystem action. Its receipt records those interpreter-local measurements separately.

When no comparator or transform callback is invoked:

```text
external_effects = false
external_effects_status = VERIFIED_NONE_WITHIN_INTERPRETER_BOUNDARY
callback_effects_verified = true
callback_determinism_verified = true
```

When a Python comparator or transform callback is invoked, effects outside the interpreter cannot be inferred from the interpreter alone. The receipt records:

```text
external_effects = null
external_effects_status = UNVERIFIED_CALLBACK_BOUNDARY
callback_effects_verified = false
callback_determinism_verified = false
callbacks_invoked = [...]
```

The interpreter-local fields remain `false`, preserving the measured boundary without promoting callback purity.

## Receipt

Every successful execution returns a SHA-256 receipt binding:

```text
program_source_sha256
program_graph_sha256
pnv_version
epistemic
mode
ordered trace hashes
assertion results
emitted value hashes
effect_boundary
```

`deterministic_receipt = true` means the observed receipt body has deterministic canonical serialization. Callback determinism is reported independently by `callback_determinism_verified`.

## GREMLIN / BELZEBUB live bridge

`gremlin_native_pnv_bridge_v01.py` binds native execution to the verified live PNCS surface. Live execution requires canonical `/dev/shm/ciel_noema` admission. GREMLIN Triple Pulse and BELZEBUB witnesses preserve callback-boundary status in their native execution receipts.

## Fail-closed gate

The interpreter rejects malformed headers, unknown opcodes, duplicate or reserved operator identities, dangling ASSERT/EMIT references, noncanonical values, non-finite arithmetic, unregistered semantics, callback exceptions, failed assertions, and source-to-graph mismatch.

The tool remains under `CHYBA` and carries zero automatic canon or release-promotion authority.
