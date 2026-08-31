import pytest

from phasenav_natural_code.pnv_holonomy_numeric_v01 import (
    checked_abs_difference_ratio,
    checked_product,
    checked_sum,
    finite_float,
)
from phasenav_natural_code.pnv_noether_collective_holonomy_v01 import (
    PNVNoetherCollectiveError,
    make_noether_collective_state,
    noether_collective_transforms,
)
from phasenav_natural_code.pnv_noether_rfc_current_holonomy_v01 import (
    PNVNoetherRFCCurrentError,
    make_noether_rfc_current_state,
)
from phasenav_natural_code.pnv_scalar_field_rotor_reduction_v01 import (
    PNVScalarFieldRotorReductionError,
    make_scalar_field_rotor_state,
)
from phasenav_natural_code.pnv_gauge_covariant_phase_pullback_v01 import (
    PNVGaugeCovariantPhasePullbackError,
    gauge_covariant_phase_pullback_defects,
    make_gauge_covariant_phase_pullback_state,
)


class LocalNumericError(RuntimeError):
    pass


def test_shared_numeric_guard_rejects_huge_int_conversion_and_overflow():
    with pytest.raises(LocalNumericError, match="finite numeric"):
        finite_float(10**10000, "huge", LocalNumericError)
    with pytest.raises(LocalNumericError, match="finite numeric"):
        checked_product(1.0e308, 1.0e308, field="mul", error_type=LocalNumericError)
    with pytest.raises(LocalNumericError, match="finite numeric"):
        checked_sum((1.0e308, 1.0e308), "sum", LocalNumericError)
    with pytest.raises(LocalNumericError, match="finite numeric"):
        checked_abs_difference_ratio(
            1.0e308,
            -1.0e308,
            1.0,
            "relative",
            LocalNumericError,
        )


def test_noether_collective_rejects_huge_integer_at_domain_boundary():
    with pytest.raises(PNVNoetherCollectiveError, match="finite numeric"):
        make_noether_collective_state(
            D=1,
            epsilon_eb=0.0,
            theta_i_eb=1.0,
            hbar=10**10000,
            j_total=2.0,
            i_phi=1.0,
            i_a=1.0,
        )


def test_noether_collective_rejects_finite_input_that_overflows_derived_product():
    state = make_noether_collective_state(
        D=1,
        epsilon_eb=0.0,
        theta_i_eb=1.0e308,
        hbar=1.0e308,
        j_total=1.0e308,
        i_phi=1.0,
        i_a=1.0,
    )
    transforms = noether_collective_transforms()
    with pytest.raises(PNVNoetherCollectiveError, match="finite numeric"):
        transforms["noether.resolve_rotor_carrier"](state)


def test_noether_rfc_rejects_weighted_total_overflow_at_state_admission():
    with pytest.raises(PNVNoetherRFCCurrentError, match="finite numeric"):
        make_noether_rfc_current_state(
            slice_id="SIGMA.OVERFLOW",
            noether_measure_id="measure:shared:v1",
            rfc_measure_id="measure:shared:v1",
            noether_cell_ids=("c0",),
            rfc_cell_ids=("c0",),
            noether_volumes=(1.0e308,),
            rfc_volumes=(1.0e308,),
            j_theta_cells=(1.0e308,),
            j_q_cells=(1.0e308,),
        )


def test_noether_rfc_rejects_huge_integer_before_weighted_total():
    with pytest.raises(PNVNoetherRFCCurrentError, match="finite numeric"):
        make_noether_rfc_current_state(
            slice_id="SIGMA.HUGE.INT",
            noether_measure_id="measure:shared:v1",
            rfc_measure_id="measure:shared:v1",
            noether_cell_ids=("c0",),
            rfc_cell_ids=("c0",),
            noether_volumes=(10**10000,),
            rfc_volumes=(1.0,),
            j_theta_cells=(1.0,),
            j_q_cells=(1.0,),
        )


def test_scalar_field_rotor_rejects_field_coefficient_overflow():
    with pytest.raises(PNVScalarFieldRotorReductionError, match="finite numeric"):
        make_scalar_field_rotor_state(
            field_phase_mode_id="mode:chi",
            rotor_phase_mode_id="mode:chi",
            field_rate_id="rate:chi",
            rotor_rate_id="rate:chi",
            field_measure_id="measure:h",
            rotor_measure_id="measure:h",
            field_cell_ids=("c0",),
            rotor_cell_ids=("c0",),
            amplitudes=(1.0e308,),
            volumes=(1.0,),
            d_tau_chi=1.0,
            i_phi=1.0,
        )


def test_gauge_pullback_rejects_finite_coordinate_addition_overflow():
    state = make_gauge_covariant_phase_pullback_state(
        field_bundle_id="bundle:u1",
        rotor_bundle_id="bundle:u1",
        field_phase_patch_id="patch:n",
        rotor_phase_patch_id="patch:n",
        field_connection_id="connection:a",
        rotor_connection_id="connection:a",
        field_measure_id="measure:h",
        rotor_measure_id="measure:h",
        field_cell_ids=("c0",),
        rotor_cell_ids=("c0",),
        phase_gradients=(1.0e308,),
        connection_components=(1.0e308,),
        gauge_shift_components=(1.0,),
        trajectory_velocity=(1.0,),
        field_normal_rate=1.0,
        rotor_rate=1.0,
        amplitudes=(1.0,),
        volumes=(1.0,),
        i_phi=2.0,
    )
    with pytest.raises(PNVGaugeCovariantPhasePullbackError, match="finite numeric"):
        gauge_covariant_phase_pullback_defects(state)


def test_gauge_pullback_rejects_action_overflow_after_finite_admission():
    state = make_gauge_covariant_phase_pullback_state(
        field_bundle_id="bundle:u1",
        rotor_bundle_id="bundle:u1",
        field_phase_patch_id="patch:n",
        rotor_phase_patch_id="patch:n",
        field_connection_id="connection:a",
        rotor_connection_id="connection:a",
        field_measure_id="measure:h",
        rotor_measure_id="measure:h",
        field_cell_ids=("c0",),
        rotor_cell_ids=("c0",),
        phase_gradients=(1.0,),
        connection_components=(1.0,),
        gauge_shift_components=(0.5,),
        trajectory_velocity=(1.0e154,),
        field_normal_rate=1.0,
        rotor_rate=1.0e154,
        amplitudes=(1.0,),
        volumes=(1.0,),
        i_phi=2.0,
    )
    with pytest.raises(PNVGaugeCovariantPhasePullbackError, match="finite numeric"):
        gauge_covariant_phase_pullback_defects(state)
