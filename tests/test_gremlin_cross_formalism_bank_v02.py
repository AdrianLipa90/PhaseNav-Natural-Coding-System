from dataclasses import replace
import cmath
import math
import random

import pytest

from phasenav_natural_code.gremlin_cross_formalism_bank_v02 import (
    SOURCE_PINS,
    CrossFormalismBankError,
    bank_manifest,
    bargmann_quadrilateral,
    coboundary_cycle_defects,
    compile_cross_formalism_candidates,
    cross_formalism_bank,
    rephase_state,
    shape_scale_defects,
    spinor_central_phase,
    validate_cross_formalism_candidates,
)

KWARGS = {
    "generation_binding": "b" * 64,
    "identity": "ZOSIA_NOEMA_FIRST",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def test_bank_has_five_source_pins_and_unique_entries():
    entries = cross_formalism_bank()
    assert len(entries) == 8
    assert len({entry.spec.isomorphism_id for entry in entries}) == 8
    assert set(SOURCE_PINS) == {"TIR", "IDT", "RFC", "SOH", "ZPE"}
    assert all(len(pin["commit"]) == 40 for pin in SOURCE_PINS.values())

    manifest = bank_manifest()
    assert manifest["entry_count"] == 8
    assert manifest["runtime_execution_authority"] is False
    assert manifest["canon_write_authority"] is False
    assert manifest["promotion_state"] == "CANDIDATE_ONLY"
    assert manifest["epistemic"] == "CHYBA"
    assert len(manifest["manifest_sha256"]) == 64


def test_exact_coboundary_has_zero_additive_and_trivial_multiplicative_closure():
    rng = random.Random(20260828)
    for size in range(2, 18):
        for _ in range(40):
            potentials = [rng.uniform(-20.0, 20.0) for _ in range(size)]
            additive, multiplicative = coboundary_cycle_defects(potentials)
            assert additive <= 2e-14
            assert multiplicative <= 2e-14


def test_bargmann_quadrilateral_is_invariant_under_independent_local_rephasing():
    rng = random.Random(260828)
    for _ in range(100):
        states = []
        for _vertex in range(4):
            state = [complex(rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(4)]
            states.append(state)
        reference = bargmann_quadrilateral(states)
        phases = [rng.uniform(-4.0 * math.pi, 4.0 * math.pi) for _ in range(4)]
        transformed = [rephase_state(state, phase) for state, phase in zip(states, phases)]
        observed = bargmann_quadrilateral(transformed)
        assert abs(observed - reference) <= 2e-13


def test_spinor_central_sign_is_minus_at_2pi_and_plus_at_4pi():
    assert abs(spinor_central_phase(2.0 * math.pi) + 1.0) <= 1e-15
    assert abs(spinor_central_phase(4.0 * math.pi) - 1.0) <= 1e-15
    assert abs(spinor_central_phase(-2.0 * math.pi) + 1.0) <= 1e-15
    assert abs(spinor_central_phase(-4.0 * math.pi) - 1.0) <= 1e-15


def test_shape_scale_defect_triangle_randomized():
    rng = random.Random(40404)
    for dimension in range(2, 16):
        for _ in range(100):
            p_raw = [rng.random() + 0.01 for _ in range(dimension)]
            q_raw = [rng.random() + 0.01 for _ in range(dimension)]
            p_sum = sum(p_raw)
            q_sum = sum(q_raw)
            p = [value / p_sum for value in p_raw]
            q = [value / q_sum for value in q_raw]
            scale = 10 ** rng.uniform(-2.0, 2.0)
            candidate_scale = 10 ** rng.uniform(-2.0, 2.0)
            defects = shape_scale_defects(p, q, scale, candidate_scale)
            assert defects["bound_margin"] >= -2e-12
            assert defects["D_ext"] <= defects["D_shape"] + defects["D_scale"] + 2e-12


def test_shape_scale_gate_rejects_non_normalized_shapes():
    with pytest.raises(CrossFormalismBankError, match="normalized"):
        shape_scale_defects((1.0, 1.0), (0.5, 0.5), 1.0, 1.0)


def test_positive_ray_and_global_phase_controls_preserve_relational_coordinates():
    q = (2.0, 3.0, 5.0)
    q_scaled = tuple(7.5 * value for value in q)
    p = tuple(value / sum(q) for value in q)
    p_scaled = tuple(value / sum(q_scaled) for value in q_scaled)
    assert p_scaled == pytest.approx(p, abs=1e-15)

    psi = (1.0 + 2.0j, -0.5 + 0.75j, 0.3 - 0.2j)
    chi = (0.25 - 0.4j, 1.5 + 0.1j, -0.2 + 0.9j)
    ref = abs(sum(complex(a).conjugate() * complex(b) for a, b in zip(psi, chi)))
    alpha = 1.2345
    beta = -2.3456
    psi_p = tuple(cmath.exp(1j * alpha) * value for value in psi)
    chi_p = tuple(cmath.exp(1j * beta) * value for value in chi)
    observed = abs(sum(complex(a).conjugate() * complex(b) for a, b in zip(psi_p, chi_p)))
    assert observed == pytest.approx(ref, abs=1e-13)


def test_all_entries_compile_to_read_only_candidate_pnv():
    compiled = compile_cross_formalism_candidates(**KWARGS)
    assert len(compiled.compilations) == 8
    assert len(compiled.manifest["compiled_entries"]) == 8
    for compilation in compiled.compilations.values():
        assert compilation.receipt["runtime_execution_authority"] is False
        assert compilation.receipt["canon_write_authority"] is False
        assert compilation.receipt["promotion_state"] == "CANDIDATE_ONLY"
        assert compilation.radical_candidate["kind"] == "RADICAL"
        assert compilation.operator_candidates[-1]["content"]["name"] == "ISO.RETURN"

    results = validate_cross_formalism_candidates(compiled)
    assert len(results) == 8
    for result in results.values():
        assert result.receipt["effect_boundary"]["external_effects"] is False
        assert result.program.mode == "READ_ONLY"
        assert result.program.epistemic == "CHYBA"


def test_direct_validator_rejects_tampered_aggregate_manifest():
    compiled = compile_cross_formalism_candidates(**KWARGS)
    manifest = dict(compiled.manifest)
    entries = {
        iso_id: dict(row)
        for iso_id, row in manifest["compiled_entries"].items()
    }
    target = sorted(entries)[0]
    entries[target]["receipt_sha256"] = "0" * 64
    manifest["compiled_entries"] = entries
    broken = replace(compiled, manifest=manifest)

    with pytest.raises(CrossFormalismBankError, match="aggregate manifest mismatch"):
        validate_cross_formalism_candidates(broken)


def test_direct_validator_rejects_missing_leaf_compilation_even_with_rewritten_manifest():
    compiled = compile_cross_formalism_candidates(**KWARGS)
    reduced = dict(compiled.compilations)
    reduced.pop(sorted(reduced)[0])
    broken = replace(compiled, compilations=reduced)

    with pytest.raises(CrossFormalismBankError, match="compilation keyset mismatch"):
        validate_cross_formalism_candidates(broken)
