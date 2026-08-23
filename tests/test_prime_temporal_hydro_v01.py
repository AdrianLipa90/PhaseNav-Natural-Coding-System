from __future__ import annotations

import cmath
import math

import pytest

from phasenav_natural_code.prime_temporal_hydro_v01 import (
    PrimeTemporalV01Error,
    SpectralRegistry,
    TemporalSpectrum,
    advance_continuity,
    critical_line_prime_factor,
    flux_log_scale,
    fs_population_speed,
    fs_temporal_speed,
    make_temporal_hydro_observable,
    odd_branch_support_disjoint,
    orbit_prime_flux,
    prime_flux,
    prime_valuation,
    shortcut_collatz,
    t36_temporal_pairs,
)


def test_prime_valuation_and_log_identity():
    assert prime_valuation(360) == ((2, 3), (3, 2), (5, 1))
    reconstructed = sum(v * math.log(p) for p, v in prime_valuation(360))
    assert reconstructed == pytest.approx(math.log(360), abs=1e-15)


def test_collatz_prime_flux_reconstructs_exact_step_ratio():
    for n in (1, 2, 3, 5, 7, 10, 27, 31):
        nxt = shortcut_collatz(n)
        flux = prime_flux(n)
        assert math.exp(flux_log_scale(flux)) == pytest.approx(nxt / n, rel=1e-14, abs=1e-14)


def test_closed_control_cycle_has_zero_net_prime_flux():
    assert orbit_prime_flux(1, 2) == ()


def test_odd_branch_prime_support_is_disjoint():
    for n in (1, 3, 5, 7, 9, 15, 27, 31, 63, 101):
        assert odd_branch_support_disjoint(n)


def test_critical_line_prime_factor_matches_direct_complex_power():
    prime, delta_v, tau = 5, -2, 3.25
    got = critical_line_prime_factor(prime, delta_v, tau)
    expected = cmath.exp(-(0.5 + 1j * tau) * delta_v * math.log(prime))
    assert got == pytest.approx(expected, rel=1e-14, abs=1e-14)


def test_prime_log_registry_is_content_addressed_and_scaled():
    reg = SpectralRegistry.from_primes((2, 3, 5), omega_scale=2.0, source_id="test:primes")
    assert reg.registry_kind == "PRIME_LOG"
    assert reg.angular_frequencies == pytest.approx(tuple(2.0 * math.log(p) for p in (2, 3, 5)))
    assert reg.registry_id == SpectralRegistry.from_primes((2, 3, 5), omega_scale=2.0, source_id="test:primes").registry_id


def test_single_mode_has_no_internal_clock():
    reg = SpectralRegistry("EXPLICIT", (7.0,), ("mode",), "test:single", 1.0)
    spectrum = TemporalSpectrum(reg, (1.0,))
    for t in (0.0, 0.1, 10.0):
        assert spectrum.coherence(t) == pytest.approx(1.0)
        assert spectrum.fuzziness(t) == pytest.approx(0.0)
    assert spectrum.phase_speed() == pytest.approx(0.0)


def test_two_mode_fuzziness_and_fs_speed():
    reg = SpectralRegistry("EXPLICIT", (1.0, 3.0), ("a", "b"), "test:two", 1.0)
    spectrum = TemporalSpectrum(reg, (0.5, 0.5))
    assert spectrum.phase_speed() == pytest.approx(1.0)
    assert spectrum.fuzziness(math.pi / 2.0) == pytest.approx(1.0, abs=1e-14)
    assert spectrum.fuzziness(math.pi) == pytest.approx(0.0, abs=1e-14)


def test_continuity_accumulates_through_revival():
    reg = SpectralRegistry("EXPLICIT", (1.0, 3.0), ("a", "b"), "test:two", 1.0)
    spectrum = TemporalSpectrum(reg, (0.5, 0.5))
    speed = fs_temporal_speed(spectrum)
    lam = 0.0
    lam = advance_continuity(lam, speed, math.pi / 2)
    at_max_fuzz = lam
    lam = advance_continuity(lam, speed, math.pi / 2)
    assert spectrum.fuzziness(math.pi) == pytest.approx(0.0, abs=1e-14)
    assert lam > at_max_fuzz > 0.0


def test_population_flow_adds_fs_structural_speed():
    probs = (0.5, 0.5)
    rates = (0.1, -0.1)
    population = fs_population_speed(probs, rates)
    assert population == pytest.approx(0.1)
    reg = SpectralRegistry("EXPLICIT", (1.0, 3.0), ("a", "b"), "test:flow", 1.0)
    spectrum = TemporalSpectrum(reg, probs)
    assert fs_temporal_speed(spectrum, probability_rates=rates) == pytest.approx(math.sqrt(1.0 + 0.01))


def test_t36_temporal_pair_geometry():
    frequencies = tuple(float(i + 1) for i in range(18))
    center = 0.7
    t = 0.125
    theta = t36_temporal_pairs(frequencies, t=t, center_phase=center)
    assert len(theta) == 36
    assert all(0.0 <= x < math.tau for x in theta)
    for j, omega in enumerate(frequencies):
        left = theta[2 * j]
        right = theta[2 * j + 1]
        assert left == pytest.approx((center - omega * t) % math.tau)
        assert right == pytest.approx((center + omega * t) % math.tau)


def test_temporal_hydro_observable_is_typed_and_non_authoritative():
    reg = SpectralRegistry.from_primes((2, 3), omega_scale=1.0, source_id="test:prime-registry")
    spectrum = TemporalSpectrum(reg, (0.4, 0.6))
    obs = make_temporal_hydro_observable(
        spectrum,
        t=0.5,
        previous_continuity=2.0,
        delta_t=0.1,
        t36_realization_id="pncs:t36:test",
    )
    assert obs.observable_id.startswith("pncs:temporal-hydro-observable:sha256:")
    assert obs.continuity_length >= 2.0
    assert obs.routing_feedback_opened is False
    assert obs.external_effects is False
    assert obs.semantic_identity_modified is False
    assert obs.laboratory_time_modified is False
    assert obs.payload["scientific_promotion"] is False


@pytest.mark.parametrize(
    "call",
    [
        lambda: prime_valuation(True),
        lambda: prime_valuation(0),
        lambda: prime_flux(3, 999),
        lambda: SpectralRegistry("EXPLICIT", (), (), "x"),
        lambda: TemporalSpectrum(SpectralRegistry("EXPLICIT", (1.0,), ("a",), "x"), (0.5,)),
        lambda: fs_population_speed((1.0, 0.0), (-0.1, 0.1)),
        lambda: t36_temporal_pairs((1.0,) * 17, t=0.0, center_phase=0.0),
    ],
)
def test_invalid_inputs_fail_closed(call):
    with pytest.raises(PrimeTemporalV01Error):
        call()
