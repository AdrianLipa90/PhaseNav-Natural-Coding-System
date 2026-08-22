from __future__ import annotations

import json
from pathlib import Path

import pytest

from phasenav_natural_code.definitions_v11 import (
    DefinitionRegistry,
    DefinitionV11Error,
    define_branch,
    define_predicate,
    verify_serialized_record,
)

ROOT = Path(__file__).parents[1]
REGISTRY_PATH = ROOT / "definitions" / "PNCS_DEFINITION_REGISTRY_V0_11.jsonl"
INDEX_PATH = ROOT / "definitions" / "PNCS_DEFINITION_CONTENT_INDEX_V0_11.json"
PNV_PATH = ROOT / "native" / "PNCS_DEFINITION_PATHS_V0_11.pnv"

ALLOWED_OPS = {
    "IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION",
    "QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT",
    "SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY",
    "MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY",
    "SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL",
    "PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR",
    "SOFT_CLIP","RESOLVE","DERIVE",
}

EXPECTED_IDS = {
    "high_risk": "pncs:def:sha256:9c3f6d9ac4c819e64ec85bb0616f38803abb94ed10fe8c0fff591547eadebd24",
    "safety_trigger": "pncs:def:sha256:e0568bb763b3af750265fc159af8d41c440e5f254b43328776fd1b95686b5076",
    "phase_ready": "pncs:def:sha256:38e29c73f334158e297c93d4b6829679a01685bcf8f895bcd1d7f61362b8b734",
    "system_guard": "pncs:def:sha256:339c789b6c2a751a919c5fd921e5b68e93b4712d36a5c32e0f6144989f6034e2",
    "safety_bifurcation": "pncs:def:sha256:b7988497bab75a526771fa24aeca75e0182bd437fd707927cb0e78b04d360cce",
}


def _registry():
    reg = DefinitionRegistry()
    high = reg.register(define_predicate("high_risk", "risk ABOVE 0.8", provenance=("surface:a",)))
    reg.register(define_predicate("risk_guard", "risk > .800", provenance=("surface:b",)))
    safety = reg.register(define_predicate(
        "safety_trigger", "(risk ABOVE 0.8 OR memory_pressure ABOVE 0.9)",
        provenance=("surface:c",)
    ))
    reg.register(define_predicate(
        "safety_trigger_alt", "(memory_pressure > .9 OR risk > .8)",
        provenance=("surface:d",)
    ))
    phase = reg.register(define_predicate(
        "phase_ready", "NOT phase_coherence BELOW 0.7", provenance=("surface:e",)
    ))
    system = reg.register(define_predicate(
        "system_guard",
        "((risk ABOVE 0.8 OR memory_pressure ABOVE 0.9) AND NOT phase_coherence BELOW 0.7)",
        provenance=("surface:f",),
        dependencies=(safety.content.content_id, phase.content.content_id),
    ))
    branch = reg.register(define_branch(
        "safety_bifurcation",
        "IF (risk ABOVE 0.8 OR memory_pressure ABOVE 0.9) THEN GO safety.pause ELSE GO runtime.continue",
        provenance=("surface:g",),
        dependencies=(safety.content.content_id,),
    ))
    return reg, high, safety, phase, system, branch


def test_alias_does_not_change_semantic_content_id():
    reg, high, *_ = _registry()
    assert reg.resolve_alias("high_risk") == reg.resolve_alias("risk_guard")
    assert reg.aliases_for(high.content.content_id) == ("high_risk", "risk_guard")


def test_surface_spelling_and_commutative_order_do_not_change_content_id():
    reg, _, safety, *_ = _registry()
    assert reg.resolve_alias("safety_trigger") == reg.resolve_alias("safety_trigger_alt")
    assert reg.resolve_alias("safety_trigger") == safety.content.content_id


def test_provenance_is_not_semantic_identity_but_is_record_identity():
    a = define_predicate("high_risk", "risk ABOVE 0.8", provenance=("source:A",))
    b = define_predicate("risk_guard", "risk > .800", provenance=("source:B",))
    assert a.content.content_id == b.content.content_id
    assert a.record_id != b.record_id


def test_boolean_equivalence_normalizes_before_hashing():
    a = define_predicate("one", "NOT (risk ABOVE 0.8 AND memory_pressure ABOVE 0.9)")
    b = define_predicate("two", "(NOT risk > .8 OR NOT memory_pressure > .9)")
    assert a.content.content_id == b.content.content_id


def test_semantic_difference_changes_content_id():
    a = define_predicate("above", "risk ABOVE 0.8")
    b = define_predicate("below", "risk BELOW 0.8")
    assert a.content.content_id != b.content.content_id


def test_branch_targets_are_part_of_content_identity():
    a = define_branch("a", "IF risk ABOVE 0.8 THEN GO safety.pause ELSE GO runtime.continue")
    b = define_branch("b", "IF risk ABOVE 0.8 THEN GO safety.pause ELSE GO runtime.stop")
    assert a.content.content_id != b.content.content_id


