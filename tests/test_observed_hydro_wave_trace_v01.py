from __future__ import annotations

import math

import pytest

from phasenav_natural_code.hydro_time_v27 import (
    HydrodynamicPhaseGate,
    PhaseFlowState36,
    run_hydrodynamic_gate,
)
from phasenav_natural_code.observed_hydro_wave_trace_v01 import (
    FROZEN_POST_OBSERVATION,
    ObservedHydroWaveTraceError,
    bind_observed_hydro_wave_trace,
    observed_hydro_pair_transport_witness,
    observed_pair_profile,
    replay_observed_hydro_wave_trace,
)
from phasenav_natural_code.temporal_geometry_v02 import (
    TemporalWaveState36,
    gaussian_observation_now,
    project_observation_now,
)


DIM = 36
TIMES = tuple(float(i - 18) for i in range(DIM))
AMPLITUDES = tuple(
    complex(math.cos(i / 7.0), math.sin(i / 7.0))
    for i in range(DIM)
)
DRIVE = tuple(1.0 if i == 18 else 0.0 for i in range(DIM))


def observation(sigma: float = 1.0):
    state = TemporalWaveState36(
        TIMES,
        AMPLITUDES,
        now=0.0,
        scale=4.0,
    )
    return gaussian_observation_now(state, sigma)


def initial_phase_state(obs=None) -> PhaseFlowState36:
    obs = observation() if obs is None else obs
    return obs.after_state.projection.to_phase_flow_state36(
        phase_proper_time=0.0
    )


def gate(*, steps: int = 100) -> HydrodynamicPhaseGate:
    return HydrodynamicPhaseGate(
        density=1.0,
        effective_viscosity=0.0,
        drive_gain=0.05,
        coordinate_dt=0.01,
        steps=steps,
    )


def stack(*, sigma: float = 1.0, steps: int = 100):
    obs = observation(sigma)
    initial = initial_phase_state(obs)
    trace = run_hydrodynamic_gate(initial, gate(steps=steps), DRIVE)
    return obs, initial, trace


def test_binding_accepts_exact_source_component_composition():
    obs, initial, trace = stack()
    bound = bind_observed_hydro_wave_trace(obs, initial, trace, DRIVE)

    payload = bound.payload
    assert payload["observation_receipt_id"] == obs.receipt_id
    assert payload["observed_after_state_id"] == obs.after_state.state_id
    assert payload["temporal_projection_id"] == obs.after_state.projection.projection_id
    assert payload["initial_phase_state_id"] == initial.state_id
    assert payload["hydro_trace_id"] == trace.trace_id
    assert payload["hydro_step_ids"] == list(trace.step_ids)
    assert payload["amplitude_policy"] == FROZEN_POST_OBSERVATION
    assert payload["basis_binding_mode"] == "EXACT_INITIAL_THETA_EQUALITY"
    assert payload["runtime_execution_authority"] is False
    assert payload["canon_write_authority"] is False
    assert payload["state_memory_write_authority"] is False


def test_binding_is_deterministic():
    obs, initial, trace = stack()
    a = bind_observed_hydro_wave_trace(obs, initial, trace, DRIVE)
    b = bind_observed_hydro_wave_trace(obs, initial, trace, DRIVE)
    assert a.receipt_sha256 == b.receipt_sha256
    assert a.payload == b.payload


def test_replay_returns_full_ordered_phase_state_sequence():
    obs, initial, trace = stack(steps=12)
    replay = replay_observed_hydro_wave_trace(obs, initial, trace, DRIVE)
    assert len(replay.phase_states) == 13
    assert replay.phase_states[0].state_id == initial.state_id
    assert replay.phase_states[-1].state_id == trace.final_state.state_id
    assert replay.binding.hydro_trace_id == trace.trace_id


def test_native_pair_transport_witness_is_nonabelian_without_qhtri_graph_hamiltonian():
    obs, initial, trace = stack(steps=100)
    replay = replay_observed_hydro_wave_trace(obs, initial, trace, DRIVE)
    witness = observed_hydro_pair_transport_witness(obs, replay, 9, 50, 100)

    assert witness.imbalance_u == pytest.approx(math.tanh(0.25), abs=2e-15)
    assert witness.left_delta == pytest.approx(-0.4963329771385685)
    assert witness.right_delta == pytest.approx(-0.5152177486710774)
    assert witness.left_delta_dot == pytest.approx(-0.025005054316652828)
    assert witness.right_delta_dot == pytest.approx(-0.05004108365853668)
    assert witness.cross_norm == pytest.approx(5.440204449331002e-06, rel=1e-12)
    assert witness.nonabelian
    assert witness.payload["qhtri_graph_hamiltonian_used"] is False


