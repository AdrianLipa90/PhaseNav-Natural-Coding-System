# PNCS v0.17 — Written PNCS Projection

## Scope

v0.17 defines a compact written representation of already existing PNCS `DefinitionContent` objects. It is not an independent parser-first language and it does not make text a semantic authority.

## Canonical four-line form

```text
PNCS 0.17
KIND PREDICATE
CID pncs:def:sha256:<64 hex>
BODY risk ABOVE 0.8
```

For an internal branch:

```text
PNCS 0.17
KIND INTERNAL_BRANCH
CID pncs:def:sha256:<64 hex>
BODY IF risk ABOVE 0.8 THEN GO safety.pause ELSE GO runtime.continue
```

The projection ends with exactly one newline.

## Authority rule

A written projection can be parsed only against a `ProjectionRegistry` that already contains the claimed `DefinitionContent` CID.

Therefore:

```text
text -> new semantic object
```

is not admitted in v0.17.

The admitted path is:

```text
registered DefinitionContent
-> canonical written projection
-> reconstruct graph from BODY
-> recompute DefinitionContent CID
-> compare with registered CID/payload
-> canonical re-render equality
-> same registered DefinitionContent
```

An unknown CID fails closed even if the text is otherwise syntactically valid and its CID was correctly computed externally.

## Determinism

The renderer uses:

- canonical identifiers, never aliases;
- `BELOW`, `ABOVE`, `EQUAL` for canonical `lt`, `gt`, `eq`;
- explicit parentheses around Boolean composition;
- canonical normalized predicate order inherited from v0.10;
- canonical internal route identifiers;
- Python shortest round-trip float representation for finite thresholds.

The parser requires exact canonical re-render equality. Case changes, extra spaces, missing final newline, additional lines, CID edits, threshold edits, and route edits fail closed.

## Semantic identity

For registered content `D`:

```text
parse(render(D)).content_id == D.content_id
parse(render(D)).semantic_payload == D.semantic_payload
```

Natural-language aliases and provenance are not emitted into written semantic projection.

## PNV relation

No PNV opcode is added. Native v0.17 evidence uses only recovered `SOURCE`, `COMPOSITION`, and `IDENTITY` operators to record round-trip identity witnesses.

## Non-goals

v0.17 does not:

- enable generic natural-language compilation;
- authorize new semantic content from text;
- execute effects;
- introduce `DEFINE`, `PARSE`, `PROJECTION`, or any other opcode;
- change v0.15/v0.16 natural resolution or admission rules.
