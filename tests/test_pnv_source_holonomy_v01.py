import math
import pytest

from phasenav_natural_code.gremlin_pnv_holonomy_v01 import (
    audit_information_holonomy,
    compile_information_holonomy_loop,
    exact_state_metric,
)
from phasenav_natural_code.model import Kaku, Vector36
from phasenav_natural_code.pnv_source_holonomy_v01 import (
    SOURCE_HOLONOMY_CONTRACT,
    PNVSourceHolonomyError,
    build_carrier_normalization_loop,
    build_epsilon_source_loop,
    build_euler_phase_intention_loop,
    build_q0_occupation_loop,
    carrier_normalization_invariants,
    carrier_normalization_transforms,
    epsilon_source_invariants,
    epsilon_source_transforms,
    euler_phase_intention_invariants,
    euler_phase_intention_transforms,
    make_current_density_state,
    make_euler_phase_intention_state,
    make_extensive_carrier_state,
    q0_occupation_invariants,
    q0_occupation_transforms,
)


BASIS = "pncs:t36:source-holonomy-test:v1"
CONTENT_IDT = "pncs:def:sha256:" + "5" * 64
CONTENT_RFC = "pncs:def:sha256:" + "6" * 64
GENERATION = "f" * 64


def _kaku(kaku_id: str, seed: float, role: str) -> Kaku:
    return Kaku(
        kaku_id=kaku_id,
        vector=Vector36(tuple(seed + i / 100.0 for i in range(36)), BASIS),
        semantic_mass=0.5 + seed,
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


def test_source_holonomy_contract_is_versioned():
    assert SOURCE_HOLONOMY_CONTRACT == "PNCS_PNV_SOURCE_HOLONOMY_LOOPS_V0_1"


def test_carrier_normalization_roundtrip_closes_exactly_and_preserves_invariants():
    extensive = _kaku("LAW.RFC.Q", 0.1, f"source_extensive:{CONTENT_RFC}")
    normalized = _kaku("LAW.IDT.P", 0.2, f"source_normalized:{CONTENT_IDT}")
    loop = build_carrier_normalization_loop(extensive, normalized, evidence_refs=("test:Q_to_p",))
    compiled = _compile(loop)
    initial = make_extensive_carrier_state([1.0, 2.0, 5.0])
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=initial,
        transforms=carrier_normalization_transforms(),
        state_metric=exact_state_metric,
        metric_id="EXACT_CANONICAL_STATE",
        invariant_evaluators=carrier_normalization_invariants(),
    )
    assert audit.receipt["status"] == "PASS"
    assert audit.state_defect == 0.0
    assert all(row["passed"] for row in audit.invariant_results)
    assert CONTENT_IDT in audit.inverse_lineage.payload["explicit_content_ids"]
    assert CONTENT_RFC in audit.inverse_lineage.payload["explicit_content_ids"]
    assert [row["transform_name"] for row in compiled.receipt["transport_plan"]] == [
        "carrier.normalize_profile",
        "carrier.reconstruct_extensive",
    ]


def test_normalization_loop_exposes_idt_rfc_law_frame_domains():
    loop = build_carrier_normalization_loop(
        _kaku("LAW.RFC.Q", 0.1, "rfc"),
        _kaku("LAW.IDT.P", 0.2, "idt"),
    )
    assert [node.domain for node in loop.nodes] == ["RFC", "IDT"]
    assert [node.law_id for node in loop.nodes] == [
        "LAW.RFC.CARRIER_EXTENSIVE",
        "LAW.IDT.NORMALIZED_PROFILE",
    ]


def test_positive_source_gate_rejects_zero_total():
    with pytest.raises(PNVSourceHolonomyError, match="Q_total > 0"):
        make_extensive_carrier_state([0.0, 0.0])


