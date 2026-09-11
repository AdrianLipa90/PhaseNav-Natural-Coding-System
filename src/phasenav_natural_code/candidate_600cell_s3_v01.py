from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from typing import Iterable, Sequence

import numpy as np

SCHEMA = "PNCS_600CELL_S3_CANDIDATE_V0_1"
STATUS = "CANDIDATE"
N = 120
DIM = 4
DEGREE = 12
PHI = (1.0 + math.sqrt(5.0)) / 2.0

# Verified low angular sectors on S^3.
ELL_TO_ADJACENCY_EIGENVALUE = {
    0: 12.0,
    1: 6.0 * PHI,
    2: 4.0 * PHI,
    3: 3.0,
    4: 0.0,
    5: -2.0,
}
ELL_TO_MULTIPLICITY = {ell: (ell + 1) ** 2 for ell in range(6)}
ELL_TO_LAPLACIAN_EIGENVALUE = {ell: ell * (ell + 2) for ell in range(6)}


class Candidate600CellError(ValueError):
    pass


@dataclass(frozen=True)
class CandidateExecutionReceipt:
    schema: str
    status: str
    candidate_id: str
    validated_ell_max: int
    complement_norm: float
    input_norm: float
    output_norm: float


def _even_permutations4() -> tuple[tuple[int, int, int, int], ...]:
    out = []
    for p in itertools.permutations(range(4)):
        inv = sum(p[i] > p[j] for i in range(4) for j in range(i + 1, 4))
        if inv % 2 == 0:
            out.append(p)
    return tuple(out)


def vertices600() -> np.ndarray:
    """Return the canonical 120 unit vertices of the 600-cell on S^3."""
    out: list[list[float]] = []

    # 8 axial vertices.
    for i in range(4):
        for sign in (-1.0, 1.0):
            v = [0.0] * 4
            v[i] = sign
            out.append(v)

    # 16 vertices (±1/2, ±1/2, ±1/2, ±1/2).
    for signs in itertools.product((-0.5, 0.5), repeat=4):
        out.append(list(signs))

    # 96 vertices: even permutations of
    # (0, ±1/2, ±phi/2, ±1/(2phi)).
    base = (0.0, 0.5, PHI / 2.0, 1.0 / (2.0 * PHI))
    for p in _even_permutations4():
        perm = [base[p[i]] for i in range(4)]
        nonzero = [i for i, value in enumerate(perm) if value != 0.0]
        for signs in itertools.product((-1.0, 1.0), repeat=3):
            v = perm.copy()
            for idx, sign in zip(nonzero, signs):
                v[idx] *= sign
            out.append(v)

    vertices = np.asarray(out, dtype=np.float64)
    if vertices.shape != (N, DIM):
        raise AssertionError("600-cell vertex count mismatch")
    if len(np.unique(np.round(vertices, 14), axis=0)) != N:
        raise AssertionError("600-cell vertices are not unique")
    if not np.allclose(np.sum(vertices * vertices, axis=1), 1.0, rtol=0.0, atol=2e-15):
        raise AssertionError("600-cell vertices left S^3")
    return vertices


def adjacency600() -> np.ndarray:
    """Return the 12-regular vertex graph adjacency matrix of the 600-cell."""
    vertices = vertices600()
    dots = vertices @ vertices.T
    adjacency = np.isclose(dots, PHI / 2.0, rtol=0.0, atol=2e-12).astype(np.float64)
    np.fill_diagonal(adjacency, 0.0)
    if not np.array_equal(adjacency, adjacency.T):
        raise AssertionError("600-cell adjacency lost symmetry")
    if not np.all(adjacency.sum(axis=1) == DEGREE):
        raise AssertionError("600-cell graph is not 12-regular")
    return adjacency


def spectral_decomposition() -> tuple[np.ndarray, np.ndarray]:
    """Return ascending eigenvalues and orthonormal eigenvectors of A_600."""
    return np.linalg.eigh(adjacency600())


def _validated_sector_mask(eigenvalues: np.ndarray, atol: float = 2e-10) -> np.ndarray:
    targets = np.asarray(tuple(ELL_TO_ADJACENCY_EIGENVALUE.values()), dtype=np.float64)
    return np.min(np.abs(eigenvalues[:, None] - targets[None, :]), axis=1) <= atol


