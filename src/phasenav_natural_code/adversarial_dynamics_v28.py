from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .hydro_time_v27 import DIM, TAU, PhaseFlowState36, _typed_id
from .orch_hydro_v27 import OrchHydroOccurrence


ADVERSARIAL_DYNAMICS_CONTRACT_ID = "PNCS_ADVERSARIAL_DYNAMICS_V0_28"
DYNAMICS_WITNESS_SCHEMA = "PNCS_ADVERSARIAL_DYNAMICS_WITNESS_V0_28"


class AdversarialDynamicsV28Error(ValueError):
    pass


def _finite(value: object, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise AdversarialDynamicsV28Error(f"{field} must be finite") from exc
    if not math.isfinite(out):
        raise AdversarialDynamicsV28Error(f"{field} must be finite")
    return out


def _semantic_occurrence_projection(occurrence: OrchHydroOccurrence) -> tuple[object, ...]:
    if not isinstance(occurrence, OrchHydroOccurrence):
        raise AdversarialDynamicsV28Error("OrchHydroOccurrence required")
    return (
        occurrence.step_index,
        occurrence.operator_id,
        occurrence.operator_vector_sha256,
        occurrence.before_sigma_id,
        occurrence.after_sigma_id,
    )


def bounded_phase_noise(state: PhaseFlowState36, delta: Sequence[float]) -> PhaseFlowState36:
    """Apply explicit bounded T^36 phase noise without changing velocity or local proper time."""
    if not isinstance(state, PhaseFlowState36):
        raise AdversarialDynamicsV28Error("PhaseFlowState36 required")
    ds = tuple(_finite(value, "phase noise") for value in delta)
    if len(ds) != DIM:
        raise AdversarialDynamicsV28Error(f"phase noise must contain exactly {DIM} values")
    theta = tuple((state.theta[i] + ds[i]) % TAU for i in range(DIM))
    return PhaseFlowState36(theta, state.velocity, state.phase_proper_time)


def validate_orch_occurrence_dynamics(occurrence: OrchHydroOccurrence) -> str:
    """Fail closed on v0.27 ORCH/Hydro dynamic-state inconsistencies.

    The validator grants no routing or effect authority. It only checks that a
    produced occurrence remains inside the release-closed v0.27 dynamics and
    reduction/memory contracts.
    """
    if not isinstance(occurrence, OrchHydroOccurrence):
        raise AdversarialDynamicsV28Error("OrchHydroOccurrence required")

    coordinate_time = _finite(occurrence.coordinate_time, "coordinate_time")
    proper_time = _finite(occurrence.proper_time_advanced, "proper_time_advanced")
    if coordinate_time <= 0.0:
        raise AdversarialDynamicsV28Error("coordinate_time must be positive")
    if proper_time < 0.0:
        raise AdversarialDynamicsV28Error("proper_time_advanced must be non-negative")

    phase = occurrence.final_phase_state
    if len(phase.theta) != DIM or len(phase.velocity) != DIM:
        raise AdversarialDynamicsV28Error("final T^36 state must contain exactly 36 modes")
    for value in (*phase.theta, *phase.velocity, phase.phase_proper_time):
        _finite(value, "final phase state")
    if phase.phase_proper_time < 0.0:
        raise AdversarialDynamicsV28Error("phase proper time must be non-negative")

    orch = occurrence.final_orch_state
    if not isinstance(orch.program_content_id, str) or not orch.program_content_id:
        raise AdversarialDynamicsV28Error("ORCH program identity required")
    semantic_mass = _finite(orch.semantic_mass, "semantic_mass")
    if semantic_mass < 0.0:
        raise AdversarialDynamicsV28Error("semantic_mass must be non-negative")
    if len(orch.orbitals) != DIM:
        raise AdversarialDynamicsV28Error("ORCH state must contain exactly 36 orbitals")

    couplings = orch.couplings
    if len(couplings) != DIM or any(len(row) != DIM for row in couplings):
        raise AdversarialDynamicsV28Error("K_ij must be a 36x36 matrix")
    for i, row in enumerate(couplings):
        for j, raw in enumerate(row):
            value = _finite(raw, "K_ij")
            if value < 0.0 or value > 1.0:
                raise AdversarialDynamicsV28Error("K_ij must remain in [0,1]")
            if i == j and value != 0.0:
                raise AdversarialDynamicsV28Error("K_ij diagonal must be zero")
            if abs(value - float(couplings[j][i])) > 1e-12:
                raise AdversarialDynamicsV28Error("K_ij must remain symmetric")

    obs = orch.observables
    coherence = _finite(obs.global_coherence, "coherence")
    defect = _finite(obs.defect, "defect")
    if coherence < 0.0 or coherence > 1.0 or defect < 0.0 or defect > 1.0:
        raise AdversarialDynamicsV28Error("coherence/defect outside [0,1]")
    if abs(defect - (1.0 - coherence)) > 1e-12:
        raise AdversarialDynamicsV28Error("defect must equal 1-coherence")
    for value in (obs.holonomic_defect_real, obs.holonomic_defect_imag, obs.relational_decoherence):
        _finite(value, "ORCH observable")

    decision = occurrence.reduction
    if decision.state_id != orch.state_id:
        raise AdversarialDynamicsV28Error("reduction decision/state mismatch")
    omega = _finite(decision.omega, "Omega")
    expected_omega = decision.kernel.omega(
        coherence=coherence,
        relation_alignment=decision.relation_alignment,
        defect=defect,
        xi=decision.xi,
    )
    if abs(omega - expected_omega) > 1e-12:
        raise AdversarialDynamicsV28Error("Omega does not match reduction kernel")
    expected_ready = omega >= decision.kernel.omega_crit
    if decision.reduce_ready is not expected_ready:
        raise AdversarialDynamicsV28Error("false reduction readiness")

    selected = decision.selected_orbital_index
    if selected is not None:
        if isinstance(selected, bool) or not isinstance(selected, int) or selected < 0 or selected >= DIM:
            raise AdversarialDynamicsV28Error("selected orbital index invalid")
        if not decision.reduce_ready:
            raise AdversarialDynamicsV28Error("selection before reduction threshold")

    residue = occurrence.memory_residue
    if not decision.reduce_ready or selected is None:
        if residue is not None:
            raise AdversarialDynamicsV28Error("memory residue without explicit reduction selection")
    else:
        if residue is None:
            raise AdversarialDynamicsV28Error("selected reduction is missing memory residue")
        if residue.reduction_decision_id != decision.decision_id:
            raise AdversarialDynamicsV28Error("memory residue/reduction identity mismatch")
        if residue.selected_orbital_id != orch.orbitals[selected].mode_id:
            raise AdversarialDynamicsV28Error("memory residue selected-orbital mismatch")
        if residue.program_content_id != orch.program_content_id:
            raise AdversarialDynamicsV28Error("memory residue program mismatch")
        if not isinstance(residue.identity_input_id, str) or not residue.identity_input_id:
            raise AdversarialDynamicsV28Error("memory residue identity input required")
        if residue.payload.get("external_effects") is not False:
            raise AdversarialDynamicsV28Error("memory residue opened external effects")

    payload = occurrence.payload
    if payload.get("reduction_ready") is not decision.reduce_ready:
        raise AdversarialDynamicsV28Error("occurrence reduction flag mismatch")
    expected_residue_id = None if residue is None else residue.residue_id
    if payload.get("memory_residue_id") != expected_residue_id:
        raise AdversarialDynamicsV28Error("occurrence residue identity mismatch")
    if payload.get("stable_memory_update") is not (residue is not None):
        raise AdversarialDynamicsV28Error("occurrence memory-update flag mismatch")
    if payload.get("semantic_identity_modified") is not False:
        raise AdversarialDynamicsV28Error("dynamics modified semantic identity")
    if payload.get("external_effects") is not False:
        raise AdversarialDynamicsV28Error("dynamics opened external effects")

    return occurrence.occurrence_id


@dataclass(frozen=True)
class DynamicsInvariantWitness:
    reference_occurrence_id: str
    candidate_occurrence_id: str
    semantic_projection: tuple[object, ...]
    substrate_changed: bool

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": DYNAMICS_WITNESS_SCHEMA,
            "contract_id": ADVERSARIAL_DYNAMICS_CONTRACT_ID,
            "reference_occurrence_id": self.reference_occurrence_id,
            "candidate_occurrence_id": self.candidate_occurrence_id,
            "semantic_projection": list(self.semantic_projection),
            "substrate_changed": self.substrate_changed,
            "semantic_identity_modified": False,
            "routing_feedback_opened": False,
            "external_effects": False,
        }

    @property
    def witness_id(self) -> str:
        return _typed_id("pncs:adversarial-dynamics-witness", self.payload)


def assert_semantic_occurrence_equivalence(
    reference: OrchHydroOccurrence,
    candidate: OrchHydroOccurrence,
) -> DynamicsInvariantWitness:
    reference_id = validate_orch_occurrence_dynamics(reference)
    candidate_id = validate_orch_occurrence_dynamics(candidate)
    reference_semantic = _semantic_occurrence_projection(reference)
    candidate_semantic = _semantic_occurrence_projection(candidate)
    if candidate_semantic != reference_semantic:
        raise AdversarialDynamicsV28Error("substrate perturbation changed semantic occurrence authority")
    substrate_changed = (
        reference.final_phase_state.state_id != candidate.final_phase_state.state_id
        or reference.final_orch_state.state_id != candidate.final_orch_state.state_id
        or reference.proper_time_advanced != candidate.proper_time_advanced
    )
    return DynamicsInvariantWitness(reference_id, candidate_id, reference_semantic, substrate_changed)
