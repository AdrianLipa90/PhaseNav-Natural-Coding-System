from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from phasenav_natural_code import (
    ClassRegistry,
    ClusterRegistry,
    DefinitionContent,
    DefinitionRecord,
    DefinitionRegistry,
    FileRegistry,
    HierarchyRegistry,
    Kaku,
    RadicalGraph,
    Vector36,
    define_class,
    define_cluster,
    define_file,
    define_high_orchestrator,
    define_low_orchestrator,
    define_subsystem,
    define_system,
)
from phasenav_natural_code import lineage_v22 as lineage


def _fixture(*, ambiguous: bool = False):
    definition = DefinitionContent(
        kind="INTERNAL_BRANCH",
        canonical_graph=("branch", ("comparison", "risk", "gt", 0.8), "route.ok", None),
        leaf_path=("DIFFERENCE", "CONDITION", "ORDER", "TRANSFORM", "COMPOSITION"),
    )
    definitions = DefinitionRegistry()
    definitions.register(DefinitionRecord(alias="lineage_definition", content=definition))

    classes = ClassRegistry({definition.content_id: definition})
    class_record = classes.register(define_class("lineage_class", (definition.content_id,)))
    files = FileRegistry(classes)
    file_record = files.register(define_file("lineage_file", (class_record.content.content_id,)))
    clusters = ClusterRegistry(files)
    cluster_record = clusters.register(define_cluster("lineage_cluster", (file_record.content.content_id,)))
    hierarchy = HierarchyRegistry(clusters)
    subsystem = hierarchy.register(define_subsystem("lineage_subsystem", (cluster_record.content.content_id,)))
    low_children = (subsystem.content.content_id, subsystem.content.content_id) if ambiguous else (subsystem.content.content_id,)
    low = hierarchy.register(define_low_orchestrator("lineage_low", low_children))
    high = hierarchy.register(define_high_orchestrator("lineage_high", (low.content.content_id,)))
    system = hierarchy.register(define_system("lineage_system", (high.content.content_id,)))

    registries = lineage.LineageRegistries(definitions, classes, files, clusters, hierarchy)

    radical = RadicalGraph("R.LINEAGE.V22", "basis36")
    schedule = []
    for i, role in enumerate(definition.leaf_path):
        kid = f"K.V22.{i}"
        radical.add_kaku(
            Kaku(
                kaku_id=kid,
                vector=Vector36(tuple((i + j) / 100.0 for j in range(36)), "basis36"),
                semantic_mass=0.1 + i,
                direction="FORWARD",
                polarity=1.0,
                role=role,
            )
        )
        schedule.append(kid)

    initial_sigma = "pncs:sigma:sha256:" + "0" * 64
    sigma_ids = ["pncs:sigma:sha256:" + f"{i + 1:x}" * 64 for i in range(len(definition.leaf_path))]
    final_state = SimpleNamespace(
        content_id=definition.content_id,
        state_id=sigma_ids[-1],
        control_location="route.ok",
    )
    steps = []
    before = initial_sigma
    for i, (role, after) in enumerate(zip(definition.leaf_path, sigma_ids), start=1):
        steps.append(
            {
                "schema": "PNCS_KAKU_TRANSITION_V0_20",
                "index": i,
                "operator_id": role,
                "operator_vector_sha256": f"{i:x}" * 64,
                "before_sigma_id": before,
                "after_sigma_id": after,
                "bindings": {},
            }
        )
        before = after

    payload = {
        "schema": lineage.EXECUTION_RECEIPT_SCHEMA_V20,
        "execution_contract_id": lineage.EXECUTION_CONTRACT_ID_V20,
        "program": {
            "content_id": definition.content_id,
            "realization_id": "pncs:realization36:sha256:" + "a" * 64,
            "realization_binding_id": "pncs:binding36:sha256:" + "b" * 64,
            "mass_binding_id": "pncs:mass-binding:sha256:" + "c" * 64,
            "phase36_sha256": "d" * 64,
            "semantic_mass": 1.0,
        },
        "canonical_graph_sha256": lineage._sha(definition.canonical_graph),
        "canonical_leaf_path": list(definition.leaf_path),
        "live_surface": {
            "root": "/dev/shm/ciel_noema",
            "phi_sha256": "1" * 64,
            "aux_phi_sha256": "2" * 64,
            "aux_feedback_phi_sha256": "3" * 64,
            "operator_registry_sha256": "4" * 64,
            "tether_receipt_sha256": "5" * 64,
        },
        "input_values": [["risk", 1.0]],
        "admission": {"branch_truth_state": "TRUE", "admitted_target": "route.ok", "epistemic_operator": None},
        "initial_sigma_id": initial_sigma,
        "final_sigma_id": final_state.state_id,
        "steps": steps,
        "result": {"kind": "INTERNAL_TRANSFORM", "control_location": "route.ok"},
        "external_effects": False,
        "semantic_mass_is_authorization": False,
        "free_form_nl_execution": False,
        "deterministic_fields_only": True,
    }
    receipt = {**payload, "receipt_sha256": lineage._sha(payload)}
    result = SimpleNamespace(target="route.ok", branch_truth_state="TRUE", final_state=final_state, receipt=receipt)
    return definition, system.content.content_id, registries, radical, tuple(schedule), result


