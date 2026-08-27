from phasenav_natural_code.gremlin_pnv_bridge_v02 import (
    SOURCE_HOLONOMY_CONTRACT,
    PNVSourceHolonomyError,
    build_carrier_normalization_loop,
    build_epsilon_source_loop,
    build_q0_occupation_loop,
    carrier_normalization_invariants,
    carrier_normalization_transforms,
    epsilon_source_invariants,
    epsilon_source_transforms,
    make_current_density_state,
    make_extensive_carrier_state,
    q0_occupation_invariants,
    q0_occupation_transforms,
)


def test_unified_bridge_exports_source_holonomy_templates():
    assert SOURCE_HOLONOMY_CONTRACT == "PNCS_PNV_SOURCE_HOLONOMY_LOOPS_V0_1"
    assert PNVSourceHolonomyError is not None
    assert callable(make_extensive_carrier_state)
    assert callable(build_carrier_normalization_loop)
    assert callable(carrier_normalization_transforms)
    assert callable(carrier_normalization_invariants)
    assert callable(build_q0_occupation_loop)
    assert callable(q0_occupation_transforms)
    assert callable(q0_occupation_invariants)
    assert callable(make_current_density_state)
    assert callable(build_epsilon_source_loop)
    assert callable(epsilon_source_transforms)
    assert callable(epsilon_source_invariants)
