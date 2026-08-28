# GREMLIN ROUND27 — Sealed Authoring Hardening v0.1

Status: `IMPLEMENTED_BRANCH_CANDIDATE / EXECUTION_PENDING_RUNNER`

## Audit finding

Review of the ROUND27 compilation path identified two persistence/provenance closure debts:

1. `bank_manifest().manifest_sha256` identifies the source-pinned bank definition, while `compile_cross_formalism_candidates()` adds concrete compiled entries after that bank hash is formed. A generation-level commitment is therefore required to bind caller provenance and concrete KAKU/RADICAL/OPERATORS/PNV/receipt outputs.
2. Passing `authoring_root` directly into the per-entry compiler publishes candidates sequentially. A durable ROUND27 package benefits from a compile-all / validate-all / seal / publish transaction boundary.

A second audit pass identified a verifier closure requirement: outer bundle-hash verification is strengthened by independent reconstruction of the embedded candidate/receipt dependency holonomy.

## Implemented hardening

Files:

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
 -> independently reconstruct internal dependency holonomy
 -> optional verified single-file atomic persistence
```

The outer bundle commitment is distinct from the source-bank definition commitment:

```text
H_bank    source pins + bank definitions
H_bundle  H_bank + caller provenance + concrete compiled generation
```

The verifier additionally checks:

```text
candidate_id == typed SHA-256(candidate body)
RADICAL.kaku_candidate_ids == embedded KAKU candidate IDs
RADICAL.dependency_ids == embedded KAKU candidate IDs
OPERATOR.radical_candidate_id == embedded RADICAL candidate ID
OPERATOR.dependency_ids == [embedded RADICAL candidate ID]
PNV == deterministic render(embedded OPERATOR sequence)
receipt_sha256 == SHA-256(receipt body)
receipt candidate IDs == embedded candidate IDs
receipt PNV hashes == parsed embedded PNV hashes
compiled_entries == embedded receipt/radical/PNV commitments
validation receipt hashes == embedded compilation receipt hashes
```

This catches both ordinary payload tampering and a payload that has been modified and then given a freshly computed outer `bundle_sha256` while its internal commitments remain inconsistent.

## Authority state

```text
runtime_execution_authority = false
canon_write_authority = false
promotion_state = CANDIDATE_ONLY
epistemic = CHYBA
```

Caller `identity` and `authority` are committed provenance assertions. Downstream live admission compares them with independently established principal/capability state.

## Targeted test definition

The sealed-bundle test file now covers:

- whole-package commitment verification;
- caller-provenance binding;
- ordinary candidate PNV tamper rejection;
- rehashed PNV tamper rejection;
- rehashed caller-provenance tamper rejection;
- rehashed KAKU-envelope tamper rejection;
- rehashed compilation-receipt tamper rejection;
- malformed generation binding rejection;
- READ_ONLY / CHYBA / zero-external-effect validation;
- verified reopen of one persisted sealed package;
- create-once target collision rejection.

Python syntax for the edited code/test sources was checked before repository write.

## Repository commits

```text
f9d0c1d9c1dc8cfbaf745d733a96e717b2a39222  internal holonomy verifier
81b732182c05d9263d3e0820ab1df7e626ec6b45  adversarial rehash test definitions
d9b0216420c978588cf298c47061e70056b3972c  sealed-authoring contract update
```

## Execution receipt boundary

Earlier hardening run:

```text
run 33183587356
classification GITHUB_ACTIONS_RUNNER_PRE_STEP_FAILURE
```

Latest code/test head `81b732182c05d9263d3e0820ab1df7e626ec6b45` triggered:

```text
run 33185243765  PNCS v0.28 adversarial conformance
run 33185243791  PNCS v1 release closure
```

For run `33185243765`, observed hosted-runner jobs include:

```text
semantic-equivalence   failure   steps=[]   runner_id=0
structural-authority   failure   steps=[]   runner_id=0
repository-integrity   failure   steps=[]   runner_id=0
concurrency-pure       failure   steps=[]   runner_id=0
dynamics-pure          failure   steps=[]   runner_id=0
```

Self-hosted/macos paths were skipped. No hosted workflow step was created before those job failures.

Classification:

```text
GITHUB_ACTIONS_RUNNER_PRE_STEP_FAILURE
```

Therefore:

```text
SEALED_AUTHORING_CODE_WRITE             PASS
SEALED_AUTHORING_SPEC_WRITE             PASS
INTERNAL_HOLONOMY_STATIC_AUDIT          PASS
TARGETED_TEST_DEFINITION_WRITE          PASS
PYTHON_SYNTAX_CHECK_EDITED_SOURCES       PASS
GITHUB_ACTIONS_TEST_EXECUTION            UNEXECUTED_RUNNER_PRE_STEP_FAILURE
FULL_BRANCH_PYTEST                       UNEXECUTED_ENVIRONMENT_DNS_BLOCK
GREMLIN_COMPILER_RUNTIME_EXECUTION       UNEXECUTED_ENVIRONMENT_DNS_BLOCK
RUNTIME_EXECUTION_AUTHORITY              FALSE
CANON_WRITE_AUTHORITY                    FALSE
```

No runtime/canon promotion is attached to this branch evidence.
