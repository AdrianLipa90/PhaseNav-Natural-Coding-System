import math
import pytest

from phasenav_natural_code.gremlin_pnv_holonomy_v01 import (
    audit_information_holonomy,
    compile_information_holonomy_loop,
    exact_state_metric,
)
from phasenav_natural_code.model import Kaku, Vector36
from phasenav_natural_code.pnv_noether_rfc_slice_holonomy_v01 import (
    NOETHER_RFC_SLICE_CONTRACT,
    NOETHER_RFC_SLICE_LOOP_ID,
    PNVNoetherRFCSliceError,
    build_noether_rfc_slice_carrier_loop,
    make_noether_rfc_slice_state,
    noether_rfc_slice_defects,
    noether_rfc_slice_invariants,
    noether_rfc_slice_transforms,
)


BASIS = "pncs:t36:noether-rfc-slice-test:v1"
GENERATION = "b" * 64
CONTENT_IDT = "pncs:def:sha256:" + "9" * 64
CONTENT_RFC = "pncs:def:sha256:" + "a" * 64


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


def _state(*, j_theta=None, v_theta=None, j_q=None, v_q=None, normal_q="future"):
    return make_noether_rfc_slice_state(
        slice_id_theta="Sigma.0",
        slice_id_q="Sigma.0",
        normal_theta="future",
        normal_q=normal_q,
        cell_ids_theta=("C0", "C1", "C2"),
        cell_ids_q=("C0", "C1", "C2"),
        j_theta=j_theta or (1.0, 2.0, 3.0),
        v_theta=v_theta or (0.5, 1.0, 1.5),
        j_q=j_q or (1.0, 2.0, 3.0),
        v_q=v_q or (0.5, 1.0, 1.5),
    )


def test_contract_and_loop_id_are_versioned():
    assert NOETHER_RFC_SLICE_CONTRACT == "PNCS_PNV_NOETHER_RFC_SLICE_CARRIER_V0_1"
    assert NOETHER_RFC_SLICE_LOOP_ID == "SOURCE.NOETHER_RFC.SLICE_CARRIER.ROUNDTRIP"


def test_exact_local_binding_closes_holonomy_and_inverse_lineage():
    loop = build_noether_rfc_slice_carrier_loop(
        _kaku("LAW.NOETHER.SLICE", 0.1, f"noether:{CONTENT_IDT}"),
        _kaku("LAW.RFC.SLICE", 0.2, f"rfc:{CONTENT_RFC}"),
        evidence_refs=("test:noether-rfc-slice",),
    )
    compiled = _compile(loop)
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=_state(),
        transforms=noether_rfc_slice_transforms(),
        state_metric=exact_state_metric,
        metric_id="EXACT_CANONICAL_STATE",
        invariant_evaluators=noether_rfc_slice_invariants(),
    )
    assert audit.receipt["status"] == "PASS"
    assert audit.state_defect == 0.0
    assert all(row["passed"] for row in audit.invariant_results)
    assert CONTENT_IDT in audit.inverse_lineage.payload["explicit_content_ids"]
    assert CONTENT_RFC in audit.inverse_lineage.payload["explicit_content_ids"]


def test_transport_order_is_noether_to_rfc_and_back():
    loop = build_noether_rfc_slice_carrier_loop(
        _kaku("LAW.NOETHER.SLICE", 0.1, "noether"),
        _kaku("LAW.RFC.SLICE", 0.2, "rfc"),
    )
    compiled = _compile(loop)
    assert [row["transform_name"] for row in compiled.receipt["transport_plan"]] == [
        "slice.bind_noether_to_rfc",
        "slice.reconstruct_noether_input",
    ]


def test_exact_binding_has_zero_three_defects_and_equal_profiles():
    state = _state()
    defects = noether_rfc_slice_defects(state)
    assert defects == {
        "Delta_J": 0.0,
        "Delta_V": 0.0,
        "Delta_Sigma": 0.0,
        "defect_bound_margin": 0.0,
    }
    bound = noether_rfc_slice_transforms()["slice.bind_noether_to_rfc"](state)
    assert bound["Q_theta"] == bound["Q_Sigma"]
    assert bound["p_theta"] == bound["p_Q"]
    assert math.isclose(sum(bound["p_theta"]), 1.0, rel_tol=0.0, abs_tol=1e-15)


def test_equal_integrated_charge_with_local_cancellation_fails_closed():
    state = _state(
        j_theta=(1.0, 1.0, 1.0),
        v_theta=(1.0, 1.0, 1.0),
        j_q=(1.5, 0.5, 1.0),
        v_q=(1.0, 1.0, 1.0),
    )
    defects = noether_rfc_slice_defects(state)
    assert defects["Delta_Sigma"] == 0.0
    assert defects["Delta_J"] > 0.0
    with pytest.raises(PNVNoetherRFCSliceError, match="local current defect"):
        noether_rfc_slice_transforms()["slice.bind_noether_to_rfc"](state)


def test_measure_mismatch_fails_closed_independently_of_current_values():
    state = _state(v_q=(0.6, 0.9, 1.5))
    defects = noether_rfc_slice_defects(state)
    assert defects["Delta_J"] == 0.0
    assert defects["Delta_V"] > 0.0
    with pytest.raises(PNVNoetherRFCSliceError, match="measure defect"):
        noether_rfc_slice_transforms()["slice.bind_noether_to_rfc"](state)


def test_triangle_bound_is_exposed_for_nonidentical_candidate():
    state = _state(
        j_q=(1.1, 1.9, 3.1),
        v_q=(0.55, 0.95, 1.45),
    )
    defects = noether_rfc_slice_defects(state)
    assert defects["Delta_Sigma"] <= defects["Delta_J"] + defects["Delta_V"] + 1e-15
    assert defects["defect_bound_margin"] == 0.0


def test_small_explicit_tolerances_can_admit_measured_candidate_and_reverse_exactly():
    state = _state(j_q=(1.0 + 1e-8, 2.0, 3.0))
    defects = noether_rfc_slice_defects(state)
    transforms = noether_rfc_slice_transforms(
        current_tolerance=1e-7,
        measure_tolerance=1e-12,
        charge_tolerance=1e-7,
    )
    bound = transforms["slice.bind_noether_to_rfc"](state)
    reconstructed = transforms["slice.reconstruct_noether_input"](bound)
    assert reconstructed == state
    assert 0.0 < defects["Delta_J"] < 1e-7


def test_slice_orientation_and_cell_identity_mismatches_fail_closed():
    with pytest.raises(PNVNoetherRFCSliceError, match="normal orientations"):
        noether_rfc_slice_defects(_state(normal_q="past"))

    state = make_noether_rfc_slice_state(
        slice_id_theta="Sigma.0",
        slice_id_q="Sigma.0",
        normal_theta="future",
        normal_q="future",
        cell_ids_theta=("C0", "C1"),
        cell_ids_q=("C1", "C0"),
        j_theta=(1.0, 2.0),
        v_theta=(1.0, 1.0),
        j_q=(1.0, 2.0),
        v_q=(1.0, 1.0),
    )
    with pytest.raises(PNVNoetherRFCSliceError, match="cell IDs/ordering"):
        noether_rfc_slice_defects(state)


def test_tampered_bound_candidate_fails_reverse_audit():
    transforms = noether_rfc_slice_transforms()
    bound = transforms["slice.bind_noether_to_rfc"](_state())
    tampered = {**bound, "Q_Sigma": bound["Q_Sigma"] * 1.01}
    with pytest.raises(PNVNoetherRFCSliceError, match="changed before reverse slice audit"):
        transforms["slice.reconstruct_noether_input"](tampered)
