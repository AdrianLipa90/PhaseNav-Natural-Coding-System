import pytest

from phasenav_natural_code.relational_observation_v01 import (
    RelationalObservationPacket,
    RelationalObservationPacketError,
    validate_relational_observation_packet,
)


def _packet(**overrides):
    data = dict(
        frequency=1.5,
        intensity=2.0,
        phase=0.25,
        linewidth=0.05,
        coherence=0.9,
        phase_count=2,
        cycle_rank=2,
        jacobian_rank=2,
        fisher_rank=2,
        fully_identifiable=True,
        upstream_repository="AdrianLipa90/Orbital-Eclipse-Spectroscopy",
        upstream_branch="integrate/relational-phase-observation-v0.1",
        upstream_commit="a" * 40,
        upstream_schema="OES_H1_HOLONOMY_RESPONSE_IDENTIFIABILITY_V0_1",
        upstream_receipt="github-actions:reference",
    )
    data.update(overrides)
    return RelationalObservationPacket(**data)


def test_valid_packet_roundtrip():
    packet = _packet().as_mapping()
    assert packet["flatten_into_t36"] is False
    assert packet["semantic_holonomy_equivalence"] == "OPEN"
    assert packet["identifiability"]["fully_identifiable"] is True
    validate_relational_observation_packet(packet)


def test_rank_deficient_packet_can_be_valid_if_marked_not_identifiable():
    packet = _packet(
        jacobian_rank=1,
        fisher_rank=1,
        fully_identifiable=False,
    ).as_mapping()
    validate_relational_observation_packet(packet)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"intensity": -1.0},
        {"linewidth": -0.1},
        {"coherence": 1.1},
        {"cycle_rank": 3},
        {"jacobian_rank": 3},
        {"fisher_rank": 3},
        {"jacobian_rank": 1, "fisher_rank": 1, "fully_identifiable": True},
        {"upstream_commit": "abc"},
        {"flatten_into_t36": True},
    ],
)
def test_invalid_packet_domains_fail_closed(kwargs):
    with pytest.raises(RelationalObservationPacketError):
        _packet(**kwargs).validate()


def test_validator_rejects_semantic_holonomy_promotion():
    packet = _packet().as_mapping()
    packet["semantic_holonomy_equivalence"] = "PASS"
    with pytest.raises(RelationalObservationPacketError):
        validate_relational_observation_packet(packet)


def test_validator_rejects_flattening_request():
    packet = _packet().as_mapping()
    packet["flatten_into_t36"] = True
    with pytest.raises(RelationalObservationPacketError):
        validate_relational_observation_packet(packet)
