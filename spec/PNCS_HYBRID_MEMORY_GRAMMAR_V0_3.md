# PNCS Hybrid Memory Grammar v0.3

Status: `CANDIDATE_ONLY / MEMORY-ONTOLOGY-INFORMED / FAIL_CLOSED`

## Core change

v0.2 treated a program primarily as a typed semantic DAG. v0.3 adds a
history-bearing layer whose state can modify the future transition policy of
that DAG.

The governing distinction is:

\[
Z_t=(X_t,M_t)
\]

where \(X_t\) is active execution state and \(M_t\) is persistent
history-bearing structure.

The imported candidate memory law is:

> Memory is a persistent, history-dependent modification of a system's
> transition structure that causally changes its future reachable trajectories.

Therefore PNCS memory is not defined as a file, variable, record, or recall API.

## Ontological chain

v0.3 exposes the Memory-Ontology chain directly:

\[
EVENT \rightarrow TRACE \rightarrow PATH \rightarrow STRUCTURE \rightarrow LAW.
\]

- `EVENT` binds a program occurrence to a semantic event.
- `TRACE` requests a history-dependent memory update.
- `ROUTE` defines a traversed execution path.
- `MEMORY` declares the persistent structure.
- `LAW` binds the update operator governing that structure.

## Memory declaration

Example:

```text
MEMORY search_skill
  RETAINS PATH TOPOLOGY OPERATOR
  PERSISTENCE STRUCTURAL
  ACCESS IMPLICIT RECONSTRUCTIVE
  PLASTICITY ADAPTIVE CONSOLIDATING
  EFFECT ROUTING ATTRACTOR
  EPISTEMIC FORMAL_EXAMPLE
```

The declaration mirrors Memory-Ontology v0.1:

\[
M=(Q,\tau,A,P,E,C),
\]

with coupling \(C\) represented by explicit `COUPLE` operations.

## Procedural memory

A procedure is not stored as a symbolic recipe by definition. A procedural
memory may be a metastable reusable path/topology/operator structure.

Example:

```text
ROUTE search_route : find.pages filter.verified compute.ranked
REINFORCE search_route INTO search_skill MODE ADAPTIVE LAW search_learning
GUIDE compute.ranked USING search_skill
```

This represents the loop:

\[
\text{traversal}
\rightarrow
\text{trace}
\rightarrow
\text{path reinforcement}
\rightarrow
\text{changed future routing}.
\]

`GUIDE` is intentionally distinct from `RECALL`. An implicit memory can
change execution without exposing a record.

## Access and provenance

Direct retrieval and reconstruction are explicit:

```text
RECALL item : STATE FROM memory_x MODE DIRECT PROVENANCE RECALLED
RECALL route : PATH FROM memory_y MODE RECONSTRUCTIVE PROVENANCE RECONSTRUCTED
```

v0.3 does not permit `MODE IMPLICIT` in `RECALL`; implicit memory must affect
execution through `GUIDE`.

This prevents conflating memory object with access mode.

## Inter-layer coupling

```text
COUPLE fast_context TO search_skill MODE CONSOLIDATE TIMESCALE slow
COUPLE search_skill TO fast_context MODE REACTIVATE TIMESCALE fast
```

This represents the candidate coupled-layer law:

\[
\dot M_i=A_i+\sum_{j\ne i}C_{ij}B_{ij}.
\]

## Representation is orthogonal

A memory object declaration does not contain a representation family.

Representation is declared separately:

```text
REPRESENT search_skill AS QUANTUM_NATIVE
  EPSILON 0.001
  HORIZON 100
  OBSERVABLE trajectory_choice
  COST STORAGE UPDATE_TIME QUERY_TIME SAMPLE_COUNT SEQUENTIAL_DEPTH
  EVIDENCE FORMAL_ONLY
  PHYSICAL_QUANTUM FALSE
```

This preserves:

\[
\text{memory law}
\neq
\text{representation}
\neq
\text{physical substrate}.
\]

v0.3 deliberately rejects `PHYSICAL_QUANTUM TRUE`. Physical substrate
necessity is not a grammar-level inference.

## Persistence boundary

`TRACE`, `REINFORCE`, and `COUPLE` are semantic memory-transition requests.
They do not themselves write durable external storage.

A durable write still requires the explicit v0.2 capability boundary:

```text
PERSIST symbol AS slot REQUIRE storage_write
```

Thus:

\[
\text{memory semantics}\neq\text{storage actuation}.
\]

## Quantum path

