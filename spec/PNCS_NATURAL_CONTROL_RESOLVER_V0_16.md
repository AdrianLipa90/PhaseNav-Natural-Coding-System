# PNCS v0.16 — Natural Control Resolver

## Scope

v0.16 adds a bounded natural-language projection for internal PNCS control flow.
It does not enable the generic natural-language compiler and it does not create an effect executor.

Accepted control statements have the bounded form:

```text
IF <registered natural predicate> THEN GO <registered internal route>
IF <registered natural predicate> THEN GO <registered internal route> ELSE GO <registered internal route>
```

`GO TO` and `ROUTE TO` are admitted surface aliases. They are not PNV opcodes.

## Semantic reduction

The predicate is resolved by the v0.15 natural relation resolver and Boolean normalizer.
The route phrase is resolved by an explicit route registry.
The resulting program is represented by the existing `INTERNAL_BRANCH` Definition content.

```text
natural predicate
  -> canonical Predicate
  -> predicate Definition content

natural route phrase
  -> registered canonical route target

Predicate + route target(s)
  -> BranchProgram
  -> DefinitionContent(kind=INTERNAL_BRANCH)
  -> pncs:def:sha256:<content>
```

No new content namespace is introduced for natural control syntax.
Equivalent natural surfaces and the corresponding canonical branch therefore share one Definition content ID.

## Route boundary

Every v0.16 route target is `INTERNAL_TRANSFORM` only:

```text
TRANSFORM(control_location, route, target)
```

The following are not equivalent and are not produced by v0.16:

```text
ACTION_REQUEST(...)
WRITE(...)
DELETE(...)
EXEC(...)
NETWORK(...)
```

An arbitrary dotted name is not route authority. A target must be registered explicitly.

## Candidate route vs admitted route

A parsed branch contains candidate route declarations. Parsing a candidate route does not admit it.
Admission depends on predicate truth at evaluation time.

```text
TRUE       -> admit true route
FALSE      -> admit false route if declared; otherwise admit none
UNRESOLVED -> CHYBA; admit no route
```

Missing, non-numeric, or non-finite values are unresolved for v0.16 admission and cannot silently become true or false.

For compound predicates, v0.16 uses explicit three-state propagation:

```text
NOT UNRESOLVED = UNRESOLVED
AND: FALSE dominates; otherwise UNRESOLVED dominates; otherwise TRUE
OR:  TRUE dominates; otherwise UNRESOLVED dominates; otherwise FALSE
```

This truth-state evaluation is an admission guard. It does not add TRUE/FALSE/UNRESOLVED PNV opcodes.

## Fail-closed cases

v0.16 rejects:

- unknown route aliases,
- ambiguous route aliases,
- arbitrary unregistered target names,
- effect verbs in place of internal `GO`/`ROUTE TO`,
- predicates rejected by v0.15,
- mixed ungrouped AND/OR precedence,
- unsupported natural free-form control syntax.

## Provenance

Surface predicate and route traces are retained as provenance data. They do not enter Definition semantic identity.

## Runtime status

The resolver and admission evaluator are reference/runtime-support code on the verified live `/dev/shm/ciel_noema` surface. Exact historical PNV-runtime replay is not claimed.
