# PNCS GREMLIN Isomorphic Codec Merge v0.1

Status: ARCHITECTURE CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false

## Purpose

GREMLIN may receive several partial relational descriptions of one codec invariant from different repositories or domains. The merge operator forms one bounded union graph before the existing relational compiler materializes KAKU, RADICAL and OPERATORS.

```text
ISO fragment A --\
                  -> ISOMORPHIC MERGE -> one relational isomorphism -> compiler
ISO fragment B --/                                             |
                                                                -> KAKU
                                                                -> RADICAL
                                                                -> OPERATORS
                                                                -> READ_ONLY PNV
```

## Admission invariant

All fragments bind one exact `invariant_id` and one exact invariant description. Shared KAKU IDs are admitted when their canonical node signatures agree. Shared relation IDs are admitted when their endpoint/type signatures agree.

A disagreement produces a fail-closed merge result before RADICAL compilation.

## Union semantics

The merge performs deterministic union of:

```text
KAKU nodes
relations
evidence references
source isomorphism references
```

Ordering is canonical by KAKU ID and relation ID. The merged isomorphism can therefore enter the existing content-addressed GREMLIN relational compiler without a parallel codec-authority path.

## Authority

The merge operator prepares a relational candidate graph. The downstream compiler preserves the existing `CANDIDATE_ONLY`, `READ_ONLY`, no-effect-boundary conformance contract. Canon promotion remains an explicit authority operation.

## PNLF use

The initial codec is split naturally across domains:

```text
PNCS TAU FRAME + T36 WITNESS + State Memory LIMINAL SEGMENT

State Memory LIMINAL SEGMENT + BioOS PNLF FILE + PNH5 VIEW
```

GREMLIN merges both fragments around the shared `K.LIMINAL.SEGMENT` node and compiles the resulting five-node codec graph into one RADICAL and deterministic operator program.
