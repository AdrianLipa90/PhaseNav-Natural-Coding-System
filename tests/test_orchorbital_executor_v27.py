import hashlib
import json

import pytest

from phasenav_natural_code.execution_v20_live import LiveSurfaceSnapshot
from phasenav_natural_code.execution_v20_model import (
    EXECUTABLE_INTERNAL_OPERATORS,
    EXECUTION_CONTRACT_ID,
    RECEIPT_SCHEMA,
    BoundInternalProgram,
    _sha256_json,
    definition_content_id,
    expected_leaf_path,
)
from phasenav_natural_code.execution_v20_state import SigmaState, _Executor
from phasenav_natural_code.hydro_time_v27 import HydrodynamicPhaseGate, PhaseFlowState36
from phasenav_natural_code.orchorbital_executor_v27 import (
    CouplingConfig,
    OrchCoupledExecutor,
    OrchExecutorV27Error,
    bind_direct_trace_to_receipt,
)
from phasenav_natural_code.orchorbital_hydro_v27 import BridgePolicy, ProjectionPolicy
from phasenav_natural_code.orchorbital_v27 import (
    AttractorWeights,
    Potentials,
    ReductionLaw,
    SelectionLaw,
    TimeLaw,
)


def _graph():
    return (
        "branch",
        (
            "or",
            ("comparison", "memory_pressure", "gt", 0.9),
            ("comparison", "risk", "gt", 0.8),
        ),
        "safety.pause",
        "runtime.continue",
    )


def _program():
    graph = _graph()
    leaf = expected_leaf_path(graph)
    cid = definition_content_id(graph, leaf)
    return BoundInternalProgram(
        cid,
        graph,
        leaf,
        "pncs:realization36:sha256:" + "1" * 64,
        "pncs:binding36:sha256:" + "2" * 64,
        "pncs:mass-binding:sha256:" + "3" * 64,
        "4" * 64,
        0.2,
    )


def _vectors():
    out = {}
    for n, op in enumerate(sorted(EXECUTABLE_INTERNAL_OPERATORS), start=1):
        out[op] = tuple(0.01 * (i + 1) + 0.03 * n for i in range(36))
    return out


def _live():
    return LiveSurfaceSnapshot(
        root="/dev/shm/ciel_noema",
        phi_sha256="a" * 64,
        aux_phi_sha256="b" * 64,
        aux_feedback_phi_sha256="c" * 64,
        operator_registry_sha256="d" * 64,
        tether_receipt_sha256="e" * 64,
        operator_vectors=_vectors(),
    )


def _initial(program):
    return SigmaState(
        content_id=program.content_id,
        realization_id=program.realization_id,
        mass_binding_id=program.mass_binding_id,
        phase36_sha256=program.phase36_sha256,
        semantic_mass=program.semantic_mass,
        surface_phi_sha256="a" * 64,
        input_values=(("memory_pressure", 0.0), ("risk", 0.0)),
        control_location="pncs.entry",
    )


