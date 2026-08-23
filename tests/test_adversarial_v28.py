from __future__ import annotations

import copy

import pytest

from phasenav_natural_code.adversarial_v28 import (
    AdversarialCase,
    AdversarialResult,
    AdversarialV28Error,
    canonical_mapping_digest,
    cyrillic_confusable_operator,
    mutate_and_resign,
    resign_coupled_receipt,
    validate_coupled_receipt_structure,
)
from phasenav_natural_code.execution_orch_authority_v27 import (
    COUPLED_EXECUTION_CONTRACT_ID,
    COUPLED_RECEIPT_SCHEMA,
    V20_CONTRACT_ID,
    V20_RECEIPT_SCHEMA,
)
from phasenav_natural_code.hydro_time_v27 import _sha256_json, _typed_id


def _sigma(ch: str) -> str:
    return "pncs:sigma:sha256:" + ch * 64


def _source_v20() -> dict[str, object]:
    program = {
        "content_id": "pncs:def:sha256:" + "1" * 64,
        "realization_id": "pncs:realization36:sha256:" + "2" * 64,
        "realization_binding_id": "pncs:binding36:sha256:" + "3" * 64,
        "mass_binding_id": "pncs:mass-binding:sha256:" + "4" * 64,
        "phase36_sha256": "5" * 64,
        "semantic_mass": 0.2,
    }
    steps = [
        {
            "index": 1,
            "operator_id": "DIFFERENCE",
            "operator_vector_sha256": "a" * 64,
            "before_sigma_id": _sigma("a"),
            "after_sigma_id": _sigma("b"),
            "bindings": {"subject": "risk", "threshold": 0.8, "value": 0.0},
        },
        {
            "index": 2,
            "operator_id": "CONDITION",
            "operator_vector_sha256": "b" * 64,
            "before_sigma_id": _sigma("b"),
            "after_sigma_id": _sigma("c"),
            "bindings": {"comparator": "gt", "difference": -0.8, "truth": False},
        },
        {
            "index": 3,
            "operator_id": "ORDER",
            "operator_vector_sha256": "c" * 64,
            "before_sigma_id": _sigma("c"),
            "after_sigma_id": _sigma("d"),
            "bindings": {"branch": "FALSE", "target": "runtime.continue"},
        },
    ]
    body = {
        "schema": V20_RECEIPT_SCHEMA,
        "execution_contract_id": V20_CONTRACT_ID,
        "program": program,
        "canonical_graph_sha256": "6" * 64,
        "canonical_leaf_path": ["DIFFERENCE", "CONDITION", "ORDER"],
        "input_values": [["risk", 0.0]],
        "admission": {
            "branch_truth_state": "FALSE",
            "admitted_target": "runtime.continue",
            "epistemic_operator": None,
        },
        "initial_sigma_id": _sigma("a"),
        "final_sigma_id": _sigma("d"),
        "steps": steps,
        "result": {"kind": "INTERNAL_TRANSFORM", "control_location": "runtime.continue"},
        "external_effects": False,
        "semantic_mass_is_authorization": False,
        "free_form_nl_execution": False,
        "deterministic_fields_only": True,
    }
    return {**body, "receipt_sha256": _sha256_json(body)}


