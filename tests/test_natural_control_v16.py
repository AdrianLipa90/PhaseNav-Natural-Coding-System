from pathlib import Path
import json
import math
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phasenav_natural_code.compiler import BasisNotCanonizedError, compile_natural_language
from phasenav_natural_code.definitions_v11 import branch_content
from phasenav_natural_code.natural_control_v16 import (
    NaturalControlRegistry,
    NaturalControlV16Error,
    RouteRegistry,
    RouteSpec,
    admit_internal_route,
    default_control_registry,
    default_route_registry,
    resolve_natural_control,
)
from phasenav_natural_code.natural_v15 import (
    NaturalRegistry,
    RelationRegistry,
    RelationSpec,
    SymbolRegistry,
    SymbolSpec,
    resolve_natural_predicate,
)
from phasenav_natural_code.surface_v09 import BranchProgram

PNV = ROOT / "native" / "PNCS_NATURAL_CONTROL_RESOLVER_V0_16.pnv"
LEDGER = ROOT / "mining" / "PNCS_NATURAL_CONTROL_RESOLVER_LEDGER_V0_16.json"

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


def expect_fail(text):
    try:
        resolve_natural_control(text)
    except NaturalControlV16Error:
        return
    raise AssertionError(text)


def test_simple_control_paraphrases_converge():
    xs = [
        "IF risk above 0.8 THEN GO safety.pause",
        "if risk is above .80 then go to safety pause",
        "IF risk > 80% THEN ROUTE TO safety pause",
    ]
    ids = {resolve_natural_control(x).content_id for x in xs}
    assert len(ids) == 1


def test_else_control_paraphrases_converge():
    xs = [
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue",
        "if risk > .80 then go to safety pause else route to runtime continue",
        "IF risk exceeds 80% THEN ROUTE TO pause safety ELSE GO TO continue runtime",
    ]
    ids = {resolve_natural_control(x).content_id for x in xs}
    assert len(ids) == 1


def test_natural_control_reuses_existing_internal_branch_content_identity():
    pred = resolve_natural_predicate("risk exceeds 0.8").predicate
    direct = branch_content(BranchProgram(pred, "safety.pause", "runtime.continue"))
    natural = resolve_natural_control(
        "IF risk is above 80% THEN GO TO safety pause ELSE GO TO runtime continue"
    )
    assert natural.content_id == direct.content_id
    assert natural.canonical_graph == direct.canonical_graph
    assert natural.leaf_path == direct.leaf_path


def test_compound_natural_predicate_flows_into_existing_branch_content():
    x = resolve_natural_control(
        "IF risk above 0.8 AND phase coherence below 0.7 THEN GO safety.pause ELSE GO runtime.continue"
    )
    assert x.content.kind == "INTERNAL_BRANCH"
    assert x.leaf_path.count("DIFFERENCE") == 2
    assert x.leaf_path.count("CONDITION") == 2
    assert "COMPOSITION" in x.leaf_path
    assert "TRANSFORM" in x.leaf_path


def test_grouped_mixed_boolean_control_is_supported():
    x = resolve_natural_control(
        "IF (risk above 0.8 AND phase coherence below 0.7) OR memory pressure above 0.9 "
        "THEN GO safety.pause ELSE GO runtime.continue"
    )
    assert x.content.kind == "INTERNAL_BRANCH"
    assert x.candidate_targets == ("safety.pause", "runtime.continue")


def test_ungrouped_mixed_boolean_control_fails_closed():
    expect_fail(
        "IF risk above 0.8 AND phase coherence below 0.7 OR memory pressure above 0.9 "
        "THEN GO safety.pause"
    )


def test_unknown_route_fails_closed():
    expect_fail("IF risk above 0.8 THEN GO nowhere.unregistered")
    expect_fail("IF risk above 0.8 THEN GO launch rockets")


def test_arbitrary_dotted_route_is_not_authority():
    expect_fail("IF risk above 0.8 THEN GO system.secret.path")


def test_effect_verbs_are_not_control_surface():
    for text in [
        "IF risk above 0.8 THEN DELETE data",
        "IF risk above 0.8 THEN WRITE config",
        "IF risk above 0.8 THEN EXEC command",
        "IF risk above 0.8 THEN ACTION_REQUEST safety.pause",
    ]:
        expect_fail(text)


def test_route_registry_rejects_ambiguous_aliases():
    routes = RouteRegistry()
    routes.register(RouteSpec("a.path", ("shared route",)))
    try:
        routes.register(RouteSpec("b.path", ("shared route",)))
    except NaturalControlV16Error:
        pass
    else:
        raise AssertionError("ambiguous route alias accepted")


def test_route_registry_rejects_duplicate_canonical_route():
    routes = RouteRegistry()
    routes.register(RouteSpec("a.path", ("route a",)))
    try:
        routes.register(RouteSpec("a.path", ("route a two",)))
    except NaturalControlV16Error:
        pass
    else:
        raise AssertionError("duplicate canonical route accepted")


