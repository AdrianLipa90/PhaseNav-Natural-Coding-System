# PNCS Semantic Phase Inverse v0.2

Status: `CANDIDATE / EXACT_NONZERO_CARRIER_INVERSE / CANONICAL_PHASE_WINDING_SPLIT / ORBIT_PLACEMENT_COMPOSITION / GREMLIN_CANDIDATE_ONLY`

RF/PNCS source parent: `PNCS_SEMANTIC_ORBITAL_CARRIER_V0_1`.

## 1. Parent semantic carrier

The parent contract is

\[
\boxed{
\mathcal S(t)
=\frac{B(t)\omega(t)N(t)}{A_R}
\bigl(\phi(t)+\kappa\bigr),
\qquad
\kappa=\frac{\ln2}{24\pi}.
}
\]

Define

\[
\boxed{
C(t):=\frac{B(t)\omega(t)N(t)}{A_R}.
}
\]

Then

\[
\mathcal S(t)=C(t)(\phi(t)+\kappa).
\]

## 2. Exact inverse on the identifiable branch

For

\[
\boxed{C(t)\ne0,}
\]

the lifted phase is uniquely fixed by the carried semantic value:

\[
\boxed{
\phi_{lift}(t)
=\frac{\mathcal S(t)}{C(t)}-\kappa
=\frac{A_R\mathcal S(t)}{B(t)\omega(t)N(t)}-\kappa.
}
\]

Substitution gives the exact roundtrip

\[
\boxed{
C(t)\bigl(\phi_{lift}(t)+\kappa\bigr)=\mathcal S(t).
}
\]

Thus semantic value, together with the admitted carrier coordinates, fixes one lifted phase coordinate through the declared inverse profile.

## 3. Canonical wrapped phase and winding

Let

\[
\tau:=2\pi.
\]

For every finite lifted phase define

\[
\boxed{
w=\left\lfloor\frac{\phi_{lift}}{2\pi}\right\rfloor\in\mathbb Z,
}
\]

and

\[
\boxed{
\phi_{wrap}=\phi_{lift}-2\pi w,
\qquad
0\le\phi_{wrap}<2\pi.
}
\]

Therefore

\[
\boxed{
\phi_{lift}=\phi_{wrap}+2\pi w.
}
\]

The semantic value is exactly recoverable from the wrapped representation:

\[
\boxed{
\mathcal S
=C\bigl(\phi_{wrap}+2\pi w+\kappa\bigr).
}
\]

The winding coordinate is therefore part of the lossless semantic phase code whenever a wrapped phase representation is used.

## 4. Zero-carrier identifiability firewall

When

\[
C=0,
\]

the parent equation becomes

\[
\mathcal S=0.
\]

Three explicit states are retained:

```text
C = 0 and S != 0  -> INCONSISTENT_ZERO_CARRIER
C = 0 and S = 0   -> NON_IDENTIFIABLE_PHASE
C != 0            -> UNIQUE_LIFTED_PHASE
```

The unique phase encoder is defined on the `C != 0` branch.

## 5. Orbit placement

The parent v0.1 contract supplies an explicit semantic-value orbital quantizer

\[
\mathcal S\xrightarrow{Q_{orbit}}O_i,
\qquad i\in\{0,\ldots,8\}.
\]

v0.2 composes the exact inverse with that quantizer:

\[
\boxed{
\mathcal S
\longmapsto
\left(
O_i,
\phi_{wrap},
w
\right).
}
\]

The complete placement receipt also carries

```text
B
omega
N
A_R
kappa
C
semantic_value
orbit_quantizer_id
```

so the phase/orbit code can be replayed exactly.

## 6. Typed admission boundary

The inverse-specific scalar coordinates

```text
semantic_target
kappa
lifted_phase
wrapped_phase
sample_time
```

require finite `numbers.Real` values with `bool` excluded. Numeric strings and arbitrary objects exposing `__float__` are rejected at this boundary. Finite-conversion overflow also fails closed.

The carrier coordinates

```text
B
omega
N
A_R
```

retain the strict-real admission contract of `PNCS_SEMANTIC_ORBITAL_CARRIER_V0_1`.

`content_id`, `kaku_id` and direct placement `orbital_band` are exact string identities. The established whitespace normalization for non-empty content/KAKU identifiers is preserved.

Canonical winding remains an exact integer with `bool` excluded.

The supplied quantizer is admitted as an `OrbitQuantizerProfile` before its `quantize()` method participates in placement construction.

## 7. Immutable placement provenance

A `SemanticPhasePlacement` stores the admitted

```text
sample_time
semantic_target
B
omega
N
A_R
```

as canonical plain `float` values before deterministic receipt construction. The placement therefore commits one scalar snapshot even when an accepted `numbers.Real` implementation has caller-controlled conversion state.

Receipt construction consumes these stored canonical coordinates directly. Repeated receipt generation from one placement preserves the same carrier coordinate snapshot.

## 8. Distinct source and placement phase profiles

The parent PNLF adapter uses the stored wrapped `OrbitalState.phase` as one source-phase profile and records PNLF winding separately.

v0.2 defines the semantic-value inverse profile:

```text
semantic target S
 -> unique lifted phase when C != 0
 -> canonical wrapped phase + integer winding
```

Both profiles carry explicit receipt identities. A later equality/transport gate can bind them through its own declared contract.

## 9. KAKU / RADICAL use

For one explicit KAKU/content identity, the candidate encoder is

```text
content_id + KAKU id
 -> carrier coordinates B,omega,N,A_R
 -> semantic target S
 -> exact phi_lift
 -> phi_wrap + winding
 -> explicit orbit quantizer
 -> O_i
```

RADICAL composition consumes these per-KAKU codes through a separately identified composition/operator profile.

## 10. GREMLIN boundary

GREMLIN may propose candidate placements. The deterministic receipt retains

```text
semantic_authority = EXPLICIT_KAKU_CONTENT_BINDING
epistemic_state = CHYBA
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
```

## 11. Validation gates

Reference tests verify:

1. exact phase inversion for positive and negative carrier prefactors;
2. semantic roundtrip through lifted phase;
3. canonical wrapped phase in `[0,2pi)`;
4. exact integer winding decomposition for positive and negative lifted phases;
5. exact roundtrip from wrapped phase plus winding;
6. distinction between inconsistent and non-identifiable zero-carrier cases;
7. composition with explicit `O0..O8` quantizer provenance;
8. deterministic receipt hashing;
9. finite-result and integer-winding admission;
10. bool, numeric-string and arbitrary float-coercible inverse-coordinate rejection;
11. exact content/KAKU/orbital-band string identity;
12. inherited strict carrier-coordinate admission;
13. quantizer type admission before quantizer execution;
14. canonical carrier-coordinate snapshot stability under caller-side `Real` conversion-state mutation.

Reference implementation: `src/phasenav_natural_code/semantic_phase_inverse_v02.py`.
Reference tests:
- `tests/test_semantic_phase_inverse_v02.py`
- `tests/test_semantic_phase_inverse_admission_v02.py`

Validation receipt: `provenance/receipts/PNCS_SEMANTIC_PHASE_INVERSE_V0_2.json`.
