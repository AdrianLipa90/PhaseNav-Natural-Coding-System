from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import itertools
import math
from typing import Sequence

import numpy as np

SCHEMA = "PNCS_600CELL_S3_ANGULAR_CANDIDATE_V0_1"
STATUS = "CANDIDATE"
EXECUTION_MODE = "EXPLICIT_CANDIDATE_API"
RUNTIME_DEFAULT_ENABLED = False
SUPPORTED_L_MAX = 5
N_VERTICES = 120
DIMENSION = 4
DEGREE = 12
N_EDGES = 720
PHI = (1.0 + math.sqrt(5.0)) / 2.0

_L_TO_ADJ_EIGENVALUE = {
    0: 12.0,
    1: 6.0 * PHI,
    2: 4.0 * PHI,
    3: 3.0,
    4: 0.0,
    5: -2.0,
}
_L_TO_MULTIPLICITY = {ell: (ell + 1) ** 2 for ell in range(SUPPORTED_L_MAX + 1)}


class Candidate600CellError(ValueError):
    pass


@dataclass(frozen=True)
class Candidate600CellStatus:
    schema: str
    status: str
    execution_mode: str
    runtime_default_enabled: bool
    supported_l_max: int
    supported_dimension: int
    physical_binding: str


def candidate_status() -> Candidate600CellStatus:
    return Candidate600CellStatus(
        schema=SCHEMA,
        status=STATUS,
        execution_mode=EXECUTION_MODE,
        runtime_default_enabled=RUNTIME_DEFAULT_ENABLED,
        supported_l_max=SUPPORTED_L_MAX,
        supported_dimension=sum(_L_TO_MULTIPLICITY.values()),
        physical_binding="OPEN",
    )


def _permutation_parity(p: tuple[int, ...]) -> int:
    inversions = sum(
        p[i] > p[j]
        for i in range(len(p))
        for j in range(i + 1, len(p))
    )
    return inversions % 2


@lru_cache(maxsize=1)
def _vertices_cached() -> np.ndarray:
    vertices: list[tuple[float, float, float, float]] = []

    for axis in range(4):
        for sign in (-1.0, 1.0):
            v = [0.0, 0.0, 0.0, 0.0]
            v[axis] = sign
            vertices.append(tuple(v))

    vertices.extend(itertools.product((-0.5, 0.5), repeat=4))

    base = (0.0, 0.5, PHI / 2.0, 1.0 / (2.0 * PHI))
    even_permutations = [
        p for p in itertools.permutations(range(4)) if _permutation_parity(p) == 0
    ]
    for p in even_permutations:
        permuted = [base[p[i]] for i in range(4)]
        nonzero = [i for i, value in enumerate(permuted) if value != 0.0]
        for signs in itertools.product((-1.0, 1.0), repeat=3):
            v = permuted.copy()
            for i, sign in zip(nonzero, signs):
                v[i] *= sign
            vertices.append(tuple(v))

    out = np.unique(np.round(np.asarray(vertices, dtype=np.float64), 14), axis=0)
    if out.shape != (N_VERTICES, DIMENSION):
        raise AssertionError(f"600-cell vertex construction produced shape {out.shape}")
    norms = np.linalg.norm(out, axis=1)
    if not np.allclose(norms, 1.0, rtol=0.0, atol=4e-14):
        raise AssertionError("600-cell vertices left S^3")
    out.setflags(write=False)
    return out


def vertices600() -> np.ndarray:
    return _vertices_cached().copy()


