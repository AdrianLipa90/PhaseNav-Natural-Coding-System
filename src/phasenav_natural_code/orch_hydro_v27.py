from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import struct
from pathlib import Path
from typing import Mapping, Sequence

try:
    from .hydro_time_v27 import (
        DEFAULT_SURFACE_ROOT, DIM, HydrodynamicPhaseGate, HydrodynamicProperTimeV27Error,
        PhaseFlowState36, _normalize_drive, _sha256_json, _typed_id, _wrap_phase,
        transport_tensor_sha256,
    )
    from .hydro_schedule_v27 import (
        HydrodynamicKakuSchedule, HydrodynamicScheduleV27Error, _validate_v20_receipt,
        load_live_operator_vectors,
    )
    from .orch_orbital_v27 import (
        AttractorReport, MemoryResidue, OrchOrbitalState, OrchOrbitalV27Error,
        ReductionDecision, ReductionKernel, SubjectiveTimeBinding, SubjectiveTimeKernel,
        TotalPotential, bind_subjective_time, bind_t36_state, decide_reduction,
        memory_residue_after_reduction, winding_vector,
    )
except ImportError:  # isolated harness compatibility
    from hydro_time_v27 import (  # type: ignore
        DEFAULT_SURFACE_ROOT, DIM, HydrodynamicPhaseGate, HydrodynamicProperTimeV27Error,
        PhaseFlowState36, _normalize_drive, _sha256_json, _typed_id, _wrap_phase,
        transport_tensor_sha256,
    )
    from hydro_schedule_v27 import (  # type: ignore
        HydrodynamicKakuSchedule, HydrodynamicScheduleV27Error, _validate_v20_receipt,
        load_live_operator_vectors,
    )
    from orch_orbital_v27 import (  # type: ignore
        AttractorReport, MemoryResidue, OrchOrbitalState, OrchOrbitalV27Error,
        ReductionDecision, ReductionKernel, SubjectiveTimeBinding, SubjectiveTimeKernel,
        TotalPotential, bind_subjective_time, bind_t36_state, decide_reduction,
        memory_residue_after_reduction, winding_vector,
    )

ORCH_HYDRO_CONTRACT_ID = "PNCS_ORCHORBITAL_HYDRO_TRANSITION_V0_27"
CONTROL_PROFILE_SCHEMA = "PNCS_ORCHORBITAL_HYDRO_CONTROL_PROFILE_V0_27"
INNER_STEP_SCHEMA = "PNCS_ORCHORBITAL_HYDRO_INNER_STEP_V0_27"
OCCURRENCE_SCHEMA = "PNCS_ORCHORBITAL_HYDRO_KAKU_OCCURRENCE_V0_27"
EXECUTION_TRACE_SCHEMA = "PNCS_ORCHORBITAL_HYDRO_EXECUTION_TRACE_V0_27"


class OrchHydroV27Error(ValueError):
    pass


@dataclass(frozen=True)
class OrchHydroControlProfile:
    time_kernel: SubjectiveTimeKernel
    orbital_radius: float
    attractor_reports: tuple[AttractorReport, ...]
    potential: TotalPotential
    reduction_kernel: ReductionKernel
    relation_alignment: float
    xi: float
    selected_orbital_index: int | None = None
    coupling_scale: float = 0.15
    coupling_gain: float = 0.05
    attractor_force_gain: float = 1.0
    truth_scalar: float | None = None

    def __post_init__(self) -> None:
        r = float(self.orbital_radius)
        if not math.isfinite(r) or r < 0.0:
            raise OrchHydroV27Error("orbital_radius must be finite and non-negative")
        for field in ("relation_alignment", "xi", "coupling_scale", "coupling_gain", "attractor_force_gain"):
            x = float(getattr(self, field))
            if not math.isfinite(x):
                raise OrchHydroV27Error(f"{field} must be finite")
        if self.coupling_scale < 0.0 or self.coupling_scale > 1.0:
            raise OrchHydroV27Error("coupling_scale must be in [0,1]")
        if self.coupling_gain < 0.0 or self.attractor_force_gain < 0.0:
            raise OrchHydroV27Error("force gains must be non-negative")
        if not self.attractor_reports:
            raise OrchHydroV27Error("attractor reports required")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": CONTROL_PROFILE_SCHEMA,
            "contract_id": ORCH_HYDRO_CONTRACT_ID,
            "time_kernel_id": self.time_kernel.kernel_id,
            "orbital_radius": self.orbital_radius,
            "attractor_report_ids": [a.report_id for a in self.attractor_reports],
            "potential_id": self.potential.potential_id,
            "reduction_kernel_id": self.reduction_kernel.kernel_id,
            "relation_alignment": self.relation_alignment,
            "xi": self.xi,
            "selected_orbital_index": self.selected_orbital_index,
            "coupling_scale": self.coupling_scale,
            "coupling_gain": self.coupling_gain,
            "attractor_force_gain": self.attractor_force_gain,
            "truth_scalar": self.truth_scalar,
            "authority_semantics": "EXPLICIT_PROFILE_NOT_INFERRED_FROM_SEMANTIC_MASS",
            "external_effects": False,
        }

    @property
    def profile_id(self) -> str:
        return _typed_id("pncs:orch-hydro-profile", self.payload)


