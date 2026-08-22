from pathlib import Path
import json
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phasenav_natural_code.algebra_v10 import (
    AlgebraV10Error,
    equivalence_key,
    equivalent,
    normalize_boolean,
    to_nnf,
)
from phasenav_natural_code.surface_v09 import parse_predicate, evaluate_predicate

PNV = ROOT / "native" / "PNCS_BOOLEAN_ALGEBRA_V0_10.pnv"
LEDGER = ROOT / "mining" / "PNCS_BOOLEAN_ALGEBRA_LEDGER_V0_10.json"

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


def test_v10_uses_only_recovered_pnv_opcodes():
    for key, val in rows().items():
        assert val[0] in ALLOWED, (key, val)
    assert ledger()["new_opcodes"] == []


def test_and_commutativity_for_pure_predicates():
    assert equivalent("a ABOVE 1 AND b BELOW 2", "b BELOW 2 AND a ABOVE 1").equivalent


def test_or_commutativity_for_pure_predicates():
    assert equivalent("a ABOVE 1 OR b BELOW 2", "b BELOW 2 OR a ABOVE 1").equivalent


def test_and_associativity_for_pure_predicates():
    a = "(a ABOVE 1 AND b ABOVE 2) AND c ABOVE 3"
    b = "a ABOVE 1 AND (b ABOVE 2 AND c ABOVE 3)"
    assert equivalent(a, b).equivalent


def test_or_associativity_for_pure_predicates():
    a = "(a ABOVE 1 OR b ABOVE 2) OR c ABOVE 3"
    b = "a ABOVE 1 OR (b ABOVE 2 OR c ABOVE 3)"
    assert equivalent(a, b).equivalent


def test_double_negation_eliminates():
    assert equivalent("NOT NOT a ABOVE 1", "a ABOVE 1").equivalent


def test_de_morgan_and():
    left = "NOT (a ABOVE 1 AND b BELOW 2)"
    right = "NOT a ABOVE 1 OR NOT b BELOW 2"
    assert equivalent(left, right).equivalent


def test_de_morgan_or():
    left = "NOT (a ABOVE 1 OR b BELOW 2)"
    right = "NOT a ABOVE 1 AND NOT b BELOW 2"
    assert equivalent(left, right).equivalent


def test_idempotence_and_or():
    assert equivalent("a ABOVE 1 AND a ABOVE 1", "a ABOVE 1").equivalent
    assert equivalent("a ABOVE 1 OR a ABOVE 1", "a ABOVE 1").equivalent


def test_absorption():
    assert equivalent("a ABOVE 1 AND (a ABOVE 1 OR b BELOW 2)", "a ABOVE 1").equivalent
    assert equivalent("a ABOVE 1 OR (a ABOVE 1 AND b BELOW 2)", "a ABOVE 1").equivalent


def test_distribution_is_true_but_not_admitted_as_rewrite_v10():
    # Distribution is intentionally outside the canonical rewrite set in v0.10.
    # Therefore these truth-equivalent trees need not share the current normal-form key.
    left = parse_predicate("a ABOVE 1 AND (b ABOVE 2 OR c ABOVE 3)")
    right = parse_predicate("(a ABOVE 1 AND b ABOVE 2) OR (a ABOVE 1 AND c ABOVE 3)")
    assert equivalence_key(left) != equivalence_key(right)
    cases = [
        {"a":2,"b":3,"c":0}, {"a":2,"b":0,"c":4},
        {"a":0,"b":3,"c":4}, {"a":0,"b":0,"c":0},
    ]
    for vals in cases:
        assert evaluate_predicate(left, vals) == evaluate_predicate(right, vals)


def test_composition_is_not_declared_globally_commutative():
    d = ledger()
    assert d["scope"]["global_composition_commutative"] is False
    assert d["scope"]["pure_predicate_only"] is True


def test_no_constant_folding_to_unadmitted_true_false():
    # A OR NOT A and A AND NOT A are not collapsed to constants because no Boolean
    # TRUE/FALSE primitive has been admitted into the PNCS leaf set in this pass.
    a = normalize_boolean(parse_predicate("a ABOVE 1 OR NOT a ABOVE 1"))
    b = normalize_boolean(parse_predicate("a ABOVE 1 AND NOT a ABOVE 1"))
    assert a.kind == "or"
    assert b.kind == "and"


