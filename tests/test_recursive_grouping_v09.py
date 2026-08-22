from pathlib import Path
import json
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phasenav_natural_code.surface_v09 import (
    SurfaceV09Error,
    evaluate_predicate,
    normalize_branch_surface,
    parse_predicate,
    select_route,
)

PNV = ROOT / "native" / "PNCS_RECURSIVE_GROUPING_V0_9.pnv"
LEDGER = ROOT / "mining" / "PNCS_RECURSIVE_GROUPING_LEDGER_V0_9.json"
ALLOWED = {
    "IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION","QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT","SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY","MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY","SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL","PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR","SOFT_CLIP","RESOLVE","DERIVE"
}


def rows():
    out = {}
    for raw in PNV.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        p = s.split()
        if p[0] == "OP":
            out[p[1]] = p[2:]
    return out


def ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def expect_fail(text: str):
    try:
        parse_predicate(text)
    except SurfaceV09Error:
        return
    raise AssertionError(text)


def test_v09_uses_only_recovered_pnv_opcodes():
    for key, val in rows().items():
        assert val[0] in ALLOWED, (key, val)
    assert ledger()["new_opcodes"] == []


def test_parentheses_are_not_opcodes():
    kinds = {v[0] for v in rows().values()}
    assert "GROUP" not in kinds
    assert not ({"AND", "OR", "NOT", "ELSE", "IF", "THEN", "GO"} & kinds)


def test_recursive_example_has_expected_shape():
    p = parse_predicate(
        "(temperature ABOVE 80 AND memory_pressure ABOVE 0.9) OR "
        "(risk ABOVE 0.8 AND NOT phase_coherence BELOW 0.7)"
    )
    assert p.kind == "or"
    assert p.terms[0].kind == "and"
    assert p.terms[1].kind == "and"
    assert p.terms[1].terms[1].kind == "not"


def test_nested_leaf_path_contains_only_existing_kaku():
    p = parse_predicate(
        "(a ABOVE 1 AND b ABOVE 2) OR (c ABOVE 3 AND NOT d ABOVE 4)"
    )
    assert p.leaf_path == (
        "DIFFERENCE","CONDITION","DIFFERENCE","CONDITION","COMPOSITION",
        "DIFFERENCE","CONDITION","DIFFERENCE","CONDITION","NEGATION","COMPOSITION",
        "COMPOSITION",
    )


def test_parenthesized_word_and_symbol_surfaces_converge():
    a = parse_predicate("(temperature ABOVE 80 AND memory_pressure ABOVE 0.9) OR risk ABOVE 0.8")
    b = parse_predicate("(temperature > 80 AND memory_pressure > .9) OR risk > .80")
    assert a == b


def test_same_kind_nary_and_is_flattened():
    p = parse_predicate("a ABOVE 1 AND b ABOVE 2 AND c ABOVE 3 AND d ABOVE 4")
    assert p.kind == "and"
    assert len(p.terms) == 4
    assert p.leaf_path.count("COMPOSITION") == 3


def test_same_kind_nary_or_is_flattened():
    p = parse_predicate("a ABOVE 1 OR b ABOVE 2 OR c ABOVE 3")
    assert p.kind == "or"
    assert len(p.terms) == 3
    assert p.leaf_path.count("COMPOSITION") == 2


def test_mixed_ungrouped_still_fails_closed():
    for bad in [
        "a ABOVE 1 AND b ABOVE 2 OR c ABOVE 3",
        "a ABOVE 1 OR b ABOVE 2 AND c ABOVE 3",
    ]:
        expect_fail(bad)


def test_explicit_grouping_disambiguates_mixed_logic():
    left = parse_predicate("(a ABOVE 1 AND b ABOVE 2) OR c ABOVE 3")
    right = parse_predicate("a ABOVE 1 AND (b ABOVE 2 OR c ABOVE 3)")
    assert left.canonical_tuple != right.canonical_tuple


def test_not_can_apply_to_a_group():
    p = parse_predicate("NOT (risk ABOVE 0.8 OR phase_coherence BELOW 0.7)")
    assert p.kind == "not"
    assert p.terms[0].kind == "or"
    assert p.leaf_path[-1] == "NEGATION"


def test_double_not_is_preserved_not_silently_simplified():
    p = parse_predicate("NOT NOT risk ABOVE 0.8")
    assert p.kind == "not" and p.terms[0].kind == "not"
    assert p.leaf_path[-2:] == ("NEGATION", "NEGATION")


def test_recursive_truth_table():
    p = parse_predicate(
        "(temperature ABOVE 80 AND memory_pressure ABOVE 0.9) OR "
        "(risk ABOVE 0.8 AND NOT phase_coherence BELOW 0.7)"
    )
    assert evaluate_predicate(p, {"temperature":81,"memory_pressure":0.91,"risk":0.1,"phase_coherence":0.1}) is True
    assert evaluate_predicate(p, {"temperature":70,"memory_pressure":0.2,"risk":0.81,"phase_coherence":0.8}) is True
    assert evaluate_predicate(p, {"temperature":70,"memory_pressure":0.2,"risk":0.81,"phase_coherence":0.6}) is False


def test_nested_program_routes_without_action_request():
    prog = normalize_branch_surface(
        "IF (temperature ABOVE 80 AND memory_pressure ABOVE 0.9) OR "
        "(risk ABOVE 0.8 AND NOT phase_coherence BELOW 0.7) "
        "THEN GO safety.pause ELSE GO runtime.continue"
    )
    assert "ACTION_REQUEST" not in prog.leaf_path
    vals = {"temperature":70,"memory_pressure":0.2,"risk":0.81,"phase_coherence":0.8}
    assert select_route(prog, vals) == "safety.pause"
    vals["phase_coherence"] = 0.6
    assert select_route(prog, vals) == "runtime.continue"


