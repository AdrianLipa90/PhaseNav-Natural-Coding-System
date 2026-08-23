from __future__ import annotations

import math

import pytest

from phasenav_natural_code.orch_hardening_v29 import (
    CHART_BLOCH,
    CHART_POINCARE,
    EntityRecordProjection,
    FactAuditCounts,
    InertLeakReceipt,
    OperationalGeometryProjection,
    OrchHardeningV29Error,
    PackageEvidenceRefs,
    SemanticActionAuditReceipt,
    SemanticActionWeights,
    evaluate_package_admission,
)


def pid(kind: str, digit: str = "a") -> str:
    return f"pncs:{kind}:sha256:{digit * 64}"


def entity(**overrides):
    data = dict(
        canonical_id=pid("result", "1"),
        object_type="ARTIFACT",
        lineage_id=pid("lineage", "2"),
        hierarchy_path_id=pid("hierarchy-lineage", "3"),
        definition_id=pid("def", "4"),
        definition_radical_binding_id=pid("def-radical-binding", "5"),
        radical_id="R.HARDENING.V29",
        kaku_ids=("K.A", "K.B"),
        sphere_id="sphere.process.0",
        parent_sphere_id="sphere.system.0",
        orbit_index=3,
        phase=0.25,
        w_ec=0.1,
        w_zs=0.2,
        w_rel=0.3,
        w_red=0.4,
        epistemic_status="CHYBA",
        dependency_links=(pid("dependency", "6"),),
        extra_provenance_links=(pid("receipt", "7"),),
    )
    data.update(overrides)
    return EntityRecordProjection(**data)


def test_entity_projection_is_deterministic_and_preserves_canonical_identity():
    a = entity()
    b = entity()
    assert a.projection_id == b.projection_id
    assert a.payload["canonical_id"] == pid("result", "1")
    assert a.projection_id != a.canonical_id


def test_entity_projection_has_no_authority_flags():
    payload = entity().payload
    assert payload["identity_authority"] is False
    assert payload["routing_authority"] is False
    assert payload["effect_authority"] is False


def test_entity_projection_provenance_binds_lineage_hierarchy_and_radical_binding():
    obj = entity()
    assert obj.provenance_links[:3] == (
        obj.lineage_id,
        obj.hierarchy_path_id,
        obj.definition_radical_binding_id,
    )


def test_entity_projection_allows_repeated_kaku_occurrences():
    obj = entity(kaku_ids=("K.A", "K.A", "K.B"))
    assert obj.kaku_ids == ("K.A", "K.A", "K.B")


@pytest.mark.parametrize(
    "field,bad",
    [
        ("canonical_id", "not-an-id"),
        ("lineage_id", pid("result", "2")),
        ("hierarchy_path_id", pid("result", "3")),
        ("definition_id", pid("result", "4")),
        ("definition_radical_binding_id", pid("result", "5")),
    ],
)
def test_entity_projection_rejects_wrong_identity_types(field, bad):
    with pytest.raises(OrchHardeningV29Error):
        entity(**{field: bad})


def test_entity_projection_rejects_empty_kaku_schedule():
    with pytest.raises(OrchHardeningV29Error, match="kaku_ids"):
        entity(kaku_ids=())


def test_entity_projection_rejects_path_like_object_type():
    with pytest.raises(OrchHardeningV29Error, match="object_type"):
        entity(object_type="src/file.py")


def test_entity_projection_passes_through_exact_mass_binding():
    obj = entity(semantic_mass=0.123, mass_binding_id=pid("mass-binding", "8"))
    assert obj.payload["semantic_mass"] == 0.123
    assert obj.mass_binding_id in obj.provenance_links


def test_entity_projection_requires_mass_and_binding_together():
    with pytest.raises(OrchHardeningV29Error, match="together"):
        entity(semantic_mass=0.1)
    with pytest.raises(OrchHardeningV29Error, match="together"):
        entity(mass_binding_id=pid("mass-binding", "8"))


def complete_evidence(**overrides):
    data = dict(
        schema_receipt_id=pid("schema-receipt", "1"),
        test_receipt_id=pid("test-receipt", "2"),
        metrics_receipt_id=pid("metrics-receipt", "3"),
        replay_receipt_id=pid("replay-receipt", "4"),
    )
    data.update(overrides)
    return PackageEvidenceRefs(**data)


def test_package_admission_requires_exact_four_slot_closure():
    receipt = evaluate_package_admission(pid("program", "a"), complete_evidence())
    assert receipt.admitted is True
    assert receipt.evidence.missing == ()
    assert receipt.admission_id.startswith("pncs:package-admission:sha256:")


@pytest.mark.parametrize(
    "field,missing",
    [
        ("schema_receipt_id", "SCHEMA"),
        ("test_receipt_id", "TESTS"),
        ("metrics_receipt_id", "METRICS"),
        ("replay_receipt_id", "REPLAYABILITY"),
    ],
)
def test_package_admission_rejects_each_missing_slot(field, missing):
    receipt = evaluate_package_admission(pid("program", "a"), complete_evidence(**{field: None}))
    assert receipt.admitted is False
    assert receipt.evidence.missing == (missing,)


def test_package_admission_malformed_evidence_fails_closed():
    with pytest.raises(OrchHardeningV29Error):
        complete_evidence(test_receipt_id="receipt")


def test_package_admission_is_measurement_boundary_only():
    payload = evaluate_package_admission(pid("program", "a"), complete_evidence()).payload
    assert payload["routing_authority"] is False
    assert payload["effect_authority"] is False


def weights():
    return SemanticActionWeights(1.0, 2.0, 3.0, 4.0, 5.0)


