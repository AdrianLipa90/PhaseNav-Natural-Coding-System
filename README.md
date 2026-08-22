# PhaseNav Natural Code System (PNCS)

Status: HIGHER_HIERARCHY_PATHS_V0_14 / FOUNDATION LINEAGE V0.1-V0.14

PhaseNav Natural Code System is a 36-dimensional relational coding system in which written code is a human-readable projection of a canonical semantic-phase graph.

Core construction:

KAKU -> RADICAL -> DEFINITION_PATH -> CLASS_PATH -> FILE_PATH -> CLUSTER_PATH -> SUBSYSTEM/DAEMON_PATH -> ORCHESTRATOR_PATH -> SYSTEM_PATH

Natural language is an admissible input surface only after resolution to canonical relational paths.

## Foundation rule

The language is derived bottom-up from a fixed 36D basis and composition rules. Keywords and textual syntax are not authoritative semantics.

## Current scope

Version 0.1 establishes:
- exact 36D vector container,
- KAKU atom schema,
- relational edge schema,
- graph container,
- path lineage model,
- fail-closed validation,
- natural-language compiler interface as an intentionally unimplemented boundary until the 36D semantic basis is canonized.

No semantic axis names are invented in this foundation release.

## v0.2 native-PNV direction

The first semantic basis seed is now derived from TIR + The Secret of a Half and encoded directly in native PNV/1 under `native/PNCS_TIR_SOH_SEED_V0_2.pnv`.

PNCS no longer assumes that the 36 coordinates require manually invented semantic axis names. The 36D PNV surface is the computational realization; relational operators and paths carry the typed structure.

## v0.3 — Grammar Mining Pass 01

TIR + The Secret of a Half were reduced to source-backed relation chains. The first recurring graph motifs are now encoded natively in `native/PNCS_GRAMMAR_MINING_V0_3.pnv`: fixed-point, invariant, cancellation, conjugacy and convergence. They introduce no new PNV opcode; each is a composition over the existing PNV/1 relational vocabulary. Recurrence support is stored separately from semantic mass.



## v0.4 — Primitive Closure and Transfer

The v0.3 radicals reduce to a seven-operator observed core. `R.INVARIANT = TRANSFORM -> DIFFERENCE -> IDENTITY` transferred unchanged into PhaseNav projective gauge invariance and the Consciousness Dictionary invariant definition, so it is promoted to `PROMOTED_GRAMMAR_RADICAL`. `R.TRAJECTORY = ORDER -> TRANSFORM -> COMPOSITION` is added as a transferred candidate. A first canonical path normal form now makes ordered KAKU expansion and argument binding authoritative; vector similarity and surface wording are non-authoritative.

## v0.5 — Semantic Collision Repair

`DERIVE` and unqualified `RESOLVE` are no longer classified as irreducible PNCS KAKU. `R.DERIVATION` expands to `SOURCE -> COMPOSITION -> TRANSFORM`. PNV name resolution is separated from mathematical solving and expands through `R.NAME_RESOLUTION = SOURCE -> COMPOSITION -> IDENTITY`. `R.FIXED_POINT` is reduced to a state-binding specialization of the already promoted `R.INVARIANT`, so both share the same leaf path `TRANSFORM -> DIFFERENCE -> IDENTITY`. The current mathematical leaf set is six operators (`SOURCE`, `ORDER`, `TRANSFORM`, `COMPOSITION`, `DIFFERENCE`, `IDENTITY`), while `CONDITION` remains a control-flow candidate for the next gate.


## v0.6 — First Control-Flow Program

The frozen surface example `IF gravity BELOW 0.5 THEN GO physics.gravity.low` now normalizes to a native PNV graph without introducing `IF`, `BELOW`, `THEN`, or `GO` as opcodes. `BELOW` expands through `DIFFERENCE -> CONDITION`; `THEN` binds order; `GO` binds the recovered `ACTION_REQUEST(route,target)` operator. The complete candidate leaf path is `DIFFERENCE -> CONDITION -> ORDER -> ACTION_REQUEST -> COMPOSITION`. `ACTION_REQUEST` remains an inspectable request node and does not imply hidden execution. Generic natural-language compilation remains disabled; v0.6 only freezes and tests this bounded control-surface family.


## v0.7 — Control Transfer Closure

The v0.6 internal `GO` binding to `ACTION_REQUEST` is superseded. Internal route changes now expand through `TRANSFORM(control_location, route, target)`, keeping control flow separate from effect requests. The shared comparison radical expands to `DIFFERENCE -> CONDITION`, and `R.CONDITIONAL_ROUTE` transferred unchanged across six domains with leaf path `DIFFERENCE -> CONDITION -> ORDER -> TRANSFORM -> COMPOSITION`; it is promoted to `PROMOTED_CONTROL_RADICAL`. No new PNV opcode is introduced.

## v0.8 — Logic and Branching

