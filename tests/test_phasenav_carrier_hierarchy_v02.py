import numpy as np
import pytest

from phasenav_natural_code.phasenav_carrier_hierarchy_v02 import (
    balanced_promoter,
    build_ghz_by_promotion,
    candidate_manifest,
    carrier_levels,
    cnot_gate,
    embed_single_qubit_gate,
    gate_promotion_defect,
    ghz_state,
    promote_state,
    promotion_contract,
    schmidt_rank,
)


def test_manifest_fail_closed_and_physical_binding_open():
    manifest = candidate_manifest()
    assert manifest["promotion_state"] == "CANDIDATE_ONLY"
    assert manifest["runtime_execution_authority"] is False
    assert manifest["canon_write_authority"] is False
    assert manifest["physical_ion_binding"] == "OPEN"


def test_hierarchy_dimensions_and_projective_spaces():
    assert [
        (x.qubits, x.label, x.complex_dim, x.real_dim, x.projective_space)
        for x in carrier_levels()
    ] == [
        (1, "H", 2, 4, "CP^1"),
        (2, "O", 4, 8, "CP^3"),
        (3, "S_16", 8, 16, "CP^7"),
        (4, "A_32", 16, 32, "CP^15"),
    ]


def test_all_promotions_preserve_metric_and_complex_structure():
    for qubits in (1, 2, 3):
        contract = promotion_contract(qubits, phase=0.371)
        assert contract["isometry"]
        assert contract["metric_defect_norm"] < 1e-12
        assert contract["complex_structure_defect_norm"] < 1e-12


def test_promote_state_preserves_norm_through_4q():
    state = np.array([1, np.exp(0.2j)], dtype=complex) / np.sqrt(2)
    for _ in range(3):
        state = promote_state(state, 1 / np.sqrt(2), 1j / np.sqrt(2))
        assert np.isclose(np.vdot(state, state).real, 1.0, atol=1e-12)
    assert state.size == 16


def test_old_subsystem_gate_intertwines_at_every_promotion():
    x = np.array([[0, 1], [1, 0]], dtype=complex)
    for qubits in (1, 2, 3):
        gate = embed_single_qubit_gate(x, qubits, target=qubits - 1)
        promotion = balanced_promoter(qubits, phase=0.2)
        assert np.allclose(gate_promotion_defect(gate, promotion), 0.0, atol=1e-12)


def test_embedded_single_qubit_gates_are_unitary_to_4q():
    h = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    for qubits in (1, 2, 3, 4):
        for target in range(qubits):
            gate = embed_single_qubit_gate(h, qubits, target)
            assert np.allclose(gate.conj().T @ gate, np.eye(2**qubits), atol=1e-12)


def test_cnot_is_unitary_for_all_pairs_from_2q_to_4q():
    for qubits in (2, 3, 4):
        for control in range(qubits):
            for target in range(qubits):
                if control == target:
                    continue
                gate = cnot_gate(qubits, control, target)
                assert np.allclose(gate.conj().T @ gate, np.eye(2**qubits), atol=1e-12)


def test_promotion_sequence_builds_exact_ghz_2_to_4():
    for qubits in (2, 3, 4):
        assert np.allclose(build_ghz_by_promotion(qubits), ghz_state(qubits), atol=1e-12)


def test_ghz_has_schmidt_rank_two_across_all_nontrivial_contiguous_splits():
    for qubits in (2, 3, 4):
        state = build_ghz_by_promotion(qubits)
        for split in range(1, qubits):
            assert schmidt_rank(state, qubits, split) == 2


def test_candidate_ceiling_and_indices_fail_closed():
    with pytest.raises(ValueError):
        balanced_promoter(4)
    with pytest.raises(ValueError):
        cnot_gate(4, 0, 0)
    with pytest.raises(ValueError):
        embed_single_qubit_gate(np.eye(2), 4, 4)
