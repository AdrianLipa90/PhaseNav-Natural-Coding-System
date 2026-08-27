from phasenav_natural_code.gremlin_pnv_bridge_v02 import (
    NOETHER_COLLECTIVE_CONTRACT,
    PNVNoetherCollectiveError,
    build_noether_collective_loop,
    collective_noether_binding_defect,
    make_noether_collective_state,
    noether_collective_invariants,
    noether_collective_transforms,
)


def test_unified_bridge_exports_noether_collective_carrier_holonomy():
    assert NOETHER_COLLECTIVE_CONTRACT == "PNCS_PNV_NOETHER_COLLECTIVE_CARRIER_V0_1"
    assert PNVNoetherCollectiveError is not None
    assert callable(make_noether_collective_state)
    assert callable(build_noether_collective_loop)
    assert callable(noether_collective_transforms)
    assert callable(noether_collective_invariants)
    assert callable(collective_noether_binding_defect)