def test_pair_transport_witness_rejects_observation_not_bound_to_replay():
    obs, initial, trace = stack(steps=100)
    replay = replay_observed_hydro_wave_trace(obs, initial, trace, DRIVE)
    other = observation(sigma=0.75)

    with pytest.raises(ObservedHydroWaveTraceError, match="observation/replay"):
        observed_hydro_pair_transport_witness(other, replay, 9, 50, 100)


def test_pair_transport_witness_requires_ordered_distinct_sections():
    obs, initial, trace = stack(steps=100)
    replay = replay_observed_hydro_wave_trace(obs, initial, trace, DRIVE)

    with pytest.raises(ObservedHydroWaveTraceError, match="greater"):
        observed_hydro_pair_transport_witness(obs, replay, 9, 100, 50)


def test_pair_profile_matches_gaussian_source_imbalance():
    obs = observation()
    profile = observed_pair_profile(obs, 9)

    assert profile.left_index == 18
    assert profile.right_index == 19
    assert profile.pair_support > 0.0
    assert profile.imbalance_u == pytest.approx(math.tanh(0.25), abs=2e-15)


def test_zero_support_pair_fails_closed():
    state = TemporalWaveState36(
        TIMES,
        AMPLITUDES,
        now=0.0,
        scale=4.0,
    )
    exact = project_observation_now(state)
    with pytest.raises(ObservedHydroWaveTraceError, match="zero/non-finite support"):
        observed_pair_profile(exact, 0)


def test_wrong_drive_fails_replay_lineage():
    obs, initial, trace = stack()
    wrong = tuple(1.0 if i == 19 else 0.0 for i in range(DIM))
    with pytest.raises(ObservedHydroWaveTraceError, match="step lineage"):
        bind_observed_hydro_wave_trace(obs, initial, trace, wrong)


def test_initial_theta_mismatch_fails_closed():
    obs, initial, trace = stack()
    theta = list(initial.theta)
    theta[0] = (theta[0] + 0.01) % (2.0 * math.pi)
    wrong_initial = PhaseFlowState36(
        theta,
        velocity=initial.velocity,
        phase_proper_time=initial.phase_proper_time,
    )
    with pytest.raises(ObservedHydroWaveTraceError, match="initial theta mismatch"):
        bind_observed_hydro_wave_trace(obs, wrong_initial, trace, DRIVE)


def test_initial_state_identity_mismatch_fails_closed():
    obs, initial, trace = stack()
    same_theta_different_time = PhaseFlowState36(
        initial.theta,
        velocity=initial.velocity,
        phase_proper_time=0.5,
    )
    with pytest.raises(ObservedHydroWaveTraceError, match="initial-state identity mismatch"):
        bind_observed_hydro_wave_trace(
            obs,
            same_theta_different_time,
            trace,
            DRIVE,
        )


def test_dynamic_or_unknown_amplitude_policy_is_rejected():
    obs, initial, trace = stack()
    with pytest.raises(ObservedHydroWaveTraceError, match="FROZEN_POST_OBSERVATION"):
        bind_observed_hydro_wave_trace(
            obs,
            initial,
            trace,
            DRIVE,
            amplitude_policy="EVOLVE_BY_ASSUMPTION",
        )


def test_observation_change_changes_binding_identity():
    obs_a, initial_a, trace_a = stack(sigma=1.0)
    obs_b, initial_b, trace_b = stack(sigma=0.75)

    # The temporal phase projection is unchanged because sigma only changes
    # observation amplitudes, but the observation/state identities differ.
    assert initial_a.state_id == initial_b.state_id
    assert trace_a.trace_id == trace_b.trace_id

    a = bind_observed_hydro_wave_trace(obs_a, initial_a, trace_a, DRIVE)
    b = bind_observed_hydro_wave_trace(obs_b, initial_b, trace_b, DRIVE)
    assert a.observed_after_state_id != b.observed_after_state_id
    assert a.observed_probabilities_sha256 != b.observed_probabilities_sha256
    assert a.receipt_sha256 != b.receipt_sha256


@pytest.mark.parametrize("bad_pair", [-1, 18, True, 1.5])
def test_pair_index_domain_is_strict(bad_pair):
    with pytest.raises(ObservedHydroWaveTraceError):
        observed_pair_profile(observation(), bad_pair)
