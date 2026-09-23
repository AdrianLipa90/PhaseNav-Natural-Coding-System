from __future__ import annotations

import numpy as np
import pytest

from phasenav_natural_code.orch_orbital_time_v27 import (
    SubjectiveTimeBinding,
    SubjectiveTimeKernel,
)
from phasenav_natural_code.pnlf_orbital_memory_v01 import (
    OrbitalState,
    PNLFHeader,
    admit_liminal_segment,
    advance_liminal_segment,
    build_state_checkpoint,
    open_liminal_segment,
)
from phasenav_natural_code.qhtri_pnlf_trajectory_binding_v01 import (
    QHTRIPNLFTrajectoryBindingError,
    build_qhtri_pnlf_trajectory_binding,
    require_segment_trajectory_commitment,
)
from phasenav_natural_code.semantic_htri_drive_v32 import (
    DriveSnapshot,
    controlled_step,
)


def d(ch: str) -> str:
    return ch * 64


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
        phi=phi,
        omega=omega,
        g=g,
        flavor=flavor,
        tau=tau,
        gravity=gravity,
        source_id="TEST_QHTRI_PNLF_TRAJECTORY_BINDING",
    )


def htri_receipts():
    state = snapshot()
    target = state.phi.copy()
    return tuple(
        dict(controlled_step(state, target, dt=dt).receipt)
        for dt in (0.01, 0.02, 0.015)
    )


def time_binding(kernel: SubjectiveTimeKernel, dt: float, g: float) -> SubjectiveTimeBinding:
    return SubjectiveTimeBinding(
        kernel=kernel,
        radius=0.5,
        coherence=0.8,
        defect=0.1,
        semantic_mass=0.3,
        attractor_influence=0.4,
        substrate_lapse=g,
        coordinate_dt=dt,
        combined_g=g,
        proper_dt=dt * g,
    )


def bindings(kernel: SubjectiveTimeKernel):
    return (
        time_binding(kernel, 0.01, 0.8),
        time_binding(kernel, 0.02, 1.25),
        time_binding(kernel, 0.015, 0.6),
    )


def orbital(tau: float, model_id: str) -> OrbitalState:
    return OrbitalState(
        attractor_id="identity:mummu-test",
        orbital_band="O4",
        r_phase=0.7,
        phase=1.25,
        E_bind=-0.8,
        L_phase=0.14,
        semantic_mass=0.42,
        orbit_period=2.5,
        winding=1.5,
        proper_time=tau,
        memory_affinity=0.75,
        mass_model_id="pncs:test-mass:v1",
        orbit_quantizer_id="pnlf:test-quantizer:v1",
        proper_time_model_id=model_id,
    )


def header(kernel: SubjectiveTimeKernel, *, basis: str = "pncs:t36:mummu-test:v1") -> PNLFHeader:
    return PNLFHeader(
        file_id="pnlf:file:mummu-qhtri-test",
        object_id="pnlf:object:mummu-qhtri-test",
        genesis_anchor=d("a"),
        basis_id="pnlf:basis:mummu-qhtri-test",
        schema_binding="PNLF_ORBITAL_MEMORY_V0_1",
        storage_profile="PNLF_NATIVE",
        mass_model_id="pncs:test-mass:v1",
        orbit_quantizer_id="pnlf:test-quantizer:v1",
        proper_time_model_id=kernel.kernel_id,
        t36_basis_id=basis,
    )


def checkpoint(tau: float, kernel: SubjectiveTimeKernel, *, predecessor=None, content="b"):
    return build_state_checkpoint(
        object_id="pnlf:object:mummu-qhtri-test",
        tau=tau,
        content_commitment=d(content),
        predecessor_checkpoint_id=predecessor,
        active_m_layers=("M3",),
        orbital_state=orbital(tau, kernel.kernel_id),
        t36_witness_sha256=d("c"),
        reduction_witness_sha256=d("d"),
        consolidation_witness_sha256=d("e"),
        relation_braid_commitment=d("f"),
    )


