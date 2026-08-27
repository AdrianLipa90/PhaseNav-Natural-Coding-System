import math
import pytest

from phasenav_natural_code.gremlin_pnv_holonomy_v01 import (
    audit_information_holonomy,
    compile_information_holonomy_loop,
    exact_state_metric,
)
from phasenav_natural_code.model import Kaku, Vector36
from phasenav_natural_code.pnv_noether_collective_holonomy_v01 import (
    NOETHER_COLLECTIVE_CONTRACT,
    NOETHER_COLLECTIVE_LOOP_ID,
    PNVNoetherCollectiveError,
    build_noether_collective_loop,
    collective_noether_binding_defect,
    make_noether_collective_state,
    noether_collective_invariants,
    noether_collective_transforms,
)


BASIS = "pncs:t36:noether-collective-test:v1"
GENERATION = "a" * 64
CONTENT_IDT = "pncs:def:sha256:" + "7" * 64
CONTENT_RFC = "pncs:def:sha256:" + "8" * 64


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


def _state(i_a=2.0):
    return make_noether_collective_state(
        D=1,
        epsilon_eb=0.0,
        theta_i_eb=math.pi,
        hbar=1.0,
        j_total=2.0 * math.pi,
        i_phi=2.0,
        i_a=i_a,
    )


def test_contract_and_semantic_loop_id_are_versioned():
    assert NOETHER_COLLECTIVE_CONTRACT == "PNCS_PNV_NOETHER_COLLECTIVE_CARRIER_V0_1"
    assert NOETHER_COLLECTIVE_LOOP_ID == "SOURCE.PHASE_NOETHER.COLLECTIVE_CARRIER.ROUNDTRIP"


def test_exact_collective_inertia_binding_closes_holonomy():
    loop = build_noether_collective_loop(
        _kaku("LAW.ROTOR", 0.1, f"rotor:{CONTENT_IDT}"),
        _kaku("LAW.NOETHER", 0.2, f"noether:{CONTENT_IDT}"),
        _kaku("LAW.RFC", 0.3, f"rfc:{CONTENT_RFC}"),
        evidence_refs=("test:noether-collective",),
    )
    compiled = _compile(loop)
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=_state(),
        transforms=noether_collective_transforms(binding_tolerance=1e-12),
        state_metric=exact_state_metric,
        metric_id="EXACT_CANONICAL_STATE",
        invariant_evaluators=noether_collective_invariants(),
    )
    assert audit.receipt["status"] == "PASS"
    assert audit.state_defect == 0.0
    assert all(row["passed"] for row in audit.invariant_results)
    assert CONTENT_IDT in audit.inverse_lineage.payload["explicit_content_ids"]
    assert CONTENT_RFC in audit.inverse_lineage.payload["explicit_content_ids"]


def test_noether_loop_orders_rotor_to_field_to_rfc_and_back():
    loop = build_noether_collective_loop(
        _kaku("LAW.ROTOR", 0.1, "rotor"),
        _kaku("LAW.NOETHER", 0.2, "noether"),
        _kaku("LAW.RFC", 0.3, "rfc"),
    )
    compiled = _compile(loop)
    assert loop.loop_id == NOETHER_COLLECTIVE_LOOP_ID
    assert [row["transform_name"] for row in compiled.receipt["transport_plan"]] == [
        "noether.resolve_rotor_carrier",
        "noether.bind_rfc_carrier",
        "noether.reconstruct_rotor_input",
    ]


def test_exact_binding_derives_p_phi_q_theta_and_epsilon_n():
    transforms = noether_collective_transforms(binding_tolerance=1e-12)
    resolved = transforms["noether.resolve_rotor_carrier"](_state())
    assert math.isclose(resolved["P_Phi_EB"], math.pi, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(resolved["phase_rate"], math.pi / 2.0, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(resolved["Q_theta"], math.pi, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(resolved["H_Phi_EB"], math.pi**2 / 4.0, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(resolved["epsilon_N_EB"], math.pi / 4.0, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(
        resolved["epsilon_N_EB"],
        resolved["H_Phi_EB"] / resolved["Q_theta"],
        rel_tol=0.0,
        abs_tol=1e-15,
    )
    assert resolved["Delta_I"] == 0.0


def test_inertia_mismatch_exposes_exact_binding_defect_and_fails_closed():
    state = _state(i_a=2.5)
    expected = abs(2.5 / 2.0 - 1.0)
    assert math.isclose(collective_noether_binding_defect(state), expected, rel_tol=0.0, abs_tol=1e-15)
    transforms = noether_collective_transforms(binding_tolerance=1e-12)
    resolved = transforms["noether.resolve_rotor_carrier"](state)
    with pytest.raises(PNVNoetherCollectiveError, match="inertia binding defect"):
        transforms["noether.bind_rfc_carrier"](resolved)


def test_explicit_nonzero_binding_tolerance_keeps_epsilon_typed_by_q_theta():
    state = _state(i_a=2.000001)
    transforms = noether_collective_transforms(binding_tolerance=1e-6)
    resolved = transforms["noether.resolve_rotor_carrier"](state)
    bound = transforms["noether.bind_rfc_carrier"](resolved)
    reconstructed = transforms["noether.reconstruct_rotor_input"](bound)
    assert reconstructed == state
    assert 0.0 < resolved["Delta_I"] < 1e-6
    assert math.isclose(
        resolved["epsilon_N_EB"],
        resolved["H_Phi_EB"] / resolved["Q_theta"],
        rel_tol=0.0,
        abs_tol=1e-15,
    )
    assert bound["Q_RFC"] == resolved["Q_theta"]
    assert bound["epsilon_Q_candidate"] == resolved["epsilon_N_EB"]


def test_tampered_rfc_candidate_fails_reverse_audit():
    transforms = noether_collective_transforms(binding_tolerance=1e-12)
    resolved = transforms["noether.resolve_rotor_carrier"](_state())
    bound = transforms["noether.bind_rfc_carrier"](resolved)
    tampered = {**bound, "Q_RFC": bound["Q_RFC"] * 1.01}
    with pytest.raises(PNVNoetherCollectiveError, match="reverse Noether audit"):
        transforms["noether.reconstruct_rotor_input"](tampered)


def test_positive_rotor_carrier_gate_fails_closed():
    state = make_noether_collective_state(
        D=1,
        epsilon_eb=0.0,
        theta_i_eb=2.0,
        hbar=1.0,
        j_total=1.0,
        i_phi=2.0,
        i_a=2.0,
    )
    transforms = noether_collective_transforms()
    with pytest.raises(PNVNoetherCollectiveError, match="positive rotor carrier"):
        transforms["noether.resolve_rotor_carrier"](state)


def test_noether_loop_exposes_required_invariants():
    loop = build_noether_collective_loop(
        _kaku("LAW.ROTOR", 0.1, "rotor"),
        _kaku("LAW.NOETHER", 0.2, "noether"),
        _kaku("LAW.RFC", 0.3, "rfc"),
    )
    assert [item.invariant_id for item in loop.invariants] == [
        "SOURCE.EULER_CLOSURE_SECTOR",
        "SOURCE.ROTOR_KINETIC_CHARGE",
        "SOURCE.NOETHER_FINITE_CHARGE",
        "SOURCE.ROTOR_PHASE_ENERGY",
        "SOURCE.NOETHER_ENERGY_PER_CHARGE",
        "SOURCE.NOETHER_INERTIA_BINDING_DEFECT",
    ]