def _config(step_count=9):
    return CouplingConfig(
        ProjectionPolicy(
            adjacency_coupling=0.4,
            memory_affinity=0.2,
            orbital_radius=1.0,
            attractor_influence=0.7,
            attractor_weights=AttractorWeights(0.6, 0.4, 0.0),
            amplitude_scale=1.0,
            sphere_attractor_weight=1.2,
            leak_mode="parent_embedding",
        ),
        TimeLaw(1.0, 0.0, 0.1, -0.05, 0.0, 0.1, 0.25, 2.0),
        ReductionLaw(1.0, 0.5, 0.5, 0.2, 999.0),
        SelectionLaw(0.1, 0.5, 0.2, 0.1, 0.0, 0.2),
        BridgePolicy(0.01, 8.0),
        {i: HydrodynamicPhaseGate(1.0, 0.1, coordinate_dt=0.01) for i in range(1, step_count + 1)},
        "pncs.test.relation",
        "pncs.test.intent",
        0.8,
        0.1,
        Potentials(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    )


def _phase():
    return PhaseFlowState36(tuple(0.01 * i for i in range(36)))


def _run_pair():
    program = _program()
    live = _live()
    initial = _initial(program)
    base = _Executor(program, live)
    base_final, base_truth = base.run(initial, "runtime.continue")
    coupled = OrchCoupledExecutor(program, live, _phase(), _config())
    trace = coupled.run_coupled(initial, "runtime.continue")
    return program, live, initial, base, base_final, base_truth, trace


def test_direct_coupling_preserves_v020_sigma_and_truth():
    _, _, _, base, final, truth, trace = _run_pair()
    assert trace.final_sigma_id == final.state_id
    assert trace.branch_truth_state == truth == "FALSE"
    assert [s.payload for s in trace.base_steps] == [s.payload for s in base.steps]


def test_direct_coupling_runs_inside_all_actual_transitions():
    *_, trace = _run_pair()
    assert len(trace.base_steps) == 9
    assert len(trace.transition_ids) == 9
    assert len(trace.final_orch.orbitals) == 9
    assert len(set(o.mode_id for o in trace.final_orch.orbitals)) == 9


def test_direct_coupling_does_not_open_authority():
    *_, trace = _run_pair()
    assert trace.payload["v020_sigma_semantics_modified"] is False
    assert trace.payload["routing_authority_opened"] is False
    assert trace.payload["effect_authority_opened"] is False
    assert trace.payload["persistent_memory_write_performed"] is False
    assert trace.payload["external_effects"] is False


def test_direct_coupling_changes_phase_sidecar_only():
    *_, trace = _run_pair()
    assert trace.final_phase.state_id != trace.initial_phase_id
    assert trace.final_phase.phase_proper_time > 0.0


def test_dynamic_process_sphere_is_adjacency_only():
    *_, trace = _run_pair()
    K = trace.final_orch.sphere.coupling
    assert K[0][1] == pytest.approx(0.4)
    assert K[1][0] == pytest.approx(0.4)
    assert K[0][2] == 0.0


def test_missing_explicit_step_gate_fails_closed():
    program = _program()
    coupled = OrchCoupledExecutor(program, _live(), _phase(), _config(step_count=1))
    with pytest.raises(OrchExecutorV27Error, match="missing explicit hydrodynamic gate"):
        coupled.run_coupled(_initial(program), "runtime.continue")


def _receipt(program, live, initial, trace):
    payload = {
        "schema": RECEIPT_SCHEMA,
        "execution_contract_id": EXECUTION_CONTRACT_ID,
        "program": program.provenance_payload,
        "canonical_graph_sha256": _sha256_json(program.canonical_graph),
        "canonical_leaf_path": list(program.leaf_path),
        "live_surface": live.receipt_payload,
        "input_values": [[k, v] for k, v in initial.input_values],
        "admission": {
            "branch_truth_state": trace.branch_truth_state,
            "admitted_target": "runtime.continue",
            "epistemic_operator": None,
        },
        "initial_sigma_id": trace.initial_sigma_id,
        "final_sigma_id": trace.final_sigma_id,
        "steps": [s.payload for s in trace.base_steps],
        "result": {"kind": "INTERNAL_TRANSFORM", "control_location": "runtime.continue"},
        "external_effects": False,
        "semantic_mass_is_authorization": False,
        "free_form_nl_execution": False,
        "deterministic_fields_only": True,
    }
    return {**payload, "receipt_sha256": _sha256_json(payload)}


def test_direct_trace_binds_to_exact_v020_receipt():
    program, live, initial, _, _, _, trace = _run_pair()
    receipt = _receipt(program, live, initial, trace)
    bound = bind_direct_trace_to_receipt(trace, receipt)
    assert bound.execution_receipt_sha256 == receipt["receipt_sha256"]
    assert bound.payload["v020_receipt_modified"] is False
    assert bound.payload["inverse_provenance"][0]["id"] == trace.trace_id


def test_receipt_tamper_rejected_after_direct_execution():
    program, live, initial, _, _, _, trace = _run_pair()
    receipt = _receipt(program, live, initial, trace)
    receipt["steps"][0]["operator_id"] = "ORDER"
    with pytest.raises(Exception):
        bind_direct_trace_to_receipt(trace, receipt)


def test_config_identity_is_deterministic():
    assert _config().config_id == _config().config_id
