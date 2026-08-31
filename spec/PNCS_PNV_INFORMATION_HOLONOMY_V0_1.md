# PNCS PNV Information Holonomy v0.1

Status: `EXECUTABLE_LAW_FRAME_IMPLEMENTED / HOLONOMY_AUDIT_IMPLEMENTED / INVERSE_LINEAGE_ATTACHED / CALLBACK_BOUNDARY_EXPLICIT`

## Purpose

This contract materializes an admitted physical-law frame as an executable closed PNV transport path. Law nodes are KAKU candidates, the closed topology is one RADICAL candidate, transports are PNV OPERATOR candidates, and the resulting audit measures state and invariant holonomy while preserving inverse provenance.

## Mathematical object

For

```math
\gamma:v_0\to v_1\to\cdots\to v_{n-1}\to v_0
```

with transport maps \(T_i\), define

```math
\mathcal H_\gamma=T_{n-1}\circ\cdots\circ T_0,
\qquad
\Delta_\gamma=d(I,\mathcal H_\gamma(I)).
```

The state gate passes when

```math
\Delta_\gamma\le\varepsilon_\gamma.
```

For every declared invariant \(F_j\), the audit records

```math
\Delta_{\gamma,j}^{\max}
=\max_k d_j(F_j(I_0),F_j(I_k))
```

and requires the declared invariant tolerance.

## Law-frame topology

A law node carries:

```text
law_id
domain
Kaku
evidence_refs
```

A transport carries:

```text
edge_id
source_node_id
target_node_id
transform_name
evidence_refs
```

For ordered nodes, transport `i` must bind `v_i -> v_(i+1 mod n)`. The number of transports equals the number of nodes. All KAKU nodes in one loop share one exact PNCS basis.

Identifiers and evidence references are normalized as non-empty strings. Duplicate node or invariant identities fail closed.

## PNV lowering

The compiler lowers the loop to:

```text
PNV 1
EPISTEMIC CHYBA
MODE READ_ONLY
OP HOL.START SOURCE holonomy.input
OP HOL.EDGE.000 TRANSFORM HOL.START <T0>
...
OP HOL.RETURN RETURN HOL.EDGE.NNN
EMIT HOL.RETURN
```

Transport semantics are explicit Python callbacks admitted through the native PNV transform registry.

## Effect-boundary accounting

The native interpreter separately proves that its own shell/subprocess/network/Git/device/arbitrary-filesystem boundary remains closed. The transform callbacks, state metric, and invariant evaluators are callable semantics outside that observable interpreter boundary.

Therefore a holonomy audit containing those callbacks records:

```text
external_effects = null
external_effects_status = UNVERIFIED_CALLBACK_BOUNDARY
callback_effects_verified = false
deterministic_fields_only = false
deterministic_serialization = true
callback_determinism_verified = false
```

The receipt also preserves:

```text
native_execution_external_effects
native_execution_external_effects_status
native_callbacks_invoked
audit_callbacks_invoked
```

This keeps the measured interpreter boundary and the unverified callback boundary separate in one content-addressed provenance object.

## Metrics

Reference metrics are:

```text
exact_state_metric
numeric_linf_metric
```

`exact_state_metric` compares the canonical finite JSON state domain. Tuple/list representations of the same JSON array therefore share one exact state identity.

For finite scalar or flat vector state:

```math
d_\infty(x,y)=\max_i|x_i-y_i|.
```

Subtraction overflow and non-finite defects fail closed. Custom metrics require an explicit non-empty `metric_id`.

Metric and invariant-evaluator exceptions are converted into controlled `PNVInformationHolonomyError` failures.

## Inverse provenance

Every completed audit invokes `PNCS_GREMLIN_CANDIDATE_INVERSE_LINEAGE_V0_1` and binds:

```text
native execution receipt
-> emitted OPERATOR root
-> dependent OPERATOR candidates
-> RADICAL
-> KAKU candidates
-> explicit content/evidence provenance
```

The inverse lineage preserves the native execution effect-boundary status. Callback uncertainty is therefore carried backward with the measured result rather than rewritten as a purity claim.

## Receipt

`PNCS_PNV_INFORMATION_HOLONOMY_AUDIT_RECEIPT_V0_1` records at least:

```text
loop_id
connection_id
connection_sha256
compilation_receipt_sha256
native_execution_receipt_sha256
inverse_lineage_id
inverse_lineage_receipt_sha256
metric_id
state_tolerance
state_defect
invariant_results
status
epistemic = CHYBA
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
effect_boundary
```

The receipt is SHA-256 content-addressed and can be persisted idempotently under `<authoring_root>/holonomy/`.

## Fail-closed gates

The audit rejects malformed law-frame objects, empty identifiers, duplicate identities, mixed PNCS basis, topology mismatch, missing transforms/evaluators, callback exceptions, non-finite or overflowing defects, compilation/loop mismatch, inverse-lineage mismatch, noncanonical receipt values, and content-addressed persistence collisions.

Operational live persistence remains bound to the admitted GREMLIN live authoring surface under `/dev/shm/ciel_noema/gremlin`. Compilation and audit remain `CHYBA / CANDIDATE_ONLY` with no automatic canon-write authority.
