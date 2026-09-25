import pytest

from phasenav_natural_code.quantum_gate_language_v01 import (
    QuantumGateLanguageError,
    compile_quantum_gate_program,
)


def test_compile_googol_extent_result_directed_program():
    source = """
    PROGRAM googol_local_z
    QUBITS 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
    MODE RESULT_DIRECTED
    GATE H q0
    GATE CZ q0 q1
    GATE CZ q1 q2
    GATE CZ q2 q3
    GATE CZ q3 q4
    GATE CZ q4 q5
    GATE CZ q5 q6
    GATE CZ q6 q7
    OBSERVE Z q7
    """
    compiled = compile_quantum_gate_program(source)
    assert compiled.logical_qubits == 10**100
    assert compiled.mode == "RESULT_DIRECTED"
    assert compiled.qir_payload["observable"] == {"pauli": "Z", "qubits": [7]}
    assert len(compiled.qir_payload["gates"]) == 8


def test_compilation_is_deterministic():
    source = """PROGRAM p
QUBITS 2
MODE RESULT_DIRECTED
GATE H q0
GATE CZ q0 q1
OBSERVE Z q1
"""
    a = compile_quantum_gate_program(source)
    b = compile_quantum_gate_program(source)
    assert a.qir_sha256 == b.qir_sha256
    assert a.to_dict() == b.to_dict()


@pytest.mark.parametrize(
    "source",
    [
        "PROGRAM p\nQUBITS 2\nMODE RESULT_DIRECTED\nGATE Y q0\nOBSERVE Z q0\n",
        "PROGRAM p\nQUBITS 2\nMODE RESULT_DIRECTED\nGATE H q2\nOBSERVE Z q0\n",
        "PROGRAM p\nQUBITS 2\nMODE RESULT_DIRECTED\nGATE RZ q0 nope\nOBSERVE Z q0\n",
        "PROGRAM p\nQUBITS 2\nMODE RESULT_DIRECTED\nGATE H q0\n",
    ],
)
def test_invalid_programs_fail_closed(source):
    with pytest.raises(QuantumGateLanguageError):
        compile_quantum_gate_program(source)
