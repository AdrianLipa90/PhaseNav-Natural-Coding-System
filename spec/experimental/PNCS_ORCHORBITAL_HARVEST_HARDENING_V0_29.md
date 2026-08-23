# PNCS OrchORbital Architecture Harvest Hardening v0.29

Status: **EXPERIMENTAL / HARDENING-PREP / NON-PROMOTING**  
Epistemic operator: `CHYBA`  
Mode: `READ_ONLY`

## Authority and source

The harvested architecture is pinned to:

```text
repository: AdrianLipa90/CIEL-Omega-ApokalypOS
commit: aa0da54ef29a1f80dd0390427935342225388950
```

Source contracts used by this hardening layer:

```text
02_ONTOLOGY_AND_OBSERVABLES.md
03_STATE_SPACE_AND_BOUNDARY_CONDITIONS.md
05_ENTITY_REGISTRY_AND_SPHERE_EMBEDDING.md
07_OORP_PIPELINE_AND_MEMORY.md
08_GEOMETRY_ENGINE_AND_UI_SURFACE.md
10_METRICS_VALIDATION_AND_EXPERIMENTS.md
11_IMPLEMENTATION_PHASES_AND_WORKPACKAGES.md
13_SPHERE_DYNAMICS_8PLUS1.md
CIEL_ETHICS_AND_SEMANTIC_ACTION_ALGORITHM.md
```

PNCS v0.22 exact inverse lineage, PNCS v0.19 semantic-mass binding, and PNCS v0.27 OrchORbital state remain their own source authorities.

## Hardening surface

The layer adds five deterministic read-only objects:

```text
exact PNCS lineage + explicit orbital metadata
-> EntityRecordProjection

schema receipt + tests receipt + metrics receipt + replay receipt
-> PackageAdmissionReceipt

explicit semantic-action measurements + explicit weights
-> SemanticActionAuditReceipt

holonomic defect
-> InertLeakReceipt

formal state + explicit chart coordinates
-> OperationalGeometryProjection
```

## EntityRecord projection

`EntityRecordProjection` preserves the upstream `canonical_id` and binds it to explicit orbital metadata plus exact v0.22 lineage references. Its own `projection_id` addresses the projection artifact only.

A semantic-mass value may be carried only together with an explicit `pncs:mass-binding:sha256:*` authority. Semantic-mass calculation authority remains the exact PNCS v0.19 binding contract.

Repeated KAKU occurrences remain valid because v0.22 lineage schedules may contain repeated exact KAKU occurrences.

Authority flags:

```text
identity_authority = false
routing_authority = false
effect_authority = false
```

## Package admission gate

The OrchORbital implementation rule is encoded as a four-slot gate:

```text
PACKAGE_ADMITTED
iff
SCHEMA_RECEIPT
and TEST_RECEIPT
and METRICS_RECEIPT
and REPLAY_RECEIPT
```

The check is O(1) after receipt resolution. Missing evidence produces a deterministic rejection receipt with the exact missing slots.

## Semantic-action audit

The measurement layer preserves the source separation between online structural action and artifact audit:

```text
S_online =
  w_L * L
+ w_phase * Delta_phase
+ w_rel * D_rel
+ w_truth_struct * Pi_truth_struct

Pi_truth_audit =
(false + unmarked + omit + hallucination) / fact_count

S_full = S_online + w_truth_audit * Pi_truth_audit
```

All weights are explicit receipt inputs. The coefficient names are independent of the fixed PNCS operator constant `κ = ln(2)/(24π)`.

Authority flags:

```text
measurement_only = true
routing_feedback_opened = false
effect_authority = false
```

## Inert leak receipt

For the complex holonomic defect

```text
Delta_H = Delta_real + i Delta_imag
```

the receipt records

```text
epsilon = -Delta_H
leak_amplitude = |epsilon|
leak_phase = arg(epsilon)
```

Zero defect is a valid typed receipt state with zero amplitude and deterministic zero phase.

Boundary state:

```text
propagation_opened = false
parent_mutation_opened = false
split_merge_elevate_opened = false
routing_feedback_opened = false
```

## Formal state to operational geometry

The projection contract keeps:

```text
base relational manifold: M_rel
geometric anchor: projective Hilbert / Kahler / Fubini-Study
Poincare: operational projection
Bloch: local reduced inspection
```

Poincare coordinates are admitted only inside the open unit disk. Bloch-local coordinates are admitted inside or on the unit ball.

Boundary state:

```text
semantic_identity_authority = false
routing_authority = false
renderer_authority = false
```

## Promotion boundary

This branch is hardening-prep. Promotion requires a closed v0.28 release foundation receipt plus a dedicated v0.29 admission decision.

Dynamic leak propagation, sphere split/merge/elevate, renderer implementation, Radical-to-sphere dynamic coupling, and 1024-ion-to-sphere dynamics remain quarantined tracks.
