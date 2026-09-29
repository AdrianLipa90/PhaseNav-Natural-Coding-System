# PNCS GL(3) Hyperelastic Field Binding v0.1
Date: 2026-09-26
Status: CANDIDATE / DYNAMICS_BINDING / NON-CANON

## Geometry

The typed deformation carrier remains

    rho_36(F)=diag(F,cof(F)),

with F in orientation-preserving GL(3).

Dynamics does not change that representation.

## Objective energy

For

    C=F^T F,
    J=det F>0,

use

    W(F)
      =mu/2[tr C-3-2ln J]
       +lambda/2(ln J)^2.

This obeys

    W(RF)=W(F)

for proper rotations R, and W(R)=0.

Stress:

    P
      =mu(F-F^{-T})
       +lambda ln(J)F^{-T}.

## Field action

For displacement u(X,tau),

    F=I+Grad u.

Candidate Lagrangian density:

    L
      =rho0/2 |u_tau|^2
       -W(F)
       -eta/2 |Grad F|^2.

Euler-Lagrange equation:

    rho0 u_tt
      =Div P
       -Div Div(eta Grad F).

## Compatibility

Row-wise

    alpha=Curl F

vanishes for smooth compatible F=Grad y.

Nonzero alpha is therefore a typed incompatibility/defect diagnostic, not an
automatic new force.

Candidate nonnegative penalty:

    W_defect=gamma/2 |Curl F|^2.

## Validation

Independent algebraic replay:

    7/7 PASS.

canon_allowed=false
