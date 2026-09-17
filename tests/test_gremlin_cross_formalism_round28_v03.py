from __future__ import annotations

import pytest

from phasenav_natural_code.gremlin_cross_formalism_round28_v01 import round28_bank, validate_round28_candidates
from phasenav_natural_code.gremlin_cross_formalism_round28_v03 import (
    ROUND28_RELATION_OPCODE_BINDINGS,
    Round28V03Error,
    compile_round28_candidates_v03,
    required_round28_relation_types,
    round28_v03_status,
    validate_round28_relation_opcode_bindings,
)
from phasenav_natural_code.gremlin_relational_compiler_v01 import (
    DEFAULT_RELATION_OPCODE,
    GremlinRelationalCompilerError,
    compile_relational_isomorphism,
)
from phasenav_natural_code.native_pnv_exec_v01 import parse_pnv

KWARGS = {
    "generation_binding": "3" * 64,
    "identity": "ZOSIA_NOEMA_ROUND28_V03",
    "authority": "USER_EXPLICIT_AUTHORING",
}
EXPECTED = {
    "DOUBLE_COVER_LIFT_OF",
    "EXACT_KERNEL_ISOMORPHISM",
    "COORDINATE_ISOMORPHIC_TO",
}


def test_binding_keyset_is_exact_and_generic_table_stays_closed():
    assert required_round28_relation_types() == EXPECTED
    assert set(ROUND28_RELATION_OPCODE_BINDINGS) == EXPECTED
    assert set(ROUND28_RELATION_OPCODE_BINDINGS.values()) == {"COMPOSITION"}
    for relation in EXPECTED:
        assert relation not in DEFAULT_RELATION_OPCODE


def test_wrong_missing_extra_or_identity_lowering_fails_closed():
    valid = dict(ROUND28_RELATION_OPCODE_BINDINGS)
    bad = dict(valid); bad["EXACT_KERNEL_ISOMORPHISM"] = "IDENTITY"
    with pytest.raises(Round28V03Error, match="only to COMPOSITION"):
        validate_round28_relation_opcode_bindings(bad)
    missing = dict(valid); missing.pop("DOUBLE_COVER_LIFT_OF")
    with pytest.raises(Round28V03Error, match="keyset mismatch"):
        validate_round28_relation_opcode_bindings(missing)
    extra = dict(valid); extra["RELATES_TO"] = "COMPOSITION"
    with pytest.raises(Round28V03Error, match="keyset mismatch"):
        validate_round28_relation_opcode_bindings(extra)


def test_v01_generic_compiler_still_rejects_each_unbound_round28_relation():
    for entry in round28_bank():
        with pytest.raises(GremlinRelationalCompilerError, match="explicit opcode binding"):
            compile_relational_isomorphism(entry.spec, **KWARGS, authoring_root=None)


def test_v03_preserves_semantic_relation_and_executes_as_ordered_composition_not_identity():
    compiled = compile_round28_candidates_v03(**KWARGS)
    assert len(compiled.compilations) == 3
    results = validate_round28_candidates(compiled)
    assert set(results) == set(compiled.compilations)
    for iso_id, compilation in compiled.compilations.items():
        semantic = compilation.spec.edges[0].relation_type
        plan = compilation.receipt["relation_plan"]
        assert plan == [dict(plan[0])]
        assert plan[0]["relation_type"] == semantic
        assert plan[0]["opcode"] == "COMPOSITION"
        program = parse_pnv(compilation.pnv_text)
        relation_ops = [op for op in program.ops if op.name.startswith("ISO.REL.")]
        assert len(relation_ops) == 1 and relation_ops[0].opcode == "COMPOSITION"
        result = results[iso_id]
        lowered_value = result.values[relation_ops[0].name]
        assert isinstance(lowered_value, list) and len(lowered_value) == 2
        assert lowered_value[0] != lowered_value[1]
        assert not isinstance(lowered_value, bool)
        assert result.program.mode == "READ_ONLY"
        assert result.program.epistemic == "CHYBA"
        assert result.receipt["effect_boundary"]["external_effects"] is False


def test_status_is_candidate_only_without_new_opcode_or_authority():
    status = round28_v03_status()
    assert status["promotion_state"] == "CANDIDATE_ONLY"
    assert status["release_class"] == "CLOSURE_REQUIRED_CANDIDATE"
    assert status["runtime_execution_authority"] is False
    assert status["canon_write_authority"] is False
    assert status["epistemic"] == "CHYBA"
    assert status["generic_default_opcode_table_mutated"] is False
    assert status["new_opcode_count"] == 0
