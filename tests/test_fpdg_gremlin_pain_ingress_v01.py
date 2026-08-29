import pytest

from phasenav_natural_code.fpdg_gremlin_pain_ingress_v01 import (
    INGRESS_SCHEMA,
    FpdgGremlinPainIngressError,
    FpdgPainAlignment,
    build_relation_mining_inputs,
)
from phasenav_natural_code.gremlin_relation_mining_adapter_v01 import (
    compile_relation_mining_finding,
    relation_mining_finding_to_isomorphism,
)
from phasenav_natural_code.gremlin_relational_compiler_v01 import (
    validate_compiled_relational_candidate,
)
from phasenav_natural_code.model import Kaku, Vector36


BASIS = "pncs:t36:fpdg-pain-ingress-test:v1"


def _packet(domain: str, chain_id: str, claims: list[str]):
    return {
        "schema": "FPDG_GREMLIN_PAIN_PACKET_V0_1",
        "epistemic": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "vector_guessing_allowed": False,
        "candidate_edges_enter_canon": False,
        "incident_signature": {
            "schema": "FPDG_PAIN_SIGNATURE_V0_1",
            "signature_hash": "a" * 64,
        },
        "zones": [
            {
                "finding_request_id": f"FPDG.GREMLIN.PAIN.{domain}",
                "invariant_id": "MINIMAL_PROMOTED_DEPENDENCY_FAILURE_FRONTIER",
                "invariant_description": "same localized failure topology",
                "domains": [domain],
                "evidence_refs": [f"evidence:{domain}"],
                "raw_chains": [
                    {
                        "chain_id": chain_id,
                        "source": "FPDG_PROMOTED_DEPENDENCY_WITNESS",
                        "status": "OBSERVED_DIAGNOSTIC_WITNESS",
                        "claims": claims,
                    }
                ],
            }
        ],
        "integration_zones": [],
    }


PACKETS = {
    "current": _packet("RFC", "CURRENT.PATH", ["RFC.A", "RFC.B"]),
    "history": _packet("IDT", "HISTORICAL.PATH", ["IDT.X", "IDT.Y"]),
}
CHAIN_A = "FPDG.CURRENT.CURRENT_PATH"
CHAIN_B = "FPDG.HISTORY.HISTORICAL_PATH"
CLAIM_TO_ATOM = {
    "RFC.A": "TRANSFORM",
    "RFC.B": "BOUNDARY",
    "IDT.X": "DERIVE",
    "IDT.Y": "BOUNDARY",
}
ALIGNMENTS = (FpdgPainAlignment(CHAIN_A, 1, CHAIN_B, 1),)


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
    for index, atom in enumerate(["TRANSFORM", "BOUNDARY", "DERIVE"], start=1)
}


def _build(**overrides):
    kwargs = {
        "claim_to_atom": CLAIM_TO_ATOM,
        "alignments": ALIGNMENTS,
        "finding_id": "FPDG.PAIN.RECURRENCE.TEST",
        "invariant_id": "INV.FPDG.PAIN.SAME_SHAPE",
        "invariant_description": "reviewed current and historical pain paths share a candidate boundary role",
    }
    kwargs.update(overrides)
    return build_relation_mining_inputs(PACKETS, **kwargs)


def test_ingress_schema_is_versioned():
    assert INGRESS_SCHEMA == "PNCS_FPDG_GREMLIN_PAIN_INGRESS_V0_1"


def test_fpdg_claim_paths_lower_to_existing_relation_mining_ledger():
    ingress = _build()

    assert ingress.ledger["schema"] == "PNCS_RELATION_MINING_LEDGER_V0_3"
    assert ingress.finding.chain_ids == (CHAIN_A, CHAIN_B)
    assert {row["source"] for row in ingress.ledger["chains"]} == {"RFC", "IDT"}
    assert ingress.receipt["claim_ids_are_kaku_atoms"] is False
    assert ingress.receipt["canonical_kaku_resolution_required"] is True
    assert ingress.receipt["vector_guessing_allowed"] is False


