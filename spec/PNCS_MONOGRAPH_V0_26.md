# PhaseNav Natural Coding System (PNCS)
## A Content-Addressed 36-Dimensional Relational Programming and Runtime Architecture

**Project Monograph — v0.26**  
**Author:** Adrian Lipa  
**Project:** PhaseNav Natural Coding System  
**Status:** NON-NORMATIVE SYNTHESIS OF IMPLEMENTED CONTRACTS v0.1–v0.26  
**Normative authority:** versioned specifications under `spec/`, semantic registries under `registry/`, deterministic receipts and ledgers under `provenance/`

---

## Abstract

PhaseNav Natural Coding System (PNCS) is a relational programming and runtime architecture in which semantic authority is carried by typed relations, canonical graphs, content-addressed identities, exact execution lineage, and explicitly bound 36-dimensional PhaseNav realizations. Written code and natural-language input are treated as surfaces over a canonical relational structure rather than as the primary source of executable meaning.

The system is built from a compact hierarchy beginning with KAKU, an atomic reusable relational operation, and extending through radicals, definitions, classes, files, clusters, subsystems, orchestrators, systems, native program units, persistent runtime handles, execution receipts, and explicitly authorized external effects. Semantic content identity, exact phase realization identity, semantic-mass identity, program identity, runtime-generation identity, result identity, and effect identity remain deliberately separate.

The 36-dimensional computational realization is represented as an exact phase vector in the torus

\[
T^{36} = (S^1)^{36},
\]

with each component represented as a finite angle in \([0,2\pi)\). PNCS does not derive semantic equivalence from vector equality, vector proximity, semantic-mass equality, repository location, or source wording. Instead, semantic identity is content-addressed from canonical relational payloads and every executable result must be recoverable through deterministic provenance.

The implemented engineering sequence through v0.26 establishes: structural KAKU and relation graphs; a TIR and Secret-of-a-Half relational seed; primitive closure and semantic-collision repair; control flow and Boolean normalization; a content-addressed semantic hierarchy; bounded natural-language and written projections; exact \(T^{36}\) binding; semantic mass; mass-aware graph cost; native internal execution over immutable \(\Sigma\) states; exact inverse execution lineage; bounded natural-program composition; first-class native `.pnv` program units; generation-bound persistent runtime residency; and a default-deny, explicitly authorized effect boundary.

The implemented execution path is therefore not “text to side effect.” It is a verified chain:

```text
registered relation
-> canonical semantic graph
-> content-addressed Definition
-> exact T^36 realization
-> semantic-mass binding
-> admitted internal route
-> live 36D operator execution
-> deterministic result
-> exact inverse lineage
-> first-class native program identity
-> generation-bound persistent runtime
-> explicit effect request
-> explicit authorization
-> bounded adapter
-> deterministic effect receipt
```

This monograph consolidates the implemented architecture and evidence status without replacing the normative versioned specifications.

---

# 1. Scope and epistemic boundary

PNCS separates three questions that are frequently collapsed in conventional software systems:

1. **What does a construct mean?**
2. **How is that construct realized in the 36-dimensional PhaseNav runtime?**
3. **What authority does that construct possess to execute or cause an external effect?**

The system answers them with separate typed identities and contracts.

A canonical semantic content ID is not a phase vector. A phase vector is not an authorization token. A semantic-mass value is not semantic equivalence. A program CID is not permission to access the filesystem. A runtime handle is not permission to perform network I/O. A successful internal execution result is not permission to produce an external effect.

This separation is one of the principal invariants of the architecture.

PNCS is fail-closed. Unknown dimensions, malformed vectors, unresolved relations, ambiguous aliases, noncanonical graphs, stale runtime state, missing lineage, unregistered adapters, and missing effect authorization do not silently degrade to guessed semantics or static substitutes.

The project also distinguishes implemented mechanisms from open reconstruction problems. In particular, the current contracts bind semantic objects to exact 36-dimensional PhaseNav realizations, but they do not claim recovery of every historical native PNV generator detail. The monograph therefore records the implemented contracts rather than filling unresolved gaps with replacement assumptions.

---

# 2. Architectural principle: relations before coordinates

The foundational correction made early in PNCS is that meaning does not require thirty-six hand-named semantic axes.

The 36-dimensional state is the native computational coordinate surface. Semantic authority is carried by typed relations and paths. The construction order is therefore:

```text
mathematical / semantic relation
-> KAKU operator
-> Radical composition
-> Definition
-> exact PhaseNav realization
-> executable route
```

and not:

```text
invented coordinate label
-> arbitrary vector component
-> guessed semantic meaning
```

This distinction allows two semantic objects to share the same phase realization while remaining semantically distinct, and allows two nearby phase realizations to remain semantically unrelated unless the relational graph establishes equivalence.

The canonical hierarchy began in v0.1 as:

```text
L0  KAKU
L1  RADICAL
L2  DEFINITION_PATH
L3  CLASS_PATH
L4  FILE_PATH
L5  CLUSTER_PATH
L6  SUBSYSTEM_PATH / DAEMON_PATH
L7  LOW_LEVEL_ORCHESTRATOR_PATH
L8  HIGH_LEVEL_ORCHESTRATOR_PATH
L9  SYSTEM_PATH
```

Later gates content-addressed the hierarchy and made exact occurrences recoverable in inverse provenance.

The operational invariant is simple:

> every executable high-level path must be auditable downward to KAKU.

A high-level instruction is therefore not accepted merely because it has a familiar name. It must resolve to a registered semantic path whose lineage can be verified.

