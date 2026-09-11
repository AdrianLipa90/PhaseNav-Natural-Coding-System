import pytest

from phasenav_natural_code.gremlin_cross_formalism_round28_v01 import (
    validate_round28_candidates,
)
from phasenav_natural_code.gremlin_cross_formalism_round28_v02 import (
    ROUND28_RELATION_OPCODE_BINDINGS,
    compile_round28_candidates_v02,
    round28_v02_status,
)
from phasenav_natural_code.gremlin_relational_compiler_v01 import (
    DEFAULT_RELATION_OPCODE,
    GremlinRelationalCompilerError,
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
    compile_relational_isomorphism,
)
from phasenav_natural_code.model import Kaku, Vector36

KWARGS = {
    "generation_binding": "d" * 64,
    "identity": "ZOSIA_NOEMA_ROUND28_V02",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def _kaku(kaku_id: str, seed: float) -> Kaku:
    return Kaku(
        kaku_id,
        Vector36(tuple(seed + i / 1000.0 for i in range(36)), "pncs:t36:round28-v02-test"),
        1.0,
        "FORWARD",
        1.0,
        "round28_v02_test",
        tuple(0.0 for _ in range(36)),
    )


def test_v02_bindings_are_local_not_generic_defaults():
    assert set(ROUND28_RELATION_OPCODE_BINDINGS) == {
        "DOUBLE_COVER_LIFT_OF",
        "EXACT_KERNEL_ISOMORPHISM",
        "COORDINATE_ISOMORPHIC_TO",
    }
    for relation in ROUND28_RELATION_OPCODE_BINDINGS:
        assert relation not in DEFAULT_RELATION_OPCODE


def test_v02_compiles_and_validates_all_round28_entries():
    compiled = compile_round28_candidates_v02(**KWARGS)
    assert len(compiled.compilations) == 3
    validation = validate_round28_candidates(compiled)
    assert len(validation) == 3
    for result in validation.values():
        assert result.program.mode == "READ_ONLY"
        assert result.program.epistemic == "CHYBA"
        assert result.receipt["effect_boundary"]["external_effects"] is False


def test_v02_status_preserves_candidate_authority_boundary():
    status = round28_v02_status()
    assert status["promotion_state"] == "CANDIDATE_ONLY"
    assert status["runtime_execution_authority"] is False
    assert status["canon_write_authority"] is False
    assert status["epistemic"] == "CHYBA"
    assert status["generic_default_opcode_table_mutated"] is False


def test_generic_compiler_still_fails_closed_without_explicit_binding():
    left = RelationalNode(_kaku("K.V02.A", 0.1), "A", "obs:a")
    right = RelationalNode(_kaku("K.V02.B", 0.2), "B", "obs:b")
    spec = RelationalIsomorphism(
        "ISO.V02.FAIL.CLOSED",
        "INV.V02.FAIL.CLOSED",
        "unbound semantic relation remains rejected by generic compiler",
        (left, right),
        (RelationalEdge("REL.V02", "K.V02.A", "K.V02.B", "DOUBLE_COVER_LIFT_OF"),),
    )
    with pytest.raises(GremlinRelationalCompilerError, match="explicit opcode binding"):
        compile_relational_isomorphism(spec, **KWARGS)
