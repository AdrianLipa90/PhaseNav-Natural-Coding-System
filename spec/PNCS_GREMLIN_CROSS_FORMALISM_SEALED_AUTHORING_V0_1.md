# PNCS GREMLIN Cross-Formalism Sealed Authoring v0.1

Status: `CANDIDATE_ONLY / CHYBA / SEALED_AUTHORING_GATE`

This contract hardens ROUND27 persistence while preserving the existing relational compiler and its KAKU → RADICAL → OPERATORS → READ_ONLY PNV pipeline.

## 1. Two commitments, internal holonomy, deterministic replay

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

The outer bundle commitment binds the concrete compiled generation, while `H_bank` identifies the source-pinned bank definition.

After the outer commitment verifies, the bundle verifier reconstructs the embedded dependency holonomy:

```text
caller provenance
 -> every content-addressed KAKU candidate
 -> RADICAL KAKU dependency map
 -> every OPERATOR RADICAL dependency
 -> deterministic READ_ONLY PNV rendering
 -> PNV source/graph commitments
 -> compilation receipt commitment
 -> compiled_entries manifest binding
 -> validation receipt binding
```

For every candidate envelope:

\[
C_{candidate}=\operatorname{typedSHA256}(\text{canonical candidate body}).
\]

For every compilation receipt:

\[
C_{receipt}=SHA256(\text{canonical receipt body}).
\]

The reopen verifier then performs deterministic replay from the installed ROUND27 bank and compiler using the committed caller provenance:

\[
\boxed{
\operatorname{Replay}(G,I,A)
\equiv
(Manifest,Payload,Validation)_{sealed}
}
\]

Comparison uses canonical JSON bytes, so tuple/list representation differences introduced by JSON round-trip do not create false divergence.

## 2. Compile-before-persist transaction

The sealed path is:

```text
SOURCE-PINNED BANK
  -> compile all entries in memory
  -> validate all READ_ONLY PNV candidates
  -> require zero external effects
  -> require CHYBA epistemic state
  -> reconstruct and verify internal holonomy
  -> seal caller provenance and all compiled bytes
  -> optional atomic single-file persistence
```

Reopen/import verification adds:

```text
sealed package
 -> outer commitment verification
 -> internal holonomy verification
 -> deterministic bank/compiler replay
 -> canonical manifest/payload equality
 -> READ_ONLY replay validation equality
```

Durable candidate publication uses the sealed bundle as the transactional unit. Individual KAKU/RADICAL/OPERATOR objects may be materialized from a bundle only after `verify_sealed_cross_formalism_bundle()` passes.

## 3. Authority boundary

Every sealed bundle carries:

```text
runtime_execution_authority = false
canon_write_authority = false
promotion_state = CANDIDATE_ONLY
epistemic = CHYBA
```

`identity` and `authority` are provenance assertions supplied to the compiler and committed by the bundle and by every candidate envelope. A downstream admission surface compares those assertions with its independently established live principal/capability state before granting any stronger operation.

## 4. Atomic create-once persistence

`write_sealed_cross_formalism_bundle()` performs:

```text
verify bundle + replay
 -> write same-directory temporary file
 -> flush
 -> fsync(file)
 -> atomically hard-link the verified inode into the final create-once path
 -> unlink temporary name
 -> fsync(parent directory)
```

Because temporary and final names are on the same filesystem, hard-link publication either creates the final name as one filesystem operation or fails with `FileExistsError` when another writer has already claimed it. Other publication failures are surfaced as `CrossFormalismBundleError`, while the temporary path is cleaned in the finalizer.

This gives one durable receipt-bearing object for the complete bank generation instead of exposing a partial generation as a complete ROUND27 package.

## 5. Verification gate

`verify_sealed_cross_formalism_bundle()` SHALL:

1. verify the top-level schema and candidate authority boundary;
2. recompute `bundle_sha256` over the canonical body;
3. recompute the source-bank `manifest_sha256` over the source-bank body;
4. verify caller provenance syntax;
5. deterministically recompile the eight ROUND27 candidates from `(generation_binding, identity, authority)`;
6. canonical-compare the sealed bank manifest with the replayed manifest;
7. canonical-compare the complete sealed candidate payload with the replayed candidate payload;
8. re-run READ_ONLY conformance validation and canonical-compare the validation summary;
9. recompute every KAKU/RADICAL/OPERATOR content-addressed candidate ID;
10. require candidate provenance to equal the bundle caller provenance;
11. require the RADICAL dependency map to equal the embedded KAKU candidate IDs;
12. require every OPERATOR to bind the embedded RADICAL candidate ID;
13. deterministically reconstruct the READ_ONLY PNV source from the OPERATOR sequence;
14. parse that PNV and recompute source/graph commitments;
15. recompute every compilation receipt commitment;
16. require receipt KAKU/RADICAL/OPERATOR IDs and PNV commitments to match the embedded generation;
17. require `compiled_entries` and validation summaries to bind the same receipt and graph commitments.

Any mismatch fails closed before persistence or materialization.

## 6. Live import gate

A future live GREMLIN/PNV importer SHALL:

1. run the complete sealed-bundle verification and deterministic replay gate;
2. compare caller provenance with current live admission state;
3. verify the current generation binding against the admitted `/dev/shm/ciel_noema` live surface;
4. materialize candidates only after complete package admission;
5. emit an import receipt binding the bundle SHA, target generation and materialized candidate IDs.

The live admission surface remains the authority source for principal/capability authentication.

## 7. Test gates

`tests/test_gremlin_cross_formalism_sealed_bundle_v01.py` targets:

- whole-package commitment verification;
- explicit caller-provenance binding;
- ordinary embedded PNV tamper rejection;
- rehashed PNV tamper rejection;
- rehashed caller-provenance tamper rejection;
- rehashed candidate-envelope tamper rejection;
- rehashed compilation-receipt tamper rejection;
- rehashed source-bank pin forgery rejected by deterministic replay;
- generation-binding syntax/type rejection;
- READ_ONLY / CHYBA / zero-external-effect validation;
- single-file reopen and complete replay verification;
- atomic create-once target collision rejection.

The execution evidence status remains tied to actual test execution. Runner-pre-step failures are recorded as infrastructure execution blockers rather than code-test failures.

## 8. Relation to ROUND27

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
