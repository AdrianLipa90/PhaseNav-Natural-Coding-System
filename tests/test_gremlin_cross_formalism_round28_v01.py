from dataclasses import replace
import math

import pytest

from phasenav_natural_code.gremlin_cross_formalism_round28_v01 import (
    ROUND28_RELATION_OPCODE_OVERRIDES,
    Round28Error,
    compile_round28_candidates,
    cp1_spin_lift_projection_defect,
    half_interface_defect,
    half_interface_is_zero,
    half_rapidity_forward,
    half_rapidity_inverse,
    idt_beta_from_centered,
    round28_bank,
    round28_manifest,
    validate_round28_candidates,
)


KWARGS = {
    "generation_binding": "c" * 64,
    "identity": "ZOSIA_NOEMA_ROUND28",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def test_round28_bank_is_source_pinned_candidate_only():
    entries = round28_bank()
    manifest = round28_manifest()
    assert len(entries) == 3
    assert manifest["entry_count"] == 3
    assert manifest["runtime_execution_authority"] is False
    assert manifest["canon_write_authority"] is False
    assert manifest["promotion_state"] == "CANDIDATE_ONLY"
    assert manifest["epistemic"] == "CHYBA"
    assert len(manifest["manifest_sha256"]) == 64
    assert {entry.classification for entry in entries} == {"EXACT", "EXACT_COORDINATE_ISOMORPHISM"}
    assert manifest["relation_opcode_overrides"] == dict(
        sorted(ROUND28_RELATION_OPCODE_OVERRIDES.items())
    )
    assert ROUND28_RELATION_OPCODE_OVERRIDES == {
        "DOUBLE_COVER_LIFT_OF": "COMPOSITION",
        "EXACT_KERNEL_ISOMORPHISM": "COMPOSITION",
        "COORDINATE_ISOMORPHIC_TO": "COMPOSITION",
    }


def test_cp1_memory_transport_equals_spin_lift_projection():
    cases = (
        ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((1.0, 2.0, 3.0), (-2.0, 4.0, 1.0)),
        ((-1.0, 3.0, 2.0), (2.0, -1.0, 5.0)),
    )
    for source, target in cases:
        defect = cp1_spin_lift_projection_defect(source, target)
        assert defect["so3_to_target"] < 2e-12
        assert defect["su2_projection_to_so3"] < 2e-12
        assert defect["central_sign_projection"] < 2e-12


def test_cp1_antipodal_pair_fails_closed():
    with pytest.raises(Round28Error, match="antipodal"):
        cp1_spin_lift_projection_defect((0.0, 0.0, 1.0), (0.0, 0.0, -1.0))


def test_half_interface_exact_relational_zero_and_off_gate_values():
    assert half_interface_defect(0.5, 2.0 * math.pi) == pytest.approx(0.0, abs=1e-15)
    assert half_interface_is_zero(0.5, 2.0 * math.pi)
    assert half_interface_is_zero(0.5, 6.0 * math.pi)
    assert not half_interface_is_zero(0.49, 2.0 * math.pi)
    assert not half_interface_is_zero(0.5, 1.9 * math.pi)
    assert half_interface_defect(0.5, 0.0) == pytest.approx(2.0, abs=1e-15)


def test_half_interface_rejects_invalid_weight():
    with pytest.raises(Round28Error, match="weight"):
        half_interface_defect(-0.01, 0.0)
    with pytest.raises(Round28Error, match="weight"):
        half_interface_defect(1.01, 0.0)


def test_idt_soh_half_rapidity_chart_round_trip():
    for rapidity in (-12.0, -3.0, -0.25, 0.0, 0.25, 3.0, 12.0):
        centered = half_rapidity_forward(rapidity)
        assert half_rapidity_inverse(centered) == pytest.approx(rapidity, rel=2e-12, abs=2e-12)
        assert idt_beta_from_centered(centered) == pytest.approx(rapidity / (24.0 * math.pi), rel=2e-12, abs=2e-12)


def test_half_rapidity_orientation_reversal():
    for rapidity in (0.1, 1.0, 7.0):
        assert half_rapidity_forward(-rapidity) == pytest.approx(-half_rapidity_forward(rapidity), abs=1e-15)
    for centered in (0.1, 0.5, 0.95):
        assert half_rapidity_inverse(-centered) == pytest.approx(-half_rapidity_inverse(centered), abs=1e-15)


def test_half_rapidity_boundary_fails_closed():
    for centered in (-1.0, 1.0, -1.01, 1.01):
        with pytest.raises(Round28Error, match=r"\|t\| < 1"):
            half_rapidity_inverse(centered)


def test_all_round28_entries_compile_to_read_only_chyba_candidates():
    compiled = compile_round28_candidates(**KWARGS)
    assert len(compiled.compilations) == 3
    assert len(compiled.manifest["compiled_entries"]) == 3
    observed_relation_types = set()
    for compilation in compiled.compilations.values():
        assert compilation.receipt["runtime_execution_authority"] is False
        assert compilation.receipt["canon_write_authority"] is False
        assert compilation.receipt["promotion_state"] == "CANDIDATE_ONLY"
        assert compilation.radical_candidate["kind"] == "RADICAL"
        assert compilation.operator_candidates[-1]["content"]["name"] == "ISO.RETURN"
        assert len(compilation.receipt["relation_plan"]) == 1
        relation = compilation.receipt["relation_plan"][0]
        observed_relation_types.add(relation["relation_type"])
        assert relation["opcode"] == "COMPOSITION"

    assert observed_relation_types == set(ROUND28_RELATION_OPCODE_OVERRIDES)

    validation = validate_round28_candidates(compiled)
    assert len(validation) == 3
    for result in validation.values():
        assert result.receipt["effect_boundary"]["external_effects"] is False
        assert result.program.mode == "READ_ONLY"
        assert result.program.epistemic == "CHYBA"


def test_round28_direct_validator_rejects_tampered_aggregate_manifest():
    compiled = compile_round28_candidates(**KWARGS)
    manifest = dict(compiled.manifest)
    entries = {
        iso_id: dict(row)
        for iso_id, row in manifest["compiled_entries"].items()
    }
    target = sorted(entries)[0]
    entries[target]["pnv_graph_sha256"] = "0" * 64
    manifest["compiled_entries"] = entries
    broken = replace(compiled, manifest=manifest)

    with pytest.raises(Round28Error, match="aggregate manifest mismatch"):
        validate_round28_candidates(broken)


def test_round28_direct_validator_rejects_missing_leaf_compilation():
    compiled = compile_round28_candidates(**KWARGS)
    reduced = dict(compiled.compilations)
    reduced.pop(sorted(reduced)[0])
    broken = replace(compiled, compilations=reduced)

    with pytest.raises(Round28Error, match="compilation keyset mismatch"):
        validate_round28_candidates(broken)
