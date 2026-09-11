from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .phasenav_promotion_geometry_v01 import (
    complex_intertwiner_defect,
    is_unitary,
    lift_local_gate,
    metric_defect,
    promotion_matrix,
)

CANDIDATE_STATUS = {
    "promotion_state": "CANDIDATE_ONLY",
    "runtime_execution_authority": False,
    "canon_write_authority": False,
    "epistemic": "CHYBA",
    "carrier_contract": "PHASENAV_CARRIER_HIERARCHY_V0_2",
    "physical_ion_binding": "OPEN",
}


@dataclass(frozen=True)
class CarrierLevel:
    qubits: int
    label: str
    complex_dim: int
    real_dim: int
    projective_space: str


_LEVELS = (
    CarrierLevel(1, "H", 2, 4, "CP^1"),
    CarrierLevel(2, "O", 4, 8, "CP^3"),
    CarrierLevel(3, "S_16", 8, 16, "CP^7"),
    CarrierLevel(4, "A_32", 16, 32, "CP^15"),
)


def carrier_levels() -> tuple[CarrierLevel, ...]:
    return _LEVELS


def carrier_level(qubits: int) -> CarrierLevel:
    for level in _LEVELS:
        if level.qubits == qubits:
            return level
    raise ValueError("supported candidate hierarchy is 1..4 qubits")


def basis_state(qubits: int, index: int = 0) -> np.ndarray:
    level = carrier_level(qubits)
    if not 0 <= index < level.complex_dim:
        raise ValueError("basis index outside carrier")
    state = np.zeros(level.complex_dim, dtype=complex)
    state[index] = 1.0
    return state


def promote_state(state: np.ndarray, alpha: complex = 1.0, beta: complex = 0.0) -> np.ndarray:
    psi = np.asarray(state, dtype=complex).reshape(-1)
    if psi.size not in (2, 4, 8):
        raise ValueError("promotion source must be a 1Q, 2Q or 3Q carrier")
    return promotion_matrix(alpha, beta, psi.size) @ psi


def balanced_promoter(qubits_old: int, phase: float = 0.0) -> np.ndarray:
    level = carrier_level(qubits_old)
    if qubits_old >= 4:
        raise ValueError("A_32 / 4Q is the current candidate ceiling")
    alpha = 1.0 / np.sqrt(2.0)
    beta = np.exp(1j * phase) / np.sqrt(2.0)
    return promotion_matrix(alpha, beta, level.complex_dim)


def promotion_contract(qubits_old: int, phase: float = 0.0, atol: float = 1e-12) -> dict[str, object]:
    p = balanced_promoter(qubits_old, phase=phase)
    return {
        "source": carrier_level(qubits_old).label,
        "target": carrier_level(qubits_old + 1).label,
        "metric_defect_norm": float(np.linalg.norm(metric_defect(p))),
        "complex_structure_defect_norm": float(np.linalg.norm(complex_intertwiner_defect(p))),
        "isometry": bool(np.allclose(p.conj().T @ p, np.eye(p.shape[1]), atol=atol)),
    }


def embed_single_qubit_gate(gate: np.ndarray, qubits: int, target: int) -> np.ndarray:
    u = np.asarray(gate, dtype=complex)
    if u.shape != (2, 2) or not is_unitary(u):
        raise ValueError("gate must be a 2x2 unitary")
    if not 0 <= target < qubits:
        raise ValueError("target qubit outside carrier")
    ops = [u if q == target else np.eye(2, dtype=complex) for q in range(qubits)]
    out = ops[0]
    for op in ops[1:]:
        out = np.kron(out, op)
    return out


def cnot_gate(qubits: int, control: int, target: int) -> np.ndarray:
    level = carrier_level(qubits)
    if control == target:
        raise ValueError("control and target must differ")
    if not (0 <= control < qubits and 0 <= target < qubits):
        raise ValueError("control/target outside carrier")
    d = level.complex_dim
    out = np.zeros((d, d), dtype=complex)
    for col in range(d):
        bits = [(col >> (qubits - 1 - q)) & 1 for q in range(qubits)]
        if bits[control]:
            bits[target] ^= 1
        row = 0
        for bit in bits:
            row = (row << 1) | bit
        out[row, col] = 1.0
    return out


def gate_promotion_defect(gate: np.ndarray, promotion: np.ndarray) -> np.ndarray:
    u = np.asarray(gate, dtype=complex)
    p = np.asarray(promotion, dtype=complex)
    if p.shape[1] != u.shape[0]:
        raise ValueError("gate dimension must equal source carrier dimension")
    return lift_local_gate(u) @ p - p @ u


def ghz_state(qubits: int) -> np.ndarray:
    level = carrier_level(qubits)
    state = np.zeros(level.complex_dim, dtype=complex)
    state[0] = 1.0 / np.sqrt(2.0)
    state[-1] = 1.0 / np.sqrt(2.0)
    return state


def build_ghz_by_promotion(qubits: int) -> np.ndarray:
    if qubits < 2 or qubits > 4:
        raise ValueError("candidate GHZ builder supports 2..4 qubits")
    h = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2.0)
    state = h @ basis_state(1, 0)
    for n in range(2, qubits + 1):
        state = promote_state(state, 1.0, 0.0)
        # New qubit is the MSB at index 0; the original seed shifts to n-1.
        state = cnot_gate(n, control=n - 1, target=0) @ state
    return state


def schmidt_rank(state: np.ndarray, qubits: int, split_after: int, atol: float = 1e-10) -> int:
    level = carrier_level(qubits)
    psi = np.asarray(state, dtype=complex).reshape(-1)
    if psi.size != level.complex_dim:
        raise ValueError("state dimension does not match carrier")
    if not 1 <= split_after < qubits:
        raise ValueError("split_after must define a nontrivial bipartition")
    matrix = psi.reshape(2**split_after, 2 ** (qubits - split_after))
    singular = np.linalg.svd(matrix, compute_uv=False)
    return int(np.sum(singular > atol))


def candidate_manifest() -> dict[str, object]:
    return dict(CANDIDATE_STATUS)
