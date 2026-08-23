from __future__ import annotations

import math

import pytest

from phasenav_natural_code.hydro_time_v27 import HydrodynamicPhaseGate, PhaseFlowState36
from phasenav_natural_code.orch_hydro_v27 import OrchHydroControlProfile, run_orchestrated_occurrence
from phasenav_natural_code.orch_orbital_v27 import (
    ORCHORBITAL_FOUNDATION_COMMIT,
    ORCHORBITAL_FOUNDATION_PATHS,
    ORCHORBITAL_FOUNDATION_REPOSITORY,
    AttractorReport,
    OrchOrbitalV27Error,
    ReductionKernel,
    SubjectiveTimeKernel,
    TotalPotential,
    bind_subjective_time,
    bind_t36_state,
    decide_reduction,
    effective_attractor_weight,
    memory_residue_after_reduction,
    phase_proximity_couplings,
    winding_increment,
)

DIM = 36
THETA = tuple(0.05 * i for i in range(DIM))
STATE = PhaseFlowState36(THETA)
DRIVE = (1.0,) + tuple(0.1 for _ in range(DIM - 1))
ZERO = tuple(0.0 for _ in range(DIM))
PROGRAM_ID = "pncs:def:sha256:" + "d" * 64
SEMANTIC_MASS = 0.2
BEFORE_SIGMA = "pncs:sigma:sha256:" + "a" * 64
AFTER_SIGMA = "pncs:sigma:sha256:" + "b" * 64
VECTOR_SHA = "c" * 64