def test_q0_conditional_occupation_roundtrip_closes_exactly():
    extensive = _kaku("LAW.RFC.Q", 0.1, f"source_extensive:{CONTENT_RFC}")
    occupation = _kaku("LAW.Q0.N", 0.2, "conditional:q0")
    loop = build_q0_occupation_loop(extensive, occupation, evidence_refs=("gate:q0:OPEN",))
    compiled = _compile(loop)
    initial = make_extensive_carrier_state([2.0, 4.0, 10.0])
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=initial,
        transforms=q0_occupation_transforms(2.0),
        state_metric=exact_state_metric,
        metric_id="EXACT_CANONICAL_STATE",
        invariant_evaluators=q0_occupation_invariants(),
    )
    assert audit.receipt["status"] == "PASS"
    assert audit.state_defect == 0.0
    assert audit.invariant_results[0]["invariant_id"] == "SOURCE.TOTAL_Q"
    assert "gate:q0:CONDITIONAL" in loop.evidence_refs


def test_q0_parameter_must_be_positive():
    with pytest.raises(PNVSourceHolonomyError, match="q0 must be strictly positive"):
        q0_occupation_transforms(0.0)


def test_epsilon_source_roundtrip_closes_exactly_for_explicit_normalization():
    current = _kaku("LAW.JQ", 0.1, f"current:{CONTENT_IDT}")
    density = _kaku("LAW.RHOQ", 0.2, f"source_density:{CONTENT_RFC}")
    loop = build_epsilon_source_loop(current, density, evidence_refs=("gate:epsilon_Q:OPEN",))
    compiled = _compile(loop)
    initial = make_current_density_state([1.0, -2.0, 4.0])
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=initial,
        transforms=epsilon_source_transforms(8.0, c_light=2.0),
        state_metric=exact_state_metric,
        metric_id="EXACT_CANONICAL_STATE",
        invariant_evaluators=epsilon_source_invariants(),
    )
    assert audit.receipt["status"] == "PASS"
    assert audit.state_defect == 0.0
    assert audit.invariant_results[0]["passed"] is True
    assert CONTENT_IDT in audit.inverse_lineage.payload["explicit_content_ids"]
    assert CONTENT_RFC in audit.inverse_lineage.payload["explicit_content_ids"]
    assert "gate:epsilon_Q:CONDITIONAL" in loop.evidence_refs


def test_epsilon_parameter_must_be_positive():
    with pytest.raises(PNVSourceHolonomyError, match="epsilon_Q must be strictly positive"):
        epsilon_source_transforms(0.0)


def test_euler_closed_charge_energy_roundtrip_closes_exactly():
    closure = _kaku("LAW.EULER", 0.31, "euler_closure")
    charge = _kaku("LAW.JI", 0.32, f"phase_charge:{CONTENT_IDT}")
    energy = _kaku("LAW.HPHI", 0.33, f"rotor_energy:{CONTENT_RFC}")
    loop = build_euler_phase_intention_loop(
        closure,
        charge,
        energy,
        evidence_refs=("source:Euler_Berry", "source:Phase_Intention_Hamiltonian"),
    )
    compiled = _compile(loop)
    initial = make_euler_phase_intention_state(
        D=1,
        epsilon_eb=0.0,
        phi_ab=math.pi / 2.0,
        phi_berry=math.pi / 4.0,
        phi_euler=math.pi / 4.0,
        theta_prior=0.0,
        hbar=1.0,
        j_total=2.0 * math.pi,
        i_phi=2.0,
    )
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=initial,
        transforms=euler_phase_intention_transforms(),
        state_metric=exact_state_metric,
        metric_id="EXACT_CANONICAL_STATE",
        invariant_evaluators=euler_phase_intention_invariants(),
    )
    assert audit.receipt["status"] == "PASS"
    assert audit.state_defect == 0.0
    assert all(row["passed"] for row in audit.invariant_results)
    assert CONTENT_IDT in audit.inverse_lineage.payload["explicit_content_ids"]
    assert CONTENT_RFC in audit.inverse_lineage.payload["explicit_content_ids"]


