# PNCS Conservative Elastic Evolution v0.1
Date: 2026-09-26
Status: CANDIDATE / NUMERICAL_REFERENCE / NON-CANON

The linearized typed elastic field admits the periodic reference Hamiltonian

    E
      =dx sum_i [
        rho0/2 v_i^2
        +rho0 c_mode^2/2 (D_+u_i)^2
        +eta/2(D_2u_i)^2
      ].

Its exact discrete force is

    a
      =c_mode^2 D_2u
       -(eta/rho0)D_2^2u.

Time evolution uses velocity-Verlet and fails closed at or above the exact
finite-difference spectral limit

    dt_max=2/omega_max,

    omega_max^2
      =4c_mode^2/dx^2
       +16eta/(rho0 dx^4).

Every run carries an explicit kinetic/elastic/gradient/total-energy and
momentum ledger.

Independent reference replay:

    7/7 PASS.

canon_allowed=false