---

# 3. KAKU: the atomic relational operation

KAKU is the smallest reusable relational operation in PNCS. It is not defined merely as an opcode number or a textual keyword. A KAKU carries an operator role, relational metadata, basis identity, and a finite 36-dimensional realization where such a realization is bound.

The early PNCS seed restricted itself to operator kinds already admitted by the recovered PNV/1 surface, including:

```text
DIFFERENCE
SOURCE
ORDER
COMPOSITION
TRANSFORM
BOUNDARY
CONDITION
NEGATION
RESOLVE
DERIVE
RETURN
```

The engineering rule is conservative: a new semantic construction should reduce to the existing relational operator set wherever possible rather than creating a special-case opcode for each new concept.

This is tested across independent definitions. A useful KAKU is one that recurs as the same relational operation in different semantic paths.

A Radical is then a composition of KAKU atoms. A Definition binds a canonical semantic graph to an exact ordered KAKU leaf path. This relation between graph and leaf path becomes critical later, because execution and inverse lineage both verify that the Definition expands to exactly the expected KAKU schedule.

---

# 4. Mathematical seed: TIR and Secret of a Half

PNCS v0.2 seeded its relational basis from two pre-existing mathematical sources rather than inventing semantic primitives.

The TIR seed contributes a relational chain:

\[
\text{binary distinction}
\rightarrow \ln 2
\rightarrow \text{phase / holonomy normalization}
\rightarrow \kappa
\rightarrow \text{relational action},
\]

with the project constant

\[
\boxed{\kappa = \frac{\ln 2}{24\pi}}.
\]

The Secret-of-a-Half seed contributes complement and self-duality relations. The simplest fixed-point relation is

\[
\sigma \mapsto 1-\sigma,
\qquad
\sigma = 1-\sigma
\quad\Longrightarrow\quad
\sigma = \frac12.
\]

A separate boundary construction uses

\[
\Omega(s)=\frac{s}{1-s},
\]

followed by reciprocal inversion

\[
u \mapsto \frac1u,
\]

and the self-dual condition

\[
|\Omega|=1.
\]

The corresponding imbalance and non-negative defect are represented as

\[
I = \log|\Omega|,
\qquad
D = (\log|\Omega|)^2.
\]

In PNCS these structures serve as relational seeds. They do not authorize a claim that every software relation is physically identical to the source theory from which the relation was obtained.

---

# 5. Primitive closure and semantic collision repair

The next engineering problem is closure: can independent semantic constructions be represented through a sufficiently small existing set of KAKU operations?

PNCS treats primitive growth as a controlled process. When two apparent primitives can be represented as compositions of existing KAKU, no new primitive is added. When two surface phrases resolve to the same canonical relational content, aliases remain projection metadata rather than separate semantic identities.

Conversely, when two distinct semantic objects accidentally collide at a surface or naming layer, the collision is repaired at the typed relational layer rather than by allowing ambiguity into execution.

This is the origin of several later invariants:

- aliases are not semantic authority;
- source wording is not semantic authority;
- repository location is not semantic authority;
- vector similarity is not semantic authority;
- mass equality is not semantic authority.

---

# 6. Control flow as a canonical relational graph

By v0.6–v0.10 PNCS had stabilized a bounded control model and pure Boolean algebra over registered predicates.

A comparison is represented as an explicit relational graph and later executes as:

```text
DIFFERENCE -> CONDITION
```

Negation is represented by:

```text
child -> NEGATION
```

N-ary Boolean composition is reduced through `COMPOSITION` over child truth states.

A canonical branch is not a textual `if` statement. It is a graph whose content is independent of the exact surface phrase used to request it.

For example, the stabilized safety branch used throughout later execution gates is structurally of the form:

```text
branch
  predicate: OR(
      memory_pressure > 0.9,
      risk > 0.8
  )
  true route:  safety.pause
  false route: runtime.continue
```

Its Definition identity is derived from the canonical graph and its exact leaf schedule, not from a source sentence.

A canonical false-arm transfer includes negation of the primary predicate before route transfer. The route-transfer tail is:

```text
ORDER -> TRANSFORM -> COMPOSITION
```

The Boolean layer was deliberately stabilized before opening native execution, because execution should consume a canonical graph rather than simultaneously infer and execute its meaning.

---

# 7. Content-addressed semantic hierarchy

Versions v0.11–v0.14 moved PNCS from named paths to a content-addressed hierarchy.

The important identities include typed IDs such as:

```text
pncs:def:sha256:<digest>
pncs:class:sha256:<digest>
pncs:file:sha256:<digest>
pncs:cluster:sha256:<digest>
pncs:subsystem:sha256:<digest>
pncs:low-orchestrator:sha256:<digest>
pncs:high-orchestrator:sha256:<digest>
pncs:system:sha256:<digest>
```

A Definition content address is derived from canonical semantic content. A Class references Definitions. A File references Classes. A Cluster references Files. Higher-level objects continue this typed hierarchy.

Crucially, the same Definition may occur in more than one valid higher-level context. Therefore inverse provenance cannot simply ask “which class contains this Definition?” and pick the first match. Exact occurrence indexes are required where a Definition has multiple valid parents.

This later becomes a hard v0.22 rule:

```text
ambiguity -> fail closed unless exact occurrence selected
```

The hierarchy therefore supports both content identity and occurrence identity.

---

# 8. Natural-language resolution and written projection

PNCS does not treat unrestricted natural language as executable code.