v0.3 does not introduce another quantum IR.

The existing path remains:

```text
PNCS Hybrid Memory Grammar v0.3
  -> PNCS Hybrid Grammar v0.2
  -> Quantum Gate Language v0.1
  -> PHASENAV_QUANTUM_GATE_IR_V1
  -> causal-cone planning
  -> execution backend
```

Memory representation may be tagged `QUANTUM_NATIVE` without claiming a
physical QPU.

## Current non-claims

v0.3 does not yet provide:

- a durable memory runtime;
- automatic reinforcement weights from live execution receipts;
- decay/forgetting dynamics;
- operator-signature type inference for memory laws;
- proof that a representation is quantum-advantaged;
- physical quantum-memory necessity.

Those remain runtime/benchmark gates, not syntax claims.


## Operational memory gate

A runtime state is not promoted to a memory claim merely because it is stored
or survives a function call. The operational gate mirrors Memory-Ontology
v0.1 and requires all three properties:

1. **history encoding** — distinct prior trajectories can alter the current
   memory structure;
2. **persistence** — the alteration remains present for a non-zero relevant
   interval in the absence of a new trace;
3. **causal efficacy** — intervention on the memory state, while keeping the
   current condition fixed, changes a future reachable route or output.

For the candidate procedural runtime the control is expressed as:

```text
same current_condition_digest
+ factual history-conditioned memory
+ counterfactual intervention on memory only
-> compare selected future route
```

The exact-blob package gate on this branch passed 13/13 targeted tests. In the
10,000-feedback control, history changed route choice from `a` to `b`; a
counterfactual intervention on memory alone changed the choice back to `a`
without mutating factual memory. The receipt is:

`provenance/receipts/PNCS_MEMORY_GUIDED_PLANNER_PACKAGE_GATE_V0_3.json`

This is evidence for the candidate computational memory mechanism, not for a
physical quantum substrate or quantum advantage.

## Checkpoint boundary

A serialized checkpoint is a **representation of memory state and
provenance**, not the ontological definition of memory.

Therefore:

```text
MEMORY != CHECKPOINT
MEMORY != FILE
MEMORY != DATABASE_ROW
```

A checkpoint may encode the current route weights, counters, state digest and
append-only update receipts, but durable external persistence remains behind
the existing `PERSIST ... REQUIRE <capability>` boundary.

The intended next codec contract is:

```text
memory runtime
-> canonical state + provenance checkpoint
-> content digest
-> explicit PERSIST capability
-> durable store
-> verified restore
-> same future-routing behavior
```

Restore equivalence must preserve the task-relevant behavioral contract, not
only byte identity.

## Representation-aware planning — next gate

Memory-Ontology v0.1 keeps representation orthogonal to the memory object.
PNCS therefore must compare execution representations under a declared
behavioral equivalence contract before choosing among backends.

For a memory/program fragment, the planner target is:

```text
same observable contract
same epsilon
same horizon H
-> compare BINARY / HYBRID / QUANTUM_NATIVE resource vectors
```

with resource coordinates at least:

```text
storage
compile_time
update_time
query_time
sample_count
sequential_depth
```

A representation may be selected only after semantic equivalence is
established. A cheaper backend that violates the observable contract is not a
valid optimization.

This is the bridge from Memory-Ontology's binaryization frontier to PNCS
`MODE AUTO`.


## Operational runtime status — 2026-09-25

The candidate branch now includes executable in-memory runtime components:

- `procedural_memory_runtime_v03.py` — history-bearing route/path memory;
- `memory_guided_planner_v03.py` — implicit `GUIDE` affects future route selection;
- `memory_coupling_runtime_v03.py` — incremental `CONSOLIDATE` and non-mutating `REACTIVATE`.

Targeted package-layout tests:

```text
19 passed, 0 failed
```

Randomized Memory-Ontology gate:

```text
500/500 history encoding PASS
500/500 persistence PASS
500/500 causal intervention PASS
```

Randomized coupling gate:

```text
300/300 exact transfer PASS
300/300 duplicate-transfer prevention PASS
300/300 non-mutating reactivation PASS
```

The implementation therefore operationalizes, for this narrow synthetic
runtime, the loop:

```text
EVENT -> TRACE -> PATH update -> GUIDE -> future route
                    |
                    +-> CONSOLIDATE -> slower layer
                                      |
                                      +-> REACTIVATE -> active suggestion
```

This does not establish the universality of the Memory Ontology law, durable
memory persistence, physical quantum memory, or quantum advantage.
