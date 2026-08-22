# PNCS Roadmap

PNCS is developed directly in native PNV. The 36D PhaseNav state is the computational coordinate surface; typed relations and canonical paths carry semantic structure. Hand-named semantic axes are not a prerequisite.

## Completed foundation sequence

### v0.1 — Structural foundation
36D integrity container, KAKU schema, relation graph, path lineage, fail-closed compiler boundary.

### v0.2 — TIR × Secret of a Half seed
Source-derived relational seeds encoded directly in native PNV. No invented 36-axis semantic dictionary.

### v0.3 — Relation mining
Recurring graph motifs extracted from TIR and Secret of a Half.

### v0.4 — Primitive closure and transfer
First cross-source grammar radical promotion and canonical path normal form.

### v0.5 — Semantic collision repair
`DERIVE` and unqualified `RESOLVE` removed from the irreducible PNCS KAKU set; name resolution separated from mathematical solving.

### v0.6 — First control-flow graph
Bounded `IF ... THEN GO ...` surface normalized into an inspectable PNV graph.

### v0.7 — Control transfer closure
Internal `GO` corrected to control-location `TRANSFORM`; `R.CONDITIONAL_ROUTE` promoted after cross-domain transfer.

### v0.8 — Logic and branching
AND/OR/NOT/ELSE reduced to `COMPOSITION`, `NEGATION`, `ORDER`, `TRANSFORM`, and existing comparison paths. No new opcode.

### v0.9 — Recursive grouping
Explicit parentheses create recursive predicate-tree structure without creating a KAKU. Homogeneous N-ary AND/OR chains are supported. Mixed ungrouped AND/OR fails closed; no implicit precedence is guessed.

### v0.10 — Pure predicate Boolean equivalence
Pure predicate graphs have deterministic algebraic equivalence keys. Commutativity/associativity of AND/OR, double negation, De Morgan, idempotence and absorption are scoped to pure read-only predicates. Arbitrary PNV `COMPOSITION` is not declared commutative. Distribution and Boolean constant folding remain deferred.

### v0.11 — Content-addressed reusable definition paths
Stable normalized graphs can be named without making names semantic authority. Semantic content IDs are SHA-256-addressed over canonical graph content plus expanded leaf path. Aliases/provenance have separate record IDs. Dependencies reference prior content IDs, native roots use content-derived IDs, and exact expansion to stabilized leaves is retained.

## Current observed leaf set

```text
SOURCE
ORDER
TRANSFORM
COMPOSITION
DIFFERENCE
IDENTITY
CONDITION
NEGATION
```

This is an observed/mined working set, not a claim of final irreducibility.

## Completed hierarchy lift

### v0.12 — Class paths over definitions
Content-addressed Definition Paths compose into ordered CLASS-level trajectories. CLASS semantic identity references Definition content IDs rather than copied graphs. Alias/provenance remain record metadata, ordering is semantic, and inverse expansion `CLASS -> DEFINITION -> KAKU` is deterministic.

### v0.13 — File and cluster paths
Ordered CLASS content IDs compose into FILE semantic trajectories; ordered FILE content IDs compose into CLUSTER trajectories. Physical/repository/deployment paths are projection metadata only and do not enter semantic identity. Inverse expansion `CLUSTER -> FILE -> CLASS -> DEFINITION -> KAKU` is deterministic.

### v0.14 — Subsystem / daemon / orchestrator / system paths
CLUSTER content IDs compose into sibling SUBSYSTEM and DAEMON levels; LOW_ORCHESTRATOR composes those roles, HIGH_ORCHESTRATOR composes LOW_ORCHESTRATOR paths, and SYSTEM composes HIGH_ORCHESTRATOR paths. Level and ordering are semantic; aliases and deployment projections are metadata only. Full inverse lineage reaches KAKU.

## Completed natural-surface gate

### v0.15 — Bounded natural relation resolver
Pure natural predicate surfaces resolve through explicit symbol/relation registries into existing PNCS comparison and Boolean graphs. Equivalent registered paraphrases converge to one Definition content ID. Unknown or ambiguous aliases, unsupported relations, unit guesses, and mixed ungrouped Boolean precedence fail closed. Generic natural-language execution remains disabled.

## Completed natural-control gate

### v0.16 — Bounded natural control resolver
Bounded `IF/THEN/ELSE` natural control statements resolve onto existing `INTERNAL_BRANCH` Definition content. Predicate semantics reuse v0.15; route targets require an explicit internal-route registry and reduce to `TRANSFORM(control_location, route, target)`. Candidate route declarations are separated from admission. Runtime-support evaluation uses `TRUE`, `FALSE`, and `UNRESOLVED`; unresolved inputs remain `CHYBA` and admit no route. No effect request or new opcode is introduced.

## Completed written-projection gate

### v0.17 — Written PNCS projection
Registered Definition content now has a deterministic four-line written form (`PNCS 0.17`, `KIND`, `CID`, `BODY`). Parsing requires the claimed content to pre-exist in `ProjectionRegistry`; BODY is reconstructed, rehashed and compared to the registered semantic payload, then exact canonical re-render equality is required. Text therefore cannot create new semantic content. No new opcode is introduced.

## Completed realization and mass gates

### v0.18 — Exact 36D realization binding
Typed PNCS content IDs bind to exact provenance-carrying `T^36` realizations. Vector equality/similarity is not semantic authority, conflicting realizations fail closed, and the unrecovered historical PNV/1 vector generator is not replay-claimed.

### v0.19 — Semantic mass binding
`Kaku.semantic_mass` binds to the validated PhaseNav runtime functional `m_k = κ*(1 + α_M*k) + (L4/L3)*R_k`. `R_k` uses the full exact 36D realization and `k` is an explicit positive index; no content-ID-to-index inference is admitted. The runtime source contract is SHA-256 pinned, direct parity is validated, and equal mass is not semantic-equivalence authority.

## Next gates

### Gate 20 — Mass-aware graph cost and safe distributivity
Define graph cost from bound KAKU mass without changing semantic identity. Use that cost only as an optimization/admission observable, then admit distributive rewrites only when canonical equivalence is preserved and duplication policy is explicit.

### Gate 21 — Boolean constant evaluation
Evaluate TRUE/FALSE outcomes as runtime values without silently creating new KAKU or semantic content objects.

## Deferred algebra gates

### Cost-aware distributivity
Admit distributive rewrites only after a graph-cost/semantic-mass policy can prevent uncontrolled duplication.

### Boolean constant folding
Evaluate whether tautology/contradiction reduction requires explicit TRUE/FALSE graph objects or can remain an evaluation-only result without new KAKU.
