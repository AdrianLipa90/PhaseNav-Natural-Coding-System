# PNCS GREMLIN Cross-Formalism Isomorphism Bank v0.2

Status: `CANDIDATE_ONLY / CHYBA / CROSS_FORMALISM_DISCOVERY`

GREMLIN authority:

```text
runtime_execution_authority = false
canon_write_authority = false
promotion_state = CANDIDATE_ONLY
epistemic = CHYBA
```

## Source pins

| Bank | Repository | Commit |
|---|---|---|
| TIR | `AdrianLipa90/The-Fundamental-Theory-of-Informational-Relations` | `26bd867c10b6f6e21b54f2a4dc7b2f49df62907a` |
| IDT | `AdrianLipa90/Informational-Dynamics-of-Time` | `3ac1f53af5223d16f8818dba99a63a6af2ba9498` |
| RFC | `AdrianLipa90/Relational-Field-Closure` | `3ebd7761ccfa70858ab8af1933c2208a82260f9d` |
| SOH | `AdrianLipa90/secret-of-a-half` | `4cf36453ee2b6d33a1f9177ca324b9ef491270be` |
| ZPE | `AdrianLipa90/Zero-Point-Energy` | `7caf8474852ac733d290313d9026f5ffc03f0c9a` |

A new source generation requires a new manifest and fresh compilation receipts.

## Candidate classes

```text
EXACT
EXACT_CONDITIONAL
EXACT_STRUCTURAL
STRONG_STRUCTURAL
SUPPORTED_EXTENSION
```

`EXACT_CONDITIONAL` means the algebraic identity is exact once the explicitly stated realization map is supplied.

## XFI.01 — Exact coboundary ↔ trivial loop holonomy

Class: `EXACT`

IDT supplies an exact edge drive

\[
A_{ab}=V(b)-V(a),
\]

for which every closed cycle obeys

\[
\sum_C A_e=0.
\]

ZPE Stage 2 supplies scalar phase-difference links

\[
U_{ij}=e^{i(\phi_j-\phi_i)},
\]

for which every closed cycle obeys

\[
\prod_C U_{ij}=1.
\]

The common spine is the additive/multiplicative image of an exact one-coboundary:

\[
\boxed{
\sum_C dV=0
\quad\longleftrightarrow\quad
\exp\!\left(i\sum_C d\phi\right)=1.
}
\]

Preserved invariant: exact edge differences carry zero closed circulation and trivial exponentiated loop holonomy.

Falsification gate: a candidate declared exact must fail if an explicitly closed cycle has nonzero additive circulation or non-unit multiplicative closure beyond tolerance.

Sources:
- IDT `formalism/00C_relational_density_viscosity.md`
- ZPE `theory/TIR_DERIVATION_STAGE2.md`

## XFI.02 — TIR CP plaquette ↔ Bargmann quadrilateral

Class: `EXACT_CONDITIONAL`

TIR Stage 36 uses the rephasing-invariant plaquette

\[
P_{ij;kl}=W_{ik}W_{jl}W_{il}^{*}W_{jk}^{*}.
\]

Under the explicit overlap realization

\[
W_{ab}=\langle\psi_a|\psi_b\rangle,
\]

Hermitian overlap reversal gives

\[
W_{il}^{*}=\langle\psi_l|\psi_i\rangle,
\qquad
W_{jk}^{*}=\langle\psi_k|\psi_j\rangle.
\]

Therefore, up to commutative scalar ordering,

\[
\boxed{
P_{ij;kl}
=
\langle i|k\rangle
\langle k|j\rangle
\langle j|l\rangle
\langle l|i\rangle,
}
\]

which is the four-vertex Bargmann closed product.

Preserved invariant: independent local rephasing of every state cancels around the loop.

Falsification gate: rephase every vertex independently and require the complex plaquette to remain invariant within numerical floor.

Sources:
- TIR `TIR/frozen_predictions/validation/TIR_POLYGONAL_EXCITATION_STAGE36_COMPLEX_HOLONOMY_CP_V0_1.md`
- ZPE `theory/TIR_PROJECTIVE_HOLONOMY_STAGE3.md`