def test_route_alias_does_not_change_semantic_identity():
    a = resolve_natural_control("IF risk above 0.8 THEN GO safety.pause")
    b = resolve_natural_control("IF risk above 0.8 THEN ROUTE TO pause safety")
    assert a.route_trace != b.route_trace
    assert a.content_id == b.content_id


def test_terminal_period_is_surface_only():
    a = resolve_natural_control("IF risk above 0.8 THEN GO safety.pause.")
    b = resolve_natural_control("IF risk above 0.8 THEN GO safety.pause")
    assert a.content_id == b.content_id


def test_case_is_surface_only():
    a = resolve_natural_control("IF RISK IS ABOVE 0.8 THEN GO SAFETY PAUSE")
    b = resolve_natural_control("if risk is above 0.8 then go safety pause")
    assert a.content_id == b.content_id


def test_candidate_routes_are_declarations_not_admissions():
    x = resolve_natural_control(
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue"
    )
    assert x.candidate_targets == ("safety.pause", "runtime.continue")
    admission = admit_internal_route(x, {"risk": 0.1})
    assert admission.truth_state == "FALSE"
    assert admission.admitted_target == "runtime.continue"
    assert x.candidate_targets != (admission.admitted_target,)


def test_true_branch_admission():
    x = resolve_natural_control("IF risk above 0.8 THEN GO safety.pause")
    a = admit_internal_route(x, {"risk": 0.81})
    assert (a.truth_state, a.admitted_target, a.epistemic_operator) == (
        "TRUE", "safety.pause", None
    )


def test_false_without_else_admits_no_route():
    x = resolve_natural_control("IF risk above 0.8 THEN GO safety.pause")
    a = admit_internal_route(x, {"risk": 0.8})
    assert (a.truth_state, a.admitted_target, a.epistemic_operator) == (
        "FALSE", None, None
    )


def test_false_with_else_admits_false_route():
    x = resolve_natural_control(
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue"
    )
    a = admit_internal_route(x, {"risk": 0.2})
    assert (a.truth_state, a.admitted_target) == ("FALSE", "runtime.continue")


def test_missing_value_is_unresolved_chyba_and_admits_nothing():
    x = resolve_natural_control(
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue"
    )
    a = admit_internal_route(x, {})
    assert (a.truth_state, a.admitted_target, a.epistemic_operator) == (
        "UNRESOLVED", None, "CHYBA"
    )


def test_nonfinite_or_non_numeric_value_is_unresolved():
    x = resolve_natural_control("IF risk above 0.8 THEN GO safety.pause")
    for value in [float("nan"), float("inf"), "not-a-number", None]:
        a = admit_internal_route(x, {"risk": value})
        assert a.truth_state == "UNRESOLVED"
        assert a.admitted_target is None
        assert a.epistemic_operator == "CHYBA"


def test_three_valued_and_short_circuits_false_over_unresolved():
    x = resolve_natural_control(
        "IF risk above 0.8 AND phase coherence below 0.7 THEN GO safety.pause"
    )
    a = admit_internal_route(x, {"risk": 0.1})
    assert a.truth_state == "FALSE"
    assert a.admitted_target is None


def test_three_valued_and_is_unresolved_without_false_term():
    x = resolve_natural_control(
        "IF risk above 0.8 AND phase coherence below 0.7 THEN GO safety.pause"
    )
    a = admit_internal_route(x, {"risk": 0.9})
    assert a.truth_state == "UNRESOLVED"
    assert a.admitted_target is None


def test_three_valued_or_short_circuits_true_over_unresolved():
    x = resolve_natural_control(
        "IF risk above 0.8 OR phase coherence below 0.7 THEN GO safety.pause"
    )
    a = admit_internal_route(x, {"risk": 0.9})
    assert a.truth_state == "TRUE"
    assert a.admitted_target == "safety.pause"


def test_three_valued_or_is_unresolved_without_true_term():
    x = resolve_natural_control(
        "IF risk above 0.8 OR phase coherence below 0.7 THEN GO safety.pause"
    )
    a = admit_internal_route(x, {"risk": 0.1})
    assert a.truth_state == "UNRESOLVED"
    assert a.admitted_target is None


def test_not_preserves_unresolved():
    x = resolve_natural_control("IF NOT risk above 0.8 THEN GO runtime.continue")
    a = admit_internal_route(x, {})
    assert a.truth_state == "UNRESOLVED"
    assert a.admitted_target is None


def test_not_complements_resolved_truth():
    x = resolve_natural_control("IF NOT risk above 0.8 THEN GO runtime.continue")
    assert admit_internal_route(x, {"risk": 0.1}).truth_state == "TRUE"
    assert admit_internal_route(x, {"risk": 0.9}).truth_state == "FALSE"


def test_custom_control_registry_is_explicit_and_does_not_leak_defaults():
    symbols = SymbolRegistry()
    symbols.register(SymbolSpec("load", ("load",), percent_is_fraction=True))
    relations = RelationRegistry()
    relations.register(RelationSpec("gt", ("above",)))
    predicates = NaturalRegistry(symbols, relations)
    routes = RouteRegistry()
    routes.register(RouteSpec("custom.relief", ("custom relief",)))
    reg = NaturalControlRegistry(predicates, routes)
    x = resolve_natural_control("IF load above 90% THEN GO custom relief", reg)
    assert x.true_route.canonical == "custom.relief"
    try:
        resolve_natural_control("IF risk above 0.8 THEN GO safety pause", reg)
    except NaturalControlV16Error:
        pass
    else:
        raise AssertionError("custom registry leaked defaults")