def test_semantic_action_audit_exact_arithmetic():
    counts = FactAuditCounts(10, false_count=1, unmarked_count=2, omit_count=1, hallucination_count=0)
    receipt = SemanticActionAuditReceipt(
        source_artifact_id=pid("result", "a"),
        path_length=2.0,
        phase_transport_cost=0.5,
        relational_defect=0.25,
        structural_truth_penalty=0.125,
        counts=counts,
        weights=weights(),
    )
    expected_online = 1.0 * 2.0 + 2.0 * 0.5 + 3.0 * 0.25 + 4.0 * 0.125
    assert receipt.online_action == pytest.approx(expected_online)
    assert counts.audit_truth_penalty == pytest.approx(0.4)
    assert receipt.full_action == pytest.approx(expected_online + 5.0 * 0.4)


def test_semantic_action_audit_is_deterministic():
    kwargs = dict(
        source_artifact_id=pid("result", "a"),
        path_length=1.0,
        phase_transport_cost=2.0,
        relational_defect=3.0,
        structural_truth_penalty=4.0,
        counts=FactAuditCounts(5, 1, 1, 0, 0),
        weights=weights(),
    )
    assert SemanticActionAuditReceipt(**kwargs).audit_id == SemanticActionAuditReceipt(**kwargs).audit_id


@pytest.mark.parametrize("field", ["path_length", "phase_transport_cost", "relational_defect", "structural_truth_penalty"])
def test_semantic_action_rejects_negative_measurements(field):
    kwargs = dict(
        source_artifact_id=pid("result", "a"),
        path_length=1.0,
        phase_transport_cost=1.0,
        relational_defect=1.0,
        structural_truth_penalty=1.0,
        counts=FactAuditCounts(1),
        weights=weights(),
    )
    kwargs[field] = -0.1
    with pytest.raises(OrchHardeningV29Error):
        SemanticActionAuditReceipt(**kwargs)


def test_semantic_action_rejects_nonfinite_weight():
    with pytest.raises(OrchHardeningV29Error):
        SemanticActionWeights(1.0, 1.0, math.inf, 1.0, 1.0)


def test_fact_audit_requires_positive_denominator():
    with pytest.raises(OrchHardeningV29Error, match="fact_count"):
        FactAuditCounts(0)


def test_fact_audit_rejects_channel_count_above_fact_count():
    with pytest.raises(OrchHardeningV29Error):
        FactAuditCounts(2, hallucination_count=3)


def test_semantic_action_is_measurement_only():
    receipt = SemanticActionAuditReceipt(
        pid("result", "a"), 0.0, 0.0, 0.0, 0.0, FactAuditCounts(1), weights()
    )
    assert receipt.payload["measurement_only"] is True
    assert receipt.payload["routing_feedback_opened"] is False
    assert receipt.payload["effect_authority"] is False


def test_inert_leak_is_exact_negative_holonomic_defect():
    receipt = InertLeakReceipt(pid("sigma", "1"), "sphere.0", "sphere.parent", 3.0, -4.0)
    assert receipt.epsilon_real == -3.0
    assert receipt.epsilon_imag == 4.0
    assert receipt.leak_amplitude == 5.0
    assert receipt.leak_phase == pytest.approx(math.atan2(4.0, -3.0) % (2.0 * math.pi))


def test_inert_leak_allows_exact_zero_defect():
    receipt = InertLeakReceipt(pid("sigma", "1"), "sphere.0", None, 0.0, 0.0)
    assert receipt.leak_amplitude == 0.0
    assert receipt.leak_phase == 0.0


def test_inert_leak_keeps_dynamic_boundaries_closed():
    payload = InertLeakReceipt(pid("sigma", "1"), "sphere.0", "sphere.parent", 1.0, 2.0).payload
    assert payload["propagation_opened"] is False
    assert payload["parent_mutation_opened"] is False
    assert payload["split_merge_elevate_opened"] is False
    assert payload["routing_feedback_opened"] is False


def test_poincare_projection_accepts_inside_unit_disk():
    obj = entity()
    projection = OperationalGeometryProjection(pid("sigma", "9"), obj.projection_id, CHART_POINCARE, (0.3, 0.4))
    assert projection.payload["base_relational_manifold"] == "M_rel"
    assert projection.payload["chart_role"] == "OPERATIONAL_PROJECTION"


@pytest.mark.parametrize("coords", [(1.0, 0.0), (0.8, 0.8)])
def test_poincare_projection_rejects_boundary_or_outside(coords):
    with pytest.raises(OrchHardeningV29Error):
        OperationalGeometryProjection(pid("sigma", "9"), entity().projection_id, CHART_POINCARE, coords)


def test_bloch_projection_accepts_unit_ball_boundary():
    projection = OperationalGeometryProjection(pid("sigma", "9"), entity().projection_id, CHART_BLOCH, (1.0, 0.0, 0.0))
    assert projection.payload["chart_role"] == "LOCAL_REDUCED_INSPECTION"


def test_bloch_projection_rejects_outside_unit_ball():
    with pytest.raises(OrchHardeningV29Error):
        OperationalGeometryProjection(pid("sigma", "9"), entity().projection_id, CHART_BLOCH, (1.0, 0.1, 0.0))


def test_geometry_projection_has_no_semantic_routing_or_renderer_authority():
    payload = OperationalGeometryProjection(pid("sigma", "9"), entity().projection_id, CHART_POINCARE, (0.0, 0.0)).payload
    assert payload["semantic_identity_authority"] is False
    assert payload["routing_authority"] is False
    assert payload["renderer_authority"] is False
