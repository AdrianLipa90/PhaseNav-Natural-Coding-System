# PNCS Defect Density Transport v0.1
Date: 2026-09-26
Status: CANDIDATE / KINEMATIC_CONSERVATION / NON-CANON

The compatible elastic field and defect state remain distinct:

    F=Grad y -> Curl F=0,

while a nonzero independently admitted

    alpha

is transported as a separate defect-density state.

Reference source-free transport:

    partial_tau alpha_c + div(v alpha_c)=0

for each component under prescribed velocity.

The finite-volume reference preserves component inventory on a periodic domain
and fails closed unless

    |vx|dt/dx+|vy|dt/dy<=1.

A true Curl-derived row additionally satisfies

    div alpha_i=0,

which the constant-coefficient periodic reference preserves to roundoff.

This gate does not define stress-driven defect velocity.

Independent replay:

    7/7 PASS.

canon_allowed=false
