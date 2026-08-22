# PNCS Control Transfer v0.7

Status: `PASS_05 / NATIVE_PNV / NO_NEW_OPCODE / CONTROL_RADICAL_PROMOTED`

## Correction to v0.6

The v0.6 representation used `ACTION_REQUEST(route, target)` for the surface form `GO target`.
That binding is too broad for an internal program route. In the recovered PNV vocabulary,
`ACTION_REQUEST` belongs to action-request/effect semantics, while an internal route can be
represented as a state transition of the control location.

v0.7 therefore binds:

```text
GO target
  -> TRANSFORM(control_location, route, target)
```

This keeps internal control transfer separate from effect requests.

## Scalar comparison radical

```text
R.COMPARISON
  = DIFFERENCE(subject, threshold)
  -> CONDITION(delta, comparator, 0)
```

Bindings:

```text
BELOW -> comparator lt
ABOVE -> comparator gt
EQUAL -> comparator eq
```

The surface words are aliases/bindings and are not machine opcodes.

## Promoted conditional-route radical

After transfer across gravity, temperature, memory pressure, phase coherence, risk and phase-error examples, the expanded path remains unchanged:

```text
R.CONDITIONAL_ROUTE
  = DIFFERENCE
  -> CONDITION
  -> ORDER
  -> TRANSFORM
  -> COMPOSITION
```

The program graph is:

```text
delta = DIFFERENCE(subject, threshold)
predicate = CONDITION(delta, comparator, 0)
route = TRANSFORM(control_location, route, target)
sequence = ORDER(predicate, route)
program = COMPOSITION(predicate, sequence, route)
```

## Surface convergence

For a fixed binding, word and symbol forms normalize to the same canonical tuple. Examples:

```text
IF temperature ABOVE 80 THEN GO cooling.emergency
IF temperature > 80 THEN GO cooling.emergency
temperature > 80 -> cooling.emergency
```

All normalize to:

```text
(subject=temperature, comparator=gt, threshold=80.0, target=cooling.emergency)
```

## Execution boundary

This release establishes canonical control-graph representation and deterministic surface normalization. It does not claim that the recovered historical PNV/1 runtime already executes conditional branches. Generic natural-language compilation remains disabled.

## Primitive status after v0.7

Mathematical/reused leaves:

```text
SOURCE
ORDER
TRANSFORM
COMPOSITION
DIFFERENCE
IDENTITY
```

Control leaf promoted by transfer:

```text
CONDITION
```

`ACTION_REQUEST` remains available in recovered PNV/1 but is not required for internal routing.
