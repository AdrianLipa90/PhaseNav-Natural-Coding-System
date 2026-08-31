import math

import pytest

from phasenav_natural_code.gremlin_cross_formalism_bank_v02 import (
    CrossFormalismBankError,
    bargmann_quadrilateral,
    coboundary_cycle_defects,
    rephase_state,
    shape_scale_defects,
    spinor_central_phase,
)
from phasenav_natural_code.gremlin_cross_formalism_round28_v01 import (
    Round28Error,
    cp1_minimal_axis_angle,
    half_interface_defect,
    half_interface_is_zero,
    half_rapidity_forward,
    half_rapidity_inverse,
    quaternion_rotate,
    rodrigues_rotate,
    spin_lift_quaternion,
)


def test_cross_formalism_rejects_real_string_coercion():
    with pytest.raises(CrossFormalismBankError, match="cycle potentials"):
        coboundary_cycle_defects((0.0, "1.0"))
    with pytest.raises(CrossFormalismBankError, match="rotation angle"):
        spinor_central_phase("6.28")


def test_cross_formalism_rejects_complex_string_coercion():
    states = (
        (1.0 + 0.0j, 0.0 + 0.0j),
        ("1+0j", 1.0j),
        (1.0, 1.0),
        (1.0j, 1.0),
    )
    with pytest.raises(CrossFormalismBankError, match="finite complex"):
        bargmann_quadrilateral(states)

    with pytest.raises(CrossFormalismBankError, match="finite complex"):
        rephase_state(("1+0j",), 0.5)


def test_cross_formalism_rejects_bool_and_string_tolerances_or_scales():
    p = (0.5, 0.5)
    with pytest.raises(CrossFormalismBankError, match="scale"):
        shape_scale_defects(p, p, True, 1.0)
    with pytest.raises(CrossFormalismBankError, match="candidate_scale"):
        shape_scale_defects(p, p, 1.0, "1.0")
    with pytest.raises(CrossFormalismBankError, match="tolerance"):
        shape_scale_defects(p, p, 1.0, 1.0, tolerance="1e-12")


def test_round28_rejects_coercible_vector_and_angle_inputs():
    with pytest.raises(Round28Error, match="three-vector"):
        cp1_minimal_axis_angle((0.0, 0.0, "1.0"), (1.0, 0.0, 0.0))
    with pytest.raises(Round28Error, match="angle"):
        rodrigues_rotate((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), "1.0")
    with pytest.raises(Round28Error, match="angle"):
        spin_lift_quaternion((0.0, 0.0, 1.0), True)
    with pytest.raises(Round28Error, match="quaternion"):
        quaternion_rotate((1.0, 0.0, 0.0), (1.0, 0.0, 0.0, "0.0"))


def test_round28_rejects_coercible_half_interface_and_tolerance_inputs():
    with pytest.raises(Round28Error, match="weight"):
        half_interface_defect(True, 2.0 * math.pi)
    with pytest.raises(Round28Error, match="weight"):
        half_interface_defect("0.5", 2.0 * math.pi)
    with pytest.raises(Round28Error, match="delta_tau"):
        half_interface_defect(0.5, "6.28")
    with pytest.raises(Round28Error, match="tolerance"):
        half_interface_is_zero(0.5, 2.0 * math.pi, tolerance="1e-12")
    with pytest.raises(Round28Error, match="tolerance"):
        cp1_minimal_axis_angle((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), tolerance=True)


def test_round28_rejects_rapidity_string_coercion():
    with pytest.raises(Round28Error, match="rapidity"):
        half_rapidity_forward("1.0")
    with pytest.raises(Round28Error, match="centered coordinate"):
        half_rapidity_inverse("0.5")
