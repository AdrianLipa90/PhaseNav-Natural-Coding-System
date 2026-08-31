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
dt > 0
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

using the parent v0.33 bounded-control law exactly.

`u_max`, `tolerance_rad`, and `dt` enter through positive finite `numbers.Real` admission with boolean values excluded. `max_ticks` and `settle_consecutive` enter through positive integer admission with boolean values excluded. Numeric conversion to the parent float/int representation occurs only after the corresponding exact type gate.

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

and takes the control bound from the explicit admitted `u_max` input. `B`, `N`, `A_R`, `Q_BNA`, semantic value, orbital band and semantic mass remain recorded semantic/source coordinates under their own typed provenance.

## 5. Exact checks

The reference gate validates:

1. the same explicit lane profile as the v0.32 bridge;
2. identical semantic target construction;
3. identical semantic frequency binding into the derived snapshot;
4. exact-real positive finite admission for `u_max`, `tolerance_rad`, and `dt`;
5. exact-integer positive admission for tick/settling limits;
6. `settle_consecutive <= max_ticks`;
7. parent v0.33 bounded control remains within `u_max`;
8. PASS and timeout statuses remain distinct;
9. source snapshot remains unchanged;
10. semantic provenance and finite-control provenance both enter the deterministic receipt;
11. candidate-only authority is preserved.

Reference implementation: `src/phasenav_natural_code/semantic_orbital_htri_bounded_v01.py`.
Reference tests: `tests/test_semantic_orbital_htri_bounded_v01.py`.
