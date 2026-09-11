from __future__ import annotations

import numpy as np
import pytest

from phasenav_natural_code import platonic_ramanujan_masked_runtime_v02 as c
from phasenav_natural_code.platonic_ramanujan_stabilizer_v01 import support_mask
from phasenav_natural_code.semantic_htri_drive_v32 import DriveSnapshot, TAU


def fixture_snapshot() -> DriveSnapshot:
    phi = np.linspace(0.0, 1.2, 36, dtype=np.float64)
    omega = np.linspace(7.0, 8.0, 36, dtype=np.float64)
    g = np.ones((36, 36), dtype=np.float64) * 0.2
    np.fill_diagonal(g, 0.1)
    flavor = np.array([0.7, 0.4, 0.6, 0.3, 0.8], dtype=np.float64)
    tau = np.linspace(0.2, 1.1, 36, dtype=np.float64)
    gravity = np.array([0.2, 1.1, 0.1], dtype=np.float64)
    return DriveSnapshot.build(
        phi=phi,
        omega=omega,
        g=g,
        flavor=flavor,
        tau=tau,
        gravity=gravity,
        source_id="test:pncs:masked-runtime-v02",
    )


def test_candidate_requires_explicit_admission_and_preserves_parent_snapshot():
    snapshot = fixture_snapshot()
    before = snapshot.g.copy()
    target = (snapshot.phi + 0.2) % TAU

    with pytest.raises(c.PlatonicRamanujanMaskedRuntimeV02Error, match="CANDIDATE"):
        c.candidate_masked_controlled_step(
            snapshot,
            target,
            candidate_enabled=False,
        )

    assert np.array_equal(snapshot.g, before)


def test_masked_parent_g_is_sparse_non_mutating_and_seven_regular():
    snapshot = fixture_snapshot()
    before = snapshot.g.copy()
    masked = c.masked_parent_g(snapshot.g, candidate_enabled=True)
    mask = support_mask()

    assert np.array_equal(snapshot.g, before)
    assert masked.shape == (36, 36)
    assert np.all(mask.sum(axis=1) == 7)
    assert np.all(masked[~mask] == 0.0)
    assert np.array_equal(masked[mask], snapshot.g[mask])


def test_candidate_step_keeps_support_invariant_and_exact_target_hit():
    snapshot = fixture_snapshot()
    target = (snapshot.phi + np.linspace(0.01, 0.36, 36)) % TAU
    step = c.candidate_masked_controlled_step(
        snapshot,
        target,
        candidate_enabled=True,
    )
    mask = support_mask()

    assert step.receipt["status"] == "CANDIDATE"
    assert step.receipt["candidate_id"] == "PNCS_SUPPORT_MASK_PARENT_G_V0_2"
    assert step.receipt["support_mask_parent_g_invariant"] is True
    assert step.receipt["outside_mask_nonzeros_g_next"] == 0
    assert step.receipt["additive_C_PR_v0_1"] == "NOT_USED"
    assert np.all(step.g_next[~mask] == 0.0)
    assert float(step.receipt["max_target_residual_rad"]) < 2e-12
    assert np.allclose(step.phi_next, target, rtol=0.0, atol=2e-12)
    assert float(step.receipt["hermiticity_error"]) < 2e-12
    assert np.allclose(step.H, step.H.conj().T, rtol=0.0, atol=2e-12)


def test_candidate_metadata_keeps_rejected_v01_separate():
    meta = c.candidate_metadata()
    assert meta["status"] == "CANDIDATE"
    assert meta["executable"] is True
    assert meta["default_enabled"] is False
    assert meta["gate_target"] == "support_mask_parent_g_activation"
    assert meta["preserves_rejection"] == "additive_C_PR_activation=REJECTED_V0_1"
