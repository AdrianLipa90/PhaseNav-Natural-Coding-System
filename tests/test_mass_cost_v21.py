from __future__ import annotations

import pytest

from phasenav_natural_code import (
    CanonicalPath, Kaku, PhaseVector36, RadicalGraph, RealizationBinding, Relation,
    SemanticMassBinding, Vector36, branch_content, materialize_kaku_mass,
)
from phasenav_natural_code.cost_v21 import (
    CostRuntimeContext, GrowthBudget, MassAwareCostV21Error, MassCostRegistry,
    assess_cost_aware_distributivity, assess_cost_aware_rewrite,
    bind_kaku_mass_witness, cost_path, cost_predicate, cost_program, cost_radical,
    distributive_candidate_once, predicate_leaf_path, prove_pure_boolean_equivalence,
)
from phasenav_natural_code.surface_v09 import BranchProgram, Comparison, Predicate

BASIS = "PNCS_V21_TEST_BASIS"
LIVE_OPS = (
    "SOURCE", "ORDER", "TRANSFORM", "COMPOSITION", "DIFFERENCE", "IDENTITY",
    "CONDITION", "NEGATION",
)
RUNTIME = CostRuntimeContext("/dev/shm/ciel_noema", "a" * 64, "b" * 64, LIVE_OPS)


def _binding(*, content_digit: str, phase_index: int, phase_offset: float = 0.0) -> SemanticMassBinding:
    content_id = "pncs:def:sha256:" + content_digit * 64
    phase = PhaseVector36(tuple((phase_offset + i * 0.01) % 6.0 for i in range(36)))
    realization = RealizationBinding(
        content_id=content_id,
        phase=phase,
        basis_id=BASIS,
        derivation_id="PNCS_V21_TEST_DERIVATION",
        source_digest_sha256=content_digit * 64,
        source_locator=f"test://v0.21/{content_digit}/{phase_index}",
    )
    return SemanticMassBinding(realization=realization, phase_index=phase_index)


def _kaku(kaku_id: str, role: str, binding: SemanticMassBinding) -> Kaku:
    return materialize_kaku_mass(
        kaku_id=kaku_id,
        vector=Vector36((0.0,) * 36, BASIS),
        direction="FORWARD",
        polarity=1.0,
        role=role,
        mass_binding=binding,
    )


def _register(registry: MassCostRegistry, kaku_id: str, role: str, digit: str, phase_index: int) -> Kaku:
    binding = _binding(content_digit=digit, phase_index=phase_index, phase_offset=phase_index * 0.01)
    kaku = _kaku(kaku_id, role, binding)
    registry.register(kaku, binding)
    return kaku


def _registry_for_roles(roles: tuple[str, ...]) -> tuple[MassCostRegistry, tuple[str, ...]]:
    registry = MassCostRegistry()
    ids = []
    digits = "123456789abcdef"
    for i, role in enumerate(roles, start=1):
        kid = f"K.V21.{i}.{role}"
        _register(registry, kid, role, digits[(i - 1) % len(digits)], i)
        ids.append(kid)
    return registry, tuple(ids)


def test_mass_witness_uses_exact_v019_binding() -> None:
    binding = _binding(content_digit="1", phase_index=7)
    kaku = _kaku("K.TEST.DIFF", "DIFFERENCE", binding)
    witness = bind_kaku_mass_witness(kaku, binding)
    assert witness.operator_id == "DIFFERENCE"
    assert witness.semantic_mass == binding.semantic_mass
    assert witness.mass_binding_id == binding.mass_binding_id


def test_radical_cost_is_sum_of_bound_kaku_masses() -> None:
    b1 = _binding(content_digit="1", phase_index=1)
    b2 = _binding(content_digit="2", phase_index=2)
    k1 = _kaku("K.SOURCE", "SOURCE", b1)
    k2 = _kaku("K.IDENTITY", "IDENTITY", b2)
    radical = RadicalGraph("R.V21", BASIS)
    radical.add_kaku(k1)
    radical.add_kaku(k2)
    radical.add_relation(Relation("E.V21", k1.kaku_id, k2.kaku_id, "REL"))
    cost = cost_radical(radical, {k1.kaku_id: b1, k2.kaku_id: b2}, RUNTIME)
    assert cost.total_mass == pytest.approx(b1.semantic_mass + b2.semantic_mass)
    assert cost.node_count == 2
    assert cost.cost_payload["semantic_identity_affected"] is False