def opened_segment(kernel: SubjectiveTimeKernel):
    left = checkpoint(2.0, kernel)
    opened = open_liminal_segment(
        segment_id="pnlf:segment:mummu-qhtri-test",
        source_checkpoint=left,
        tau_start=2.0,
        active_m_layers=("M3",),
        relation_braid_commitment=d("1"),
        trajectory_commitment=d("2"),
        modulation_commitment=d("3"),
        t36_trajectory_commitment=d("4"),
    )
    return left, opened


def candidate_segment(kernel: SubjectiveTimeKernel):
    left, opened = opened_segment(kernel)
    advanced = advance_liminal_segment(
        opened,
        tau_cursor=2.042,
        trajectory_commitment=d("5"),
        t36_trajectory_commitment=d("6"),
    )
    return left, opened, advanced


def test_real_source_objects_emit_deterministic_candidate_commitment():
    kernel = SubjectiveTimeKernel()
    _, _, segment = candidate_segment(kernel)
    a = build_qhtri_pnlf_trajectory_binding(
        header(kernel),
        segment,
        htri_receipts(),
        bindings(kernel),
    )
    b = build_qhtri_pnlf_trajectory_binding(
        header(kernel),
        segment,
        htri_receipts(),
        bindings(kernel),
    )
    assert a.commitment == b.commitment
    assert len(a.commitment) == 64
    assert a.binding_id.endswith(a.commitment)
    assert a.payload["tau_end"] == pytest.approx(2.042)
    assert sum(x["proper_dt"] for x in a.payload["steps"]) == pytest.approx(0.042)


def test_candidate_can_be_rebound_into_open_segment_without_identity_cycle():
    kernel = SubjectiveTimeKernel()
    _, opened, segment = candidate_segment(kernel)
    binding = build_qhtri_pnlf_trajectory_binding(
        header(kernel),
        segment,
        htri_receipts(),
        bindings(kernel),
    )
    rebound = advance_liminal_segment(
        opened,
        tau_cursor=2.042,
        trajectory_commitment=d("5"),
        t36_trajectory_commitment=binding.commitment,
    )
    require_segment_trajectory_commitment(binding, rebound)


def test_binding_survives_ordinary_pnlf_admission():
    kernel = SubjectiveTimeKernel()
    left, opened, segment = candidate_segment(kernel)
    binding = build_qhtri_pnlf_trajectory_binding(
        header(kernel),
        segment,
        htri_receipts(),
        bindings(kernel),
    )
    rebound = advance_liminal_segment(
        opened,
        tau_cursor=2.042,
        trajectory_commitment=d("5"),
        t36_trajectory_commitment=binding.commitment,
    )
    right = checkpoint(
        2.042,
        kernel,
        predecessor=left.checkpoint_object_id,
        content="8",
    )
    admitted = admit_liminal_segment(
        rebound,
        right_checkpoint=right,
        resolution_witness_sha256=d("9"),
    )
    assert admitted.resolution_state == "ADMITTED"
    assert admitted.tau_end == admitted.tau_cursor == pytest.approx(2.042)
    require_segment_trajectory_commitment(binding, admitted)


def test_stale_segment_commitment_fails_closed():
    kernel = SubjectiveTimeKernel()
    _, _, segment = candidate_segment(kernel)
    binding = build_qhtri_pnlf_trajectory_binding(
        header(kernel),
        segment,
        htri_receipts(),
        bindings(kernel),
    )
    with pytest.raises(
        QHTRIPNLFTrajectoryBindingError,
        match="t36_trajectory_commitment",
    ):
        require_segment_trajectory_commitment(binding, segment)


def test_mixed_time_kernel_fails_closed():
    kernel = SubjectiveTimeKernel()
    other = SubjectiveTimeKernel(bias=0.1)
    _, _, segment = candidate_segment(kernel)
    mixed = list(bindings(kernel))
    mixed[1] = time_binding(other, 0.02, 1.25)
    with pytest.raises(
        QHTRIPNLFTrajectoryBindingError,
        match="time binding kernel",
    ):
        build_qhtri_pnlf_trajectory_binding(
            header(kernel),
            segment,
            htri_receipts(),
            mixed,
        )


