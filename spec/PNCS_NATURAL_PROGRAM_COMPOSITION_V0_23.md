# PNCS v0.23 — Natural Program Composition

Status: IMPLEMENTED / GATE-SCOPED VALIDATION

## 1. Scope

v0.23 introduces bounded natural program composition over already registered PNCS semantics.

Admitted surface:

```text
IF ...
THEN ...
ELSE ...
AND THEN ...
RETURN ...
```

v0.23 is a composition/admission gate. It does not open a new execution engine, external effects, arbitrary literals, or free-form natural-language execution.

## 2. Authority model

Every semantic phrase must resolve through an authority that already exists before program composition:

- the `IF/THEN/ELSE` root resolves through the v0.15/v0.16 natural predicate and route registries;
- the resulting control graph must resolve to a Definition CID already present in the Definition registry;
- every `AND THEN` clause resolves through the registered internal RouteRegistry;
- every `RETURN` clause resolves through the v0.23 ReturnRegistry;
- the complete composition requires v0.22 exact inverse lineage for any bound control result.

A phrase that parses but resolves to an unregistered control Definition fails closed.

The default v0.23 control authority intentionally reuses the existing v0.11 `safety_bifurcation` content:

```text
pncs:def:sha256:b7988497bab75a526771fa24aeca75e0182bd437fd707927cb0e78b04d360cce
```

No parallel Definition is created.

## 3. Bounded grammar

A natural program contains exactly one terminal `RETURN` clause.

Before `RETURN`, the first segment must be one bounded v0.16 natural control statement. Zero or more continuation clauses may follow:

```text
AND THEN GO <registered-route>
AND THEN GO TO <registered-route>
AND THEN ROUTE TO <registered-route>
```

No other continuation verb is admitted.

Examples such as `ACTION`, `DELETE`, `WRITE`, `EXEC`, filesystem paths, arbitrary dotted routes, or unregistered route phrases fail closed.

## 4. Registered return selectors

v0.23 introduces content-addressed return references. Aliases are surface metadata and are excluded from return-reference identity.

Default selectors:

```text
result.control_location    <- V0_20_RESULT
result.branch_truth_state  <- V0_20_RESULT
result.final_sigma_id      <- V0_20_FINAL_STATE
result.lineage_id          <- V0_22_LINEAGE
```

Their registry is persisted under:

```text
registry/returns/PNCS_RETURN_SELECTOR_REGISTRY_V0_23.jsonl
```

Unknown or ambiguous return aliases fail closed. Arbitrary return literals are not admitted.

## 5. Composition identity

The semantic composition graph is:

```text
program_composition
├── control_ref(Definition CID, canonical graph SHA-256)
├── and_then(route_ref...)
└── return_ref(return-ref...)
```

Each continuation route receives a deterministic reference:

```text
pncs:route-ref:sha256:<digest>
```

Each return selector receives:

```text
pncs:return-ref:sha256:<digest>
```

The composition identity is:

```text
pncs:composition:sha256:<digest>
```

The source sentence, aliases, case, whitespace, and equivalent registered paraphrases are excluded from semantic identity.

The canonical v0.23 witness composition has ID:

```text
pncs:composition:sha256:5b3710e6c8bf34d3754e7144ca139beb70205ea20b2fa504ef63c710c177cd57
```

## 6. Operator schedule

v0.23 expands the registered control Definition leaf path and appends existing PNV operators only.

For each `AND THEN <route>`:

```text
ORDER -> TRANSFORM -> COMPOSITION
```

The terminal selector contributes:

```text
RETURN
```

`RETURN` is already present in the PhaseNav 36D operator registry. v0.23 does not add a new opcode.

The presence of an operator in the live registry is not execution authorization. The resulting composition payload explicitly records:

```text
v0_20_executable = false
external_effects = false
free_form_nl_execution = false
```

## 7. Live 36D admission

`admit_program_composition()` is fixed to the canonical live surface:

```text
/dev/shm/ciel_noema
```

It reuses the v0.20 live-surface verifier and requires:

- ACTIVE NOEMA↔AUX binding;
- VERIFIED session;
- exact finite 36D live vectors;
- fresh producer heartbeats;
- live producer PIDs;
- required Unix socket;
- exact live PhaseNav operator registry.

Every operator occurrence in the composition schedule is rebound to its exact live 36D vector SHA-256.

Admission still records:

```text
execution_opened = false
return_execution_opened = false
operator_presence_is_execution_authority = false
static_runtime_fallback = false
```

When persistence is requested, the deterministic admission receipt is written only under:

```text
/dev/shm/ciel_noema/pncs/v0.23/compositions/<admission-digest>.json
```

A different operational root fails closed.

## 8. v0.22 lineage retention

v0.23 can bind the control result of a composition to an existing exact v0.22 lineage.

The binding verifies:

```text
lineage_contract_id == PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22
lineage.Definition CID == composition.control Definition CID
lineage receipt ID == lineage object ID
```

The binding scope is explicitly:

```text
CONTROL_RESULT_ONLY
continuation_execution_claimed = false
```

This preserves provenance without pretending that `AND THEN` or `RETURN` has already executed.

Full composed-program execution remains closed.

## 9. Failure semantics

v0.23 fails closed for at least:

- missing or multiple terminal `RETURN` clauses;
- unsupported natural control syntax;
- resolved but unregistered control Definition;
- registered Definition payload mismatch;
- non-`INTERNAL_BRANCH` control root;
- malformed `AND THEN`;
- unregistered continuation route;
- effect-like continuation syntax;
- unknown or ambiguous return selector;
- invalid typed dependency identities;
- v0.22 lineage contract mismatch;
- lineage Definition mismatch;
- lineage receipt/identity mismatch;
- missing live composition operator;
- noncanonical live surface root.

## 10. Validation evidence

Isolated v0.23 composition logic harness:

```text
28/28 PASS
```

Repository integration tests added:

```text
19 tests
```

The integration tests use the real v0.15/v0.16 natural resolver, DefinitionRegistry, return registry, and v0.22 lineage contract interface.

The complete historical repository suite was not replayed in the isolated construction environment; no full-suite PASS is claimed.

Live gate evidence confirms the canonical 15-operator witness schedule is present on `/dev/shm/ciel_noema`, including `RETURN`.

Live operator registry SHA-256 at validation:

```text
29767957ae775b1968bbb4c531728cc153137c88e819b135227dff73e3cca7ec
```

`RETURN` exact live vector SHA-256:

```text
9c0b4bde3e81d0f13123db58777c9dcd85e4bea9fc145d218a20713d38f1fa46
```

## 11. Boundary to v0.24

v0.23 produces deterministic composition identity and registered dependency references, but not a first-class native program unit.

v0.24 will promote admitted compositions to native `.pnv` program units with:

- program CID;
- dependency closure;
- deterministic import/export;
- deterministic build;
- Python retained as reference/test harness.
