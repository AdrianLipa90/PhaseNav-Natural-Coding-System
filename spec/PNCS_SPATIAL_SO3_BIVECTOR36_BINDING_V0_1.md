# PNCS Spatial SO(3) Bivector36 Binding v0.1
Date: 2026-09-26
Status: CANDIDATE / TYPED_SO3_BINDING / NON-CANON

## 1. Target carrier

Target basis:

    PNV_BIVECTOR_OPERATOR36_LAMBDA2_R4_PAIRBASIS_V1

with pair basis

    (01,02,03,23,31,12).

For a physical spatial rotation R in SO(3),

    E(R)=diag(1,R)

and

    rho_36(R)=Lambda^2 E(R).

In the declared pair basis,

    rho_36(R)=diag(R,R).

Thus the 36 coefficients do not represent 36 independent physical axes.
They represent one 6x6 operator carrying two equivalent SO(3) vector blocks.

## 2. Lie algebra

For rotation vector omega,

    J_36(omega)=diag([omega]_x,[omega]_x).

The unit-axis generators obey

    [J_x,J_y]=J_z,
    [J_y,J_z]=J_x,
    [J_z,J_x]=J_y.

The prior planar Moire calibration is the z-axis subgroup.

## 3. Typed source phase basis

Candidate source basis:

    PNV_SPATIAL_SO3_LOG_PHASE_MATRIX6_ROW_MAJOR_V1.

It stores wrapped row-major coefficients of J_36(omega).

For ||omega||<pi, principal unwrapping followed by projection onto

    span{J_x,J_y,J_z}

recovers omega exactly for on-subspace records.

Generic PNV_T36_PHASE_ANGLES_RADIANS_V1 remains rejected.

## 4. Invariant

For any rotation axis and angle theta,

    tr rho_36 = 2+4cos(theta),

so

    D_rot=[6-tr rho_36]/2
         =4sin^2(theta/2).

Axis information is retained in the operator blocks.

## 5. Moire specialization

For two planar identical lattices, the usual homobilayer Moire formula applies
only when the relative rotation axis is the common layer normal.

Then the SO(3) binding reduces to the calibrated SO(2) subgroup:

    D_rot=(a/L_M)^2.

Arbitrary 3D tilt is not silently converted to a planar Moire wavelength.

## 6. Validation

Independent algebraic/control replay:

    8/8 PASS.

Covered:
- exact diag(R,R) exterior-square structure;
- so(3) generator commutator;
- axis-independent trace residual;
- exact z-axis compatibility with the earlier SO(2) carrier;
- axis-angle inverse;
- typed rotation-vector log-phase roundtrip;
- generic T36 rejection contract;
- off-subspace rejection control.

canon_allowed=false
