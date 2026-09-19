import hashlib
import json

import pytest

from phasenav_natural_code.relational_evidence_v01 import (
    PNCSRelationalEvidencePacket,
    RelationalEvidencePacketError,
    routing_decision,
    verify_gremlin_evidence_packet,
)


def _canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _gremlin_packet(
    *,
    state="CONSISTENT",
    admissible=False,
    physical_source_selected=False,
    phase_count=2,
    cycle_rank=2,
    jacobian_rank=2,
    fisher_rank=2,
):
    packet = {
        "schema": "GREMLIN_CROSS_MODAL_RELATIONAL_EVIDENCE_PACKET_V0_1",
        "status": "CANDIDATE_ONLY",
        "consistency_state": state,
        "source_attribution_admissible": admissible,
        "physical_source_selected": physical_source_selected,
        "phase_identifiability": {
            "phase_count": phase_count,
            "cycle_rank": cycle_rank,
            "jacobian_rank": jacobian_rank,
            "fisher_rank": fisher_rank,
            "fully_identifiable": (
                jacobian_rank >= cycle_rank and fisher_rank >= cycle_rank
            ),
        },
        "channels": [
            {
                "name": "orbital",
                "observed": 1.2,
                "predicted": 0.0,
                "sigma": 1.0,
                "residual": 1.2,
                "normalized_residual": 1.2,
                "independently_constrained": True,
                "circular_fit": False,
                "provenance": {
                    "repository": "AdrianLipa90/Informational-Dynamics-of-Time",
                    "branch": "candidate/idt-eb-bec-orbital-acoustic-v0.1",
                    "commit": "a" * 40,
                    "schema": "IDT_02JQ",
                    "receipt": "github-actions:reference",
                    "epistemic": "CHYBA",
                },
            }
        ],
        "consistency": {
            "chi_square": 1.44,
            "residual_dof": 1,
            "max_abs_normalized_residual": 1.2,
            "per_channel_sigma_threshold": 3.0,
            "residual_resolution_sigma": 1.0,
        },
        "source_attribution": {
            "known_sectors_independently_constrained": True,
            "circular_fit_present": False,
            "residual_resolved": True,
            "required_source_bindings_admitted": admissible,
            "admissible": admissible,
        },
    }
    packet["packet_sha256"] = hashlib.sha256(_canonical(packet)).hexdigest()
    return packet


def _wrapper(packet):
    return PNCSRelationalEvidencePacket(
        gremlin_packet=packet,
        upstream_repository="AdrianLipa90/GREMLIN",
        upstream_branch="integrate/relational-phase-observation-v0.1",
        upstream_commit="b" * 40,
        upstream_receipt="github-actions:fail-loud-audit",
    )


@pytest.mark.parametrize(
    ("state", "admissible", "expected"),
    [
        ("INCONSISTENT", False, "STOP_DECLARED_MODEL"),
        ("UNDERDETERMINED", False, "REQUEST_MORE_CONSTRAINTS"),
        ("CONSISTENT", False, "NO_SOURCE_ROUTE"),
        ("CONSISTENT", True, "ALLOW_CANDIDATE_SOURCE_TESTS"),
    ],
)
def test_routing_is_conservative(state, admissible, expected):
    packet = _gremlin_packet(state=state, admissible=admissible)
    assert routing_decision(packet) == expected


def test_wrapper_never_selects_physical_source_or_flattens_t36():
    mapped = _wrapper(_gremlin_packet(admissible=True)).as_mapping()
    assert mapped["route"] == "ALLOW_CANDIDATE_SOURCE_TESTS"
    assert mapped["physical_source_selected"] is False
    assert mapped["flatten_into_t36"] is False
    assert mapped["semantic_holonomy_equivalence"] == "OPEN"


def test_packet_hash_detects_tampering():
    packet = _gremlin_packet()
    verify_gremlin_evidence_packet(packet)
    packet["channels"][0]["observed"] = 99.0
    with pytest.raises(RelationalEvidencePacketError, match="hash mismatch"):
        verify_gremlin_evidence_packet(packet)


def test_physical_source_selection_is_rejected_even_with_valid_hash():
    packet = _gremlin_packet(physical_source_selected=True)
    with pytest.raises(
        RelationalEvidencePacketError,
        match="physical_source_selected",
    ):
        verify_gremlin_evidence_packet(packet)


def test_impossible_cycle_rank_is_rejected():
    packet = _gremlin_packet(
        phase_count=2,
        cycle_rank=3,
        jacobian_rank=2,
        fisher_rank=2,
    )
    with pytest.raises(RelationalEvidencePacketError, match="cycle_rank"):
        verify_gremlin_evidence_packet(packet)


def test_disagreeing_source_admissibility_fields_are_rejected():
    packet = _gremlin_packet(admissible=True)
    packet["source_attribution"]["admissible"] = False
    packet.pop("packet_sha256")
    packet["packet_sha256"] = hashlib.sha256(_canonical(packet)).hexdigest()
    with pytest.raises(RelationalEvidencePacketError, match="fields disagree"):
        verify_gremlin_evidence_packet(packet)


def test_wrapper_rejects_t36_flattening():
    wrapped = PNCSRelationalEvidencePacket(
        gremlin_packet=_gremlin_packet(),
        upstream_repository="AdrianLipa90/GREMLIN",
        upstream_branch="integrate/relational-phase-observation-v0.1",
        upstream_commit="b" * 40,
        upstream_receipt="github-actions:fail-loud-audit",
        flatten_into_t36=True,
    )
    with pytest.raises(RelationalEvidencePacketError, match="T36"):
        wrapped.validate()


def test_wrapper_requires_exact_upstream_sha():
    wrapped = PNCSRelationalEvidencePacket(
        gremlin_packet=_gremlin_packet(),
        upstream_repository="AdrianLipa90/GREMLIN",
        upstream_branch="integrate/relational-phase-observation-v0.1",
        upstream_commit="bad",
        upstream_receipt="github-actions:fail-loud-audit",
    )
    with pytest.raises(RelationalEvidencePacketError, match="40-character"):
        wrapped.validate()
