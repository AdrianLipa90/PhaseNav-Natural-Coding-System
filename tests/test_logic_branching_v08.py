from pathlib import Path
import json
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phasenav_natural_code.surface_v08 import (
    SurfaceV08Error,
    evaluate_predicate,
    normalize_branch_surface,
    parse_predicate,
    select_route,
)

PNV = ROOT / "native" / "PNCS_LOGIC_BRANCHING_V0_8.pnv"
LEDGER = ROOT / "mining" / "PNCS_LOGIC_BRANCHING_LEDGER_V0_8.json"
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


def test_v08_uses_only_recovered_pnv_opcodes():
    for key, val in rows().items():
        assert val[0] in ALLOWED, (key, val)
    assert ledger()["new_opcodes"] == []


def test_and_or_not_else_are_not_machine_opcodes():
    kinds = {v[0] for v in rows().values()}
    assert not ({"AND", "OR", "NOT", "ELSE"} & kinds)


def test_and_uses_composition_all_binding():
    assert rows()["R.PREDICATE_AND"] == ["COMPOSITION", "predicate_a", "all", "predicate_b"]


def test_or_uses_composition_any_binding():
    assert rows()["R.PREDICATE_OR"] == ["COMPOSITION", "predicate_a", "any", "predicate_b"]


def test_not_uses_existing_negation():
    assert rows()["R.PREDICATE_NOT"] == ["NEGATION", "predicate"]
    assert ledger()["radicals"]["R.PREDICATE_NOT"]["status"] == "CONTROL_SUPPORTING_LEAF"


def test_else_false_branch_is_bound_to_negation():
    r = rows()
    assert r["EX.ELSE.FALSE_PRED"] == ["NEGATION", "EX.ELSE.RISK.PRED"]
    assert ledger()["else_semantics"] == "false branch is bound to NEGATION(primary_predicate)"


def test_action_request_not_used_for_logic_or_routes():
    assert all(v[0] != "ACTION_REQUEST" for v in rows().values())
    assert ledger()["action_request_used"] is False


def test_and_paraphrases_converge():
    a = normalize_branch_surface("IF temperature ABOVE 80 AND memory_pressure ABOVE 0.9 THEN GO safety.pause")
    b = normalize_branch_surface("IF temperature > 80 AND memory_pressure > .9 THEN GO safety.pause")
    assert a == b
    assert a.predicate.kind == "and"
    assert a.true_target == "safety.pause"


def test_or_paraphrases_converge():
    a = normalize_branch_surface("IF risk ABOVE 0.8 OR phase_coherence BELOW 0.7 THEN GO safety.pause")
    b = normalize_branch_surface("IF risk > .8 OR phase_coherence < .70 THEN GO safety.pause")
    assert a == b
    assert a.predicate.kind == "or"


def test_not_paraphrases_converge_for_comparator_surface():
    a = normalize_branch_surface("IF NOT risk ABOVE 0.8 THEN GO runtime.continue")
    b = normalize_branch_surface("IF NOT risk > .8 THEN GO runtime.continue")
    assert a == b
    assert a.predicate.kind == "not"


def test_else_paraphrases_converge():
    a = normalize_branch_surface("IF risk ABOVE 0.8 THEN GO safety.pause ELSE GO runtime.continue")
    b = normalize_branch_surface("IF risk > .80 THEN GO safety.pause ELSE GO runtime.continue")
    assert a == b
    assert a.false_target == "runtime.continue"


def test_compound_predicate_leaf_paths_are_shared():
    a = parse_predicate("temperature ABOVE 80 AND memory_pressure ABOVE 0.9")
    b = parse_predicate("risk ABOVE .8 OR phase_coherence BELOW .7")
    expected = ("DIFFERENCE","CONDITION","DIFFERENCE","CONDITION","COMPOSITION")
    assert a.leaf_path == expected
    assert b.leaf_path == expected


def test_simple_route_preserves_v07_leaf_path():
    p = normalize_branch_surface("IF gravity BELOW 0.5 THEN GO physics.gravity.low")
    assert p.leaf_path == ("DIFFERENCE","CONDITION","ORDER","TRANSFORM","COMPOSITION")


def test_else_adds_negation_and_second_route_without_action_request():
    p = normalize_branch_surface("IF risk ABOVE 0.8 THEN GO safety.pause ELSE GO runtime.continue")
    assert p.leaf_path == (
        "DIFFERENCE","CONDITION","NEGATION","ORDER","TRANSFORM","ORDER","TRANSFORM","COMPOSITION"
    )
    assert "ACTION_REQUEST" not in p.leaf_path


def test_and_truth_table():
    p = parse_predicate("temperature ABOVE 80 AND memory_pressure ABOVE 0.9")
    assert evaluate_predicate(p, {"temperature": 81, "memory_pressure": 0.91}) is True
    assert evaluate_predicate(p, {"temperature": 81, "memory_pressure": 0.90}) is False
    assert evaluate_predicate(p, {"temperature": 79, "memory_pressure": 0.91}) is False


def test_or_truth_table():
    p = parse_predicate("risk ABOVE 0.8 OR phase_coherence BELOW 0.7")
    assert evaluate_predicate(p, {"risk": 0.81, "phase_coherence": 0.8}) is True
    assert evaluate_predicate(p, {"risk": 0.7, "phase_coherence": 0.69}) is True
    assert evaluate_predicate(p, {"risk": 0.8, "phase_coherence": 0.7}) is False


