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

## 3. Typed Moire phase basis

Introduce the candidate basis identity

    PNV_MOIRE_RELATIVE_PHASE_MATRIX6_ROW_MAJOR_V1.

Carrier:
- exactly 36 finite phase angles in [0,2pi);
- row-major indexing of a 6x6 matrix;
- matrix role: principal wrapped Lie-coordinate generator on Lambda^2(R^4);
- pair basis downstream:
  (01,02,03,23,31,12).

This basis is distinct from the generic PNCS T36 basis.

## 4. SO(2) orbital specialization

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

## 5. Physical calibration

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

## 6. Binding object

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

## 7. Live Phi boundary

The live /dev/shm/ciel_noema phi, aux_phi and aux_feedback_phi surfaces are
generic PhaseNav runtime state unless their basis metadata proves otherwise.

This candidate does not silently retype those byte streams.

## 8. Promotion gate

Promotion requires:
1. exact basis identity;
2. exact 36-angle validation;
3. provenance-bound derivation identity;
4. off-axis rejection;
5. branch-cut rejection;
6. roundtrip theta recovery;
7. Bivector36 group-law validation;
8. physical Moire geometry calibration;
9. explicit proof that any proposed legacy/live source uses the typed basis.

No item may be replaced by dimension matching alone.
