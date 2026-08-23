from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import struct
from typing import Mapping, Sequence

from .execution_v20_model import BoundInternalProgram, _sha256_json, _typed_id
from .execution_v20_live import LiveSurfaceSnapshot
from .execution_v20_state import ExecutionStep, SigmaState, _Executor
from .hydro_time_v27 import HydrodynamicPhaseGate, PhaseFlowState36
from .orchorbital_v27 import (
    AttractorWeights,
    OrchState,
    Orbital,
    Potentials,
    ProcessSphere,
    ReductionLaw,
    SelectionLaw,
    TimeLaw,
)
from .orchorbital_hydro_v27 import (
    BridgePolicy,
    ProjectionPolicy,
    OrchHydroV27Error,
    Transition,
    transition as orch_hydro_transition,
    validate_receipt,
)

EXECUTOR_COUPLING_ID = "PNCS_ORCHORBITAL_DIRECT_EXECUTOR_COUPLING_V0_27"
TRACE_SCHEMA = "PNCS_ORCHORBITAL_DIRECT_EXECUTION_TRACE_V0_27"
BOUND_TRACE_SCHEMA = "PNCS_ORCHORBITAL_RECEIPT_BOUND_EXECUTION_TRACE_V0_27"


class OrchExecutorV27Error(ValueError):
    pass


def _canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _operator_projection(
    program_id: str,
    step: ExecutionStep,
    vector: Sequence[float],
    policy: ProjectionPolicy,
    semantic_mass: float,
) -> Orbital:
    vals = tuple(float(x) for x in vector)
    if len(vals) != 36 or not all(math.isfinite(x) for x in vals):
        raise OrchExecutorV27Error("exact finite 36D operator vector required")
    raw_sha = hashlib.sha256(struct.pack("<36d", *vals)).hexdigest()
    if raw_sha != step.operator_vector_sha256:
        raise OrchExecutorV27Error("live operator vector differs from v0.20 transition")
    re = sum(math.cos(x) for x in vals)
    im = sum(math.sin(x) for x in vals)
    phase = math.atan2(im, re) % (2.0 * math.pi)
    coherence = math.hypot(re, im) / 36.0
    amplitude = policy.amplitude_scale * math.sqrt(sum(x * x for x in vals) / 36.0)
    bindings = step.bindings
    truth = bindings.get("truth") if isinstance(bindings, Mapping) else None
    truth_spin = 1 if truth is True else (-1 if truth is False else 0)
    occurrence_id = _typed_id(
        "pncs:live-kaku-orbital",
        {
            "schema": "PNCS_LIVE_KAKU_ORBITAL_OCCURRENCE_V0_27",
            "program_content_id": program_id,
            "step_index": step.index,
            "operator_id": step.operator_id,
            "operator_vector_sha256": step.operator_vector_sha256,
            "before_sigma_id": step.before_sigma_id,
            "after_sigma_id": step.after_sigma_id,
            "projection_policy_id": policy.policy_id,
        },
    )
    return Orbital(
        occurrence_id,
        amplitude,
        phase,
        coherence,
        truth_spin,
        policy.memory_affinity,
        policy.orbital_radius,
        semantic_mass,
        policy.attractor_influence,
        policy.attractor_weights,
    )


