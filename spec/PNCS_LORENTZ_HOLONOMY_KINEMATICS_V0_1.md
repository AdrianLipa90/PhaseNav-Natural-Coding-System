# PNCS Lorentz Holonomy Kinematics v0.1
Date: 2026-09-26
Status: CANDIDATE / GAUGE_HOLONOMY / NON-CANON

Lorentz links U_ba transport internal vectors between vertices.

Path composition:

    H=U_n...U_1.

Bivector36 transport:

    H_6=Lambda^2(H).

Pure-gauge links generated from vertex frames,

    U_ba=G_bG_a^{-1},

must give identity on every closed loop.

Under vertex gauge transformations,

    U_ba->H_bU_baH_a^{-1},

so a loop based at 0 transforms by conjugation

    H_loop->H_0H_loopH_0^{-1}.

Lorentz Lie generators and their induced Bivector36 generators preserve eta
and G_(3,3), respectively.

Independent validation: PASS.

Nontrivial loop holonomy is retained as a gauge witness only. Curvature
promotion requires a shrinking-loop limit.

canon_allowed=false
