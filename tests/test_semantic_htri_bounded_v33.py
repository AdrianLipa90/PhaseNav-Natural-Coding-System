from __future__ import annotations

import numpy as np

from phasenav_natural_code.semantic_address_v31 import build_semantic_trajectory
from phasenav_natural_code.semantic_htri_bounded_v33 import (
    bounded_step,
    execute_bounded_trajectory,
    track_target,
)
from phasenav_natural_code.semantic_htri_drive_v32 import DriveSnapshot
from phasenav_natural_code.semantic_sequence_v31 import (
    build_nisaba_frozen_roles,
    compile_semantic_sequence,
)

SOURCE_SHA = "0a6c02eda6b5e0b890e1ea5106a9c5b302cc4ef52de426cea0187134ae27750d"


def snapshot() -> DriveSnapshot:
    phi = np.linspace(0.07, 5.91, 36, dtype=np.float64)
    omega = 39.6 + np.linspace(-0.12, 0.12, 36, dtype=np.float64)
    i = np.arange(36, dtype=np.float64)
    g = 0.18 * np.cos((i[:, None] - i[None, :]) * np.pi / 18.0)
    g = 0.5 * (g + g.T)
    np.fill_diagonal(g, 0.0)
    flavor = np.array([0.31, 0.72, 0.23, 0.56, 0.48, 0.5], dtype=np.float64)
    tau = np.linspace(0.21, 0.49, 36, dtype=np.float64)
    gravity = np.array([0.0, 1.17, 0.3, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float64)
    return DriveSnapshot.build(
        phi=phi, omega=omega, g=g, flavor=flavor, tau=tau, gravity=gravity,
        source_id="TEST_V33_DETERMINISTIC_SNAPSHOT",
    )


def trajectories():
    roles = build_nisaba_frozen_roles(source_digest_sha256=SOURCE_SHA)
    original = compile_semantic_sequence(roles)
    reverse = compile_semantic_sequence(tuple(reversed(roles)))
    shuffle = compile_semantic_sequence((roles[3], roles[6], roles[0], roles[4], roles[2], roles[5], roles[1]))
    return tuple(
        build_semantic_trajectory(x.ordered_semantic_id, x.content_ids)
        for x in (original, reverse, shuffle)
    )


def test_bounded_step_respects_component_limit():
    target = trajectories()[0].addresses[0].phase36
    step = bounded_step(snapshot(), target, u_max=25.0)
    assert np.max(np.abs(step.control)) <= 25.0 + 1e-12
    assert step.receipt["control_max_abs"] <= 25.0 + 1e-12
    assert 0.0 <= step.receipt["saturation_fraction"] <= 1.0


def test_very_low_bound_fails_target_timeout():
    target = trajectories()[0].addresses[0].phase36
    result = track_target(
        snapshot(), target, u_max=1.0,
        tolerance_rad=1e-6, max_ticks=8, settle_consecutive=3,
    )
    assert result.receipt["status"] == "FAIL_TARGET_SETTLING_TIMEOUT"
    assert result.receipt["settling_tick"] is None


def test_sufficient_bound_settles_target():
    target = trajectories()[0].addresses[0].phase36
    result = track_target(
        snapshot(), target, u_max=400.0,
        tolerance_rad=1e-6, max_ticks=8, settle_consecutive=3,
    )
    assert result.receipt["status"] == "PASS_TARGET_SETTLED"
    assert result.receipt["settling_tick"] is not None
    assert result.receipt["last_max_target_residual_rad"] <= 1e-6


def test_full_bounded_execution_passes_at_high_reference_bound():
    result = execute_bounded_trajectory(
        snapshot(), trajectories()[0], u_max=400.0,
        tolerance_rad=1e-6, max_ticks_per_target=8, settle_consecutive=3,
    )
    assert result["status"] == "PASS_BOUNDED_MULTI_TICK_TRAJECTORY"
    assert result["targets_completed"] == 7
    assert result["max_hermiticity_error"] < 1e-12
    assert result["max_cumulative_unitarity_error"] < 1e-10
    assert result["max_control_abs"] <= 400.0 + 1e-12
    assert result["new_pnv_opcodes"] == 0


def test_original_reverse_shuffle_distinct_after_bounded_time_ordered_execution():
    original, reverse, shuffle = trajectories()
    results = [
        execute_bounded_trajectory(
            snapshot(), x, u_max=400.0,
            tolerance_rad=1e-6, max_ticks_per_target=8, settle_consecutive=3,
        )
        for x in (original, reverse, shuffle)
    ]
    assert all(r["status"] == "PASS_BOUNDED_MULTI_TICK_TRAJECTORY" for r in results)
    assert len({r["execution_id"] for r in results}) == 3
    assert len({r["final_g_sha256"] for r in results}) == 3
    assert len({r["U_total_sha256"] for r in results}) == 3


def test_bounded_execution_is_deterministic():
    traj = trajectories()[0]
    a = execute_bounded_trajectory(
        snapshot(), traj, u_max=400.0,
        tolerance_rad=1e-6, max_ticks_per_target=8, settle_consecutive=3,
    )
    b = execute_bounded_trajectory(
        snapshot(), traj, u_max=400.0,
        tolerance_rad=1e-6, max_ticks_per_target=8, settle_consecutive=3,
    )
    assert a["execution_id"] == b["execution_id"]
    assert a["receipt_sha256"] == b["receipt_sha256"]
    assert np.array_equal(a["U_total"], b["U_total"])