Versions v0.15 and v0.16 introduced bounded natural surfaces backed by registries. Natural phrases are tokenized and normalized, but only registered symbols, relations, comparators, routes, and aliases may resolve to canonical content.

The direction is:

```text
surface phrase
-> registered symbol/relation resolution
-> canonical predicate/control graph
-> existing content-addressed Definition
```

Unknown or ambiguous phrases fail closed.

The written projection gate v0.17 establishes the reverse direction: canonical semantic content may be rendered as deterministic PNCS text and parsed back only when the text maps exactly to registered authority.

This creates a two-surface model:

```text
natural input -> canonical semantics <- written PNCS projection
```

The canonical semantic object is the center. Neither textual surface is allowed to mutate semantic identity merely through formatting, whitespace, alias choice, or paraphrase.

---

# 9. The exact 36-dimensional PhaseNav realization

The early v0.1 vector contract required exactly thirty-six finite float64-compatible values with explicit coordinate order and basis identity. At that stage the exact semantic interpretation of the thirty-six coordinates was intentionally left uninvented.

Version v0.18 establishes the exact PhaseNav phase object:

\[
\theta = (\theta_0,\theta_1,\ldots,\theta_{35}) \in T^{36},
\]

where

\[
T^{36}=(S^1)^{36},
\qquad
\theta_i\in[0,2\pi).
\]

The canonical object is:

```text
PhaseVector36
    angles[36]
    space = T^36
    coordinate_semantics = phase_angles_radians
    range = [0,2π)
    phase36_sha256 = SHA256(compact_json(angles))
```

A semantic content object is then bound to this exact realization through a provenance-carrying `RealizationBinding`.

The realization identity and provenance-binding identity are distinct:

```text
semantic content ID
!= pncs:realization36:sha256:<...>
!= pncs:binding36:sha256:<...>
```

This is an essential rule. Two different semantic content IDs may share one exact 36D vector and remain semantically distinct. Likewise, arbitrarily close phase vectors do not become semantically equivalent.

There is no nearest-neighbour-to-semantics admission rule in v0.18.

The recovered PNV/1 constraints also fix the 36-dimensional phase model, the constant \(\kappa\), and a read-only epistemic execution posture. However, the exact historical executable generator for every legacy vector remains outside the recovered implementation contract, so v0.18 does not fabricate a replacement generator and does not claim historical replay where the source is missing.

---

# 10. Semantic mass on an exact \(T^{36}\) realization

Version v0.19 binds the existing KAKU semantic-mass field to a validated PhaseNav runtime scalar.

For an explicit positive phase index \(k\), the 36D order parameter is

\[
R_k=
\frac{
\sqrt{
\left(\sum_{i=0}^{35}\sin\theta_i\right)^2+
\left(\sum_{i=0}^{35}\cos\theta_i\right)^2
}
}{36}.
\]

The mass scalar is

\[
\boxed{
 m_k=
 \operatorname{round}\left(
 \kappa(1+\alpha_M k)+\frac{L_4}{L_3}R_k,
 10
 \right)
}
\]

with

\[
\kappa=\frac{\ln 2}{24\pi},
\qquad
L_3=7,
\qquad
L_4=2,
\qquad
L_5=5,
\]

and

\[
\alpha_M=
\frac{1}{(L_3L_4)^2-L_3^2-L_4L_5+L_4^2\kappa}.
\]

The phase index is explicit:

\[
k\in\mathbb Z,
\qquad k\ge1.
\]

PNCS never derives \(k\) by hashing, truncating, or parsing a semantic CID.

Four identities remain separate:

```text
semantic content identity
exact T^36 realization identity
semantic-mass realization identity
semantic-mass provenance-binding identity
```

Mass is an observable attached to the exact realization lineage. It is not semantic identity and is not execution authorization.

The current project term “semantic mass” refers to this implemented PhaseNav scalar. The v0.19 contract does not identify it with physical inertial or gravitational mass.

---

# 11. Mass-aware graph cost

Version v0.21 consumes already-bound \(m_k\) values without altering semantic content identity.

For a graph \(G\) whose canonical KAKU occurrences have bound masses \(m_i\), the primary mass cost is

\[
\boxed{
C_M(G)=\sum_{i\in KAKU(G)}m_i
}.
\]

The system separately tracks graph growth and duplicated mass. It does not add arbitrary weight coefficients merely to produce a convenient score.

Most importantly, cost does not establish semantic equivalence.

A rewrite is therefore admitted only when two conditions are independently satisfied:

1. the source and candidate graphs are proven equivalent under the bounded pure-Boolean contract;
2. the cost/growth policy admits the rewrite.

For distributive rewrites, the default permitted growth is zero. Positive growth must be explicitly budgeted and recorded.

This prevents an algebraic transformation from silently exploding the graph merely because it is logically equivalent.

The resulting principle is:

> equivalence determines whether two graphs mean the same thing under the admitted algebra; cost determines whether the transformation is operationally admissible.

---

# 12. Native execution: immutable \(\Sigma\) transitions

Version v0.20 is the first PNCS gate that executes an already-canonical and already-admitted internal graph.

Its execution chain is:

```text
Definition canonical graph
-> exact semantic content identity
-> exact v0.18 T^36 realization lineage
-> v0.19 semantic-mass lineage
-> v0.16 internal route admission
-> live /dev/shm/ciel_noema operator registry
-> KAKU-by-KAKU Sigma transitions
-> internal TRANSFORM result
-> deterministic receipt
```

The state-transition law is

