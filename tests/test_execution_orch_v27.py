from __future__ import annotations

import copy

import pytest

from phasenav_natural_code.execution_orch_authority_v27 import (
    COUPLED_EXECUTION_CONTRACT_ID,
    COUPLED_RECEIPT_SCHEMA,
    CoupledExecutionV27Error,
    ProgramAuthority,
    definition_content_id,
    expected_leaf_path,
)
from phasenav_natural_code.hydro_time_v27 import _sha256_json

GRAPH = (
    "branch",
    (
        "or",
        ("comparison", "memory_pressure", "gt", 0.9),
        ("comparison", "risk", "gt", 0.8),
    ),
    "safety.pause",
    "runtime.continue",
)
LEAF = expected_leaf_path(GRAPH)
CONTENT_ID = definition_content_id(GRAPH, LEAF)


def _receipt() -> dict[str, object]:
    program = {
        "content_id": CONTENT_ID,
        "realization_id": "pncs:realization36:sha256:" + "1" * 64,
        "realization_binding_id": "pncs:binding36:sha256:" + "2" * 64,
        "mass_binding_id": "pncs:mass-binding:sha256:" + "3" * 64,
        "phase36_sha256": "4" * 64,
        "semantic_mass": 0.2,
    }
    body = {
        "schema": "PNCS_NATIVE_EXECUTION_RECEIPT_V0_20",
        "execution_contract_id": "PNCS_NATIVE_EXECUTION_CORE_V0_20",
        "program": program,
        "canonical_graph_sha256": _sha256_json(GRAPH),
        "canonical_leaf_path": list(LEAF),
        "live_surface": {
            "root": "/dev/shm/ciel_noema",
            "phi_sha256": "5" * 64,
            "aux_phi_sha256": "6" * 64,
            "aux_feedback_phi_sha256": "6" * 64,
            "operator_registry_sha256": "7" * 64,
            "tether_receipt_sha256": "8" * 64,
        },
        "input_values": [["memory_pressure", 0.0], ["risk", 0.0]],
        "admission": {
            "branch_truth_state": "FALSE",
            "admitted_target": "runtime.continue",
            "epistemic_operator": None,
        },
        "initial_sigma_id": "pncs:sigma:sha256:" + "9" * 64,
        "final_sigma_id": "pncs:sigma:sha256:" + "a" * 64,
        "steps": [],
        "result": {"kind": "INTERNAL_TRANSFORM", "control_location": "runtime.continue"},
        "external_effects": False,
        "semantic_mass_is_authorization": False,
        "free_form_nl_execution": False,
        "deterministic_fields_only": True,
    }
    return {**body, "receipt_sha256": _sha256_json(body)}


def test_program_authority_binds_exact_v20_receipt():
    receipt = _receipt()
    authority = ProgramAuthority.from_v20_receipt(receipt, GRAPH)
    assert authority.source_v20_receipt_sha256 == receipt["receipt_sha256"]
    assert authority.content_id == CONTENT_ID
    assert authority.canonical_graph == GRAPH
    assert authority.leaf_path == LEAF


def test_definition_identity_recomputed_from_graph_and_leaf_path():
    assert definition_content_id(GRAPH, LEAF) == CONTENT_ID


def test_program_authority_id_is_deterministic():
    receipt = _receipt()
    a = ProgramAuthority.from_v20_receipt(receipt, GRAPH)
    b = ProgramAuthority.from_v20_receipt(receipt, GRAPH)
    assert a.authority_id == b.authority_id


def test_tampered_v20_receipt_rejected():
    receipt = _receipt()
    receipt["result"]["control_location"] = "runtime.tampered"
    with pytest.raises(CoupledExecutionV27Error, match="digest"):
        ProgramAuthority.from_v20_receipt(receipt, GRAPH)


def test_wrong_graph_rejected():
    wrong = (
        "branch",
        ("comparison", "risk", "gt", 0.8),
        "safety.pause",
        "runtime.continue",
    )
    with pytest.raises(CoupledExecutionV27Error):
        ProgramAuthority.from_v20_receipt(_receipt(), wrong)


def test_wrong_graph_sha_rejected_even_after_outer_resign():
    receipt = _receipt()
    receipt["canonical_graph_sha256"] = "0" * 64
    body = dict(receipt)
    body.pop("receipt_sha256")
    receipt["receipt_sha256"] = _sha256_json(body)
    with pytest.raises(CoupledExecutionV27Error, match="canonical graph SHA"):
        ProgramAuthority.from_v20_receipt(receipt, GRAPH)


def test_wrong_content_id_rejected_even_after_outer_resign():
    receipt = _receipt()
    receipt["program"]["content_id"] = "pncs:def:sha256:" + "0" * 64
    body = dict(receipt)
    body.pop("receipt_sha256")
    receipt["receipt_sha256"] = _sha256_json(body)
    with pytest.raises(CoupledExecutionV27Error, match="graph/content"):
        ProgramAuthority.from_v20_receipt(receipt, GRAPH)


def test_leaf_path_is_exact_and_contains_false_arm_negation():
    assert LEAF == (
        "DIFFERENCE",
        "CONDITION",
        "DIFFERENCE",
        "CONDITION",
        "COMPOSITION",
        "NEGATION",
        "ORDER",
        "TRANSFORM",
        "ORDER",
        "TRANSFORM",
        "COMPOSITION",
    )


def test_coupled_contract_names_are_frozen():
    assert COUPLED_EXECUTION_CONTRACT_ID == "PNCS_ORCHORBITAL_COUPLED_EXECUTION_V0_27"
    assert COUPLED_RECEIPT_SCHEMA == "PNCS_ORCHORBITAL_COUPLED_EXECUTION_RECEIPT_V0_27"


def test_pure_authority_tests_do_not_require_historical_paths_or_live_surface():
    authority = ProgramAuthority.from_v20_receipt(_receipt(), GRAPH)
    assert authority.semantic_mass == pytest.approx(0.2)