@lru_cache(maxsize=1)
def _adjacency_cached() -> np.ndarray:
    v = _vertices_cached()
    dots = v @ v.T
    adjacency = np.isclose(dots, PHI / 2.0, rtol=0.0, atol=2e-13).astype(np.float64)
    np.fill_diagonal(adjacency, 0.0)
    if not np.array_equal(adjacency, adjacency.T):
        raise AssertionError("600-cell adjacency lost symmetry")
    if not np.all(adjacency.sum(axis=1) == DEGREE):
        raise AssertionError("600-cell graph is not 12-regular")
    if int(adjacency.sum() // 2) != N_EDGES:
        raise AssertionError("600-cell edge count mismatch")
    adjacency.setflags(write=False)
    return adjacency


def adjacency600() -> np.ndarray:
    return _adjacency_cached().copy()


def graph_laplacian600() -> np.ndarray:
    return DEGREE * np.eye(N_VERTICES, dtype=np.float64) - _adjacency_cached()


def _clustered_spectrum(tol: float = 1e-9) -> tuple[tuple[float, int], ...]:
    eigenvalues = np.linalg.eigvalsh(_adjacency_cached())
    clusters: list[list[float | int]] = []
    for value in eigenvalues:
        x = float(value)
        if not clusters or abs(x - float(clusters[-1][0])) > tol:
            clusters.append([x, 1])
        else:
            clusters[-1][1] = int(clusters[-1][1]) + 1
    return tuple((float(v), int(m)) for v, m in clusters)


def adjacency_spectrum() -> tuple[tuple[float, int], ...]:
    return _clustered_spectrum()


@lru_cache(maxsize=1)
def _spectral_decomposition() -> tuple[np.ndarray, np.ndarray]:
    values, vectors = np.linalg.eigh(_adjacency_cached())
    values.setflags(write=False)
    vectors.setflags(write=False)
    return values, vectors


def projector_l(ell: int, *, eigenvalue_tolerance: float = 2e-9) -> np.ndarray:
    if isinstance(ell, bool) or not isinstance(ell, int) or ell not in _L_TO_ADJ_EIGENVALUE:
        raise Candidate600CellError(f"ell must be an integer in [0,{SUPPORTED_L_MAX}]")
    values, vectors = _spectral_decomposition()
    target = _L_TO_ADJ_EIGENVALUE[ell]
    mask = np.abs(values - target) <= eigenvalue_tolerance
    expected = _L_TO_MULTIPLICITY[ell]
    if int(mask.sum()) != expected:
        raise AssertionError(
            f"ell={ell} eigenspace multiplicity {int(mask.sum())} != {expected}"
        )
    q = vectors[:, mask]
    return q @ q.T


def supported_projector() -> np.ndarray:
    out = np.zeros((N_VERTICES, N_VERTICES), dtype=np.float64)
    for ell in range(SUPPORTED_L_MAX + 1):
        out += projector_l(ell)
    return out


def angular_laplacian_candidate() -> np.ndarray:
    """Finite S^3 angular operator on the verified ell=0..5 carrier sectors.

    On projector_l(ell), this operator has eigenvalue ell*(ell+2), matching
    -Delta_{S^3}. Unsupported graph sectors are assigned zero here and MUST
    be rejected by apply_angular_laplacian_candidate unless explicitly
    projected into the supported carrier first.
    """
    out = np.zeros((N_VERTICES, N_VERTICES), dtype=np.float64)
    for ell in range(SUPPORTED_L_MAX + 1):
        out += float(ell * (ell + 2)) * projector_l(ell)
    return out


def _vector120(vector: Sequence[complex]) -> np.ndarray:
    try:
        out = np.asarray(vector, dtype=np.complex128)
    except (TypeError, ValueError, OverflowError) as exc:
        raise Candidate600CellError("vector must be a finite complex 120-vector") from exc
    if out.shape != (N_VERTICES,) or not np.isfinite(out).all():
        raise Candidate600CellError("vector must be a finite complex 120-vector")
    return out.copy()


def decompose_l0_l5(vector: Sequence[complex]) -> dict[int, np.ndarray]:
    x = _vector120(vector)
    return {ell: projector_l(ell) @ x for ell in range(SUPPORTED_L_MAX + 1)}


def unsupported_residual_norm(vector: Sequence[complex]) -> float:
    x = _vector120(vector)
    supported = supported_projector() @ x
    return float(np.linalg.norm(x - supported))


def apply_angular_laplacian_candidate(
    vector: Sequence[complex],
    *,
    support_tolerance: float = 1e-10,
) -> np.ndarray:
    x = _vector120(vector)
    residual = unsupported_residual_norm(x)
    scale = max(1.0, float(np.linalg.norm(x)))
    if residual > support_tolerance * scale:
        raise Candidate600CellError(
            "input contains unsupported ell>5 / folded 600-cell sectors; "
            "candidate operator fails closed"
        )
    return angular_laplacian_candidate().astype(np.complex128) @ x


def sphere_s3_monomial_moment(exponents: Sequence[int]) -> float:
    exp = tuple(exponents)
    if len(exp) != 4 or any(
        isinstance(e, bool) or not isinstance(e, int) or e < 0 for e in exp
    ):
        raise Candidate600CellError("exponents must be four non-negative integers")
    if any(e % 2 for e in exp):
        return 0.0
    half = [e // 2 for e in exp]
    total = sum(half)
    value = math.gamma(2.0) / math.gamma(2.0 + total)
    for b in half:
        value *= math.gamma(b + 0.5) / math.gamma(0.5)
    return float(value)
