from __future__ import annotations

import numpy as np


CANDIDATE_STATUS = {
    "promotion_state": "CANDIDATE_ONLY",
    "runtime_execution_authority": False,
    "canon_write_authority": False,
    "epistemic": "CHYBA",
    "carrier_contract": "PHASENAV_PROMOTION_GEOMETRY_V0_1",
}


def complex_structure(dim_complex: int) -> np.ndarray:
    if dim_complex <= 0:
        raise ValueError("dim_complex must be positive")
    eye = np.eye(dim_complex, dtype=float)
    zero = np.zeros_like(eye)
    return np.block([[zero, -eye], [eye, zero]])


def realify(matrix: np.ndarray) -> np.ndarray:
    z = np.asarray(matrix, dtype=complex)
    return np.block([[z.real, -z.imag], [z.imag, z.real]])


def normalize_promotion(raw: np.ndarray, metric_old: np.ndarray | None = None, metric_new: np.ndarray | None = None, atol: float = 1e-12) -> np.ndarray:
    m = np.asarray(raw, dtype=complex)
    rows, cols = m.shape
    if rows < cols:
        raise ValueError("promotion must not reduce carrier dimension")
    g_old = np.eye(cols, dtype=complex) if metric_old is None else np.asarray(metric_old, dtype=complex)
    g_new = np.eye(rows, dtype=complex) if metric_new is None else np.asarray(metric_new, dtype=complex)
    gram = m.conj().T @ g_new @ m
    vals, vecs = np.linalg.eigh(gram)
    if np.min(vals) <= atol:
        raise ValueError("raw promotion is rank deficient under target metric")
    inv_sqrt = (vecs * (1.0 / np.sqrt(vals))) @ vecs.conj().T
    vals_old, vecs_old = np.linalg.eigh(g_old)
    if np.min(vals_old) <= atol:
        raise ValueError("source metric must be positive definite")
    sqrt_old = (vecs_old * np.sqrt(vals_old)) @ vecs_old.conj().T
    return m @ inv_sqrt @ sqrt_old


def promotion_matrix(alpha: complex, beta: complex, dim_old: int, atol: float = 1e-12) -> np.ndarray:
    if dim_old <= 0:
        raise ValueError("dim_old must be positive")
    norm = abs(alpha) ** 2 + abs(beta) ** 2
    if not np.isclose(norm, 1.0, atol=atol):
        raise ValueError("promotion amplitudes must satisfy |alpha|^2 + |beta|^2 = 1")
    eye = np.eye(dim_old, dtype=complex)
    return np.vstack((alpha * eye, beta * eye))


def metric_defect(promotion: np.ndarray, metric_old: np.ndarray | None = None, metric_new: np.ndarray | None = None) -> np.ndarray:
    p = np.asarray(promotion, dtype=complex)
    rows, cols = p.shape
    g_old = np.eye(cols, dtype=complex) if metric_old is None else np.asarray(metric_old, dtype=complex)
    g_new = np.eye(rows, dtype=complex) if metric_new is None else np.asarray(metric_new, dtype=complex)
    return p.conj().T @ g_new @ p - g_old


def complex_intertwiner_defect(promotion: np.ndarray) -> np.ndarray:
    p = np.asarray(promotion, dtype=complex)
    rows, cols = p.shape
    r = realify(p)
    return complex_structure(rows) @ r - r @ complex_structure(cols)


def projector(promotion: np.ndarray) -> np.ndarray:
    p = np.asarray(promotion, dtype=complex)
    return p @ p.conj().T


def orthogonal_projector(promotion: np.ndarray) -> np.ndarray:
    p = np.asarray(promotion, dtype=complex)
    return np.eye(p.shape[0], dtype=complex) - projector(p)


def berry_connection(promotion: np.ndarray, derivative: np.ndarray) -> np.ndarray:
    p = np.asarray(promotion, dtype=complex)
    return p.conj().T @ np.asarray(derivative, dtype=complex)


def qgt_block(promotion: np.ndarray, derivative_mu: np.ndarray, derivative_nu: np.ndarray) -> np.ndarray:
    p = np.asarray(promotion, dtype=complex)
    q = orthogonal_projector(p)
    dmu = np.asarray(derivative_mu, dtype=complex)
    dnu = np.asarray(derivative_nu, dtype=complex)
    return dmu.conj().T @ q @ dnu


