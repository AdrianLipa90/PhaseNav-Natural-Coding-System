# PNCS Lorentz Connection Curvature v0.1
Date: 2026-09-26
Status: CANDIDATE / GAUGE_CURVATURE / NON-CANON

Connection:

    A_mu in so(1,3).

Field strength:

    F_mu_nu
      =partial_mu A_nu
       -partial_nu A_mu
       +[A_mu,A_nu].

Shrinking-loop gate:

    H(h)
      =I+h^2F_mu_nu+O(h^3)

for the explicitly declared loop orientation and constant-connection control.

Orientation reversal flips the leading sign. Commuting connection is a zero
control.

Bivector36 representation:

    d(Lambda^2)(F_mu_nu)

and Lie brackets are preserved.

Independent validation: PASS.

This establishes Lorentz gauge curvature, not yet the spacetime Riemann tensor.
A coframe + torsion/spin-connection binding is mandatory before that promotion.

canon_allowed=false