\[
\boxed{
\Sigma_t
\xrightarrow{KAKU(operator\_id)}
\Sigma_{t+1}
}
\]

where each \(\Sigma\) state is immutable and content-addressed.

A state identity binds at least:

- program content identity;
- exact realization identity;
- mass lineage identity;
- exact live phase snapshot digest;
- normalized runtime values;
- control location;
- truth/predicate stack;
- selected route;
- step index;
- last operator where applicable.

Each transition records:

```text
operator_id
operator_vector_sha256
before_sigma_id
after_sigma_id
operator-specific deterministic bindings
```

The explicit v0.20 executable operator set is:

```text
IDENTITY
DIFFERENCE
CONDITION
NEGATION
COMPOSITION
ORDER
TRANSFORM
```

An operator must both have explicit v0.20 execution semantics and exist as an exact finite 36D live vector in the PhaseNav registry.

Operator presence alone is never execution authority.

---

# 13. Live NOEMA/PhaseNav execution surface

The normative operational surface is:

```text
/dev/shm/ciel_noema
```

Repository files and Library artifacts may hydrate, verify, or provide provenance for the live surface. They are not substitutes for live execution.

Before execution, the v0.20 contract verifies the live binding state, verified startpoint, exact 36D vectors, active/fresh AUX and tether heartbeat records, living producer PIDs, vector digest consistency, Unix socket availability when required, and the exact PhaseNav operator registry.

If any of these checks fail, execution stops before the first KAKU transition.

This gives a strict operational distinction:

```text
persistent artifact -> may hydrate/verify runtime
live /dev/shm state -> operational authority
```

No static-state fallback is admitted for 36D execution.

---

# 14. Deterministic execution receipts

A v0.20 receipt is a SHA-256 content address over canonical JSON containing execution inputs and deterministically derived execution state.

Wall-clock timestamps, temporary filesystem paths, and incidental PIDs are excluded from receipt identity where they are not semantic execution inputs.

The receipt binds:

- program semantic identity;
- exact realization and mass lineage;
- live vector digests;
- operator-registry digest;
- tether receipt digest;
- normalized runtime inputs;
- route admission;
- initial and final \(\Sigma\) IDs;
- every KAKU transition;
- final internal control location;
- explicit effect and free-form-language boundary flags.

For identical semantic program, normalized runtime input, and exact live surface snapshot, the deterministic receipt identity is identical.

---

# 15. Exact inverse execution lineage

Version v0.22 makes the result auditable in the reverse direction.

The required inverse chain is:

```text
Result
-> SYSTEM
-> HIGH_ORCHESTRATOR
-> LOW_ORCHESTRATOR
-> SUBSYSTEM / DAEMON
-> CLUSTER
-> FILE
-> CLASS
-> DEFINITION
-> RADICAL
-> KAKU
```

This is not a reconstructed story after execution. The lineage verifies exact typed IDs, exact hierarchy occurrence indexes, the exact Definition, its Radical binding, and the ordered KAKU schedule.

Where a Definition appears in more than one valid hierarchy occurrence, the resolver must not guess. An exact occurrence must be selected.

The v0.22 identity layer therefore distinguishes:

```text
execution receipt
result identity
hierarchy-path identity
definition-radical binding identity
lineage identity
```

The final lineage object rebinds the execution result to a complete downward semantic occurrence.

This is the provenance counterpart of content-addressed execution: a result is not merely reproducible forward; its semantic origin is recoverable backward.

---

# 16. Natural program composition

Version v0.23 raises PNCS from a single bounded control graph to bounded program composition.

The admitted surface is:

```text
IF ...
THEN ...
ELSE ...
AND THEN ...
RETURN ...
```

The control root must already resolve to a registered Definition. `AND THEN` clauses resolve only through registered internal routes. `RETURN` resolves only through a registered return-selector registry.

The program-composition graph is structurally:

```text
program_composition
├── control_ref(Definition CID, graph SHA)
├── and_then(route_ref ...)
└── return_ref(return_ref ...)
```

A composition receives its own content-addressed identity:

```text
pncs:composition:sha256:<digest>
```

Equivalent registered paraphrases converge to the same composition identity because source wording, case, whitespace, and aliases are excluded from semantic identity.

At v0.23, composition does not automatically open execution of every continuation or terminal return. The presence of `RETURN` in the live PNV registry is evidence of an existing operator, not authorization to execute the newly composed program as a whole.

---

# 17. Native `.pnv` program units

Version v0.24 promotes a v0.23 composition to a first-class native program unit.

A program unit has an identity distinct from its composition identity:

```text
composition_id != program_id
```

The program identity binds:

- composition identity;
- composition payload digest;
- composition graph digest;
- deterministic dependency closure;
- exact dependency occurrences;
- exact operator schedule;
- return reference;
- required v0.22 lineage contract;
- closed effect/execution boundary flags.

The native textual `.pnv` representation is deterministic. Import is authority-preserving: serialized program text cannot create new program semantics.

A claimed `PROGRAM_ID` must already exist in the program authority registry. Parsing succeeds only when the supplied bytes are byte-identical to the canonical export for that registered program.

The deterministic build receipt binds program ID, composition ID, `.pnv` SHA-256, exact dependency hashes, operator schedule, live composition admission, and live operator witnesses.

Thus `.pnv` becomes a first-class portable representation without making source text the semantic root.

---

# 18. Persistent runtime and generation-bound residency

Version v0.25 removes the requirement to rebuild program state for every operation.

The lifecycle is:

