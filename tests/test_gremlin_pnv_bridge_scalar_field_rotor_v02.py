from phasenav_natural_code.gremlin_pnv_bridge_v02 import (
    SCALAR_FIELD_ROTOR_CONTRACT,
    SCALAR_FIELD_ROTOR_LOOP_ID,
    PNVScalarFieldRotorReductionError,
    build_scalar_field_rotor_reduction_loop,
    make_scalar_field_rotor_state,
    scalar_field_rotor_reduction_defects,
    scalar_field_rotor_reduction_invariants,
    scalar_field_rotor_reduction_transforms,
)


def test_unified_bridge_exports_scalar_field_rotor_reduction_holonomy():
    assert SCALAR_FIELD_ROTOR_CONTRACT == "PNCS_PNV_SCALAR_FIELD_ROTOR_INERTIA_REDUCTION_V0_1"
    assert SCALAR_FIELD_ROTOR_LOOP_ID == "SOURCE.PHASE_NOETHER.ROTOR_INERTIA.REDUCTION.ROUNDTRIP"
    assert PNVScalarFieldRotorReductionError is not None
    assert callable(make_scalar_field_rotor_state)
    assert callable(build_scalar_field_rotor_reduction_loop)
    assert callable(scalar_field_rotor_reduction_transforms)
    assert callable(scalar_field_rotor_reduction_invariants)
    assert callable(scalar_field_rotor_reduction_defects)
