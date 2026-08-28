import math

import pytest

from phasenav_natural_code.pnlf_orbit_governor_v01 import (
    PHASE9_QUANTIZER_ID,
    PNLFOrbitGovernorError,
    classify_phase9,
    classify_transition,
    phase_distance,
    quantize_phase9,
    transition_kind,
)


def test_phase_distance_is_circular_and_symmetric():
    eps = 0.05
    assert phase_distance(0.0, 2.0 * math.pi - eps) == pytest.approx(eps)
    assert phase_distance(2.0 * math.pi - eps, 0.0) == pytest.approx(eps)
    assert phase_distance(0.0, math.pi) == pytest.approx(math.pi)


def test_phase9_boundaries():
    width = math.pi / 9.0
    assert quantize_phase9(0.0) == "O0"
    assert quantize_phase9(width - 1e-12) == "O0"
    assert quantize_phase9(width) == "O1"
    assert quantize_phase9(4.0 * width) == "O4"
    assert quantize_phase9(math.pi - 1e-12) == "O8"
    assert quantize_phase9(math.pi) == "O8"


def test_phase9_rejects_out_of_domain_distance():
    with pytest.raises(PNLFOrbitGovernorError):
        quantize_phase9(-1e-9)
    with pytest.raises(PNLFOrbitGovernorError):
        quantize_phase9(math.pi + 1e-9)


def test_transition_direction_is_geometric_only():
    assert transition_kind("O7", "O2") == "PNLF.ORBIT_PROMOTE"
    assert transition_kind("O2", "O7") == "PNLF.ORBIT_DEMOTE"
    assert transition_kind("O4", "O4") == "PNLF.ORBIT_BIND"


def test_classification_has_no_stable_memory_authority():
    c = classify_phase9(0.2, 0.0)
    assert c.quantizer_id == PHASE9_QUANTIZER_ID
    assert c.payload["classification_only"] is True
    assert c.payload["stable_memory_admission"] is False
    assert c.payload["runtime_execution_authority"] is False
    assert c.payload["canon_write_authority"] is False


def test_transition_candidate_still_requires_reduction():
    result = classify_transition("O8", 0.0, 0.0)
    assert result["target_band"] == "O0"
    assert result["transition"] == "PNLF.ORBIT_PROMOTE"
    assert result["requires_reduction_admission"] is True
    assert result["stable_memory_update"] is False
    assert result["runtime_execution_authority"] is False
    assert result["canon_write_authority"] is False