def test_htri_dt_and_orch_coordinate_dt_mismatch_fails_closed():
    kernel = SubjectiveTimeKernel()
    _, _, segment = candidate_segment(kernel)
    bad = list(bindings(kernel))
    bad[0] = time_binding(kernel, 0.011, 0.8)
    with pytest.raises(
        QHTRIPNLFTrajectoryBindingError,
        match="HTRI dt differs",
    ):
        build_qhtri_pnlf_trajectory_binding(
            header(kernel),
            segment,
            htri_receipts(),
            bad,
        )


def test_proper_time_span_mismatch_fails_closed():
    kernel = SubjectiveTimeKernel()
    _, opened = opened_segment(kernel)
    segment = advance_liminal_segment(
        opened,
        tau_cursor=2.043,
        trajectory_commitment=d("5"),
        t36_trajectory_commitment=d("6"),
    )
    with pytest.raises(
        QHTRIPNLFTrajectoryBindingError,
        match="does not close PNLF segment",
    ):
        build_qhtri_pnlf_trajectory_binding(
            header(kernel),
            segment,
            htri_receipts(),
            bindings(kernel),
        )


def test_step_order_and_t36_basis_enter_commitment_identity():
    kernel = SubjectiveTimeKernel()
    _, _, segment = candidate_segment(kernel)
    receipts = htri_receipts()
    times = bindings(kernel)
    base = build_qhtri_pnlf_trajectory_binding(
        header(kernel),
        segment,
        receipts,
        times,
    )
    reordered = build_qhtri_pnlf_trajectory_binding(
        header(kernel),
        segment,
        tuple(reversed(receipts)),
        tuple(reversed(times)),
    )
    other_basis = build_qhtri_pnlf_trajectory_binding(
        header(kernel, basis="pncs:t36:mummu-test:v2"),
        segment,
        receipts,
        times,
    )
    assert len({base.commitment, reordered.commitment, other_basis.commitment}) == 3


def test_receipt_is_candidate_only_and_cannot_write_state_memory():
    kernel = SubjectiveTimeKernel()
    _, _, segment = candidate_segment(kernel)
    receipt = build_qhtri_pnlf_trajectory_binding(
        header(kernel),
        segment,
        htri_receipts(),
        bindings(kernel),
    ).deterministic_receipt()
    assert receipt["epistemic_state"] == "CHYBA"
    assert receipt["promotion_state"] == "CANDIDATE_ONLY"
    assert receipt["runtime_execution_authority"] is False
    assert receipt["canon_write_authority"] is False
    assert receipt["state_memory_write_authority"] is False


def test_invalid_containers_and_rejected_segment_fail_closed():
    kernel = SubjectiveTimeKernel()
    left, opened, segment = candidate_segment(kernel)
    receipts = htri_receipts()
    times = bindings(kernel)

    with pytest.raises(QHTRIPNLFTrajectoryBindingError):
        build_qhtri_pnlf_trajectory_binding(
            header(kernel),
            segment,
            list(receipts),
            list(times[:2]),
        )

    right = checkpoint(
        2.042,
        kernel,
        predecessor=left.checkpoint_object_id,
        content="8",
    )
    # The ordinary PNLF rejection route closes without a right checkpoint;
    # construct it through the public API rather than mutating segment state.
    from phasenav_natural_code.pnlf_orbital_memory_v01 import reject_liminal_segment

    rejected = reject_liminal_segment(
        segment,
        resolution_witness_sha256=d("9"),
    )
    with pytest.raises(
        QHTRIPNLFTrajectoryBindingError,
        match="rejected PNLF segment",
    ):
        build_qhtri_pnlf_trajectory_binding(
            header(kernel),
            rejected,
            receipts,
            times,
        )
