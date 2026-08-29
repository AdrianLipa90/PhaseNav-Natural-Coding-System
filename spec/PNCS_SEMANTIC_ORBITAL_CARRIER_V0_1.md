# PNCS Semantic Orbital Carrier v0.1

Status: `CANDIDATE / EXACT_SEMANTIC_VALUE_EVALUATOR / EXPLICIT_ORBIT_QUANTIZER_INTEGRATION / GREMLIN_CANDIDATE_ONLY`

## 1. Canonical semantic carrier

For a semantic carrier sampled at time `t`, PNCS uses the user-specified value

\[
\boxed{
\mathcal S(t)
=\frac{B(t)\,\omega(t)\,N(t)}{A_R}
\bigl(\phi(t)+\kappa\bigr)
}
\]

with the canonical PNCS/TIR constant

\[
\boxed{
\kappa=\frac{\ln 2}{24\pi}.
}
\]

The exact factorization is

\[
\mathcal C(t):=\frac{B(t)\omega(t)N(t)}{A_R},
\qquad
\Phi_\kappa(t):=\phi(t)+\kappa,
\]

\[
\boxed{\mathcal S(t)=\mathcal C(t)\Phi_\kappa(t).}
\]

`B`, `omega`, `N`, `A_R`, and `phi` remain source-typed coordinates supplied by the calling model/profile. v0.1 preserves their symbols exactly.

## 2. Semantic identity and numeric realization

The semantic identity of a KAKU is supplied by the existing explicit `atom -> content_id` binding. The orbital carrier adds a deterministic numeric realization attached to that identity:

```text
content_id
KAKU id
sample time t
B(t)
omega(t)
N(t)
A_R
phi(t)
kappa
semantic_value S(t)
```

This preserves the existing GREMLIN KAKU resolver authority contract while adding a semantic-value coordinate suitable for orbital assignment.

## 3. Orbital assignment

PNLF already represents orbital bands

```text
O0 O1 O2 O3 O4 O5 O6 O7 O8
```

through an explicit `orbit_quantizer_id`.

PNCS therefore composes

\[
\boxed{
\mathcal S(t)
\xrightarrow{Q_{orbit}}
O_i,
\qquad i\in\{0,\ldots,8\}.
}
\]

The v0.1 quantizer profile MUST explicitly carry all three items:

```text
quantizer_id
8 strictly increasing semantic-value boundaries
ordered 9-element permutation of O0..O8
```

The ordered band permutation is part of the source profile. The semantic carrier formula does not choose whether increasing `S(t)` corresponds to increasing band index, decreasing band index, or another admitted permutation. Therefore the API has no implicit `O0 -> O8` direction.

Both threshold values and exact band ordering enter provenance. Identical semantic values evaluated under profiles with different thresholds or different band permutations remain distinguishable receipts.

## 4. Oscillator coordinates

An orbital carrier receipt preserves

```text
orbital_band
omega(t)
phi(t)
B(t)
N(t)
A_R
semantic_value
orbit_quantizer_id
explicit band ordering
```

When the source is a PNLF `OrbitalState`, the standard angular-frequency projection from its positive orbital period is

\[
\boxed{
\omega_{orbit}=\frac{2\pi}{T_{orbit}}.
}
\]

The PNLF wrapped `phase` is copied as `phi`; `winding` remains a separate recorded coordinate. An alternate phase-lift profile can therefore be introduced with an explicit profile identifier while preserving the v0.1 formula.

## 5. KAKU/RADICAL/OPERATORS boundary

The v0.1 carrier attaches one semantic-orbital sample to one admitted KAKU identity.

```text
explicit content binding
 -> KAKU
 -> semantic carrier sample
 -> S(t)
 -> explicit orbit quantizer profile
 -> orbital-band candidate
```

RADICAL composition consumes the per-KAKU carrier receipts. A RADICAL aggregation law is carried by its own operator/profile identifier, so the single-KAKU formula remains exact and independently auditable.

## 6. GREMLIN use

GREMLIN may propose candidate semantic-orbital bindings using the same evaluator and an admitted quantizer profile. Candidate receipts retain

```text
epistemic_state = CHYBA
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
```

The existing explicit `content_id` remains the semantic authority input.

## 7. Deterministic receipt

The reference implementation emits a canonical JSON receipt containing

- formula schema and canonical `kappa`;
- KAKU/content identifiers;
- exact sample coordinates;
- carrier prefactor `C(t)`;
- shifted phase `phi+kappa`;
- semantic value `S(t)`;
- orbital band, quantizer identifier, thresholds and explicit band permutation;
- PNLF source coordinates when present;
- GREMLIN authority fields;
- SHA-256 over canonical JSON.

## 8. Validation gates

The reference gate checks

1. the canonical value of `kappa`;
2. exact formula evaluation;
3. exact factorization `S=C(phi+kappa)`;
4. finite input coordinates and nonzero `A_R`;
5. explicit presence of a 9-band ordering together with 8 ordered thresholds;
6. exact validation that the band ordering is a permutation of `O0..O8`;
7. deterministic quantization under the declared profile;
8. PNLF `orbit_period -> omega=2pi/T` projection;
9. preservation of wrapped phase and winding provenance;
10. explicit KAKU/content identity fields;
11. receipt determinism and sensitivity to quantizer thresholds, id and band ordering;
12. GREMLIN candidate authority fields.

Reference implementation: `src/phasenav_natural_code/semantic_orbital_carrier_v01.py`.
Reference tests: `tests/test_semantic_orbital_carrier_v01.py`.
Validation receipt: `provenance/receipts/PNCS_SEMANTIC_ORBITAL_CARRIER_V0_1.json`.
