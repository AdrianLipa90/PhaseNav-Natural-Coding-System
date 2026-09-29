# PNCS Finite-Strain Multiplicative Plasticity v0.1
Date: 2026-09-26
Status: CANDIDATE / GL_PLUS_3_DYNAMICS / NON-CANON

Kinematics:

    F=F_e F_p,
    F_e=F F_p^{-1},
    F,F_e,F_p in GL+(3).

Elastic free energy is the objective compressible neo-Hookean energy evaluated
on F_e.

Define Mandel stress

    M=F_e^T P_e.

Candidate viscous plastic flow:

    L_p
      =m_dev dev(sym M)
       +m_vol mean(M)I,

    dot(F_p)=L_p F_p,

with nonnegative mobilities.

At fixed F:

    dot(psi)
      =-M:L_p
      =-m_dev|dev M|^2
       -3m_vol mean(M)^2
      <=0.

Use multiplicative exponential update

    F_p^{n+1}=exp(dt L_p)F_p^n,

which preserves GL+(3).

For m_vol=0, tr L_p=0 and plastic volume is preserved.

Independent validation/crosscheck: PASS.

The previous additive beta_p model is retained as the small-strain limit, not
silently deleted.

canon_allowed=false
