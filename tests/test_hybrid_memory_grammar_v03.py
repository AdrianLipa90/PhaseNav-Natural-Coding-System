import pytest

from phasenav_natural_code.hybrid_memory_grammar_v03 import (
    HybridMemoryGrammarError,
    compile_hybrid_memory_program,
)


def _procedural_prefix():
    return """
MEMORY fast_context RETAINS STATE RELATION PERSISTENCE TRANSIENT ACCESS DIRECT PLASTICITY VOLATILE EFFECT BIAS EPISTEMIC FORMAL_EXAMPLE
MEMORY search_skill RETAINS PATH TOPOLOGY OPERATOR PERSISTENCE STRUCTURAL ACCESS IMPLICIT RECONSTRUCTIVE PLASTICITY ADAPTIVE CONSOLIDATING EFFECT ROUTING ATTRACTOR EPISTEMIC FORMAL_EXAMPLE
REPRESENT search_skill AS QUANTUM_NATIVE EPSILON 0.001 HORIZON 100 OBSERVABLE trajectory_choice COST STORAGE UPDATE_TIME QUERY_TIME SAMPLE_COUNT SEQUENTIAL_DEPTH EVIDENCE FORMAL_ONLY PHYSICAL_QUANTUM FALSE
LAW search_learning FOR search_skill USING path_reinforcement
"""


def test_procedural_memory_modifies_future_execution_graph():
    source = """PROGRAM memory_browser
TASK search
INPUT query : QUERY
FIND pages : SET<PAGE> FROM web.index RELATED_TO query
FILTER verified : SET<PAGE> FROM pages BY verified_source
COMPUTE ranked : LIST<PAGE> USING semantic_rank INPUT verified query MODE AUTO
""" + _procedural_prefix() + """
EVENT success FROM ranked
TRACE success_trace FROM success INTO search_skill LAW search_learning
ROUTE search_route : find.pages filter.verified compute.ranked
REINFORCE search_route INTO search_skill MODE ADAPTIVE LAW search_learning
GUIDE compute.ranked USING search_skill
COUPLE fast_context TO search_skill MODE CONSOLIDATE TIMESCALE slow
RETURN ranked
"""
    compiled = compile_hybrid_memory_program(source)
    ir = compiled.to_ir()
    mem = ir["memory_model"]
    skill = next(x for x in mem["objects"] if x["memory_id"] == "search_skill")
    assert skill["retained_objects"] == ["path", "topology", "operator"]
    assert skill["persistence"] == "structural"
    kinds = [x["kind"] for x in mem["operations"]]
    assert {"EVENT", "TRACE", "PATH", "REINFORCE", "GUIDE", "COUPLE", "LAW"} <= set(kinds)
    guide = next(x for x in mem["operations"] if x["kind"] == "GUIDE")
    assert guide["attributes"]["direct_retrieval"] is False
    assert guide["attributes"]["changes_future_transition_policy"] is True


def test_representation_is_separate_from_memory_ontology():
    source = """PROGRAM rep_split
INPUT x : TEXT
MEMORY m RETAINS PATH PERSISTENCE PERSISTENT ACCESS IMPLICIT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC HYPOTHESIS
REPRESENT m AS QUANTUM_NATIVE EPSILON 0.01 HORIZON 10 OBSERVABLE next_step COST STORAGE QUERY_TIME EVIDENCE FORMAL_ONLY
RETURN x
"""
    ir = compile_hybrid_memory_program(source).to_ir()
    obj = ir["memory_model"]["objects"][0]
    rep = ir["memory_model"]["representations"][0]
    assert "representation_family" not in obj
    assert rep["representation_family"] == "quantum_native"
    assert rep["physical_substrate_claim"] is False


def test_reconstructive_recall_has_explicit_provenance():
    source = """PROGRAM recall_demo
MEMORY m RETAINS RELATION PATH PERSISTENCE PERSISTENT ACCESS RECONSTRUCTIVE PLASTICITY ADAPTIVE EFFECT GENERATIVE EPISTEMIC FORMAL_EXAMPLE
RECALL path : PATH FROM m MODE RECONSTRUCTIVE PROVENANCE RECONSTRUCTED
COMPUTE text : TEXT USING explain INPUT path MODE AUTO
RETURN text
"""
    ir = compile_hybrid_memory_program(source).to_ir()
    access = ir["memory_model"]["accesses"][0]
    assert access["type"] == "PATH"
    assert access["provenance_class"] == "RECONSTRUCTED"
    node = next(x for x in ir["nodes"] if x["node_id"] == "input.path")
    assert node["kind"] == "MEMORY_ACCESS"
    assert node["output_type"] == "PATH"


def test_implicit_memory_cannot_be_recalled_as_record():
    source = """PROGRAM bad_implicit
MEMORY m RETAINS PATH PERSISTENCE STRUCTURAL ACCESS IMPLICIT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC FORMAL_EXAMPLE
RECALL p : PATH FROM m MODE IMPLICIT
RETURN p
"""
    with pytest.raises(HybridMemoryGrammarError):
        compile_hybrid_memory_program(source)


