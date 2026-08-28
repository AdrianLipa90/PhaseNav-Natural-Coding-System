from phasenav_natural_code.gremlin_pnv_bridge_v02 import (
    NOETHER_RFC_CURRENT_CONTRACT,
    NOETHER_RFC_CURRENT_LOOP_ID,
    PNVNoetherRFCCurrentError,
    build_noether_rfc_current_loop,
    make_noether_rfc_current_state,
    noether_rfc_current_invariants,
    noether_rfc_current_transforms,
)


def test_unified_bridge_exports_noether_rfc_current_holonomy():
    assert NOETHER_RFC_CURRENT_CONTRACT == "PNCS_PNV_NOETHER_RFC_CURRENT_BINDING_V0_1"
    assert NOETHER_RFC_CURRENT_LOOP_ID == "SOURCE.PHASE_NOETHER.RFC_CONSERVED_CURRENT.ROUNDTRIP"
    assert PNVNoetherRFCCurrentError is not None
    assert callable(make_noether_rfc_current_state)
    assert callable(build_noether_rfc_current_loop)
    assert callable(noether_rfc_current_transforms)
    assert callable(noether_rfc_current_invariants)
