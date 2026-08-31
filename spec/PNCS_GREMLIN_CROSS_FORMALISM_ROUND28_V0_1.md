# PNCS GREMLIN Cross-Formalism ROUND28 v0.1

Status: `CANDIDATE_ONLY / CHYBA / SOURCE_PINNED`

ROUND28 extends the cross-formalism discovery bank with three source-pinned relational isomorphisms whose preserved structures admit direct algebraic or geometric probes.

Source pins:

```text
IDT  AdrianLipa90/Informational-Dynamics-of-Time@3ac1f53af5223d16f8818dba99a63a6af2ba9498
SOH  AdrianLipa90/secret-of-a-half@4cf36453ee2b6d33a1f9177ca324b9ef491270be
ZPE  AdrianLipa90/Zero-Point-Energy@7caf8474852ac733d290313d9026f5ffc03f0c9a
```

The GREMLIN authority boundary remains:

```text
runtime_execution_authority = false
canon_write_authority = false
promotion_state = CANDIDATE_ONLY
epistemic = CHYBA
```

## XFI.28.01 — CP1 memory transport ↔ SU(2) spin lift

IDT 06C transports the Kähler memory dyad between non-antipodal Bloch anchors by the minimal rotation

\[
R_{b\leftarrow a}\in SO(3).
\]

For normalized endpoints \(\mathbf n_a,\mathbf n_b\), define

\[
\theta_{ab}=\arccos(\mathbf n_a\cdot\mathbf n_b),
\qquad
\mathbf a_{ab}
=\frac{\mathbf n_a\times\mathbf n_b}
{\|\mathbf n_a\times\mathbf n_b\|}.
\]

The ZPE projective-holonomy construction uses the corresponding spin lift

\[
W_{ab}
=\exp\!\left[-\frac{i}{2}\theta_{ab}
(\mathbf a_{ab}\cdot\boldsymbol\sigma)\right]
\in SU(2).
\]

Under the standard double-cover projection \(\pi:SU(2)\to SO(3)\), ROUND28 records the candidate identity

\[
\boxed{\pi(W_{ab})=R_{b\leftarrow a}}.
\]

The reference implementation expresses the same lift as the unit quaternion

\[
q_{ab}
=\left(
\cos\frac{\theta_{ab}}2,
\sin\frac{\theta_{ab}}2\,\mathbf a_{ab}
\right)
\]

and compares its projected action against the Rodrigues rotation. Both \(q_{ab}\) and \(-q_{ab}\) project to the same SO(3) transport.

Preserved structure:

```text
Bloch endpoints
minimal geodesic axis
geodesic angle
orientation-preserving tangent-frame transport
antipodal ambiguity gate
```

Architecture consequence for a lifted memory representation:

```text
CP1/Bloch state                -> projective state
central SU(2) sign / lift      -> separate lineage relation
```

A system that retains spinorial history can therefore bind the lift sign as provenance alongside the projective memory state.

Falsification gate: for any admitted non-antipodal endpoint pair, the quaternion/SU(2) projection and the Rodrigues/SO(3) transport must agree within the declared numerical tolerance.

Classification: `EXACT`.

## XFI.28.02 — Half interface relational zero

IDT 01I defines

\[
\mathcal D_{1/2}(p,\Delta\tau)
=1+2\sqrt{p(1-p)}
\cos\!\left(\frac{\Delta\tau}{2}\right).
\]

Secret-of-a-Half SOH-X uses the same two-channel kernel under

\[
\phi=\frac{\Delta\tau}{2}.
\]

The shared exact zero is

\[
\boxed{
\mathcal D_{1/2}=0
\iff
p=\frac12,
\quad
\Delta\tau\equiv2\pi\pmod{4\pi}.
}
\]

SOH-G013 supplies the compatible spinorial order-doubling relation

\[
U_j(\pi)^2=-I,
\qquad
U_j(\pi)^4=I.
\]

ROUND28 therefore binds the invariant

```text
balanced two-channel weight
+ spinorial half-angle phase
+ lifted 2pi sign change
-> relational projection zero
```

Preserved structure:

```text
balanced weight one-half
spinorial half-angle carrier
2pi lifted displacement -> relative phase pi
4pi spinor return
relational null of the symmetric projection
```

Scope firewall: each physical two-channel realization retains its own repository admission and falsification gates; ROUND28 exports the exact shared local kernel and transformation law.

Classification: `EXACT`.

## XFI.28.03 — Hyperbolic centered-coordinate chart

IDT 04A has

\[
\frac{\mathfrak j}{\mathfrak a}
=\tanh\!\left(\frac A2\right),
\qquad
A=2\operatorname{artanh}\!\left(\frac{\mathfrak j}{\mathfrak a}\right).
\]

SOH-G009 has

\[
t=\tanh\!\left(\frac\lambda2\right),
\qquad
\lambda=2\operatorname{artanh}(t).
\]

The exact coordinate identification is

\[
\boxed{
t\leftrightarrow\frac{\mathfrak j}{\mathfrak a},
\qquad
\lambda\leftrightarrow A.}
\]

Because IDT also defines

\[
\beta=\frac{A}{24\pi},
\]

the mapped phase coordinate is

\[
\boxed{\beta=\frac{\lambda}{24\pi}}.
\]

Orientation reversal is preserved:

\[
t\mapsto-t
\Longleftrightarrow
\frac{\mathfrak j}{\mathfrak a}\mapsto-rac{\mathfrak j}{\mathfrak a},
\]

\[
\lambda\mapsto-\lambda
\Longleftrightarrow
A\mapsto-A.
\]

The arithmetic and kinetic meanings remain separately typed; the candidate invariant is the exact centered hyperbolic chart and its involution law.

Classification: `EXACT_COORDINATE_ISOMORPHISM`.

## GREMLIN compilation

`src/phasenav_natural_code/gremlin_cross_formalism_round28_v01.py` compiles every entry through the existing relational compiler:

```text
RelationalIsomorphism
 -> KAKU candidates
 -> RADICAL candidate
 -> OPERATORS
 -> READ_ONLY PNV
 -> validator receipt
```

Every compiled candidate must return:

```text
external_effects = false
mode = READ_ONLY
epistemic = CHYBA
```

The whole T36 lane remains a relational witness. ROUND28 assigns semantic roles to KAKU objects and relations rather than to individual T36 coordinates.

## Executable gates

`tests/test_gremlin_cross_formalism_round28_v01.py` targets:

1. source-pinned three-entry manifest closure;
2. CP1 minimal-rotation / spin-lift projection agreement;
3. equality of the q and -q SO(3) projections;
4. fail-closed antipodal ambiguity;
5. exact half-interface relational zero and off-gate controls;
6. hyperbolic forward/inverse round trip;
7. orientation reversal in the centered chart;
8. KAKU -> RADICAL -> OPERATORS -> READ_ONLY PNV compilation for all three entries.

Execution evidence remains attached to an actual test run or CI receipt.
