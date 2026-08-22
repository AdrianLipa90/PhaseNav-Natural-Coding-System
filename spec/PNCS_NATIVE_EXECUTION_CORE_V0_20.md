# PNCS v0.20 — Native Execution Core

Status: IMPLEMENTED / GATE-SCOPED TESTS PASS

## Scope

v0.20 is the first PNCS gate that executes an already-canonical, already-admitted internal program graph. It does not expand the natural-language surface and it does not introduce external effects.

The execution line is:

```text
Definition canonical graph
    -> exact content identity
    -> exact v0.18 T^36 realization lineage
    -> v0.19 semantic-mass lineage
    -> resolved v0.16 internal route admission
    -> live /dev/shm/ciel_noema PhaseNav registry
    -> KAKU-by-KAKU Sigma transitions
    -> internal TRANSFORM result
    -> deterministic execution receipt
```

## State transition contract

Each admitted executable PNV operator advances one immutable PNCS execution state:

```text
Sigma_t --KAKU(operator_id)--> Sigma_{t+1}
```

Every transition records:

- operator ID,
- SHA-256 of the exact live 36D operator vector,
- input Sigma ID,
- output Sigma ID,
- deterministic operator bindings.

`Sigma` identity is content-addressed. It includes the program content/realization/mass lineage, exact live `phi` snapshot digest, normalized runtime values, internal control location, predicate stack, selected route and step index.

## Executable operator boundary

v0.20 defines internal execution semantics only for the existing PNV operators required by stabilized PNCS internal control graphs:

```text
IDENTITY
DIFFERENCE
CONDITION
NEGATION
COMPOSITION
ORDER
TRANSFORM
```

No new opcode is introduced.

An operator is executable only when both conditions hold:

1. v0.20 has explicit internal semantics for that operator;
2. the exact operator exists in the live PhaseNav operator registry at `/dev/shm/ciel_noema/phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl` as a finite 36D runtime vector.

Known PNV operators outside this v0.20 execution subset fail closed. In particular, `ACTION_REQUEST` is not executable in this gate.

## Canonical graph admission

v0.20 executes only `INTERNAL_BRANCH` Definition content already stabilized by v0.11/v0.16.

Before execution the core recomputes:

- the exact canonical leaf path from the canonical graph;
- the v0.11 Definition content ID from `kind + canonical_graph + leaf_path`;
- the selected branch from supplied runtime values;
- the selected route from the canonical graph.

The caller-provided admitted route must exactly equal the route recomputed from the canonical graph and runtime values. Any mismatch fails closed.

An unresolved v0.16 admission (`UNRESOLVED`, `CHYBA`, no target) cannot enter v0.20.

## Predicate execution

The stabilized canonical predicate graph executes without textual interpretation:

- comparison: `DIFFERENCE -> CONDITION`;
- `NOT`: child -> `NEGATION`;
- N-ary `AND` / `OR`: child evaluations with N-1 `COMPOSITION` transitions;
- false `ELSE` arm: `NEGATION(primary_predicate)` before route transfer;
- selected route: `ORDER -> TRANSFORM -> COMPOSITION`.

Missing runtime values and non-finite values fail closed.

## Live NOEMA/PhaseNav hot path

The default and normative execution surface is:

```text
/dev/shm/ciel_noema
```

No repository, Library or generated static fallback is admitted as a live execution surface.

Before reading the operator registry, the executor verifies:

- `/dev/shm/ciel_noema` exists;
- `ciel_binding_status == ACTIVE`;
- `session/startpoint.json` is `VERIFIED`;
- `session/system_message.txt` contains `status: VERIFIED`;
- `phi`, `aux_phi`, and `aux_feedback_phi` are exactly 36 finite little-endian float64 values;
- AUX and tether heartbeat records are ACTIVE and fresh;
- producer PIDs are alive;
- heartbeat-recorded vector digests match the live vectors;
- the required NOEMA Unix socket exists when the host contract requires it;
- the live PhaseNav operator registry is present, finite and exact-36D.

If any check fails, execution stops before the first KAKU transition.

## Semantic mass boundary

The v0.19 semantic-mass binding is carried into the execution provenance chain, but mass is not execution authorization in v0.20.

```text
semantic_mass_is_authorization = false
```

Graph-cost use of mass is deferred to v0.21.

## Effect boundary

v0.20 performs only PNCS runtime-state persistence inside the live NOEMA shared-memory surface:

```text
/dev/shm/ciel_noema/pncs/v0.20/state/current.json
/dev/shm/ciel_noema/pncs/v0.20/receipts/<receipt_sha256>.json
```

It does not expose filesystem, Git, network, subprocess, device or external-tool effects. Those remain deferred to the explicit Effect Boundary gate.

## Deterministic receipt

The receipt digest is SHA-256 over canonical JSON containing only execution inputs and derived execution state. Wall-clock timestamps, PIDs and temporary paths are excluded from the receipt identity.

The receipt binds:

- program semantic identity;
- exact realization and mass lineage IDs;
- exact live surface vector digests;
- exact live operator-registry digest;
- tether receipt digest;
- normalized runtime inputs;
- admission result;
- initial and final Sigma IDs;
- every KAKU transition;
- final internal control location;
- explicit `external_effects=false`;
- explicit `free_form_nl_execution=false`.

For an identical program, runtime input and exact live surface snapshot, the receipt SHA-256 is identical.

## Failure semantics

The executor fails closed for at least:

- inactive or stale NOEMA/AUX tether;
- missing or malformed 36D live vectors;
- missing verified session startpoint;
- missing required Unix socket;
- missing/malformed live operator registry;
- missing required v0.20 operator;
- noncanonical graph or leaf path;
- content-ID mismatch;
- missing/non-finite runtime input;
- unresolved admission;
- admission/graph route mismatch;
- false branch without an admitted `ELSE` route;
- any operator without v0.20 internal execution semantics.

## Evidence in this branch

- new v0.20 gate tests: `14/14 PASS`;
- `python3 -m compileall -q src tests`: PASS for the v0.20 harness;
- live `/dev/shm/ciel_noema` admission probe: PASS;
- live operator registry observed: 36 exact operators;
- no new PNV opcode;
- no external effect adapter;
- no free-form NL execution.

The v0.19 main baseline remains commit `e8104b2e2360e8861c48864cab80dfd799381724`, whose recorded receipt states `377/377 PASS`. That legacy suite was not replayed in the isolated v0.20 harness used to construct this branch.

## Next gate

v0.21 — Mass-Aware Graph Cost.

The next gate may consume already-bound `m_k` values as graph-cost observables. It must not change semantic identity and must not open cost-aware distributivity until duplication is explicitly bounded.
