# PNCS GREMLIN Cross-Formalism Sealed Authoring v0.1

Status: `CANDIDATE_ONLY / CHYBA / SEALED_AUTHORING_GATE`

This contract hardens ROUND27 persistence while preserving the existing relational compiler and its KAKU → RADICAL → OPERATORS → READ_ONLY PNV pipeline.

## 1. Two commitments

The bank-definition commitment remains the commitment produced by `bank_manifest()`:

\[
H_{bank}=H(\text{source pins},\text{entry definitions},\text{classifications},\text{guardrails}).
\]

A compiled authoring generation receives a second commitment:

\[
\boxed{
H_{bundle}=H(
H_{bank},
G,
I,
A,
\{KAKU\},
\{RADICAL\},
\{OPERATORS\},
\{PNV\},
\{RECEIPTS\}
)
}
\]

where

- `G` is the 64-hex generation binding;
- `I` is the caller identity assertion;
- `A` is the caller authority assertion.

The outer bundle commitment therefore binds the concrete compiled generation, while `H_bank` continues to identify the source-pinned bank definition.

## 2. Compile-before-persist transaction

The sealed path is:

```text
SOURCE-PINNED BANK
  -> compile all entries in memory
  -> validate all READ_ONLY PNV candidates
  -> require zero external effects
  -> require CHYBA epistemic state
  -> seal caller provenance and all compiled bytes
  -> optional atomic single-file persistence
```

Durable candidate publication uses the sealed bundle as the transactional unit. Individual KAKU/RADICAL/OPERATOR objects may be materialized from a bundle only after its `bundle_sha256` verifies.

## 3. Authority boundary

Every sealed bundle carries:

```text
runtime_execution_authority = false
canon_write_authority = false
promotion_state = CANDIDATE_ONLY
epistemic = CHYBA
```

`identity` and `authority` are provenance assertions supplied to the compiler and cryptographically committed by the bundle. A downstream admission surface compares those assertions with its independently established live principal/capability state before granting any stronger operation.

## 4. Atomic create-once persistence

`write_sealed_cross_formalism_bundle()` performs:

```text
verify bundle
 -> write same-directory temporary file
 -> flush
 -> fsync(file)
 -> atomically hard-link the verified inode into the final create-once path
 -> unlink temporary name
 -> fsync(parent directory)
```

Because temporary and final names are on the same filesystem, hard-link publication either creates the final name as one filesystem operation or fails with `FileExistsError` when another writer has already claimed it. The writer converts that collision into a fail-closed `CrossFormalismBundleError`.

This gives one durable receipt-bearing object for the complete bank generation instead of exposing a partial generation as a complete ROUND27 package.

## 5. Import gate

A future live GREMLIN/PNV importer SHALL:

1. parse the sealed JSON package;
2. verify `schema`;
3. recompute `bundle_sha256` over the canonical body;
4. require the fixed candidate authority boundary;
5. compare caller provenance with current live admission state;
6. verify every embedded compilation receipt;
7. verify each embedded READ_ONLY PNV graph before materializing KAKU/RADICAL/OPERATORS;
8. emit an import receipt binding the bundle SHA, target generation and materialized candidate IDs.

Any failed dependency stops import before candidate publication.

## 6. Test gates

`tests/test_gremlin_cross_formalism_sealed_bundle_v01.py` targets:

- whole-package commitment verification;
- explicit caller-provenance binding;
- tamper rejection inside embedded PNV text;
- generation-binding syntax/type rejection;
- READ_ONLY / CHYBA / zero-external-effect validation;
- single-file reopen and commitment verification;
- atomic create-once target collision rejection.

The execution evidence status remains tied to actual test execution. The recorded environment/runner blockers remain attached until an exact branch run executes these gates.

## 7. Relation to ROUND27

ROUND27 discovery entries remain independently classified:

```text
XFI.01 EXACT
XFI.04 EXACT
XFI.02 EXACT_CONDITIONAL
XFI.03 EXACT_STRUCTURAL
XFI.07 SUPPORTED_EXTENSION
XFI.05 STRONG_STRUCTURAL
XFI.06 STRONG_STRUCTURAL
XFI.08 STRONG_STRUCTURAL
```

The sealed authoring layer changes persistence integrity and provenance closure. Candidate evidence classes continue to be controlled by their entry-specific mathematical and empirical gates.
