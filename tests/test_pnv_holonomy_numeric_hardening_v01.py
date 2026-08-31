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
