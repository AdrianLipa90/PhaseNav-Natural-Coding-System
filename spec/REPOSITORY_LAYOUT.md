# PNCS Canonical Repository Layout

Status: NORMATIVE REPOSITORY STRUCTURE

This document defines repository placement only. It does not alter PNCS semantic identity, content IDs, 36D realizations, semantic-mass bindings, graph-cost records, or execution semantics.

```text
/
├── README.md
├── pyproject.toml
├── MANIFEST.sha256.json
├── src/                         # reference implementation
│   └── phasenav_natural_code/
├── tests/                       # conformance and gate tests
├── native/                      # native .pnv witnesses/program units
├── registry/                    # semantic registries and content indexes
│   ├── definitions/
│   ├── classes/
│   ├── files/
│   ├── clusters/
│   └── hierarchy/
├── provenance/                  # non-semantic audit artifacts
│   ├── ledgers/
│   └── receipts/
└── spec/                        # normative specifications and roadmap
    ├── ROADMAP.md
    └── REPOSITORY_LAYOUT.md
```

## Placement invariants

1. Semantic registries live only under `registry/`.
2. Ledgers and deterministic receipts live only under `provenance/`.
3. Runtime/reference code lives only under `src/`.
4. Native PNCS/PNV artifacts live only under `native/`.
5. Specifications live only under `spec/`.
6. A file move must not change file bytes unless an explicit gate requires a content change.
7. Repository paths are provenance/projection metadata and are not semantic identity.
8. Duplicate normative documents are forbidden. `spec/ROADMAP.md` is the single roadmap authority.
9. `MANIFEST.sha256.json` fails closed whenever repository placement changes and must be regenerated before release closure.

## Canonicalization after v0.21

The layout cleanup moves the existing top-level `definitions/`, `classes/`, `files/`, `clusters/`, and `hierarchy/` trees under `registry/`, and moves `mining/` and `receipts/` under `provenance/`. Existing Git subtrees are reused without content mutation. The duplicate engineering-roadmap copy is removed; `spec/ROADMAP.md` remains authoritative.
