from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Sequence

import numpy as np


SCHEMA = "PNCS_PLATONIC_RAMANUJAN_STABILIZER_V0_1"
N_CHANNELS = 12
LANES_PER_CHANNEL = 3
N = N_CHANNELS * LANES_PER_CHANNEL
CHANNEL_DEGREE = 5
LOCAL_DEGREE = 2
DEGREE = CHANNEL_DEGREE + LOCAL_DEGREE

# Deterministic icosahedral graph labelling. Channel i maps to vertex i;
# existing PNCS lane order is preserved as lane = 3*i + local_lane.
ICOSAHEDRAL_EDGES: tuple[tuple[int, int], ...] = (
    (0, 1), (0, 5), (0, 7), (0, 8), (0, 11),
    (1, 2), (1, 5), (1, 6), (1, 8),
    (2, 3), (2, 6), (2, 8), (2, 9),
    (3, 4), (3, 6), (3, 9), (3, 10),
    (4, 5), (4, 6), (4, 10), (4, 11),
    (5, 6), (5, 11),
    (7, 8), (7, 9), (7, 10), (7, 11),
    (8, 9),
    (9, 10),
    (10, 11),
)


class PlatonicRamanujanStabilizerV01Error(ValueError):
    pass


def _finite_real(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise PlatonicRamanujanStabilizerV01Error(f"{name} must be a finite real")
    out = float(value)
    if not math.isfinite(out):
        raise PlatonicRamanujanStabilizerV01Error(f"{name} must be a finite real")
    return out


def _phase_vector(phi: Sequence[float]) -> np.ndarray:
    try:
        out = np.asarray(phi, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise PlatonicRamanujanStabilizerV01Error("phi must be a finite real 36-vector") from exc
    if out.shape != (N,) or not np.isfinite(out).all():
        raise PlatonicRamanujanStabilizerV01Error("phi must be a finite real 36-vector")
    return out.copy()


def icosahedral_adjacency() -> np.ndarray:
    a = np.zeros((N_CHANNELS, N_CHANNELS), dtype=np.float64)
    for i, j in ICOSAHEDRAL_EDGES:
        a[i, j] = 1.0
        a[j, i] = 1.0
    if not np.array_equal(a, a.T):
        raise AssertionError("icosahedral adjacency lost symmetry")
    if not np.all(a.sum(axis=1) == CHANNEL_DEGREE):
        raise AssertionError("icosahedral adjacency is not 5-regular")
    return a


def local_k3_adjacency() -> np.ndarray:
    return np.ones((LANES_PER_CHANNEL, LANES_PER_CHANNEL), dtype=np.float64) - np.eye(
        LANES_PER_CHANNEL, dtype=np.float64
    )


def adjacency36() -> np.ndarray:
    """Cartesian product I_12 square K_3 in the existing 12x3 PNCS lane order."""
    a_i = icosahedral_adjacency()
    a_k3 = local_k3_adjacency()
    a = np.kron(a_i, np.eye(LANES_PER_CHANNEL)) + np.kron(
        np.eye(N_CHANNELS), a_k3
    )
    if a.shape != (N, N):
        raise AssertionError("unexpected carrier shape")
    if not np.array_equal(a, a.T):
        raise AssertionError("carrier adjacency lost symmetry")
    if not np.all(a.sum(axis=1) == DEGREE):
        raise AssertionError("carrier is not 7-regular")
    if np.any(np.diag(a) != 0.0):
        raise AssertionError("carrier has self-loops")
    return a


def support_mask() -> np.ndarray:
    return adjacency36().astype(bool)


def apply_support_mask(g: Sequence[Sequence[float]]) -> np.ndarray:
    try:
        x = np.asarray(g, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise PlatonicRamanujanStabilizerV01Error("g must be a finite 36x36 real matrix") from exc
    if x.shape != (N, N) or not np.isfinite(x).all():
        raise PlatonicRamanujanStabilizerV01Error("g must be a finite 36x36 real matrix")
    return np.where(support_mask(), x, 0.0)


@dataclass(frozen=True)
class SpectralMetrics:
    degree: int
    nontrivial_radius: float
    ramanujan_bound: float
    normalized_laplacian_gap: float
    is_ramanujan: bool


def spectral_metrics() -> SpectralMetrics:
    eig = np.linalg.eigvalsh(adjacency36())
    eig = np.sort(eig)[::-1]
    if not math.isclose(float(eig[0]), float(DEGREE), rel_tol=0.0, abs_tol=1e-12):
        raise AssertionError("principal eigenvalue mismatch")
    rho = float(np.max(np.abs(eig[1:])))
    bound = 2.0 * math.sqrt(DEGREE - 1.0)
    gap = 1.0 - float(eig[1]) / float(DEGREE)
    return SpectralMetrics(
        degree=DEGREE,
        nontrivial_radius=rho,
        ramanujan_bound=bound,
        normalized_laplacian_gap=gap,
        is_ramanujan=bool(rho <= bound + 1e-12),
    )


def exact_normalized_gap() -> float:
    """Expected gap 1 - (2+sqrt(5))/7 for I_12 square K_3."""
    return (5.0 - math.sqrt(5.0)) / 7.0


def linearized_decay_bound(beta: float) -> float:
    """Local mean-zero contraction-rate lower bound for beta >= 0."""
    b = _finite_real("beta", beta)
    if b < 0.0:
        raise PlatonicRamanujanStabilizerV01Error("beta must be non-negative")
    return b * exact_normalized_gap()


def phase_disagreement_energy(phi: Sequence[float]) -> float:
    r"""Graph phase-disagreement Lyapunov potential.

    V(phi) = sum_{(i,j) in E} [1 - cos(phi_i - phi_j)].
    """
    p = _phase_vector(phi)
    a = adjacency36()
    diff = p[:, None] - p[None, :]
    return float(0.5 * np.sum(a * (1.0 - np.cos(diff))))


def stabilizing_coupling(phi: Sequence[float], beta: float) -> np.ndarray:
    r"""Candidate sparse phase regularizer.

    C_i^PR = -(beta/7) sum_j A_ij sin(phi_i - phi_j)

    This is an additive candidate term only. It does not mutate or replace
    the parent v0.32 coupling law.
    """
    p = _phase_vector(phi)
    b = _finite_real("beta", beta)
    if b < 0.0:
        raise PlatonicRamanujanStabilizerV01Error("beta must be non-negative")
    if b == 0.0:
        return np.zeros(N, dtype=np.float64)
    a = adjacency36()
    diff = p[:, None] - p[None, :]
    return -(b / float(DEGREE)) * np.sum(a * np.sin(diff), axis=1)


def channel_local_lane(index: int) -> tuple[int, int]:
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < N:
        raise PlatonicRamanujanStabilizerV01Error("index must be an integer in [0,35]")
    return divmod(index, LANES_PER_CHANNEL)
