from __future__ import annotations

from fractions import Fraction
from math import isclose, log, pi

import pytest

from phasenav_natural_code.golden_mean_dynamics_v01 import (
    FIREWALLS,
    KAPPA,
    SOURCE_COMMITS,
    admissible_word_count,
    artin_mazur_series_coefficients,
    coding_fraction,
    collatz_parity_prefix,
    critical_dimension,
    exact_period_point_count,
    finite_euler_product_matches_zeta,
    finite_shift_conjugacy_holds,
    fixed_point_count,
    hausdorff_dimension,
    iter_admissible_words,
    lucas,
    orbit_euler_product_coefficients,
    positive_integer_witness_for_admissible_word,
    pressure,
    pressure_slope,
    primitive_orbit_count,
    topological_entropy,
    transfer_power,
    weighted_positive_pole,
)


def test_exact_finite_collatz_language_and_constructive_witnesses() -> None:
    for length in range(0, 9):
        words = tuple(iter_admissible_words(length))
        assert len(words) == admissible_word_count(length)
        assert len(words) == len(set(words))
        for word in words:
            assert "11" not in word
            witness = positive_integer_witness_for_admissible_word(word)
            assert witness > 0
            assert collatz_parity_prefix(witness, length) == word


def test_finite_coding_conjugacy_is_exact_over_fractions() -> None:
    for length in range(0, 10):
        for word in iter_admissible_words(length):
            assert finite_shift_conjugacy_holds(word)
            q = coding_fraction(word)
            assert isinstance(q, Fraction)
            assert Fraction(0, 1) <= q <= Fraction(2, 3)


def test_transfer_fibonacci_power_and_word_count() -> None:
    expected = {
        0: ((1, 0), (0, 1)),
        1: ((1, 1), (1, 0)),
        2: ((2, 1), (1, 1)),
        3: ((3, 2), (2, 1)),
        8: ((34, 21), (21, 13)),
    }
    for n, matrix in expected.items():
        assert transfer_power(n) == matrix


def test_entropy_dimension_kappa_and_pressure_crosswalk() -> None:
    d = critical_dimension()
    assert isclose(d, hausdorff_dimension(), rel_tol=0.0, abs_tol=1e-15)
    assert isclose(d, 0.6942419136306174, rel_tol=0.0, abs_tol=1e-15)
    assert isclose(topological_entropy(), log((1.0 + 5.0**0.5) / 2.0), rel_tol=0.0, abs_tol=1e-15)
    assert isclose(pressure(d), 0.0, rel_tol=0.0, abs_tol=2e-16)
    assert isclose(-pressure_slope(), 24.0 * pi * KAPPA, rel_tol=0.0, abs_tol=2e-16)
    assert isclose(weighted_positive_pole(d), 1.0, rel_tol=0.0, abs_tol=2e-15)


def test_lucas_periodic_points_and_primitive_orbits() -> None:
    expected_primitive = (1, 1, 1, 1, 2, 2, 4, 5, 8, 11, 18, 25)
    expected_fixed = (1, 3, 4, 7, 11, 18, 29, 47, 76, 123, 199, 322)
    for n, (primitive, fixed) in enumerate(zip(expected_primitive, expected_fixed), start=1):
        assert lucas(n) == fixed
        assert fixed_point_count(n) == fixed
        assert primitive_orbit_count(n) == primitive
        assert exact_period_point_count(n) == n * primitive


def test_primitive_orbit_euler_product_matches_artin_mazur_to_finite_order() -> None:
    for degree in range(0, 17):
        assert finite_euler_product_matches_zeta(degree)
        assert orbit_euler_product_coefficients(degree) == artin_mazur_series_coefficients(degree)


def test_provenance_and_claim_firewalls_are_pinned() -> None:
    assert SOURCE_COMMITS["tir_cp1_dyadic_fractal"] == "2c23cc50357c136cf21e14a8f9552a30e8496489"
    assert SOURCE_COMMITS["tir_primitive_orbit_euler_product"] == "18947402100145b5e8b88865ea90e4aab146a8dc"
    required = {
        "RUNTIME_DEFAULT_OFF",
        "PHYSICAL_BINDING_OPEN",
        "RIEMANN_ZETA_FIREWALL",
        "ARITHMETIC_PRIME_FIREWALL",
        "E7_E8_LINEAR_INTERTWINER_NOGO",
        "METRIC_COUPLING_NOT_ACTIVATED",
    }
    assert required.issubset(set(FIREWALLS))


def test_invalid_language_fails_closed() -> None:
    from phasenav_natural_code.golden_mean_dynamics_v01 import GoldenMeanKernelError

    with pytest.raises(GoldenMeanKernelError):
        positive_integer_witness_for_admissible_word("11")
    with pytest.raises(GoldenMeanKernelError):
        coding_fraction("102")
