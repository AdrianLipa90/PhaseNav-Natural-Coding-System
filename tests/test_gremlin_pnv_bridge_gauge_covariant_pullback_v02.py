from phasenav_natural_code.gremlin_pnv_bridge_v02 import (
    GAUGE_COVARIANT_PULLBACK_CONTRACT,
    GAUGE_COVARIANT_PULLBACK_LOOP_ID,
    PNVGaugeCovariantPhasePullbackError,
    build_gauge_covariant_phase_pullback_loop,
    gauge_covariant_phase_pullback_defects,
    gauge_covariant_phase_pullback_invariants,
    gauge_covariant_phase_pullback_transforms,
    make_gauge_covariant_phase_pullback_state,
)


def test_unified_bridge_exports_gauge_covariant_phase_pullback_holonomy():
    assert GAUGE_COVARIANT_PULLBACK_CONTRACT == "PNCS_PNV_GAUGE_COVARIANT_PHASE_PULLBACK_V0_1"
    assert GAUGE_COVARIANT_PULLBACK_LOOP_ID == "SOURCE.PHASE.NOETHER.GAUGE_COVARIANT_PULLBACK.ROUNDTRIP"
    assert PNVGaugeCovariantPhasePullbackError is not None
    assert callable(make_gauge_covariant_phase_pullback_state)
    assert callable(build_gauge_covariant_phase_pullback_loop)
    assert callable(gauge_covariant_phase_pullback_transforms)
    assert callable(gauge_covariant_phase_pullback_invariants)
    assert callable(gauge_covariant_phase_pullback_defects)
