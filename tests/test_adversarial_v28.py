from __future__ import annotations

from dataclasses import replace

import pytest

from phasenav_natural_code.adversarial_v28 import (
    AdversarialCase,
    AdversarialResult,
    AdversarialV28Error,
    canonical_mapping_digest,
    cyrillic_confusable_operator,
    mutate_and_resign,
    resign_v20_receipt,
    validate_direct_trace_structure,
)
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
from phasenav_natural_code.execution_v20_state import ExecutionStep, SigmaState, _Executor
from phasenav_natural_code.hydro_time_v27 import HydrodynamicPhaseGate, PhaseFlowState36
from phasenav_natural_code.orchorbital_executor_v27 import (
    CouplingConfig,
    OrchCoupledExecutor,
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
        ("or", ("comparison", "memory_pressure", "gt", 0.9), ("comparison", "risk", "gt", 0.8)),
        "safety.pause",
        "runtime.continue",
    )


def _program():
    graph = _graph()
    leaf = expected_leaf_path(graph)
    return BoundInternalProgram(
        definition_content_id(graph, leaf),
        graph,
        leaf,
        "pncs:realization36:sha256:" + "1" * 64,
        "pncs:binding36:sha256:" + "2" * 64,
        "pncs:mass-binding:sha256:" + "3" * 64,
        "4" * 64,
        0.2,
    )


def _vectors():
    return {
        op: tuple(0.01 * (i + 1) + 0.03 * n for i in range(36))
        for n, op in enumerate(sorted(EXECUTABLE_INTERNAL_OPERATORS), start=1)
    }


def _live():
    return LiveSurfaceSnapshot(
        "/dev/shm/ciel_noema", "a" * 64, "b" * 64, "c" * 64, "d" * 64, "e" * 64, _vectors()
    )


def _initial(program):
    return SigmaState(
        program.content_id,
        program.realization_id,
        program.mass_binding_id,
        program.phase36_sha256,
        program.semantic_mass,
        "a" * 64,
        (("memory_pressure", 0.0), ("risk", 0.0)),
        "pncs.entry",
    )


def _config(step_count=9):
    return CouplingConfig(
        ProjectionPolicy(0.4, 0.2, 1.0, 0.7, AttractorWeights(0.6, 0.4, 0.0), 1.0, 1.2, "parent_embedding"),
        TimeLaw(1.0, 0.0, 0.1, -0.05, 0.0, 0.1, 0.25, 2.0),
        ReductionLaw(1.0, 0.5, 0.5, 0.2, 999.0),
        SelectionLaw(0.1, 0.5, 0.2, 0.1, 0.0, 0.2),
        BridgePolicy(0.01, 8.0),
        {i: HydrodynamicPhaseGate(1.0, 0.1, coordinate_dt=0.01) for i in range(1, step_count + 1)},
        "pncs.test.relation",
        "pncs.test.intent",
        0.8,
        0.1,
        Potentials(0, 0, 0, 0, 0, 0),
    )


def _phase():
    return PhaseFlowState36(tuple(0.01 * i for i in range(36)))


def _run():
    program = _program()
    live = _live()
    initial = _initial(program)
    base = _Executor(program, live)
    base_final, base_truth = base.run(initial, "runtime.continue")
    coupled = OrchCoupledExecutor(program, live, _phase(), _config())
    trace = coupled.run_coupled(initial, "runtime.continue")
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
    receipt = {**payload, "receipt_sha256": _sha256_json(payload)}
    return program, base_final, base_truth, trace, receipt


def _must_reject(trace, receipt):
    with pytest.raises(Exception):
        bind_direct_trace_to_receipt(trace, receipt)


def test_valid_direct_trace_structure_passes():
    *_, trace, _ = _run()
    assert validate_direct_trace_structure(trace) == trace.trace_id


def test_valid_receipt_still_binds():
    *_, trace, receipt = _run()
    assert bind_direct_trace_to_receipt(trace, receipt).execution_receipt_sha256 == receipt["receipt_sha256"]


def test_resigned_valid_receipt_preserves_digest():
    *_, receipt = _run()
    assert resign_v20_receipt(receipt)["receipt_sha256"] == receipt["receipt_sha256"]


def test_resigned_confusable_operator_is_rejected_semantically():
    *_, trace, receipt = _run()
    attacked = mutate_and_resign(
        receipt,
        lambda r: r["steps"][7].__setitem__("operator_id", cyrillic_confusable_operator("TRANSFORM")),
    )
    _must_reject(trace, attacked)


def test_resigned_valid_operator_substitution_rejected():
    *_, trace, receipt = _run()
    attacked = mutate_and_resign(receipt, lambda r: r["steps"][0].__setitem__("operator_id", "ORDER"))
    _must_reject(trace, attacked)


def test_resigned_vector_digest_substitution_rejected():
    *_, trace, receipt = _run()
    attacked = mutate_and_resign(receipt, lambda r: r["steps"][0].__setitem__("operator_vector_sha256", "0" * 64))
    _must_reject(trace, attacked)


def test_resigned_final_sigma_substitution_rejected():
    *_, trace, receipt = _run()
    attacked = mutate_and_resign(receipt, lambda r: r.__setitem__("final_sigma_id", "pncs:sigma:sha256:" + "0" * 64))
    _must_reject(trace, attacked)


