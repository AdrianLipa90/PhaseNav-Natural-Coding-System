# PhaseNav promotion geometry v0.1 — CANDIDATE_ONLY

Status: `CANDIDATE_ONLY / RUNTIME_DEFAULT_OFF / CANON_WRITE_AUTHORITY_FALSE / EPISTEMIC_CHYBA`.

This candidate defines a single promotion contract for the finite carrier hierarchy

`H ~ R^4 ~ C^2 -> O ~ R^8 ~ C^4 -> S_16 ~ R^16 ~ C^8 -> A_32 ~ R^32 ~ C^16`.

The hypercomplex algebras are treated as state/geometry carriers. Executable gates live in the associative operator algebra on the carrier. No claim is made that octonion/sedenion multiplication itself is the quantum gate composition law.

## Core contract

For a promotion `P : E_n -> E_{n+1}`:

- metric defect: `Delta_G = P^† G_{n+1} P - G_n`;
- complex-structure defect: `Upsilon = J_{n+1} P - P J_n`;
- connection defect: `Xi = dP + A_{n+1} P - P A_n`;
- curvature defect: `Delta_F = F_{n+1} P - P F_n`.

Exact candidate admission requires the relevant defect to vanish within declared numerical tolerance.

The normalized promotion of a raw full-rank map `M` is

`P = M (M^† G_{n+1} M)^(-1/2) G_n^(1/2)`.

For a symmetric Cayley–Dickson-style doubling this reduces to the familiar factor `1/sqrt(2)`. More generally `P_chi = [alpha I; beta I]`, with `|alpha|^2 + |beta|^2 = 1`.

## Gate representation

For `U = A + iB in U(d)`, realification is

`R(U) = [[A,-B],[B,A]]`.

It preserves the real metric and commutes with the canonical real complex structure `J`. Hence the candidate execution representation uses

`U(d) ~= O(2d) ∩ Comm(J)`.

Local gate promotion is `U -> I_2 ⊗ U`, and obeys `(I_2 ⊗ U) P_chi = P_chi U`.

The module tests `X,Y,Z,H,S,T`; `CNOT` acting after a balanced promotion produces the Bell state `( |00> + |11> ) / sqrt(2)`.

## Entanglement / relational wedge

For two qubits with amplitudes `(c00,c01,c10,c11)`, the separable Segre locus is

`c00*c11 - c01*c10 = 0`.

The candidate relational scalar is

`R = 2 |c00*c11 - c01*c10|`,

which equals two-qubit concurrence for a normalized pure state. This is a precise algebraic measure; no broader physical identification is implied.

## Quantum geometric tensor

With `Pi = P P^†` and `Q = I-Pi`,

`QGT_{mu,nu} = (d_mu P)^† Q (d_nu P)`.

Its Hermitian/real part gives the quantum metric and its anti-Hermitian/imaginary part gives Berry curvature (up to convention). For the Bloch rank-1 promotion the implementation reproduces the Fubini–Study metric and Berry curvature.

## Epistemic boundary

This closes a candidate representation/execution interface for finite-dimensional unitary gates. It does **not** establish that physical spacetime, atoms, Standard-Model fields or gravity are literally Cayley–Dickson algebras. Those bindings remain independent falsification tasks.
