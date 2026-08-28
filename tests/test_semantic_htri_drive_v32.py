from __future__ import annotations

import numpy as np

from phasenav_natural_code.semantic_address_v31 import build_semantic_trajectory
from phasenav_natural_code.semantic_htri_drive_v32 import (
    DEFAULT_DT,
    DriveSnapshot,
    controlled_step,
    execute_trajectory,
)
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
        source_id="TEST_V32_DETERMINISTIC_SNAPSHOT",
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


def test_inverse_dynamics_hits_target_in_one_step():
    target = trajectories()[0].addresses[0].phase36
    step = controlled_step(snapshot(), target, dt=DEFAULT_DT)
    assert step.receipt["max_target_residual_rad"] < 1e-12
    assert step.receipt["rms_target_residual_rad"] < 1e-12
    assert np.max(np.abs(np.angle(np.exp(1j * (np.asarray(target) - step.phi_next))))) < 1e-12


def test_controlled_step_preserves_symmetric_coupling_and_hermitian_hamiltonian():
    target = trajectories()[0].addresses[0].phase36
    step = controlled_step(snapshot(), target)
    assert np.max(np.abs(step.g_next - step.g_next.T)) < 1e-12
    assert step.receipt["hermiticity_error"] < 1e-12
    assert np.max(np.abs(step.H - step.H.conj().T)) < 1e-12


def test_control_effort_is_explicit_and_finite():
    target = trajectories()[0].addresses[0].phase36
    rec = controlled_step(snapshot(), target).receipt
    assert np.isfinite(rec["control_l2"])
    assert np.isfinite(rec["control_rms"])
    assert np.isfinite(rec["control_max_abs"])
    assert rec["control_l2"] > 0.0
    assert rec["drive_role"] == "EXACT_ONE_STEP_INVERSE_DYNAMICS_REFERENCE"


def test_full_execution_is_deterministic():
    traj = trajectories()[0]
    a = execute_trajectory(snapshot(), traj)
    b = execute_trajectory(snapshot(), traj)
    assert a["execution_id"] == b["execution_id"]
    assert a["receipt_sha256"] == b["receipt_sha256"]
    assert np.array_equal(a["final_phi"], b["final_phi"])
    assert np.array_equal(a["final_g"], b["final_g"])
    assert np.array_equal(a["U_total"], b["U_total"])


def test_full_execution_passes_numeric_invariants():
    result = execute_trajectory(snapshot(), trajectories()[0])
    assert result["max_target_residual_rad"] < 1e-12
    assert result["max_hermiticity_error"] < 1e-12
    assert result["max_cumulative_unitarity_error"] < 1e-11
    assert result["new_pnv_opcodes"] == 0
    assert result["execution_status"] == "MODEL_LEVEL_CONTROLLED_HTRI_QHTRI_REFERENCE"
    assert result["runtime_role"] == "READ_ONLY_LIVE_DERIVED_COPY"


def test_original_reverse_shuffle_remain_distinct_after_time_ordered_qhtri():
    original, reverse, shuffle = trajectories()
    a = execute_trajectory(snapshot(), original)
    b = execute_trajectory(snapshot(), reverse)
    c = execute_trajectory(snapshot(), shuffle)
    assert len({a["execution_id"], b["execution_id"], c["execution_id"]}) == 3
    assert len({a["final_g_sha256"], b["final_g_sha256"], c["final_g_sha256"]}) == 3
    assert len({a["U_total_sha256"], b["U_total_sha256"], c["U_total_sha256"]}) == 3


def test_reverse_ends_on_original_first_target_and_original_on_last_target():
    original, reverse, _ = trajectories()
    a = execute_trajectory(snapshot(), original)
    b = execute_trajectory(snapshot(), reverse)
    first = np.asarray(original.addresses[0].phase36)
    last = np.asarray(original.addresses[-1].phase36)
    assert np.max(np.abs(np.angle(np.exp(1j * (last - a["final_phi"]))))) < 1e-12
    assert np.max(np.abs(np.angle(np.exp(1j * (first - b["final_phi"]))))) < 1e-12
