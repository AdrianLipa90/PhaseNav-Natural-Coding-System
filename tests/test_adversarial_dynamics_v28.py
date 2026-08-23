from __future__ import annotations

from dataclasses import replace
import math

import pytest

from phasenav_natural_code.adversarial_dynamics_v28 import (
    AdversarialDynamicsV28Error,
    assert_semantic_occurrence_equivalence,
    bounded_phase_noise,
    validate_orch_occurrence_dynamics,
)
from phasenav_natural_code.hydro_time_v27 import (
    HydrodynamicPhaseGate,
    HydrodynamicProperTimeV27Error,
    PhaseFlowState36,
)
from phasenav_natural_code.orch_hydro_v27 import (
    OrchHydroControlProfile,
    OrchHydroV27Error,
    run_orchestrated_occurrence,
)
from phasenav_natural_code.orch_orbital_v27 import (
    AttractorReport,
    MemoryResidue,
    OrchOrbitalState,
    OrchOrbitalV27Error,
    ReductionKernel,
    SubjectiveTimeKernel,
    TotalPotential,
)

DIM = 36
THETA = tuple(0.05 * i for i in range(DIM))
STATE = PhaseFlowState36(THETA)
DRIVE = (1.0,) + tuple(0.1 for _ in range(DIM - 1))
ZERO = tuple(0.0 for _ in range(DIM))
BEFORE_SIGMA = "pncs:sigma:sha256:" + "a" * 64
AFTER_SIGMA = "pncs:sigma:sha256:" + "b" * 64
VECTOR_SHA = "c" * 64
PROGRAM_ID = "pncs:def:sha256:" + "d" * 64
SEMANTIC_MASS = 0.2

