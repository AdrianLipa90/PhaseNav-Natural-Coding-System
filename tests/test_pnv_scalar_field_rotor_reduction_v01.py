import math
import pytest

from phasenav_natural_code.gremlin_pnv_holonomy_v01 import (
    audit_information_holonomy,
    compile_information_holonomy_loop,
    exact_state_metric,
)
from phasenav_natural_code.model import Kaku, Vector36
from phasenav_natural_code.pnv_scalar_field_rotor_reduction_v01 import (
    SCALAR_FIELD_ROTOR_CONTRACT,
    SCALAR_FIELD_ROTOR_LOOP_ID,
    PNVScalarFieldRotorReductionError,
    build_scalar_field_rotor_reduction_loop,
    make_scalar_field_rotor_state,
    scalar_field_rotor_reduction_defects,
    scalar_field_rotor_reduction_invariants,
    scalar_field_rotor_reduction_transforms,
)


BASIS = "pncs:t36:scalar-field-rotor-test:v1"
GENERATION = "b" * 64
CONTENT_FIELD = "pncs:def:sha256:" + "9" * 64
CONTENT_ROTOR = "pncs:def:sha256:" + "a" * 64


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


def _state(*, i_phi=2.0, phase_mode="mode:chi", rate_id="rate:D_tau_chi", measure="measure:h", rotor_cells=None):
    field_cells = ("cell:0", "cell:1")
    return make_scalar_field_rotor_state(
        field_phase_mode_id=phase_mode,
        rotor_phase_mode_id=phase_mode,
        field_rate_id=rate_id,
        rotor_rate_id=rate_id,
        field_measure_id=measure,
        rotor_measure_id=measure,
        field_cell_ids=field_cells,
        rotor_cell_ids=field_cells if rotor_cells is None else rotor_cells,
        amplitudes=(1.0, 1.0),
        volumes=(0.5, 0.5),
        d_tau_chi=3.0,
        i_phi=i_phi,
        j_i=0.25,
    )


def test_contract_and_loop_id_are_versioned():
    assert SCALAR_FIELD_ROTOR_CONTRACT == "PNCS_PNV_SCALAR_FIELD_ROTOR_INERTIA_REDUCTION_V0_1"
    assert SCALAR_FIELD_ROTOR_LOOP_ID == "SOURCE.PHASE_NOETHER.ROTOR_INERTIA.REDUCTION.ROUNDTRIP"


def test_exact_collective_reduction_has_zero_defects_and_half_rate_epsilon():
    state = _state(i_phi=2.0)
    transforms = scalar_field_rotor_reduction_transforms(reduction_tolerance=0.0)
    bound = transforms["scalar_field.bind_rotor_inertia"](state)
    assert bound["I_A"] == 2.0
    assert bound["I_phi"] == 2.0
    assert bound["field_phase_coefficient"] == 1.0
    assert bound["rotor_phase_coefficient"] == 1.0
    assert bound["Q_theta"] == 6.0
    assert bound["P_Phi"] == 6.0
    assert bound["H_Phi"] == 9.0
    assert bound["epsilon_N"] == 1.5
    assert bound["half_phase_rate"] == 1.5
    assert bound["Delta_I_reduction"] == 0.0
    assert bound["Delta_coefficient"] == 0.0
    assert bound["Delta_Q_reduction"] == 0.0
    assert bound["Delta_epsilon_reduction"] == 0.0
    assert bound["Delta_identity_residual"] == 0.0


