# PNCS Prime-Temporal Hydrodynamic Substrate v0.1

**Status:** EXPERIMENTAL / READ_ONLY / NON-PROMOTING  
**Epistemic operator:** CHYBA  
**PNCS release effect:** none  
**Routing feedback:** closed  
**External effects:** closed  
**Laboratory-time claim:** closed  

## 1. Scope

This module implements the prime-valuation and temporal-flow layer as an experimental
PhaseNav coding-language module. It does not modify v0.28 release closure.

The implemented path is:

```text
positive integer
-> exact prime valuation
-> exact Collatz prime flux
-> explicit content-addressed spectral registry
-> explicit spectral weights
-> relative-phase evolution
-> temporal coherence C_Z
-> temporal fuzziness F_Z
-> Fubini-Study temporal speed v_T
-> continuity accumulator Lambda_T
-> 18 complementary pairs
-> T^36 realization
-> typed temporal-hydrodynamic observable
```

## 2. Exact arithmetic layer

For positive integer `n`:

\[
v(n)=(v_2(n),v_3(n),v_5(n),\ldots)
\]

with finite support and

\[
\log n=\sum_p v_p(n)\log p.
\]

For an exact shortcut-Collatz step:

\[
\Delta v_p=v_p(C(n))-v_p(n),
\qquad
\log\frac{C(n)}n=\sum_p\Delta v_p\log p.
\]

For odd `n`, the implementation verifies the exact support-disjoint condition

\[
\gcd(n,C(n))=1.
\]

## 3. Critical-line prime realization

For declared `tau` and valuation flux `Delta v_p`:

\[
p^{-(1/2+i\tau)\Delta v_p}
=
p^{-\Delta v_p/2}
e^{-i\tau\Delta v_p\log p}.
\]

This numerical realization does not alter the exact prime-flux identity.

## 4. Spectral-lift boundary

The arithmetic product is not automatically converted into a spectral superposition.

A spectral state requires:
- an explicit content-addressed frequency registry;
- explicit normalized probabilities/weights;
- a declared registry kind: `PRIME_LOG`, `ZETA_ZERO`, or `EXPLICIT`;
- an explicit frequency scale.

`PRIME_LOG` and `ZETA_ZERO` registries are distinct evidence layers.

## 5. Relative-phase and fuzziness observables

For normalized probabilities `p_j` and registered angular frequencies `omega_j`:

\[
C_Z(t)=\left|\sum_jp_je^{-i\omega_jt}\right|,
\qquad
F_Z(t)=1-C_Z(t)^2.
\]

A one-mode state has zero internal phase dispersion.

## 6. Fubini-Study temporal flow

The implemented local speed is

\[
v_T^2
=
\frac14\sum_j\frac{\dot p_j^2}{p_j}
+
\operatorname{Var}_p(\omega_j).
\]

The first term is optional and is admitted only when probability-rate inputs are explicit
and normalization-conserving.

The accumulated continuity coordinate is

\[
\Lambda_T(t+\Delta t)
=
\Lambda_T(t)+v_T\Delta t.
\]

A decrease of fuzziness during a revival never decreases `Lambda_T`.

## 7. T^36 projection

Exactly 18 registered frequencies are mapped to 18 complementary phase pairs:

\[
\theta_{2j-1}=(\theta_c-\omega_jt)\bmod 2\pi,
\qquad
\theta_{2j}=(\theta_c+\omega_jt)\bmod 2\pi.
\]

The center phase is explicit input. No unparented phase constant is inserted.

## 8. Hydrodynamic boundary

The typed observable carries:
- `C_Z`;
- `F_Z`;
- `v_T`;
- `Lambda_T`;
- spectral registry identity;
- optional T^36 realization identity.

It does **not** define or modify the hydrodynamic lapse.

Any later relation

\[
N_i=\mathcal N(v_{T,i},F_{Z,i},\rho_i,\nu_{\rm eff,i},\ldots)
\]

requires a separately preregistered and tested policy.

## 9. Validation gates

The pure test suite requires:
- exact prime factorization/log identity;
- exact Collatz prime-flux ratio reconstruction;
- zero net prime flux on the `1 -> 2 -> 1` control cycle;
- odd-branch support disjointness;
- critical-line prime-factor agreement;
- deterministic content-addressed spectral registries;
- zero fuzziness and zero phase speed for one mode;
- two-mode phase dispersion and revival;
- monotonic continuity through revival;
- Fubini-Study population-flow contribution;
- exact 36-coordinate pair geometry;
- typed non-authoritative temporal-hydrodynamic observable;
- fail-closed invalid-input handling.
