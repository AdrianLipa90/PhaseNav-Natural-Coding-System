from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from .semantic_address_v31 import SemanticTrajectory36
from .semantic_htri_drive_v32 import (
    N, TAU, DEFAULT_DT, KAPPA,
    DriveSnapshot,
    SemanticHTRIDriveV32Error,
    _EYE_N, _CH_ROWS, _CH_COLS,
    _require_vec,
    array_sha,
    digest,
    harmonic_composite_phase,
    phase_state,
    qhtri_graph_hamiltonian,
    unitary,
    wrap_delta,
)

CONTRACT_ID = "PNCS_BOUNDED_MULTI_TICK_HTRI_DRIVE_V0_33"
STEP_SCHEMA = "PNCS_BOUNDED_HTRI_STEP_V0_33"
TRACK_SCHEMA = "PNCS_BOUNDED_HTRI_TARGET_TRACK_V0_33"
EXEC_SCHEMA = "PNCS_BOUNDED_HTRI_EXECUTION_V0_33"
REFERENCE_U_MAX = 50.0
REFERENCE_TOLERANCE_RAD = 1.0e-6
REFERENCE_MAX_TICKS_PER_TARGET = 64
REFERENCE_SETTLE_CONSECUTIVE = 3


class SemanticHTRIBoundedV33Error(SemanticHTRIDriveV32Error):
    pass


@dataclass(frozen=True)
class BoundedStep:
    phi_next: np.ndarray
    g_next: np.ndarray
    gravity_next: np.ndarray
    control: np.ndarray
    exact_control: np.ndarray
    H: np.ndarray
    receipt: Mapping[str, object]


def bounded_step(
    snapshot: DriveSnapshot,
    target36: Sequence[float],
    *,
    u_max: float,
    dt: float = DEFAULT_DT,
) -> BoundedStep:
    if not math.isfinite(u_max) or u_max <= 0.0:
        raise SemanticHTRIBoundedV33Error("u_max must be positive finite")
    if not math.isfinite(dt) or dt <= 0.0:
        raise SemanticHTRIBoundedV33Error("dt must be positive finite")

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
    coupling *= tau_mod * min(float(gravity[1]), 2.0)

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
    base_velocity = effective_omega + coupling
    exact_control = desired / dt - base_velocity
    control = np.clip(exact_control, -u_max, u_max)
    phi_next = (phi_base + dt * (base_velocity + control)) % TAU
    residual = wrap_delta(target, phi_next)

    dphi = wrap_delta(phi_next, phi_base)
    semantic_density = min(10.0, float(np.mean(np.abs(dphi)) / dt))
    gravity_next = gravity.copy()
    gravity_next[0] = semantic_density
    gravity_next[1] = 1.0 + math.tanh(semantic_density * 0.5) * 9.0
    gravity_next[2] = gravity_next[2] * 0.99 + semantic_density * 0.01

    H, hmeta = qhtri_graph_hamiltonian(omega, g)
    saturation = np.abs(exact_control) > u_max
    receipt = {
        "schema": STEP_SCHEMA,
        "contract_id": CONTRACT_ID,
        "source_snapshot_id": snapshot.snapshot_id,
        "dt": float(dt),
        "u_max": float(u_max),
        "target_phase36_sha256": array_sha(target),
        "phi_next_sha256": array_sha(phi_next),
        "g_next_sha256": array_sha(g),
        "H_sha256": array_sha(H),
        "max_target_residual_rad": float(np.max(np.abs(residual))),
        "rms_target_residual_rad": float(np.sqrt(np.mean(residual * residual))),
        "control_l2": float(np.linalg.norm(control)),
        "control_max_abs": float(np.max(np.abs(control))),
        "saturation_fraction": float(np.mean(saturation)),
        "hermiticity_error": float(np.max(np.abs(H - H.conj().T))),
        "semantic_authority": "TYPED_CONTENT_AND_ORDER",
        "drive_role": "CLIPPED_EXACT_INVERSE_DYNAMICS_CONTROL",
        "runtime_role": "CONTROLLED_LIVE_COPY_REFERENCE",
        "qhtri_hamiltonian": hmeta,
        "new_pnv_opcodes": 0,
    }
    return BoundedStep(phi_next, g, gravity_next, control, exact_control, H, receipt)


