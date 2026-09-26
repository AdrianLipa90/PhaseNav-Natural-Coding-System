# PNCS GL(3) Deformation Bivector36 Binding v0.1
Date: 2026-09-26
Status: CANDIDATE / TYPED_GL3_BINDING / NON-CANON

## Representation

For invertible spatial deformation F in GL(3),

    E(F)=diag(1,F),

and in the pair basis (01,02,03,23,31,12),

    rho_36(F)=Lambda^2 E(F)
             =diag(F,cof(F)),

with

    cof(F)=det(F)F^{-T}.

The upper block recovers F exactly. The lower block is a deterministic
consistency witness.

Admission requires:
- invertible upper F block;
- zero off-block terms;
- lower block equal to cof(F) within explicit tolerance.

## SO(3) specialization

For R in SO(3),

    cof(R)=R,

so the binding reduces exactly to the existing spatial SO(3) carrier.

## General planar Moire geometry

For direct primitive matrix A and layer-2 deformation F_2,

    A_2=F_2 A,
    B=2pi A^{-T},
    B_2=F_2^{-T}B,
    Delta B=(F_2^{-T}-I)B.

If Delta B is invertible,

    A_M=2pi(Delta B)^{-T}.

This one expression covers:
- twist;
- isotropic lattice mismatch;
- anisotropic strain;
- shear.

Checks:
- pure rotation recovers L_M=a/[2sin(|theta|/2)] for a hexagonal lattice;
- isotropic F=sI gives primitive scale |s/(s-1)|a.

## Validation

Independent algebraic replay:

    7/7 PASS.

No elastic-energy law, nonlinear defect theory, curvature or generic live-T36
binding is introduced by this gate.

canon_allowed=false
