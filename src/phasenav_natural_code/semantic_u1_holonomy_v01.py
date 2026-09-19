"""Reference harness for PNCS native semantic U(1) holonomy.

Native authority: native/PNCS_NONLOCAL_SEMANTIC_U1_HOLONOMY_V0_1.pnv
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

SEMANTIC_U1_HOLONOMY_CONTRACT = "PNCS_NONLOCAL_SEMANTIC_U1_HOLONOMY_V0_1"
SEMANTIC_U1_HOLONOMY_EPISTEMIC = "CHYBA"


def _finite(values: Iterable[float]) -> tuple[float, ...]:
    out=tuple(float(v) for v in values)
    if not all(math.isfinite(v) for v in out):
        raise ValueError("A_sem edge potentials must be finite")
    return out


def semantic_u1_transport(edge_potentials: Sequence[float]) -> complex:
    """W_sem[gamma] = exp(i sum A_sem,e)."""
    phase=math.fsum(_finite(edge_potentials))
    return complex(math.cos(phase),math.sin(phase))


def semantic_u1_phase(edge_potentials: Sequence[float]) -> float:
    w=semantic_u1_transport(edge_potentials)
    return math.atan2(w.imag,w.real)


def semantic_u1_coupling(overlap: complex, edge_potentials: Sequence[float]) -> complex:
    """C_ij = W_sem z_ij for a scalar projective overlap z_ij."""
    z=complex(overlap)
    if not (math.isfinite(z.real) and math.isfinite(z.imag)):
        raise ValueError("semantic overlap must be finite")
    return semantic_u1_transport(edge_potentials)*z


def open_gauge_shift(edge_potentials: Sequence[float], vertex_gauge: Sequence[float]) -> tuple[float, ...]:
    """A_prime_e = A_e + chi_(k+1) - chi_k for an open path."""
    edges=_finite(edge_potentials)
    chi=_finite(vertex_gauge)
    if len(chi) != len(edges)+1:
        raise ValueError("open path requires one more vertex gauge than edges")
    return tuple(edges[k]+chi[k+1]-chi[k] for k in range(len(edges)))


def closed_gauge_shift(edge_potentials: Sequence[float], vertex_gauge: Sequence[float]) -> tuple[float, ...]:
    """Cyclic discrete gauge shift for a closed loop."""
    edges=_finite(edge_potentials)
    chi=_finite(vertex_gauge)
    if len(chi) != len(edges):
        raise ValueError("closed loop requires one vertex gauge per edge")
    if not edges:
        return ()
    return tuple(edges[k]+chi[(k+1)%len(chi)]-chi[k] for k in range(len(edges)))