def test_exact_result_to_kaku_inverse_chain_is_deterministic():
    definition, system_id, registries, radical, schedule, result = _fixture()
    value = lineage.resolve_exact_inverse_lineage(result, system_id, registries, radical, schedule)
    again = lineage.resolve_exact_inverse_lineage(result, system_id, registries, radical, schedule)
    assert value.lineage_id == again.lineage_id
    assert value.hierarchy.definition_id == definition.content_id
    assert [row["level"] for row in value.inverse_chain] == [
        "RESULT", "SYSTEM", "HIGH_ORCHESTRATOR", "LOW_ORCHESTRATOR", "SUBSYSTEM",
        "CLUSTER", "FILE", "CLASS", "DEFINITION", "RADICAL", "KAKU",
    ]
    assert value.definition_radical.operator_ids == definition.leaf_path


def test_reused_hierarchy_content_is_ambiguous_without_occurrence_selector():
    _definition, system_id, registries, radical, schedule, result = _fixture(ambiguous=True)
    occurrences = lineage.find_definition_occurrences(system_id, result.final_state.content_id, registries)
    assert len(occurrences) == 2
    assert occurrences[0] != occurrences[1]
    with pytest.raises(lineage.ExactInverseLineageV22Error, match="ambiguous inverse lineage"):
        lineage.resolve_exact_inverse_lineage(result, system_id, registries, radical, schedule)
    selected = lineage.resolve_exact_inverse_lineage(
        result, system_id, registries, radical, schedule, selected_occurrence=occurrences[1]
    )
    assert selected.hierarchy == occurrences[1]


def test_transition_trace_tamper_fails_closed_even_when_receipt_is_rehashed():
    _definition, system_id, registries, radical, schedule, result = _fixture()
    tampered = copy.deepcopy(result.receipt)
    tampered["steps"][1]["before_sigma_id"] = "pncs:sigma:sha256:" + "f" * 64
    tampered.pop("receipt_sha256")
    tampered["receipt_sha256"] = lineage._sha(tampered)
    bad = SimpleNamespace(target=result.target, branch_truth_state=result.branch_truth_state, final_state=result.final_state, receipt=tampered)
    with pytest.raises(lineage.ExactInverseLineageV22Error, match="discontinuous"):
        lineage.resolve_exact_inverse_lineage(bad, system_id, registries, radical, schedule)


def test_definition_radical_role_mismatch_fails_closed():
    definition, _system_id, _registries, radical, schedule, _result = _fixture()
    first = radical.nodes[schedule[0]]
    radical.nodes[schedule[0]] = Kaku(
        kaku_id=first.kaku_id,
        vector=first.vector,
        semantic_mass=first.semantic_mass,
        direction=first.direction,
        polarity=first.polarity,
        role="NEGATION",
        phase=first.phase,
    )
    with pytest.raises(lineage.ExactInverseLineageV22Error, match="does not match Definition leaf_path"):
        lineage.bind_definition_radical(definition, radical, schedule)


def test_receipt_definition_graph_and_leaf_path_must_match_registered_content():
    _definition, system_id, registries, radical, schedule, result = _fixture()
    tampered = copy.deepcopy(result.receipt)
    tampered["canonical_leaf_path"] = ["NEGATION"]
    tampered.pop("receipt_sha256")
    tampered["receipt_sha256"] = lineage._sha(tampered)
    bad = SimpleNamespace(target=result.target, branch_truth_state=result.branch_truth_state, final_state=result.final_state, receipt=tampered)
    with pytest.raises(lineage.ExactInverseLineageV22Error, match="leaf path/Definition mismatch"):
        lineage.resolve_exact_inverse_lineage(bad, system_id, registries, radical, schedule)


def test_operational_persistence_rejects_non_noema_surface_before_io():
    _definition, system_id, registries, radical, schedule, result = _fixture()
    value = lineage.resolve_exact_inverse_lineage(result, system_id, registries, radical, schedule)
    with pytest.raises(lineage.ExactInverseLineageV22Error, match="fixed to /dev/shm/ciel_noema"):
        lineage.persist_exact_inverse_lineage(value, surface_root="/tmp/not-authoritative")
