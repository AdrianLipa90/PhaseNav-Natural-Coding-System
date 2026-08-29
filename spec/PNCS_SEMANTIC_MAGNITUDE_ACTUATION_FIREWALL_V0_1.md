# PNCS Semantic Magnitude -> HTRI Actuation Firewall v0.1

Status: `CANDIDATE / EXACT_NON_ACTUATION_FIREWALL / SOURCE_BINDING_OPEN`

## 1. Algebraic source factor

The canonical semantic carrier admits the exact factorization

\[
\boxed{
Q_{BNA}(t):=\frac{B(t)N(t)}{A_R(t)},
}
\]

\[
\boxed{
\mathcal S(t)=Q_{BNA}(t)\,\omega(t)\,(\phi(t)+\kappa).
}
\]

`Q_BNA` is an algebraic coordinate of the user formula. v0.1 preserves the source symbols `B`, `N`, and `A_R` and assigns no additional physical normalization to this coordinate.

## 2. Current HTRI boundary

The v0.32 semantic HTRI drive consumes a 36D target phase and a `DriveSnapshot` containing `omega`, coupling `g`, flavor, tau and gravity coordinates.

The Semantic Orbital -> HTRI Bridge v0.1 binds semantic `phi` and, under an explicit profile, semantic `omega` to selected lanes. It carries `B`, `N`, `A_R`, `Q_BNA`, and `semantic_value` as provenance.

The v0.33 bounded HTRI reference additionally exposes a positive control bound `u_max` and saturation diagnostics. `u_max` is an independently typed control limit.

## 3. Exact non-actuation theorem for v0.1

Consider two semantic bindings `X` and `Y` with the same:

```text
content_id
kaku_id
phi
omega
lane profile
frequency binding profile
source HTRI DriveSnapshot
```

while `B`, `N`, and/or `A_R` may differ.

Then the current v0.1 HTRI bridge produces exactly the same numeric:

```text
target36
derived omega vector
derived phi vector
derived g/flavor/tau/gravity arrays
controlled phi_next
controlled g_next
controlled gravity_next
control vector
QHTRI Hamiltonian H
```

because those arrays depend on the semantic binding only through the explicitly admitted `phi` and `omega` lane channels.

The semantic receipts remain distinct because `Q_BNA`, `semantic_value`, quantized orbital band, and semantic binding commitment may differ.

This is a deliberate firewall separating semantic magnitude coordinates from physical HTRI actuation.

## 4. Open source-binding gate

A future actuation law may bind a source-derived function of

\[
(B,N,A_R,\mathcal S,Q_{BNA})
\]

to an HTRI/QHTRI actuation coordinate such as a bounded control envelope, coupling parameter, or another admitted hardware carrier. That law requires its own units, normalization, source provenance and falsification receipt.

The current gate records this frontier as:

```text
SEMANTIC_MAGNITUDE_TO_HTRI_ACTUATION = OPEN_SOURCE_BINDING
```

## 5. Validation

The reference audit:

1. computes `Q_BNA=B*N/A_R`;
2. requires equal KAKU/content identity, `phi`, and `omega` for a magnitude-only comparison;
3. executes both bindings through the same HTRI bridge profile and source snapshot;
4. checks exact equality of all numeric HTRI/QHTRI output arrays listed above;
5. confirms semantic values may differ;
6. confirms deterministic semantic/bridge receipt provenance remains distinct;
7. retains `CHYBA / CANDIDATE_ONLY` authority.

Reference implementation: `src/phasenav_natural_code/semantic_magnitude_actuation_firewall_v01.py`.
Reference tests: `tests/test_semantic_magnitude_actuation_firewall_v01.py`.
