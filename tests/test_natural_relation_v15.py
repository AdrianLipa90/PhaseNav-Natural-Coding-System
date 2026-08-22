from pathlib import Path
import json
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phasenav_natural_code.compiler import BasisNotCanonizedError, compile_natural_language
from phasenav_natural_code.definitions_v11 import predicate_content
from phasenav_natural_code.natural_v15 import (
    NaturalV15Error,
    RelationRegistry,
    RelationSpec,
    SymbolRegistry,
    SymbolSpec,
    default_natural_registry,
    resolve_natural_predicate,
)

PNV = ROOT / "native" / "PNCS_NATURAL_RELATION_RESOLVER_V0_15.pnv"
LEDGER = ROOT / "mining" / "PNCS_NATURAL_RELATION_RESOLVER_LEDGER_V0_15.json"

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
        resolve_natural_predicate(text)
    except NaturalV15Error:
        return
    raise AssertionError(text)


def test_relation_paraphrases_converge_to_one_content_id():
    xs = [
        "risk above 0.8",
        "risk is above .80",
        "risk greater than 0.800",
        "risk is greater than 0.8",
        "risk exceeds 0.8",
        "risk > 0.8",
    ]
    ids = {resolve_natural_predicate(x).content_id for x in xs}
    assert len(ids) == 1


def test_subject_phrase_aliases_converge():
    a = resolve_natural_predicate("phase coherence below 0.7")
    b = resolve_natural_predicate("phase_coherence is below .70")
    assert a.content_id == b.content_id
    assert a.canonical_graph == b.canonical_graph


def test_percent_fraction_requires_explicit_symbol_policy():
    a = resolve_natural_predicate("risk above 80%")
    b = resolve_natural_predicate("risk above 0.8")
    assert a.content_id == b.content_id
    assert a.trace[0].canonical_scalar == 0.8
    expect_fail("temperature above 80%")


def test_three_comparators_resolve_to_existing_bindings():
    gt = resolve_natural_predicate("risk above 0.8")
    lt = resolve_natural_predicate("risk below 0.8")
    eq = resolve_natural_predicate("risk equals 0.8")
    assert gt.predicate.canonical_tuple[2] == "gt"
    assert lt.predicate.canonical_tuple[2] == "lt"
    assert eq.predicate.canonical_tuple[2] == "eq"
    assert gt.leaf_path == lt.leaf_path == eq.leaf_path == ("DIFFERENCE", "CONDITION")


def test_compound_surface_reuses_boolean_algebra():
    a = resolve_natural_predicate("risk above 0.8 AND phase coherence below 0.7")
    b = resolve_natural_predicate("phase_coherence < .70 AND risk > .80")
    assert a.content_id == b.content_id
    assert a.leaf_path.count("COMPOSITION") == 1


def test_grouped_mixed_logic_is_supported_without_precedence_guessing():
    a = resolve_natural_predicate("(risk above 0.8 AND phase coherence below 0.7) OR memory pressure above 0.9")
    b = resolve_natural_predicate("memory_pressure > .90 OR (phase_coherence < .70 AND risk > .80)")
    assert a.content_id == b.content_id


def test_ungrouped_mixed_logic_fails_closed():
    expect_fail("risk above 0.8 AND phase coherence below 0.7 OR memory pressure above 0.9")
    expect_fail("risk above 0.8 OR phase coherence below 0.7 AND memory pressure above 0.9")


def test_not_and_grouping_reuse_existing_negation():
    x = resolve_natural_predicate("NOT (risk above 0.8 OR phase coherence below 0.7)")
    assert "NEGATION" in x.leaf_path
    assert set(x.leaf_path) <= {"DIFFERENCE", "CONDITION", "COMPOSITION", "NEGATION"}


def test_unknown_subject_fails_closed():
    expect_fail("entropy pressure above 0.8")


def test_unknown_relation_fails_closed():
    expect_fail("risk around 0.8")
    expect_fail("risk approximately 0.8")


def test_unsupported_comparators_fail_closed():
    for x in ["risk >= 0.8", "risk <= 0.8", "risk != 0.8"]:
        expect_fail(x)


