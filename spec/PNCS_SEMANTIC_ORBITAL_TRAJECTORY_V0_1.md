# PNCS Semantic Orbital Trajectory v0.1

Status: `CANDIDATE / LIFTED_PHASE_TRAJECTORY / EXPLICIT_PHASE_RATE_PROFILE`

## 1. Purpose

The single-sample semantic carrier assigns a value and an orbital band at one time. The trajectory layer checks whether a time-ordered sequence of such samples forms a phase-rate-consistent orbital oscillation.

The parent semantic value remains

\[
\mathcal S(t)=\frac{B(t)\omega(t)N(t)}{A_R(t)}(\phi(t)+\kappa).
\]

## 2. Lifted phase

For a wrapped phase `phi` and explicit winding coordinate `w`, define

\[
\boxed{\widetilde\phi=\phi+2\pi w}.
\]

PNLF already carries wrapped `phase` and separate `winding`; the trajectory layer keeps both source coordinates and uses the lifted value only for ordered phase transport.

## 3. Phase-rate consistency profile

v0.1 defines one explicit integration profile:

```text
TRAPEZOIDAL_PHASE_RATE_V0_1
```

For consecutive samples `i` and `i+1` with strictly increasing times,

\[
\Delta t_i=t_{i+1}-t_i,
\]

\[
\Delta\widetilde\phi_i=\widetilde\phi_{i+1}-\widetilde\phi_i,
\]

and the profile-integrated phase increment is

\[
\Delta\phi_{\omega,i}
=\frac{\omega_i+\omega_{i+1}}{2}\Delta t_i.
\]

The segment residual is

\[
\boxed{
R_{\phi,i}=\Delta\widetilde\phi_i-\Delta\phi_{\omega,i}.
}
\]

`R_phi = 0` is exact phase-rate consistency for the declared interpolation profile. Finite-precision admission may use an explicit non-negative tolerance carried in the receipt.

For constant `omega`, the condition reduces to

\[
\Delta\widetilde\phi=\omega\Delta t.
\]

## 4. Semantic/orbital preservation

Every point preserves its KAKU/content identity, semantic value, orbital assignment, `B`, `omega`, `N`, `A_R`, wrapped `phi`, winding, and sample time.

A trajectory requires one KAKU/content identity throughout v0.1. Cross-KAKU phase relations remain the RADICAL layer.

## 5. Oscillation receipt

A trajectory receipt records:

- ordered point receipts;
- lifted phases;
- per-segment `delta_t`;
- per-segment `delta_lifted_phase`;
- integrated phase increment from the declared profile;
- signed phase residual;
- maximum absolute residual;
- explicit tolerance;
- exact `PASS` / `FAIL` consistency result;
- candidate-only authority fields.

## 6. Validation gates

The reference implementation rejects:

1. fewer than two trajectory points;
2. non-increasing sample times;
3. mixed KAKU ids or content ids;
4. non-finite winding or tolerance;
5. negative tolerance;
6. unsupported phase-rate profile;
7. a claimed consistent trajectory whose residual exceeds tolerance.

Reference implementation: `src/phasenav_natural_code/semantic_orbital_trajectory_v01.py`.
Reference tests: `tests/test_semantic_orbital_trajectory_v01.py`.
