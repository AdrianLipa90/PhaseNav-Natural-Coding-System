# PNCS Class Paths v0.12

Status: `PASS_CANDIDATE / CONTENT_ADDRESSED_CLASS_PATH / NO_NEW_OPCODE / FAIL_CLOSED`

## Purpose

Lift stabilized content-addressed Definition Paths to the next PNCS hierarchy level without copying definition graphs.

## Identity

A CLASS semantic content object contains only an ordered tuple of Definition content IDs plus the class path mode:

```text
CLASS_CONTENT = ORDERED_COMPOSITION(def_id_1, def_id_2, ...)
```

The class alias and provenance are record metadata and do not enter semantic content identity. Reusing a different alias for the same ordered Definition IDs therefore yields the same CLASS content ID.

## Ordering

Unlike pure Boolean predicate normalization, CLASS order is semantic. Swapping Definition Paths changes the CLASS content ID. No global commutativity is inferred.

## Native realization

Native PNV class roots reference existing content-derived `D.<hash>.ROOT` nodes using only recovered `ORDER`, `COMPOSITION`, and `IDENTITY` opcodes. Definition graphs are not copied into the CLASS source.

## Inverse expansion

Every CLASS can be expanded deterministically:

```text
CLASS content ID
  -> ordered Definition content IDs
  -> Definition leaf paths
  -> KAKU leaf lineage
```

Missing Definition content IDs fail closed.

## Epistemic status

All records remain `CHYBA`, `canon_allowed=false`. This gate establishes structural/content-addressed class composition and reference execution, not historical native-runtime replay.
