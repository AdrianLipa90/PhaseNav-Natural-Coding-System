# PNCS Quantum Gate Language v0.1

Status: `CANDIDATE_ONLY / BACKEND_NEUTRAL / FAIL_CLOSED`

This is a deliberately small gate language for result-directed PhaseNav computation.

## Grammar

```text
PROGRAM <id>
QUBITS <positive integer>
MODE RESULT_DIRECTED | FULL_STATE

GATE H <q>
GATE X <q>
GATE RZ <q> <theta>
GATE PHASE <q> <theta>
GATE CNOT <control> <target>
GATE CZ <control> <target>

OBSERVE <PauliWord> <q0> ... <qn>
```

Qubit references use `q<non-negative-integer>`.

Example:

```text
PROGRAM local_z
QUBITS 1000000
MODE RESULT_DIRECTED

GATE H q0
GATE CZ q0 q1
GATE CZ q1 q2
GATE CZ q2 q3

OBSERVE Z q3
```

The language does **not** imply that all declared logical qubits are hydrated or simultaneously represented. Under `RESULT_DIRECTED`, the program compiles to `PHASENAV_QUANTUM_GATE_IR_V1`; PhaseNav then computes the exact conservative backward causal cone before hydration.

## Design constraints

1. No backend names in the source language.
2. No silent approximation.
3. Unsupported gates fail closed.
4. The requested observable is part of the QIR digest.
5. Global logical extent and active workspace are distinct quantities.
6. QPU/Q28/QHTRI parity is tested after compilation against the same QIR hash.

This v0.1 intentionally admits only the gate subset already supported by the current Q28 path either natively or through exact `CZ -> H,CNOT,H` lowering.