@dataclass(frozen=True)
class TargetTrack:
    state: DriveSnapshot
    U_total: np.ndarray
    receipt: Mapping[str, object]


def track_target(
    initial: DriveSnapshot,
    target36: Sequence[float],
    *,
    u_max: float = REFERENCE_U_MAX,
    tolerance_rad: float = REFERENCE_TOLERANCE_RAD,
    max_ticks: int = REFERENCE_MAX_TICKS_PER_TARGET,
    settle_consecutive: int = REFERENCE_SETTLE_CONSECUTIVE,
    dt: float = DEFAULT_DT,
    U_total: np.ndarray | None = None,
) -> TargetTrack:
    if not math.isfinite(tolerance_rad) or tolerance_rad <= 0.0:
        raise SemanticHTRIBoundedV33Error("tolerance_rad must be positive finite")
    if max_ticks < 1 or settle_consecutive < 1:
        raise SemanticHTRIBoundedV33Error("tick counts must be positive")
    if settle_consecutive > max_ticks:
        raise SemanticHTRIBoundedV33Error("settle_consecutive exceeds max_ticks")

    state = initial
    total = np.eye(N, dtype=np.complex128) if U_total is None else np.asarray(U_total, dtype=np.complex128).copy()
    consecutive = 0
    first_settle: int | None = None
    ticks: list[dict[str, object]] = []

    for tick_index in range(1, max_ticks + 1):
        step = bounded_step(state, target36, u_max=u_max, dt=dt)
        U = unitary(step.H, dt)
        total = U @ total
        unit_err = float(np.max(np.abs(total.conj().T @ total - np.eye(N))))
        rec = dict(step.receipt)
        rec["tick_index"] = tick_index
        rec["cumulative_unitarity_error"] = unit_err
        ticks.append(rec)

        residual = float(step.receipt["max_target_residual_rad"])
        if residual <= tolerance_rad:
            consecutive += 1
            if consecutive == settle_consecutive:
                first_settle = tick_index - settle_consecutive + 1
        else:
            consecutive = 0

        state = DriveSnapshot.build(
            phi=step.phi_next,
            omega=state.omega,
            g=step.g_next,
            flavor=state.flavor,
            tau=state.tau,
            gravity=step.gravity_next,
            source_id=f"{initial.snapshot_id}:bounded-tick:{tick_index}",
        )
        if first_settle is not None:
            break

    status = "PASS_TARGET_SETTLED" if first_settle is not None else "FAIL_TARGET_SETTLING_TIMEOUT"
    payload = {
        "schema": TRACK_SCHEMA,
        "contract_id": CONTRACT_ID,
        "status": status,
        "initial_snapshot_id": initial.snapshot_id,
        "u_max": float(u_max),
        "tolerance_rad": float(tolerance_rad),
        "max_ticks": int(max_ticks),
        "settle_consecutive": int(settle_consecutive),
        "settling_tick": first_settle,
        "ticks_used": len(ticks),
        "last_max_target_residual_rad": float(ticks[-1]["max_target_residual_rad"]),
        "mean_saturation_fraction": float(np.mean([x["saturation_fraction"] for x in ticks])),
        "max_saturation_fraction": float(np.max([x["saturation_fraction"] for x in ticks])),
        "ticks": ticks,
    }
    return TargetTrack(state, total, {**payload, "track_id": "pncs:htri-target-track:sha256:" + digest(payload)})


