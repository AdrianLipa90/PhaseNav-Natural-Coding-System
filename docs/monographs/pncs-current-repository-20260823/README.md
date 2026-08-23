# PNCS Current Repository Monograph — 23 August 2026

Status: `NON-NORMATIVE REPOSITORY-WIDE SYNTHESIS / MAIN + BRANCH TOPOLOGY`.

Pinned repository snapshot: `AdrianLipa90/PhaseNav-Natural-Coding-System@de8ccd4a6d7c32bd0a079a679416c556c5901790`.

This corrected edition extends the existing 55-page PNCS v0.26 monograph instead of replacing it with a separate research brochure.

## Structure

- Part I: the complete v0.26 core monograph. Its canonical repository source remains `spec/PNCS_MONOGRAPH_V0_26.md`. The locally rendered full edition preserves the supplied `PNCS_MONOGRAPH_V0_26.pdf` verbatim.
- Part II: current repository update covering:
  - v0.27 ORCHORBITAL × Hydro T^36 release closure;
  - T^36 temporal-fibre optimization;
  - merged experimental prime-temporal hydrodynamic coding layer;
  - v0.28 adversarial release-closure implementation now on main, with release still NOT CLOSED;
  - branch topology and merged/historical/superseded classification;
  - updated evidence matrix, current frontier, formulas and source map.

## Local full-edition build

Place the supplied v0.26 PDF next to `main.tex` as `PNCS_MONOGRAPH_V0_26_BASE.pdf`, then run:

```bash
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

The repository does not duplicate the historical v0.26 PDF binary; its canonical text source already exists under `spec/`.

## Authority boundary

The monograph is a synthesis. Normative authority remains with versioned repository specifications, registries, receipts and ledgers. The current v0.28 spec on main states `CURRENT-MAIN INTEGRATION GATE / RELEASE NOT CLOSED`; merge of PR #15 is not treated as release closure by itself.
