import math
import pytest

from phasenav_natural_code.gremlin_pnv_holonomy_v01 import (
    audit_information_holonomy,
    compile_information_holonomy_loop,
    exact_state_metric,
)
from phasenav_natural_code.model import Kaku, Vector36
from phasenav_natural_code.pnv_gauge_covariant_phase_pullback_v01 import (
    GAUGE_COVARIANT_PULLBACK_CONTRACT,
    GAUGE_COVARIANT_PULLBACK_LOOP_ID,
    PNVGaugeCovariantPhasePullbackError,
    build_gauge_covariant_phase_pullback_loop,
    gauge_covariant_phase_pullback_defects,
    gauge_covariant_phase_pullback_invariants,
    gauge_covariant_phase_pullback_transforms,
    make_gauge_covariant_phase_pullback_state,
)


BASIS = "pncs:t36:gauge-pullback-test:v1"
GENERATION = "c" * 64
CONTENT_FIELD = "pncs:def:sha256:" + "d" * 64
CONTENT_ROTOR = "pncs:def:sha256:" + "e" * 64


def _kaku(kaku_id: str, seed: float, role: str) -> Kaku:
    return Kaku(
        kaku_id=kaku_id,
        vector=Vector36(tuple(seed + i / 100.0 for i in range(36)), BASIS),
        semantic_mass=1.0 + seed,
        direction="FORWARD",
        polarity=1.0,
        role=role,
        phase=tuple((seed + i) / 36.0 for i in range(36)),
    )


def _compile(loop):
    return compile_information_holonomy_loop(
        loop,
        generation_binding=GENERATION,
        identity="ZOSIA_NOEMA_FIRST",
        authority="USER_EXPLICIT_AUTHORING",
    )


def _state(**overrides):
    data = dict(
        field_bundle_id="bundle:phase-u1",
        rotor_bundle_id="bundle:phase-u1",
        field_phase_patch_id="patch:north",
        rotor_phase_patch_id="patch:north",
        field_connection_id="connection:ABE:v1",
        rotor_connection_id="connection:ABE:v1",
        field_measure_id="measure:h",
        rotor_measure_id="measure:h",
        field_cell_ids=("cell:0", "cell:1"),
        rotor_cell_ids=("cell:0", "cell:1"),
        phase_gradients=(0.4, -0.2),
        connection_components=(0.1, 0.5),
        gauge_shift_components=(0.3, -0.4),
        trajectory_velocity=(1.0, 0.0),
        field_normal_rate=0.5,
        rotor_rate=0.5,
        amplitudes=(1.0, 1.0),
        volumes=(0.5, 0.5),
        i_phi=2.0,
    )
    data.update(overrides)
    return make_gauge_covariant_phase_pullback_state(**data)


def test_contract_and_loop_id_are_versioned():
    assert GAUGE_COVARIANT_PULLBACK_CONTRACT == "PNCS_PNV_GAUGE_COVARIANT_PHASE_PULLBACK_V0_1"
    assert GAUGE_COVARIANT_PULLBACK_LOOP_ID == "SOURCE.PHASE.NOETHER.GAUGE_COVARIANT_PULLBACK.ROUNDTRIP"


def test_exact_common_u1_pullback_has_zero_binding_defects():
    defects = gauge_covariant_phase_pullback_defects(_state())
    assert defects["Delta_gauge"] <= 1e-15
    assert defects["Delta_I_reduction"] == 0.0
    assert defects["Delta_rate"] == 0.0
    assert defects["Delta_normal"] == 0.0
    assert defects["Delta_Q"] == 0.0
    assert defects["Delta_epsilon"] == 0.0
    assert defects["Delta_factorization"] == 0.0
    assert defects["Delta_action"] == 0.0


def test_admitted_plus_sign_is_gauge_invariant_and_opposite_sign_is_discriminated():
    transforms = gauge_covariant_phase_pullback_transforms(tolerance=1e-12)
    bound = transforms["gauge_phase.bind_common_u1_generator"](_state())
    assert bound["Delta_gauge"] <= 1e-15
    assert bound["gauge_probe_norm"] > 0.0
    assert bound["opposite_sign_residual"] > 0.0
    assert bound["transformed_phase_gradients"] == pytest.approx([0.7, -0.6])
    assert bound["transformed_connection_components"] == pytest.approx([-0.2, 0.9])


def test_pullback_reconstructs_same_rotor_rate_and_moment_map():
    transforms = gauge_covariant_phase_pullback_transforms(tolerance=1e-12)
    bound = transforms["gauge_phase.bind_common_u1_generator"](_state())
    assert bound["field_pullback_rate"] == pytest.approx(0.5)
    assert bound["field_normal_rate"] == pytest.approx(0.5)
    assert bound["rotor_rate"] == pytest.approx(0.5)
    assert bound["I_A"] == pytest.approx(2.0)
    assert bound["I_phi"] == pytest.approx(2.0)
    assert bound["Q_theta"] == pytest.approx(1.0)
    assert bound["P_Phi"] == pytest.approx(1.0)
    assert bound["epsilon_N"] == pytest.approx(0.25)
    assert bound["half_rotor_rate"] == pytest.approx(0.25)


def test_rate_mismatch_is_visible_before_generator_promotion():
    state = _state(rotor_rate=0.55)
    defects = gauge_covariant_phase_pullback_defects(state)
    assert defects["Delta_rate"] > 0.0
    assert defects["Delta_Q"] > 0.0
    with pytest.raises(PNVGaugeCovariantPhasePullbackError, match="Delta_rate"):
        gauge_covariant_phase_pullback_transforms(tolerance=0.0)["gauge_phase.bind_common_u1_generator"](state)


