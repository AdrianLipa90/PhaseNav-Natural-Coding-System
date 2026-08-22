# PNCS File and Cluster Paths v0.13

Status: `CONTENT_ADDRESSED / READ_ONLY / CHYBA / NO_NEW_OPCODE`

## FILE

A FILE-level semantic object is an ordered composition of CLASS content IDs. A filesystem location, filename, extension, repository path, and alias are record metadata only and are excluded from the FILE semantic digest.

```text
FILE_CONTENT = ORDERED_COMPOSITION(class_content_id_1, ..., class_content_id_n)
```

Native roots reference `C.<hash>.ROOT` nodes and do not copy CLASS or DEFINITION graphs.

## CLUSTER

A CLUSTER-level semantic object is an ordered composition of FILE content IDs. Deployment folders or human-facing cluster names are record metadata only.

```text
CLUSTER_CONTENT = ORDERED_COMPOSITION(file_content_id_1, ..., file_content_id_n)
```

Native roots reference `F.<hash>.ROOT` nodes.

## Lineage

```text
CLUSTER -> FILE -> CLASS -> DEFINITION -> RADICAL -> KAKU
```

Every content dependency is resolved by content ID. Missing dependencies fail closed. Ordering remains semantic at FILE and CLUSTER levels. Predicate-only Boolean commutativity from v0.10 is not lifted to either level.

## Projection boundary

`projection_path` is retained in content records for provenance and tooling, but it is not included in semantic content hashes. Two records may therefore project the same FILE or CLUSTER semantic object to different physical or deployment paths while sharing one content ID. Their record IDs remain different.

## Validation boundary

This release validates deterministic content addressing, dependency closure, inverse expansion, serialization integrity, and PNV/1-compatible structural output. It does not claim historical native-runtime replay or external canon promotion.
