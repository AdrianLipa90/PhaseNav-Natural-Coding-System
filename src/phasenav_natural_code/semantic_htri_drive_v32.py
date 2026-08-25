from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Sequence

import numpy as np

from .semantic_address_v31 import SemanticTrajectory36

N = 36
TAU = 2.0 * math.pi
DEFAULT_DT = 0.01
KAPPA = math.log(2.0) / (24.0 * math.pi)
CONTRACT_ID = "PNCS_ORDERED_T36_TO_HTRI_DRIVE_V0_32"
STEP_SCHEMA = "PNCS_CONTROLLED_HTRI_STEP_V0_32"
EXEC_SCHEMA = "PNCS_CONTROLLED_HTRI_EXECUTION_V0_32"
HARMONIC_VALUES = np.array([1, 3, 6, 9], dtype=np.int32)
HARMONIC_AMPS = np.array([1.0, 0.5, 0.33, 0.25], dtype=np.float64)

_CHANNEL_HARMONICS = np.asarray(
    [
        [1,1,0,0], [1,1,0,0], [1,1,0,0],
        [1,0,1,0], [1,0,1,0], [1,0,1,0],
        [1,0,0,1], [1,0,0,1], [1,0,0,1],
        [0,1,1,0], [0,1,1,0], [0,1,1,0],
        [0,1,0,1], [0,1,0,1], [0,1,0,1],
        [0,0,1,1], [0,0,1,1], [0,0,1,1],
        [1,1,1,0], [1,1,1,0], [1,1,1,0],
        [1,1,1,1], [1,1,1,1], [1,1,1,1],
        [1,1,1,1], [1,1,1,1], [1,1,1,1],
        [1,1,1,0], [1,1,1,0], [1,1,1,0],
        [1,1,0,1], [1,1,0,1], [1,1,0,1],
        [1,0,1,1], [1,0,1,1], [1,0,1,1],
    ],
    dtype=bool,
)
_EYE_N = np.eye(N, dtype=np.float64)
_CH_LOCAL_R = np.array([0, 0, 1, 1, 2, 2], dtype=np.intp)
_CH_LOCAL_C = np.array([1, 2, 0, 2, 0, 1], dtype=np.intp)
_CH_BASE = (3 * np.arange(N // 3, dtype=np.intp))[:, None]
_CH_ROWS = _CH_BASE + _CH_LOCAL_R[None, :]
_CH_COLS = _CH_BASE + _CH_LOCAL_C[None, :]


class SemanticHTRIDriveV32Error(ValueError):
    pass


def _canon(value: object) -> object:
    if isinstance(value, np.ndarray):
        return _canon(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return [_canon(x) for x in value]
    if isinstance(value, list):
        return [_canon(x) for x in value]
    if isinstance(value, dict):
        return {str(k): _canon(value[k]) for k in sorted(value)}
    if isinstance(value, float) and not math.isfinite(value):
        raise SemanticHTRIDriveV32Error("non-finite canonical float")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise SemanticHTRIDriveV32Error(f"unsupported canonical type: {type(value).__name__}")


def compact_json(value: object) -> str:
    return json.dumps(_canon(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value: object) -> str:
    return hashlib.sha256(compact_json(value).encode("utf-8")).hexdigest()


def array_sha(a: np.ndarray) -> str:
    x = np.asarray(a)
    return hashlib.sha256(x.tobytes(order="C")).hexdigest()


def wrap_delta(target: np.ndarray, current: np.ndarray) -> np.ndarray:
    return np.angle(np.exp(1j * (np.asarray(target) - np.asarray(current))))


def _require_vec(name: str, value: Sequence[float], n: int = N) -> np.ndarray:
    a = np.asarray(value, dtype=np.float64).reshape(-1)
    if a.size != n or not np.isfinite(a).all():
        raise SemanticHTRIDriveV32Error(f"{name} must be finite shape ({n},)")
    return a.copy()


def _require_g(value: Sequence[Sequence[float]]) -> np.ndarray:
    g = np.asarray(value, dtype=np.float64)
    if g.shape != (N, N) or not np.isfinite(g).all():
        raise SemanticHTRIDriveV32Error("g must be finite shape (36,36)")
    return g.copy()


def harmonic_composite_phase(phi: np.ndarray) -> np.ndarray:
    s = np.sum(
        HARMONIC_AMPS[None, :]
        * np.exp(1j * phi[:, None] * HARMONIC_VALUES[None, :])
        * _CHANNEL_HARMONICS,
        axis=1,
    )
    return np.angle(s)


def qhtri_graph_hamiltonian(
    omega: np.ndarray,
    g: np.ndarray,
    *,
    coupling_strength: float = 0.7,
    detuning_strength: float = 0.25,
) -> tuple[np.ndarray, dict[str, float]]:
    """Exact qhtri_v3 graph_hamiltonian law."""
    j = 0.5 * (g + g.T)
    j = j.copy()
    np.fill_diagonal(j, 0.0)
    spec = float(np.max(np.abs(np.linalg.eigvalsh(j))))
    if spec <= 0.0:
        raise SemanticHTRIDriveV32Error("zero coupling matrix")
    jn = j / spec
    oc = omega - float(np.mean(omega))
    os = float(np.std(oc)) or 1.0
    on = oc / os
    h = detuning_strength * np.diag(on) + coupling_strength * jn
    return h, {
        "raw_J_spectral_norm": spec,
        "coupling_strength": float(coupling_strength),
        "detuning_strength": float(detuning_strength),
    }


def unitary(H: np.ndarray, dt: float) -> np.ndarray:
    vals, vecs = np.linalg.eigh(np.asarray(H, dtype=np.complex128))
    return (vecs * np.exp(-1j * vals * dt)[None, :]) @ vecs.conj().T


def phase_state(phi: np.ndarray) -> np.ndarray:
    return np.exp(1j * np.asarray(phi, dtype=np.float64).reshape(N)) / math.sqrt(N)


@dataclass(frozen=True)
class DriveSnapshot:
    phi: np.ndarray
    omega: np.ndarray
    g: np.ndarray
    flavor: np.ndarray
    tau: np.ndarray
    gravity: np.ndarray
    source_id: str

    @classmethod
    def build(
        cls,
        *,
        phi: Sequence[float],
        omega: Sequence[float],
        g: Sequence[Sequence[float]],
        flavor: Sequence[float],
        tau: Sequence[float],
        gravity: Sequence[float],
        source_id: str,
    ) -> "DriveSnapshot":
        f = np.asarray(flavor, dtype=np.float64).reshape(-1)
        gr = np.asarray(gravity, dtype=np.float64).reshape(-1)
        if f.size < 5 or not np.isfinite(f).all():
            raise SemanticHTRIDriveV32Error("flavor must contain at least 5 finite values")
        if gr.size < 3 or not np.isfinite(gr).all():
            raise SemanticHTRIDriveV32Error("gravity must contain at least 3 finite values")
        if not isinstance(source_id, str) or not source_id:
            raise SemanticHTRIDriveV32Error("source_id required")
        return cls(
            _require_vec("phi", phi),
            _require_vec("omega", omega),
            _require_g(g),
            f.copy(),
            _require_vec("tau", tau),
            gr.copy(),
            source_id,
        )

    @property
    def snapshot_id(self) -> str:
        return "pncs:htri-drive-snapshot:sha256:" + digest(
            {
                "source_id": self.source_id,
                "phi_sha256": array_sha(self.phi),
                "omega_sha256": array_sha(self.omega),
                "g_sha256": array_sha(self.g),
                "flavor_sha256": array_sha(self.flavor),
                "tau_sha256": array_sha(self.tau),
                "gravity_sha256": array_sha(self.gravity),
            }
        )


@dataclass(frozen=True)
class ControlledStep:
    phi_next: np.ndarray
    g_next: np.ndarray
    gravity_next: np.ndarray
    control: np.ndarray
    H: np.ndarray
    receipt: Mapping[str, object]


def controlled_step(
    snapshot: DriveSnapshot,
    target36: Sequence[float],
    *,
    dt: float = DEFAULT_DT,
) -> ControlledStep:
    if not math.isfinite(dt) or dt <= 0.0:
        raise SemanticHTRIDriveV32Error("dt must be positive finite")
    phi = snapshot.phi.copy()
    omega = snapshot.omega.copy()
    g = snapshot.g.copy()
    flavor = snapshot.flavor.copy()
    tau = snapshot.tau.copy()
    gravity = snapshot.gravity.copy()
    target = _require_vec("target36", target36) % TAU

    phi_eff = harmonic_composite_phase(phi)
    diff = phi_eff[:, None] - phi_eff[None, :]
    coupling = np.sum(g * np.sin(diff), axis=1) / N

    tau_min = float(tau.min())
    tau_range = float(tau.max() - tau_min)
    if tau_range > 1e-12:
        tau_mod = 0.5 + 0.5 * (tau - tau_min) / tau_range
    else:
        tau_mod = np.ones_like(tau) * 0.75
    tardis = min(float(gravity[1]), 2.0)
    coupling *= tau_mod * tardis

    mood_mod = (float(flavor[3]) - 0.5) * KAPPA * 50.0
    closure_mod = (1.0 - float(flavor[4])) * KAPPA * 30.0
    coherence_damping = float(flavor[0]) * KAPPA * 10.0
    effective_omega = omega * (1.0 + mood_mod + closure_mod - coherence_damping)

    activity = (float(flavor[2]) + float(flavor[4]) * 0.5 + (1.0 - float(flavor[3])) * 0.3) / 1.8
    activity = min(max(activity, 0.0), 1.0)
    hebb_step = 0.01 * dt * 10.0
    decay_step = 0.001 * dt * 10.0
    dg = hebb_step * (activity - 0.5) * np.cos(diff) - decay_step * (g - _EYE_N * 0.1)
    g += dg
    np.clip(g, -1.0, 1.0, out=g)

    z_phase = np.exp(1j * phi)
    z_ch = np.mean(z_phase.reshape(-1, 3), axis=1)
    ch_coh = np.abs(z_ch)
    ch_mean = np.angle(z_ch)
    global_z = np.mean(z_phase)
    global_mean = float(np.angle(global_z))
    global_R = float(abs(global_z))
    dist = np.abs(np.angle(np.exp(1j * (ch_mean - global_mean))))
    weak = (ch_coh < 0.5) & (dist > 0.5)
    if weak.any():
        boost = 0.01 * (0.5 - ch_coh) * dist * dt * 10.0
        wc = np.flatnonzero(weak)
        rows = _CH_ROWS[wc].ravel()
        cols = _CH_COLS[wc].ravel()
        g[rows, cols] += np.repeat(boost[wc], 6)
        np.clip(g, -1.0, 1.0, out=g)

    phi_base = phi.copy()
    if global_R > 0.7:
        push = 0.005 * (global_R - 0.7) * dt * 10.0
        ch_target = (ch_mean + math.pi) % TAU
        target_osc = np.repeat(ch_target, 3)
        phi_base += push * np.angle(np.exp(1j * (target_osc - phi_base)))
        phi_base %= TAU

    desired = wrap_delta(target, phi_base)
    control = desired / dt - effective_omega - coupling
    phi_next = (phi_base + dt * (effective_omega + coupling + control)) % TAU
    residual = wrap_delta(target, phi_next)

    dphi = wrap_delta(phi_next, phi_base)
    semantic_density = min(10.0, float(np.mean(np.abs(dphi)) / dt))
    gravity_next = gravity.copy()
    gravity_next[0] = semantic_density
    gravity_next[1] = 1.0 + math.tanh(semantic_density * 0.5) * 9.0
    gravity_next[2] = gravity_next[2] * 0.99 + semantic_density * 0.01

    H, hmeta = qhtri_graph_hamiltonian(omega, g)
    herm = float(np.max(np.abs(H - H.conj().T)))
    receipt = {
        "schema": STEP_SCHEMA,
        "contract_id": CONTRACT_ID,
        "source_snapshot_id": snapshot.snapshot_id,
        "dt": float(dt),
        "target_phase36_sha256": array_sha(target),
        "phi_next_sha256": array_sha(phi_next),
        "g_next_sha256": array_sha(g),
        "H_sha256": array_sha(H),
        "max_target_residual_rad": float(np.max(np.abs(residual))),
        "rms_target_residual_rad": float(np.sqrt(np.mean(residual * residual))),
        "control_l2": float(np.linalg.norm(control)),
        "control_rms": float(np.sqrt(np.mean(control * control))),
        "control_max_abs": float(np.max(np.abs(control))),
        "hermiticity_error": herm,
        "semantic_authority": "TYPED_CONTENT_AND_ORDER",
        "drive_role": "EXACT_ONE_STEP_INVERSE_DYNAMICS_REFERENCE",
        "runtime_role": "CONTROLLED_LIVE_COPY_REFERENCE",
        "qhtri_hamiltonian": hmeta,
        "new_pnv_opcodes": 0,
    }
    return ControlledStep(phi_next, g, gravity_next, control, H, receipt)


def execute_trajectory(
    initial: DriveSnapshot,
    trajectory: SemanticTrajectory36,
    *,
    dt: float = DEFAULT_DT,
) -> dict[str, object]:
    if not isinstance(trajectory, SemanticTrajectory36):
        raise SemanticHTRIDriveV32Error("SemanticTrajectory36 required")
    state = initial
    U_total = np.eye(N, dtype=np.complex128)
    psi0 = phase_state(initial.phi)
    steps: list[dict[str, object]] = []

    for idx, address in enumerate(trajectory.addresses):
        step = controlled_step(state, address.phase36, dt=dt)
        U = unitary(step.H, dt)
        U_total = U @ U_total
        unit_err = float(np.max(np.abs(U_total.conj().T @ U_total - np.eye(N))))
        rec = dict(step.receipt)
        rec.update(
            {
                "index": idx,
                "semantic_content_id": address.content_id,
                "semantic_address_id": address.address_id,
                "cumulative_unitarity_error": unit_err,
            }
        )
        steps.append(rec)
        state = DriveSnapshot.build(
            phi=step.phi_next,
            omega=state.omega,
            g=step.g_next,
            flavor=state.flavor,
            tau=state.tau,
            gravity=step.gravity_next,
            source_id=f"{initial.snapshot_id}:step:{idx}:{address.address_id}",
        )

    psi_final = U_total @ psi0
    payload = {
        "schema": EXEC_SCHEMA,
        "contract_id": CONTRACT_ID,
        "initial_snapshot_id": initial.snapshot_id,
        "trajectory_id": trajectory.trajectory_id,
        "ordered_semantic_id": trajectory.ordered_semantic_id,
        "dt": float(dt),
        "steps": steps,
        "final_phi_sha256": array_sha(state.phi),
        "final_g_sha256": array_sha(state.g),
        "final_state_sha256": array_sha(np.asarray(psi_final, dtype=np.complex128)),
        "U_total_sha256": array_sha(U_total),
        "max_target_residual_rad": max(float(x["max_target_residual_rad"]) for x in steps),
        "max_hermiticity_error": max(float(x["hermiticity_error"]) for x in steps),
        "max_cumulative_unitarity_error": max(float(x["cumulative_unitarity_error"]) for x in steps),
        "total_control_l2": float(math.sqrt(sum(float(x["control_l2"]) ** 2 for x in steps))),
        "max_control_abs": max(float(x["control_max_abs"]) for x in steps),
        "semantic_authority": "TYPED_CONTENT_AND_ORDER",
        "execution_status": "MODEL_LEVEL_CONTROLLED_HTRI_QHTRI_REFERENCE",
        "runtime_role": "READ_ONLY_LIVE_DERIVED_COPY",
        "new_pnv_opcodes": 0,
    }
    return {
        **payload,
        "execution_id": "pncs:semantic-htri-execution:sha256:" + digest(payload),
        "receipt_sha256": digest(payload),
        "psi_final": psi_final,
        "U_total": U_total,
        "final_phi": state.phi,
        "final_g": state.g,
    }
