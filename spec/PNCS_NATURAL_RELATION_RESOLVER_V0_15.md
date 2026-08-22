# PNCS Natural Relation Resolver v0.15

Status: `CANDIDATE / BOUNDED_NATURAL_SURFACE / FAIL_CLOSED / NO_NEW_OPCODE`

## Scope

v0.15 resolves a bounded natural-language predicate surface into the already stabilized PNCS predicate graph. It does not enable arbitrary natural-language execution and it does not replace the native PNV graph as semantic authority.

The resolver path is:

```text
surface phrase
-> explicit symbol alias resolution
-> explicit relation alias resolution
-> scalar normalization
-> Predicate graph
-> v0.10 Boolean canonicalization
-> v0.11 DefinitionContent
-> pncs:def:sha256:<content>
```

## Symbol authority

Natural names are aliases only. Canonical subjects are explicit registry entries. An unknown alias is rejected. Two canonical subjects may not share one normalized alias.

The default v0.15 registry contains the already used project subjects:

- `risk`
- `phase_coherence`
- `memory_pressure`
- `temperature`
- `phase_error`
- `gravity`

This list is a bounded resolver registry, not a claim of a complete PNCS ontology.

## Relation authority

Only the existing comparison semantics are admitted:

```text
gt -> DIFFERENCE -> CONDITION
lt -> DIFFERENCE -> CONDITION
eq -> DIFFERENCE -> CONDITION
```

Surface aliases such as `above`, `is above`, `greater than`, `exceeds`, `below`, `less than`, `equals`, and symbolic `>`, `<`, `==` resolve to those existing comparator bindings. They are not new PNV opcodes.

`>=`, `<=`, and `!=` remain rejected in v0.15 because the stabilized comparison surface has not admitted those relations.

## Percent surface

Percent syntax is only accepted for symbols explicitly marked as normalized fractions. For example:

```text
risk above 80% == risk above 0.8
```

No generic unit inference is performed. `temperature above 80%` is rejected by the default registry.

## Boolean composition

Natural `AND`, `OR`, `NOT`, and parentheses reuse the v0.9/v0.10 predicate grammar and algebra. Mixed ungrouped `AND/OR` remains rejected; v0.15 does not introduce implicit precedence.

## Identity

Surface wording and resolution trace do not participate in DefinitionContent identity. Equivalent registered surfaces that normalize to the same predicate graph obtain the same `pncs:def:sha256:` content ID. The trace is provenance only.

## Failure rules

Resolution fails closed when any of the following holds:

- unknown subject alias;
- unknown relation phrase;
- ambiguous registry alias;
- unsupported comparator;
- invalid or non-finite scalar;
- percentage used for a symbol without declared percent normalization;
- mixed AND/OR without grouping;
- unsupported free-form wording.

## Execution boundary

`compile_natural_language()` remains disabled. v0.15 only produces a canonical predicate DefinitionContent. No route or effect is executed from natural text in this gate.