def test_word_number_is_not_guessed():
    expect_fail("risk above eighty percent")


def test_free_form_high_low_is_not_guessed():
    for x in ["risk is high", "risk is kind of high", "phase coherence looks low"]:
        expect_fail(x)


def test_negative_scalar_is_supported_deterministically():
    a = resolve_natural_predicate("temperature below -10")
    assert a.trace[0].canonical_scalar == -10.0


def test_terminal_period_is_surface_only():
    a = resolve_natural_predicate("risk exceeds 0.8.")
    b = resolve_natural_predicate("risk exceeds 0.8")
    assert a.content_id == b.content_id


def test_trace_is_not_semantic_identity():
    a = resolve_natural_predicate("risk exceeds 0.8")
    b = resolve_natural_predicate("risk is above .80")
    assert a.trace != b.trace
    assert a.content_id == b.content_id


def test_definition_content_matches_direct_canonical_predicate_content():
    x = resolve_natural_predicate("risk exceeds 0.8")
    direct = predicate_content("risk ABOVE 0.8")
    assert x.content_id == direct.content_id
    assert x.canonical_graph == direct.canonical_graph


def test_ambiguous_symbol_alias_registration_is_rejected():
    r = SymbolRegistry()
    r.register(SymbolSpec("a", ("shared",)))
    try:
        r.register(SymbolSpec("b", ("shared",)))
    except NaturalV15Error:
        pass
    else:
        raise AssertionError("ambiguous alias accepted")


def test_ambiguous_relation_alias_registration_is_rejected():
    r = RelationRegistry()
    r.register(RelationSpec("gt", ("beyond",)))
    try:
        r.register(RelationSpec("lt", ("beyond",)))
    except NaturalV15Error:
        pass
    else:
        raise AssertionError("ambiguous relation alias accepted")


def test_custom_registry_is_explicit_and_bounded():
    symbols = SymbolRegistry()
    symbols.register(SymbolSpec("coherence", ("coherence",), percent_is_fraction=True))
    relations = RelationRegistry()
    relations.register(RelationSpec("gt", ("above",)))
    from phasenav_natural_code.natural_v15 import NaturalRegistry
    reg = NaturalRegistry(symbols, relations)
    x = resolve_natural_predicate("coherence above 50%", reg)
    assert x.trace[0].canonical_subject == "coherence"
    assert x.trace[0].canonical_scalar == 0.5
    try:
        resolve_natural_predicate("risk above 0.8", reg)
    except NaturalV15Error:
        pass
    else:
        raise AssertionError("custom registry leaked default symbol")


def test_default_registry_has_no_alias_collision_on_construction():
    assert default_natural_registry().symbols.resolve("phase coherence").canonical == "phase_coherence"


def test_native_v15_uses_only_recovered_pnv_opcodes():
    for key, val in rows().items():
        assert val[0] in ALLOWED, (key, val)
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert ledger["new_opcodes"] == []


def test_natural_surface_words_are_not_native_opcodes():
    kinds = {val[0] for val in rows().values()}
    assert not ({"ABOVE", "BELOW", "EXCEEDS", "GREATER", "LESS", "AND", "OR", "NOT"} & kinds)


def test_native_file_obeys_reconstructed_line_contract():
    allowed_instr = {"PNV", "EPISTEMIC", "MODE", "OP", "VECTOR", "EMIT"}
    for raw in PNV.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        assert s.split()[0] in allowed_instr, s


def test_generic_natural_language_compiler_remains_disabled():
    try:
        compile_natural_language("risk above 0.8")
    except BasisNotCanonizedError:
        pass
    else:
        raise AssertionError("generic compiler was silently enabled")


def test_ledger_preserves_execution_boundary():
    d = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert d["generic_natural_language_compiler_enabled"] is False
    assert d["resolver_scope"] == "PURE_PREDICATE"
    assert d["surface_authority"] is False
    assert d["resolution_trace_affects_content_id"] is False


def test_case_is_surface_only():
    a = resolve_natural_predicate("RISK IS ABOVE 0.8")
    b = resolve_natural_predicate("risk is above 0.8")
    assert a.content_id == b.content_id