def project_validated_l0_l5(state: Sequence[complex]) -> tuple[np.ndarray, float]:
    """Project a 120-vector to the validated ell=0..5 S^3 sector.

    Returns (projected_state, complement_norm). This is a candidate research
    operator, not a canonical physical binding.
    """
    x = np.asarray(state, dtype=np.complex128)
    if x.shape != (N,) or not np.isfinite(x.real).all() or not np.isfinite(x.imag).all():
        raise Candidate600CellError("state must be a finite complex 120-vector")

    eigenvalues, eigenvectors = spectral_decomposition()
    mask = _validated_sector_mask(eigenvalues)
    coeff = eigenvectors.T.conj() @ x
    projected_coeff = np.where(mask, coeff, 0.0)
    complement_coeff = np.where(mask, 0.0, coeff)
    projected = eigenvectors @ projected_coeff
    return projected, float(np.linalg.norm(complement_coeff))


def apply_s3_laplacian_candidate(
    state: Sequence[complex],
    *,
    candidate_enabled: bool,
    complement_tolerance: float = 1e-9,
) -> tuple[np.ndarray, CandidateExecutionReceipt]:
    """Apply -Delta_{S^3} = ell(ell+2) on validated ell=0..5 sectors.

    Candidate execution is explicit. The function fails closed when the input
    contains unresolved 600-cell mirror-sector support above tolerance.
    """
    if candidate_enabled is not True:
        raise Candidate600CellError(
            "600-cell working implementation is CANDIDATE; pass candidate_enabled=True explicitly"
        )
    if not math.isfinite(complement_tolerance) or complement_tolerance < 0.0:
        raise Candidate600CellError("complement_tolerance must be finite and non-negative")

    x = np.asarray(state, dtype=np.complex128)
    if x.shape != (N,) or not np.isfinite(x.real).all() or not np.isfinite(x.imag).all():
        raise Candidate600CellError("state must be a finite complex 120-vector")

    eigenvalues, eigenvectors = spectral_decomposition()
    coeff = eigenvectors.T.conj() @ x

    weights = np.full(N, np.nan, dtype=np.float64)
    validated = np.zeros(N, dtype=bool)
    for ell, target in ELL_TO_ADJACENCY_EIGENVALUE.items():
        hit = np.isclose(eigenvalues, target, rtol=0.0, atol=2e-10)
        weights[hit] = float(ELL_TO_LAPLACIAN_EIGENVALUE[ell])
        validated |= hit

    complement_norm = float(np.linalg.norm(coeff[~validated]))
    if complement_norm > complement_tolerance:
        raise Candidate600CellError(
            f"state leaves validated ell<=5 sector: complement_norm={complement_norm:.6e}"
        )

    out_coeff = np.zeros_like(coeff)
    out_coeff[validated] = weights[validated] * coeff[validated]
    out = eigenvectors @ out_coeff

    receipt = CandidateExecutionReceipt(
        schema=SCHEMA,
        status=STATUS,
        candidate_id="600CELL_S3_ANGULAR_L0_L5_V0_1",
        validated_ell_max=5,
        complement_norm=complement_norm,
        input_norm=float(np.linalg.norm(x)),
        output_norm=float(np.linalg.norm(out)),
    )
    return out, receipt


def normalized_s3_monomial_moment(exponents: Sequence[int]) -> float:
    """Exact normalized S^3 monomial moment evaluated as a float."""
    exponents = tuple(exponents)
    if len(exponents) != 4 or any(
        isinstance(e, bool) or not isinstance(e, int) or e < 0 for e in exponents
    ):
        raise Candidate600CellError("exponents must be four non-negative integers")
    if any(e % 2 for e in exponents):
        return 0.0

    half = [e // 2 for e in exponents]
    total = sum(half)
    if total == 0:
        return 1.0

    numerator = 1
    for a in half:
        for k in range(1, a + 1):
            numerator *= 2 * k - 1

    denominator = 1
    for j in range(total):
        denominator *= 4 + 2 * j
    return float(numerator / denominator)


def candidate_metadata() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "candidate_id": "600CELL_S3_ANGULAR_L0_L5_V0_1",
        "executable": True,
        "default_enabled": False,
        "validated_ell": list(range(6)),
        "validated_design_degree": 11,
        "first_known_quadrature_break_degree": 12,
        "physical_binding": False,
        "promotion_requires": [
            "full repository regression PASS",
            "parent PhaseNav benchmark non-regression",
            "explicit physical binding evidence",
        ],
    }