def test_default_routes_are_internal_transform_only():
    routes = default_route_registry()
    for phrase in [
        "safety pause", "runtime continue", "emergency cooling", "memory relief",
        "coherence recovery", "low gravity path",
    ]:
        assert routes.resolve(phrase).route_kind == "INTERNAL_TRANSFORM"


def test_leaf_path_contains_no_action_request():
    x = resolve_natural_control(
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue"
    )
    assert "ACTION_REQUEST" not in x.leaf_path
    assert "TRANSFORM" in x.leaf_path


def test_native_v16_uses_only_recovered_pnv_opcodes():
    for key, val in rows().items():
        assert val[0] in ALLOWED, (key, val)
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert ledger["new_opcodes"] == []


def test_native_v16_does_not_use_action_request_for_internal_routes():
    kinds = {val[0] for val in rows().values()}
    assert "ACTION_REQUEST" not in kinds
    assert "TRANSFORM" in kinds


def test_surface_control_words_are_not_native_opcodes():
    kinds = {val[0] for val in rows().values()}
    assert not ({"IF", "THEN", "ELSE", "GO", "ROUTE"} & kinds)


def test_native_file_obeys_reconstructed_line_contract():
    allowed_instr = {"PNV", "EPISTEMIC", "MODE", "OP", "VECTOR", "EMIT"}
    for raw in PNV.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        assert s.split()[0] in allowed_instr, s


def test_generic_natural_language_compiler_remains_disabled():
    try:
        compile_natural_language("IF risk above 0.8 THEN GO safety.pause")
    except BasisNotCanonizedError:
        pass
    else:
        raise AssertionError("generic compiler was silently enabled")


def test_ledger_preserves_control_effect_boundary():
    d = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert d["resolver_scope"] == "INTERNAL_CONTROL_ONLY"
    assert d["effect_requests_emitted"] is False
    assert d["route_registry_required"] is True
    assert d["unresolved_truth_state"] == "CHYBA_NO_ROUTE"
    assert d["generic_natural_language_compiler_enabled"] is False


def test_default_control_registry_constructs_without_alias_collision():
    reg = default_control_registry()
    assert reg.routes.resolve("safety pause").canonical == "safety.pause"
    assert reg.predicates.symbols.resolve("phase coherence").canonical == "phase_coherence"


def test_natural_control_content_id_stays_in_definition_namespace():
    x = resolve_natural_control("IF risk above 0.8 THEN GO safety.pause")
    assert x.content_id.startswith("pncs:def:sha256:")
    assert x.content.kind == "INTERNAL_BRANCH"


def test_complete_three_state_and_truth_table():
    x = resolve_natural_control(
        "IF risk above 0.8 AND phase coherence below 0.7 THEN GO safety.pause"
    )
    cases = {
        ("T", "T"): "TRUE",
        ("T", "F"): "FALSE",
        ("F", "T"): "FALSE",
        ("F", "F"): "FALSE",
        ("T", "U"): "UNRESOLVED",
        ("U", "T"): "UNRESOLVED",
        ("F", "U"): "FALSE",
        ("U", "F"): "FALSE",
        ("U", "U"): "UNRESOLVED",
    }
    risk = {"T": 0.9, "F": 0.1}
    phase = {"T": 0.6, "F": 0.8}
    for (a, b), expected in cases.items():
        values = {}
        if a != "U":
            values["risk"] = risk[a]
        if b != "U":
            values["phase_coherence"] = phase[b]
        admission = admit_internal_route(x, values)
        assert admission.truth_state == expected, ((a, b), admission)
        if expected == "UNRESOLVED":
            assert admission.admitted_target is None
            assert admission.epistemic_operator == "CHYBA"


def test_complete_three_state_or_truth_table():
    x = resolve_natural_control(
        "IF risk above 0.8 OR phase coherence below 0.7 THEN GO safety.pause"
    )
    cases = {
        ("T", "T"): "TRUE",
        ("T", "F"): "TRUE",
        ("F", "T"): "TRUE",
        ("F", "F"): "FALSE",
        ("T", "U"): "TRUE",
        ("U", "T"): "TRUE",
        ("F", "U"): "UNRESOLVED",
        ("U", "F"): "UNRESOLVED",
        ("U", "U"): "UNRESOLVED",
    }
    risk = {"T": 0.9, "F": 0.1}
    phase = {"T": 0.6, "F": 0.8}
    for (a, b), expected in cases.items():
        values = {}
        if a != "U":
            values["risk"] = risk[a]
        if b != "U":
            values["phase_coherence"] = phase[b]
        admission = admit_internal_route(x, values)
        assert admission.truth_state == expected, ((a, b), admission)
        if expected == "UNRESOLVED":
            assert admission.admitted_target is None
            assert admission.epistemic_operator == "CHYBA"
