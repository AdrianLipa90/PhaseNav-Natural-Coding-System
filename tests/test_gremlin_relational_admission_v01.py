import pytest

from phasenav_natural_code.gremlin_relational_compiler_v01 import (
    GremlinRelationalCompilerError,
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
    compile_relational_isomorphism,
)
from phasenav_natural_code.model import Kaku, Vector36


BASIS = "pncs:t36:relational-admission-test:v1"
KWARGS = {
    "generation_binding": "a" * 64,
    "identity": "ZOSIA_NOEMA_FIRST",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def _kaku(name: str, seed: float) -> Kaku:
    return Kaku(
        name,
        Vector36(tuple(seed + i / 100.0 for i in range(36)), BASIS),
        0.5,
        "FORWARD",
        1.0,
        "test",
    )


def test_whitespace_cannot_fabricate_two_relational_domains():
    a = RelationalNode(_kaku("K.A", 0.1), "IDT", "obs:a")
    b = RelationalNode(_kaku("K.B", 0.2), " IDT ", "obs:b")
    with pytest.raises(GremlinRelationalCompilerError, match="at least two domains"):
        RelationalIsomorphism(
            "ISO.SAME.DOMAIN",
            "INV.SAME.DOMAIN",
            "same normalized domain",
            (a, b),
            (),
        )


def test_relational_metadata_is_trimmed_before_compilation():
    a = RelationalNode(_kaku("K.A", 0.1), " IDT ", " obs:a ")
    b = RelationalNode(_kaku("K.B", 0.2), " RFC ", " obs:b ")
    edge = RelationalEdge(" REL.AB ", " K.A ", " K.B ", " ISOMORPHIC_TO ")
    spec = RelationalIsomorphism(
        " ISO.TRIM ",
        " INV.TRIM ",
        " invariant description ",
        (a, b),
        (edge,),
        (" evidence:b ", "evidence:a", "evidence:a"),
    )
    compiled = compile_relational_isomorphism(spec, **KWARGS)
    assert spec.isomorphism_id == "ISO.TRIM"
    assert spec.invariant_id == "INV.TRIM"
    assert spec.invariant_description == "invariant description"
    assert spec.evidence_refs == ("evidence:a", "evidence:b")
    assert [node.domain for node in spec.nodes] == ["IDT", "RFC"]
    assert spec.edges[0].relation_id == "REL.AB"
    assert spec.edges[0].source_id == "K.A"
    assert spec.edges[0].target_id == "K.B"
    assert spec.edges[0].relation_type == "ISOMORPHIC_TO"
    assert compiled.receipt["domains"] == ["IDT", "RFC"]


@pytest.mark.parametrize(
    "factory",
    [
        lambda: RelationalNode(_kaku("K.A", 0.1), 7, "obs:a"),
        lambda: RelationalNode(_kaku("K.A", 0.1), "IDT", object()),
        lambda: RelationalEdge(7, "K.A", "K.B", "ORDER"),
        lambda: RelationalEdge("REL.AB", "K.A", "K.B", object()),
    ],
)
def test_relational_primitives_reject_non_string_identity_fields(factory):
    with pytest.raises(GremlinRelationalCompilerError, match="non-empty string"):
        factory()


def test_relation_opcode_overrides_reject_non_string_keys_and_values():
    a = RelationalNode(_kaku("K.A", 0.1), "A", "obs:a")
    b = RelationalNode(_kaku("K.B", 0.2), "B", "obs:b")
    spec = RelationalIsomorphism(
        "ISO.OVERRIDE",
        "INV.OVERRIDE",
        "override typing",
        (a, b),
        (RelationalEdge("REL.AB", "K.A", "K.B", "CUSTOM"),),
    )
    with pytest.raises(GremlinRelationalCompilerError, match="override"):
        compile_relational_isomorphism(
            spec,
            relation_opcode_overrides={1: "ORDER"},
            **KWARGS,
        )
    with pytest.raises(GremlinRelationalCompilerError, match="override"):
        compile_relational_isomorphism(
            spec,
            relation_opcode_overrides={"CUSTOM": 1},
            **KWARGS,
        )