def test_path_cost_preserves_order_and_detects_repeated_kaku() -> None:
    registry = MassCostRegistry()
    k = _register(registry, "K.REPEAT", "SOURCE", "3", 3)
    path = CanonicalPath("P.V21", "DEFINITION", (k.kaku_id, k.kaku_id), ("E",), BASIS)
    cost = cost_path(path, registry, RUNTIME)
    assert cost.node_count == 2
    assert cost.unique_kaku_count == 1
    assert cost.duplicate_node_count == 1
    assert cost.duplicate_mass_units > 0


def test_program_cost_requires_exact_leaf_role_schedule() -> None:
    predicate = Predicate("comparison", (Comparison("risk", "gt", 0.8),))
    content = branch_content(BranchProgram(predicate, "safety.pause", "runtime.continue"))
    registry, ids = _registry_for_roles(content.leaf_path)
    cost = cost_program(content, ids, registry, RUNTIME)
    assert tuple(cost.cost_payload["operator_ids"]) == content.leaf_path
    assert cost.subject_id == content.content_id


def test_program_cost_rejects_role_mismatch() -> None:
    predicate = Predicate("comparison", (Comparison("risk", "gt", 0.8),))
    content = branch_content(BranchProgram(predicate, "safety.pause", None))
    registry, ids = _registry_for_roles(content.leaf_path)
    bad = list(ids)
    bad[0], bad[1] = bad[1], bad[0]
    with pytest.raises(MassAwareCostV21Error, match="operator schedule"):
        cost_program(content, tuple(bad), registry, RUNTIME)


def test_no_mass_inference_from_missing_kaku_or_cid() -> None:
    registry = MassCostRegistry()
    path = CanonicalPath("P.MISSING", "DEFINITION", ("K.UNKNOWN",), (), BASIS)
    with pytest.raises(MassAwareCostV21Error, match="missing explicit mass witness"):
        cost_path(path, registry, RUNTIME)


def test_cost_rejects_operator_absent_from_live_registry() -> None:
    registry = MassCostRegistry()
    _register(registry, "K.RETURN", "RETURN", "4", 4)
    path = CanonicalPath("P.RETURN", "DEFINITION", ("K.RETURN",), (), BASIS)
    with pytest.raises(MassAwareCostV21Error, match="absent from live PhaseNav registry"):
        cost_path(path, registry, RUNTIME)


def test_distributive_candidate_is_independently_proven_equivalent() -> None:
    a = ("comparison", "a", "gt", 0.0)
    b = ("comparison", "b", "gt", 0.0)
    c = ("comparison", "c", "gt", 0.0)
    source = ("and", a, ("or", b, c))
    target = distributive_candidate_once(source)
    evidence = prove_pure_boolean_equivalence(source, target)
    assert evidence.equivalent is True
    assert evidence.valuation_count == 8
    assert len(predicate_leaf_path(target)) > len(predicate_leaf_path(source))


def _costed_distribution():
    a = ("comparison", "a", "gt", 0.0)
    b = ("comparison", "b", "gt", 0.0)
    c = ("comparison", "c", "gt", 0.0)
    source = ("and", a, ("or", b, c))
    target = distributive_candidate_once(source)
    registry = MassCostRegistry()

    def add(kid: str, role: str, digit: str, phase_index: int) -> str:
        _register(registry, kid, role, digit, phase_index)
        return kid

    a_d = add("K.A.D", "DIFFERENCE", "1", 1)
    a_c = add("K.A.C", "CONDITION", "2", 2)
    b_d = add("K.B.D", "DIFFERENCE", "3", 3)
    b_c = add("K.B.C", "CONDITION", "4", 4)
    c_d = add("K.C.D", "DIFFERENCE", "5", 5)
    c_c = add("K.C.C", "CONDITION", "6", 6)
    m_or = add("K.M.OR", "COMPOSITION", "7", 7)
    m_and = add("K.M.AND", "COMPOSITION", "8", 8)

    source_ids = (a_d, a_c, b_d, b_c, c_d, c_c, m_or, m_and)
    target_ids = (a_d, a_c, b_d, b_c, m_and, a_d, a_c, c_d, c_c, m_and, m_or)
    source_cost = cost_predicate(source, "PRED.SOURCE", source_ids, registry, RUNTIME)
    target_cost = cost_predicate(target, "PRED.TARGET", target_ids, registry, RUNTIME)
    evidence = prove_pure_boolean_equivalence(source, target)
    return source_cost, target_cost, evidence


