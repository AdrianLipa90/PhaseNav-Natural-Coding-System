# PNCS Control Flow v0.6 — First Full Program Graph

Status: `PASS_04 / NATIVE_PNV / NO_NEW_OPCODE / CONTROL_FLOW_CANDIDATE`

## Goal

Compile the declared surface statement

```text
IF gravity BELOW 0.5 THEN GO physics.gravity.low
```

into a canonical PNV relational graph without introducing `IF`, `BELOW`, `THEN`, or `GO` as machine opcodes.

## Surface is not authority

The surface words are projections:

- `BELOW(a,b)` binds a numeric difference to a strict-negative condition;
- `IF` introduces the predicate binding;
- `THEN` fixes predicate-before-action order;
- `GO target` binds an existing `ACTION_REQUEST` with action type `route`.

The canonical graph is:

```text
DIFFERENCE(subject, threshold)
  -> CONDITION(delta, lt, 0)
  -> ORDER(predicate, action)
  -> ACTION_REQUEST(route, target)
  -> COMPOSITION(predicate, order, action)
```

This gives the current control leaf path:

```text
DIFFERENCE -> CONDITION -> ORDER -> ACTION_REQUEST -> COMPOSITION
```

`CONDITION` and `ACTION_REQUEST` are control-plane KAKU candidates, not yet promoted universal primitives. They are reused from the recovered PNV/1 vocabulary.

## Important execution boundary

An `OP ... ACTION_REQUEST ...` node is an inspectable request in the graph. It is not permission for hidden execution. PNV/1 effectful instructions compile to effect requests and the reconstructed native v0.1 runtime does not contain a mutating effect executor.

Therefore v0.6 proves **control-flow representation and deterministic normalization**, not that the historical runtime already performs branch execution.

## BELOW is not a primitive keyword

For scalar bindings:

```text
delta = subject - threshold
BELOW(subject, threshold) <=> delta < 0
```

The relation is therefore represented by `DIFFERENCE` plus `CONDITION`. The literal token `BELOW` is only a surface alias.

## THEN is order, GO is an action binding

`THEN` contributes no independent KAKU. It binds `ORDER(predicate, action)`.

`GO` contributes no new opcode. It binds:

```text
ACTION_REQUEST(route, target)
```

## Name resolution remains separate

The symbol `gravity` in the example is a binding slot. If it is supplied as natural-language text rather than a canonical concept ID, name resolution occurs before this graph using the v0.5 `R.NAME_RESOLUTION` path. Control-flow semantics do not depend on alias lookup.

## Reference truth table

For the frozen example threshold `0.5`:

```text
gravity=0.49 -> predicate TRUE  -> route requested
gravity=0.50 -> predicate FALSE -> no route
gravity=0.51 -> predicate FALSE -> no route
```

The Python helper included in v0.6 is only a test/reference normalizer. Native PNV remains the semantic authority.

## Gate for v0.7

Transfer the same control graph to at least two non-gravity examples and test surface paraphrase convergence. Promote a control radical only if its expanded leaf path remains unchanged.