Bounded `AND`, `OR`, `NOT`, and `ELSE` surfaces now normalize without new machine opcodes. Two-predicate `AND`/`OR` expressions compose already-formed predicates with `COMPOSITION(..., all|any, ...)`; `NOT` uses the recovered `NEGATION` operator; `ELSE` binds a second internal `TRANSFORM` route to `NEGATION(primary_predicate)`. Internal routing remains separate from `ACTION_REQUEST`. Mixed/nested boolean expressions remain fail-closed pending a later grouping gate.

## v0.9 — Recursive Grouping

Predicate composition is now recursive. Explicit parentheses define tree structure but introduce no KAKU or opcode. Homogeneous N-ary AND/OR chains are supported as repeated `COMPOSITION` with `all`/`any` bindings. Mixed ungrouped AND/OR still fails closed; PNCS does not guess conventional precedence. `NOT` continues to use existing `NEGATION`, and internal routes remain `TRANSFORM(control_location, route, target)` rather than `ACTION_REQUEST`.

## v0.10 — Pure Predicate Boolean Algebra

Boolean equivalence canonicalization is now separated from surface parsing. For pure read-only predicate graphs only, PNCS admits commutativity/associativity of AND/OR, double-negation elimination, De Morgan rewrites, idempotence, and absorption. This does not make arbitrary PNV `COMPOSITION` commutative or associative. Distributivity and TRUE/FALSE constant folding remain deliberately deferred. No new opcode is introduced.

## v0.11 — Content-Addressed Definition Paths

Stable normalized predicate and internal-branch graphs can now be registered as reusable `DEFINITION`-level objects. Semantic identity is `pncs:def:sha256:<digest>` over canonical graph content plus fully expanded leaf path; alias, provenance, and dependency metadata are excluded from semantic identity and preserved separately in `pncs:def-record:sha256:<digest>` records. Equivalent aliases share one semantic content object while retaining independent provenance records. Dependencies reference prior content IDs and fail closed when unresolved. Native PNV roots are keyed by content-derived IDs and reuse prior roots directly; no `DEFINE` or `ALIAS` opcode was added. v0.11 passes 149/149 tests.

## v0.12 — Content-addressed Class Paths

Definition content IDs are now composable into ordered CLASS-level semantic trajectories. CLASS content identity is derived from the ordered Definition content-ID sequence, not from aliases or filesystem locations. Native class roots reference `D.<hash>.ROOT` nodes through recovered `ORDER` / `COMPOSITION` / `IDENTITY` operators; definition graphs are not copied. Inverse expansion `CLASS -> DEFINITION -> KAKU` is deterministic and missing dependencies fail closed.



## v0.13 — Content-addressed File and Cluster Paths

CLASS content IDs now compose into ordered FILE semantic trajectories, and FILE content IDs compose into ordered CLUSTER semantic trajectories. Filesystem/repository/deployment paths are preserved only as record metadata (`projection_path`) and are excluded from semantic identity. Native FILE roots reference `C.<hash>.ROOT`; CLUSTER roots reference `F.<hash>.ROOT`. Full inverse lineage `CLUSTER -> FILE -> CLASS -> DEFINITION -> KAKU` is deterministic, with missing dependencies failing closed. No new PNV opcode is introduced. v0.13 passes 188/188 tests.


## v0.14 — Content-addressed Higher Hierarchy Paths

CLUSTER content IDs now compose into sibling SUBSYSTEM and DAEMON semantic levels. LOW_ORCHESTRATOR paths may compose both sibling types; HIGH_ORCHESTRATOR paths compose LOW_ORCHESTRATOR IDs; SYSTEM paths compose HIGH_ORCHESTRATOR IDs. Level identity and ordered child content IDs determine semantic hashes. Aliases and deployment/service projections remain record metadata only. Native roots use existing `IDENTITY`, `ORDER`, and `COMPOSITION` operators, and full inverse expansion `SYSTEM -> ... -> KAKU` is deterministic and fail-closed. No new opcode is introduced. v0.14 passes 208/208 tests.

## v0.15 — Bounded Natural Relation Resolver

Natural predicate phrases now resolve through explicit symbol and relation registries into the stabilized predicate graph. Surface forms such as `risk above 0.8`, `risk is greater than .80`, `risk exceeds 0.8`, and `risk > 0.8` converge to the same content-addressed Definition identity when their registered semantics are identical. Multi-word subjects such as `phase coherence` resolve to canonical identifiers, Boolean composition reuses v0.9/v0.10, and percent notation is accepted only for symbols with an explicit normalized-fraction policy. Unknown or ambiguous aliases, unsupported comparators, unit guesses, and free-form high/low wording fail closed. Generic `compile_natural_language()` remains disabled; v0.15 resolves pure predicates only and executes no routes or effects. No new PNV opcode is introduced. v0.15 passes 235/235 tests.
