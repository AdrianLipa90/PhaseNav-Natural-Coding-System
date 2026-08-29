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

The mapping is explicit provenance. v0.1 rejects lane collisions and rejects missing or extra KAKU mappings relative to the supplied semantic binding set.

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

The selected profile is part of the deterministic receipt. No frequency map is inferred from orbital band, semantic value, KAKU mass, or neighboring lanes.

## 4. v0.32 composition

The bridge constructs a derived read-only `DriveSnapshot`:

```text
phi    = original snapshot phi
omega  = profile-bound omega
-g/-flavor/-tau/-gravity = unchanged copies from source snapshot
source_id = content-addressed bridge identity
```

It separately constructs `target36` by replacing only the explicitly assigned phase lanes.

Then it calls the existing

```text
semantic_htri_drive_v32.controlled_step(derived_snapshot, target36, dt)
```

without modifying the v0.32 control, coupling, HTRI or QHTRI Hamiltonian laws.

Therefore the semantic carrier enters the existing oscillator through an explicit typed boundary instead of a parallel oscillator implementation.

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
kappa
semantic_value
semantic carrier receipt sha256
```

`B`, `N`, `A_R`, and `semantic_value` are provenance in v0.1. The v0.32 drive has no native actuation input for those coordinates. A future actuation gate may map an explicitly source-bound coordinate into coupling/drive parameters with its own validation receipt.

## 6. Exact invariants

The bridge validates:

1. every semantic KAKU has exactly one explicit lane;
2. lanes are unique integers in `[0,35]`;
3. assigned target phase equals wrapped semantic `phi`;
4. unassigned target phases equal the source snapshot phases exactly;
5. under `ASSIGN_SAMPLE_OMEGA`, assigned frequencies equal semantic `omega`;
6. unassigned frequencies equal source frequencies exactly;
7. under `PRESERVE_SNAPSHOT_OMEGA`, all frequencies equal the source vector;
8. `g`, `flavor`, `tau`, and `gravity` are copied unchanged into the derived snapshot;
9. the existing v0.32 controlled step hits the resulting 36D target to its parent numerical tolerance;
10. lane/frequency profile changes alter the bridge receipt identity.

## 7. Authority boundary

The bridge is a candidate/read-only reference.

```text
epistemic_state            = CHYBA
promotion_state            = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority       = false
live_surface_writes         = 0
```

Reference implementation: `src/phasenav_natural_code/semantic_orbital_htri_bridge_v01.py`.
Reference tests: `tests/test_semantic_orbital_htri_bridge_v01.py`.
Validation receipt: `provenance/receipts/PNCS_SEMANTIC_ORBITAL_HTRI_BRIDGE_V0_1.json`.
