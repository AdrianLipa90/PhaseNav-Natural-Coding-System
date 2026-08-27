# PNCS PNV Information Holonomy v0.1

Status: `EXECUTABLE_LAW_FRAME_IMPLEMENTED / HOLONOMY_AUDIT_IMPLEMENTED / INVERSE_LINEAGE_ATTACHED / LIVE_GREMLIN_HYDRATION_OPEN`

## Purpose

This contract turns the physical-law scaffold into an executable PNV object.

An admitted law frame is represented by a directed closed path

```text
law node -> transport -> law node -> ... -> starting law node
```

with law nodes materialized as exact PNCS KAKU candidates, the frame topology materialized as one RADICAL candidate, and each information transport materialized as a native PNV `TRANSFORM` OPERATOR candidate.

The resulting program measures information holonomy rather than relying on document-level consistency alone.

## Mathematical object

For a closed ordered path

```math
\gamma:\;v_0\to v_1\to\cdots\to v_{n-1}\to v_0
```

with transport maps \(T_i:v_i\to v_{i+1}\), define

```math
\mathcal H_\gamma
= T_{n-1}\circ\cdots\circ T_1\circ T_0.
```

For initial information state \(I\), the state holonomy defect is

```math
\Delta_\gamma
= d\!\left(I,\mathcal H_\gamma(I)\right).
```

The audit receives an explicit metric \(d\) and tolerance. A zero-tolerance exact control loop passes its state gate when

```math
\Delta_\gamma=0.
```

Tolerance-controlled loops pass when

```math
\Delta_\gamma\le \varepsilon_\gamma.
```

## Physical-law frame

A law-frame node is:

```text
LawFrameNode(
  law_id,
  domain,
  Kaku,
  evidence_refs
)
```

`domain` identifies the source formalism/repository/sector, for example `IDT`, `RFC`, `TIR`, `NOETHER`, or another admitted frame namespace.

The law frame supports:

- local self-loops,
- local multi-node loops inside one domain,
- cross-domain loops such as IDT ↔ RFC,
- larger closed paths through several admitted physical-law gates.

All KAKU nodes in one compiled loop share one exact PNCS basis.

## Closed transport topology

An ordered transport is:

```text
LawTransport(
  edge_id,
  source_node_id,
  target_node_id,
  transform_name,
  evidence_refs
)
```

For ordered nodes \(v_0,\ldots,v_{n-1}\), transport \(i\) is required to bind

```text
v_i -> v_(i+1 mod n)
```

and the number of transports equals the number of nodes.

A one-node loop therefore has the exact topology

```text
v_0 -> v_0
```

with one admitted transform.

## PNV lowering

Compilation produces a native PNV1 candidate program:

```text
PNV 1
EPISTEMIC CHYBA
MODE READ_ONLY
OP HOL.START SOURCE holonomy.input
OP HOL.EDGE.000 TRANSFORM HOL.START <T0>
...
OP HOL.EDGE.NNN TRANSFORM HOL.EDGE.<NNN-1> <TN>
OP HOL.RETURN RETURN HOL.EDGE.NNN
EMIT HOL.RETURN
```

Only the already admitted native PNV vocabulary is used. Transport semantics are injected explicitly through the native executor transform registry.

The execution effect boundary remains pure:

```text
external_effects = false
```

## Candidate graph

Every law node is written as a content-addressed KAKU candidate.

The RADICAL records the closed law-frame topology with relations:

```text
LAW_TRANSPORT:<transform_name>
```

Every `HOL.EDGE.*` OPERATOR binds the same RADICAL candidate and records the transport evidence.

The compilation receipt binds:

- ordered law-frame nodes,
- domains,
- KAKU candidate IDs,
- RADICAL candidate ID,
- OPERATOR candidate IDs,
- ordered transport plan,
- declared invariants,
- PNV source SHA-256,
- PNV graph SHA-256.

Compilation remains under:

```text
EPISTEMIC CHYBA
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
```

## Invariant audit

A loop may declare independent invariants:

```text
HolonomyInvariant(
  invariant_id,
  mode,
  tolerance
)
```

v0.1 admits two defect modes:

```text
EXACT
ABS
```

For invariant observable \(F_j\), the audit evaluates every execution stage

```math
F_j(I_0),\;F_j(I_1),\;\ldots,\;F_j(I_n)
```

