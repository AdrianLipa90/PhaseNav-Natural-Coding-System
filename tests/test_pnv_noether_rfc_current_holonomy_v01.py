import pytest

from phasenav_natural_code.gremlin_pnv_holonomy_v01 import (
    audit_information_holonomy,
    compile_information_holonomy_loop,
    exact_state_metric,
)
from phasenav_natural_code.model import Kaku, Vector36
from phasenav_natural_code.pnv_noether_rfc_current_holonomy_v01 import (
    NOETHER_RFC_CURRENT_CONTRACT,
    NOETHER_RFC_CURRENT_LOOP_ID,
    PNVNoetherRFCCurrentError,
    build_noether_rfc_current_loop,
    make_noether_rfc_current_state,
    noether_rfc_current_invariants,
    noether_rfc_current_transforms,
)


BASIS = "pncs:t36:noether-rfc-current-test:v1"
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


def _state(*, j_theta=(1.0, 2.0, 3.0), j_q=(1.0, 2.0, 3.0), side_flux=0.0):
    return make_noether_rfc_current_state(
        slice_id="SIGMA.TEST.001",
        noether_measure_id="measure:shared:v1",
        rfc_measure_id="measure:shared:v1",
        noether_cell_ids=("c0", "c1", "c2"),
        rfc_cell_ids=("c0", "c1", "c2"),
        noether_volumes=(1.0, 2.0, 1.0),
        rfc_volumes=(1.0, 2.0, 1.0),
        j_theta_cells=j_theta,
        j_q_cells=j_q,
        side_flux=side_flux,
    )


def _loop():
    return build_noether_rfc_current_loop(
        _kaku("LAW.NOETHER.LOCAL", 0.1, f"noether:{CONTENT_IDT}"),
        _kaku("LAW.MEASURE.SHARED", 0.2, f"measure:{CONTENT_IDT}"),
        _kaku("LAW.RFC.LOCAL", 0.3, f"rfc:{CONTENT_RFC}"),
        evidence_refs=("test:noether-rfc-current",),
    )


def test_contract_and_semantic_loop_id_are_versioned():
    assert NOETHER_RFC_CURRENT_CONTRACT == "PNCS_PNV_NOETHER_RFC_CURRENT_BINDING_V0_1"
    assert NOETHER_RFC_CURRENT_LOOP_ID == "SOURCE.PHASE_NOETHER.RFC_CONSERVED_CURRENT.ROUNDTRIP"


def test_exact_local_current_binding_closes_holonomy():
    loop = _loop()
    compiled = _compile(loop)
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=_state(),
        transforms=noether_rfc_current_transforms(),
        state_metric=exact_state_metric,
        metric_id="EXACT_CANONICAL_STATE",
        invariant_evaluators=noether_rfc_current_invariants(),
    )
    assert audit.receipt["status"] == "PASS"
    assert audit.state_defect == 0.0
    assert all(row["passed"] for row in audit.invariant_results)
    assert CONTENT_IDT in audit.inverse_lineage.payload["explicit_content_ids"]
    assert CONTENT_RFC in audit.inverse_lineage.payload["explicit_content_ids"]


def test_loop_transport_order_is_noether_measure_rfc_roundtrip():
    compiled = _compile(_loop())
    assert [row["transform_name"] for row in compiled.receipt["transport_plan"]] == [
        "noether_rfc.resolve_common_measure",
        "noether_rfc.bind_conserved_current",
        "noether_rfc.reconstruct_pair",
    ]


def test_equal_total_charge_does_not_hide_local_current_mismatch():
    state = make_noether_rfc_current_state(
        slice_id="SIGMA.TEST.002",
        noether_measure_id="measure:shared:v1",
        rfc_measure_id="measure:shared:v1",
        noether_cell_ids=("c0", "c1"),
        rfc_cell_ids=("c0", "c1"),
        noether_volumes=(1.0, 1.0),
        rfc_volumes=(1.0, 1.0),
        j_theta_cells=(1.0, 3.0),
        j_q_cells=(2.0, 2.0),
    )
    transforms = noether_rfc_current_transforms()
    resolved = transforms["noether_rfc.resolve_common_measure"](state)
    assert resolved["Delta_total_charge"] == 0.0
    assert resolved["Delta_local_current"] > 0.0
    with pytest.raises(PNVNoetherRFCCurrentError, match="local-current defect"):
        transforms["noether_rfc.bind_conserved_current"](resolved)


