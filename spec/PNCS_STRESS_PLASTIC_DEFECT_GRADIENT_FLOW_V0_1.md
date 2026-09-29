# PNCS Stress–Plastic–Defect Gradient Flow v0.1
Date: 2026-09-26
Status: CANDIDATE / THERMODYNAMIC_COUPLING / NON-CANON

Internal state:

    beta_p

with

    eps_e=sym(Grad u-beta_p).

Free energy:

    psi
      =mu|eps_e|^2
       +lambda/2[tr eps_e]^2
       +H/2|beta_p|^2.

Stress:

    sigma=2mu eps_e+lambda tr(eps_e)I.

Conjugate force:

    Y=sigma-H beta_p=-delta psi/delta beta_p.

Onsager flow:

    beta_p_dot=M Y,
    M>=0.

Therefore at fixed total strain:

    dpsi/dtau=-M|Y|^2<=0.

The local flow is solved exactly by symmetric-deviatoric, spherical and skew
sector decomposition.

Project defect convention:

    alpha=Curl beta_p.

Independent replay:

    8/8 PASS.

This remains a small-strain viscous-plastic reference. Finite-strain
multiplicative plasticity is a separate future gate.

canon_allowed=false
