# PNCS Semantic RADICAL Oscillator v0.1

Status: `CANDIDATE / EXACT_RELATIONAL_OSCILLATOR_DERIVATION / EXPLICIT_AGGREGATION_ONLY`

## 1. Parent carrier

For every KAKU `a`, the parent semantic carrier remains

\[
\boxed{
\mathcal S_a(t)=\frac{B_a(t)\,\omega_a(t)\,N_a(t)}{A_{R,a}(t)}\bigl(\phi_a(t)+\kappa\bigr),
\qquad
\kappa=\frac{\ln2}{24\pi}.
}
\]

RF/PNCS semantic identity remains the explicit KAKU/content binding. The RADICAL layer composes already-bound KAKU carriers and does not redefine the single-KAKU formula.

## 2. RADICAL carrier bundle

For a `RadicalGraph` with KAKU set `V` and relation set `E`, v0.1 requires exactly one semantic-orbital binding for every KAKU id in `V` and rejects missing or additional bindings.

The canonical bundle is

```text
RADICAL id
basis id
ordered per-KAKU semantic-orbital receipts
ordered relation oscillator deltas
optional explicit aggregation receipt
```

## 3. Relational oscillator coordinates

For every directed relation `a -> b`, PNCS derives

\[
\boxed{\Delta\phi_{ab}=\phi_b-\phi_a},
\qquad
\boxed{\Delta\omega_{ab}=\omega_b-\omega_a},
\qquad
\boxed{\Delta\mathcal S_{ab}=\mathcal S_b-\mathcal S_a}.
\]

Because the same canonical `kappa` shifts both endpoint phases,

\[
(\phi_b+\kappa)-(\phi_a+\kappa)=\phi_b-\phi_a,
\]

so the directed phase relation is exactly invariant under the common `+kappa` offset.

Each edge receipt also records source and target orbital bands. This permits a RADICAL to carry semantic relations as phase/frequency/value differences between already-assigned orbital carriers.

## 4. Aggregation firewall

The RADICAL has no implicit scalar semantic value.

A scalar aggregate exists only when the caller supplies an explicit aggregation profile

```text
aggregation_profile_id
weights[kaku_id]
normalization = NONE | UNIT_SUM
```

with exact KAKU coverage. The reference linear aggregate is

\[
\boxed{
\mathcal S_R=\sum_{a\in V} w_a\mathcal S_a.
}
\]

For `UNIT_SUM`, the profile additionally requires

\[
\sum_a w_a=1.
\]

Changing the profile id, a weight, or normalization changes the deterministic receipt.

## 5. GREMLIN / OPERATORS boundary

The bundle is suitable as candidate material for the existing path

```text
KAKU -> RADICAL -> OPERATORS -> READ_ONLY PNV conformance
```

GREMLIN retains `CHYBA / CANDIDATE_ONLY`; this layer grants neither runtime execution authority nor canon-write authority.

An operator may consume the ordered per-node carriers, relation deltas, or an explicitly declared aggregate. The aggregation profile is provenance and cannot be inferred from the RADICAL topology.

## 6. Validation gates

The reference gate checks:

1. exact KAKU coverage;
2. KAKU id agreement between graph node and carrier receipt;
3. deterministic node ordering;
4. exact directed `delta_phi`, `delta_omega`, and `delta_semantic_value`;
5. exact cancellation of the common `kappa` in phase differences;
6. preservation of source/target orbital bands;
7. explicit aggregation-profile requirement;
8. exact aggregation weight coverage;
9. `UNIT_SUM` normalization;
10. deterministic receipt hashing and profile sensitivity;
11. candidate-only authority fields.

Reference implementation: `src/phasenav_natural_code/semantic_radical_oscillator_v01.py`.
Reference tests: `tests/test_semantic_radical_oscillator_v01.py`.
