# PNCS ADM Coframe + Independent Source Reference v0.1
Date: 2026-09-26
Status: CANDIDATE / TYPED_3PLUS1_BINDING / NON-CANON

Typed time-gauge coframe:

    e^0=N dt,
    e^a=E^a_i(dx^i+beta^i dt),

with

    N>0,
    E in GL+(3),
    beta in R^3.

Metric:

    h=E^T E,
    g_tt=-N^2+beta^T h beta,
    g_ti=(h beta)_i,
    g_ij=h_ij.

The previous spatial GL(3) carrier is recovered exactly for N=1,beta=0.

No generic T36 state is retyped as lapse, shift or triad.

Independent source reference:
straight string dust aligned with z,

    T_cov=diag(rho,0,0,-rho).

For the analytic conformal geometry and Lambda=0, exact source matching requires

    rho=-(4a/kappa)e^(-2sigma).

For positive kappa and standard rho>=0, this requires a<0.

The matched source is covariantly conserved when static and depends only on
x,y, but is not globally localized on the infinite transverse plane.

Independent validation: PASS.

canon_allowed=false
