import pytest

from phasenav_natural_code.semantic_orbital_htri_bridge_v01 import (
    ASSIGN_SAMPLE_OMEGA,
    SemanticHTRILaneProfile,
)


def test_lane_profile_freezes_mapping_snapshot_after_admission():
    source = {"K.A": 3, "K.B": 27}
    profile = SemanticHTRILaneProfile(
        lane_profile_id="LANE.FROZEN",
        kaku_to_lane=source,
        frequency_binding=ASSIGN_SAMPLE_OMEGA,
    )
    before = profile.to_dict()

    source["K.A"] = 9
    source["K.B"] = 10
    with pytest.raises(TypeError):
        profile.kaku_to_lane["K.A"] = 9  # type: ignore[index]

    assert dict(profile.kaku_to_lane) == {"K.A": 3, "K.B": 27}
    assert profile.to_dict() == before