and records the largest defect from the initial value:

```math
\Delta_{\gamma,j}^{\max}
=\max_k d_j\!\left(F_j(I_0),F_j(I_k)\right).
```

This separates final loop closure from intermediate invariant preservation. A loop can therefore return to the initial state while still exposing an invariant defect at an intermediate law gate.

The audit status is `PASS` when both conditions hold:

```math
\Delta_\gamma\le\varepsilon_\gamma
```

and, for every declared invariant \(j\),

```math
\Delta_{\gamma,j}^{\max}\le\varepsilon_j.
```

Otherwise the audit receipt records `FAIL` while the candidate remains `CANDIDATE_ONLY`.

## Metrics

v0.1 provides two reference metrics:

```text
exact_state_metric
numeric_linf_metric
```

`exact_state_metric` compares canonical serialized state bytes.

For finite numeric scalar/vector state,

```math
d_\infty(x,y)=\max_i|x_i-y_i|.
```

Custom metrics are explicit callables and carry an explicit `metric_id` in the receipt.

## Inverse provenance

Every completed holonomy audit invokes

```text
PNCS_GREMLIN_CANDIDATE_INVERSE_LINEAGE_V0_1
```

and binds:

```text
inverse_lineage_id
inverse_lineage_receipt_sha256
```

The measured defect can therefore be traced backward:

```text
HOLONOMY RESULT
  -> HOL.RETURN
  -> HOL.EDGE.* OPERATOR candidates
  -> RADICAL
  -> law KAKU candidates
  -> explicit content IDs / evidence refs
```

This is the provenance path required for later IDT/RFC/TIR law-frame receipts.

## First physical-law loops

The contract is suitable for exact control loops such as:

```text
Q_a
  -> p_a = Q_a / Q_total
  -> Q'_a = Q_total p_a
  -> Q_a
```

conditional discrete carrier loops:

```text
Q_a
  -> n_a = Q_a / q0
  -> Q'_a = q0 n_a
  -> Q_a
```

and conditional energy-density loops:

```text
j_Q
  -> rho_Q = (epsilon_Q / c^2) j_Q
  -> j'_Q = (c^2 / epsilon_Q) rho_Q
  -> j_Q.
```

These loops can be local to one formalism or span IDT/RFC law nodes. OPEN physical bindings remain explicit loop gates rather than being silently promoted by the holonomy engine.

## Information-holonomy receipt

The audit receipt schema is:

```text
PNCS_PNV_INFORMATION_HOLONOMY_AUDIT_RECEIPT_V0_1
```

and records:

```text
loop_id
compilation_receipt_sha256
native_execution_receipt_sha256
inverse_lineage_id
inverse_lineage_receipt_sha256
metric_id
state_tolerance
state_defect
invariant_results
status
epistemic
promotion_state
external_effects
```

The receipt itself is content-addressed by SHA-256.

## Persistence

Repository/conformance persistence stores:

```text
<authoring_root>/holonomy/<receipt_sha256>.json
```

with idempotent content-addressed writes.

The unified GREMLIN ↔ PNV bridge exposes live wrappers:

```text
compile_information_holonomy_loop_live()
persist_information_holonomy_audit_live()
```

which resolve a `GremlinPNVAuthoringSession` before using the canonical live authoring root.

Operational live persistence remains gated by the hydrated GREMLIN state witness under:

```text
/dev/shm/ciel_noema/gremlin
```

## Fail-closed gates

The v0.1 law-frame audit rejects malformed or incomplete objects at the following boundaries:

- empty law frame,
- duplicate law-node identities,
- mixed PNCS basis,
- transport-count/topology mismatch,
- duplicate invariant identity,
- missing admitted transform,
- missing invariant evaluator,
- invalid/non-finite metric defect,
- invalid invariant defect,
- compilation/loop receipt mismatch,
- inverse-lineage provenance mismatch,
- content-addressed audit collision.

## Architecture

The resulting PNCS architecture is:

```text
GREMLIN
  -> relational candidate discovery
  -> exact KAKU resolution
  -> RADICAL / OPERATOR authoring
  -> PNV law-frame execution
  -> information-holonomy audit
  -> inverse lineage
  -> admission / physical-law gate
```

This implements the physical-law scaffold as an executable connection with measurable holonomy rather than a document-only dependency graph.
