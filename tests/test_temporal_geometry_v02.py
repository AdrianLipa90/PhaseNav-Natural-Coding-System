from __future__ import annotations

import math
import cmath
import pytest

from phasenav_natural_code.temporal_geometry_v02 import (
    DIM,
    TAU,
    EPISTEMIC_STATUS,
    PROMOTION_TRACK,
    RiemannConformalTemplateReceipt,
    TemporalConformalPoint,
    TemporalDualPairReceipt,
    TemporalPhaseProjection36,
    TemporalDualPairProjection36,
    TemporalWaveState36,
    TemporalWaveCorpuscleReceipt,
    TemporalGeometryV02Error,
    riemann_center,
    riemann_cayley,
    riemann_functional_dual,
    project_observation_now,
    gaussian_observation_now,
)


def grid36(now: float = 0.0) -> tuple[float, ...]:
    return tuple(now + float(i - 18) for i in range(DIM))


def amplitudes36() -> tuple[complex, ...]:
    return tuple(complex(math.cos(i / 7.0), math.sin(i / 7.0)) for i in range(DIM))


@pytest.mark.parametrize("s", [
    0.5 + 1j,
    0.5 + 14.134725j,
    0.2 + 3.0j,
    0.8 - 4.25j,
    1.25 + 0.5j,
])
def test_riemann_exact_inversion_template(s: complex) -> None:
    z = riemann_cayley(s)
    dual = riemann_cayley(riemann_functional_dual(s))
    assert abs(dual - 1.0 / z) < 1e-12


def test_riemann_center_turns_functional_symmetry_into_sign_flip() -> None:
    s = 0.37 + 8.2j
    assert abs(riemann_center(1.0 - s) + riemann_center(s)) < 1e-15


@pytest.mark.parametrize("t", [0.0, 0.1, 1.0, 14.134725, -2.5, 1000.0])
def test_critical_line_maps_to_unit_circle(t: float) -> None:
    receipt = RiemannConformalTemplateReceipt(0.5 + 1j * t)
    assert receipt.symmetry_pass
    assert receipt.on_critical_line
    assert receipt.on_unit_circle
    assert receipt.critical_equivalence_pass
    assert receipt.critical_line_residual < 1e-12


@pytest.mark.parametrize("sigma", [0.1, 0.2, 0.4, 0.8, 1.2])
def test_off_critical_line_maps_off_unit_circle(sigma: float) -> None:
    if sigma == 0.5:
        pytest.skip()
    receipt = RiemannConformalTemplateReceipt(sigma + 2.0j)
    assert receipt.symmetry_pass
    assert not receipt.on_critical_line
    assert not receipt.on_unit_circle
    assert receipt.critical_equivalence_pass


def test_temporal_now_maps_to_minus_one_fixed_point() -> None:
    point = TemporalConformalPoint(42.0, 42.0, 3.0)
    assert point.branch == "NOW"
    assert point.u == 0.0
    assert point.w == 0.0j
    assert point.z == -1.0 + 0.0j
    assert abs(1.0 / point.z - point.z) == 0.0
    assert point.phase == pytest.approx(math.pi)


@pytest.mark.parametrize("delta", [0.0, 0.125, 1.0, 7.0, 100.0])
def test_temporal_past_future_are_exact_inversion_duals(delta: float) -> None:
    receipt = TemporalDualPairReceipt(now=10.0, delta=delta, scale=2.5)
    assert receipt.passed
    assert receipt.inversion_residual < 1e-12
    assert receipt.conjugation_residual < 1e-12
    assert receipt.unit_circle_residual < 1e-12
    assert receipt.now_fixed_point_residual == 0.0


@pytest.mark.parametrize("time_value", [-100.0, -1.0, 0.0, 1.0, 100.0])
def test_real_temporal_axis_maps_to_unit_circle(time_value: float) -> None:
    point = TemporalConformalPoint(time_value, now=0.0, scale=4.0)
    assert point.modulus == pytest.approx(1.0, abs=1e-12)
    assert 0.0 <= point.phase < TAU