ATTRACTORS = (
    AttractorReport("AttractorEC", 0.75, ZERO, 0.5, "PURE_EC"),
    AttractorReport("AttractorZS", 0.80, ZERO, 0.5, "PURE_ZS"),
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


def _orch_state():
    return bind_t36_state(
        STATE,
        tick=0,
        program_content_id=PROGRAM_ID,
        semantic_mass=SEMANTIC_MASS,
        attractor_reports=ATTRACTORS,
        potential=POTENTIAL,
    )


def _occurrence(*, profile=PROFILE, gate=GATE):
    return run_orchestrated_occurrence(
        STATE,
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
        identity_input_id="pure-v0.27",
    )


def test_foundation_repo_and_commit_bound():
    assert ORCHORBITAL_FOUNDATION_REPOSITORY == "AdrianLipa90/CIEL-Omega-ApokalypOS"
    assert ORCHORBITAL_FOUNDATION_COMMIT == "aa0da54ef29a1f80dd0390427935342225388950"
    assert len(ORCHORBITAL_FOUNDATION_PATHS) == 6


def test_t36_binding_has_exactly_36_orbitals():
    assert len(_orch_state().orbitals) == DIM


def test_sphere_declares_required_fields():
    payload = _orch_state().sphere.payload
    for key in ("sphere_id", "parent_sphere_id", "child_sphere_ids", "internal_modes", "leak_mode", "effective_attractor_weight"):
        assert key in payload


def test_projective_kahler_anchor_preserved():
    payload = _orch_state().sphere.payload
    assert "Kahler" in payload["geometric_anchor"]
    assert payload["bloch_chart_role"] == "LOCAL_REDUCED_CHART_ONLY"


def test_global_coherence_and_defect_bounds():
    observables = _orch_state().observables
    assert 0.0 <= observables.global_coherence <= 1.0
    assert 0.0 <= observables.defect <= 1.0
    assert observables.defect == pytest.approx(1.0 - observables.global_coherence)


def test_phase_proximity_coupling_is_symmetric_zero_diagonal():
    matrix = _orch_state().couplings
    for i in range(DIM):
        assert matrix[i][i] == 0.0
        for j in range(DIM):
            assert matrix[i][j] == pytest.approx(matrix[j][i])


def test_phase_proximity_exact_endpoints():
    same = phase_proximity_couplings((0.0, 0.0), scale=0.3)
    opposite = phase_proximity_couplings((0.0, math.pi), scale=0.3)
    assert same[0][1] == pytest.approx(0.3)
    assert opposite[0][1] == pytest.approx(0.0)


def test_total_potential_exact_sum():
    potential = TotalPotential(1, 2, 3, 4, 5, 6)
    assert potential.total == 21
    assert potential.payload["contract_expression"] == "V_tot=V_EC+V_ZS+V_rel+V_mem+V_def+V_ext"


def test_attractor_effective_weight_explicit():
    assert effective_attractor_weight(ATTRACTORS) == pytest.approx(0.775)


def test_subjective_time_kernel_deterministic_and_un_calibrated():
    args = dict(radius=1.0, coherence=0.8, defect=0.2, semantic_mass=0.04, attractor_influence=0.7)
    assert TIME_KERNEL.evaluate(**args) == TIME_KERNEL.evaluate(**args)
    assert TIME_KERNEL.payload["physical_calibration_claimed"] is False


def test_subjective_time_binding_formula_and_boundary():
    binding = bind_subjective_time(_orch_state(), TIME_KERNEL, orbital_radius=1.0, substrate_lapse=0.5, coordinate_dt=0.02)
    assert binding.proper_dt == pytest.approx(0.02 * binding.combined_g)
    assert binding.payload["laboratory_time_modified"] is False


def test_winding_formula_exact():
    assert winding_increment(math.pi, 0.2, 0.1) == pytest.approx(1.0)


def test_no_selection_before_threshold():
    with pytest.raises(OrchOrbitalV27Error, match="before reduction"):
        decide_reduction(_orch_state(), REDUCE_NEVER, relation_alignment=1.0, xi=0.0, selected_orbital_index=0)


def test_no_reduction_no_memory_update():
    state = _orch_state()
    decision = decide_reduction(state, REDUCE_NEVER, relation_alignment=1.0, xi=0.0)
    assert decision.reduce_ready is False
    assert memory_residue_after_reduction(state, decision, identity_input_id="pure") is None


def test_reduction_with_explicit_selection_yields_residue():
    state = _orch_state()
    kernel = ReductionKernel(1.0, 1.0, 0.0, 0.0, -1.0)
    decision = decide_reduction(state, kernel, relation_alignment=1.0, xi=0.0, selected_orbital_index=0)
    residue = memory_residue_after_reduction(state, decision, identity_input_id="pure")
    assert decision.reduce_ready is True
    assert residue is not None
    assert residue.payload["memory_semantics"] == "REDUCTION_RESIDUE_NOT_RAW_INPUT_STORAGE"


def test_orchestrated_occurrence_changes_only_substrate_sidecar():
    occurrence = _occurrence()
    assert occurrence.final_phase_state.state_id != STATE.state_id
    assert occurrence.before_sigma_id == BEFORE_SIGMA
    assert occurrence.after_sigma_id == AFTER_SIGMA
    assert occurrence.payload["semantic_identity_modified"] is False
    assert occurrence.payload["external_effects"] is False


def test_orchestrated_occurrence_binds_winding_and_no_residue_without_reduction():
    occurrence = _occurrence()
    assert occurrence.proper_time_advanced > 0.0
    assert occurrence.reduction.reduce_ready is False
    assert occurrence.memory_residue is None


def test_different_explicit_time_kernels_change_tau_not_semantic_occurrence():
    slow = SubjectiveTimeKernel(beta_coherence=-1.0, beta_defect=1.0)
    fast = SubjectiveTimeKernel(beta_coherence=1.0, beta_defect=-1.0)
    slow_profile = OrchHydroControlProfile(slow, 1.0, ATTRACTORS, POTENTIAL, REDUCE_NEVER, 1.0, 0.0)
    fast_profile = OrchHydroControlProfile(fast, 1.0, ATTRACTORS, POTENTIAL, REDUCE_NEVER, 1.0, 0.0)
    a = _occurrence(profile=slow_profile)
    b = _occurrence(profile=fast_profile)
    assert a.proper_time_advanced != b.proper_time_advanced
    assert (a.operator_id, a.before_sigma_id, a.after_sigma_id) == (b.operator_id, b.before_sigma_id, b.after_sigma_id)
