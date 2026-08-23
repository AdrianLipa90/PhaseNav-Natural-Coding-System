from __future__ import annotations

from pathlib import Path


PNV = Path(__file__).resolve().parents[1] / "native" / "experimental" / "PNCS_ORCHORBITAL_HARVEST_HARDENING_V0_29.pnv"


def lines():
    return [line.strip() for line in PNV.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]


def test_native_contract_is_read_only_chyba():
    rows = lines()
    assert rows[:3] == ["PNV 1", "EPISTEMIC CHYBA", "MODE READ_ONLY"]


def test_native_operator_ids_are_unique():
    ops = [row.split()[1] for row in lines() if row.startswith("OP ")]
    assert len(ops) == len(set(ops))


def test_native_required_hardening_operators_present():
    text = PNV.read_text(encoding="utf-8")
    for op in (
        "ORH.ENTITY_PROJECT",
        "ORH.PACKAGE_ADMISSION",
        "ORH.SEMANTIC_ACTION_AUDIT",
        "ORH.LEAK_RECEIPT",
        "ORH.GEOMETRY_PROJECT",
    ):
        assert f"OP {op} " in text


def test_native_authority_boundaries_are_explicitly_closed():
    text = PNV.read_text(encoding="utf-8")
    for boundary in (
        "ORH.IDENTITY_BOUNDARY CONDITION identity_authority equals false",
        "ORH.ROUTING_BOUNDARY CONDITION routing_feedback_opened equals false",
        "ORH.EFFECT_BOUNDARY CONDITION effect_authority equals false",
        "ORH.LEAK_PROPAGATION_BOUNDARY CONDITION propagation_opened equals false",
        "ORH.SPHERE_LIFECYCLE_BOUNDARY CONDITION split_merge_elevate_opened equals false",
        "ORH.RENDERER_BOUNDARY CONDITION renderer_authority equals false",
    ):
        assert boundary in text


def test_native_paths_emit_only_read_only_hardening_surfaces():
    emitted = [row.split()[1] for row in lines() if row.startswith("EMIT ")]
    assert emitted == [
        "PATH.ORH.LINEAGE_TO_ENTITY",
        "PATH.ORH.PACKAGE_HARDENING",
        "PATH.ORH.STATE_TO_OPERATIONAL_GEOMETRY",
    ]
