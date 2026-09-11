from __future__ import annotations

import math
import numpy as np
import pytest

from phasenav_natural_code import candidate_600cell_s3_v01 as c


def exponent_tuples(max_degree: int):
    for total in range(max_degree + 1):
        for a in range(total + 1):
            for b in range(total - a + 1):
                for d in range(total - a - b + 1):
                    e = total - a - b - d
                    yield (a, b, d, e)


def test_candidate_is_executable_but_not_default():
    meta = c.candidate_metadata()
    assert meta["status"] == "CANDIDATE"
    assert meta["executable"] is True
    assert meta["default_enabled"] is False

    with pytest.raises(c.Candidate600CellError):
        c.apply_s3_laplacian_candidate(np.ones(120), candidate_enabled=False)


def test_600cell_vertices_and_graph():
    v = c.vertices600()
    a = c.adjacency600()
    assert v.shape == (120, 4)
    assert np.allclose(np.sum(v * v, axis=1), 1.0, rtol=0.0, atol=2e-15)
    assert a.shape == (120, 120)
    assert np.array_equal(a, a.T)
    assert np.all(a.sum(axis=1) == 12.0)
    assert int(a.sum() // 2) == 720


def test_spectrum_contains_exact_s3_low_sector_degeneracies():
    eig = np.linalg.eigvalsh(c.adjacency600())
    for ell in range(6):
        target = c.ELL_TO_ADJACENCY_EIGENVALUE[ell]
        multiplicity = int(np.count_nonzero(np.isclose(eig, target, rtol=0.0, atol=2e-10)))
        assert multiplicity == (ell + 1) ** 2


def test_spherical_11_design_and_degree12_break():
    v = c.vertices600()
    max_error = 0.0
    for exponents in exponent_tuples(11):
        sampled = float(np.mean(np.prod(v ** np.asarray(exponents), axis=1)))
        expected = c.normalized_s3_monomial_moment(exponents)
        max_error = max(max_error, abs(sampled - expected))
    assert max_error < 1e-14

    sampled12 = float(np.mean(v[:, 0] ** 12))
    expected12 = c.normalized_s3_monomial_moment((12, 0, 0, 0))
    assert math.isclose(sampled12 - expected12, 1.0 / 4096.0, rel_tol=0.0, abs_tol=1e-15)


def test_candidate_laplacian_maps_low_sectors_to_ell_ellplus2():
    eig, vec = c.spectral_decomposition()
    for ell in range(6):
        target = c.ELL_TO_ADJACENCY_EIGENVALUE[ell]
        i = int(np.flatnonzero(np.isclose(eig, target, rtol=0.0, atol=2e-10))[0])
        x = vec[:, i]
        out, receipt = c.apply_s3_laplacian_candidate(
            x, candidate_enabled=True, complement_tolerance=1e-8
        )
        assert receipt.status == "CANDIDATE"
        assert receipt.validated_ell_max == 5
        assert np.allclose(
            out,
            c.ELL_TO_LAPLACIAN_EIGENVALUE[ell] * x,
            rtol=0.0,
            atol=2e-9,
        )


def test_unvalidated_mirror_sector_fails_closed():
    eig, vec = c.spectral_decomposition()
    i = int(np.flatnonzero(np.isclose(eig, -3.0, rtol=0.0, atol=2e-10))[0])
    with pytest.raises(c.Candidate600CellError, match="leaves validated"):
        c.apply_s3_laplacian_candidate(vec[:, i], candidate_enabled=True)
