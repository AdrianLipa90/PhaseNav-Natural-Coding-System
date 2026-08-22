# PNCS v0.9 — Recursive Grouping

Status: `IMPLEMENTED / TEST_PENDING / NATIVE_PNV / NO_NEW_OPCODE / FAIL_CLOSED`

## Scope

v0.9 generalizes the bounded v0.8 two-term logic surface into a recursive predicate tree while preserving the existing PNV/1 operator vocabulary.

The accepted recursive forms are:

```text
comparison
NOT predicate
predicate AND predicate [...]
predicate OR predicate [...]
(predicate)
```

Parentheses are structural boundaries only. They do not introduce a PNV operator, KAKU, radical, vector axis, or execution effect.

## No implicit mixed precedence

PNCS v0.9 deliberately does not infer conventional Boolean precedence for a mixed ungrouped expression.

```text
A AND B OR C
```

fails closed.

The intended structure must be declared:

```text
(A AND B) OR C
A AND (B OR C)
```

These are distinct canonical trees.

Homogeneous chains are accepted because no AND/OR ambiguity exists at that syntactic level:

```text
A AND B AND C
A OR B OR C OR D
```

They are represented as recursive `COMPOSITION` paths with relation binding `all` or `any` respectively.

## Recursive example

Surface:

```text
IF (temperature ABOVE 80 AND memory_pressure ABOVE 0.9)
   OR (risk ABOVE 0.8 AND NOT phase_coherence BELOW 0.7)
THEN GO safety.pause
ELSE GO runtime.continue
```

Predicate tree:

```text
OR
├── AND
│   ├── temperature > 80
│   └── memory_pressure > 0.9
└── AND
    ├── risk > 0.8
    └── NOT
        └── phase_coherence < 0.7
```

Each comparison expands to:

```text
DIFFERENCE -> CONDITION
```

`AND` and `OR` use `COMPOSITION` with `all` / `any` relation bindings. `NOT` uses existing `NEGATION`. The route remains internal `TRANSFORM(control_location, route, target)`.

## Integrity boundaries

- no new PNV opcode;
- no `GROUP`, `AND`, `OR`, `NOT`, `IF`, `THEN`, `ELSE`, or `GO` machine opcode;
- no hidden precedence guessing;
- no `ACTION_REQUEST` for internal route transfer;
- explicit parentheses alter tree structure but add no semantic leaf;
- generic natural-language compilation remains disabled;
- Python is a reference parser/test harness only; native PNV remains semantic authority.

## Deferred

v0.9 does not silently apply Boolean algebra rewrites such as associativity canonicalization, commutativity reordering, De Morgan transforms, double-negation elimination, distributivity, or constant folding. Those require independent equivalence and canonicalization gates.
