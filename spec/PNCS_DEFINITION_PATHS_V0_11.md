# PNCS Definition Paths v0.11 — Content-Addressed Reuse

Status: `PASS_09 / CONTENT_ADDRESSED_DEFINITION_PATHS / NO_NEW_OPCODE / FAIL_CLOSED`

## Scope

This pass introduces reusable named definition paths above the already stabilized PNCS predicate/control graph layers.

A definition has two separate identities:

1. **semantic content identity** — derived only from the canonical normalized graph and its fully expanded stabilized leaf path;
2. **record identity** — derived from alias, semantic content ID, provenance, dependencies, epistemic state and canon flag.

The human name is therefore not semantic authority.

## Content identity

For a definition content payload:

```text
schema
kind
canonical_graph
leaf_path
```

PNCS computes:

```text
content_id = "pncs:def:sha256:" + SHA256(canonical_json(payload))
```

The hash excludes:

```text
alias
provenance
dependencies
record_id
```

Therefore equivalent normalized graphs have the same semantic identity even when they originate from different surface spellings or aliases.

Example:

```text
high_risk := risk ABOVE 0.8
risk_guard := risk > .800
```

Both normalize to:

```text
comparison(risk, gt, 0.8)
```

and therefore share one `content_id`.

## Record identity and provenance

Each alias is represented by a separate definition record:

```text
record_id = SHA256(
  alias,
  content_id,
  provenance,
  dependencies,
  epistemic_operator,
  canon_allowed
)
```

This preserves provenance without duplicating semantic content.

Two aliases can therefore share one content object while retaining different record IDs.

## Dependency lineage

A reusable definition can refer to previously registered definition content IDs.

Example:

```text
safety_trigger
  = risk > 0.8 OR memory_pressure > 0.9

phase_ready
  = NOT phase_coherence < 0.7

system_guard
  = safety_trigger AND phase_ready
```

`system_guard` records both prior content IDs as dependencies. Registration fails closed when a referenced dependency is not already present.

This creates an acyclic construction order for v0.11 without introducing a separate dependency opcode.

## Native PNV representation

PNV/1 receives no `DEFINE`, `ALIAS`, `IMPORT`, or other new opcode.

Native roots are keyed by the first 16 hexadecimal characters of the semantic content digest:

```text
D.<content-short-id>.ROOT
```

Aliases are stored in the definition registry, not in native semantic node IDs.

Where possible, new definitions reuse earlier native roots directly rather than copying their lower-level graph.

For example:

```text
D.system_guard.ROOT
  = COMPOSITION(
      D.safety_trigger.ROOT,
      D.phase_ready.ROOT,
      all
    )
```

The actual file uses content-address-derived IDs rather than the human names shown above.

## Inverse expansion

Every definition content stores its fully expanded `leaf_path`.

For the current v0.11 scope the admitted leaves are:

```text
DIFFERENCE
CONDITION
COMPOSITION
NEGATION
ORDER
TRANSFORM
```

A definition can therefore be expanded back to its stabilized lower-level path without consulting its alias.

Examples:

```text
high_risk
  -> DIFFERENCE
  -> CONDITION

safety_trigger
  -> DIFFERENCE
  -> CONDITION
  -> DIFFERENCE
  -> CONDITION
  -> COMPOSITION

safety_bifurcation
  -> DIFFERENCE
  -> CONDITION
  -> DIFFERENCE
  -> CONDITION
  -> COMPOSITION
  -> NEGATION
  -> ORDER
  -> TRANSFORM
  -> ORDER
  -> TRANSFORM
  -> COMPOSITION
```

## 36D realization

Each unique definition content may receive a PNV `VECTOR` address derived from its full `content_id`.

This address is a computational realization. It does not replace the relational graph and does not make vector similarity semantic authority.

## Epistemic boundary

All v0.11 records remain:

```text
EPISTEMIC CHYBA
canon_allowed = false
```

Content addressing proves deterministic identity within the implemented PNCS normalization rules. It does not independently prove that the reconstructed PNV/1 runtime is the historical canonical runtime.

## Integrity rules

- zero new opcode;
- alias is not semantic identity;
- provenance is not hashed into semantic identity;
- provenance is hashed into record identity;
- dependencies are content IDs, not alias strings;
- dependencies must exist before registration;
- duplicate aliases fail closed;
- semantic graph differences change the content hash;
- native nodes use content-derived IDs;
- internal branches remain `TRANSFORM` routes, not `ACTION_REQUEST`;
- definition expansion remains lossless to the declared stabilized leaf path;
- generic natural-language compilation remains disabled outside the bounded surface grammars.