## XFI.03 — Spinor central sign across SOH, IDT horizon and ZPE Wilson sectors

Class: `EXACT_STRUCTURAL`

Three separately typed domains share the same double-cover invariant:

```text
SOH SU(2) double cover
IDT Euclidean-horizon spin-1/2 thermal circle
ZPE field-bound SU(2) Wilson transport
```

For a spin-1/2 representation,

\[
\boxed{
2\pi\mapsto -1,
\qquad
4\pi\mapsto +1.
}
\]

ZPE retains both `+I` and `-I` Wilson sectors; IDT derives the primitive horizon `2π` frame winding and its spin-half `-1` factor; SOH carries the central `±I` double-cover lineage.

This is the structural parent of the BioOS/QHTRI integer-turn witness

\[
\zeta=(-1)^n.
\]

Falsification gate: the representation must return the central minus sign after one `2π` lift and return to plus after `4π`.

Sources:
- SOH `research/SOH_G013_PAULI_SPINOR_LIFT_V0_1.md`
- IDT `formalism/01AI_horizon_spin_half_thermal_antiperiodicity.md`
- ZPE `theory/TIR_FIELD_HOLONOMY_STAGE4.md`

## XFI.04 — Shape/scale defect triangle

Class: `EXACT`

IDT 01X factorizes a positive extensive state into normalized shape and scale:

\[
Q=S p,
\qquad
S=Q_\Sigma,
\qquad
\sum_a p_a=1.
\]

For a candidate realization

\[
\widehat Q=\widehat S\,\widehat p,
\qquad
r=\widehat S/S,
\]

define

\[
D_{ext}:=\frac{\|Q-\widehat Q\|_1}{S},
\quad
D_{shape}:=\|p-\widehat p\|_1,
\quad
D_{scale}:=|1-r|.
\]

Then

\[
D_{ext}=\|p-r\widehat p\|_1
\le
\|p-\widehat p\|_1+\|(1-r)\widehat p\|_1,
\]

and because `widehat p` is normalized,

\[
\boxed{
D_{ext}\le D_{shape}+D_{scale}.
}
\]

This has the same defect-separation grammar as the IDT↔RFC conserved-current theorem

\[
\Delta_\Sigma\le\Delta_J+\Delta_V.
\]

Potential BioOS use: a ZPE-normalized compute gate can audit relational-shape drift and physical/execution-scale drift as separate coordinates while retaining a rigorous bound on the extensive realization defect.

Falsification gate: randomized positive simplex/scale pairs must satisfy the inequality; adversarial non-normalized shape input is rejected before applying the theorem.

Sources:
- IDT `formalism/01X_RFC_normalized_shape_extensive_scale_interface.md`
- IDT `formalism/01AA_noether_rfc_conserved_current_binding.md`

## XFI.05 — Positive-ray quotient ↔ projective U(1) quotient

Class: `STRONG_STRUCTURAL`

IDT normalization identifies every positive ray

\[
Q\sim\lambda Q,
\qquad \lambda>0,
\]

with one simplex point

\[
p=Q/Q_\Sigma.
\]

ZPE projective geometry identifies

\[
|\psi\rangle\sim e^{i\alpha}|\psi\rangle
\]

with one projective state.

Common spine:

```text
raw state
 -> global one-parameter group orbit
 -> quotient
 -> relational/projective shape
```

Preserved structure: relative coordinates survive while one global gauge/scale coordinate is factored into a separate fiber.

The quotient groups and metric structures remain explicitly typed by their source domains.

Falsification gate: positive rescaling must preserve simplex shape; global phase multiplication must preserve projective overlap magnitudes.

Sources:
- IDT `formalism/01X_RFC_normalized_shape_extensive_scale_interface.md`
- ZPE `theory/TIR_PROJECTIVE_HOLONOMY_STAGE3.md`

## XFI.06 — Scale × direction fibration across carrier, field and rotor

Class: `STRONG_STRUCTURAL`

Three formalisms independently separate an extensive/radial scale from normalized relational direction:

\[
Q=Q_\Sigma p,
\]

\[
B=|B|n,
\qquad n=B/|B|\in S^2,
\]

\[
\omega=\Omega\widehat\omega.
\]