def _append_occurrence(
    current: OrchState | None,
    orbital: Orbital,
    *,
    program_content_id: str,
    relation_id: str,
    intent_id: str,
    policy: ProjectionPolicy,
    potentials: Potentials,
    previous_memory_state_id: str | None,
) -> OrchState:
    if current is None:
        orbitals = (orbital,)
        tick = 0
    else:
        if orbital.mode_id in current.sphere.mode_ids:
            raise OrchExecutorV27Error("duplicate live KAKU occurrence identity")
        orbitals = current.orbitals + (orbital,)
        tick = current.tick
    ids = tuple(o.mode_id for o in orbitals)
    n = len(ids)
    coupling = [[0.0] * n for _ in range(n)]
    if current is not None:
        old = current.sphere.coupling
        for i in range(n - 1):
            for j in range(n - 1):
                coupling[i][j] = old[i][j]
    if n > 1:
        coupling[n - 2][n - 1] = policy.adjacency_coupling
        coupling[n - 1][n - 2] = policy.adjacency_coupling
    sphere_id = _typed_id(
        "pncs:live-kaku-process-sphere",
        {
            "schema": "PNCS_LIVE_KAKU_PROCESS_SPHERE_V0_27",
            "program_content_id": program_content_id,
            "mode_ids": list(ids),
            "projection_policy_id": policy.policy_id,
        },
    )
    sphere = ProcessSphere(
        sphere_id,
        ids,
        tuple(tuple(row) for row in coupling),
        policy.leak_mode,
        policy.sphere_attractor_weight,
    )
    return OrchState(
        tick,
        relation_id,
        intent_id,
        sphere,
        orbitals,
        potentials,
        previous_memory_state_id,
    )


@dataclass(frozen=True)
class CouplingConfig:
    projection_policy: ProjectionPolicy
    time_law: TimeLaw
    reduction_law: ReductionLaw
    selection_law: SelectionLaw
    bridge_policy: BridgePolicy
    gates_by_step: Mapping[int, HydrodynamicPhaseGate]
    relation_id: str
    intent_id: str
    relation_alignment: float
    contradiction_load: float
    potentials: Potentials
    previous_memory_state_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.projection_policy, ProjectionPolicy):
            raise OrchExecutorV27Error("ProjectionPolicy required")
        if not isinstance(self.time_law, TimeLaw) or not isinstance(self.reduction_law, ReductionLaw):
            raise OrchExecutorV27Error("ORCH time/reduction laws required")
        if not isinstance(self.selection_law, SelectionLaw) or not isinstance(self.bridge_policy, BridgePolicy):
            raise OrchExecutorV27Error("selection/bridge laws required")
        if not isinstance(self.gates_by_step, Mapping) or not self.gates_by_step:
            raise OrchExecutorV27Error("explicit gates_by_step mapping required")
        for key, gate in self.gates_by_step.items():
            if isinstance(key, bool) or not isinstance(key, int) or key < 1 or not isinstance(gate, HydrodynamicPhaseGate):
                raise OrchExecutorV27Error("invalid step gate binding")
        if not isinstance(self.relation_id, str) or not self.relation_id or not isinstance(self.intent_id, str) or not self.intent_id:
            raise OrchExecutorV27Error("relation_id and intent_id required")
        if not math.isfinite(float(self.relation_alignment)) or not 0.0 <= float(self.relation_alignment) <= 1.0:
            raise OrchExecutorV27Error("relation_alignment must be in [0,1]")
        if not math.isfinite(float(self.contradiction_load)) or float(self.contradiction_load) < 0.0:
            raise OrchExecutorV27Error("contradiction_load must be non-negative")
        if not isinstance(self.potentials, Potentials):
            raise OrchExecutorV27Error("Potentials required")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": "PNCS_ORCH_EXECUTOR_COUPLING_CONFIG_V0_27",
            "contract_id": EXECUTOR_COUPLING_ID,
            "projection_policy_id": self.projection_policy.policy_id,
            "time_law_id": self.time_law.law_id,
            "reduction_law_id": self.reduction_law.law_id,
            "selection_law_id": self.selection_law.law_id,
            "bridge_policy_id": self.bridge_policy.policy_id,
            "gate_ids_by_step": [[i, self.gates_by_step[i].gate_id] for i in sorted(self.gates_by_step)],
            "relation_id": self.relation_id,
            "intent_id": self.intent_id,
            "relation_alignment": float(self.relation_alignment),
            "contradiction_load": float(self.contradiction_load),
            "potentials": self.potentials.payload,
            "previous_memory_state_id": self.previous_memory_state_id,
            "routing_authority": False,
            "effect_authority": False,
            "persistent_memory_write": False,
        }

    @property
    def config_id(self) -> str:
        return _typed_id("pncs:orch-executor-config", self.payload)


