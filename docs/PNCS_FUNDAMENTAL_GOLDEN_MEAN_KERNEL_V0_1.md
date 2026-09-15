# PNCS Fundamental Golden-Mean Dynamics Kernel v0.1

Status: `CANDIDATE_ONLY / EXACT_SYMBOLIC_KERNEL / RUNTIME_DEFAULT_OFF / PHYSICAL_BINDING_OPEN`.

This candidate imports the executable mathematical core of the current fundamental-repository chain into PNCS without changing the existing runtime, semantic hierarchy, PhaseNav 36D realization, or any physical binding. The implementation is intentionally additive.

## Provenance

The candidate is pinned to the following upstream merges:

- IDT Collatz–Fubini–Study phase interface: `afed815f190ee5b162d1406878305a4259536af0`.
- TIR CP1 dyadic / Collatz-admissible fractal gate: `2c23cc50357c136cf21e14a8f9552a30e8496489`.
- TIR homogeneous `5|1|2` fibration: `0772bca5852194a0bf0edbe2cdd49993bb7ed5ba`.
- TIR golden-mean transfer / κ identity: `0593bfc5af98224b8f788ee958e7e011c785bf9e`.
- TIR golden-mean pressure / κ operator: `c6e282980377b43c1209ad4842b3b71e4fc394f3`.
- TIR coding conjugacy / Artin–Mazur zeta: `2097ddc26f97dfca2141e52bf53fed7d9fee2994`.
- TIR primitive-orbit Euler product: `18947402100145b5e8b88865ea90e4aab146a8dc`.
- So½ fail-closed repository holonomy: `23eae95d8cbc33782c4a819ae40b2b166b566235`.
- RFC Collatz–FS phase-fibre interface: `dbbfcc83de96246aa96217a9c40def64661474d7`.

Target base: PNCS `main` at `c031e58afe65762d2c60fad62ebf531ac0ef3f3d`.

## Executable kernel

`src/phasenav_natural_code/golden_mean_dynamics_v01.py` implements:

1. The exact unreduced-Collatz finite language `L_C={w in {0,1}*: 11 not in w}`.
2. Exact Fibonacci word counts `|L_C(k)|=F_{k+2}`.
3. A constructive witness algorithm: every finite admissible C-word is converted into `0`/`10` accelerated-map blocks and lifted through the exact parity-vector bijection to a positive integer realizing that Collatz prefix.
4. Exact finite dyadic coding using `fractions.Fraction`, with `D(q)=2q mod 1` and finite-prefix shift conjugacy.
5. The golden-mean inverse/self-similar branches `x/2` and `1/2+x/4`.
6. Transfer matrix `A=[[1,1],[1,0]]`, exact Fibonacci powers, entropy `ln(phi)`, and `dim_H K_C=log_2(phi)`.
7. The Parry maximum-entropy transition matrix and stationary distribution.
8. Weighted transfer `M(s)=2^(-s) A`, symbolic pressure `P(s)=ln(phi)-s ln(2)`, the critical dimension, and the exact normalization crosswalk `-P'(s)=24*pi*kappa` with canonical `kappa=ln(2)/(24*pi)`.
9. Lucas fixed-point counts, Möbius inversion, exact-period point counts, and primitive-orbit multiplicities.
10. Exact finite-order expansion of the primitive-orbit Euler product and comparison with the Artin–Mazur series `1/(1-z-z^2)`.
11. Weighted dynamical-zeta evaluation `1/(1-2^(-s)z-2^(-2s)z^2)`.

The existing PNCS `temporal_fibre_v1.py` is deliberately not duplicated or modified. A later candidate may explicitly compose the new symbolic phase kernel with the existing temporal-fibre machinery after a separate admission contract is written and tested.

## Mandatory type and claim firewalls

The following are invariants of this candidate:

- `RUNTIME_DEFAULT_OFF`.
- `PHYSICAL_BINDING_OPEN`.
- symbolic pressure is not thermodynamic, mechanical, gravitational, cosmological, or fluid pressure.
- Artin–Mazur zeta is not the Riemann zeta function.
- primitive/prime dynamical orbits are not arithmetic prime integers.
- the symbolic two-state transfer operator is not identified with the geometric `E7,E8` basis or the `E6` axial generator; the upstream linear-intertwiner no-go is preserved.
- the RFC metric extension remains quarantined; no metric, Einstein, Hamiltonian, energy, mass, particle, cosmological, or physical-time coupling is activated.
- the `5|1|2` fibration is retained as typed geometric provenance; it does not make the symbolic kernel a physical dimensional-reduction mechanism.
- no result here is a proof of the Collatz conjecture. The finite admissible-language theorem is local and exact; terminal-reaching claims retain their upstream boundary.

## Candidate admission

Promotion beyond candidate status requires all of the following:

1. hosted branch CI passes the dedicated golden-mean test suite;
2. all existing PNCS tests remain green;
3. provenance SHAs remain pinned or are intentionally advanced with a new receipt;
4. PhaseNav consumer integration is performed through its own repository contract and remains runtime-default-off until separately promoted;
5. no existing PNCS runtime path is modified by this candidate.

No `main` promotion is authorized by this document.