def execute_bounded_trajectory(
    initial: DriveSnapshot,
    trajectory: SemanticTrajectory36,
    *,
    u_max: float = REFERENCE_U_MAX,
    tolerance_rad: float = REFERENCE_TOLERANCE_RAD,
    max_ticks_per_target: int = REFERENCE_MAX_TICKS_PER_TARGET,
    settle_consecutive: int = REFERENCE_SETTLE_CONSECUTIVE,
    dt: float = DEFAULT_DT,
) -> dict[str, object]:
    if not isinstance(trajectory, SemanticTrajectory36):
        raise SemanticHTRIBoundedV33Error("SemanticTrajectory36 required")

    state = initial
    U_total = np.eye(N, dtype=np.complex128)
    psi0 = phase_state(initial.phi)
    target_receipts: list[Mapping[str, object]] = []

    for index, address in enumerate(trajectory.addresses):
        tr = track_target(
            state,
            address.phase36,
            u_max=u_max,
            tolerance_rad=tolerance_rad,
            max_ticks=max_ticks_per_target,
            settle_consecutive=settle_consecutive,
            dt=dt,
            U_total=U_total,
        )
        rec = dict(tr.receipt)
        rec.update({
            "target_index": index,
            "semantic_content_id": address.content_id,
            "semantic_address_id": address.address_id,
        })
        target_receipts.append(rec)
        state = tr.state
        U_total = tr.U_total
        if rec["status"] != "PASS_TARGET_SETTLED":
            break

    all_pass = len(target_receipts) == len(trajectory.addresses) and all(
        r["status"] == "PASS_TARGET_SETTLED" for r in target_receipts
    )
    psi_final = U_total @ psi0
    all_ticks = [tick for target in target_receipts for tick in target["ticks"]]
    payload = {
        "schema": EXEC_SCHEMA,
        "contract_id": CONTRACT_ID,
        "status": "PASS_BOUNDED_MULTI_TICK_TRAJECTORY" if all_pass else "FAIL_BOUNDED_MULTI_TICK_TRAJECTORY",
        "initial_snapshot_id": initial.snapshot_id,
        "trajectory_id": trajectory.trajectory_id,
        "ordered_semantic_id": trajectory.ordered_semantic_id,
        "u_max": float(u_max),
        "tolerance_rad": float(tolerance_rad),
        "max_ticks_per_target": int(max_ticks_per_target),
        "settle_consecutive": int(settle_consecutive),
        "dt": float(dt),
        "targets_completed": sum(r["status"] == "PASS_TARGET_SETTLED" for r in target_receipts),
        "total_ticks": sum(int(r["ticks_used"]) for r in target_receipts),
        "target_receipts": target_receipts,
        "final_phi_sha256": array_sha(state.phi),
        "final_g_sha256": array_sha(state.g),
        "U_total_sha256": array_sha(U_total),
        "final_state_sha256": array_sha(np.asarray(psi_final, dtype=np.complex128)),
        "max_hermiticity_error": max((float(t["hermiticity_error"]) for t in all_ticks), default=0.0),
        "max_cumulative_unitarity_error": max((float(t["cumulative_unitarity_error"]) for t in all_ticks), default=0.0),
        "total_control_l2": float(math.sqrt(sum(float(t["control_l2"]) ** 2 for t in all_ticks))),
        "max_control_abs": max((float(t["control_max_abs"]) for t in all_ticks), default=0.0),
        "semantic_authority": "TYPED_CONTENT_AND_ORDER",
        "execution_status": "MODEL_LEVEL_BOUNDED_CONTROLLED_HTRI_QHTRI_REFERENCE",
        "runtime_role": "READ_ONLY_LIVE_DERIVED_COPY",
        "new_pnv_opcodes": 0,
    }
    return {
        **payload,
        "execution_id": "pncs:bounded-semantic-htri-execution:sha256:" + digest(payload),
        "receipt_sha256": digest(payload),
        "psi_final": psi_final,
        "U_total": U_total,
        "final_phi": state.phi,
        "final_g": state.g,
    }
