# PNCS Boolean Algebra v0.10 — Pure Predicate Equivalence

Status: `PASS_08 / PURE_PREDICATE_SCOPE / NO_NEW_OPCODE / FAIL_CLOSED`

## Scope

This pass tests algebraic rewrites for the frozen pure-predicate subset introduced in v0.8-v0.9:

```text
comparison := DIFFERENCE -> CONDITION
NOT        := NEGATION(predicate)
AND        := COMPOSITION(predicate..., all)
OR         := COMPOSITION(predicate..., any)
```

The result is deliberately scoped. It does **not** state that arbitrary PNV `COMPOSITION` is commutative or associative. Reordering is admitted only for pure read-only Boolean predicate graphs containing no actions, effects, mutation, external reads, timing dependence, or control-location transforms.

## Admitted equivalences

For pure predicates `A`, `B`, `C`:

```text
A AND B                  == B AND A
A OR B                   == B OR A
(A AND B) AND C          == A AND (B AND C)
(A OR B) OR C            == A OR (B OR C)
NOT NOT A                == A
NOT(A AND B)             == (NOT A) OR (NOT B)
NOT(A OR B)              == (NOT A) AND (NOT B)
A AND A                  == A
A OR A                   == A
A AND (A OR B)           == A
A OR (A AND B)           == A
```

These laws are used to construct a deterministic equivalence key for pure predicates.

## Canonicalization procedure

The v0.10 reference normalizer performs:

1. negation-normal-form conversion;
2. double-negation elimination;
3. De Morgan pushdown;
4. same-kind associative flattening;
5. deterministic structural sorting for AND/OR;
6. idempotent duplicate removal;
7. absorption.

Surface parsing remains unchanged. v0.9's explicit-parenthesis rule still controls parse structure. Algebraic canonicalization is a separate phase after a valid predicate graph has been constructed.

## Deliberately deferred

### Distributivity

Distributivity is truth-equivalent for the current Boolean evaluator, but v0.10 does not use it as a canonical rewrite:

```text
A AND (B OR C)
<=>
(A AND B) OR (A AND C)
```

Distribution may duplicate subgraphs and can increase graph mass/size. It remains deferred until a cost-preserving or explicitly cost-aware normal-form policy is defined.

### Constant folding

The following are not collapsed to machine constants in v0.10:

```text
A OR NOT A
A AND NOT A
```

No `TRUE` or `FALSE` KAKU/opcode is introduced by this pass. The existing truth evaluator may evaluate them for concrete values, but canonical graph reduction stops before inventing a new Boolean constant primitive.

## Integrity rules

- zero new opcode;
- no global commutativity claim for `COMPOSITION`;
- no reorder across effectful/action/control nodes;
- no implicit distributive expansion;
- no invented TRUE/FALSE primitive;
- surface parser remains fail-closed on ambiguous ungrouped mixed AND/OR;
- Python is a reference/test normalizer; native PNV remains the project representation.
