from __future__ import annotations

import numpy as np
import pytest

from phasenav_natural_code.semantic_address_v31 import build_semantic_trajectory
from phasenav_natural_code.semantic_htri_drive_v32 import (
    DEFAULT_DT,
    DriveSnapshot,
    SemanticHTRIDriveV32Error,
    controlled_step,
    digest,
    execute_trajectory,
    qhtri_graph_hamiltonian,
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


def test_snapshot_rejects_implicit_numeric_coercion_and_false_36d_shape():
    base = snapshot()
    kwargs = dict(
        omega=base.omega,
        g=base.g,
        flavor=base.flavor,
        tau=base.tau,
        gravity=base.gravity,
        source_id="STRICT_SNAPSHOT",
    )
    for bad_phi in (
        ["1.0"] * 36,
        [True] * 36,
        np.ones((6, 6), dtype=np.float64),
    ):
        with pytest.raises(SemanticHTRIDriveV32Error, match="phi"):
            DriveSnapshot.build(phi=bad_phi, **kwargs)


def test_snapshot_rejects_nonreal_matrix_and_nonvector_metadata():
    base = snapshot()
    with pytest.raises(SemanticHTRIDriveV32Error, match="g"):
        DriveSnapshot.build(
            phi=base.phi,
            omega=base.omega,
            g=np.ones((36, 36), dtype=bool),
            flavor=base.flavor,
            tau=base.tau,
            gravity=base.gravity,
            source_id="BAD_G",
        )
    with pytest.raises(SemanticHTRIDriveV32Error, match="flavor"):
        DriveSnapshot.build(
            phi=base.phi,
            omega=base.omega,
            g=base.g,
            flavor=np.ones((2, 3), dtype=np.float64),
            tau=base.tau,
            gravity=base.gravity,
            source_id="BAD_FLAVOR",
        )
    with pytest.raises(SemanticHTRIDriveV32Error, match="source_id"):
        DriveSnapshot.build(
            phi=base.phi,
            omega=base.omega,
            g=base.g,
            flavor=base.flavor,
            tau=base.tau,
            gravity=base.gravity,
            source_id="   ",
        )


def test_parent_dt_and_target_admission_reject_bool_strings_and_shape_coercion():
    target = trajectories()[0].addresses[0].phase36
    for bad_dt in (True, "0.01", object()):
        with pytest.raises(SemanticHTRIDriveV32Error, match="dt"):
            controlled_step(snapshot(), target, dt=bad_dt)  # type: ignore[arg-type]
    with pytest.raises(SemanticHTRIDriveV32Error, match="target36"):
        controlled_step(snapshot(), np.ones((6, 6), dtype=np.float64))
    with pytest.raises(SemanticHTRIDriveV32Error, match="target36"):
        controlled_step(snapshot(), ["0.1"] * 36)  # type: ignore[list-item]


def test_hamiltonian_strengths_require_exact_finite_real_inputs():
    state = snapshot()
    for field in ("coupling_strength", "detuning_strength"):
        for bad in (True, "0.7", object()):
            kwargs = {field: bad}
            with pytest.raises(SemanticHTRIDriveV32Error, match=field):
                qhtri_graph_hamiltonian(
                    state.omega,
                    state.g,
                    **kwargs,  # type: ignore[arg-type]
                )


def test_digest_rejects_non_string_mapping_keys_instead_of_stringifying_them():
    with pytest.raises(SemanticHTRIDriveV32Error, match="mapping keys must be strings"):
        digest({1: "value"})