def _coupled(source: dict[str, object] | None = None) -> dict[str, object]:
    source = source or _source_v20()
    exact_fields = (
        "program",
        "canonical_graph_sha256",
        "canonical_leaf_path",
        "input_values",
        "admission",
        "initial_sigma_id",
        "final_sigma_id",
        "steps",
        "result",
        "external_effects",
        "semantic_mass_is_authorization",
        "free_form_nl_execution",
        "deterministic_fields_only",
    )
    projection = {field: copy.deepcopy(source[field]) for field in exact_fields}
    occurrences = []
    ids = []
    for step in projection["steps"]:
        occurrence = {
            "step_index": step["index"],
            "operator_id": step["operator_id"],
            "operator_vector_sha256": step["operator_vector_sha256"],
            "before_sigma_id": step["before_sigma_id"],
            "after_sigma_id": step["after_sigma_id"],
            "proper_time_advanced": 0.01,
            "semantic_identity_modified": False,
            "external_effects": False,
        }
        occurrences.append(occurrence)
        ids.append(_typed_id("pncs:orch-hydro-occurrence", occurrence))
    program_authority_id = _typed_id(
        "pncs:coupled-program-authority",
        {
            "source_v20_receipt_sha256": source["receipt_sha256"],
            "program": projection["program"],
            "canonical_graph_sha256": projection["canonical_graph_sha256"],
            "leaf_path": projection["canonical_leaf_path"],
        },
    )
    body = {
        "schema": COUPLED_RECEIPT_SCHEMA,
        "execution_contract_id": COUPLED_EXECUTION_CONTRACT_ID,
        "source_v20_authority_receipt_sha256": source["receipt_sha256"],
        "program_authority_id": program_authority_id,
        "semantic_projection": projection,
        "semantic_projection_sha256": _sha256_json(projection),
        "orch_occurrences": occurrences,
        "orch_occurrence_ids": ids,
        "final_phase_state_id": "pncs:t36-flow-state:sha256:" + "7" * 64,
        "phase_proper_time_advanced": 0.03,
        "routing_feedback_opened": False,
        "semantic_identity_modified": False,
        "external_effects": False,
        "laboratory_time_modified": False,
        "deterministic_fields_only": True,
    }
    return {**body, "receipt_sha256": _sha256_json(body)}


def _reject(receipt: dict[str, object], source: dict[str, object] | None = None) -> None:
    with pytest.raises(AdversarialV28Error):
        validate_coupled_receipt_structure(receipt, source_v20_receipt=source or _source_v20())


def test_valid_current_coupled_receipt_passes():
    source = _source_v20()
    receipt = _coupled(source)
    assert validate_coupled_receipt_structure(receipt, source_v20_receipt=source) == receipt["receipt_sha256"]


def test_resign_without_mutation_preserves_identity():
    receipt = _coupled()
    assert resign_coupled_receipt(receipt)["receipt_sha256"] == receipt["receipt_sha256"]


def test_mapping_insertion_order_is_equivalent():
    receipt = _coupled()
    reversed_mapping = dict(reversed(list(receipt.items())))
    assert canonical_mapping_digest(receipt) == canonical_mapping_digest(reversed_mapping)
    assert validate_coupled_receipt_structure(reversed_mapping, source_v20_receipt=_source_v20()) == receipt["receipt_sha256"]


def test_resigned_confusable_operator_rejected_against_source():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["semantic_projection"]["steps"][2].__setitem__(
            "operator_id", cyrillic_confusable_operator("ORDER")
        ),
    )
    _reject(attacked)


def test_resigned_registered_operator_substitution_rejected_against_source():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["semantic_projection"]["steps"][0].__setitem__("operator_id", "ORDER"),
    )
    _reject(attacked)


def test_resigned_vector_digest_substitution_rejected_against_source():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["semantic_projection"]["steps"][0].__setitem__("operator_vector_sha256", "0" * 64),
    )
    _reject(attacked)


def test_resigned_initial_sigma_substitution_rejected_against_source():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["semantic_projection"].__setitem__("initial_sigma_id", _sigma("0")),
    )
    _reject(attacked)


def test_resigned_final_sigma_substitution_rejected_against_source():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["semantic_projection"].__setitem__("final_sigma_id", _sigma("0")),
    )
    _reject(attacked)


def test_resigned_program_content_id_substitution_rejected():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["semantic_projection"]["program"].__setitem__(
            "content_id", "pncs:def:sha256:" + "0" * 64
        ),
    )
    _reject(attacked)


def test_resigned_truth_state_substitution_rejected_against_source():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["semantic_projection"]["admission"].__setitem__("branch_truth_state", "TRUE"),
    )
    _reject(attacked)


