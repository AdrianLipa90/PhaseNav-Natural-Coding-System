import itertools
import pytest

from phasenav_natural_code.ternary_stella_v03 import (
    Stella3,
    TernaryStellaError,
    pack_codes_5bit,
    quantize_weight,
    route_choice_full,
    route_choice_sign,
    route_choice_stella3,
    shell_counts,
    theoretical_storage_bits,
    unpack_codes_5bit,
)


def test_exact_state_count_and_shell_decomposition():
    states = {Stella3(*digits).code for digits in itertools.product((-1, 0, 1), repeat=3)}
    assert len(states) == 27
    assert states == set(range(27))
    assert shell_counts() == {"CENTER": 1, "AXIS": 6, "EDGE": 12, "CORNER": 8}


def test_balanced_levels_round_trip_all_27_states():
    for level in range(-13, 14):
        s = Stella3.from_level(level)
        assert s.level == level
        assert Stella3.from_code(s.code) == s
        assert s.code == level + 13


def test_three_trits_are_not_misreported_as_one_trit():
    assert len({Stella3(t, 0, 0).d0 for t in (-1, 0, 1)}) == 3
    assert len({Stella3(*x).code for x in itertools.product((-1, 0, 1), repeat=3)}) == 27


def test_weight_quantization_error_is_bounded_inside_scale():
    scale = 2.0
    for i in range(-200, 201):
        w = i / 100.0
        q = quantize_weight(w, scale=scale)
        assert q.absolute_error <= scale / 26 + 1e-12


def test_sign_only_is_an_intentionally_weak_baseline():
    weights = {"a": 0.1, "b": 0.9}
    assert route_choice_full(weights) == "b"
    assert route_choice_sign(weights) == "a"
    assert route_choice_stella3(weights)[0] == "b"


def test_stella_routing_preserves_clear_ordering():
    weights = {"a": -0.8, "b": 0.15, "c": 0.91, "d": 0.2}
    selected, q = route_choice_stella3(weights)
    assert selected == route_choice_full(weights) == "c"
    assert q["c"].stella.level > q["d"].stella.level


def test_5bit_pack_round_trip():
    states = tuple(Stella3.from_code(i) for i in range(27))
    payload = pack_codes_5bit(states)
    assert len(payload) == 17
    assert unpack_codes_5bit(payload, len(states)) == states


def test_invalid_5bit_code_fails_closed():
    with pytest.raises(TernaryStellaError):
        unpack_codes_5bit(bytes([31]), 1)


def test_theoretical_storage_is_labelled_not_python_object_size():
    x = theoretical_storage_bits(100)
    assert x["float64_weights"] == 6400
    assert x["stella3_binary_pack"] == 500
    assert x["stella3_shannon_floor"] < 500


def test_quantization_clips_only_outside_declared_scale():
    q = quantize_weight(5.0, scale=1.0)
    assert q.stella.level == 13
    assert q.reconstructed == 1.0


def test_hybrid_memory_grammar_admits_ternary_stella_as_representation_not_substrate():
    from phasenav_natural_code.hybrid_memory_grammar_v03 import compile_hybrid_memory_program
    src = """PROGRAM ternary_memory
INPUT x : TEXT
MEMORY m RETAINS PATH PERSISTENCE STRUCTURAL ACCESS IMPLICIT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC HYPOTHESIS
REPRESENT m AS TERNARY_STELLA EPSILON 0.05 HORIZON 100 OBSERVABLE route_choice COST STORAGE QUERY_TIME EVIDENCE FORMAL_ONLY
RETURN x
"""
    ir = compile_hybrid_memory_program(src).to_ir()
    rep = ir["memory_model"]["representations"][0]
    assert rep["representation_family"] == "ternary_stella"
    assert rep["physical_substrate_claim"] is False


def test_canonical_representation_planner_can_compare_ternary_to_binary():
    from phasenav_natural_code.representation_planner_v03 import (
        EquivalenceContract,
        RepresentationCandidate,
        ResourceVector,
        select_representation,
    )
    contract = EquivalenceContract(0.05, 100, "route_choice", "bounded_output_distance")
    ternary = RepresentationCandidate(
        "ternary", "TERNARY_STELLA", contract,
        ResourceVector(5, 1, 1, 1, 1, 1), "FORMAL_ONLY"
    )
    binary = RepresentationCandidate(
        "binary", "BINARY", contract,
        ResourceVector(64, 1, 1, 1, 1, 1), "PARITY"
    )
    decision = select_representation([binary, ternary], contract, weights={"storage": 1})
    assert decision.selected.candidate_id == "ternary"
    assert decision.to_dict()["physical_quantum_claim"] is False