def test_total_charge_mismatch_fails_closed_even_with_common_partition():
    transforms = noether_rfc_current_transforms(local_current_tolerance=1.0)
    resolved = transforms["noether_rfc.resolve_common_measure"](
        _state(j_q=(1.0, 2.0, 4.0))
    )
    assert resolved["Delta_total_charge"] > 0.0
    with pytest.raises(PNVNoetherRFCCurrentError, match="total-charge defect"):
        transforms["noether_rfc.bind_conserved_current"](resolved)


def test_measure_id_mismatch_fails_before_current_binding():
    state = make_noether_rfc_current_state(
        slice_id="SIGMA.TEST.003",
        noether_measure_id="measure:noether:v1",
        rfc_measure_id="measure:rfc:v1",
        noether_cell_ids=("c0",),
        rfc_cell_ids=("c0",),
        noether_volumes=(1.0,),
        rfc_volumes=(1.0,),
        j_theta_cells=(1.0,),
        j_q_cells=(1.0,),
    )
    with pytest.raises(PNVNoetherRFCCurrentError, match="measure IDs differ"):
        noether_rfc_current_transforms()["noether_rfc.resolve_common_measure"](state)


def test_cell_partition_mismatch_fails_before_current_binding():
    state = make_noether_rfc_current_state(
        slice_id="SIGMA.TEST.004",
        noether_measure_id="measure:shared:v1",
        rfc_measure_id="measure:shared:v1",
        noether_cell_ids=("c0", "c1"),
        rfc_cell_ids=("c0", "c2"),
        noether_volumes=(1.0, 1.0),
        rfc_volumes=(1.0, 1.0),
        j_theta_cells=(1.0, 1.0),
        j_q_cells=(1.0, 1.0),
    )
    with pytest.raises(PNVNoetherRFCCurrentError, match="cell partitions differ"):
        noether_rfc_current_transforms()["noether_rfc.resolve_common_measure"](state)


def test_volume_measure_defect_is_measured_and_fails_closed():
    state = make_noether_rfc_current_state(
        slice_id="SIGMA.TEST.005",
        noether_measure_id="measure:shared:v1",
        rfc_measure_id="measure:shared:v1",
        noether_cell_ids=("c0", "c1"),
        rfc_cell_ids=("c0", "c1"),
        noether_volumes=(1.0, 1.0),
        rfc_volumes=(1.0, 1.1),
        j_theta_cells=(1.0, 1.0),
        j_q_cells=(1.0, 1.0),
    )
    with pytest.raises(PNVNoetherRFCCurrentError, match="common-measure defect"):
        noether_rfc_current_transforms()["noether_rfc.resolve_common_measure"](state)


def test_nonzero_side_flux_fails_conservation_gate():
    transforms = noether_rfc_current_transforms()
    resolved = transforms["noether_rfc.resolve_common_measure"](_state(side_flux=0.01))
    with pytest.raises(PNVNoetherRFCCurrentError, match="side-flux defect"):
        transforms["noether_rfc.bind_conserved_current"](resolved)


def test_tampered_bound_total_fails_reverse_audit():
    transforms = noether_rfc_current_transforms()
    resolved = transforms["noether_rfc.resolve_common_measure"](_state())
    bound = transforms["noether_rfc.bind_conserved_current"](resolved)
    tampered = {**bound, "Q_RFC": bound["Q_RFC"] * 1.01}
    with pytest.raises(PNVNoetherRFCCurrentError, match="reverse current audit"):
        transforms["noether_rfc.reconstruct_pair"](tampered)


def test_loop_exposes_measure_local_total_and_flux_invariants():
    loop = _loop()
    assert [item.invariant_id for item in loop.invariants] == [
        "SOURCE.NOETHER_TOTAL_CHARGE",
        "SOURCE.RFC_TOTAL_CHARGE",
        "SOURCE.COMMON_MEASURE_DEFECT",
        "SOURCE.LOCAL_CURRENT_BINDING_DEFECT",
        "SOURCE.TOTAL_CHARGE_BINDING_DEFECT",
        "SOURCE.SIDE_FLUX_DEFECT",
    ]
