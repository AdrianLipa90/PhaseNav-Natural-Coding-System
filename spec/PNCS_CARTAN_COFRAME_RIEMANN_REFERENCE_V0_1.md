# PNCS Cartan Coframe -> Riemann Reference v0.1
Date: 2026-09-26
Status: CANDIDATE / ANALYTIC_GEOMETRY_BINDING / NON-CANON

For the declared reference coframe

    e=(dt,e^sigma dx,e^sigma dy,dz),

with sigma=a(x^2+y^2), the torsion-free Cartan connection satisfies

    T^a=de^a+omega^a_b wedge e^b=0.

Its curvature 2-form satisfies

    Omega^1_2=-(Delta sigma)dx wedge dy.

Using

    R^rho_{ sigma mu nu}
      =e_a^rho Omega^a_{b mu nu}e^b_sigma

reproduces the coordinate Riemann tensor independently calculated from the
metric g=e^T eta e.

For the reference:

    R^x_{ yxy}=-4a,

    R_scalar=-8a exp(-2sigma).

Shrinking-loop spin holonomy converges to the same curvature.

Independent validation: PASS.

This is a reference theorem/check for the declared geometry, not a physical
gravity-source law.

canon_allowed=false
