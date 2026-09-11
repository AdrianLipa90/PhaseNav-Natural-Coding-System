from __future__ import annotations

import math
import numpy as np

from phasenav_natural_code import platonic_ramanujan_stabilizer_v01 as pr


def test_carrier_shape_degree_edges_and_connectivity():
    a = pr.adjacency36()
    assert a.shape == (36, 36)
    assert np.array_equal(a, a.T)
    assert np.all(np.diag(a) == 0.0)
    assert np.all(a.sum(axis=1) == 7.0)
    assert int(a.sum() // 2) == 126

    seen = {0}
    frontier = [0]
    while frontier:
        i = frontier.pop()
        for j in np.flatnonzero(a[i]):
            jj = int(j)
            if jj not in seen:
                seen.add(jj)
                frontier.append(jj)
    assert len(seen) == 36


def test_exact_cartesian_product_spectrum_and_ramanujan_bound():
    eig = np.linalg.eigvalsh(pr.adjacency36())
    expected = (
        [7.0] * 1
        + [2.0 + math.sqrt(5.0)] * 3
        + [4.0] * 2
        + [math.sqrt(5.0) - 1.0] * 6
        + [1.0] * 5
        + [2.0 - math.sqrt(5.0)] * 3
        + [-2.0] * 10
        + [-1.0 - math.sqrt(5.0)] * 6
    )
    assert np.allclose(np.sort(eig), np.sort(expected), rtol=0.0, atol=2e-12)

    metrics = pr.spectral_metrics()
    assert metrics.degree == 7
    assert metrics.is_ramanujan
    assert math.isclose(
        metrics.nontrivial_radius, 2.0 + math.sqrt(5.0), rel_tol=0.0, abs_tol=2e-12
    )
    assert metrics.nontrivial_radius < 2.0 * math.sqrt(6.0)
    assert math.isclose(
        metrics.normalized_laplacian_gap,
        (5.0 - math.sqrt(5.0)) / 7.0,
        rel_tol=0.0,
        abs_tol=2e-12,
    )


def test_existing_12x3_lane_order_is_preserved():
    for i in range(36):
        assert pr.channel_local_lane(i) == (i // 3, i % 3)


def test_support_mask_has_seven_neighbors_per_lane():
    mask = pr.support_mask()
    assert mask.dtype == np.bool_
    assert np.all(mask.sum(axis=1) == 7)
    assert not np.any(np.diag(mask))


def test_mask_is_non_mutating_and_sparse():
    g = np.arange(36 * 36, dtype=np.float64).reshape(36, 36)
    before = g.copy()
    out = pr.apply_support_mask(g)
    assert np.array_equal(g, before)
    assert np.count_nonzero(pr.support_mask(), axis=1).tolist() == [7] * 36
    assert np.all(out[~pr.support_mask()] == 0.0)


def test_stabilizer_uniform_phase_zero_and_global_phase_covariant():
    phi = np.full(36, 1.234, dtype=np.float64)
    assert np.allclose(pr.stabilizing_coupling(phi, 0.7), 0.0, atol=1e-15)

    rng = np.random.default_rng(20260911)
    phi = rng.uniform(-math.pi, math.pi, size=36)
    c0 = pr.stabilizing_coupling(phi, 0.25)
    c1 = pr.stabilizing_coupling(phi + 0.918273, 0.25)
    assert np.allclose(c0, c1, rtol=0.0, atol=2e-15)
    assert abs(float(c0.sum())) < 5e-15


def test_small_perturbations_contract_under_candidate_term():
    rng = np.random.default_rng(7)
    delta = rng.normal(size=36)
    delta -= delta.mean()
    delta *= 1e-4 / np.linalg.norm(delta)
    beta = 0.5
    dt = 0.1
    c = pr.stabilizing_coupling(delta, beta)
    nxt = delta + dt * c
    nxt -= nxt.mean()
    assert np.linalg.norm(nxt) < np.linalg.norm(delta)


def test_linearized_gap_bound_is_positive_and_exact():
    beta = 0.75
    expected = beta * (5.0 - math.sqrt(5.0)) / 7.0
    assert math.isclose(pr.linearized_decay_bound(beta), expected, rel_tol=0.0, abs_tol=1e-15)
