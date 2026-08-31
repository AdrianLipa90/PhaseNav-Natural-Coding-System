import math

import pytest

from phasenav_natural_code.gremlin_strict_admission_v01 import (
    STRICT_ADMISSION_SCHEMA,
    GremlinStrictAdmissionError,
    closed_unit_interval,
    exact_sequence,
    finite_complex,
    finite_complex_sequence,
    finite_real,
    finite_real_sequence,
    nonnegative_real,
    positive_real,
)


def test_schema_is_versioned():
    assert STRICT_ADMISSION_SCHEMA == "PNCS_GREMLIN_STRICT_ADMISSION_V0_1"


@pytest.mark.parametrize("bad", [True, "1.0", 1 + 0j, float("inf"), float("nan")])
def test_finite_real_rejects_coercible_or_nonfinite_values(bad):
    with pytest.raises(GremlinStrictAdmissionError, match="finite real"):
        finite_real(bad, "value")


def test_finite_real_accepts_exact_real_numbers():
    assert finite_real(2, "value") == 2.0
    assert finite_real(-0.25, "value") == -0.25


@pytest.mark.parametrize("bad", [True, "1+2j", complex(float("inf"), 0.0), complex(0.0, float("nan"))])
def test_finite_complex_rejects_coercible_or_nonfinite_values(bad):
    with pytest.raises(GremlinStrictAdmissionError, match="finite complex"):
        finite_complex(bad, "value")


def test_finite_complex_accepts_real_and_complex_number_objects():
    assert finite_complex(2.0, "value") == 2.0 + 0.0j
    assert finite_complex(1.0 + 2.0j, "value") == 1.0 + 2.0j


def test_exact_sequence_rejects_string_as_container():
    with pytest.raises(GremlinStrictAdmissionError, match="explicit iterable container"):
        exact_sequence("123", "values")


def test_real_sequence_rejects_coercible_members_and_enforces_shape():
    with pytest.raises(GremlinStrictAdmissionError, match=r"values\[1\]"):
        finite_real_sequence((1.0, "2.0"), "values")
    with pytest.raises(GremlinStrictAdmissionError, match="exactly 3"):
        finite_real_sequence((1.0, 2.0), "values", exact_length=3)
    assert finite_real_sequence((1, 2.5, -3), "values", exact_length=3) == (1.0, 2.5, -3.0)


def test_complex_sequence_rejects_coercible_members():
    with pytest.raises(GremlinStrictAdmissionError, match=r"state\[1\]"):
        finite_complex_sequence((1.0 + 0.0j, "2+0j"), "state")


def test_numeric_domain_helpers_fail_closed():
    assert positive_real(0.5, "scale") == 0.5
    assert nonnegative_real(0.0, "tolerance") == 0.0
    assert closed_unit_interval(1.0, "weight") == 1.0

    with pytest.raises(GremlinStrictAdmissionError, match="strictly positive"):
        positive_real(0.0, "scale")
    with pytest.raises(GremlinStrictAdmissionError, match="non-negative"):
        nonnegative_real(-1e-9, "tolerance")
    with pytest.raises(GremlinStrictAdmissionError, match=r"\[0,1\]"):
        closed_unit_interval(1.01, "weight")


def test_custom_error_type_preserves_caller_contract():
    class DomainError(RuntimeError):
        pass

    with pytest.raises(DomainError, match="finite real"):
        finite_real("1.0", "phase", error_type=DomainError)


def test_nonfinite_sequence_member_fails_before_math():
    with pytest.raises(GremlinStrictAdmissionError, match=r"vector\[1\]"):
        finite_real_sequence((1.0, math.inf, 2.0), "vector")
