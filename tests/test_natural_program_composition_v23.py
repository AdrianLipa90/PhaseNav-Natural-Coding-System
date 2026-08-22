from __future__ import annotations

from types import SimpleNamespace

import pytest

from phasenav_natural_code import DefinitionRecord
from phasenav_natural_code.composition_v23 import (
    LINEAGE_CONTRACT_ID,
    NaturalProgramV23Error,
    ReturnRegistry,
    ReturnSpec,
    admit_program_composition,
    bind_control_result_lineage,
    default_program_registry,
    resolve_natural_program,
)
from phasenav_natural_code.natural_control_v16 import resolve_natural_control

SAFETY_BIFURCATION_CID = "pncs:def:sha256:b7988497bab75a526771fa24aeca75e0182bd437fd707927cb0e78b04d360cce"
PROGRAM_A = (
    "IF (risk > 80% OR memory pressure exceeds 90%) THEN GO safety pause ELSE GO runtime continue "
    "AND THEN GO coherence recovery RETURN selected route."
)
PROGRAM_B = (
    "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN ROUTE TO safety pause ELSE GO TO runtime continue "
    "AND THEN ROUTE TO phasenav coherence recover RETURN control location"
)


def test_default_program_authority_reuses_existing_safety_bifurcation_cid():
    resolution = resolve_natural_program(PROGRAM_A, default_program_registry())
    assert resolution.composition.control_content.content_id == SAFETY_BIFURCATION_CID


def test_registered_paraphrases_have_same_composition_identity():
    registry = default_program_registry()
    left = resolve_natural_program(PROGRAM_A, registry)
    right = resolve_natural_program(PROGRAM_B, registry)
    assert left.source_text != right.source_text
    assert left.composition_id == right.composition_id
    assert left.canonical_graph == right.canonical_graph


def test_and_then_route_changes_composition_identity():
    registry = default_program_registry()
    with_step = resolve_natural_program(PROGRAM_A, registry)
    without_step = resolve_natural_program(
        "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN GO safety pause ELSE GO runtime continue RETURN selected route",
        registry,
    )
    assert with_step.composition_id != without_step.composition_id


def test_return_selector_changes_composition_identity():
    registry = default_program_registry()
    route_result = resolve_natural_program(
        "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN GO safety pause ELSE GO runtime continue RETURN selected route",
        registry,
    )
    truth_result = resolve_natural_program(
        "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN GO safety pause ELSE GO runtime continue RETURN truth state",
        registry,
    )
    assert route_result.composition_id != truth_result.composition_id


def test_operator_schedule_uses_existing_pnv_return_but_does_not_open_execution():
    resolution = resolve_natural_program(PROGRAM_A, default_program_registry())
    assert resolution.operator_schedule[-4:] == ("ORDER", "TRANSFORM", "COMPOSITION", "RETURN")
    assert resolution.composition.payload["v0_20_executable"] is False
    assert resolution.composition.payload["external_effects"] is False
    assert resolution.composition.payload["free_form_nl_execution"] is False


def test_dependency_closure_is_typed_and_deterministic():
    registry = default_program_registry()
    resolution = resolve_natural_program(PROGRAM_A, registry)
    deps = resolution.composition.dependency_ids
    assert deps[0] == SAFETY_BIFURCATION_CID
    assert deps[1].startswith("pncs:route-ref:sha256:")
    assert deps[-1].startswith("pncs:return-ref:sha256:")
    assert deps == resolve_natural_program(PROGRAM_B, registry).composition.dependency_ids


def test_program_requires_exactly_one_terminal_return():
    registry = default_program_registry()
    with pytest.raises(NaturalProgramV23Error, match="exactly one terminal RETURN"):
        resolve_natural_program(
            "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN GO safety pause ELSE GO runtime continue",
            registry,
        )
    with pytest.raises(NaturalProgramV23Error, match="exactly one terminal RETURN"):
        resolve_natural_program(
            "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN GO safety pause ELSE GO runtime continue RETURN route RETURN route",
            registry,
        )


def test_resolved_but_unregistered_control_definition_fails_closed():
    with pytest.raises(NaturalProgramV23Error, match="not registered authority"):
        resolve_natural_program(
            "IF temperature ABOVE 50 THEN GO safety pause ELSE GO runtime continue RETURN route",
            default_program_registry(),
        )