def test_euler_loop_orders_closure_before_charge_before_rotor_energy():
    loop = build_euler_phase_intention_loop(
        _kaku("LAW.EULER", 0.31, "euler"),
        _kaku("LAW.JI", 0.32, "charge"),
        _kaku("LAW.HPHI", 0.33, "energy"),
    )
    compiled = _compile(loop)
    assert [row["transform_name"] for row in compiled.receipt["transport_plan"]] == [
        "euler.resolve_intention_charge",
        "rotor.derive_energy_per_charge",
        "rotor.reconstruct_euler_input",
    ]
    assert [item.invariant_id for item in loop.invariants] == [
        "SOURCE.EULER_CLOSURE_SECTOR",
        "SOURCE.INTENTION_ACTION_CHARGE",
        "SOURCE.ROTOR_PHASE_ENERGY",
        "SOURCE.ENERGY_PER_ACTION_CHARGE",
    ]


def test_euler_loop_derives_expected_epsilon_and_effective_floquet_step():
    state = make_euler_phase_intention_state(
        D=1,
        epsilon_eb=0.0,
        phi_ab=math.pi / 2.0,
        phi_berry=math.pi / 4.0,
        phi_euler=math.pi / 4.0,
        theta_prior=0.0,
        hbar=1.0,
        j_total=2.0 * math.pi,
        i_phi=2.0,
    )
    transforms = euler_phase_intention_transforms()
    charged = transforms["euler.resolve_intention_charge"](state)
    energized = transforms["rotor.derive_energy_per_charge"](charged)
    assert math.isclose(charged["theta_I_EB"], math.pi, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(charged["J_I_EB"], math.pi, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(energized["H_Phi_EB"], math.pi**2 / 4.0, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(energized["epsilon_I_EB"], math.pi / 4.0, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(energized["Delta_tau_eff_EB"], 4.0 / math.pi, rel_tol=0.0, abs_tol=1e-15)


def test_euler_loop_fails_closed_for_zero_or_negative_action_charge():
    transforms = euler_phase_intention_transforms()
    state = make_euler_phase_intention_state(
        D=0,
        epsilon_eb=0.0,
        phi_ab=0.0,
        phi_berry=0.0,
        phi_euler=0.0,
        theta_prior=0.0,
        hbar=1.0,
        j_total=1.0,
        i_phi=1.0,
    )
    with pytest.raises(PNVSourceHolonomyError, match="action charge must be positive"):
        transforms["euler.resolve_intention_charge"](state)


def test_euler_loop_fails_closed_for_rotor_degeneracy():
    transforms = euler_phase_intention_transforms()
    state = make_euler_phase_intention_state(
        D=1,
        epsilon_eb=0.0,
        phi_ab=math.pi,
        phi_berry=0.0,
        phi_euler=0.0,
        theta_prior=0.0,
        hbar=1.0,
        j_total=math.pi,
        i_phi=1.0,
    )
    charged = transforms["euler.resolve_intention_charge"](state)
    with pytest.raises(PNVSourceHolonomyError, match="rotor phase energy must be positive"):
        transforms["rotor.derive_energy_per_charge"](charged)


def test_source_loop_rejects_mixed_basis_before_compilation():
    left = _kaku("LAW.LEFT", 0.1, "left")
    right = Kaku(
        kaku_id="LAW.RIGHT",
        vector=Vector36(tuple(0.2 + i / 100.0 for i in range(36)), "pncs:other:basis"),
        semantic_mass=0.7,
        direction="FORWARD",
        polarity=1.0,
        role="right",
        phase=tuple((0.2 + i) / 36.0 for i in range(36)),
    )
    with pytest.raises(PNVSourceHolonomyError, match="share one exact PNCS basis"):
        build_carrier_normalization_loop(left, right)
