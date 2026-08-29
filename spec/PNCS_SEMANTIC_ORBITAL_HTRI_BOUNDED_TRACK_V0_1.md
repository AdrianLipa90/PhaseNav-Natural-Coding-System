# PNCS Semantic Orbital -> Bounded HTRI Track v0.1

Status: `CANDIDATE / V0_33_BOUNDED_TRACK_REUSE / FINITE_ACTUATION_REACHABILITY`

## 1. Purpose

The exact v0.32 bridge shows how semantic orbital phase/frequency coordinates enter the existing 36D HTRI/QHTRI reference. This gate evaluates the same target under the finite-control v0.33 parent.

## 2. Composition

Given:

```text
source DriveSnapshot
semantic-orbital KAKU bindings
explicit SemanticHTRILaneProfile
u_max > 0
tolerance_rad > 0
max_ticks >= 1
settle_consecutive >= 1
```

v0.1 constructs the same:

```text
derived DriveSnapshot
target36
```

as `PNCS_SEMANTIC_ORBITAL_HTRI_BRIDGE_V0_1` and calls the existing

```text
semantic_htri_bounded_v33.track_target(...)
```

without changing the v0.33 bounded-control law.

## 3. Reachability result

The parent track receipt supplies the exact finite-actuation result

```text
PASS_TARGET_SETTLED
FAIL_TARGET_SETTLING_TIMEOUT
```

with `u_max`, tolerance, tick count, settling tick, residuals and saturation diagnostics.

The semantic bridge receipt adds explicit KAKU/content/lane/orbit provenance and the semantic carrier commitments that generated the target.

## 4. Actuation firewall

`u_max` is an independently typed control bound from PNCS v0.33.

The current gate records

```text
SEMANTIC_MAGNITUDE_TO_HTRI_ACTUATION = OPEN_SOURCE_BINDING
```

and does not infer `u_max` from `B`, `N`, `A_R`, `Q_BNA`, semantic value, orbital band or semantic mass.

## 5. Exact checks

The reference gate validates:

1. the same explicit lane profile as the v0.32 bridge;
2. identical semantic target construction;
3. identical semantic frequency binding into the derived snapshot;
4. positive finite `u_max` and tolerance;
5. positive tick/settling limits with `settle_consecutive <= max_ticks`;
6. parent v0.33 bounded control never exceeds `u_max`;
7. PASS and timeout statuses remain distinct;
8. source snapshot remains unchanged;
9. semantic provenance and finite-control provenance both enter the deterministic receipt;
10. candidate-only authority is preserved.

Reference implementation: `src/phasenav_natural_code/semantic_orbital_htri_bounded_v01.py`.
Reference tests: `tests/test_semantic_orbital_htri_bounded_v01.py`.
