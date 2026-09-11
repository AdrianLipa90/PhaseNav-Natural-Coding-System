# PhaseNav carrier hierarchy v0.2 — CANDIDATE_ONLY

Status: `CANDIDATE_ONLY / RUNTIME_DEFAULT_OFF / CANON_WRITE_AUTHORITY_FALSE / EPISTEMIC_CHYBA`.

This candidate extends the v0.1 promotion geometry into an executable finite carrier ladder:

`H ~ R^4 ~ C^2 -> O ~ R^8 ~ C^4 -> S_16 ~ R^16 ~ C^8 -> A_32 ~ R^32 ~ C^16`.

The corresponding projective state spaces are

`CP^1 -> CP^3 -> CP^7 -> CP^15`.

These labels describe the candidate representation carrier. They do not establish a physical ion implementation. `physical_ion_binding=OPEN` remains explicit.

## Promotion contract

At each step a normalized promotion `P : C^(2^n) -> C^(2^(n+1))` must satisfy

- `P^† P = I`;
- `Delta_G = P^† G' P - G = 0` within tolerance;
- `Upsilon = J' R(P) - R(P) J = 0` within tolerance.

The balanced family uses

`P_phi = (1/sqrt(2)) [ I ; exp(i phi) I ]`.

The current executable ceiling is 4Q / `A_32`. Calls requesting a further promotion fail closed.

## Executable gates

Single-qubit unitaries are embedded by tensor product on an explicitly selected target qubit. Multi-qubit CNOT is generated directly in the computational basis for every distinct `(control,target)` pair from 2Q through 4Q.

The old-subsystem intertwining condition is tested at every promotion step:

`(I_2 tensor U) P - P U = 0`.

This preserves the distinction between hypercomplex carrier geometry and the associative operator algebra used for executable gates.

## Entanglement gate

The validation sequence constructs exact GHZ states by repeated promotion and entangling CNOT operations:

`GHZ_n = (|0...0> + |1...1>) / sqrt(2)`, for `n=2,3,4`.

Each GHZ state is required to have Schmidt rank 2 across every nontrivial contiguous bipartition. This is an algebraic execution test only; it is not evidence that a physical 16-ion or 32-ion device has been realised.

## Admission boundary

A carrier step remains `CANDIDATE_ONLY` unless all declared metric, complex-structure, gate-intertwining, unitarity and entanglement tests pass. Runtime default and canon-write authority remain disabled independently of test success.
