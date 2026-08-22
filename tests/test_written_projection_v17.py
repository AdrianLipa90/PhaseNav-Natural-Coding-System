from pathlib import Path
import json
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phasenav_natural_code.definitions_v11 import branch_content, predicate_content
from phasenav_natural_code.natural_control_v16 import resolve_natural_control
from phasenav_natural_code.natural_v15 import resolve_natural_predicate
from phasenav_natural_code.surface_v09 import BranchProgram
from phasenav_natural_code.written_v17 import (
    ProjectionRegistry,
    WrittenV17Error,
    parse_written_projection,
    render_written_projection,
)

PNV = ROOT / "native" / "PNCS_WRITTEN_PROJECTION_V0_17.pnv"
LEDGER = ROOT / "mining" / "PNCS_WRITTEN_PROJECTION_LEDGER_V0_17.json"

ALLOWED = {
    "IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION","QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT","SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY","MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY","SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL","PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR","SOFT_CLIP","RESOLVE","DERIVE"
}


def fail(fn):
    try:
        fn()
    except WrittenV17Error:
        return
    raise AssertionError("expected WrittenV17Error")


def registry_for(*contents):
    r = ProjectionRegistry()
    for content in contents:
        r.register(content)
    return r


def test_predicate_roundtrip_preserves_content_id_and_payload():
    content = resolve_natural_predicate(
        "risk above 0.8 AND phase coherence below 0.7"
    ).content
    registry = registry_for(content)
    text = registry.render(content)
    parsed = registry.parse(text)
    assert parsed.content_id == content.content_id
    assert parsed.content.semantic_payload == content.semantic_payload
    assert parsed.text == text


def test_internal_branch_roundtrip_preserves_content_id_and_payload():
    content = resolve_natural_control(
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue"
    ).content
    registry = registry_for(content)
    text = registry.render(content.content_id)
    parsed = parse_written_projection(text, registry)
    assert parsed.content_id == content.content_id
    assert parsed.content.semantic_payload == content.semantic_payload


def test_equivalent_natural_paraphrases_render_identically():
    a = resolve_natural_predicate("risk exceeds 80%").content
    b = resolve_natural_predicate("risk is above .80").content
    registry = registry_for(a, b)
    assert a.content_id == b.content_id
    assert registry.render(a) == registry.render(b)


def test_written_predicate_is_canonical_not_natural_surface():
    content = resolve_natural_predicate("risk exceeds 80%").content
    text = registry_for(content).render(content)
    assert "BODY risk ABOVE 0.8\n" in text
    assert "exceeds" not in text
    assert "80%" not in text


def test_boolean_projection_uses_explicit_grouping():
    content = resolve_natural_predicate(
        "(risk above 0.8 AND phase coherence below 0.7) OR memory pressure above 0.9"
    ).content
    text = registry_for(content).render(content)
    assert "BODY ((phase_coherence BELOW 0.7 AND risk ABOVE 0.8) OR memory_pressure ABOVE 0.9)\n" in text


def test_not_projection_roundtrip():
    content = resolve_natural_predicate("NOT risk above 0.8").content
    registry = registry_for(content)
    text = registry.render(content)
    assert "BODY NOT (risk ABOVE 0.8)\n" in text
    assert registry.parse(text).content_id == content.content_id


def test_branch_projection_uses_canonical_route_ids_not_aliases():
    content = resolve_natural_control(
        "IF risk exceeds 80% THEN ROUTE TO pause safety ELSE GO TO continue runtime"
    ).content
    text = registry_for(content).render(content)
    assert "THEN GO safety.pause ELSE GO runtime.continue" in text
    assert "pause safety" not in text


def test_text_cannot_create_unregistered_semantics_even_with_valid_computed_cid():
    content = predicate_content("risk ABOVE 0.8")
    text = render_written_projection(content)
    empty = ProjectionRegistry()
    fail(lambda: empty.parse(text))


def test_body_tamper_fails_closed():
    content = predicate_content("risk ABOVE 0.8")
    registry = registry_for(content)
    text = registry.render(content).replace("ABOVE 0.8", "ABOVE 0.9")
    fail(lambda: registry.parse(text))


def test_route_tamper_fails_closed():
    content = branch_content("IF risk ABOVE 0.8 THEN GO safety.pause ELSE GO runtime.continue")
    registry = registry_for(content)
    text = registry.render(content).replace("safety.pause", "cooling.emergency")
    fail(lambda: registry.parse(text))


def test_cid_tamper_fails_closed():
    content = predicate_content("risk ABOVE 0.8")
    registry = registry_for(content)
    text = registry.render(content)
    bad = text.replace(content.content_id[-1], "0" if content.content_id[-1] != "0" else "1", 1)
    fail(lambda: registry.parse(bad))


def test_kind_tamper_fails_closed():
    content = predicate_content("risk ABOVE 0.8")
    registry = registry_for(content)
    fail(lambda: registry.parse(registry.render(content).replace("KIND PREDICATE", "KIND INTERNAL_BRANCH")))