@dataclass(frozen=True)
class DirectCoupledTrace:
    program_content_id: str
    config_id: str
    initial_sigma_id: str
    final_sigma_id: str
    branch_truth_state: str
    base_steps: tuple[ExecutionStep, ...]
    initial_phase_id: str
    final_phase: PhaseFlowState36
    final_orch: OrchState
    transition_ids: tuple[str, ...]
    memory_residue_ids: tuple[str, ...]

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TRACE_SCHEMA,
            "contract_id": EXECUTOR_COUPLING_ID,
            "program_content_id": self.program_content_id,
            "config_id": self.config_id,
            "initial_sigma_id": self.initial_sigma_id,
            "final_sigma_id": self.final_sigma_id,
            "branch_truth_state": self.branch_truth_state,
            "base_steps": [step.payload for step in self.base_steps],
            "initial_phase_id": self.initial_phase_id,
            "final_phase_id": self.final_phase.state_id,
            "final_orch_state_id": self.final_orch.state_id,
            "transition_ids": list(self.transition_ids),
            "memory_residue_ids": list(self.memory_residue_ids),
            "v020_sigma_semantics_modified": False,
            "routing_authority_opened": False,
            "effect_authority_opened": False,
            "persistent_memory_write_performed": False,
            "external_effects": False,
            "laboratory_time_modified": False,
        }

    @property
    def trace_id(self) -> str:
        return _typed_id("pncs:orch-direct-trace", self.payload)


class OrchCoupledExecutor(_Executor):
    """v0.20 executor with an authority-neutral ORCHORBITAL/T^36 side-car.

    The base `_Executor._transition()` always executes first. ORCHORBITAL never
    changes Sigma, truth evaluation, selected route, or v0.20 operator steps in
    this gate. A side-car failure aborts the coupled execution fail-closed.
    """

    def __init__(
        self,
        program: BoundInternalProgram,
        live: LiveSurfaceSnapshot,
        phase_state: PhaseFlowState36,
        config: CouplingConfig,
    ) -> None:
        super().__init__(program, live)
        if not isinstance(phase_state, PhaseFlowState36):
            raise OrchExecutorV27Error("PhaseFlowState36 required")
        if not isinstance(config, CouplingConfig):
            raise OrchExecutorV27Error("CouplingConfig required")
        self.phase_state = phase_state
        self.initial_phase_id = phase_state.state_id
        self.config = config
        self.orch_state: OrchState | None = None
        self.orch_transitions: list[Transition] = []

    def _transition(self, state: SigmaState, operator_id: str, *, bindings: Mapping[str, object], **changes: object) -> SigmaState:
        after = super()._transition(state, operator_id, bindings=bindings, **changes)
        step = self.steps[-1]
        if after.semantic_mass != self.program.semantic_mass or state.semantic_mass != self.program.semantic_mass:
            raise OrchExecutorV27Error("Sigma semantic mass differs from bound program")
        vector = self.live.operator_vectors.get(operator_id)
        if vector is None:
            raise OrchExecutorV27Error("live operator vector disappeared after v0.20 transition")
        gate = self.config.gates_by_step.get(step.index)
        if gate is None:
            raise OrchExecutorV27Error(f"missing explicit hydrodynamic gate for v0.20 step {step.index}")
        orbital = _operator_projection(
            self.program.content_id,
            step,
            vector,
            self.config.projection_policy,
            self.program.semantic_mass,
        )
        self.orch_state = _append_occurrence(
            self.orch_state,
            orbital,
            program_content_id=self.program.content_id,
            relation_id=self.config.relation_id,
            intent_id=self.config.intent_id,
            policy=self.config.projection_policy,
            potentials=self.config.potentials,
            previous_memory_state_id=self.config.previous_memory_state_id,
        )
        try:
            coupled = orch_hydro_transition(
                self.phase_state,
                gate,
                vector,
                self.orch_state,
                orbital.mode_id,
                self.config.time_law,
                self.config.reduction_law,
                self.config.selection_law,
                self.config.bridge_policy,
                self.config.relation_alignment,
                self.config.contradiction_load,
            )
        except OrchHydroV27Error as exc:
            raise OrchExecutorV27Error("ORCHORBITAL/T^36 transition failed closed") from exc
        self.phase_state = coupled.after_phase
        self.orch_state = coupled.after_orch
        self.orch_transitions.append(coupled)
        return after

    def run_coupled(self, initial: SigmaState, admitted_target: str) -> DirectCoupledTrace:
        if self.steps or self.orch_transitions or self.orch_state is not None:
            raise OrchExecutorV27Error("OrchCoupledExecutor is single-run")
        initial_sigma_id = initial.state_id
        final_state, truth = super().run(initial, admitted_target)
        if self.orch_state is None or len(self.orch_transitions) != len(self.steps):
            raise OrchExecutorV27Error("ORCH side-car transition chain is incomplete")
        residues = tuple(t.memory_residue_id for t in self.orch_transitions if t.memory_residue_id is not None)
        return DirectCoupledTrace(
            self.program.content_id,
            self.config.config_id,
            initial_sigma_id,
            final_state.state_id,
            truth,
            tuple(self.steps),
            self.initial_phase_id,
            self.phase_state,
            self.orch_state,
            tuple(t.transition_id for t in self.orch_transitions),
            residues,
        )


