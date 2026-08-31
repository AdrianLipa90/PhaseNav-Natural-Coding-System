import pytest

from phasenav_natural_code.gremlin_relation_mining_adapter_v01 import (
    GremlinRelationMiningAdapterError,
    RelationMiningAlignment,
    RelationMiningFinding,
    relation_mining_finding_to_isomorphism,
)
from phasenav_natural_code.model import Kaku, Vector36


BASIS = "pncs:t36:relation-mining-admission-test:v1"


def _kaku(atom: str) -> Kaku:
    return Kaku(
        f"K.{atom}",
        Vector36(tuple(i / 100.0 for i in range(36)), BASIS),
        0.5,
        "FORWARD",
        1.0,
        f"atom:{atom}",
    )


def test_alignment_boolean_indexes_fail_closed():
    with pytest.raises(GremlinRelationMiningAdapterError, match="left_atom_index"):
        RelationMiningAlignment("A", True, "B", 0)
    with pytest.raises(GremlinRelationMiningAdapterError, match="right_atom_index"):
        RelationMiningAlignment("A", 0, "B", False)


def test_whitespace_cannot_fabricate_distinct_ledger_domains():
    ledger = {
        "schema": "PNCS_RELATION_MINING_LEDGER_V0_3",
        "chains": [
            {"id": "A", "source": "IDT", "atoms": ["IDENTITY"]},
            {"id": "B", "source": " IDT ", "atoms": ["IDENTITY"]},
        ],
    }
    finding = RelationMiningFinding(
        "F",
        "INV.F",
        "same normalized domain",
        ("A", "B"),
        (RelationMiningAlignment("A", 0, "B", 0),),
    )
    with pytest.raises(GremlinRelationMiningAdapterError, match="at least two source domains"):
        relation_mining_finding_to_isomorphism(
            ledger,
            finding,
            kaku_by_atom={"IDENTITY": _kaku("IDENTITY")},
        )


def test_ledger_chain_and_atom_types_are_not_stringified():
    ledger_bad_source = {
        "schema": "PNCS_RELATION_MINING_LEDGER_V0_3",
        "chains": [
            {"id": "A", "source": 7, "atoms": ["IDENTITY"]},
            {"id": "B", "source": "B", "atoms": ["IDENTITY"]},
        ],
    }
    finding = RelationMiningFinding(
        "F",
        "INV.F",
        "typed ledger",
        ("A", "B"),
        (RelationMiningAlignment("A", 0, "B", 0),),
    )
    with pytest.raises(GremlinRelationMiningAdapterError, match="chain source"):
        relation_mining_finding_to_isomorphism(
            ledger_bad_source,
            finding,
            kaku_by_atom={"IDENTITY": _kaku("IDENTITY")},
        )

    ledger_bad_atom = {
        "schema": "PNCS_RELATION_MINING_LEDGER_V0_3",
        "chains": [
            {"id": "A", "source": "A", "atoms": [1]},
            {"id": "B", "source": "B", "atoms": ["IDENTITY"]},
        ],
    }
    with pytest.raises(GremlinRelationMiningAdapterError, match="atom"):
        relation_mining_finding_to_isomorphism(
            ledger_bad_atom,
            finding,
            kaku_by_atom={"IDENTITY": _kaku("IDENTITY")},
        )


def test_finding_metadata_and_refs_are_canonicalized():
    finding = RelationMiningFinding(
        " F ",
        " INV.F ",
        " description ",
        (" A ", " B "),
        (RelationMiningAlignment(" A ", 0, " B ", 0, " ISOMORPHIC_TO "),),
        (" evidence:b ", "evidence:a", "evidence:a"),
    )
    assert finding.finding_id == "F"
    assert finding.invariant_id == "INV.F"
    assert finding.invariant_description == "description"
    assert finding.chain_ids == ("A", "B")
    assert finding.alignments[0].left_chain_id == "A"
    assert finding.alignments[0].right_chain_id == "B"
    assert finding.alignments[0].relation_type == "ISOMORPHIC_TO"
    assert finding.evidence_refs == ("evidence:a", "evidence:b")
