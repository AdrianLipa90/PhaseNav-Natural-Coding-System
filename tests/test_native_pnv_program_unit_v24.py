from __future__ import annotations

import hashlib

import pytest

from phasenav_natural_code.composition_v23 import (
    default_program_registry,
    resolve_natural_program,
)
from phasenav_natural_code.program_unit_v24 import (
    EXPECTED_LINEAGE_CONTRACT_ID,
    NativeProgramUnit,
    NativeProgramUnitRegistry,
    NativeProgramV24Error,
    build_native_program_unit,
    parse_native_program_unit,
    render_native_program_unit,
)

PROGRAM_A = (
    "IF (risk > 80% OR memory pressure exceeds 90%) THEN GO safety pause ELSE GO runtime continue "
    "AND THEN GO coherence recovery RETURN selected route."
)
PROGRAM_B = (
    "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) THEN ROUTE TO safety pause ELSE GO TO runtime continue "
    "AND THEN ROUTE TO phasenav coherence recover RETURN control location"
)
EXPECTED_COMPOSITION_ID = (
    "pncs:composition:sha256:5b3710e6c8bf34d3754e7144ca139beb70205ea20b2fa504ef63c710c177cd57"
)
EXPECTED_PROGRAM_ID = (
    "pncs:program:sha256:572660a1046975c57e01f7e402677f1e4ca845e51bca1bee6517e0d86b35c4d7"
)
EXPECTED_PNV_SHA256 = "012b41c149b1ba518d9be65d34d7ab6605b92500e8768e23c11abff7330a77fb"


def _composition(text: str = PROGRAM_A):
    return resolve_natural_program(text, default_program_registry()).composition


def _unit() -> NativeProgramUnit:
    return NativeProgramUnit.from_composition(_composition())


def _registry() -> tuple[NativeProgramUnit, NativeProgramUnitRegistry, str]:
    unit = _unit()
    registry = NativeProgramUnitRegistry()
    registry.register_unit(unit)
    return unit, registry, render_native_program_unit(unit)


def test_v023_witness_promotes_to_known_v024_program_identity():
    composition = _composition()
    assert composition.composition_id == EXPECTED_COMPOSITION_ID
    assert NativeProgramUnit.from_composition(composition).program_id == EXPECTED_PROGRAM_ID


def test_registered_paraphrases_promote_to_same_program_identity():
    left = NativeProgramUnit.from_composition(_composition(PROGRAM_A))
    right = NativeProgramUnit.from_composition(_composition(PROGRAM_B))
    assert left.program_id == right.program_id
    assert left.semantic_payload == right.semantic_payload


def test_program_identity_is_distinct_from_composition_identity():
    unit = _unit()
    assert unit.program_id != unit.composition_id
    assert unit.program_id.startswith("pncs:program:sha256:")


def test_dependency_closure_is_content_addressed_and_deterministic():
    unit = _unit()
    assert unit.dependency_closure[0].kind == "COMPOSITION"
    assert unit.dependency_closure[0].content_id == EXPECTED_COMPOSITION_ID
    assert unit.dependency_closure_sha256 == _unit().dependency_closure_sha256
    assert unit.dependency_occurrences_sha256 == _unit().dependency_occurrences_sha256


def test_dependency_occurrences_preserve_program_order():
    unit = _unit()
    assert [x.kind for x in unit.dependency_occurrences] == [
        "CONTROL_DEFINITION",
        "ROUTE_REF",
        "RETURN_REF",
    ]
    assert unit.dependency_occurrences[-1].content_id == unit.return_ref_id


def test_operator_schedule_is_exact_and_terminates_in_existing_return():
    unit = _unit()
    assert len(unit.operator_schedule) == 15
    assert unit.operator_schedule[-4:] == (
        "ORDER",
        "TRANSFORM",
        "COMPOSITION",
        "RETURN",
    )


def test_export_is_deterministic_and_has_known_sha256():
    text = render_native_program_unit(_unit())
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == EXPECTED_PNV_SHA256
    assert text.endswith("\n")


def test_import_export_round_trip_is_byte_identical():
    unit, registry, text = _registry()
    parsed = parse_native_program_unit(text, registry)
    assert parsed.unit == unit
    assert parsed.text == text
    assert render_native_program_unit(parsed.unit) == text


def test_serialized_text_cannot_create_unregistered_program_semantics():
    _unit_value, registry, text = _registry()
    unknown = "pncs:program:sha256:" + "f" * 64
    tampered = text.replace(EXPECTED_PROGRAM_ID, unknown)
    with pytest.raises(NativeProgramV24Error, match="not registered authority"):
        parse_native_program_unit(tampered, registry)


def test_tampered_effect_boundary_fails_closed():
    _unit_value, registry, text = _registry()
    tampered = text.replace("EXTERNAL_EFFECTS FALSE", "EXTERNAL_EFFECTS TRUE")
    with pytest.raises(NativeProgramV24Error, match="not canonical"):
        parse_native_program_unit(tampered, registry)


def test_reordered_dependency_rows_fail_closed():
    _unit_value, registry, text = _registry()
    lines = text.splitlines()
    indexes = [i for i, line in enumerate(lines) if line.startswith("DEPENDENCY ")]
    lines[indexes[1]], lines[indexes[2]] = lines[indexes[2]], lines[indexes[1]]
    with pytest.raises(NativeProgramV24Error, match="not canonical"):
        parse_native_program_unit("\n".join(lines) + "\n", registry)


def test_extra_clause_fails_closed():
    _unit_value, registry, text = _registry()
    tampered = text.replace("END PROGRAM_UNIT\n", "UNKNOWN CLAUSE\nEND PROGRAM_UNIT\n")
    with pytest.raises(NativeProgramV24Error, match="not canonical"):
        parse_native_program_unit(tampered, registry)


def test_program_unit_preserves_v022_lineage_requirement():
    unit = _unit()
    assert unit.lineage_contract_id == EXPECTED_LINEAGE_CONTRACT_ID
    assert (
        unit.semantic_payload["required_result_lineage_contract_id"]
        == EXPECTED_LINEAGE_CONTRACT_ID
    )


def test_program_unit_does_not_open_execution_or_effects():
    payload = _unit().semantic_payload
    assert payload["native_execution_opened"] is False
    assert payload["return_execution_opened"] is False
    assert payload["external_effects"] is False
    assert payload["free_form_nl_execution"] is False
    assert payload["static_runtime_fallback"] is False


def test_live_build_rejects_noncanonical_surface_before_io():
    with pytest.raises(NativeProgramV24Error, match="fixed to /dev/shm/ciel_noema"):
        build_native_program_unit(
            _composition(),
            surface_root="/tmp/not-authoritative",
            persist=False,
        )
