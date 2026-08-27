import pytest

from phasenav_natural_code.gremlin_relation_mining_adapter_v01 import (
    ADAPTER_SCHEMA,
    GremlinRelationMiningAdapterError,
    RelationMiningAlignment,
    RelationMiningFinding,
    compile_relation_mining_finding,
    relation_mining_finding_to_isomorphism,
)
from phasenav_natural_code.gremlin_relational_compiler_v01 import validate_compiled_relational_candidate
from phasenav_natural_code.model import Kaku, Vector36
from phasenav_natural_code.native_pnv_exec_v01 import SUPPORTED_OPCODES


BASIS = "pncs:t36:relation-mining-adapter-test:v1"
LEDGER = {
    "schema": "PNCS_RELATION_MINING_LEDGER_V0_3",
    "status": "CANDIDATE_GRAMMAR_MINING_PASS_01",
    "chains": [
        {
            "id": "DOMAIN_A.INVARIANT",
            "source": "DOMAIN_A",
            "status": "EXACT_A",
            "atoms": ["TRANSFORM", "DIFFERENCE", "IDENTITY"],
            "statement": "A invariant path",
        },
        {
            "id": "DOMAIN_B.INVARIANT",
            "source": "DOMAIN_B",
            "status": "EXACT_B",
            "atoms": ["DERIVE", "COMPOSITION", "IDENTITY"],
            "statement": "B convergent path",
        },
    ],
}


def _kaku(atom: str, seed: float) -> Kaku:
    return Kaku(
        kaku_id=f"K.{atom}",
        vector=Vector36(tuple(seed + i / 100.0 for i in range(36)), BASIS),
        semantic_mass=0.5 + seed,
        direction="FORWARD",
        polarity=1.0,
        role=f"grammar_atom:{atom}",
        phase=tuple((seed + i) / 36.0 for i in range(36)),
    )


KAKU = {
    atom: _kaku(atom, index / 10.0)
    for index, atom in enumerate(
        ["TRANSFORM", "DIFFERENCE", "IDENTITY", "DERIVE", "COMPOSITION"],
        start=1,
    )
}

FINDING = RelationMiningFinding(
    finding_id="CROSS_DOMAIN.IDENTITY_ANCHOR",
    invariant_id="INV.SHARED.IDENTITY.ENDPOINT",
    invariant_description="two source-derived paths terminate in a shared identity role",
    chain_ids=("DOMAIN_A.INVARIANT", "DOMAIN_B.INVARIANT"),
    alignments=(
        RelationMiningAlignment("DOMAIN_A.INVARIANT", 2, "DOMAIN_B.INVARIANT", 2),
    ),
    evidence_refs=("evidence:adapter-test",),
)

KWARGS = {
    "generation_binding": "a" * 64,
    "identity": "ZOSIA_NOEMA_FIRST",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def test_adapter_schema_is_versioned():
    assert ADAPTER_SCHEMA == "PNCS_GREMLIN_RELATION_MINING_ADAPTER_V0_1"


def test_relation_mining_finding_becomes_cross_domain_isomorphism_graph():
    iso = relation_mining_finding_to_isomorphism(LEDGER, FINDING, kaku_by_atom=KAKU)

    assert {node.domain for node in iso.nodes} == {"DOMAIN_A", "DOMAIN_B"}
    assert len(iso.nodes) == 6
    assert sum(edge.relation_type == "ORDER" for edge in iso.edges) == 4
    assert sum(edge.relation_type == "ISOMORPHIC_TO" for edge in iso.edges) == 1
    assert all(node.kaku.kaku_id.startswith("RM.") for node in iso.nodes)


def test_historical_non_native_grammar_atoms_remain_kaku_not_executable_opcodes():
    compiled = compile_relation_mining_finding(LEDGER, FINDING, kaku_by_atom=KAKU, **KWARGS)

    assert compiled.spec.invariant_id == "INV.SHARED.IDENTITY.ENDPOINT"
    assert any("DERIVE" in value["content"]["role"] for value in compiled.kaku_candidates.values())
    for operator in compiled.operator_candidates:
        assert operator["content"]["opcode"] in SUPPORTED_OPCODES
    assert " DERIVE " not in compiled.pnv_text


def test_compiled_relation_mining_candidate_executes_purely():
    compiled = compile_relation_mining_finding(LEDGER, FINDING, kaku_by_atom=KAKU, **KWARGS)
    execution = validate_compiled_relational_candidate(compiled)

    assert execution.receipt["effect_boundary"]["external_effects"] is False
    assert execution.receipt["unknown_semantics_fail_closed"] is True
    assert "ISO.RETURN" in execution.emitted


def test_missing_kaku_mapping_fails_closed_without_vector_guessing():
    incomplete = dict(KAKU)
    incomplete.pop("DERIVE")
    with pytest.raises(GremlinRelationMiningAdapterError, match="canonical KAKU mapping required"):
        relation_mining_finding_to_isomorphism(LEDGER, FINDING, kaku_by_atom=incomplete)


def test_invalid_kaku_mapping_fails_closed_with_adapter_error():
    invalid = dict(KAKU)
    invalid["DERIVE"] = object()
    with pytest.raises(GremlinRelationMiningAdapterError, match="invalid value"):
        relation_mining_finding_to_isomorphism(LEDGER, FINDING, kaku_by_atom=invalid)


def test_same_source_family_cannot_be_presented_as_cross_domain_isomorphism():
    ledger = {
        "schema": "PNCS_RELATION_MINING_LEDGER_V0_3",
        "chains": [
            {"id": "A.1", "source": "A", "atoms": ["IDENTITY"]},
            {"id": "A.2", "source": "A", "atoms": ["IDENTITY"]},
        ],
    }
    finding = RelationMiningFinding(
        "SAME_DOMAIN",
        "INV.SAME",
        "same domain candidate",
        ("A.1", "A.2"),
        (RelationMiningAlignment("A.1", 0, "A.2", 0),),
    )
    with pytest.raises(GremlinRelationMiningAdapterError, match="at least two source domains"):
        relation_mining_finding_to_isomorphism(ledger, finding, kaku_by_atom={"IDENTITY": KAKU["IDENTITY"]})


def test_alignment_index_out_of_range_fails_closed():
    finding = RelationMiningFinding(
        "BAD.INDEX",
        "INV.BAD.INDEX",
        "invalid alignment",
        ("DOMAIN_A.INVARIANT", "DOMAIN_B.INVARIANT"),
        (RelationMiningAlignment("DOMAIN_A.INVARIANT", 99, "DOMAIN_B.INVARIANT", 0),),
    )
    with pytest.raises(GremlinRelationMiningAdapterError, match="out of range"):
        relation_mining_finding_to_isomorphism(LEDGER, finding, kaku_by_atom=KAKU)


def test_resolved_atoms_must_share_one_exact_basis():
    other = dict(KAKU)
    other["DERIVE"] = Kaku(
        "K.DERIVE.OTHER",
        Vector36(tuple(float(i) for i in range(36)), "pncs:other:basis"),
        1.0,
        "FORWARD",
        1.0,
        "grammar_atom:DERIVE",
    )
    with pytest.raises(GremlinRelationMiningAdapterError, match="share one exact PNCS basis"):
        relation_mining_finding_to_isomorphism(LEDGER, FINDING, kaku_by_atom=other)