The common candidate fibration is

\[
\boxed{x=\text{positive scale}\times\text{normalized relational shape/direction}.}
\]

This is a useful parent for the BioOS normalization controller: computational scale may vary while a separately tested relational coordinate remains inside its admission tolerance.

Falsification gate: positive scale changes must preserve the declared normalized coordinate; any direction/shape drift is measured separately rather than absorbed into scale.

Sources:
- IDT `formalism/01X_RFC_normalized_shape_extensive_scale_interface.md`
- ZPE `theory/TIR_FIELD_HOLONOMY_STAGE4.md`
- ZPE `theory/TIR_DERIVATION_STAGE2.md`

## XFI.07 — Action/area/holonomy bank extension

Class: `SUPPORTED_EXTENSION`

IDT already stores GREMLIN hypothesis `ACTION_AREA_HOLONOMY_V0_1`, relating:

```text
Kepler swept area
symplectic action-area
Berry curvature/holonomy
memory circulation
```

through the boundary/curvature-flux spine.

ZPE Stage 3 and Stage 4 add two compatible path observables:

- Bargmann/Pancharatnam closed product;
- field-derived SU(2) Wilson loop.

Thus the existing bank may be extended from a U(1)/two-form area grammar to a broader path-holonomy grammar while keeping Abelian and non-Abelian carriers separately typed.

Falsification gate: orientation reversal must transform each declared oriented observable according to its own source representation; numerical identification across domains additionally requires an explicit pullback and normalization.

Sources:
- IDT `validation/gremlin/ACTION_AREA_HOLONOMY_V0_1.md`
- IDT `formalism/00D_memory_orbit_drive.md`
- ZPE `theory/TIR_PROJECTIVE_HOLONOMY_STAGE3.md`
- ZPE `theory/TIR_FIELD_HOLONOMY_STAGE4.md`

## XFI.08 — Mobility/orientation split ↔ magnitude/phase split

Class: `STRONG_STRUCTURAL`

IDT directed kinetics factorize as

\[
W_{a\to b}=M_{ab}e^{A_{ab}/2},
\qquad
W_{b\to a}=M_{ab}e^{-A_{ab}/2},
\]

where edge reversal preserves the positive mobility coordinate and reverses the signed affinity coordinate.

TIR complex holonomy links factorize as

\[
W^{\mathbb C}_{ij}=a_{ij}e^{i\phi_{ij}},
\]

where magnitude and phase are separately addressable coordinates.

Common structural invariant:

```text
positive magnitude / pace channel
+
orientation-sensitive channel
```

The IDT orientation carrier is a real exponential coordinate while the TIR carrier is unitary phase; the bank preserves this type distinction.

Falsification gate: edge reversal must preserve the declared magnitude coordinate and transform the orientation coordinate according to the source-domain involution.

Sources:
- IDT `formalism/00C_relational_density_viscosity.md`
- TIR `TIR/frozen_predictions/validation/TIR_POLYGONAL_EXCITATION_STAGE36_COMPLEX_HOLONOMY_CP_V0_1.md`

## Ranking

```text
XFI.01  EXACT              coboundary -> trivial loop holonomy
XFI.04  EXACT              shape/scale defect triangle
XFI.02  EXACT_CONDITIONAL  CP plaquette -> Bargmann quadrilateral
XFI.03  EXACT_STRUCTURAL   spinor central sign triple bridge
XFI.07  SUPPORTED_EXTENSION action/area/holonomy bank + Bargmann/Wilson
XFI.05  STRONG_STRUCTURAL  positive-ray quotient <-> projective quotient
XFI.06  STRONG_STRUCTURAL  scale x normalized direction fibration
XFI.08  STRONG_STRUCTURAL  mobility/orientation <-> magnitude/phase split
```

## Promotion rule

Every entry compiles independently through the existing GREMLIN relational compiler:

```text
RelationalIsomorphism
 -> KAKU candidate(s)
 -> RADICAL candidate
 -> OPERATORS candidate(s)
 -> READ_ONLY PNV conformance graph
```

Compilation and structural salience do not change the evidence status of the source claims. Promotion requires the entry-specific falsification gate and any explicit physical binding required by the source formalism.