ATTRACTORS = (
    AttractorReport("AttractorEC", 0.75, ZERO, 0.5, "V028_EC"),
    AttractorReport("AttractorZS", 0.80, ZERO, 0.5, "V028_ZS"),
    AttractorReport("AttractorLLMTemp", 0.0, ZERO, 0.0, "DISABLED"),
)
POTENTIAL = TotalPotential(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
TIME_KERNEL = SubjectiveTimeKernel(
    beta_radius=-0.1,
    beta_coherence=0.4,
    beta_defect=-0.4,
    beta_mass=-0.2,
    beta_attractor=0.2,
)
REDUCE_NEVER = ReductionKernel(1.0, 1.0, 1.0, 1.0, 10.0)
REDUCE_ALWAYS = ReductionKernel(1.0, 1.0, 0.0, 0.0, -1.0)
PROFILE = OrchHydroControlProfile(
    TIME_KERNEL,
    1.0,
    ATTRACTORS,
    POTENTIAL,
    REDUCE_NEVER,
    1.0,
    0.0,
    coupling_scale=0.15,
    coupling_gain=0.05,
    attractor_force_gain=1.0,
)
GATE = HydrodynamicPhaseGate(0.5, 0.2, steps=2, coordinate_dt=0.01)


def _profile(*, reduction=REDUCE_NEVER, selected=None, coupling_scale=0.15, time_kernel=TIME_KERNEL):
    return OrchHydroControlProfile(
        time_kernel,
        1.0,
        ATTRACTORS,
        POTENTIAL,
        reduction,
        1.0,
        0.0,
        selected_orbital_index=selected,
        coupling_scale=coupling_scale,
        coupling_gain=0.05,
        attractor_force_gain=1.0,
    )


def _occurrence(*, gate=GATE, profile=PROFILE, state=STATE):
    return run_orchestrated_occurrence(
        state,
        gate,
        DRIVE,
        occurrence_step_index=1,
        operator_id="DIFFERENCE",
        operator_vector_sha256=VECTOR_SHA,
        before_sigma_id=BEFORE_SIGMA,
        after_sigma_id=AFTER_SIGMA,
        tick_start=0,
        program_content_id=PROGRAM_ID,
        semantic_mass=SEMANTIC_MASS,
        profile=profile,
        identity_input_id="v0.28-adversarial-dynamics",
    )


def test_baseline_occurrence_passes_dynamic_validator():
    occurrence = _occurrence()
    assert validate_orch_occurrence_dynamics(occurrence) == occurrence.occurrence_id


def test_density_perturbation_changes_substrate_not_semantic_authority():
    reference = _occurrence()
    candidate = _occurrence(gate=HydrodynamicPhaseGate(0.8, 0.2, steps=2, coordinate_dt=0.01))
    witness = assert_semantic_occurrence_equivalence(reference, candidate)
    assert witness.substrate_changed is True
    assert witness.payload["semantic_identity_modified"] is False


def test_viscosity_perturbation_changes_substrate_not_semantic_authority():
    reference = _occurrence()
    candidate = _occurrence(gate=HydrodynamicPhaseGate(0.5, 0.7, steps=2, coordinate_dt=0.01))
    witness = assert_semantic_occurrence_equivalence(reference, candidate)
    assert witness.substrate_changed is True


def test_coupling_scale_perturbation_changes_kij_not_semantic_authority():
    reference = _occurrence()
    candidate = _occurrence(profile=_profile(coupling_scale=0.35))
    witness = assert_semantic_occurrence_equivalence(reference, candidate)
    assert witness.substrate_changed is True
    assert reference.final_orch_state.couplings != candidate.final_orch_state.couplings


def test_bounded_phase_noise_changes_substrate_not_semantic_authority():
    noisy = bounded_phase_noise(STATE, tuple(0.001 if i % 2 == 0 else -0.001 for i in range(DIM)))
    reference = _occurrence()
    candidate = _occurrence(state=noisy)
    witness = assert_semantic_occurrence_equivalence(reference, candidate)
    assert witness.substrate_changed is True


def test_nonfinite_phase_noise_rejected():
    delta = list(0.0 for _ in range(DIM))
    delta[3] = float("nan")
    with pytest.raises(AdversarialDynamicsV28Error, match="phase noise"):
        bounded_phase_noise(STATE, delta)


def test_wrong_phase_noise_dimension_rejected():
    with pytest.raises(AdversarialDynamicsV28Error, match="exactly 36"):
        bounded_phase_noise(STATE, (0.0,) * 35)


def test_negative_density_rejected_fail_closed():
    with pytest.raises(HydrodynamicProperTimeV27Error, match="density"):
        HydrodynamicPhaseGate(-0.1, 0.2)


def test_negative_effective_viscosity_rejected_fail_closed():
    with pytest.raises(HydrodynamicProperTimeV27Error, match="viscosity"):
        HydrodynamicPhaseGate(0.5, -0.1)


def test_nonfinite_phase_state_rejected_fail_closed():
    theta = list(THETA)
    theta[0] = float("inf")
    with pytest.raises(HydrodynamicProperTimeV27Error):
        PhaseFlowState36(theta)


def test_negative_local_proper_time_rejected_fail_closed():
    with pytest.raises(HydrodynamicProperTimeV27Error, match="non-negative"):
        PhaseFlowState36(THETA, phase_proper_time=-0.01)


def test_nonfinite_subjective_time_kernel_rejected_fail_closed():
    with pytest.raises((HydrodynamicProperTimeV27Error, OrchOrbitalV27Error)):
        SubjectiveTimeKernel(beta_coherence=float("nan"))


def test_excessive_speed_transition_rejected():
    fast_state = PhaseFlowState36(THETA, velocity=(1.0,) * DIM)
    strict_gate = HydrodynamicPhaseGate(0.5, 0.0, steps=1, coordinate_dt=0.01, max_speed=0.01)
    with pytest.raises(OrchHydroV27Error, match="max_speed"):
        _occurrence(gate=strict_gate, state=fast_state)


def test_asymmetric_kij_injection_rejected():
    state = _occurrence().final_orch_state
    matrix = [list(row) for row in state.couplings]
    matrix[0][1] = min(1.0, matrix[0][1] + 0.1)
    with pytest.raises(OrchOrbitalV27Error, match="symmetric"):
        OrchOrbitalState(
            state.tick,
            state.program_content_id,
            state.semantic_mass,
            state.sphere,
            state.orbitals,
            tuple(tuple(row) for row in matrix),
            state.observables,
            state.attractor_reports,
            state.potential,
        )


def test_nonfinite_kij_injection_rejected():
    state = _occurrence().final_orch_state
    matrix = [list(row) for row in state.couplings]
    matrix[0][1] = float("nan")
    matrix[1][0] = float("nan")
    with pytest.raises((HydrodynamicProperTimeV27Error, OrchOrbitalV27Error)):
        OrchOrbitalState(
            state.tick,
            state.program_content_id,
            state.semantic_mass,
            state.sphere,
            state.orbitals,
            tuple(tuple(row) for row in matrix),
            state.observables,
            state.attractor_reports,
            state.potential,
        )


def test_coupling_scale_out_of_bounds_rejected():
    with pytest.raises((OrchHydroV27Error, OrchOrbitalV27Error)):
        _profile(coupling_scale=1.1)


def test_no_reduction_means_no_residue():
    occurrence = _occurrence()
    assert occurrence.reduction.reduce_ready is False
    assert occurrence.memory_residue is None
    validate_orch_occurrence_dynamics(occurrence)


def test_reduction_ready_without_selection_still_has_no_residue():
    occurrence = _occurrence(profile=_profile(reduction=REDUCE_ALWAYS))
    assert occurrence.reduction.reduce_ready is True
    assert occurrence.reduction.selected_orbital_index is None
    assert occurrence.memory_residue is None
    validate_orch_occurrence_dynamics(occurrence)


def test_selection_before_reduction_threshold_rejected():
    with pytest.raises(OrchOrbitalV27Error, match="before reduction"):
        _occurrence(profile=_profile(reduction=REDUCE_NEVER, selected=0))


def test_explicit_reduction_selection_yields_valid_residue():
    occurrence = _occurrence(profile=_profile(reduction=REDUCE_ALWAYS, selected=0))
    assert occurrence.reduction.reduce_ready is True
    assert occurrence.memory_residue is not None
    validate_orch_occurrence_dynamics(occurrence)


def test_false_reduction_flag_injection_rejected():
    base = _occurrence()
    forged_decision = replace(base.reduction, reduce_ready=True)
    forged = replace(base, reduction=forged_decision)
    with pytest.raises(AdversarialDynamicsV28Error, match="false reduction"):
        validate_orch_occurrence_dynamics(forged)


def test_residue_injection_without_reduction_rejected():
    base = _occurrence()
    forged_residue = MemoryResidue(
        "pncs:orch-reduction:sha256:" + "0" * 64,
        None,
        base.final_orch_state.orbitals[0].mode_id,
        PROGRAM_ID,
        "forged",
    )
    forged = replace(base, memory_residue=forged_residue)
    with pytest.raises(AdversarialDynamicsV28Error, match="without explicit reduction"):
        validate_orch_occurrence_dynamics(forged)


def test_residue_selected_orbital_substitution_rejected():
    base = _occurrence(profile=_profile(reduction=REDUCE_ALWAYS, selected=0))
    assert base.memory_residue is not None
    forged_residue = replace(base.memory_residue, selected_orbital_id=base.final_orch_state.orbitals[1].mode_id)
    forged = replace(base, memory_residue=forged_residue)
    with pytest.raises(AdversarialDynamicsV28Error, match="selected-orbital"):
        validate_orch_occurrence_dynamics(forged)


def test_operator_substitution_breaks_semantic_equivalence():
    reference = _occurrence()
    candidate = replace(reference, operator_id="ORDER")
    with pytest.raises(AdversarialDynamicsV28Error, match="semantic occurrence authority"):
        assert_semantic_occurrence_equivalence(reference, candidate)


def test_operator_vector_substitution_breaks_semantic_equivalence():
    reference = _occurrence()
    candidate = replace(reference, operator_vector_sha256="0" * 64)
    with pytest.raises(AdversarialDynamicsV28Error, match="semantic occurrence authority"):
        assert_semantic_occurrence_equivalence(reference, candidate)


def test_sigma_endpoint_substitution_breaks_semantic_equivalence():
    reference = _occurrence()
    candidate = replace(reference, after_sigma_id="pncs:sigma:sha256:" + "0" * 64)
    with pytest.raises(AdversarialDynamicsV28Error, match="semantic occurrence authority"):
        assert_semantic_occurrence_equivalence(reference, candidate)


def test_different_time_kernel_changes_tau_not_semantic_authority():
    reference = _occurrence()
    faster = SubjectiveTimeKernel(beta_coherence=1.0, beta_defect=-1.0)
    candidate = _occurrence(profile=_profile(time_kernel=faster))
    witness = assert_semantic_occurrence_equivalence(reference, candidate)
    assert witness.substrate_changed is True
    assert reference.proper_time_advanced != candidate.proper_time_advanced


def test_witness_is_deterministic_and_keeps_authority_closed():
    reference = _occurrence()
    candidate = _occurrence(gate=HydrodynamicPhaseGate(0.7, 0.2, steps=2, coordinate_dt=0.01))
    a = assert_semantic_occurrence_equivalence(reference, candidate)
    b = assert_semantic_occurrence_equivalence(reference, candidate)
    assert a.witness_id == b.witness_id
    assert a.payload["routing_feedback_opened"] is False
    assert a.payload["external_effects"] is False