def test_grouping_does_not_add_leaf():
    a = parse_predicate("a ABOVE 1 AND b ABOVE 2")
    b = parse_predicate("(a ABOVE 1 AND b ABOVE 2)")
    assert a == b
    assert a.leaf_path == b.leaf_path


def test_nested_same_kind_parentheses_canonicalize_by_flattening_only_at_same_level():
    # Parentheses around a homogeneous nested term remain semantically equivalent
    # only after explicit structural flattening is performed by this parser level.
    a = parse_predicate("a ABOVE 1 AND b ABOVE 2 AND c ABOVE 3")
    b = parse_predicate("a ABOVE 1 AND (b ABOVE 2 AND c ABOVE 3)")
    # We deliberately preserve explicit nested structure rather than silently invoking associativity.
    assert a.canonical_tuple != b.canonical_tuple
    assert evaluate_predicate(a, {"a":2,"b":3,"c":4}) == evaluate_predicate(b, {"a":2,"b":3,"c":4})


def test_invalid_parentheses_fail_closed():
    for bad in [
        "(a ABOVE 1 AND b ABOVE 2",
        "a ABOVE 1 AND b ABOVE 2)",
        "()",
        "( )",
    ]:
        expect_fail(bad)


def test_unsupported_comparator_still_fails_closed():
    for bad in ["a >= 1", "a <= 1", "a != 1"]:
        expect_fail(bad)


def test_nonfinite_runtime_value_fails_closed():
    p = parse_predicate("risk ABOVE 0.8")
    for value in [float("inf"), float("-inf"), float("nan")]:
        try:
            evaluate_predicate(p, {"risk": value})
        except SurfaceV09Error:
            pass
        else:
            raise AssertionError(value)


def test_native_recursive_graph_matches_declared_bindings():
    r = rows()
    assert r["EX.V09.AB"] == ["COMPOSITION", "EX.V09.A", "all", "EX.V09.B"]
    assert r["EX.V09.NOT_D"] == ["NEGATION", "EX.V09.D"]
    assert r["EX.V09.C_NOT_D"] == ["COMPOSITION", "EX.V09.C", "all", "EX.V09.NOT_D"]
    assert r["EX.V09.ROOT"] == ["COMPOSITION", "EX.V09.AB", "any", "EX.V09.C_NOT_D"]


def test_native_file_obeys_reconstructed_line_contract_v09():
    allowed_instr = {"PNV", "EPISTEMIC", "MODE", "OP", "VECTOR", "EMIT"}
    for raw in PNV.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        assert s.split()[0] in allowed_instr, s


def test_ledger_records_no_precedence_guessing():
    d = ledger()
    assert d["implicit_mixed_precedence"] is False
    assert d["grouping_is_semantic_leaf"] is False
    assert d["generic_natural_language_compiler_enabled"] is False


def test_nested_transfer_across_three_domain_trees():
    xs = [
        "(temperature ABOVE 80 AND memory_pressure ABOVE 0.9) OR (risk ABOVE 0.8 AND NOT phase_coherence BELOW 0.7)",
        "(phase_error ABOVE 0 AND phase_coherence BELOW 0.8) OR (memory_pressure ABOVE 0.9 AND NOT temperature BELOW 20)",
        "(gravity BELOW 0.5 AND risk ABOVE 0.7) OR (temperature ABOVE 90 AND NOT memory_pressure ABOVE 0.95)",
    ]
    ys = [parse_predicate(x) for x in xs]
    assert len({y.leaf_path for y in ys}) == 1


def test_long_homogeneous_chain_scales_by_composition_count():
    text = " AND ".join(f"p{i} ABOVE {i}" for i in range(1, 13))
    p = parse_predicate(text)
    assert len(p.terms) == 12
    assert p.leaf_path.count("DIFFERENCE") == 12
    assert p.leaf_path.count("CONDITION") == 12
    assert p.leaf_path.count("COMPOSITION") == 11


def test_nested_not_group_truth_complement():
    inner = parse_predicate("(a ABOVE 1 AND b ABOVE 2) OR c ABOVE 3")
    outer = parse_predicate("NOT ((a ABOVE 1 AND b ABOVE 2) OR c ABOVE 3)")
    cases = [
        {"a":2,"b":3,"c":0},
        {"a":0,"b":3,"c":4},
        {"a":0,"b":0,"c":0},
    ]
    for vals in cases:
        assert evaluate_predicate(outer, vals) is (not evaluate_predicate(inner, vals))


def test_nested_surface_program_paraphrases_converge():
    a = normalize_branch_surface(
        "IF (temperature ABOVE 80 AND memory_pressure ABOVE 0.9) OR (risk ABOVE 0.8 AND NOT phase_coherence BELOW 0.7) THEN GO safety.pause ELSE GO runtime.continue"
    )
    b = normalize_branch_surface(
        "IF (temperature > 80 AND memory_pressure > .90) OR (risk > .80 AND NOT phase_coherence < .70) THEN GO safety.pause ELSE GO runtime.continue"
    )
    assert a == b


def test_deep_explicit_grouping_preserves_evaluation():
    text = "((((a ABOVE 1))))"
    p = parse_predicate(text)
    q = parse_predicate("a ABOVE 1")
    assert p == q
    assert p.leaf_path == q.leaf_path
