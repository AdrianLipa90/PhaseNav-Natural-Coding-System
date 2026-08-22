# PNCS Grammar Mining v0.3 — TIR × Secret of a Half

Status: `CANDIDATE / PASS_01 / NATIVE_PNV / NO_NEW_OPCODE`

## Result

The first mining pass does not assign semantic names to the 36 PhaseNav coordinates. It asks a narrower question: **which native PNV relational operators recur when independent source constructions are reduced to their minimal operation paths?**

Ten source-backed chains were reduced. Recurrence is tracked separately from PhaseNav semantic mass; frequency is evidence for grammar reuse, not a replacement mass formula.

## Cross-source recurrent KAKU

The following operators recur across both TIR and Secret-of-a-Half source families:

- `TRANSFORM`
- `DIFFERENCE`
- `COMPOSITION`
- `IDENTITY`
- `DERIVE`

`CONDITION` and `RESOLVE` recur strongly inside the Secret-of-a-Half fixed-point/self-duality constructions and remain active candidates. `BOUNDARY` and `NEGATION` are supporting operations in this pass. `ORDER`, `SOURCE`, and `RETURN` are retained from the existing PNV/1 vocabulary but are not promoted by this pass.

## First mined radicals

No radical below is a new opcode. Each is a reusable path over native PNV/1 operators.

```text
R.FIXED_POINT = TRANSFORM -> CONDITION -> RESOLVE
R.INVARIANT   = TRANSFORM -> DIFFERENCE -> IDENTITY
R.CANCELLATION= COMPOSITION -> DIFFERENCE -> IDENTITY
R.CONJUGACY   = TRANSFORM -> COMPOSITION -> IDENTITY
R.CONVERGENCE = DERIVE -> COMPOSITION -> IDENTITY -> RESOLVE
```

## Why these survive pass 01

- **Fixed point:** Secret-of-a-Half uses the same structure for complement balance and reciprocal/self-dual balance.
- **Invariant:** TIR Appendix L explicitly shows a transformation (common shift) under which pairwise differences remain identical.
- **Cancellation:** TIR Appendix M removes a shared baseline by subtraction.
- **Conjugacy:** Secret-of-a-Half maps one transformation into another through the Möbius coordinate.
- **Convergence:** Secret-of-a-Half independently selects the same `1/2` node through label-swap, reciprocal, spinor and Fisher–Rao constructions.

These are therefore graph motifs, not surface-language keywords.

## Emerging code principle

A high-level written statement should resolve to a definition path built from these motifs. For example, a future natural phrase such as `find the state unchanged by this transform` should not require a special parser opcode for *fixed point*. It can resolve to `PATH.DEF.FIXED_POINT`, whose lineage is the KAKU path `TRANSFORM -> CONDITION -> RESOLVE`.

## Gate for v0.4

Mine at least two more independent domains. A radical is promoted from `CANDIDATE` only if it transfers without a special-case opcode and without changing its atomic path.