def _attractor_force(profile: OrchHydroControlProfile) -> tuple[float, ...]:
    total = [0.0] * DIM
    for report in profile.attractor_reports:
        scale = report.attractor_weight * report.compatibility_score
        for i, value in enumerate(report.force_contribution):
            total[i] += scale * value
    return tuple(total)


def _coupling_force(state: OrchOrbitalState) -> tuple[float, ...]:
    phases = [o.phase for o in state.orbitals]
    n = len(phases)
    out = []
    for i in range(n):
        force = 0.0
        for j in range(n):
            force += state.couplings[i][j] * math.sin(phases[j] - phases[i])
        out.append(force / n)
    return tuple(out)


@dataclass(frozen=True)
class OrchHydroInnerStep:
    index: int
    before_phase_state_id: str
    after_phase_state: PhaseFlowState36
    before_orch_state_id: str
    after_orch_state_id: str
    time_binding: SubjectiveTimeBinding
    drive_sha256: str
    effective_drive_sha256: str
    coupling_force_sha256: str
    attractor_force_sha256: str
    winding_rel: tuple[float, ...]
    speed_before: float
    speed_after: float
    tensor_sha256_before: str

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": INNER_STEP_SCHEMA,
            "contract_id": ORCH_HYDRO_CONTRACT_ID,
            "index": self.index,
            "before_phase_state_id": self.before_phase_state_id,
            "after_phase_state_id": self.after_phase_state.state_id,
            "before_orch_state_id": self.before_orch_state_id,
            "after_orch_state_id": self.after_orch_state_id,
            "time_binding_id": self.time_binding.binding_id,
            "drive_sha256": self.drive_sha256,
            "effective_drive_sha256": self.effective_drive_sha256,
            "coupling_force_sha256": self.coupling_force_sha256,
            "attractor_force_sha256": self.attractor_force_sha256,
            "winding_components": {"w_rel": list(self.winding_rel)},
            "speed_before": self.speed_before,
            "speed_after": self.speed_after,
            "tensor_sha256_before": self.tensor_sha256_before,
            "semantic_identity_modified": False,
            "external_effects": False,
            "laboratory_time_modified": False,
        }

    @property
    def step_id(self) -> str:
        return _typed_id("pncs:orch-hydro-step", self.payload)


