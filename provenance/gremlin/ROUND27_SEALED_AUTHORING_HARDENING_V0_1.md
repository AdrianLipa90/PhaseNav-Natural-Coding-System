# GREMLIN ROUND27 — Sealed Authoring Hardening v0.1

Status: `IMPLEMENTED_BRANCH_CANDIDATE / EXECUTION_PENDING_RUNNER`

## Audit finding

Review of the ROUND27 compilation path identified two persistence/provenance closure debts:

1. `bank_manifest().manifest_sha256` identifies the source-pinned bank definition, while `compile_cross_formalism_candidates()` adds concrete compiled entries after that bank hash is formed. A generation-level commitment is therefore required to bind caller provenance and concrete KAKU/RADICAL/OPERATORS/PNV/receipt outputs.
2. Passing `authoring_root` directly into the per-entry compiler publishes candidates sequentially. A durable ROUND27 package benefits from a compile-all / validate-all / seal / publish transaction boundary.

## Implemented hardening

Added:

- `src/phasenav_natural_code/gremlin_cross_formalism_sealed_bundle_v01.py`
- `tests/test_gremlin_cross_formalism_sealed_bundle_v01.py`
- `spec/PNCS_GREMLIN_CROSS_FORMALISM_SEALED_AUTHORING_V0_1.md`

The hardened path is:

```text
compile all eight entries in memory
 -> validate all READ_ONLY candidates
 -> require zero external effects
 -> require CHYBA epistemic state
 -> bind generation_binding + identity + authority
 -> bind every KAKU/RADICAL/OPERATOR/PNV/receipt
 -> compute bundle_sha256
 -> optional verified single-file atomic persistence
```

The outer bundle commitment is distinct from the source-bank definition commitment:

```text
H_bank    source pins + bank definitions
H_bundle  H_bank + caller provenance + concrete compiled generation
```

## Authority state

```text
runtime_execution_authority = false
canon_write_authority = false
promotion_state = CANDIDATE_ONLY
epistemic = CHYBA
```

Caller `identity` and `authority` are committed provenance assertions. Downstream live admission remains responsible for comparison with independently established principal/capability state.

## Targeted new tests

The new test file covers:

- whole-package commitment verification;
- caller-provenance binding;
- candidate PNV tamper rejection;
- malformed generation binding rejection;
- READ_ONLY / CHYBA / zero-external-effect validation;
- verified reopen of one persisted sealed package;
- create-once target collision rejection.

## Execution receipt boundary

After hardening head `6c9196bdf2f4fa3eb807c52e58b2ec7ae3004dfb`, GitHub Actions run `33183587356` was triggered.

Observed job state:

```text
ubuntu-latest failed jobs       5
failed jobs with steps          0/5
failed jobs runner_id           0
self-hosted/macos skipped       4
```

The hosted jobs stopped before any workflow step was created. Classification:

```text
GITHUB_ACTIONS_RUNNER_PRE_STEP_FAILURE
```

Therefore:

```text
SEALED_AUTHORING_CODE_WRITE          PASS
SEALED_AUTHORING_SPEC_WRITE          PASS
TARGETED_TEST_DEFINITION_WRITE       PASS
GITHUB_ACTIONS_TEST_EXECUTION        UNEXECUTED_RUNNER_PRE_STEP_FAILURE
FULL_BRANCH_PYTEST                   UNEXECUTED_ENVIRONMENT_DNS_BLOCK
GREMLIN_COMPILER_RUNTIME_EXECUTION   UNEXECUTED_ENVIRONMENT_DNS_BLOCK
```

No runtime/canon promotion is attached to this branch evidence.