def test_expansion_is_lossless_to_stabilized_leaf_path():
    reg, high, safety, phase, system, branch = _registry()
    assert reg.expand(high.content.content_id) == ("DIFFERENCE", "CONDITION")
    assert reg.expand("safety_trigger") == (
        "DIFFERENCE","CONDITION","DIFFERENCE","CONDITION","COMPOSITION"
    )
    assert reg.expand("phase_ready") == ("DIFFERENCE","CONDITION","NEGATION")
    assert reg.expand("system_guard") == (
        "DIFFERENCE","CONDITION","NEGATION",
        "DIFFERENCE","CONDITION",
        "DIFFERENCE","CONDITION","COMPOSITION",
        "COMPOSITION",
    )
    assert reg.expand("safety_bifurcation") == (
        "DIFFERENCE","CONDITION","DIFFERENCE","CONDITION","COMPOSITION",
        "NEGATION","ORDER","TRANSFORM","ORDER","TRANSFORM","COMPOSITION",
    )


def test_dependency_lineage_requires_preexisting_content():
    reg = DefinitionRegistry()
    missing = "pncs:def:sha256:" + "0" * 64
    record = define_predicate("x", "risk ABOVE 0.8", dependencies=(missing,))
    with pytest.raises(DefinitionV11Error, match="dependency not registered"):
        reg.register(record)


def test_dependency_lineage_is_content_addressed():
    reg, _, safety, phase, system, branch = _registry()
    assert system.dependencies == (safety.content.content_id, phase.content.content_id)
    assert branch.dependencies == (safety.content.content_id,)


def test_alias_collision_fails_closed():
    reg = DefinitionRegistry()
    reg.register(define_predicate("same", "risk ABOVE 0.8"))
    with pytest.raises(DefinitionV11Error, match="duplicate definition alias"):
        reg.register(define_predicate("same", "risk BELOW 0.8"))


def test_frozen_content_ids_are_reproducible():
    reg, *_ = _registry()
    for alias, expected in EXPECTED_IDS.items():
        assert reg.resolve_alias(alias) == expected


def test_serialized_registry_verifies_and_has_five_unique_contents():
    rows = [json.loads(line) for line in REGISTRY_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 7
    for row in rows:
        verify_serialized_record(row)
        assert row["canon_allowed"] is False
        assert row["epistemic_operator"] == "CHYBA"
    assert len({row["content_id"] for row in rows}) == 5


def test_serialized_tamper_is_detected():
    row = json.loads(REGISTRY_PATH.read_text(encoding="utf-8").splitlines()[0])
    row["content"]["canonical_graph"] = ["comparison", "risk", "gt", 0.81]
    with pytest.raises(DefinitionV11Error, match="content digest mismatch"):
        verify_serialized_record(row)


def test_content_index_matches_registry_alias_sets():
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in REGISTRY_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_content = {}
    for row in rows:
        by_content.setdefault(row["content_id"], []).append(row["alias"])
    assert index["content_count"] == 5
    assert index["alias_count"] == 7
    for item in index["contents"]:
        assert item["aliases"] == sorted(by_content[item["content_id"]])



def test_definition_content_exposes_definition_level_and_content_derived_root():
    reg, high, *_ = _registry()
    assert high.content.level == "DEFINITION"
    assert high.content.native_root_id == "D.9c3f6d9ac4c819e6.ROOT"

def test_native_definition_file_uses_only_recovered_pnv_opcodes():
    lines = [
        line.strip() for line in PNV_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert lines[0] == "PNV 1"
    assert lines[1] == "EPISTEMIC CHYBA"
    assert lines[2] == "MODE READ_ONLY"
    for line in lines[3:]:
        parts = line.split()
        if parts[0] == "OP":
            assert parts[2] in ALLOWED_OPS
        else:
            assert parts[0] in {"VECTOR", "EMIT"}


def test_native_roots_are_content_keyed_and_aliases_are_not_active_semantic_ids():
    active = "\n".join(
        line.strip() for line in PNV_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    for alias in ("high_risk", "risk_guard", "safety_trigger", "safety_trigger_alt", "phase_ready", "system_guard", "safety_bifurcation"):
        assert alias not in active
    for expected in EXPECTED_IDS.values():
        short = expected.rsplit(":", 1)[-1][:16]
        assert f"D.{short}" in active


def test_native_reuse_references_prior_content_roots_without_action_request():
    active = "\n".join(
        line.strip() for line in PNV_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    assert "D.e0568bb763b3af75.ROOT COMPOSITION D.9c3f6d9ac4c819e6.ROOT" in active
    assert "D.339c789b6c2a751a.ROOT COMPOSITION D.e0568bb763b3af75.ROOT D.38e29c73f334158e.ROOT all" in active
    assert "ACTION_REQUEST" not in active