def test_inertia_carrier_and_epsilon_defects_are_the_same_coordinate():
    state = _state(i_phi=2.2)
    defects = scalar_field_rotor_reduction_defects(state)
    expected = 0.1
    assert math.isclose(defects["Delta_I_reduction"], expected, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(defects["Delta_coefficient"], expected, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(defects["Delta_Q_reduction"], expected, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(defects["Delta_epsilon_reduction"], expected, rel_tol=0.0, abs_tol=1e-15)
    assert defects["Delta_identity_residual"] <= 1e-15


def test_mismatched_inertia_fails_closed_at_zero_tolerance():
    transforms = scalar_field_rotor_reduction_transforms(reduction_tolerance=0.0)
    with pytest.raises(PNVScalarFieldRotorReductionError, match="inertia reduction defect"):
        transforms["scalar_field.bind_rotor_inertia"](_state(i_phi=2.000001))


def test_explicit_nonzero_tolerance_roundtrips_independent_i_phi():
    state = _state(i_phi=2.000001)
    transforms = scalar_field_rotor_reduction_transforms(reduction_tolerance=1e-6)
    bound = transforms["scalar_field.bind_rotor_inertia"](state)
    reconstructed = transforms["scalar_field.reconstruct_reduction_input"](bound)
    assert reconstructed == state
    assert 0.0 < bound["Delta_I_reduction"] < 1e-6
    assert math.isclose(bound["Delta_Q_reduction"], bound["Delta_I_reduction"], rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(bound["Delta_epsilon_reduction"], bound["Delta_I_reduction"], rel_tol=0.0, abs_tol=1e-15)


def test_phase_mode_mismatch_fails_before_reduction():
    state = _state()
    state["rotor_phase_mode_id"] = "mode:other"
    with pytest.raises(PNVScalarFieldRotorReductionError, match="phase-mode IDs differ"):
        scalar_field_rotor_reduction_defects(state)


def test_covariant_rate_identity_mismatch_fails_before_reduction():
    state = _state()
    state["rotor_rate_id"] = "rate:other"
    with pytest.raises(PNVScalarFieldRotorReductionError, match="covariant-rate IDs differ"):
        scalar_field_rotor_reduction_defects(state)


def test_measure_and_collective_support_mismatch_fail_closed():
    state = _state()
    state["rotor_measure_id"] = "measure:other"
    with pytest.raises(PNVScalarFieldRotorReductionError, match="measure IDs differ"):
        scalar_field_rotor_reduction_defects(state)

    support = _state(rotor_cells=("cell:1", "cell:0"))
    with pytest.raises(PNVScalarFieldRotorReductionError, match="collective supports differ"):
        scalar_field_rotor_reduction_defects(support)


def test_tampered_derived_coordinate_fails_reverse_audit():
    transforms = scalar_field_rotor_reduction_transforms(reduction_tolerance=0.0)
    bound = transforms["scalar_field.bind_rotor_inertia"](_state())
    tampered = {**bound, "epsilon_N": bound["epsilon_N"] * 1.01}
    with pytest.raises(PNVScalarFieldRotorReductionError, match="epsilon_N changed"):
        transforms["scalar_field.reconstruct_reduction_input"](tampered)


def test_exact_reduction_closes_full_information_holonomy_and_lineage():
    loop = build_scalar_field_rotor_reduction_loop(
        _kaku("LAW.FIELD", 0.1, f"field:{CONTENT_FIELD}"),
        _kaku("LAW.ROTOR", 0.2, f"rotor:{CONTENT_ROTOR}"),
        evidence_refs=("IDT:formalism/01AB_scalar_field_rotor_inertia_reduction.md", "RFC:formalism/RFN1B2L_SCALAR_FIELD_ROTOR_INERTIA_REDUCTION.md"),
    )
    compiled = _compile(loop)
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=_state(),
        transforms=scalar_field_rotor_reduction_transforms(reduction_tolerance=0.0),
        state_metric=exact_state_metric,
        metric_id="EXACT_CANONICAL_STATE",
        invariant_evaluators=scalar_field_rotor_reduction_invariants(),
    )
    assert audit.receipt["status"] == "PASS"
    assert audit.state_defect == 0.0
    assert all(row["passed"] for row in audit.invariant_results)
    assert CONTENT_FIELD in audit.inverse_lineage.payload["explicit_content_ids"]
    assert CONTENT_ROTOR in audit.inverse_lineage.payload["explicit_content_ids"]


def test_loop_exposes_coefficient_inertia_carrier_and_epsilon_invariants():
    loop = build_scalar_field_rotor_reduction_loop(
        _kaku("LAW.FIELD", 0.1, "field"),
        _kaku("LAW.ROTOR", 0.2, "rotor"),
    )
    ids = [item.invariant_id for item in loop.invariants]
    assert "SOURCE.FIELD_PHASE_COEFFICIENT" in ids
    assert "SOURCE.ROTOR_PHASE_COEFFICIENT" in ids
    assert "SOURCE.INERTIA_REDUCTION_DEFECT" in ids
    assert "SOURCE.CARRIER_REDUCTION_DEFECT" in ids
    assert "SOURCE.EPSILON_REDUCTION_DEFECT" in ids
    assert "SOURCE.REDUCTION_DEFECT_IDENTITY_RESIDUAL" in ids