def advance_orchestrated_phase_flow(
    state: PhaseFlowState36,
    gate: HydrodynamicPhaseGate,
    drive: Sequence[float],
    *,
    tick: int,
    program_content_id: str,
    semantic_mass: float,
    profile: OrchHydroControlProfile,
    index: int,
) -> tuple[OrchHydroInnerStep, OrchOrbitalState]:
    d = _normalize_drive(drive)
    drive_sha = _sha256_json(list(d))
    before_orch = bind_t36_state(
        state,
        tick=tick,
        program_content_id=program_content_id,
        semantic_mass=semantic_mass,
        attractor_reports=profile.attractor_reports,
        potential=profile.potential,
        coupling_scale=profile.coupling_scale,
        truth_scalar=profile.truth_scalar,
    )
    tb = bind_subjective_time(
        before_orch,
        profile.time_kernel,
        orbital_radius=profile.orbital_radius,
        substrate_lapse=gate.lapse,
        coordinate_dt=gate.coordinate_dt,
        combined_min=gate.lapse_min,
        combined_max=gate.lapse_max,
    )
    coupling = _coupling_force(before_orch)
    attr_force = _attractor_force(profile)
    effective_raw = tuple(
        d[i] + profile.coupling_gain * coupling[i] + profile.attractor_force_gain * attr_force[i]
        for i in range(DIM)
    )
    effective_drive = _normalize_drive(effective_raw)
    u = state.velocity
    dot_ud = sum(a * b for a, b in zip(u, effective_drive))
    hydro_force = tuple(gate.density * effective_drive[i] + u[i] * dot_ud for i in range(DIM))
    accel = tuple(
        gate.drive_gain * hydro_force[i]
        + profile.coupling_gain * coupling[i]
        + profile.attractor_force_gain * attr_force[i]
        - gate.effective_viscosity * u[i]
        for i in range(DIM)
    )
    proper_dt = tb.proper_dt
    new_u = tuple(u[i] + proper_dt * accel[i] for i in range(DIM))
    speed_before = math.sqrt(sum(x*x for x in u))
    speed_after = math.sqrt(sum(x*x for x in new_u))
    if not math.isfinite(speed_after) or speed_after > gate.max_speed:
        raise OrchHydroV27Error("orchestrated hydrodynamic step exceeded max_speed")
    new_theta = tuple(_wrap_phase(state.theta[i] + proper_dt * new_u[i]) for i in range(DIM))
    after_phase = PhaseFlowState36(new_theta, new_u, state.phase_proper_time + proper_dt)
    after_orch = bind_t36_state(
        after_phase,
        tick=tick + 1,
        program_content_id=program_content_id,
        semantic_mass=semantic_mass,
        attractor_reports=profile.attractor_reports,
        potential=profile.potential,
        coupling_scale=profile.coupling_scale,
        truth_scalar=profile.truth_scalar,
    )
    winding = winding_vector(state.theta, after_phase.theta, coordinate_dt=gate.coordinate_dt, proper_dt=proper_dt)
    step = OrchHydroInnerStep(
        index=index,
        before_phase_state_id=state.state_id,
        after_phase_state=after_phase,
        before_orch_state_id=before_orch.state_id,
        after_orch_state_id=after_orch.state_id,
        time_binding=tb,
        drive_sha256=drive_sha,
        effective_drive_sha256=_sha256_json(list(effective_drive)),
        coupling_force_sha256=_sha256_json(list(coupling)),
        attractor_force_sha256=_sha256_json(list(attr_force)),
        winding_rel=winding,
        speed_before=speed_before,
        speed_after=speed_after,
        tensor_sha256_before=transport_tensor_sha256(state, gate),
    )
    return step, after_orch


@dataclass(frozen=True)
class OrchHydroOccurrence:
    step_index: int
    operator_id: str
    operator_vector_sha256: str
    before_sigma_id: str
    after_sigma_id: str
    initial_phase_state_id: str
    final_phase_state: PhaseFlowState36
    inner_step_ids: tuple[str, ...]
    final_orch_state: OrchOrbitalState
    reduction: ReductionDecision
    memory_residue: MemoryResidue | None
    coordinate_time: float
    proper_time_advanced: float

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": OCCURRENCE_SCHEMA,
            "contract_id": ORCH_HYDRO_CONTRACT_ID,
            "step_index": self.step_index,
            "operator_id": self.operator_id,
            "operator_vector_sha256": self.operator_vector_sha256,
            "before_sigma_id": self.before_sigma_id,
            "after_sigma_id": self.after_sigma_id,
            "initial_phase_state_id": self.initial_phase_state_id,
            "final_phase_state_id": self.final_phase_state.state_id,
            "inner_step_ids": list(self.inner_step_ids),
            "final_orch_state_id": self.final_orch_state.state_id,
            "reduction_decision_id": self.reduction.decision_id,
            "reduction_ready": self.reduction.reduce_ready,
            "memory_residue_id": None if self.memory_residue is None else self.memory_residue.residue_id,
            "stable_memory_update": self.memory_residue is not None,
            "coordinate_time": self.coordinate_time,
            "proper_time_advanced": self.proper_time_advanced,
            "semantic_identity_modified": False,
            "external_effects": False,
        }

    @property
    def occurrence_id(self) -> str:
        return _typed_id("pncs:orch-hydro-occurrence", self.payload)


