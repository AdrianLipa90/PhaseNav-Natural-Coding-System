# PNCS Einstein Geometric Reference v0.1
Date: 2026-09-26
Status: CANDIDATE / GEOMETRIC_EINSTEIN_TENSOR / NON-CANON

For the validated Cartan/Riemann reference, construct

    G_mu_nu
      =Ric_mu_nu
       -1/2 g_mu_nu R.

The implementation independently checks:
- Ricci contraction;
- scalar curvature;
- Einstein tensor symmetry;
- trace identity G^mu_mu=-R;
- contracted Bianchi identity

      nabla_mu G^mu_nu=0.

Validation: PASS.

This specification does not define T_mu_nu, kappa or Lambda.

A future source binding must be independently typed and physically calibrated;
T=G/kappa is not accepted as evidence of a source mechanism by itself.

canon_allowed=false
