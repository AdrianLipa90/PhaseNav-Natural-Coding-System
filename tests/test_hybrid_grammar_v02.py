import pytest

from phasenav_natural_code.hybrid_grammar_v02 import (
    HybridGrammarError,
    compile_hybrid_program,
)
from phasenav_natural_code.quantum_gate_language_v01 import (
    compile_quantum_gate_program,
)


def test_browser_style_semantic_program_compiles_to_typed_ir():
    source = """
PROGRAM browser_demo
TASK search
INPUT query : QUERY
FIND pages : SET<PAGE> FROM web.index RELATED_TO query
FILTER verified : SET<PAGE> FROM pages BY verified_source
COMPUTE ranked : LIST<PAGE> USING semantic_rank INPUT verified query MODE AUTO
REQUIRE verified_source ON compute.ranked
RETURN ranked
"""
    compiled = compile_hybrid_program(source)
    assert compiled.program_id == "browser_demo"
    assert compiled.return_symbols == ("ranked",)
    assert compiled.has_external_effects is False
    assert compiled.to_ir()["effect_policy"]["actuation_performed"] is False
    assert {s.name: s.type_name for s in compiled.symbols}["ranked"] == "LIST<PAGE>"


def test_quantum_block_reuses_exact_quantum_gate_language_qir():
    source = """
PROGRAM hybrid_quantum
TASK solve
QUANTUM BEGIN local_z QUBITS 1000000 MODE RESULT_DIRECTED
GATE H q0
GATE CZ q0 q1
GATE CZ q1 q2
GATE CZ q2 q3
GATE CZ q3 q4
GATE CZ q4 q5
GATE CZ q5 q6
GATE CZ q6 q7
OBSERVE Z q7
QUANTUM END
OBSERVE score : REAL FROM local_z
RETURN score
"""
    compiled = compile_hybrid_program(source)
    binding = compiled.quantum_bindings[0]

    q_source = """PROGRAM local_z
QUBITS 1000000
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
    direct = compile_quantum_gate_program(q_source)
    assert binding.compiled.qir_sha256 == direct.qir_sha256
    observe = next(n for n in compiled.nodes if n.kind == "OBSERVE")
    assert observe.attributes["qir_sha256"] == direct.qir_sha256


def test_effect_and_persist_are_never_self_authorized():
    source = """
PROGRAM guarded_effects
TASK publish
INPUT result : DOCUMENT
PERSIST result AS library/search/latest REQUIRE storage_write
EFFECT show USING browser.render INPUT result REQUIRE user_authorization
RETURN result
"""
    compiled = compile_hybrid_program(source)
    effects = [n for n in compiled.nodes if n.external_effect]
    assert len(effects) == 2
    assert all(n.execution_authorized is False for n in effects)
    assert compiled.has_external_effects is True
    assert compiled.all_external_effects_authorized is False
    assert compiled.to_ir()["effect_policy"]["actuation_performed"] is False


def test_when_requires_boolean_symbol():
    bad = """
PROGRAM bad_when
INPUT query : QUERY
WHEN query ENABLE compute.answer
COMPUTE answer : TEXT USING echo INPUT query MODE AUTO
RETURN answer
"""
    with pytest.raises(HybridGrammarError):
        compile_hybrid_program(bad)


def test_when_and_parallel_validate_node_references():
    source = """
PROGRAM guarded_parallel
INPUT ok : BOOLEAN
INPUT a : TEXT
COMPUTE left : TEXT USING echo INPUT a MODE CLASSICAL_PREFERRED
COMPUTE right : TEXT USING echo INPUT a MODE CLASSICAL_PREFERRED
WHEN ok ENABLE compute.left
PARALLEL twins : compute.left compute.right
RETURN left right
"""
    compiled = compile_hybrid_program(source)
    assert any(n.kind == "WHEN" for n in compiled.nodes)
    assert any(n.kind == "PARALLEL" for n in compiled.nodes)


def test_quantum_required_must_reference_declared_quantum_kernel():
    bad = """
PROGRAM bad_quantum
COMPUTE score : REAL USING imaginary_kernel MODE QUANTUM_REQUIRED
RETURN score
"""
    with pytest.raises(HybridGrammarError):
        compile_hybrid_program(bad)


def test_quantum_kernel_symbolic_inputs_fail_closed_in_v02():
    bad = """
PROGRAM bad_qinput
INPUT x : REAL
QUANTUM BEGIN qk QUBITS 2 MODE RESULT_DIRECTED
GATE H q0
OBSERVE Z q0
QUANTUM END
COMPUTE y : REAL USING qk INPUT x MODE QUANTUM_REQUIRED
RETURN y
"""
    with pytest.raises(HybridGrammarError):
        compile_hybrid_program(bad)


def test_unknown_symbols_fail_closed():
    bad = """
PROGRAM bad_symbol
COMPUTE y : REAL USING add INPUT missing MODE AUTO
RETURN y
"""
    with pytest.raises(HybridGrammarError):
        compile_hybrid_program(bad)


def test_return_is_terminal():
    bad = """
PROGRAM bad_return
INPUT x : TEXT
RETURN x
COMPUTE y : TEXT USING echo INPUT x MODE AUTO
"""
    with pytest.raises(HybridGrammarError):
        compile_hybrid_program(bad)


def test_ir_hash_is_deterministic():
    source = """PROGRAM deterministic
TASK t
INPUT q : QUERY
FIND pages : SET<PAGE> FROM web.index RELATED_TO q
RETURN pages
"""
    a = compile_hybrid_program(source)
    b = compile_hybrid_program(source)
    assert a.ir_sha256 == b.ir_sha256
    assert a.to_dict() == b.to_dict()


def test_unknown_statement_fails_closed():
    with pytest.raises(HybridGrammarError):
        compile_hybrid_program(
            "PROGRAM no_magic\nTELEPORT x TO y\n"
        )