def test_explicit_registration_admits_new_control_definition():
    registry = default_program_registry()
    control = resolve_natural_control(
        "IF temperature ABOVE 50 THEN GO safety pause ELSE GO runtime continue",
        registry.controls,
    )
    registry.definitions.register(
        DefinitionRecord(alias="temperature_guard", content=control.content, provenance=("test:v0.23",))
    )
    resolution = resolve_natural_program(
        "IF temperature ABOVE 50 THEN GO safety pause ELSE GO runtime continue RETURN route",
        registry,
    )
    assert resolution.composition.control_content.content_id == control.content_id


def test_unknown_and_then_route_fails_closed():
    with pytest.raises(NaturalProgramV23Error, match="unknown internal route"):
        resolve_natural_program(
            "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN GO safety pause ELSE GO runtime continue AND THEN GO nowhere RETURN route",
            default_program_registry(),
        )


def test_and_then_accepts_only_internal_route_grammar():
    with pytest.raises(NaturalProgramV23Error, match="AND THEN accepts only"):
        resolve_natural_program(
            "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN GO safety pause ELSE GO runtime continue AND THEN ACTION filesystem.write RETURN route",
            default_program_registry(),
        )


def test_unknown_return_selector_fails_closed():
    with pytest.raises(NaturalProgramV23Error, match="unknown registered return selector"):
        resolve_natural_program(
            "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN GO safety pause ELSE GO runtime continue RETURN arbitrary literal",
            default_program_registry(),
        )


def test_return_registry_rejects_ambiguous_aliases():
    registry = ReturnRegistry()
    registry.register(ReturnSpec("result.alpha", ("same phrase",), "V0_20_RESULT"))
    with pytest.raises(NaturalProgramV23Error, match="ambiguous return alias"):
        registry.register(ReturnSpec("result.beta", ("same phrase",), "V0_20_RESULT"))


def test_result_lineage_contract_is_required_by_composition():
    resolution = resolve_natural_program(PROGRAM_A, default_program_registry())
    assert resolution.composition.payload["required_result_lineage_contract_id"] == LINEAGE_CONTRACT_ID


def _fake_lineage(definition_id: str, *, contract: str = LINEAGE_CONTRACT_ID, receipt_match: bool = True):
    lineage_id = "pncs:lineage:sha256:" + "b" * 64
    return SimpleNamespace(
        payload={"lineage_contract_id": contract},
        hierarchy=SimpleNamespace(definition_id=definition_id),
        result_id="pncs:result:sha256:" + "a" * 64,
        lineage_id=lineage_id,
        receipt={"lineage_id": lineage_id if receipt_match else "pncs:lineage:sha256:" + "c" * 64},
    )


def test_control_result_lineage_binding_preserves_v0_22_origin_without_claiming_continuations():
    resolution = resolve_natural_program(PROGRAM_A, default_program_registry())
    binding = bind_control_result_lineage(
        resolution.composition,
        _fake_lineage(resolution.composition.control_content.content_id),
    )
    assert binding.control_definition_id == resolution.composition.control_content.content_id
    assert binding.payload["binding_scope"] == "CONTROL_RESULT_ONLY"
    assert binding.payload["continuation_execution_claimed"] is False


def test_control_result_lineage_definition_mismatch_fails_closed():
    resolution = resolve_natural_program(PROGRAM_A, default_program_registry())
    with pytest.raises(NaturalProgramV23Error, match="does not match program control Definition"):
        bind_control_result_lineage(
            resolution.composition,
            _fake_lineage("pncs:def:sha256:" + "d" * 64),
        )


def test_control_result_requires_exact_v0_22_lineage_contract():
    resolution = resolve_natural_program(PROGRAM_A, default_program_registry())
    with pytest.raises(NaturalProgramV23Error, match="does not expose the v0.22 lineage contract"):
        bind_control_result_lineage(
            resolution.composition,
            _fake_lineage(resolution.composition.control_content.content_id, contract="OTHER"),
        )


def test_control_lineage_receipt_identity_mismatch_fails_closed():
    resolution = resolve_natural_program(PROGRAM_A, default_program_registry())
    with pytest.raises(NaturalProgramV23Error, match="receipt/identity mismatch"):
        bind_control_result_lineage(
            resolution.composition,
            _fake_lineage(resolution.composition.control_content.content_id, receipt_match=False),
        )


def test_live_admission_rejects_noncanonical_surface_before_io():
    resolution = resolve_natural_program(PROGRAM_A, default_program_registry())
    with pytest.raises(NaturalProgramV23Error, match="fixed to /dev/shm/ciel_noema"):
        admit_program_composition(resolution.composition, surface_root="/tmp/not-authoritative", persist=False)
