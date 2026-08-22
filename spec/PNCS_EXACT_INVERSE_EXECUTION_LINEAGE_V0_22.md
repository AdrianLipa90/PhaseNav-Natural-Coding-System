# PNCS v0.22 — Exact Inverse Execution Lineage

Status: IMPLEMENTED / GATE-SCOPED VALIDATION

## 1. Scope

v0.22 binds every admitted v0.20 internal execution result to one exact content-addressed semantic origin and an exact Definition→Radical→KAKU witness.

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

The gate adds no new PNV opcode and does not authorize external effects.

## 2. Result identity

A v0.20 execution result is first verified against `PNCS_NATIVE_EXECUTION_RECEIPT_V0_20` and `PNCS_NATIVE_EXECUTION_CORE_V0_20`.

v0.22 recomputes the receipt SHA-256, verifies the final Sigma ID, result target, branch truth state, exact program provenance IDs, live-surface digest fields, and the v0.20 effect/free-form boundaries.

The execution trace must be a non-empty, continuous Sigma transition chain:

```text
Sigma_0 -> Sigma_1 -> ... -> Sigma_n
```

Every step must have the expected 1-based index, an admitted v0.20 internal operator, a 36D operator-vector SHA-256, and exact before/after Sigma IDs. The last step must terminate at the result final Sigma.

A deterministic result ID is then computed as:

```text
pncs:result:sha256:<digest>
```

from the verified receipt digest, final Sigma ID, Definition CID, branch truth state, and result payload.

## 3. Exact hierarchy occurrence

Content IDs can legitimately be reused in more than one ordered hierarchy position. Therefore a content ID alone does not identify an occurrence.

Every non-root hierarchy node stores its exact `child_index`. The root SYSTEM has `child_index = null`.

The admitted sequence is exactly:

```text
SYSTEM
-> HIGH_ORCHESTRATOR
-> LOW_ORCHESTRATOR
-> SUBSYSTEM | DAEMON
-> CLUSTER
-> FILE
-> CLASS
-> DEFINITION
```

For a requested `(SYSTEM CID, DEFINITION CID)`:

- zero occurrences: fail closed;
- exactly one occurrence: admit automatically;
- more than one occurrence: fail closed unless the caller supplies one exact candidate occurrence, including all child indexes;
- a forged or non-candidate selector: fail closed.

No alias, filesystem projection, deployment path, runtime location, or similarity search may resolve this ambiguity.

## 4. Definition receipt rebound

The Definition referenced by the execution receipt is reloaded from the Definition registry.

v0.22 requires:

```text
receipt.canonical_leaf_path == Definition.leaf_path
receipt.canonical_graph_sha256 == SHA256(Definition.canonical_graph)
```

when the Definition exposes the canonical graph. A correctly rehashed but semantically altered execution receipt still fails this check.

## 5. Definition → Radical → KAKU binding

The Definition is bound to one exact RadicalGraph and one ordered KAKU occurrence schedule.

The binding records:

- Definition CID;
- Radical ID;
- SHA-256 of the complete RadicalGraph payload;
- basis ID;
- ordered KAKU IDs;
- ordered operator IDs;
- SHA-256 of every exact KAKU payload.

The complete RadicalGraph digest covers every KAKU's:

```text
kaku_id
basis_id
vector36
semantic_mass
direction
polarity
role
phase36
```

plus all Radical relations.

The ordered KAKU role sequence must equal the Definition `leaf_path` exactly. Missing KAKU, hidden extra Radical KAKU, role substitution, or basis mismatch fails closed.

Repeated KAKU occurrences are allowed in the schedule when the Definition leaf path requires them; the Radical node set must still equal the schedule's exact KAKU set.

The deterministic binding ID is:

```text
pncs:def-radical-binding:sha256:<digest>
```

## 6. Complete lineage receipt

The final lineage receipt contains:

- deterministic result ID;
- exact v0.20 execution receipt SHA-256;
- content-addressed hierarchy occurrence path and child indexes;
- exact Definition→Radical binding ID and payload;
- complete inverse chain;
- explicit non-authority flags for aliases and runtime location;
- deterministic-only flag.

Its identity is:

```text
pncs:lineage:sha256:<digest>
```

## 7. Live operational boundary

Operational persistence is fixed to:

```text
/dev/shm/ciel_noema
```

Before writing a lineage receipt, v0.22 reuses the v0.20 live-surface verifier, including ACTIVE binding, VERIFIED session, exact 36D vectors, fresh heartbeats, producer liveness, Unix socket, and PhaseNav operator registry.

The persisted path is:

```text
/dev/shm/ciel_noema/pncs/v0.22/lineage/<lineage-digest>.json
```

A different operational root is rejected. There is no static runtime fallback.

## 8. Authority boundaries

v0.22 does not change semantic identity and does not infer hierarchy from a result payload.

```text
runtime_location_is_semantic_authority = false
aliases_are_semantic_authority = false
external_effects = false
semantic_mass_is_authorization = false
free_form_nl_execution = false
```

v0.22 also does not claim that a SHA-256 digest is a signature. The digest proves deterministic payload identity; the gate separately validates the frozen schema, contract, semantic registry links, and transition invariants.

## 9. Failure semantics

v0.22 fails closed for at least:

- unsupported or altered v0.20 receipt schema/contract;
- receipt digest mismatch;
- invalid program provenance IDs or phase digest;
- non-finite semantic mass;
- final Sigma/program mismatch;
- broken or empty Sigma transition trace;
- non-v0.20 internal operator in the trace;
- result kind other than `INTERNAL_TRANSFORM`;
- result target/truth-state mismatch;
- receipt not bound to `/dev/shm/ciel_noema`;
- effectful or free-form execution receipt;
- receipt Definition graph/leaf mismatch;
- missing requested SYSTEM or Definition content;
- invalid hierarchy child level;
- zero hierarchy occurrences;
- ambiguous hierarchy occurrence without exact selector;
- forged occurrence selector;
- missing/extra KAKU in Definition→Radical binding;
- KAKU role schedule different from Definition leaf path;
- Radical/KAKU basis mismatch;
- operational persistence outside the live NOEMA surface.

## 10. Validation evidence

Isolated v0.22 pure-core harness:

```text
27/27 PASS
```

The harness covers deterministic identity, unique and ambiguous hierarchy occurrences, explicit selection, forged selectors, Definition/Radical/KAKU schedule integrity, receipt and graph tampering, live-root boundary, execution contract/result-kind boundaries, and Sigma transition continuity.

A repository integration test is included using the real PNCS Definition, Class, File, Cluster and Higher Hierarchy registry implementations.

The complete historical repository suite has not been replayed in the isolated construction environment; no full-suite pass count is claimed by this gate receipt.

## 11. Next gate

v0.23 — Natural Program Composition.

Bounded registered program forms may compose only after v0.22 can deterministically recover the exact semantic origin of an execution result.
