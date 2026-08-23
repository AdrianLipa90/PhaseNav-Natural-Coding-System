import pytest

from phasenav_natural_code.orchorbital_v27 import AttractorWeights, OrchV27Error, SelectionLaw


def test_llm_temp_attractor_fails_closed_without_decay_schedule():
    with pytest.raises(OrchV27Error, match="decay schedule"):
        AttractorWeights(0.6, 0.3, 0.1)


def test_selection_tie_tolerance_must_be_non_negative():
    with pytest.raises(OrchV27Error, match="tie"):
        SelectionLaw(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, tie=-1.0)