def test_noncanonical_case_or_spacing_fails_closed():
    content = predicate_content("risk ABOVE 0.8")
    registry = registry_for(content)
    canonical = registry.render(content)
    fail(lambda: registry.parse(canonical.replace("BODY risk ABOVE", "BODY risk above")))
    fail(lambda: registry.parse(canonical.replace("BODY risk", "BODY  risk")))


def test_missing_final_newline_fails_closed():
    content = predicate_content("risk ABOVE 0.8")
    registry = registry_for(content)
    fail(lambda: registry.parse(registry.render(content).rstrip("\n")))


def test_extra_line_fails_closed():
    content = predicate_content("risk ABOVE 0.8")
    registry = registry_for(content)
    fail(lambda: registry.parse(registry.render(content) + "COMMENT nope\n"))


def test_projection_contains_no_alias_or_provenance_fields():
    content = predicate_content("risk ABOVE 0.8")
    text = registry_for(content).render(content)
    assert "ALIAS" not in text
    assert "PROVENANCE" not in text
    assert text.splitlines()[1] == "KIND PREDICATE"


def test_projection_registry_idempotent_for_identical_content():
    content = predicate_content("risk ABOVE 0.8")
    r = ProjectionRegistry()
    r.register(content)
    r.register(predicate_content("risk ABOVE 0.8"))
    assert r.content(content.content_id).semantic_payload == content.semantic_payload


def test_projection_does_not_enable_generic_natural_language_compiler():
    from phasenav_natural_code.compiler import BasisNotCanonizedError, compile_natural_language
    try:
        compile_natural_language("risk above 0.8")
    except BasisNotCanonizedError:
        pass
    else:
        raise AssertionError("generic NL compiler unexpectedly enabled")


def test_native_projection_uses_only_recovered_opcodes_and_no_new_projection_opcode():
    ops = []
    text = PNV.read_text(encoding="utf-8")
    for raw in text.splitlines():
        parts = raw.strip().split()
        if parts[:1] == ["OP"]:
            ops.append(parts[2])
    assert ops
    assert set(ops) <= ALLOWED
    assert "PROJECTION" not in ops
    assert "PARSE" not in ops
    assert "DEFINE" not in ops


def test_native_projection_has_content_identity_witnesses():
    text = PNV.read_text(encoding="utf-8")
    assert "OP W17.PREDICATE.IDENTITY IDENTITY" in text
    assert "OP W17.BRANCH.IDENTITY IDENTITY" in text
    assert "ACTION_REQUEST" not in text


def test_ledger_records_projection_only_authority_rule():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["new_opcodes"] == 0
    assert data["text_semantic_authority"] is False
    assert data["registered_content_required"] is True
    assert data["roundtrip_content_id_required"] is True
    assert data["canonical_rerender_required"] is True


def test_float_repr_roundtrip_preserves_threshold_identity():
    content = predicate_content("phase_error ABOVE 0.10000000000000002")
    registry = registry_for(content)
    text = registry.render(content)
    parsed = registry.parse(text)
    assert parsed.content_id == content.content_id


def test_negative_zero_roundtrip_is_byte_stable():
    content = predicate_content("temperature EQUAL -0.0")
    registry = registry_for(content)
    text = registry.render(content)
    assert "EQUAL -0.0" in text
    assert registry.parse(text).content_id == content.content_id


def test_projection_of_direct_and_natural_branch_is_identical():
    pred = resolve_natural_predicate("risk above 0.8").predicate
    direct = branch_content(BranchProgram(pred, "safety.pause", "runtime.continue"))
    natural = resolve_natural_control(
        "IF risk is above 80% THEN GO safety.pause ELSE GO runtime.continue"
    ).content
    registry = registry_for(direct, natural)
    assert direct.content_id == natural.content_id
    assert registry.render(direct) == registry.render(natural)


def test_algebraic_equivalent_predicates_have_identical_written_projection():
    a = predicate_content("risk ABOVE 0.8 AND phase_error BELOW 0.2")
    b = predicate_content("phase_error BELOW 0.2 AND risk ABOVE 0.8")
    r = registry_for(a, b)
    assert a.content_id == b.content_id
    assert r.render(a) == r.render(b)


def test_double_negation_normalizes_before_projection():
    a = predicate_content("NOT NOT risk ABOVE 0.8")
    b = predicate_content("risk ABOVE 0.8")
    r = registry_for(a, b)
    assert a.content_id == b.content_id
    assert r.render(a) == r.render(b)
    assert "NOT" not in r.render(a)


def test_all_default_comparators_roundtrip():
    for surface in [
        "temperature BELOW -10.5",
        "temperature ABOVE 100.25",
        "temperature EQUAL 0.0",
    ]:
        content = predicate_content(surface)
        r = registry_for(content)
        assert r.parse(r.render(content)).content_id == content.content_id


def test_written_module_contains_no_broad_exception_handler():
    source = (ROOT / "src" / "phasenav_natural_code" / "written_v17.py").read_text(encoding="utf-8")
    assert "except Exception" not in source
