from __future__ import annotations

import pytest

from phasenav_natural_code.candidate_600cell_mckay_e8_v03 import (
    Candidate600CellMcKayError,
    EXPECTED_COEFFICIENT_RANKS,
    EXPECTED_CUMULATIVE_RANKS,
    EXPECTED_RESTRICTIONS,
    IRREP_DIMS,
    candidate_metadata,
    coefficient_rank,
    cumulative_carrier_rank,
    representation_dimension,
    subtract_representation_fail_closed,
    sym_power_restriction,
    validate_exact_closure,
    validate_mckay_graph,
)


def test_affine_e8_mckay_graph_is_dimension_balanced():
    assert validate_mckay_graph() is True


def test_low_sym_power_restrictions_are_exact():
    for ell in range(8):
        assert sym_power_restriction(ell, candidate_enabled=True) == dict(
            sorted(EXPECTED_RESTRICTIONS[ell].items())
        )
        assert representation_dimension(ell, candidate_enabled=True) == ell + 1


def test_coefficient_ranks_explain_l6_l7_numeric_rank_collapse():
    ranks = tuple(coefficient_rank(ell, candidate_enabled=True) for ell in range(8))
    assert ranks == EXPECTED_COEFFICIENT_RANKS
    assert ranks[6] == 4**2 + 3**2 == 25
    assert ranks[7] == 6**2 + 2**2 == 40


def test_finite_carrier_closes_exactly_at_l7():
    cumulative = tuple(cumulative_carrier_rank(ell, candidate_enabled=True) for ell in range(8))
    assert cumulative == EXPECTED_CUMULATIVE_RANKS
    assert cumulative[5] == 91
    assert cumulative[6] == 116
    assert cumulative[7] == 120
    assert sum(dim * dim for dim in IRREP_DIMS.values()) == 120


def test_ell6_is_first_irreducibility_break_and_l7_adds_only_terminal_doublet():
    for ell in range(6):
        assert len(sym_power_restriction(ell, candidate_enabled=True)) == 1
    assert sym_power_restriction(6, candidate_enabled=True) == {"rho3b": 1, "rho4b": 1}
    assert sym_power_restriction(7, candidate_enabled=True) == {"rho2b": 1, "rho6": 1}
    assert cumulative_carrier_rank(7, candidate_enabled=True) - cumulative_carrier_rank(
        6, candidate_enabled=True
    ) == IRREP_DIMS["rho2b"] ** 2 == 4


def test_representation_subtraction_is_fail_closed():
    with pytest.raises(Candidate600CellMcKayError, match="negative representation multiplicity"):
        subtract_representation_fail_closed({"rho1": 1}, {"rho1": 2})


def test_candidate_gate_and_certified_range_fail_closed():
    with pytest.raises(Candidate600CellMcKayError, match="CANDIDATE"):
        sym_power_restriction(0, candidate_enabled=False)
    with pytest.raises(Candidate600CellMcKayError, match="certified McKay range"):
        sym_power_restriction(8, candidate_enabled=True)
    with pytest.raises(Candidate600CellMcKayError, match="certified McKay range"):
        sym_power_restriction(-1, candidate_enabled=True)


def test_exact_closure_receipt_preserves_epistemic_boundary():
    receipt = validate_exact_closure(candidate_enabled=True)
    assert receipt.ell6_coefficient_rank == 25
    assert receipt.ell7_coefficient_rank == 40
    assert receipt.ell7_cumulative_rank == 120
    assert receipt.group_algebra_dimension == 120
    assert receipt.runtime_default is False
    assert receipt.canon_write_authority is False
    assert receipt.physical_binding == "OPEN"

    metadata = candidate_metadata()
    assert metadata["promotion_state"] == "CANDIDATE_ONLY"
    assert metadata["runtime_laplacian_extension_authorized"] is False
    assert metadata["prime_aliases_canonical"] is False
    assert metadata["interpretation"]["ell6"] == "FIRST_IRREDUCIBILITY_BREAKING_FINITE_RESOLUTION_THRESHOLD"
    assert metadata["interpretation"]["ell7"] == "FINITE_REPRESENTATION_CLOSURE"
