# PNCS Logic and Branching v0.8

Status: `PASS_06 / NATIVE_PNV / NO_NEW_OPCODE / BRANCH_COMPOSITION_TRANSFERRED`

## Scope

This pass extends the promoted v0.7 conditional-route radical with bounded two-predicate composition and a two-way branch.

The supported surface families are:

```text
IF A ABOVE x AND B BELOW y THEN GO target
IF A ABOVE x OR B BELOW y THEN GO target
IF NOT A ABOVE x THEN GO target
IF A ABOVE x THEN GO target_true ELSE GO target_false
```

`AND`, `OR`, `NOT`, and `ELSE` are not PNV machine opcodes.

## Predicate composition

Each scalar comparison retains the v0.7 expansion:

```text
DIFFERENCE -> CONDITION
```

Two already-formed predicates are combined through existing `COMPOSITION`:

```text
AND(A,B) -> COMPOSITION(A, all, B)
OR(A,B)  -> COMPOSITION(A, any, B)
```

`all` and `any` are relation bindings carried by the composition node. They are not opcodes.

For two scalar comparisons the expanded predicate path is therefore:

```text
DIFFERENCE -> CONDITION
DIFFERENCE -> CONDITION
COMPOSITION
```

## NOT

Logical inversion uses the recovered PNV `NEGATION` operator:

```text
NOT(P) -> NEGATION(P)
```

No additional machine instruction is introduced.

## ELSE

`ELSE` is represented as the second route bound to the negated primary predicate:

```text
P
NOT_P = NEGATION(P)
ORDER(P, TRUE_ROUTE)
TRANSFORM(control_location, route, true_target)
ORDER(NOT_P, FALSE_ROUTE)
TRANSFORM(control_location, route, false_target)
COMPOSITION(TRUE_BRANCH, branch, FALSE_BRANCH)
```

Both routes remain internal control-location transforms. They are not `ACTION_REQUEST` nodes.

## Execution boundary

This pass validates canonical graph representation, bounded surface normalization, route selection in the reference harness, and truth-table consistency. It does not claim that the recovered historical PNV/1 runtime already contains a generic branch executor.

## Fail-closed limits

v0.8 intentionally rejects:

- mixed `AND` and `OR` without explicit grouping;
- more than two predicates in one compound condition;
- unsupported comparators such as `<=` or `!=`;
- parentheses and arbitrary nested natural language;
- missing values in reference evaluation.

These cases require later grammar gates rather than silent guessing.