def test_temporal_reflection_changes_branch_and_inverts_phase_point() -> None:
    past = TemporalConformalPoint(-3.0, now=0.0, scale=2.0)
    future = past.dual
    assert past.branch == "PAST"
    assert future.branch == "FUTURE"
    assert future.time_value == 3.0
    assert future.z == pytest.approx(1.0 / past.z)
    assert future.z == pytest.approx(past.z.conjugate())


def test_t36_projection_is_exactly_36_and_deterministic() -> None:
    times = grid36()
    a = TemporalPhaseProjection36(times, now=0.0, scale=5.0)
    b = TemporalPhaseProjection36(times, now=0.0, scale=5.0)
    assert len(a.theta) == DIM
    assert len(a.z_coordinates) == DIM
    assert a.projection_id == b.projection_id
    assert all(0.0 <= theta < TAU for theta in a.theta)
    assert all(abs(abs(z) - 1.0) < 1e-12 for z in a.z_coordinates)
    assert a.branches.count("NOW") == 1
    assert a.payload["space"] == "T^36"
    assert a.payload["epistemic_status"] == EPISTEMIC_STATUS
    assert a.payload["promotion_track"] == PROMOTION_TRACK


def test_t36_projection_preserves_reflection_inversion_for_paired_samples() -> None:
    projection = TemporalPhaseProjection36(grid36(), now=0.0, scale=3.0)
    by_time = {t: z for t, z in zip(projection.times, projection.z_coordinates)}
    for t in range(1, 18):
        assert by_time[float(t)] == pytest.approx(1.0 / by_time[-float(t)])


def test_wave36_normalizes_amplitudes_and_probability_partition() -> None:
    state = TemporalWaveState36(grid36(), amplitudes36(), now=0.0, scale=4.0)
    assert state.probability_total == pytest.approx(1.0)
    assert state.past_probability + state.now_probability + state.future_probability == pytest.approx(1.0)
    assert state.support_size == DIM
    assert state.state_id.startswith("pncs:temporal-wave36-state:sha256:")


def test_exact_now_projector_localizes_to_one_coordinate() -> None:
    state = TemporalWaveState36(grid36(), amplitudes36(), now=0.0, scale=4.0)
    receipt = project_observation_now(state)
    assert receipt.mode == "EXACT_NOW_PROJECTOR"
    assert receipt.selected_index == 18
    assert receipt.post_support == 1
    assert receipt.after_state.now_probability == pytest.approx(1.0)
    assert receipt.after_state.past_probability == pytest.approx(0.0)
    assert receipt.after_state.future_probability == pytest.approx(0.0)
    assert receipt.post_variance == pytest.approx(0.0)
    assert receipt.pre_variance > receipt.post_variance
    assert receipt.receipt_id.startswith("pncs:temporal-observation:sha256:")


@pytest.mark.parametrize("sigma", [0.25, 0.5, 1.0, 3.0])
def test_gaussian_observation_reduces_temporal_variance(sigma: float) -> None:
    state = TemporalWaveState36(grid36(), amplitudes36(), now=0.0, scale=4.0)
    receipt = gaussian_observation_now(state, sigma)
    assert receipt.mode == "FINITE_GAUSSIAN_NOW_LOCALIZATION"
    assert receipt.kernel_sigma == sigma
    assert receipt.after_state.probability_total == pytest.approx(1.0)
    assert receipt.post_variance < receipt.pre_variance
    assert receipt.after_state.now_probability > state.now_probability


def test_wave_corpuscle_receipt_binds_wave_and_localized_state() -> None:
    state = TemporalWaveState36(grid36(), amplitudes36(), now=0.0, scale=4.0)
    observation = project_observation_now(state)
    receipt = TemporalWaveCorpuscleReceipt(state, observation)
    payload = receipt.payload
    assert payload["wave_support_before"] == DIM
    assert payload["localized_support_after"] == 1
    assert payload["now_probability_after"] == pytest.approx(1.0)
    assert payload["pre_variance"] > payload["post_variance"]
    assert receipt.receipt_id.startswith("pncs:temporal-wave-corpuscle:sha256:")