def test_resigned_initial_sigma_substitution_rejected():
    *_, trace, receipt = _run()
    attacked = mutate_and_resign(receipt, lambda r: r.__setitem__("initial_sigma_id", "pncs:sigma:sha256:" + "0" * 64))
    _must_reject(trace, attacked)


def test_resigned_program_content_id_substitution_rejected():
    *_, trace, receipt = _run()
    attacked = mutate_and_resign(receipt, lambda r: r["program"].__setitem__("content_id", "pncs:def:sha256:" + "0" * 64))
    _must_reject(trace, attacked)


def test_resigned_truth_state_substitution_rejected():
    *_, trace, receipt = _run()
    attacked = mutate_and_resign(receipt, lambda r: r["admission"].__setitem__("branch_truth_state", "TRUE"))
    _must_reject(trace, attacked)


def test_resigned_step_truncation_rejected():
    *_, trace, receipt = _run()
    def mut(r):
        r["steps"] = r["steps"][:-1]
    _must_reject(trace, mutate_and_resign(receipt, mut))


def test_resigned_step_index_discontinuity_rejected():
    *_, trace, receipt = _run()
    attacked = mutate_and_resign(receipt, lambda r: r["steps"][3].__setitem__("index", 99))
    _must_reject(trace, attacked)


def test_resigned_sigma_chain_gap_rejected():
    *_, trace, receipt = _run()
    attacked = mutate_and_resign(receipt, lambda r: r["steps"][2].__setitem__("before_sigma_id", "pncs:sigma:sha256:" + "f" * 64))
    _must_reject(trace, attacked)


def test_direct_trace_transition_count_substitution_rejected():
    *_, trace, _ = _run()
    bad = replace(trace, transition_ids=trace.transition_ids[:-1])
    with pytest.raises(AdversarialV28Error, match="transition count"):
        validate_direct_trace_structure(bad)


def test_direct_trace_duplicate_transition_identity_rejected():
    *_, trace, _ = _run()
    ids = list(trace.transition_ids)
    ids[1] = ids[0]
    bad = replace(trace, transition_ids=tuple(ids))
    with pytest.raises(AdversarialV28Error, match="duplicate ORCH transition"):
        validate_direct_trace_structure(bad)


def test_direct_trace_sigma_chain_gap_rejected():
    *_, trace, _ = _run()
    steps = list(trace.base_steps)
    victim = steps[2]
    steps[2] = ExecutionStep(
        victim.index,
        victim.operator_id,
        victim.operator_vector_sha256,
        "pncs:sigma:sha256:" + "0" * 64,
        victim.after_sigma_id,
        victim.bindings,
    )
    bad = replace(trace, base_steps=tuple(steps))
    with pytest.raises(AdversarialV28Error, match="Sigma chain discontinuity"):
        validate_direct_trace_structure(bad)


def test_direct_trace_step_index_substitution_rejected():
    *_, trace, _ = _run()
    steps = list(trace.base_steps)
    victim = steps[1]
    steps[1] = ExecutionStep(
        7,
        victim.operator_id,
        victim.operator_vector_sha256,
        victim.before_sigma_id,
        victim.after_sigma_id,
        victim.bindings,
    )
    bad = replace(trace, base_steps=tuple(steps))
    with pytest.raises(AdversarialV28Error, match="step index discontinuity"):
        validate_direct_trace_structure(bad)


def test_receipt_mapping_key_order_is_equivalent():
    *_, trace, receipt = _run()
    reversed_mapping = dict(reversed(list(receipt.items())))
    assert canonical_mapping_digest(receipt) == canonical_mapping_digest(reversed_mapping)
    assert bind_direct_trace_to_receipt(trace, reversed_mapping).bound_trace_id == bind_direct_trace_to_receipt(trace, receipt).bound_trace_id


def test_config_gate_mapping_insertion_order_is_equivalent():
    a = _config()
    rev = dict(reversed(list(a.gates_by_step.items())))
    b = replace(a, gates_by_step=rev)
    assert a.config_id == b.config_id


def test_adversarial_case_identity_is_deterministic():
    a = AdversarialCase("UNICODE_CONFUSABLE", "v0.20 operator_id", "Latin O -> Cyrillic O")
    b = AdversarialCase("UNICODE_CONFUSABLE", "v0.20 operator_id", "Latin O -> Cyrillic O")
    assert a.case_id == b.case_id
    assert a.payload["external_effects"] is False


def test_adversarial_result_pass_logic_reject():
    case = AdversarialCase("TYPED_ID_SUBSTITUTION", "program.content_id", "valid-shape wrong digest")
    result = AdversarialResult(case, "REJECT", "bind_direct_trace_to_receipt", "program mismatch")
    assert result.passed is True and result.payload["external_effects"] is False


def test_adversarial_result_pass_logic_equivalence():
    case = AdversarialCase("MAPPING_ORDER", "receipt", "reverse insertion order", expected="EQUIVALENT")
    result = AdversarialResult(case, "ACCEPT_EQUIVALENT", "canonical_mapping_digest", "same digest")
    assert result.passed is True


def test_invalid_expected_class_fails_closed():
    with pytest.raises(AdversarialV28Error):
        AdversarialCase("X", "Y", "Z", expected="MAYBE")


def test_confusable_is_not_ascii_operator():
    attacked = cyrillic_confusable_operator("ORDER")
    assert attacked != "ORDER" and attacked.encode("utf-8") != b"ORDER"