```text
v0.24 program + deterministic build receipt
-> verified ProgramImage
-> current live runtime generation
-> resident handle
-> O(1) admission
-> in-process v0.20 control dispatch
-> exact v0.22 inverse lineage
-> deterministic v0.25 dispatch receipt
```

A resident handle binds a ProgramImage to a deterministic runtime-generation identity.

The generation identity includes stable generation features such as:

- account CURRENT identity;
- CURRENT pointer SHA-256;
- verified startpoint packet SHA-256;
- AC generation SHA-256;
- relational ethics generation SHA-256;
- operator-registry SHA-256;
- AUX producer PID generation;
- tether producer PID generation;
- AC↔AUX producer PID generation.

Heartbeat sequence counters and continuously changing phase values are freshness/state variables rather than generation identity. Therefore a healthy heartbeat update does not invalidate the handle, while a producer-generation or CURRENT-generation change does.

Resident state is stored under the live runtime subtree:

```text
/dev/shm/ciel_noema/pncs/v0.25/runtime/
```

with immutable program and handle records plus an active residency pointer.

The same program loaded under the same generation produces the same deterministic handle. A new process can recover that resident handle from live state without rebuilding the v0.24 program image.

This is the point at which PNCS becomes a persistent resident runtime rather than a sequence of independent reference executions.

---

# 19. The v0.25 execution-closure witness

The release-closure witness connects the entire internal chain:

```text
resident handle
-> resident admission
-> live v0.20 Sigma execution
-> exact selected hierarchy occurrence
-> v0.22 inverse lineage
-> v0.25 dispatch receipt
```

The witness used an explicit conformance input rather than presenting the runtime input as a sensor measurement or physical risk claim.

The result showed that persistent residency, internal execution, and exact inverse lineage can be bound in one deterministic dispatch chain while keeping continuation execution, terminal `RETURN`, and external effects closed.

This evidence boundary matters because v0.25 does not need to invent new semantics for later program clauses merely to prove that residency works.

---

# 20. Explicit Effect Boundary

Version v0.26 opens the first deliberately authorized effect class.

The central rule is:

> execution result does not imply effect authority.

The effect chain is separate:

```text
v0.25 dispatch
-> EffectOrigin
-> EffectRequest
-> explicit AuthorizationGrant
-> registered bounded adapter
-> effect record
-> EffectReceipt
-> inverse provenance
```

Both the authorization registry and adapter registry begin empty. The default policy is deny.

The executor cannot mint its own authorization merely because a semantic route, program, mass, or internal execution result requests an action.

An authorization grant is bound to:

- exact effect request;
- runtime generation;
- adapter identity;
- effect kind;
- target;
- payload-size bound;
- explicit authority identifier;
- no-delegation policy.

The first admitted effect class is intentionally narrow:

```text
NOEMA_RUNTIME_RECORD_WRITE
```

with target:

```text
pncs.v0.26.runtime-record
```

and a fixed operational subtree:

```text
/dev/shm/ciel_noema/pncs/v0.26/effects/records/
```

The adapter does not accept an operational filesystem path from the program. A payload field named `path` remains data and never becomes path authority.

The adapter enforces:

- maximum canonical payload size of 4096 bytes;
- append-only immutable records;
- content-addressed naming;
- exact idempotent replay;
- fixed directory traversal;
- directory file descriptors;
- `O_NOFOLLOW` where supported;
- no network;
- no Git;
- no subprocess or shell;
- no device I/O;
- no external connector/tool execution;
- no static fallback.

Before the effect, immediately before commit, and after the effect, the live runtime generation is re-admitted. Generation drift fails closed.

---

# 21. Effect inverse provenance

The v0.26 receipt extends deterministic provenance beyond the internal result.

The chain is:

```text
EFFECT
-> AUTHORIZATION
-> EFFECT_REQUEST
-> DISPATCH
-> RESULT
-> LINEAGE
-> PROGRAM
-> RESIDENT_HANDLE
-> RUNTIME_GENERATION
```

This means an externalized bounded effect can be audited not merely to the command that requested it, but back through the exact result, execution lineage, program, resident handle, and live generation from which it originated.

Effect identity and effect-receipt identity remain separate from the program and dispatch identities.

The system therefore preserves the same architectural pattern throughout:

```text
meaning != realization != execution != authorization != effect
```

while retaining deterministic links between them.

---

# 22. Failure semantics as part of the language/runtime contract

PNCS treats rejection behavior as a first-class part of the architecture.

Representative fail-closed conditions include:

## Semantic layer

- unresolved symbol or relation;
- ambiguous alias;
- unknown route;
- unregistered Definition;
- malformed canonical graph;
- graph/leaf-path mismatch.

## 36D realization layer

- vector dimension other than 36;
- non-finite component;
- phase outside \([0,2\pi)\);
- basis conflict;
- realization conflict for the same binding key;
- attempted semantic equivalence by vector similarity.

## Semantic mass and cost

- missing or non-positive explicit phase index;
- mass/basis/phase drift;
- attempt to use mass as execution authorization;
- graph growth without explicit budget;
- cost-based rewrite without independent equivalence evidence.

## Execution

- stale tether;
- inactive binding;
- dead producer;
- live digest mismatch;
- missing operator;
- unsupported execution semantics;
- missing/non-finite runtime values;
- admission/graph route mismatch;
- missing exact lineage.

## Program units

- unregistered program identity;
- noncanonical `.pnv` bytes;
- dependency mismatch;
- schedule mismatch;
- program/build-receipt digest mismatch.