def test_claim_ids_are_not_silently_reused_as_kaku_atoms():
    ingress = _build()
    all_atoms = {atom for chain in ingress.ledger["chains"] for atom in chain["atoms"]}
    assert "RFC.A" not in all_atoms
    assert "IDT.X" not in all_atoms
    assert all_atoms == {"TRANSFORM", "BOUNDARY", "DERIVE"}


def test_result_enters_actual_gremlin_relational_adapter_after_explicit_kaku_binding():
    ingress = _build()
    iso = relation_mining_finding_to_isomorphism(
        ingress.ledger,
        ingress.finding,
        kaku_by_atom=KAKU,
    )

    assert {node.domain for node in iso.nodes} == {"RFC", "IDT"}
    assert sum(edge.relation_type == "ISOMORPHIC_TO" for edge in iso.edges) == 1
    assert sum(edge.relation_type == "ORDER" for edge in iso.edges) == 2


def test_fpdg_pain_candidate_reaches_radical_native_pnv_and_executes_read_only():
    ingress = _build()
    compiled = compile_relation_mining_finding(
        ingress.ledger,
        ingress.finding,
        kaku_by_atom=KAKU,
        generation_binding="a" * 64,
        identity="ZOSIA_NOEMA_FIRST",
        authority="USER_EXPLICIT_AUTHORING",
    )
    execution = validate_compiled_relational_candidate(compiled)

    assert compiled.receipt["promotion_state"] == "CANDIDATE_ONLY"
    assert compiled.receipt["runtime_execution_authority"] is False
    assert compiled.receipt["canon_write_authority"] is False
    assert compiled.radical_candidate["kind"] == "RADICAL"
    assert "MODE READ_ONLY" in compiled.pnv_text
    assert execution.receipt["effect_boundary"]["external_effects"] is False
    assert execution.receipt["unknown_semantics_fail_closed"] is True


def test_missing_claim_to_atom_binding_fails_closed():
    incomplete = dict(CLAIM_TO_ATOM)
    incomplete.pop("IDT.X")
    with pytest.raises(FpdgGremlinPainIngressError, match="explicit claim_to_atom binding required"):
        _build(claim_to_atom=incomplete)


def test_packet_cannot_escalate_runtime_authority():
    unsafe = dict(PACKETS["current"])
    unsafe["runtime_execution_authority"] = True
    packets = dict(PACKETS)
    packets["current"] = unsafe
    with pytest.raises(FpdgGremlinPainIngressError, match="unsafe or incompatible"):
        build_relation_mining_inputs(
            packets,
            claim_to_atom=CLAIM_TO_ATOM,
            alignments=ALIGNMENTS,
            finding_id="BAD.AUTHORITY",
            invariant_id="INV.BAD",
            invariant_description="must fail",
        )


def test_alignment_must_cross_distinct_domains():
    packets = {
        "current": _packet("RFC", "CURRENT.PATH", ["RFC.A", "RFC.B"]),
        "history": _packet("RFC", "HISTORICAL.PATH", ["IDT.X", "IDT.Y"]),
    }
    with pytest.raises(FpdgGremlinPainIngressError, match="at least two explicit source domains"):
        build_relation_mining_inputs(
            packets,
            claim_to_atom=CLAIM_TO_ATOM,
            alignments=ALIGNMENTS,
            finding_id="SAME.DOMAIN",
            invariant_id="INV.SAME.DOMAIN",
            invariant_description="must fail",
        )


def test_integration_only_packet_cannot_be_fabricated_into_relation_chain():
    packet = _packet("RFC", "TEMP", ["RFC.A"])
    packet["zones"] = []
    packet["integration_zones"] = [{"frontier_location": "FPDG.SOURCE_HEAD_LOCK.RFC"}]
    with pytest.raises(FpdgGremlinPainIngressError, match="integration-only pain"):
        build_relation_mining_inputs(
            {"integration": packet},
            claim_to_atom={"RFC.A": "BOUNDARY"},
            alignments=(FpdgPainAlignment("A", 0, "B", 0),),
            finding_id="INTEGRATION.ONLY",
            invariant_id="INV.INTEGRATION",
            invariant_description="must fail",
        )
