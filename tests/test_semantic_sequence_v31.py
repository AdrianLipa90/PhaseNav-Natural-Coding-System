from __future__ import annotations

import pytest

from phasenav_natural_code.semantic_sequence_v31 import (
    SemanticRoleRecord,
    SemanticSequenceV31Error,
    build_nisaba_frozen_roles,
    compile_semantic_sequence,
)

SOURCE_SHA = "0a6c02eda6b5e0b890e1ea5106a9c5b302cc4ef52de426cea0187134ae27750d"


def fixture():
    return build_nisaba_frozen_roles(source_digest_sha256=SOURCE_SHA)


def test_frozen_roles_are_seven_distinct_typed_contents():
    roles = fixture()
    assert len(roles) == 7
    ids = [r.content.content_id for r in roles]
    assert len(set(ids)) == 7
    assert all(x.startswith("pncs:semantic-role:sha256:") for x in ids)
    assert all(r.canon_allowed is False for r in roles)


def test_original_reverse_and_shuffle_have_distinct_ordered_semantic_ids():
    roles = fixture()
    original = compile_semantic_sequence(roles)
    reverse = compile_semantic_sequence(tuple(reversed(roles)))
    shuffle = compile_semantic_sequence((roles[3], roles[6], roles[0], roles[4], roles[2], roles[5], roles[1]))
    assert original.ordered_semantic_id != reverse.ordered_semantic_id
    assert original.ordered_semantic_id != shuffle.ordered_semantic_id
    assert reverse.ordered_semantic_id != shuffle.ordered_semantic_id


def test_surface_paraphrase_does_not_change_semantic_identity():
    roles = fixture()
    paraphrased = tuple(
        SemanticRoleRecord(
            content=r.content,
            surface_label=f"paraphrase-{i}",
            source_locator=r.source_locator,
            source_digest_sha256=r.source_digest_sha256,
            legacy_card_id=r.legacy_card_id,
            legacy_hook=r.legacy_hook,
        )
        for i, r in enumerate(roles)
    )
    a = compile_semantic_sequence(roles)
    b = compile_semantic_sequence(paraphrased)
    assert a.ordered_semantic_id == b.ordered_semantic_id
    assert a.content_ids == b.content_ids


def test_legacy_hook_is_provenance_not_semantic_authority():
    roles = fixture()
    changed = tuple(
        SemanticRoleRecord(
            content=r.content,
            surface_label=r.surface_label,
            source_locator=r.source_locator,
            source_digest_sha256=r.source_digest_sha256,
            legacy_card_id=r.legacy_card_id,
            legacy_hook="quarantined-legacy-hook",
        )
        for r in roles
    )
    assert compile_semantic_sequence(roles).ordered_semantic_id == compile_semantic_sequence(changed).ordered_semantic_id


def test_lowering_uses_only_existing_admitted_sequence_primitives():
    compiled = compile_semantic_sequence(fixture())
    schedule = compiled.operator_schedule
    assert len(schedule) == 25
    assert schedule[0] == "IDENTITY"
    assert set(schedule) <= {"IDENTITY", "ORDER", "TRANSFORM", "COMPOSITION"}
    assert schedule.count("IDENTITY") == 7
    assert schedule.count("ORDER") == 6
    assert schedule.count("TRANSFORM") == 6
    assert schedule.count("COMPOSITION") == 6


def test_receipt_stays_fail_closed_before_t36_and_htri():
    receipt = compile_semantic_sequence(fixture()).receipt
    assert receipt["new_pnv_opcodes"] == 0
    assert receipt["semantic_identity_from_surface_label"] is False
    assert receipt["semantic_identity_from_legacy_vector"] is False
    assert receipt["legacy_hook_execution"] is False
    assert receipt["t36_realization_present"] is False
    assert receipt["htri_admitted"] is False
    assert receipt["blocked_next_gate"] == "MISSING_TYPED_SEMANTIC_ROLE_TO_T36_REALIZATION_CONTRACT"


def test_duplicate_typed_role_fails_closed():
    roles = fixture()
    with pytest.raises(SemanticSequenceV31Error):
        compile_semantic_sequence((roles[0], roles[1], roles[0]))


def test_content_identity_excludes_surface_and_provenance_record_fields():
    roles = fixture()
    r = roles[0]
    variant = SemanticRoleRecord(
        content=r.content,
        surface_label="A completely different phrase",
        source_locator="another-valid-provenance-locator",
        source_digest_sha256="1" * 64,
        legacy_card_id="different",
        legacy_hook="different",
    )
    assert r.content.content_id == variant.content.content_id
    assert r.record_id != variant.record_id


def test_compilation_is_deterministic():
    a = compile_semantic_sequence(fixture())
    b = compile_semantic_sequence(fixture())
    assert a.ordered_semantic_id == b.ordered_semantic_id
    assert a.compile_id == b.compile_id
    assert a.receipt == b.receipt