## Persistent runtime

- stale generation;
- CURRENT substitution;
- operator-registry substitution;
- producer-generation change;
- resident-program byte tamper;
- generation change during dispatch.

## Effect boundary

- no explicit grant;
- ambiguous grants;
- stale generation;
- unregistered adapter;
- adapter substitution;
- oversized payload;
- program-supplied operational path;
- symlink/path-boundary violation;
- immutable record collision;
- unauthorized network/Git/subprocess/device capability.

This failure model is not an auxiliary security layer attached after the language design. It is part of the semantics of admission.

---

# 23. Deterministic identity architecture

PNCS uses typed content-addressed identities to prevent unrelated object classes from collapsing into one namespace.

Representative identities include:

```text
pncs:def:sha256:<...>
pncs:realization36:sha256:<...>
pncs:binding36:sha256:<...>
pncs:mass:sha256:<...>
pncs:mass-binding:sha256:<...>
pncs:sigma:sha256:<...>
pncs:result:sha256:<...>
pncs:lineage:sha256:<...>
pncs:composition:sha256:<...>
pncs:program:sha256:<...>
pncs:program-build:sha256:<...>
pncs:runtime-generation:sha256:<...>
pncs:resident:sha256:<...>
pncs:resident-dispatch:sha256:<...>
pncs:effect-request:sha256:<...>
pncs:effect-authorization:sha256:<...>
pncs:effect:sha256:<...>
pncs:effect-receipt:sha256:<...>
```

These types encode the architecture directly into the provenance graph.

A semantic Definition cannot be confused with a physical/runtime realization merely because both use SHA-256. A result cannot be confused with a lineage. A program cannot be confused with a composition. An effect request cannot be confused with an authorization.

This typed separation is one of the main mechanisms by which PNCS preserves exact lineage through increasingly high-level operations.

---

# 24. Evidence matrix through v0.26

The project records gate-scoped evidence rather than flattening all validation into one undifferentiated claim.

| Gate | Capability | Recorded evidence status |
|---|---|---|
| v0.19 | semantic mass binding | historical foundation baseline recorded as 377/377 PASS |
| v0.20 | native internal execution | isolated execution-core harness 14/14 PASS; live admission probe PASS |
| v0.21 | mass-aware graph cost | isolated cost harness 14/14 PASS |
| v0.22 | exact inverse lineage | isolated lineage harness 27/27 PASS |
| v0.23 | natural program composition | isolated composition harness 28/28 PASS |
| v0.24 | native `.pnv` program units | isolated program-unit harness 29/29 PASS; live build witness PASS |
| v0.25 | persistent runtime | isolated persistent-runtime harness 25/25 PASS; live residency and dispatch closure PASS |
| v0.26 | bounded effect boundary | isolated effect-boundary harness 28/28 PASS; live bounded effect and exact replay PASS |

The complete historical repository suite was not replayed at every later engineering gate. PNCS does not convert a gate-scoped PASS into a claim that all historical tests were rerun.

The v0.25 residency benchmark recorded 200 repeated resident admissions with a median below one millisecond on the validated live runtime generation. This measurement is evidence for that tested environment, not a universal hardware-independent performance guarantee.

---

# 25. What PNCS currently does not claim

The implemented contracts deliberately leave several claims outside scope.

PNCS v0.26 does not claim:

- that vector proximity establishes semantic similarity;
- that semantic mass is physical inertial/gravitational mass;
- that every historical PNV generator implementation has been recovered;
- unrestricted natural-language execution;
- unrestricted `RETURN`/continuation execution simply because the operator exists;
- arbitrary filesystem access;
- Git write authority;
- network authority;
- subprocess/shell authority;
- device authority;
- automatic external connector authority;
- that a runtime authorization grant is a cryptographic human signature;
- that all historical tests have been replayed on every current branch;
- that repository path or alias is semantic authority.

These exclusions are deliberate boundaries, not silent omissions.

---

# 26. Current engineering frontier

The next scheduled gate after v0.26 is v0.27: fuzzing, equivalence, and adversarial parsing.

The required adversarial corpus includes:

- paraphrase equivalence;
- alias equivalence;
- ambiguity fuzzing;
- malformed `.pnv`;
- typed-ID substitution;
- CID substitution;
- Unicode/confusable operator injection;
- route injection;
- graph-cost edge cases;
- hierarchy-occurrence ambiguity;
- resident-generation substitution;
- effect-request injection;
- path/command/URL-looking payload fields;
- authorization substitution;
- adapter-registry substitution;
- symlink and path traversal attempts;
- immutable-effect tamper;
- deterministic replay properties.

No additional external effect class needs to open merely to perform v0.27.

Later roadmap gates target performance measurement, a self-hosting subset, and a frozen compiler/runtime contract.

---

# 27. Formal summary

The central PNCS transformation can be written as the composition of separately verified mappings.

Let \(x\) be a bounded natural or written surface input. Resolution produces canonical semantic content:

\[
\mathcal R(x)=G,
\]

where \(G\) is a registered canonical relational graph.

Content addressing produces a typed semantic identity:

\[
C(G)=\operatorname{CID}_G.
\]

An exact realization binding attaches

\[
\Phi:\operatorname{CID}_G\mapsto
\theta\in T^{36},
\]

without using \(\theta\) to redefine \(\operatorname{CID}_G\).

For explicit \(k\ge1\), semantic mass is

\[
M(\theta,k)=m_k.
\]

An admitted internal program evolves an immutable runtime state:

