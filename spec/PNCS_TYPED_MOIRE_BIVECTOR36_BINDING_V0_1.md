# PNCS Typed Moire Bivector36 Binding v0.1
Date: 2026-09-26
Status: CANDIDATE / FAIL-CLOSED / NON-CANON

## 1. Existing authority

PNCS currently defines the generic exact phase realization as

    PhaseVector36 in T^36
    basis_id = PNV_T36_PHASE_ANGLES_RADIANS_V1
    coordinate_semantics = phase_angles_radians.

The semantic/physical meanings of the individual coordinate axes remain
intentionally unassigned by PNCS_36D_BASIS_V0_1.

Therefore this specification does not reinterpret the generic basis.

## 2. No-canonical-adapter result

Current PNCS authority does not determine a unique mapping

    PNV_T36_PHASE_ANGLES_RADIANS_V1
      -> PNV_BIVECTOR_OPERATOR36_LAMBDA2_R4_PAIRBASIS_V1.

A mapping would require additional axis/basis semantics or an explicit
derivation receipt. Vector length 36 alone is insufficient evidence.

Rule:

    generic basis + no explicit typed derivation -> REJECT.

This preserves the existing invariant that coordinate similarity or shape is
not semantic authority.

## 3. Recovered glossary strengthens the no-go

The persistent recovered glossary phase marker uses

    phi_i(q) =
      [kappa*tau
       + alpha_M*tau*(i mod 7)
       + (2/7)*tau*floor(i/7)
       + (q mod 5)*tau/7] mod tau.

Thus

    phi_i(q)=B_i+delta(q) mod tau

with q-dependence independent of i.

Therefore every pairwise recovered-glossary difference is a common phase shift

    Delta phi = Delta * (1,1,...,1).

A full 115-record audit found:
- six quark-prime labels: 3,5,7,11,13,17;
- four unique 36D vectors;
- one recovered formula;
- maximum pairwise non-uniformity of the common shift ~7.82e-11;
- q mod 5 shift agreement error ~1.21e-12;
- common-template error after shift removal ~7.70e-11.

If, only as a negative control, this uniform difference is forcibly reshaped
row-major into a 6x6 matrix,

    X_legacy = Delta * Ones_(6x6).

For the calibrated orbital generator J_36,

    sum J_36[r,c]=0,

hence

    <X_legacy,J_36>_F=0.

So every nonzero recovered legacy common shift has best-fit physical x-y twist

    theta_hat=0

with a strictly nonzero off-axis residual.

Consequently the recovered glossary phase-marker family is not the typed
physical SO(2) log-phase carrier.

## 4. Typed Moire phase basis

Introduce the candidate basis identity

    PNV_MOIRE_RELATIVE_PHASE_MATRIX6_ROW_MAJOR_V1.

Carrier:
- exactly 36 finite phase angles in [0,2pi);
- row-major indexing of a 6x6 matrix;
- matrix role: principal wrapped Lie-coordinate generator on Lambda^2(R^4);
- pair basis downstream:
  (01,02,03,23,31,12).

This basis is distinct from the generic PNCS T36 basis.

## 5. SO(2) orbital specialization

For the physical x-y rotation generator J_36,

    X(theta)=theta J_36.

The typed phase record stores

    phase_ij = X_ij mod 2pi.

For |theta|<pi, principal unwrapping recovers X(theta) exactly.

The adapter estimates

    theta_hat=<X,J_36>_F/<J_36,J_36>_F

and admits only if

    ||X-theta_hat J_36||_F <= epsilon

for an explicit tolerance.

The admitted target is

    PNV_BIVECTOR_OPERATOR36_LAMBDA2_R4_PAIRBASIS_V1.

## 6. Physical calibration

For the admitted target

    rho_36(theta)=Lambda^2 R_xy(theta),

    tr rho_36(theta)=2+4cos(theta),

and

    [6-tr rho_36(theta)]/2
      =4sin^2(theta/2).

For an identical-lattice Moire system,

    L_M=a/[2sin(|theta|/2)],

therefore

    [6-tr rho_36]/2=(a/L_M)^2.

The forward measurement path is also defined:

    (a,L_M)
      -> principal |theta|
      -> typed Moire log-phase T36
      -> Bivector36.

Orientation sign requires an independent handedness/orientation witness.

## 7. Binding object

A binding MUST record at least:

    source_basis_id
    source_derivation_id
    source_id/reference_id
    adapter_id
    target_basis_id
    theta_radians
    generator_fit_abs
    generator_fit_rel
    tolerance
    branch_cut_policy
    provenance source
    canon_allowed=false

The binding is invalid if the source basis is the generic
PNV_T36_PHASE_ANGLES_RADIANS_V1 unless a separate source-owned basis conversion
has already been established.

The recovered glossary formula itself does not provide such a conversion; it
provides a global-phase family analytically orthogonal to the calibrated
J_36 axis under the historical row-major negative control.

## 8. Live Phi boundary

The live /dev/shm/ciel_noema phi, aux_phi and aux_feedback_phi surfaces are
generic PhaseNav runtime state unless their basis metadata proves otherwise.

A live generic phi snapshot was explicitly admission-tested and rejected before
physical conversion. This is the required fail-closed behavior.

## 9. Promotion gate

Promotion requires:
1. exact basis identity;
2. exact 36-angle validation;
3. provenance-bound derivation identity;
4. off-axis rejection;
5. branch-cut rejection;
6. roundtrip theta recovery;
7. Bivector36 group-law validation;
8. physical Moire geometry calibration;
9. explicit proof that any proposed live source uses the typed basis.

No item may be replaced by dimension matching alone.

Recovered legacy glossary -> physical Bivector36 SO(2) is currently classified:

    NO_GO_UNDER_RECOVERED_PHASE_MARKER_FORMULA.
