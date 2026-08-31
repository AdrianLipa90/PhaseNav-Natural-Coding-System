import numpy as np
import pytest

from phasenav_natural_code.semantic_htri_drive_v32 import (
    DriveSnapshot,
    controlled_step,
)


def _inputs():
    phi = np.linspace(0.05, 5.95, 36, dtype=np.float64)
    omega = 39.4 + np.linspace(-0.1, 0.1, 36, dtype=np.float64)
    i = np.arange(36, dtype=np.float64)
    g = 0.2 * np.cos((i[:, None] - i[None, :]) * np.pi / 18.0)
    np.fill_diagonal(g, 0.0)
    flavor = np.array([0.31, 0.72, 0.23, 0.56, 0.48, 0.5], dtype=np.float64)
    tau = np.linspace(0.2, 0.5, 36, dtype=np.float64)
    gravity = np.array([0.0, 1.1, 0.3, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float64)
    return phi, omega, g, flavor, tau, gravity


def _snapshot():
    phi, omega, g, flavor, tau, gravity = _inputs()
    return DriveSnapshot.build(
        phi=phi,
        omega=omega,
        g=g,
        flavor=flavor,
        tau=tau,
        gravity=gravity,
        source_id="SNAPSHOT.IMMUTABLE.TEST",
    )


def test_snapshot_freezes_all_admitted_arrays_and_snapshot_identity():
    snapshot = _snapshot()
    before = snapshot.snapshot_id

    for array in (
        snapshot.phi,
        snapshot.omega,
        snapshot.g,
        snapshot.flavor,
        snapshot.tau,
        snapshot.gravity,
    ):
        assert array.flags.writeable is False
        with pytest.raises(ValueError):
            array.flat[0] = array.flat[0] + 1.0
        with pytest.raises(ValueError):
            array.setflags(write=True)

    assert snapshot.snapshot_id == before


def test_source_array_mutation_after_build_does_not_change_snapshot():
    phi, omega, g, flavor, tau, gravity = _inputs()
    snapshot = DriveSnapshot.build(
        phi=phi,
        omega=omega,
        g=g,
        flavor=flavor,
        tau=tau,
        gravity=gravity,
        source_id="SNAPSHOT.SOURCE.COPY.TEST",
    )
    before = snapshot.snapshot_id

    phi[:] = 0.0
    omega[:] = 0.0
    g[:] = 0.0
    flavor[:] = 0.0
    tau[:] = 0.0
    gravity[:] = 0.0

    assert snapshot.snapshot_id == before
    assert np.any(snapshot.phi != 0.0)
    assert np.any(snapshot.omega != 0.0)
    assert np.any(snapshot.g != 0.0)


def test_controlled_step_operates_on_writable_copies_of_immutable_snapshot():
    snapshot = _snapshot()
    before = snapshot.snapshot_id
    target = (snapshot.phi + 0.17) % (2.0 * np.pi)

    step = controlled_step(snapshot, target, dt=0.01)

    assert step.phi_next.shape == (36,)
    assert step.g_next.shape == (36, 36)
    assert step.receipt["source_snapshot_id"] == before
    assert snapshot.snapshot_id == before