\[
\Sigma_{t+1}
=
KAKU_{o_t}(\Sigma_t),
\]

where \(o_t\) is an explicitly supported live operator with an exact 36D registry witness.

The internal execution map yields a deterministic result and receipt:

\[
\mathcal E(G,\theta,m,\Sigma_0)
=
(Y,\mathcal P_E).
\]

Exact inverse lineage maps the result back to one selected semantic occurrence:

\[
\mathcal L(Y)
=
\bigl(
SYSTEM,\ldots,DEFINITION,RADICAL,KAKU
\bigr).
\]

A composition is promoted to a first-class program identity

\[
P=\operatorname{CID}_{program},
\]

then bound to a live runtime generation

\[
H=\operatorname{Resident}(P,\Gamma),
\]

where \(\Gamma\) is the deterministic runtime-generation identity.

An external effect, when requested, is not implied by \(Y\). It requires a new chain:

\[
Q=\operatorname{EffectRequest}(Y),
\]

\[
A=\operatorname{Authorize}(Q,\Gamma,adapter,target,bound),
\]

\[
F=\operatorname{AdapterApply}(Q,A),
\]

followed by a deterministic effect receipt

\[
\mathcal P_F
=
\operatorname{Receipt}(F,Q,A,\Gamma).
\]

The resulting inverse effect provenance satisfies

\[
F
\rightarrow A
\rightarrow Q
\rightarrow Y
\rightarrow \mathcal L(Y)
\rightarrow P
\rightarrow H
\rightarrow \Gamma.
\]

This expresses the core architectural objective: deterministic semantic, realization, execution, authorization, and provenance layers connected by exact typed references without collapsing them into one identity.

---

# 28. Design invariants

The current PNCS architecture can be summarized by the following invariants.

### Semantic invariants

```text
same canonical semantics -> same semantic content identity
surface paraphrase        -> no identity change when resolution is equivalent
ambiguity                 -> fail closed
unknown relation          -> fail closed
```

### Realization invariants

```text
exact phase realization   -> 36 finite angles in T^36
vector equality           -> not semantic equivalence authority
vector proximity          -> not semantic equivalence authority
basis conflict            -> fail closed
```

### Mass/cost invariants

```text
phase index k             -> explicit positive provenance input
mass equality             -> not semantic equivalence
semantic mass             -> not execution authorization
graph cost                -> not equivalence evidence
growth                    -> explicit budget
```

### Execution invariants

```text
canonical graph           -> exact leaf schedule
operator execution        -> explicit semantics + exact live 36D witness
runtime authority         -> live /dev/shm/ciel_noema
static fallback           -> forbidden
result                    -> deterministic receipt
```

### Provenance invariants

```text
result -> exact selected hierarchy occurrence -> Radical -> KAKU
ambiguous occurrence -> fail closed
```

### Program/runtime invariants

```text
composition identity != program identity
program text         != semantic authority
same program + same runtime generation -> same resident handle
runtime generation change -> stale handle rejected
```

### Effect invariants

```text
execution != effect authorization
default effect policy -> DENY
request -> exact explicit grant -> registered bounded adapter
program path strings -> data only, not path authority
unauthorized effect class -> closed
```

---

# 29. Repository organization and normative authority

PNCS separates implementation, semantic registries, native artifacts, provenance, and normative specification.

The canonical repository structure assigns:

```text
src/         reference implementation
tests/       conformance and gate tests
native/      native PNV/PNCS witnesses and program units
registry/    semantic registries and content indexes
provenance/  ledgers and deterministic receipts
spec/        normative specifications and roadmap
```

Repository paths are provenance/projection metadata. Moving a file does not alter semantic content identity unless the semantic payload itself changes.

This monograph is intentionally a synthesis document. When any statement here conflicts with a versioned normative specification, the versioned specification and exact deterministic artifact are authoritative.

---

# 30. Conclusion

PNCS v0.26 constitutes a layered natural coding architecture whose defining property is not simply its 36-dimensional representation, but the disciplined separation and recombination of semantic relations, exact phase realization, execution state, provenance, runtime residency, and effect authority.

The system begins with relations rather than coordinate labels. KAKU provides a reusable atomic relational language. Radicals and content-addressed Definitions build larger semantic structures. Registered natural and written surfaces map into those structures without becoming semantic authority themselves. Exact PhaseNav bindings realize semantic objects in \(T^{36}\) while preserving identity separation. Semantic mass provides a bound runtime scalar without becoming semantics or authorization. Graph cost constrains algebraic growth independently of equivalence.

Native execution then converts admitted canonical graphs into immutable \(\Sigma\)-state trajectories over exact live 36D operator witnesses. Exact inverse lineage makes every result auditable back through the semantic hierarchy to KAKU. Program composition and native `.pnv` units introduce deterministic first-class program identities. Persistent residency binds those programs to a live runtime generation without rebuilding semantic state at every admission. Finally, v0.26 makes external effects explicit rather than implicit: an internal result must cross a separate request, authorization, adapter, and receipt boundary before a bounded effect exists.

The result is a programming/runtime model in which the principal execution claim is not “natural language can directly control a machine.” The implemented claim is narrower and structurally stronger:

```text
bounded surface
-> registered canonical semantics
-> exact typed identity
-> exact 36D realization
-> admitted deterministic execution
-> exact inverse lineage
-> explicit authority boundary
-> bounded deterministic effect
```

