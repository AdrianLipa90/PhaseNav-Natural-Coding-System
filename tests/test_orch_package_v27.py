from __future__ import annotations

import math

import pytest

from phasenav_natural_code import execution_orch_v27 as execution
from phasenav_natural_code import hydro_time_v27 as hydro
from phasenav_natural_code import orch_hydro_v27 as orch_hydro
from phasenav_natural_code import orch_orbital_v27 as orch

ZERO = (0.0,) * 36
ATTRS = (
    orch.AttractorReport("AttractorEC", 0.75, ZERO, 0.5, "PACKAGE_EC"),
    orch.AttractorReport("AttractorZS", 0.80, ZERO, 0.5, "PACKAGE_ZS"),
    orch.AttractorReport("AttractorLLMTemp", 0.0, ZERO, 0.0, "DISABLED"),
)
POTENTIAL = orch.TotalPotential(0, 0, 0, 0, 0, 0)


def test_package_facades_import():
    assert orch.ORCHORBITAL_CONTRACT_ID == "PNCS_ORCHORBITAL_BINDING_V0_27"
    assert orch_hydro.ORCH_HYDRO_CONTRACT_ID == "PNCS_ORCHORBITAL_HYDRO_TRANSITION_V0_27"
    assert execution.COUPLED_EXECUTION_CONTRACT_ID == "PNCS_ORCHORBITAL_COUPLED_EXECUTION_V0_27"


def test_exact_phase_flow_schema_binds_across_module_boundary():
    state = hydro.PhaseFlowState36(tuple((i + 1) * 0.1 % (2 * math.pi) for i in range(36)))
    bound = orch.bind_t36_state(
        state,
        tick=0,
        program_content_id="pncs:def:sha256:" + "1" * 64,
        semantic_mass=0.1,
        attractor_reports=ATTRS,
        potential=POTENTIAL,
    )
    assert len(bound.orbitals) == 36
    assert bound.payload["external_effects"] is False


def test_wrong_phase_flow_schema_fails_closed():
    class WrongState:
        theta = (0.0,) * 36
        velocity = (0.0,) * 36
        payload = {"schema": "WRONG"}

    with pytest.raises(orch.OrchOrbitalV27Error, match="schema mismatch"):
        orch.bind_t36_state(
            WrongState(),
            tick=0,
            program_content_id="pncs:def:sha256:" + "2" * 64,
            semantic_mass=0.1,
            attractor_reports=ATTRS,
            potential=POTENTIAL,
        )


def test_coupled_executor_uses_package_hydrodynamic_gate_class():
    assert execution.HydrodynamicPhaseGate is hydro.HydrodynamicPhaseGate
    gate = hydro.HydrodynamicPhaseGate(0.5, 0.2)
    assert isinstance(gate, execution.HydrodynamicPhaseGate)
