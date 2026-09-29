# PNCS GL(4) Coframe / Bivector36 v0.1
Date: 2026-09-26
Status: CANDIDATE / KINEMATIC_GL4_BINDING / NON-CANON

Carrier:

    rho_36(A)=Lambda^2 A,
    A in GL(4),

on the pair basis

    (01,02,03,23,31,12).

Exact identities:

    rho_36(AB)=rho_36(A)rho_36(B),

    det rho_36(A)=det(A)^3.

Spatial restriction:

    A=diag(1,F)
      -> rho_36(A)=diag(F,cof(F)).

Lorentz sector with eta=diag(-1,1,1,1):

    Lambda^T eta Lambda=eta

induces

    rho_36(Lambda)^T G rho_36(Lambda)=G,

where

    G=diag(-1,-1,-1,+1,+1,+1).

Coframe metric:

    g=e^T eta e

is invariant under internal left Lorentz action

    e->Lambda e.

Exact inverse ambiguity:

    rho_36(-A)=rho_36(A).

Therefore a Bivector36-to-coframe inverse must expose the Z2 sign ambiguity or
use an independent orientation/time-orientation witness.

Independent validation: PASS.

No connection, torsion, curvature or gravity dynamics is promoted here.

canon_allowed=false
