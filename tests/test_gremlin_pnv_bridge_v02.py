from phasenav_natural_code.gremlin_pnv_bridge_v02 import (
    AUTHORING_SCHEMA,
    BRIDGE_SCHEMA,
    CANDIDATE_SCHEMA,
    RELATION_MINING_ADAPTER_SCHEMA,
    RELATIONAL_COMPILER_SCHEMA,
    RelationMiningAlignment,
    RelationMiningFinding,
    build_kaku_candidate,
    build_operator_candidate,
    build_radical_candidate,
    render_operator_program,
)
from phasenav_natural_code.model import Kaku, RadicalGraph, Vector36


def test_unified_bridge_exposes_candidate_authoring_chain():
    generation = "a" * 64
    kwargs = {
        "generation_binding": generation,
        "identity": "ZOSIA_NOEMA_FIRST",
        "authority": "USER_EXPLICIT_AUTHORING",
    }
    vector = Vector36(tuple(float(i) / 36.0 for i in range(36)), "pncs:test:basis")
    kaku = Kaku("K.CODE", vector, 1.0, "FORWARD", 1.0, "code_atom")
    kaku_candidate = build_kaku_candidate(kaku, **kwargs)

    radical = RadicalGraph("R.CODE", "pncs:test:basis")
    radical.add_kaku(kaku)
    radical_candidate = build_radical_candidate(
        radical,
        kaku_candidate_ids={"K.CODE": kaku_candidate["candidate_id"]},
        **kwargs,
    )
    source = build_operator_candidate(
        "CODE.SOURCE",
        "SOURCE",
        ("candidate.input",),
        radical_candidate_id=radical_candidate["candidate_id"],
        **kwargs,
    )
    returned = build_operator_candidate(
        "CODE.RETURN",
        "RETURN",
        ("CODE.SOURCE",),
        radical_candidate_id=radical_candidate["candidate_id"],
        **kwargs,
    )
    pnv = render_operator_program((source, returned), emits=("CODE.RETURN",))

    assert BRIDGE_SCHEMA == "PNCS_GREMLIN_NATIVE_PNV_BRIDGE_V0_2"
    assert AUTHORING_SCHEMA == "PNCS_GREMLIN_PNV_AUTHORING_V0_2"
    assert RELATIONAL_COMPILER_SCHEMA == "PNCS_GREMLIN_RELATIONAL_ISOMORPHISM_COMPILER_V0_1"
    assert RELATION_MINING_ADAPTER_SCHEMA == "PNCS_GREMLIN_RELATION_MINING_ADAPTER_V0_1"
    assert kaku_candidate["schema"] == CANDIDATE_SCHEMA
    assert radical_candidate["dependency_ids"] == [kaku_candidate["candidate_id"]]
    assert "OP CODE.SOURCE SOURCE candidate.input" in pnv
    assert "OP CODE.RETURN RETURN CODE.SOURCE" in pnv
    assert "EMIT CODE.RETURN" in pnv


def test_unified_bridge_exports_relation_mining_finding_contract():
    finding = RelationMiningFinding(
        "ISO.TEST",
        "INV.TEST",
        "cross-domain invariant candidate",
        ("A", "B"),
        (RelationMiningAlignment("A", 0, "B", 0),),
    )
    assert finding.finding_id == "ISO.TEST"
    assert finding.alignments[0].relation_type == "ISOMORPHIC_TO"