def test_resigned_step_truncation_rejected_against_source():
    def mutate(r):
        r["semantic_projection"]["steps"] = r["semantic_projection"]["steps"][:-1]
    _reject(mutate_and_resign(_coupled(), mutate))


def test_resigned_step_index_discontinuity_rejected():
    source = _source_v20()
    attacked = mutate_and_resign(
        _coupled(source),
        lambda r: (
            r["semantic_projection"]["steps"][1].__setitem__("index", 99),
            r["orch_occurrences"][1].__setitem__("step_index", 99),
        ),
    )
    _reject(attacked, source)


def test_resigned_sigma_chain_gap_rejected():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["semantic_projection"]["steps"][1].__setitem__("before_sigma_id", _sigma("0")),
    )
    _reject(attacked)


def test_orch_occurrence_count_substitution_rejected():
    def mutate(r):
        r["orch_occurrences"] = r["orch_occurrences"][:-1]
        r["orch_occurrence_ids"] = r["orch_occurrence_ids"][:-1]
    _reject(mutate_and_resign(_coupled(), mutate))


def test_duplicate_orch_occurrence_identity_rejected():
    def mutate(r):
        r["orch_occurrence_ids"][1] = r["orch_occurrence_ids"][0]
    _reject(mutate_and_resign(_coupled(), mutate))


def test_orch_operator_substitution_rejected():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["orch_occurrences"][0].__setitem__("operator_id", "ORDER"),
    )
    _reject(attacked)


def test_orch_vector_substitution_rejected():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["orch_occurrences"][0].__setitem__("operator_vector_sha256", "0" * 64),
    )
    _reject(attacked)


def test_external_effect_boundary_substitution_rejected():
    attacked = mutate_and_resign(_coupled(), lambda r: r.__setitem__("external_effects", True))
    _reject(attacked)


def test_negative_proper_time_rejected():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r["orch_occurrences"][0].__setitem__("proper_time_advanced", -0.1),
    )
    _reject(attacked)


def test_tampered_source_v20_digest_rejected():
    source = _source_v20()
    source["steps"][0]["operator_id"] = "ORDER"
    with pytest.raises(AdversarialV28Error, match="source v0.20 receipt digest"):
        validate_coupled_receipt_structure(_coupled(), source_v20_receipt=source)


def test_program_authority_substitution_rejected_even_after_resign():
    attacked = mutate_and_resign(
        _coupled(),
        lambda r: r.__setitem__("program_authority_id", "pncs:coupled-program-authority:sha256:" + "0" * 64),
    )
    _reject(attacked)


def test_adversarial_case_identity_is_deterministic():
    a = AdversarialCase("UNICODE_CONFUSABLE", "operator_id", "Latin O -> Cyrillic O")
    b = AdversarialCase("UNICODE_CONFUSABLE", "operator_id", "Latin O -> Cyrillic O")
    assert a.case_id == b.case_id
    assert a.payload["external_effects"] is False


def test_adversarial_result_reject_pass_logic():
    case = AdversarialCase("TYPED_ID_SUBSTITUTION", "program.content_id", "wrong digest")
    result = AdversarialResult(case, "REJECT", "validate_coupled_receipt_structure", "program mismatch")
    assert result.passed is True
    assert result.payload["external_effects"] is False


def test_adversarial_result_equivalence_pass_logic():
    case = AdversarialCase("MAPPING_ORDER", "receipt", "reverse insertion order", expected="EQUIVALENT")
    result = AdversarialResult(case, "ACCEPT_EQUIVALENT", "canonical_mapping_digest", "same digest")
    assert result.passed is True


def test_invalid_expected_class_fails_closed():
    with pytest.raises(AdversarialV28Error):
        AdversarialCase("X", "Y", "Z", expected="MAYBE")


def test_confusable_is_not_ascii_operator():
    attacked = cyrillic_confusable_operator("ORDER")
    assert attacked != "ORDER"
    assert attacked.encode("utf-8") != b"ORDER"
