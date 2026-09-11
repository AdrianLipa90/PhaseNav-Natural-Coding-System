import numpy as np

from phasenav_natural_code.phasenav_promotion_geometry_v01 import (
    bell_state_via_promotion,
    bloch_promotion,
    candidate_manifest,
    complex_intertwiner_defect,
    controlled_unitary,
    gate_real_contract,
    lift_local_gate,
    metric_defect,
    promotion_matrix,
    qgt_trace,
    relational_wedge_two_qubit,
    segre_determinant_two_qubit,
)


def _gates():
    x = np.array([[0, 1], [1, 0]], dtype=complex)
    y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    z = np.diag([1, -1]).astype(complex)
    h = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    s = np.diag([1, 1j]).astype(complex)
    t = np.diag([1, np.exp(1j * np.pi / 4)]).astype(complex)
    return {"X": x, "Y": y, "Z": z, "H": h, "S": s, "T": t}


def test_candidate_authority_is_fail_closed():
    status = candidate_manifest()
    assert status["promotion_state"] == "CANDIDATE_ONLY"
    assert status["runtime_execution_authority"] is False
    assert status["canon_write_authority"] is False
    assert status["epistemic"] == "CHYBA"


def test_metric_and_complex_structure_are_preserved():
    p = promotion_matrix(1 / np.sqrt(2), 1j / np.sqrt(2), 2)
    assert np.allclose(metric_defect(p), 0.0, atol=1e-12)
    assert np.allclose(complex_intertwiner_defect(p), 0.0, atol=1e-12)


def test_standard_single_qubit_gates_preserve_G_and_J():
    for name, gate in _gates().items():
        contract = gate_real_contract(gate)
        assert contract["unitary"], name
        assert contract["real_orthogonal"], name
        assert contract["commutes_with_J"], name


def test_local_gate_promotion_round_trip():
    p = promotion_matrix(1 / np.sqrt(2), 1j / np.sqrt(2), 2)
    for name, gate in _gates().items():
        assert np.allclose(lift_local_gate(gate) @ p, p @ gate, atol=1e-12), name


def test_cnot_promotion_builds_bell_state():
    out = bell_state_via_promotion()
    target = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    assert np.allclose(out, target, atol=1e-12)
    assert np.isclose(relational_wedge_two_qubit(out), 1.0, atol=1e-12)


def test_segre_determinant_detects_separable_and_entangled_states():
    separable = np.array([1, 1, 1, 1], dtype=complex) / 2
    bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    assert np.isclose(segre_determinant_two_qubit(separable), 0.0, atol=1e-12)
    assert np.isclose(abs(segre_determinant_two_qubit(bell)), 0.5, atol=1e-12)


def test_bloch_qgt_recovers_fubini_study_metric_and_berry_curvature():
    theta = 1.123
    phi = -0.456
    p, dtheta, dphi = bloch_promotion(theta, phi)
    qtt = qgt_trace(p, dtheta, dtheta)
    qpp = qgt_trace(p, dphi, dphi)
    qtp = qgt_trace(p, dtheta, dphi)
    assert np.isclose(qtt.real, 0.25, atol=1e-12)
    assert np.isclose(qpp.real, 0.25 * np.sin(theta) ** 2, atol=1e-12)
    assert np.isclose(qtp.real, 0.0, atol=1e-12)
    assert np.isclose(qtp.imag, 0.25 * np.sin(theta), atol=1e-12)


def test_controlled_unitary_is_unitary_for_unitary_target():
    cu = controlled_unitary(_gates()["X"])
    assert np.allclose(cu.conj().T @ cu, np.eye(4), atol=1e-12)
