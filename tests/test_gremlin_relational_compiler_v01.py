from pathlib import Path

import pytest

from phasenav_natural_code.gremlin_relational_compiler_v01 import (
    COMPILER_SCHEMA,
    GremlinRelationalCompilerError,
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
    compile_relational_isomorphism,
    validate_compiled_relational_candidate,
)
from phasenav_natural_code.model import Kaku, Vector36


BASIS = "pncs:t36:isomorphism-test:v1"
KWARGS = {
    "generation_binding": "a" * 64,
    "identity": "ZOSIA_NOEMA_FIRST",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def _kaku(name: str, seed: float, role: str) -> Kaku:
    return Kaku(
        name,
        Vector36(tuple(seed + i / 100.0 for i in range(36)), BASIS),
        0.5 + seed,
        "FORWARD",
        1.0,
        role,
        tuple((seed + i) / 36.0 for i in range(36)),
    )


def _spec() -> RelationalIsomorphism:
    return RelationalIsomorphism(
        isomorphism_id="ISO.TIME.CARRIER",
        invariant_id="INV.CONSERVED.TRANSPORT",
        invariant_description="local transport object -> conserved extensive total -> normalized distributional shape",
        nodes=(
            RelationalNode(_kaku("K.IDT", 0.1, "distribution_shape"), "IDT", "idt:p"),
            RelationalNode(_kaku("K.TIR", 0.2, "conserved_current"), "TIR", "tir:noether-current"),
            RelationalNode(_kaku("K.RFC", 0.3, "source_carrier"), "RFC", "rfc:carrier-factorization"),
        ),
        edges=(
            RelationalEdge("REL.IDT.TIR", "K.IDT", "K.TIR", "ISOMORPHIC_TO"),
            RelationalEdge("REL.TIR.RFC", "K.TIR", "K.RFC", "TRANSFORMS_TO"),
        ),
        evidence_refs=("evidence:unit-test",),
    )


def test_cross_domain_isomorphism_required():
    node = RelationalNode(_kaku("K.ONE", 0.1, "single"), "IDT", "idt:one")
    with pytest.raises(GremlinRelationalCompilerError, match="at least two domains"):
        RelationalIsomorphism("ISO.ONE", "INV.ONE", "same", (node,), ())


def test_compile_materializes_kaku_radical_operator_program_chain():
    result = compile_relational_isomorphism(_spec(), **KWARGS)

    assert result.receipt["compiler_contract"] == COMPILER_SCHEMA
    assert set(result.kaku_candidates) == {"K.IDT", "K.TIR", "K.RFC"}
    assert result.radical_candidate["kind"] == "RADICAL"
    assert result.radical_candidate["promotion_state"] == "CANDIDATE_ONLY"
    assert len(result.radical_candidate["dependency_ids"]) == 3
    assert result.operator_candidates[-1]["content"]["name"] == "ISO.RETURN"
    assert "OP ISO.RETURN RETURN" in result.pnv_text
    assert "EMIT ISO.RETURN" in result.pnv_text


def test_relation_types_are_lowered_deterministically_to_native_pnv():
    result = compile_relational_isomorphism(_spec(), **KWARGS)
    plan = {row["relation_type"]: row["opcode"] for row in result.receipt["relation_plan"]}
    assert plan["ISOMORPHIC_TO"] == "COMPOSITION"
    assert plan["TRANSFORMS_TO"] == "ORDER"
    assert "OP ISO.REL.000 COMPOSITION" in result.pnv_text
    assert "OP ISO.REL.001 ORDER" in result.pnv_text


def test_unknown_relation_type_fails_closed_until_explicitly_bound():
    spec = RelationalIsomorphism(
        "ISO.UNKNOWN",
        "INV.UNKNOWN",
        "test unknown relation lowering",
        (
            RelationalNode(_kaku("K.A", 0.1, "a"), "A", "a:1"),
            RelationalNode(_kaku("K.B", 0.2, "b"), "B", "b:1"),
        ),
        (RelationalEdge("REL.AB", "K.A", "K.B", "MYSTERY_LINK"),),
    )
    with pytest.raises(GremlinRelationalCompilerError, match="explicit opcode binding"):
        compile_relational_isomorphism(spec, **KWARGS)

    compiled = compile_relational_isomorphism(
        spec,
        relation_opcode_overrides={"MYSTERY_LINK": "COMPOSITION"},
        **KWARGS,
    )
    assert compiled.receipt["relation_plan"][0]["opcode"] == "COMPOSITION"


def test_compiled_candidate_executes_in_pure_conformance_mode():
    compiled = compile_relational_isomorphism(_spec(), **KWARGS)
    execution = validate_compiled_relational_candidate(compiled)

    assert "ISO.RETURN" in execution.emitted
    assert execution.receipt["effect_boundary"]["external_effects"] is False
    assert execution.receipt["unknown_semantics_fail_closed"] is True
    assert execution.program.epistemic == "CHYBA"
    assert execution.program.mode == "READ_ONLY"


def test_candidate_sources_are_exact_kaku_envelopes():
    compiled = compile_relational_isomorphism(_spec(), **KWARGS)
    assert set(compiled.source_bindings) == {
        "gremlin.iso.source.000",
        "gremlin.iso.source.001",
        "gremlin.iso.source.002",
    }
    for value in compiled.source_bindings.values():
        assert value["kind"] == "KAKU"
        assert value["runtime_execution_authority"] is False
        assert value["canon_write_authority"] is False


def test_persistent_candidate_compilation_is_content_addressed(tmp_path: Path):
    compiled = compile_relational_isomorphism(_spec(), authoring_root=tmp_path, **KWARGS)

    assert len(list((tmp_path / "kaku").glob("*.json"))) == 3
    assert len(list((tmp_path / "radical").glob("*.json"))) == 1
    assert len(list((tmp_path / "operator").glob("*.json"))) == len(compiled.operator_candidates)

    again = compile_relational_isomorphism(_spec(), authoring_root=tmp_path, **KWARGS)
    assert again.receipt["receipt_sha256"] == compiled.receipt["receipt_sha256"]
    assert len(list((tmp_path / "kaku").glob("*.json"))) == 3


def test_basis_mismatch_fails_before_radical_compilation():
    other = Kaku(
        "K.OTHER",
        Vector36(tuple(float(i) for i in range(36)), "pncs:other:basis"),
        1.0,
        "FORWARD",
        1.0,
        "other",
    )
    spec = RelationalIsomorphism(
        "ISO.BASIS",
        "INV.BASIS",
        "basis mismatch",
        (
            RelationalNode(_kaku("K.BASE", 0.1, "base"), "A", "a:base"),
            RelationalNode(other, "B", "b:other"),
        ),
        (),
    )
    with pytest.raises(GremlinRelationalCompilerError, match="share one PNCS basis"):
        compile_relational_isomorphism(spec, **KWARGS)