def run_orchestrated_occurrence(
    initial_state: PhaseFlowState36,
    gate: HydrodynamicPhaseGate,
    drive: Sequence[float],
    *,
    occurrence_step_index: int,
    operator_id: str,
    operator_vector_sha256: str,
    before_sigma_id: str,
    after_sigma_id: str,
    tick_start: int,
    program_content_id: str,
    semantic_mass: float,
    profile: OrchHydroControlProfile,
    identity_input_id: str,
) -> OrchHydroOccurrence:
    current = initial_state
    inner_ids = []
    last_orch = None
    start_tau = current.phase_proper_time
    for inner in range(gate.steps):
        step, last_orch = advance_orchestrated_phase_flow(
            current,
            gate,
            drive,
            tick=tick_start + inner,
            program_content_id=program_content_id,
            semantic_mass=semantic_mass,
            profile=profile,
            index=inner,
        )
        inner_ids.append(step.step_id)
        current = step.after_phase_state
    assert last_orch is not None
    decision = decide_reduction(
        last_orch,
        profile.reduction_kernel,
        relation_alignment=profile.relation_alignment,
        xi=profile.xi,
        selected_orbital_index=profile.selected_orbital_index,
    )
    residue = memory_residue_after_reduction(
        last_orch,
        decision,
        identity_input_id=identity_input_id,
    )
    return OrchHydroOccurrence(
        step_index=occurrence_step_index,
        operator_id=operator_id,
        operator_vector_sha256=operator_vector_sha256,
        before_sigma_id=before_sigma_id,
        after_sigma_id=after_sigma_id,
        initial_phase_state_id=initial_state.state_id,
        final_phase_state=current,
        inner_step_ids=tuple(inner_ids),
        final_orch_state=last_orch,
        reduction=decision,
        memory_residue=residue,
        coordinate_time=gate.steps * gate.coordinate_dt,
        proper_time_advanced=current.phase_proper_time - start_tau,
    )


@dataclass(frozen=True)
class OrchHydroExecutionTrace:
    execution_receipt_sha256: str
    program_content_id: str
    semantic_mass: float
    schedule_id: str
    profile_id: str
    initial_phase_state_id: str
    final_phase_state: PhaseFlowState36
    occurrence_ids: tuple[str, ...]
    operator_names: tuple[str, ...]
    coordinate_time: float
    proper_time_advanced: float
    reduction_ready_count: int
    stable_memory_update_count: int
    live_operator_registry_sha256: str

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": EXECUTION_TRACE_SCHEMA,
            "contract_id": ORCH_HYDRO_CONTRACT_ID,
            "execution_receipt_sha256": self.execution_receipt_sha256,
            "program_content_id": self.program_content_id,
            "semantic_mass": self.semantic_mass,
            "schedule_id": self.schedule_id,
            "profile_id": self.profile_id,
            "initial_phase_state_id": self.initial_phase_state_id,
            "final_phase_state_id": self.final_phase_state.state_id,
            "occurrence_ids": list(self.occurrence_ids),
            "operator_names": list(self.operator_names),
            "coordinate_time": self.coordinate_time,
            "proper_time_advanced": self.proper_time_advanced,
            "reduction_ready_count": self.reduction_ready_count,
            "stable_memory_update_count": self.stable_memory_update_count,
            "live_operator_registry_sha256": self.live_operator_registry_sha256,
            "oorp_pipeline_bound": True,
            "semantic_identity_modified": False,
            "external_effects": False,
            "laboratory_time_modified": False,
            "executor_coupling": "PENDING",
        }

    @property
    def trace_id(self) -> str:
        return _typed_id("pncs:orch-hydro-execution", self.payload)