@dataclass(frozen=True)
class ReceiptBoundDirectTrace:
    direct_trace: DirectCoupledTrace
    execution_receipt_sha256: str

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": BOUND_TRACE_SCHEMA,
            "contract_id": EXECUTOR_COUPLING_ID,
            "direct_trace_id": self.direct_trace.trace_id,
            "execution_receipt_sha256": self.execution_receipt_sha256,
            "program_content_id": self.direct_trace.program_content_id,
            "inverse_provenance": [
                {"level": "ORCH_DIRECT_TRACE", "id": self.direct_trace.trace_id},
                {"level": "V0_20_EXECUTION_RECEIPT", "sha256": self.execution_receipt_sha256},
                {"level": "PROGRAM_DEFINITION", "id": self.direct_trace.program_content_id},
            ],
            "v020_receipt_modified": False,
            "external_effects": False,
        }

    @property
    def bound_trace_id(self) -> str:
        return _typed_id("pncs:orch-receipt-bound-trace", self.payload)


def bind_direct_trace_to_receipt(
    trace: DirectCoupledTrace,
    receipt: Mapping[str, object],
) -> ReceiptBoundDirectTrace:
    if not isinstance(trace, DirectCoupledTrace):
        raise OrchExecutorV27Error("DirectCoupledTrace required")
    receipt_sha = validate_receipt(receipt)
    program = receipt.get("program")
    if not isinstance(program, Mapping) or program.get("content_id") != trace.program_content_id:
        raise OrchExecutorV27Error("receipt program differs from ORCH direct trace")
    if receipt.get("initial_sigma_id") != trace.initial_sigma_id or receipt.get("final_sigma_id") != trace.final_sigma_id:
        raise OrchExecutorV27Error("receipt Sigma endpoints differ from ORCH direct trace")
    admission = receipt.get("admission")
    if not isinstance(admission, Mapping) or admission.get("branch_truth_state") != trace.branch_truth_state:
        raise OrchExecutorV27Error("receipt truth state differs from ORCH direct trace")
    receipt_steps = receipt.get("steps")
    if not isinstance(receipt_steps, list) or len(receipt_steps) != len(trace.base_steps):
        raise OrchExecutorV27Error("receipt step count differs from ORCH direct trace")
    for raw, step in zip(receipt_steps, trace.base_steps):
        if not isinstance(raw, Mapping) or dict(raw) != step.payload:
            raise OrchExecutorV27Error("receipt KAKU occurrence differs from ORCH direct trace")
    return ReceiptBoundDirectTrace(trace, receipt_sha)
