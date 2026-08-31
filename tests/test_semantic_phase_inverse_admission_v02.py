from dataclasses import replace

import pytest

from phasenav_natural_code.semantic_orbital_carrier_v01 import (
    KAPPA,
    DEFAULT_BANDS,
    OrbitQuantizerProfile,
)
from phasenav_natural_code.semantic_phase_inverse_v02 import (
    SemanticPhaseInverseError,
    canonical_phase_split,
    encode_semantic_phase_placement,
    lifted_phase_from_semantic_value,
)


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        quantizer_id="Q.SEM.PHASE.ADMISSION",
        boundaries=(-8.0, -4.0, -2.0, -1.0, 0.0, 1.0, 2.0, 4.0),
        bands=DEFAULT_BANDS,
    )


class _LooksNumeric:
    def __float__(self):
        return 0.5


class _LooksTextual:
    def __str__(self):
        return "SEM.LOOKS_VALID"


def _placement(**overrides):
    kwargs = dict(
        content_id="SEM.ADMISSION",
        kaku_id="K.ADMISSION",
        sample_time=1.0,
        semantic_target=0.6,
        B=2.0,
        omega=1.5,
        N=3.0,
        A_R=2.5,
        quantizer=_quantizer(),
    )
    kwargs.update(overrides)
    return encode_semantic_phase_placement(**kwargs)


def test_inverse_target_rejects_bool_numeric_string_and_float_like_object():
    for bad in (True, "0.6", _LooksNumeric()):
        with pytest.raises(SemanticPhaseInverseError, match="semantic_target must be finite real"):
            lifted_phase_from_semantic_value(bad, 2.0, 1.5, 3.0, 2.5)


def test_inverse_kappa_rejects_bool_numeric_string_and_float_like_object():
    for bad in (True, str(KAPPA), _LooksNumeric()):
        with pytest.raises(SemanticPhaseInverseError, match="kappa must be finite real"):
            lifted_phase_from_semantic_value(0.6, 2.0, 1.5, 3.0, 2.5, kappa=bad)


def test_phase_split_rejects_implicit_numeric_coercion():
    for bad in (True, "0.25", _LooksNumeric()):
        with pytest.raises(SemanticPhaseInverseError, match="finite real"):
            canonical_phase_split(bad)


def test_semantic_identity_rejects_string_like_objects():
    with pytest.raises(SemanticPhaseInverseError, match="content_id must be non-empty"):
        _placement(content_id=_LooksTextual())
    with pytest.raises(SemanticPhaseInverseError, match="kaku_id must be non-empty"):
        _placement(kaku_id=_LooksTextual())


def test_parent_carrier_coordinates_keep_strict_real_boundary():
    for field in ("B", "omega", "N", "A_R"):
        with pytest.raises(SemanticPhaseInverseError, match="finite real"):
            _placement(**{field: "1.0"})


def test_direct_placement_requires_exact_orbital_band_string():
    placement = _placement()
    with pytest.raises(SemanticPhaseInverseError, match="orbital_band must be an exact string"):
        replace(placement, orbital_band=_LooksTextual())


def test_legal_inverse_receipt_remains_deterministic():
    a = _placement().deterministic_receipt()
    b = _placement().deterministic_receipt()
    assert a == b
    assert len(a["receipt_sha256"]) == 64