def test_normal_projection_mismatch_is_visible_even_with_matching_pullback_and_rotor_rate():
    state = _state(field_normal_rate=0.45)
    defects = gauge_covariant_phase_pullback_defects(state)
    assert defects["Delta_rate"] == 0.0
    assert defects["Delta_normal"] > 0.0
    assert defects["Delta_Q"] > 0.0
    with pytest.raises(PNVGaugeCovariantPhasePullbackError, match="Delta_normal"):
        gauge_covariant_phase_pullback_transforms(tolerance=0.0)["gauge_phase.bind_common_u1_generator"](state)


def test_inertia_mismatch_is_not_hidden_by_matching_rates():
    state = _state(i_phi=2.2)
    defects = gauge_covariant_phase_pullback_defects(state)
    assert defects["Delta_rate"] == 0.0
    assert defects["Delta_normal"] == 0.0
    assert defects["Delta_I_reduction"] > 0.0
    assert defects["Delta_Q"] > 0.0


def test_moment_map_factorization_identity_holds_off_exact_gate():
    state = _state(i_phi=2.2, field_normal_rate=0.45, rotor_rate=0.55)
    transforms = gauge_covariant_phase_pullback_transforms(tolerance=1.0)
    bound = transforms["gauge_phase.bind_common_u1_generator"](state)
    assert math.isclose(
        bound["moment_map_ratio"],
        bound["factorized_moment_map_ratio"],
        rel_tol=1e-15,
        abs_tol=1e-15,
    )
    assert bound["Delta_factorization"] <= 1e-15


def test_bundle_patch_connection_measure_and_support_mismatches_fail_closed():
    cases = (
        ("rotor_bundle_id", "bundle:other", "bundle IDs differ"),
        ("rotor_phase_patch_id", "patch:other", "phase-patch IDs differ"),
        ("rotor_connection_id", "connection:other", "connection IDs differ"),
        ("rotor_measure_id", "measure:other", "measure IDs differ"),
        ("rotor_cell_ids", ("cell:1", "cell:0"), "collective supports differ"),
    )
    for field, value, message in cases:
        with pytest.raises(PNVGaugeCovariantPhasePullbackError, match=message):
            gauge_covariant_phase_pullback_defects(_state(**{field: value}))


def test_nontrivial_gauge_probe_and_positive_rates_fail_closed():
    with pytest.raises(PNVGaugeCovariantPhasePullbackError, match="nontrivial gauge probe"):
        _state(gauge_shift_components=(0.0, 0.0))
    with pytest.raises(PNVGaugeCovariantPhasePullbackError, match="field_normal_rate must be strictly positive"):
        _state(field_normal_rate=0.0)
    with pytest.raises(PNVGaugeCovariantPhasePullbackError, match="rotor_rate must be strictly positive"):
        _state(rotor_rate=0.0)


def test_tampered_moment_map_coordinate_fails_reverse_audit():
    transforms = gauge_covariant_phase_pullback_transforms(tolerance=1e-12)
    bound = transforms["gauge_phase.bind_common_u1_generator"](_state())
    tampered = {**bound, "Q_theta": bound["Q_theta"] * 1.01}
    with pytest.raises(PNVGaugeCovariantPhasePullbackError, match="Q_theta changed"):
        transforms["gauge_phase.reconstruct_pullback_input"](tampered)


def test_exact_pullback_closes_information_holonomy_and_inverse_lineage():
    loop = build_gauge_covariant_phase_pullback_loop(
        _kaku("LAW.GAUGE.FIELD", 0.1, f"field:{CONTENT_FIELD}"),
        _kaku("LAW.GAUGE.ROTOR", 0.2, f"rotor:{CONTENT_ROTOR}"),
        evidence_refs=(
            "IDT:formalism/01AC_gauge_covariant_phase_pullback_noether_generator.md",
            "RFC:formalism/RFN1B2M_GAUGE_COVARIANT_PHASE_PULLBACK_NOETHER_GENERATOR.md",
        ),
    )
    compiled = _compile(loop)
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=_state(),
        transforms=gauge_covariant_phase_pullback_transforms(tolerance=1e-12),
        state_metric=exact_state_metric,
        metric_id="EXACT_CANONICAL_STATE",
        invariant_evaluators=gauge_covariant_phase_pullback_invariants(),
    )
    assert audit.receipt["status"] == "PASS"
    assert audit.state_defect == 0.0
    assert all(row["passed"] for row in audit.invariant_results)
    assert CONTENT_FIELD in audit.inverse_lineage.payload["explicit_content_ids"]
    assert CONTENT_ROTOR in audit.inverse_lineage.payload["explicit_content_ids"]


def test_loop_exposes_gauge_rate_normal_moment_map_and_action_invariants():
    loop = build_gauge_covariant_phase_pullback_loop(
        _kaku("LAW.GAUGE.FIELD", 0.1, "field"),
        _kaku("LAW.GAUGE.ROTOR", 0.2, "rotor"),
    )
    ids = [item.invariant_id for item in loop.invariants]
    assert "SOURCE.GAUGE_INVARIANCE_DEFECT" in ids
    assert "SOURCE.GAUGE_SIGN_DISCRIMINATION" in ids
    assert "SOURCE.RATE_BINDING_DEFECT" in ids
    assert "SOURCE.NORMAL_PROJECTION_DEFECT" in ids
    assert "SOURCE.MOMENT_MAP_DEFECT" in ids
    assert "SOURCE.MOMENT_MAP_FACTORIZATION_DEFECT" in ids
    assert "SOURCE.ACTION_REDUCTION_DEFECT" in ids
    assert "SOURCE.EPSILON_PULLBACK_DEFECT" in ids
