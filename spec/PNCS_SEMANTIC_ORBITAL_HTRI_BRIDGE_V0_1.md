# PNCS Semantic Orbital -> HTRI Bridge v0.1

Status: `CANDIDATE / EXPLICIT_36D_LANE_BINDING / V0_32_DRIVE_REUSE / READ_ONLY_REFERENCE`

## 1. Purpose

This gate binds semantic-orbital KAKU carriers to the already implemented PNCS v0.32 HTRI/QHTRI controlled drive.

The parent semantic carrier is

\[
\mathcal S_a(t)=\frac{B_a(t)\omega_a(t)N_a(t)}{A_{R,a}(t)}(\phi_a(t)+\kappa).
\]

The HTRI parent already evolves 36 phase lanes with the v0.32 controlled Kuramoto/QHTRI reference. This bridge supplies explicit semantic lane targets and reuses that parent implementation.

## 2. Explicit lane assignment

A `SemanticHTRILaneProfile` contains

```text
lane_profile_id
kaku_to_lane[kaku_id] -> integer 0..35
frequency_binding = ASSIGN_SAMPLE_OMEGA | PRESERVE_SNAPSHOT_OMEGA
```

The mapping is explicit provenance. `lane_profile_id`, every `kaku_id`, and `frequency_binding` are admitted as exact non-empty Python strings. The lane map is admitted as an explicit mapping and copied into the profile snapshot. KAKU identifiers are normalized by surrounding-whitespace trimming, and normalized duplicate identifiers fail admission before lane assignment.

Lane values are exact integer values in `[0,35]`, with boolean values excluded from integer admission. v0.1 rejects lane collisions and rejects missing or extra KAKU mappings relative to the supplied semantic binding set.

For KAKU `a` assigned to lane `lambda(a)`, the phase target is

\[
\boxed{
\phi^*_{\lambda(a)}=\phi_a\pmod{2\pi}.
}
\]

Every unassigned lane retains the input snapshot phase exactly.

## 3. Frequency binding

Two explicit profiles are admitted.

### ASSIGN_SAMPLE_OMEGA

\[
\boxed{
\omega'_{\lambda(a)}=\omega_a.
}
\]

Every unassigned lane retains the input snapshot frequency exactly.

### PRESERVE_SNAPSHOT_OMEGA

The complete input `snapshot.omega` vector is retained.

The selected profile is part of the deterministic receipt. Frequency mode admission is exact-string typed before normalization to the declared uppercase mode identifier.

## 4. v0.32 composition

The bridge constructs a derived read-only `DriveSnapshot`:

```text
phi    = original snapshot phi
omega  = profile-bound omega
g      = unchanged copy from source snapshot
flavor = unchanged copy from source snapshot
tau    = unchanged copy from source snapshot
gravity = unchanged copy from source snapshot
source_id = content-addressed bridge identity
```

It separately constructs `target36` by replacing only the explicitly assigned phase lanes.

Then it calls the existing

```text
semantic_htri_drive_v32.controlled_step(derived_snapshot, target36, dt)
```

with `dt` admitted as a positive finite `numbers.Real` scalar with boolean values excluded. The admitted value is converted to the parent float representation only after the exact numeric type gate.

Therefore the semantic carrier enters the existing oscillator through an explicit typed boundary and the existing v0.32 control, coupling, HTRI and QHTRI Hamiltonian laws remain the active parent implementation.

## 5. Semantic-value and source-coordinate provenance

For every assigned KAKU, the receipt carries

```text
content_id
kaku_id
lane
orbital_band
B
omega
N
A_R
phi
semantic_value
semantic carrier receipt sha256
```

`B`, `N`, `A_R`, and `semantic_value` are provenance in v0.1. The actuation boundary remains the existing declared lane/frequency profile and parent v0.32 controlled drive.

## 6. Exact invariants

The bridge validates:

1. every semantic KAKU has exactly one explicit lane;
2. lane-profile IDs, KAKU IDs and frequency modes enter through exact string admission;
3. normalized duplicate KAKU IDs fail admission;
4. lane-map and semantic-binding inputs use explicit mapping containers;
5. lanes are unique integers in `[0,35]` with boolean lane values excluded;
6. assigned target phase equals wrapped semantic `phi`;
7. unassigned target phases equal the source snapshot phases exactly;
8. under `ASSIGN_SAMPLE_OMEGA`, assigned frequencies equal semantic `omega`;
9. unassigned frequencies equal source frequencies exactly;
10. under `PRESERVE_SNAPSHOT_OMEGA`, all frequencies equal the source vector;
11. `g`, `flavor`, `tau`, and `gravity` are copied unchanged into the derived snapshot;
12. `dt` is a positive finite real admitted before parent execution;
13. the existing v0.32 controlled step hits the resulting 36D target to its parent numerical tolerance;
14. lane/frequency profile changes alter the bridge receipt identity.

## 7. Authority boundary

The bridge is a candidate/read-only reference.

```text
epistemic_state             = CHYBA
promotion_state             = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority       = false
live_surface_writes         = 0
```

Reference implementation: `src/phasenav_natural_code/semantic_orbital_htri_bridge_v01.py`.
Reference tests: `tests/test_semantic_orbital_htri_bridge_v01.py`.
Validation receipt: `provenance/receipts/PNCS_SEMANTIC_ORBITAL_HTRI_BRIDGE_V0_1.json`.
