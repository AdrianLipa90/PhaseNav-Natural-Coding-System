# PNCS Primitive Closure v0.4 — Cross-Domain Transfer

Status: `PASS_02 / NATIVE_PNV / NO_NEW_OPCODE / ONE_RADICAL_PROMOTED`

## Scope

This pass continues the bottom-up mining procedure. It does not invent semantic names for the 36 PhaseNav coordinates and does not add a new opcode. It tests whether the v0.3 graph motifs survive transfer into two additional formal domains:

1. PhaseNav projective/trajectory geometry;
2. the Consciousness Dictionary meta-formal layer.

TIR and The Secret of a Half remain the seed domains.

## Primitive closure

All five v0.3 radicals expand using only seven recurrent operators:

```text
TRANSFORM
DIFFERENCE
IDENTITY
COMPOSITION
CONDITION
RESOLVE
DERIVE
```

`ORDER` is retained as an eighth KAKU candidate because ordered transformation is explicit in both the PhaseNav sentence trajectory and the meta-formal definition of a trajectory.

No claim is made that these eight operators are the final irreducible alphabet. This pass only freezes the smallest observed set required by the current evidence.

## Transfer result: INVARIANT

The v0.3 path is unchanged:

```text
R.INVARIANT = TRANSFORM -> DIFFERENCE -> IDENTITY
```

It now has three source realizations without a special-case opcode:

- TIR translation invariance: a common transformation leaves pairwise differences unchanged;
- PhaseNav global-phase gauge invariance: a global phase shift changes the representative while preserving the projective/relative-phase object;
- Consciousness Dictionary: an invariant is a property preserved under an admissible class of transformations.

Status in v0.4: `PROMOTED_GRAMMAR_RADICAL`.

Promotion means only that the relational path is now reusable PNCS grammar. It does not canonize any physical interpretation attached to a particular use of the path.

## New candidate: TRAJECTORY

The transferred path is:

```text
R.TRAJECTORY = ORDER -> TRANSFORM -> COMPOSITION
```

Evidence:

- PhaseNav represents an information-bearing sequence as ordered operators acting on successive relation-states; the sentence is a trajectory rather than only a terminal embedding.
- The meta-formal registry defines trajectory as an ordered sequence of states connected by transformations, with the path itself part of the represented object.

Status in v0.4: `TRANSFERRED_CANDIDATE`.

It is not promoted yet because the formal definition and PhaseNav implementation are closely related provenance families. A later pass must transfer the same atomic path into a materially different domain.

## Canonical path normal form

PNCS now freezes a first normal-form rule for definition paths:

```text
surface expression
    -> resolve aliases / concepts
    -> expand named radical
    -> ordered KAKU sequence
    -> bind arguments
    -> canonical relational path
    -> attach / compare 36D realization
```

A named radical is therefore a compression handle for its ordered KAKU path, not a new semantic primitive.

Two surface expressions are candidates for the same PNCS definition only when:

1. their expanded ordered KAKU sequences are identical;
2. their argument bindings are compatible;
3. no declared type or epistemic boundary is violated.

Vector proximity alone is insufficient for semantic equivalence.

## Compression consequence

The current grammar can store a repeated structure once:

```text
R.INVARIANT
```

instead of copying:

```text
TRANSFORM -> DIFFERENCE -> IDENTITY
```

into every definition. The full lineage remains recoverable by recursive expansion.

## Promotion ledger

```text
R.INVARIANT    PROMOTED_GRAMMAR_RADICAL
R.FIXED_POINT  CANDIDATE
R.CANCELLATION CANDIDATE
R.CONJUGACY    CANDIDATE
R.CONVERGENCE  CANDIDATE
R.TRAJECTORY   TRANSFERRED_CANDIDATE
```

## Gate for v0.5

1. Transfer `R.TRAJECTORY` into a materially different domain without changing `ORDER -> TRANSFORM -> COMPOSITION`.
2. Test whether `DERIVE` and `RESOLVE` are irreducible KAKU or higher-level compressed paths.
3. Begin phrase-to-path equivalence tests using natural-language paraphrases, but keep the canonical relational path authoritative.