def test_normalization_is_idempotent():
    p = parse_predicate("NOT ((b BELOW 2 AND a ABOVE 1) OR NOT NOT a ABOVE 1)")
    n1 = normalize_boolean(p)
    n2 = normalize_boolean(n1)
    assert n1 == n2


def test_canonical_equivalence_key_stable_across_surface_synonyms():
    a = equivalence_key("temperature ABOVE 80 AND memory_pressure BELOW 0.9")
    b = equivalence_key("memory_pressure < .90 AND temperature > 80.0")
    assert a == b


def test_nnf_contains_negation_only_on_comparison_leaves():
    p = to_nnf(parse_predicate("NOT ((a ABOVE 1 AND b BELOW 2) OR c EQUAL 3)"))
    def walk(n):
        if n.kind == "not":
            assert n.terms[0].kind == "comparison"
        for t in n.terms:
            if hasattr(t, "kind"):
                walk(t)
    walk(p)


def test_native_examples_record_equivalence_without_new_boolean_opcode():
    r = rows()
    assert r["EQ.AND.COMMUTATIVE"][0] == "IDENTITY"
    assert r["EQ.DOUBLE_NEGATION"][0] == "IDENTITY"
    assert r["EQ.DE_MORGAN.AND"][0] == "IDENTITY"
    kinds = {v[0] for v in r.values()}
    assert not ({"AND","OR","NOT","BOOL_TRUE","BOOL_FALSE"} & kinds)


def test_ledger_records_admitted_and_deferred_laws():
    d = ledger()
    assert set(d["admitted_rewrites"]) == {
        "AND_COMMUTATIVITY","OR_COMMUTATIVITY","AND_ASSOCIATIVITY","OR_ASSOCIATIVITY",
        "DOUBLE_NEGATION","DE_MORGAN","IDEMPOTENCE","ABSORPTION"
    }
    assert "DISTRIBUTIVITY" in d["deferred_rewrites"]
    assert "CONSTANT_FOLDING" in d["deferred_rewrites"]


def test_normalization_preserves_truth_for_representative_recursive_family():
    expressions = [
        "a ABOVE 1 AND b ABOVE 1",
        "b ABOVE 1 OR a ABOVE 1",
        "NOT NOT a ABOVE 1",
        "NOT (a ABOVE 1 AND b ABOVE 1)",
        "NOT (a ABOVE 1 OR b ABOVE 1)",
        "a ABOVE 1 AND (a ABOVE 1 OR b ABOVE 1)",
        "a ABOVE 1 OR (a ABOVE 1 AND b ABOVE 1)",
        "(a ABOVE 1 AND b ABOVE 1) OR (c ABOVE 1 AND NOT a ABOVE 1)",
        "NOT ((a ABOVE 1 OR b ABOVE 1) AND (c ABOVE 1 OR NOT a ABOVE 1))",
    ]
    cases = []
    for mask in range(8):
        cases.append({
            "a": 2.0 if mask & 1 else 0.0,
            "b": 2.0 if mask & 2 else 0.0,
            "c": 2.0 if mask & 4 else 0.0,
        })
    for text in expressions:
        raw = parse_predicate(text)
        norm = normalize_boolean(raw)
        for vals in cases:
            assert evaluate_predicate(raw, vals) == evaluate_predicate(norm, vals), (text, vals)


def test_equivalence_key_collapses_order_association_and_double_not_together():
    xs = [
        "(a ABOVE 1 AND b ABOVE 2) AND c ABOVE 3",
        "c ABOVE 3 AND (b ABOVE 2 AND a ABOVE 1)",
        "NOT NOT (b ABOVE 2 AND c ABOVE 3 AND a ABOVE 1)",
    ]
    keys = {equivalence_key(x) for x in xs}
    assert len(keys) == 1


def test_non_equivalent_and_or_do_not_collapse():
    assert not equivalent("a ABOVE 1 AND b ABOVE 2", "a ABOVE 1 OR b ABOVE 2").equivalent


def test_comparator_binding_remains_semantically_significant():
    assert not equivalent("a ABOVE 1", "a BELOW 1").equivalent
    assert not equivalent("a ABOVE 1", "a EQUAL 1").equivalent