def test_default_zero_growth_budget_rejects_distributive_growth() -> None:
    source_cost, target_cost, evidence = _costed_distribution()
    result = assess_cost_aware_distributivity(source_cost, target_cost, evidence)
    assert result.admitted is False
    assert result.classification == "UNJUSTIFIED_GROWTH"
    assert result.unjustified_growth_detected is True


def test_explicit_sufficient_growth_budget_can_admit_equivalent_distribution() -> None:
    source_cost, target_cost, evidence = _costed_distribution()
    delta_mass_units = max(0, target_cost.total_mass_units - source_cost.total_mass_units)
    delta_nodes = max(0, target_cost.node_count - source_cost.node_count)
    budget = GrowthBudget(
        max_added_nodes=delta_nodes,
        max_added_mass_units=delta_mass_units,
        justification="explicit v0.21 distributive expansion budget",
    )
    result = assess_cost_aware_distributivity(source_cost, target_cost, evidence, budget)
    assert result.admitted is True
    assert result.classification == "BUDGETED_GROWTH"


def test_insufficient_budget_rejects_growth() -> None:
    source_cost, target_cost, evidence = _costed_distribution()
    budget = GrowthBudget(
        max_added_nodes=max(0, target_cost.node_count - source_cost.node_count - 1),
        max_added_mass_units=max(0, target_cost.total_mass_units - source_cost.total_mass_units),
        justification="intentionally insufficient node budget",
    )
    result = assess_cost_aware_distributivity(source_cost, target_cost, evidence, budget)
    assert result.admitted is False
    assert result.classification == "BUDGET_EXCEEDED"


def test_positive_growth_budget_requires_explicit_justification() -> None:
    with pytest.raises(MassAwareCostV21Error, match="explicit justification"):
        GrowthBudget(max_added_nodes=1)


def test_non_equivalent_rewrite_is_rejected_independently_of_cost() -> None:
    a = ("comparison", "a", "gt", 0.0)
    b = ("comparison", "b", "gt", 0.0)
    source = ("and", a, b)
    target = ("or", a, b)
    evidence = prove_pure_boolean_equivalence(source, target)
    source_roles = predicate_leaf_path(source)
    target_roles = predicate_leaf_path(target)
    source_registry, source_ids = _registry_for_roles(source_roles)
    target_registry, target_ids = _registry_for_roles(target_roles)
    source_cost = cost_predicate(source, "NON_EQ.S", source_ids, source_registry, RUNTIME)
    target_cost = cost_predicate(target, "NON_EQ.T", target_ids, target_registry, RUNTIME)
    assert evidence.equivalent is False
    result = assess_cost_aware_rewrite(
        source_cost,
        target_cost,
        evidence,
        GrowthBudget(100, 10**15, "large budget must not override semantics"),
    )
    assert result.admitted is False
    assert result.classification == "NON_EQUIVALENT"


def test_cost_receipt_is_deterministic_and_not_semantic_authority() -> None:
    registry = MassCostRegistry()
    k = _register(registry, "K.DET", "SOURCE", "5", 5)
    path = CanonicalPath("P.DET", "DEFINITION", (k.kaku_id,), (), BASIS)
    a = cost_path(path, registry, RUNTIME)
    b = cost_path(path, registry, RUNTIME)
    assert a.cost_id == b.cost_id
    assert a.deterministic_receipt == b.deterministic_receipt
    assert a.cost_payload["semantic_equivalence_from_cost"] is False
