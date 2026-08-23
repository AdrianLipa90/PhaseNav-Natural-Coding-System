from __future__ import annotations

import itertools

from phasenav_natural_code.hydro_time_v27 import PhaseFlowState36
from phasenav_natural_code.natural_control_v16 import admit_internal_route, resolve_natural_control
from phasenav_natural_code.orch_orbital_v27 import AttractorReport, TotalPotential, bind_t36_state

DIM = 36
THETA = tuple(0.03 * i for i in range(DIM))
ZERO = (0.0,) * DIM
SEMANTIC_MASS = 0.2
ATTRACTORS = (
    AttractorReport("AttractorEC", 0.75, ZERO, 0.5, "EQUIV_EC"),
    AttractorReport("AttractorZS", 0.80, ZERO, 0.5, "EQUIV_ZS"),
    AttractorReport("AttractorLLMTemp", 0.0, ZERO, 0.0, "DISABLED"),
)
POTENTIAL = TotalPotential(0, 0, 0, 0, 0, 0)


def _orch_observable_projection(content_id: str) -> tuple[float, ...]:
    state = bind_t36_state(
        PhaseFlowState36(THETA),
        tick=0,
        program_content_id=content_id,
        semantic_mass=SEMANTIC_MASS,
        attractor_reports=ATTRACTORS,
        potential=POTENTIAL,
    )
    obs = state.observables
    return (
        obs.global_coherence,
        obs.defect,
        obs.holonomic_defect_real,
        obs.holonomic_defect_imag,
        obs.relational_decoherence,
        *(report.compatibility_score for report in state.attractor_reports),
        *(report.attractor_weight for report in state.attractor_reports),
    )


def _assert_equivalent_surfaces(texts: tuple[str, ...], values: dict[str, float]) -> None:
    resolutions = tuple(resolve_natural_control(text) for text in texts)
    content_ids = {resolution.content_id for resolution in resolutions}
    assert len(content_ids) == 1

    admissions = tuple(admit_internal_route(resolution, values) for resolution in resolutions)
    outcomes = {
        (admission.truth_state, admission.admitted_target, admission.epistemic_operator)
        for admission in admissions
    }
    assert len(outcomes) == 1

    projections = {
        _orch_observable_projection(resolution.content_id)
        for resolution in resolutions
    }
    assert len(projections) == 1


def test_risk_paraphrases_preserve_definition_result_and_orch_envelope():
    texts = (
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue",
        "if risk > .80 then go to safety pause else route to runtime continue",
        "IF risk exceeds 80% THEN ROUTE TO pause safety ELSE GO TO continue runtime",
    )
    _assert_equivalent_surfaces(texts, {"risk": 0.91})
    _assert_equivalent_surfaces(texts, {"risk": 0.20})


def test_case_period_and_route_aliases_are_representation_only():
    texts = (
        "IF RISK IS ABOVE 0.8 THEN GO SAFETY PAUSE ELSE GO RUNTIME CONTINUE.",
        "if risk is above 0.8 then route to pause safety else go to continue runtime",
        "IF risk > 80% THEN GO TO safety.pause ELSE ROUTE TO runtime.continue",
    )
    _assert_equivalent_surfaces(texts, {"risk": 0.8})
    _assert_equivalent_surfaces(texts, {"risk": 0.81})


def test_compound_paraphrases_preserve_definition_and_outcome():
    texts = (
        "IF risk above 0.8 AND phase coherence below 0.7 THEN GO safety.pause ELSE GO runtime.continue",
        "IF risk exceeds 80% AND phase coherence is below .70 THEN ROUTE TO pause safety ELSE GO TO continue runtime",
    )
    for risk, coherence in ((0.9, 0.6), (0.9, 0.8), (0.1, 0.6)):
        _assert_equivalent_surfaces(texts, {"risk": risk, "phase_coherence": coherence})


def test_equivalent_surface_corpus_is_stable_over_boundary_values():
    texts = (
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue",
        "IF risk > 80% THEN ROUTE TO safety pause ELSE ROUTE TO runtime continue",
    )
    for value in (0.0, 0.799999, 0.8, 0.800001, 1.0):
        _assert_equivalent_surfaces(texts, {"risk": value})


def test_missing_input_equivalence_fails_closed_to_same_chyba_state():
    texts = (
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue",
        "IF risk exceeds 80% THEN ROUTE TO pause safety ELSE GO TO continue runtime",
    )
    resolutions = tuple(resolve_natural_control(text) for text in texts)
    admissions = tuple(admit_internal_route(resolution, {}) for resolution in resolutions)
    assert {(a.truth_state, a.admitted_target, a.epistemic_operator) for a in admissions} == {
        ("UNRESOLVED", None, "CHYBA")
    }


def test_surface_equivalence_does_not_open_effect_or_routing_shortcut():
    texts = (
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue",
        "IF risk is above 80% THEN ROUTE TO safety pause ELSE ROUTE TO continue runtime",
    )
    for text in texts:
        resolution = resolve_natural_control(text)
        assert resolution.true_route.route_kind == "INTERNAL_TRANSFORM"
        assert resolution.false_route is not None
        assert resolution.false_route.route_kind == "INTERNAL_TRANSFORM"
        admission = admit_internal_route(resolution, {"risk": 0.95})
        assert admission.admitted_target == "safety.pause"
        assert admission.epistemic_operator is None


def test_paraphrase_pairwise_definition_identity_is_transitive():
    texts = (
        "IF risk above 0.8 THEN GO safety.pause ELSE GO runtime.continue",
        "if risk > .80 then go to safety pause else route to runtime continue",
        "IF risk exceeds 80% THEN ROUTE TO pause safety ELSE GO TO continue runtime",
    )
    resolutions = tuple(resolve_natural_control(text) for text in texts)
    for left, right in itertools.combinations(resolutions, 2):
        assert left.content_id == right.content_id
        assert left.canonical_graph == right.canonical_graph
        assert left.leaf_path == right.leaf_path