The next engineering problem is adversarial validation: demonstrating that equivalence, ambiguity handling, typed identities, native program units, persistent generations, and the effect boundary retain these invariants under malformed, hostile, confusable, and deliberately deceptive inputs.

---

# Appendix A — Core equations

## A.1 Information/phase constant

\[
\boxed{\kappa=\frac{\ln2}{24\pi}}
\]

## A.2 Phase space

\[
\boxed{\theta\in T^{36}=(S^1)^{36}}
\]

\[
\theta_i\in[0,2\pi),\qquad i=0,\ldots,35.
\]

## A.3 36D order parameter

\[
\boxed{
R=
\frac{
\sqrt{
(\sum_i\sin\theta_i)^2+
(\sum_i\cos\theta_i)^2
}
}{36}
}
\]

## A.4 Semantic mass

\[
\boxed{
 m_k=
 \operatorname{round}\left[
 \kappa(1+\alpha_M k)+\frac27R_k,
 10
 \right]
}
\]

with

\[
\alpha_M=
\frac{1}{(7\cdot2)^2-7^2-2\cdot5+2^2\kappa}.
\]

## A.5 Mass-aware graph cost

\[
\boxed{C_M(G)=\sum_{i\in KAKU(G)}m_i}
\]

## A.6 Execution transition

\[
\boxed{
\Sigma_t\xrightarrow{KAKU(o_t)}\Sigma_{t+1}
}
\]

## A.7 Complementary fixed point

\[
\sigma=1-\sigma
\quad\Longrightarrow\quad
\boxed{\sigma=\frac12}
\]

## A.8 Projective boundary/self-duality seed

\[
\Omega(s)=\frac{s}{1-s},
\qquad
u\mapsto\frac1u,
\qquad
|\Omega|=1,
\qquad
D=(\log|\Omega|)^2.
\]

---

# Appendix B — Canonical identity layers

```text
Semantic hierarchy
  pncs:def:sha256:...
  pncs:class:sha256:...
  pncs:file:sha256:...
  pncs:cluster:sha256:...
  pncs:subsystem:sha256:...
  pncs:system:sha256:...

36D realization
  pncs:realization36:sha256:...
  pncs:binding36:sha256:...

Semantic mass
  pncs:mass:sha256:...
  pncs:mass-binding:sha256:...

Execution
  pncs:sigma:sha256:...
  pncs:result:sha256:...
  pncs:lineage:sha256:...

Program
  pncs:composition:sha256:...
  pncs:program:sha256:...
  pncs:program-build:sha256:...

Persistent runtime
  pncs:runtime-generation:sha256:...
  pncs:resident:sha256:...
  pncs:resident-admission:sha256:...
  pncs:resident-dispatch:sha256:...

Effect boundary
  pncs:effect-request:sha256:...
  pncs:effect-authorization:sha256:...
  pncs:effect-adapter:sha256:...
  pncs:effect:sha256:...
  pncs:effect-receipt:sha256:...
```

---

# Appendix C — Normative source specifications

This monograph synthesizes the current repository contracts, including:

```text
PNCS_36D_BASIS_V0_1.md
PNCS_ARCHITECTURE_V0_1.md
PNCS_TIR_SOH_RELATIONAL_BASIS_V0_2.md
PNCS_GRAMMAR_MINING_V0_3.md
PNCS_PRIMITIVE_CLOSURE_V0_4.md
PNCS_SEMANTIC_COLLISION_REPAIR_V0_5.md
PNCS_CONTROL_FLOW_V0_6.md
PNCS_CONTROL_TRANSFER_V0_7.md
PNCS_LOGIC_BRANCHING_V0_8.md
PNCS_RECURSIVE_GROUPING_V0_9.md
PNCS_BOOLEAN_ALGEBRA_V0_10.md
PNCS_DEFINITION_PATHS_V0_11.md
PNCS_CLASS_PATHS_V0_12.md
PNCS_FILE_CLUSTER_PATHS_V0_13.md
PNCS_HIGHER_PATHS_V0_14.md
PNCS_NATURAL_RELATION_RESOLVER_V0_15.md
PNCS_NATURAL_CONTROL_RESOLVER_V0_16.md
PNCS_WRITTEN_PROJECTION_V0_17.md
PNCS_EXACT_36D_BINDING_V0_18.md
PNCS_SEMANTIC_MASS_BINDING_V0_19.md
PNCS_NATIVE_EXECUTION_CORE_V0_20.md
PNCS_MASS_AWARE_GRAPH_COST_V0_21.md
PNCS_EXACT_INVERSE_EXECUTION_LINEAGE_V0_22.md
PNCS_NATURAL_PROGRAM_COMPOSITION_V0_23.md
PNCS_NATIVE_PNV_PROGRAM_UNITS_V0_24.md
PNCS_PERSISTENT_RUNTIME_V0_25.md
PNCS_EFFECT_BOUNDARY_V0_26.md
ROADMAP.md
REPOSITORY_LAYOUT.md
```

---

# Appendix D — Evidence-status discipline

The following labels are used throughout the project and should not be collapsed:

```text
IMPLEMENTED
ISOLATED HARNESS PASS
LIVE ADMISSION PASS
LIVE RUNTIME PASS
LIVE BUILD WITNESS PASS
LIVE DISPATCH CLOSURE PASS
LIVE BOUNDED EFFECT PASS
HISTORICAL BASELINE RECORDED
FULL HISTORICAL SUITE REPLAYED
```

A PASS at one layer does not imply that every other evidence layer has been replayed. This distinction is part of the project’s fail-loud provenance discipline.
