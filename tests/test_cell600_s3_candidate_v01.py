import math

import numpy as np
import pytest

from phasenav_natural_code import cell600_s3_candidate_v01 as c


def _all_exponents_of_total(total):
    for a in range(total + 1):
        for b in range(total - a + 1):
            for d in range(total - a - b + 1):
                e = total - a - b - d
                yield (a, b, d, e)


def test_candidate_status_is_working_not_canonical():
    s = c.candidate_status()
    assert s.status == "CANDIDATE"
    assert s.execution_mode == "EXPLICIT_CANDIDATE_API"
    assert not s.runtime_default_enabled
    assert s.supported_l_max == 5
    assert s.supported_dimension == 91
    assert s.physical_binding == "OPEN"


def test_600cell_vertices_live_on_s3_and_are_antipodal():
    v = c.vertices600()
    assert v.shape == (120, 4)
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0, rtol=0.0, atol=4e-14)
    rows = {tuple(row) for row in np.round(v, 12)}
    assert all(tuple(-row) in rows for row in np.round(v, 12))


def test_600cell_graph_degree_edges_and_spectrum():
    a = c.adjacency600()
    assert a.shape == (120, 120)
    assert np.array_equal(a, a.T)
    assert np.all(np.diag(a) == 0.0)
    assert np.all(a.sum(axis=1) == 12.0)
    assert int(a.sum() // 2) == 720

    observed = c.adjacency_spectrum()
    phi = c.PHI
    expected = (
        (-6.0 / phi, 4),
        (-3.0, 16),
        (-4.0 / phi, 9),
        (-2.0, 36),
        (0.0, 25),
        (3.0, 16),
        (4.0 * phi, 9),
        (6.0 * phi, 4),
        (12.0, 1),
    )
    assert len(observed) == len(expected)
    for (got_v, got_m), (want_v, want_m) in zip(observed, expected):
        assert got_m == want_m
        assert math.isclose(got_v, want_v, rel_tol=0.0, abs_tol=3e-12)


def test_l0_l5_projectors_are_orthogonal_and_have_s3_multiplicities():
    ps = [c.projector_l(ell) for ell in range(6)]
    for ell, p in enumerate(ps):
        assert np.allclose(p, p.T, rtol=0.0, atol=3e-13)
        assert np.allclose(p @ p, p, rtol=0.0, atol=2e-12)
        assert math.isclose(float(np.trace(p)), float((ell + 1) ** 2), abs_tol=2e-11)
        for j, q in enumerate(ps):
            if ell != j:
                assert np.linalg.norm(p @ q) < 3e-12

    p_supported = c.supported_projector()
    assert math.isclose(float(np.trace(p_supported)), 91.0, abs_tol=5e-11)


def test_candidate_angular_operator_matches_s3_eigenvalues_on_l0_l5():
    op = c.angular_laplacian_candidate()
    for ell in range(6):
        p = c.projector_l(ell)
        assert np.linalg.norm(op @ p - ell * (ell + 2) * p) < 2e-10


def test_candidate_operator_executes_on_supported_state():
    rng = np.random.default_rng(20260911)
    x = rng.normal(size=120) + 1j * rng.normal(size=120)
    x = c.supported_projector() @ x
    out = c.apply_angular_laplacian_candidate(x)
    assert out.shape == (120,)
    assert np.isfinite(out).all()
    assert c.unsupported_residual_norm(out) < 1e-9


def test_candidate_operator_fails_closed_on_unsupported_sector():
    a = c.adjacency600()
    values, vectors = np.linalg.eigh(a)
    idx = int(np.argmin(np.abs(values + 3.0)))
    x = vectors[:, idx]
    assert c.unsupported_residual_norm(x) > 0.99
    with pytest.raises(c.Candidate600CellError, match="fails closed"):
        c.apply_angular_laplacian_candidate(x)


def test_600cell_is_exact_spherical_11_design_to_numerical_precision():
    v = c.vertices600()
    max_error = 0.0
    checked = 0
    for total in range(12):
        for exp in _all_exponents_of_total(total):
            sampled = float(np.mean(np.prod(v ** np.asarray(exp), axis=1)))
            exact = c.sphere_s3_monomial_moment(exp)
            max_error = max(max_error, abs(sampled - exact))
            checked += 1
    assert checked == 1365
    assert max_error < 3e-14


def test_degree_12_is_first_explicit_nonexact_witness():
    v = c.vertices600()
    sampled = float(np.mean(v[:, 0] ** 12))
    exact = c.sphere_s3_monomial_moment((12, 0, 0, 0))
    assert math.isclose(sampled - exact, 1.0 / 4096.0, rel_tol=0.0, abs_tol=2e-15)