def test_direct_and_reconstructive_provenance_cannot_be_mislabeled():
    source = """PROGRAM bad_prov
MEMORY m RETAINS STATE PERSISTENCE PERSISTENT ACCESS DIRECT PLASTICITY ADAPTIVE EFFECT BIAS EPISTEMIC FORMAL_EXAMPLE
RECALL x : STATE FROM m MODE DIRECT PROVENANCE RECONSTRUCTED
RETURN x
"""
    with pytest.raises(HybridMemoryGrammarError):
        compile_hybrid_memory_program(source)


def test_reinforce_requires_path_retention():
    source = """PROGRAM bad_path
INPUT x : TEXT
COMPUTE y : TEXT USING echo INPUT x MODE AUTO
MEMORY m RETAINS STATE PERSISTENCE STRUCTURAL ACCESS IMPLICIT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC FORMAL_EXAMPLE
ROUTE r : input.x compute.y
REINFORCE r INTO m MODE ADAPTIVE
RETURN y
"""
    with pytest.raises(HybridMemoryGrammarError):
        compile_hybrid_memory_program(source)


def test_reinforce_mode_must_be_declared_plasticity():
    source = """PROGRAM bad_plasticity
INPUT x : TEXT
COMPUTE y : TEXT USING echo INPUT x MODE AUTO
MEMORY m RETAINS PATH PERSISTENCE STRUCTURAL ACCESS IMPLICIT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC FORMAL_EXAMPLE
ROUTE r : input.x compute.y
REINFORCE r INTO m MODE CONSOLIDATING
RETURN y
"""
    with pytest.raises(HybridMemoryGrammarError):
        compile_hybrid_memory_program(source)


def test_route_references_real_execution_nodes():
    source = """PROGRAM bad_route
INPUT x : TEXT
MEMORY m RETAINS PATH PERSISTENCE STRUCTURAL ACCESS IMPLICIT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC FORMAL_EXAMPLE
ROUTE r : input.x compute.missing
RETURN x
"""
    with pytest.raises(HybridMemoryGrammarError):
        compile_hybrid_memory_program(source)


def test_quantum_native_profile_cannot_self_assert_physical_quantum_necessity():
    source = """PROGRAM bad_physical
INPUT x : TEXT
MEMORY m RETAINS PATH PERSISTENCE STRUCTURAL ACCESS IMPLICIT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC HYPOTHESIS
REPRESENT m AS QUANTUM_NATIVE EPSILON 0.01 HORIZON 10 OBSERVABLE next_step COST STORAGE EVIDENCE PHYSICAL_QUANTUM_NECESSITY PHYSICAL_QUANTUM TRUE
RETURN x
"""
    with pytest.raises(HybridMemoryGrammarError):
        compile_hybrid_memory_program(source)


def test_coupling_is_directional_and_memory_typed():
    source = """PROGRAM coupling
INPUT x : TEXT
MEMORY fast RETAINS STATE PERSISTENCE TRANSIENT ACCESS DIRECT PLASTICITY VOLATILE EFFECT BIAS EPISTEMIC FORMAL_EXAMPLE
MEMORY slow RETAINS PATH TOPOLOGY PERSISTENCE STRUCTURAL ACCESS IMPLICIT PLASTICITY CONSOLIDATING EFFECT ROUTING EPISTEMIC FORMAL_EXAMPLE
COUPLE fast TO slow MODE CONSOLIDATE TIMESCALE slow
RETURN x
"""
    ir = compile_hybrid_memory_program(source).to_ir()
    op = next(x for x in ir["memory_model"]["operations"] if x["kind"] == "COUPLE")
    assert op["attributes"]["source_memory"] == "fast"
    assert op["attributes"]["target_memory"] == "slow"
    assert op["attributes"]["relation"] == "consolidate"


def test_v02_quantum_block_still_compiles_through_same_base_path():
    source = """PROGRAM qmem
QUANTUM BEGIN local_z QUBITS 1000000 MODE RESULT_DIRECTED
GATE H q0
GATE CZ q0 q1
GATE CZ q1 q2
OBSERVE Z q2
QUANTUM END
OBSERVE score : REAL FROM local_z
MEMORY qhistory RETAINS PATH OPERATOR PERSISTENCE PERSISTENT ACCESS IMPLICIT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC FORMAL_EXAMPLE
GUIDE observe.score USING qhistory
RETURN score
"""
    compiled = compile_hybrid_memory_program(source)
    ir = compiled.to_ir()
    assert ir["quantum_bindings"][0]["qir"]["schema"] == "PHASENAV_QUANTUM_GATE_IR_V1"
    assert ir["memory_model"]["law"]["representation_is_orthogonal"] is True


def test_ir_hash_is_deterministic():
    source = """PROGRAM deterministic_memory
INPUT x : TEXT
MEMORY m RETAINS RELATION PERSISTENCE PERSISTENT ACCESS DIRECT PLASTICITY ADAPTIVE EFFECT BIAS EPISTEMIC FORMAL_EXAMPLE
EVENT e FROM x
TRACE t FROM e INTO m
RETURN x
"""
    a = compile_hybrid_memory_program(source)
    b = compile_hybrid_memory_program(source)
    assert a.ir_sha256 == b.ir_sha256
    assert a.to_dict() == b.to_dict()
