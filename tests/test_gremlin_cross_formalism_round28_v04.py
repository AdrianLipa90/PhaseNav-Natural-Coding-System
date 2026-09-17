from __future__ import annotations

from dataclasses import replace
import math

import pytest

from phasenav_natural_code.gremlin_cross_formalism_round28_v01 import (
    Round28Error,
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
from phasenav_natural_code.gremlin_cross_formalism_round28_v04 import (
    ROUND28_RELATION_OPCODE_BINDINGS,
    Round28V04Error,
    compile_round28_candidates_v04,
    required_round28_relation_types,
    round28_v04_status,
    validate_round28_relation_opcode_bindings,
)
from phasenav_natural_code.gremlin_relational_compiler_v01 import (
    DEFAULT_RELATION_OPCODE,
    GremlinRelationalCompilerError,
    compile_relational_isomorphism,
)
from phasenav_natural_code.native_pnv_exec_v01 import parse_pnv

KWARGS = {
    "generation_binding": "4" * 64,
    "identity": "ZOSIA_NOEMA_ROUND28_V04",
    "authority": "USER_EXPLICIT_AUTHORING",
}
EXPECTED = {
    "DOUBLE_COVER_LIFT_OF",
    "EXACT_KERNEL_ISOMORPHISM",
    "COORDINATE_ISOMORPHIC_TO",
}


def test_v01_exact_bank_and_candidate_boundary_are_preserved():
    entries = round28_bank()
    manifest = round28_manifest()
    assert len(entries) == 3
    assert manifest["entry_count"] == 3
    assert manifest["runtime_execution_authority"] is False
    assert manifest["canon_write_authority"] is False
    assert manifest["promotion_state"] == "CANDIDATE_ONLY"
    assert manifest["epistemic"] == "CHYBA"
    assert {entry.classification for entry in entries} == {"EXACT", "EXACT_COORDINATE_ISOMORPHISM"}


def test_v01_cp1_spin_lift_math_and_antipodal_gate_are_preserved():
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
    with pytest.raises(Round28Error, match="antipodal"):
        cp1_spin_lift_projection_defect((0.0, 0.0, 1.0), (0.0, 0.0, -1.0))


def test_v01_half_interface_math_and_invalid_weight_gate_are_preserved():
    assert half_interface_defect(0.5, 2.0 * math.pi) == pytest.approx(0.0, abs=1e-15)
    assert half_interface_is_zero(0.5, 2.0 * math.pi)
    assert half_interface_is_zero(0.5, 6.0 * math.pi)
    assert not half_interface_is_zero(0.49, 2.0 * math.pi)
    assert not half_interface_is_zero(0.5, 1.9 * math.pi)
    assert half_interface_defect(0.5, 0.0) == pytest.approx(2.0, abs=1e-15)
    for weight in (-0.01, 1.01):
        with pytest.raises(Round28Error, match="weight"):
            half_interface_defect(weight, 0.0)


def test_v01_half_rapidity_math_orientation_and_boundary_are_preserved():
    for rapidity in (-12.0, -3.0, -0.25, 0.0, 0.25, 3.0, 12.0):
        centered = half_rapidity_forward(rapidity)
        assert half_rapidity_inverse(centered) == pytest.approx(rapidity, rel=2e-12, abs=2e-12)
        assert idt_beta_from_centered(centered) == pytest.approx(rapidity / (24.0 * math.pi), rel=2e-12, abs=2e-12)
    for rapidity in (0.1, 1.0, 7.0):
        assert half_rapidity_forward(-rapidity) == pytest.approx(-half_rapidity_forward(rapidity), abs=1e-15)
    for centered in (0.1, 0.5, 0.95):
        assert half_rapidity_inverse(-centered) == pytest.approx(-half_rapidity_inverse(centered), abs=1e-15)
    for centered in (-1.0, 1.0, -1.01, 1.01):
        with pytest.raises(Round28Error, match=r"\|t\| < 1"):
            half_rapidity_inverse(centered)


def test_generic_v01_compiler_must_still_fail_closed_without_explicit_binding():
    for entry in round28_bank():
        with pytest.raises(GremlinRelationalCompilerError, match="explicit opcode binding"):
            compile_relational_isomorphism(entry.spec, **KWARGS, authoring_root=None)


def test_v04_binding_keyset_is_exact_and_generic_table_stays_closed():
    assert required_round28_relation_types() == EXPECTED
    assert set(ROUND28_RELATION_OPCODE_BINDINGS) == EXPECTED
    assert set(ROUND28_RELATION_OPCODE_BINDINGS.values()) == {"COMPOSITION"}
    for relation in EXPECTED:
        assert relation not in DEFAULT_RELATION_OPCODE


def test_wrong_missing_extra_or_identity_lowering_fails_closed():
    valid = dict(ROUND28_RELATION_OPCODE_BINDINGS)
    bad = dict(valid)
    bad["EXACT_KERNEL_ISOMORPHISM"] = "IDENTITY"
    with pytest.raises(Round28V04Error, match="only to COMPOSITION"):
        validate_round28_relation_opcode_bindings(bad)
    missing = dict(valid)
    missing.pop("DOUBLE_COVER_LIFT_OF")
    with pytest.raises(Round28V04Error, match="keyset mismatch"):
        validate_round28_relation_opcode_bindings(missing)
    extra = dict(valid)
    extra["RELATES_TO"] = "COMPOSITION"
    with pytest.raises(Round28V04Error, match="keyset mismatch"):
        validate_round28_relation_opcode_bindings(extra)


def test_v04_preserves_semantic_relation_and_executes_as_ordered_composition_not_identity():
    compiled = compile_round28_candidates_v04(**KWARGS)
    assert len(compiled.compilations) == 3
    results = validate_round28_candidates(compiled)
    assert set(results) == set(compiled.compilations)
    for iso_id, compilation in compiled.compilations.items():
        semantic = compilation.spec.edges[0].relation_type
        plan = compilation.receipt["relation_plan"]
        assert len(plan) == 1
        assert plan[0]["relation_type"] == semantic
        assert plan[0]["opcode"] == "COMPOSITION"
        program = parse_pnv(compilation.pnv_text)
        relation_ops = [op for op in program.ops if op.name.startswith("ISO.REL.")]
        assert len(relation_ops) == 1
        assert relation_ops[0].opcode == "COMPOSITION"
        result = results[iso_id]
        lowered_value = result.values[relation_ops[0].name]
        assert isinstance(lowered_value, list) and len(lowered_value) == 2
        assert lowered_value[0] != lowered_value[1]
        assert not isinstance(lowered_value, bool)
        assert result.program.mode == "READ_ONLY"
        assert result.program.epistemic == "CHYBA"
        assert result.receipt["effect_boundary"]["external_effects"] is False


def test_v04_integrity_validator_rejects_tampered_aggregate_manifest_and_missing_leaf():
    compiled = compile_round28_candidates_v04(**KWARGS)
    manifest = dict(compiled.manifest)
    entries = {iso_id: dict(row) for iso_id, row in manifest["compiled_entries"].items()}
    target = sorted(entries)[0]
    entries[target]["pnv_graph_sha256"] = "0" * 64
    manifest["compiled_entries"] = entries
    with pytest.raises(Round28Error, match="aggregate manifest mismatch"):
        validate_round28_candidates(replace(compiled, manifest=manifest))

    reduced = dict(compiled.compilations)
    reduced.pop(sorted(reduced)[0])
    with pytest.raises(Round28Error, match="compilation keyset mismatch"):
        validate_round28_candidates(replace(compiled, compilations=reduced))


def test_v04_status_stays_candidate_only_without_new_opcode_or_authority():
    status = round28_v04_status()
    assert status["promotion_state"] == "CANDIDATE_ONLY"
    assert status["release_class"] == "CLOSURE_REQUIRED_CANDIDATE"
    assert status["runtime_execution_authority"] is False
    assert status["canon_write_authority"] is False
    assert status["epistemic"] == "CHYBA"
    assert status["generic_default_opcode_table_mutated"] is False
    assert status["new_opcode_count"] == 0