def test_not_truth_table():
    p = parse_predicate("NOT risk ABOVE 0.8")
    assert evaluate_predicate(p, {"risk": 0.8}) is True
    assert evaluate_predicate(p, {"risk": 0.81}) is False


def test_else_route_selection_is_total_for_boolean_predicate():
    p = normalize_branch_surface("IF risk ABOVE 0.8 THEN GO safety.pause ELSE GO runtime.continue")
    assert select_route(p, {"risk": 0.81}) == "safety.pause"
    assert select_route(p, {"risk": 0.80}) == "runtime.continue"


def test_single_branch_returns_none_when_false():
    p = normalize_branch_surface("IF risk ABOVE 0.8 THEN GO safety.pause")
    assert select_route(p, {"risk": 0.8}) is None


def test_missing_value_fails_closed():
    p = parse_predicate("risk ABOVE 0.8")
    try:
        evaluate_predicate(p, {})
    except SurfaceV08Error:
        pass
    else:
        raise AssertionError("missing predicate input must fail closed")


def test_mixed_boolean_without_grouping_fails_closed():
    bad = "IF risk ABOVE 0.8 AND temperature ABOVE 80 OR phase_coherence BELOW 0.7 THEN GO safety.pause"
    try:
        normalize_branch_surface(bad)
    except SurfaceV08Error:
        pass
    else:
        raise AssertionError("mixed AND/OR must fail closed in v0.8")


def test_three_predicates_fail_closed():
    bad = "IF a ABOVE 1 AND b ABOVE 2 AND c ABOVE 3 THEN GO x"
    try:
        normalize_branch_surface(bad)
    except SurfaceV08Error:
        pass
    else:
        raise AssertionError("v0.8 supports exactly two compound predicates")


def test_unsupported_comparators_fail_closed():
    for bad in [
        "IF risk >= 0.8 THEN GO x",
        "IF risk != 0.8 THEN GO x",
        "IF risk <= 0.8 OR temperature > 80 THEN GO x",
    ]:
        try:
            normalize_branch_surface(bad)
        except SurfaceV08Error:
            pass
        else:
            raise AssertionError(bad)


def test_native_file_obeys_reconstructed_line_contract_v08():
    allowed_instr = {"PNV", "EPISTEMIC", "MODE", "OP", "VECTOR", "EMIT"}
    for raw in PNV.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        assert s.split()[0] in allowed_instr, s


def test_and_transfers_across_three_domain_pairs():
    xs = [
        "IF temperature ABOVE 80 AND memory_pressure ABOVE 0.9 THEN GO safety.pause",
        "IF risk ABOVE 0.8 AND phase_coherence BELOW 0.7 THEN GO safety.degraded",
        "IF phase_error EQUAL 0 AND phase_coherence ABOVE 0.9 THEN GO phasenav.locked",
    ]
    ys = [normalize_branch_surface(x) for x in xs]
    expected = (
        "DIFFERENCE","CONDITION","DIFFERENCE","CONDITION","COMPOSITION",
        "ORDER","TRANSFORM","COMPOSITION"
    )
    assert {y.leaf_path for y in ys} == {expected}


def test_or_transfers_across_three_domain_pairs():
    xs = [
        "IF risk ABOVE 0.8 OR phase_coherence BELOW 0.7 THEN GO safety.pause",
        "IF memory_pressure ABOVE 0.9 OR temperature ABOVE 80 THEN GO runtime.relief",
        "IF phase_error ABOVE 0 OR phase_coherence BELOW 0.9 THEN GO phasenav.relock",
    ]
    ys = [normalize_branch_surface(x) for x in xs]
    expected = (
        "DIFFERENCE","CONDITION","DIFFERENCE","CONDITION","COMPOSITION",
        "ORDER","TRANSFORM","COMPOSITION"
    )
    assert {y.leaf_path for y in ys} == {expected}


def test_else_transfers_across_three_domains():
    xs = [
        "IF risk ABOVE 0.8 THEN GO safety.pause ELSE GO runtime.continue",
        "IF temperature ABOVE 80 THEN GO cooling.emergency ELSE GO cooling.normal",
        "IF phase_coherence BELOW 0.7 THEN GO phasenav.relock ELSE GO phasenav.locked",
    ]
    ys = [normalize_branch_surface(x) for x in xs]
    expected = (
        "DIFFERENCE","CONDITION","NEGATION","ORDER","TRANSFORM",
        "ORDER","TRANSFORM","COMPOSITION"
    )
    assert {y.leaf_path for y in ys} == {expected}


def test_and_or_share_structure_but_not_binding():
    a = normalize_branch_surface("IF temperature ABOVE 80 AND memory_pressure ABOVE 0.9 THEN GO safety.pause")
    o = normalize_branch_surface("IF temperature ABOVE 80 OR memory_pressure ABOVE 0.9 THEN GO safety.pause")
    assert a.leaf_path == o.leaf_path
    assert a.predicate.canonical_tuple != o.predicate.canonical_tuple
    assert a.predicate.kind == "and" and o.predicate.kind == "or"


def test_else_true_and_false_routes_are_complementary():
    p = normalize_branch_surface("IF temperature ABOVE 80 THEN GO cooling.emergency ELSE GO cooling.normal")
    for value in [79.0, 80.0, 81.0]:
        route = select_route(p, {"temperature": value})
        assert route in {"cooling.emergency", "cooling.normal"}
        assert (route == "cooling.emergency") == (value > 80.0)
