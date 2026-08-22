# PNCS Semantic Collision Repair v0.5

Status: `PASS_03 / NATIVE_PNV / NO_NEW_OPCODE / FAIL_CLOSED`

## Scope

This pass tests whether `DERIVE` and `RESOLVE` are irreducible KAKU.

## DERIVE

The current source material does not require `DERIVE` as an irreducible leaf.

The Consciousness Dictionary defines reasoning as transformation of representations according to inferential rules or learned relations to obtain conclusions or decisions, and inference as derivation or update of representations from evidence plus a model or rule set.

PNCS therefore expands derivation as:

```text
R.DERIVATION
  = SOURCE
  -> COMPOSITION
  -> TRANSFORM
```

Bindings carry the premises/evidence, rule/model, and result. `DERIVE` remains part of the recovered PNV/1 operator vocabulary for compatibility, but v0.5 does not promote it as a PNCS KAKU.

## RESOLVE namespace split

The current PNV database/runtime command `resolve(term)` performs identifier/alias lookup and returns matching canonical or observed records. It does not solve equations or choose a unique mathematical root.

PNCS therefore separates:

```text
R.NAME_RESOLUTION
  = SOURCE
  -> COMPOSITION
  -> IDENTITY
```

from mathematical relation solving.

Unqualified `RESOLVE` is not used as a leaf in corrected PNCS mathematical definition paths.

## Fixed-point reduction

A fixed point is represented as the state-level specialization of the already promoted invariant path:

```text
R.INVARIANT
  = TRANSFORM
  -> DIFFERENCE
  -> IDENTITY

R.FIXED_POINT
  = R.INVARIANT
    with output bound to input
```

The fully expanded leaf path of `R.FIXED_POINT` is therefore identical to `R.INVARIANT`.

No separate `CONDITION -> RESOLVE` leaf sequence is required for fixed-point semantics.

## Convergence reduction

The former convergence candidate used both `DERIVE` and `RESOLVE` as leaves.

v0.5 expands it to:

```text
R.CONVERGENCE
  = R.DERIVATION
  -> COMPOSITION
  -> IDENTITY
```

and therefore to the leaf sequence:

```text
SOURCE
-> COMPOSITION
-> TRANSFORM
-> COMPOSITION
-> IDENTITY
```

## Primitive status after pass 03

Observed/reused PNCS leaves:

```text
SOURCE
ORDER
TRANSFORM
COMPOSITION
DIFFERENCE
IDENTITY
```

`CONDITION` remains a control-flow primitive candidate for later executable-language tests. It is not required by the corrected mathematical fixed-point path.

`DERIVE` and `RESOLVE` remain valid recovered PNV/1 operator names, but they are no longer classified as irreducible PNCS KAKU in this pass.

## Integrity rules

- no new opcode;
- no semantic promotion from vector similarity;
- name resolution is not equation solving;
- fixed point is not a separate primitive from invariant;
- every radical must recursively expand to declared leaves;
- compatibility vocabulary may be broader than the minimal PNCS alphabet.