def qgt_trace(promotion: np.ndarray, derivative_mu: np.ndarray, derivative_nu: np.ndarray) -> complex:
    return complex(np.trace(qgt_block(promotion, derivative_mu, derivative_nu)))


def berry_curvature_block(promotion: np.ndarray, derivative_mu: np.ndarray, derivative_nu: np.ndarray) -> np.ndarray:
    return qgt_block(promotion, derivative_mu, derivative_nu) - qgt_block(promotion, derivative_nu, derivative_mu)


def connection_defect(promotion: np.ndarray, connection_old: np.ndarray, connection_new: np.ndarray, derivative_promotion: np.ndarray | None = None) -> np.ndarray:
    p = np.asarray(promotion, dtype=complex)
    dp = np.zeros_like(p) if derivative_promotion is None else np.asarray(derivative_promotion, dtype=complex)
    return dp + np.asarray(connection_new, dtype=complex) @ p - p @ np.asarray(connection_old, dtype=complex)


def curvature_defect(promotion: np.ndarray, curvature_old: np.ndarray, curvature_new: np.ndarray) -> np.ndarray:
    p = np.asarray(promotion, dtype=complex)
    return np.asarray(curvature_new, dtype=complex) @ p - p @ np.asarray(curvature_old, dtype=complex)


def lift_local_gate(gate: np.ndarray) -> np.ndarray:
    u = np.asarray(gate, dtype=complex)
    if u.ndim != 2 or u.shape[0] != u.shape[1]:
        raise ValueError("gate must be square")
    return np.kron(np.eye(2, dtype=complex), u)


def controlled_unitary(unitary: np.ndarray) -> np.ndarray:
    u = np.asarray(unitary, dtype=complex)
    if u.ndim != 2 or u.shape[0] != u.shape[1]:
        raise ValueError("unitary must be square")
    d = u.shape[0]
    zero = np.zeros((d, d), dtype=complex)
    eye = np.eye(d, dtype=complex)
    return np.block([[eye, zero], [zero, u]])


def is_unitary(matrix: np.ndarray, atol: float = 1e-10) -> bool:
    u = np.asarray(matrix, dtype=complex)
    return bool(u.ndim == 2 and u.shape[0] == u.shape[1] and np.allclose(u.conj().T @ u, np.eye(u.shape[0]), atol=atol))


def gate_real_contract(gate: np.ndarray, atol: float = 1e-10) -> dict[str, bool]:
    u = np.asarray(gate, dtype=complex)
    r = realify(u)
    j = complex_structure(u.shape[0])
    return {
        "unitary": is_unitary(u, atol=atol),
        "real_orthogonal": bool(np.allclose(r.T @ r, np.eye(r.shape[0]), atol=atol)),
        "commutes_with_J": bool(np.allclose(r @ j, j @ r, atol=atol)),
    }


def segre_determinant_two_qubit(state: np.ndarray) -> complex:
    psi = np.asarray(state, dtype=complex).reshape(-1)
    if psi.size != 4:
        raise ValueError("two-qubit state must have four amplitudes")
    c00, c01, c10, c11 = psi
    return complex(c00 * c11 - c01 * c10)


def relational_wedge_two_qubit(state: np.ndarray) -> float:
    return float(2.0 * abs(segre_determinant_two_qubit(state)))


def bell_state_via_promotion() -> np.ndarray:
    p = promotion_matrix(1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), dim_old=2)
    zero = np.array([1.0, 0.0], dtype=complex)
    x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    return controlled_unitary(x) @ (p @ zero)


def bloch_promotion(theta: float, phi: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    phase = np.exp(1j * phi)
    p = np.array([[c], [phase * s]], dtype=complex)
    dtheta = np.array([[-0.5 * s], [0.5 * phase * c]], dtype=complex)
    dphi = np.array([[0.0], [1j * phase * s]], dtype=complex)
    return p, dtheta, dphi


def candidate_manifest() -> dict[str, object]:
    return dict(CANDIDATE_STATUS)
