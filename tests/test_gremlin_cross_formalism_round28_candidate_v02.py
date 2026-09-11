from __future__ import annotations

from phasenav_natural_code.gremlin_cross_formalism_round28_candidate_v02 import (
    ROUND28_RELATION_OPCODE_OVERRIDES,
    candidate_metadata,
    compile_round28_candidates_v02,
    validate_round28_candidates_v02,
)

KWARGS = {
    "generation_binding": "c" * 64,
    "identity": "ZOSIA_NOEMA_ROUND28_V02",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def test_round28_v02_uses_only_existing_composition_opcode():
    assert ROUND28_RELATION_OPCODE_OVERRIDES == {
        "DOUBLE_COVER_LIFT_OF": "COMPOSITION",
        "EXACT_KERNEL_ISOMORPHISM": "COMPOSITION",
        "COORDINATE_ISOMORPHIC_TO": "COMPOSITION",
    }
    meta = candidate_metadata()
    assert meta["status"] == "CANDIDATE"
    assert meta["active_working"] is True
    assert meta["new_opcode_count"] == 0


def test_round28_v02_compiles_all_three_and_preserves_candidate_authority():
    compiled = compile_round28_candidates_v02(**KWARGS)
    assert len(compiled.compilations) == 3
    for compilation in compiled.compilations.values():
        # The canonical v0.1 compiler receipt calls this field relation_plan.
        # Candidate v0.2 changes only the explicit bindings, not the receipt schema.
        plan = compilation.receipt["relation_plan"]
        assert len(plan) == 1
        assert plan[0]["opcode"] == "COMPOSITION"
        assert compilation.receipt["promotion_state"] == "CANDIDATE_ONLY"
        assert compilation.receipt["runtime_execution_authority"] is False
        assert compilation.receipt["canon_write_authority"] is False


def test_round28_v02_executes_through_existing_v01_integrity_validator():
    compiled = compile_round28_candidates_v02(**KWARGS)
    results = validate_round28_candidates_v02(compiled)
    assert len(results) == 3
    for result in results.values():
        assert result.program.mode == "READ_ONLY"
        assert result.program.epistemic == "CHYBA"
        assert result.receipt["effect_boundary"]["external_effects"] is False