def test_exact_now_projector_requires_one_exact_now_sample() -> None:
    times = tuple(float(i + 1) for i in range(DIM))
    state = TemporalWaveState36(times, amplitudes36(), now=0.5, scale=1.0)
    with pytest.raises(TemporalGeometryV02Error):
        project_observation_now(state)


@pytest.mark.parametrize("bad_scale", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_temporal_scale_fails_closed(bad_scale: float) -> None:
    with pytest.raises(TemporalGeometryV02Error):
        TemporalConformalPoint(1.0, 0.0, bad_scale)


def test_wrong_t36_dimension_fails_closed() -> None:
    with pytest.raises(TemporalGeometryV02Error):
        TemporalPhaseProjection36(range(35), now=0.0)


def test_non_monotonic_t36_times_fail_closed() -> None:
    times = list(grid36())
    times[10] = times[9]
    with pytest.raises(TemporalGeometryV02Error):
        TemporalPhaseProjection36(times, now=0.0)


def test_zero_wave_norm_fails_closed() -> None:
    with pytest.raises(TemporalGeometryV02Error):
        TemporalWaveState36(grid36(), [0.0j] * DIM, now=0.0)


def test_invalid_gaussian_sigma_fails_closed() -> None:
    state = TemporalWaveState36(grid36(), amplitudes36(), now=0.0)
    with pytest.raises(TemporalGeometryV02Error):
        gaussian_observation_now(state, 0.0)


def test_ids_change_when_now_changes() -> None:
    times = grid36()
    a = TemporalPhaseProjection36(times, now=0.0, scale=4.0)
    b = TemporalPhaseProjection36(times, now=0.5, scale=4.0)
    assert a.projection_id != b.projection_id


def test_ids_change_when_scale_changes() -> None:
    times = grid36()
    a = TemporalPhaseProjection36(times, now=0.0, scale=4.0)
    b = TemporalPhaseProjection36(times, now=0.0, scale=5.0)
    assert a.projection_id != b.projection_id


def test_dual_pair_projection36_is_18_pairs_and_36_phases() -> None:
    projection = TemporalDualPairProjection36(tuple(float(i) for i in range(1, 19)), now=0.0, scale=3.0)
    assert len(projection.deltas) == 18
    assert len(projection.theta) == 36
    assert len(projection.z_pairs) == 18
    assert projection.verification_residual < 1e-12
    assert projection.payload["pair_count"] == 18
    assert projection.projection_id.startswith("pncs:temporal-dual-t36-projection:sha256:")


def test_dual_pair_projection_matches_direct_temporal_map() -> None:
    deltas = tuple(float(i) for i in range(1, 19))
    dual = TemporalDualPairProjection36(deltas, now=5.0, scale=2.0)
    direct_times = tuple(sorted([5.0 - d for d in deltas] + [5.0 + d for d in deltas]))
    direct = TemporalPhaseProjection36(direct_times, now=5.0, scale=2.0)
    direct_by_time = {t: z for t, z in zip(direct.times, direct.z_coordinates)}
    for (past_t, future_t), (past_z, future_z) in zip(dual.time_pairs, dual.z_pairs):
        assert past_z == pytest.approx(direct_by_time[past_t])
        assert future_z == pytest.approx(direct_by_time[future_t])


def test_dual_pair_projection_fails_on_wrong_pair_count() -> None:
    with pytest.raises(TemporalGeometryV02Error):
        TemporalDualPairProjection36(range(17), now=0.0)


def test_dual_pair_projection_fails_on_duplicate_deltas() -> None:
    deltas = list(float(i) for i in range(1, 19))
    deltas[10] = deltas[9]
    with pytest.raises(TemporalGeometryV02Error):
        TemporalDualPairProjection36(deltas, now=0.0)