def replay_v20_orchorbital_hydrodynamic_schedule(
    receipt: Mapping[str, object],
    initial_state: PhaseFlowState36,
    schedule: HydrodynamicKakuSchedule,
    profile: OrchHydroControlProfile,
    *,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
) -> OrchHydroExecutionTrace:
    receipt_sha = _validate_v20_receipt(receipt)
    if schedule.execution_receipt_sha256 != receipt_sha:
        raise OrchHydroV27Error("schedule does not bind exact v0.20 receipt")
    program = receipt.get("program")
    if not isinstance(program, Mapping):
        raise OrchHydroV27Error("v0.20 program payload required")
    program_id = str(program.get("content_id", ""))
    semantic_mass = float(program.get("semantic_mass", -1.0))
    if not program_id or not math.isfinite(semantic_mass) or semantic_mass < 0.0:
        raise OrchHydroV27Error("program identity/semantic mass missing")
    if schedule.program_content_id != program_id:
        raise OrchHydroV27Error("schedule/program identity mismatch")
    steps = receipt.get("steps")
    if not isinstance(steps, list) or len(steps) != len(schedule.entries):
        raise OrchHydroV27Error("schedule length differs from v0.20 receipt")
    operators, registry_sha = load_live_operator_vectors(surface_root)
    current = initial_state
    occurrence_ids = []
    operator_names = []
    coordinate = 0.0
    start_tau = current.phase_proper_time
    ready_count = 0
    memory_count = 0
    tick = 0
    for step, entry in zip(steps, schedule.entries):
        if not isinstance(step, Mapping):
            raise OrchHydroV27Error("invalid v0.20 step")
        if int(step["index"]) != entry.step_index or str(step["operator_id"]) != entry.operator_id:
            raise OrchHydroV27Error("schedule occurrence mismatch")
        if str(step["operator_vector_sha256"]) != entry.operator_vector_sha256:
            raise OrchHydroV27Error("schedule operator hash mismatch")
        vec = operators.get(entry.operator_id.upper())
        if vec is None:
            raise OrchHydroV27Error(f"live operator missing: {entry.operator_id}")
        live_sha = hashlib.sha256(struct.pack("<36d", *vec)).hexdigest()
        if live_sha != entry.operator_vector_sha256:
            raise OrchHydroV27Error("live operator vector bytes differ from exact v0.20 witness")
        occurrence = run_orchestrated_occurrence(
            current,
            entry.gate,
            vec,
            occurrence_step_index=entry.step_index,
            operator_id=entry.operator_id,
            operator_vector_sha256=entry.operator_vector_sha256,
            before_sigma_id=str(step["before_sigma_id"]),
            after_sigma_id=str(step["after_sigma_id"]),
            tick_start=tick,
            program_content_id=program_id,
            semantic_mass=semantic_mass,
            profile=profile,
            identity_input_id=receipt_sha,
        )
        occurrence_ids.append(occurrence.occurrence_id)
        operator_names.append(entry.operator_id)
        coordinate += occurrence.coordinate_time
        ready_count += int(occurrence.reduction.reduce_ready)
        memory_count += int(occurrence.memory_residue is not None)
        tick += entry.gate.steps
        current = occurrence.final_phase_state
    return OrchHydroExecutionTrace(
        execution_receipt_sha256=receipt_sha,
        program_content_id=program_id,
        semantic_mass=semantic_mass,
        schedule_id=schedule.schedule_id,
        profile_id=profile.profile_id,
        initial_phase_state_id=initial_state.state_id,
        final_phase_state=current,
        occurrence_ids=tuple(occurrence_ids),
        operator_names=tuple(operator_names),
        coordinate_time=coordinate,
        proper_time_advanced=current.phase_proper_time - start_tau,
        reduction_ready_count=ready_count,
        stable_memory_update_count=memory_count,
        live_operator_registry_sha256=registry_sha,
    )
