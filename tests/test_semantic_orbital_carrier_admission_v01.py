import pytest

from phasenav_natural_code.semantic_orbital_carrier_v01 import (
    DEFAULT_BANDS,
    OrbitQuantizerProfile,
    SemanticCarrierSample,
    SemanticOrbitalCarrierError,
    bind_semantic_sample,
    semantic_value,
)


def _quantizer() -> OrbitQuantizerProfile:
    return OrbitQuantizerProfile(
        "Q.STRICT",
        (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
        DEFAULT_BANDS,
    )


def _sample() -> SemanticCarrierSample:
    return SemanticCarrierSample("SEM.STRICT", "K.STRICT", 0.0, 1.0, 2.0, 3.0, 4.0, 0.5)


def test_semantic_formula_rejects_bool_numeric_string_and_objects():
    for field_index in range(5):
        for bad in (True, "1.0", object()):
            args = [1.0, 2.0, 3.0, 4.0, 0.5]
            args[field_index] = bad
            with pytest.raises(SemanticOrbitalCarrierError, match="finite real"):
                semantic_value(*args)  # type: ignore[arg-type]


def test_sample_identity_requires_exact_strings():
    for bad_content in (1, True, object()):
        with pytest.raises(SemanticOrbitalCarrierError, match="content_id"):
            SemanticCarrierSample(bad_content, "K", 0.0, 1.0, 1.0, 1.0, 1.0, 0.0)  # type: ignore[arg-type]
    for bad_kaku in (1, True, object()):
        with pytest.raises(SemanticOrbitalCarrierError, match="kaku_id"):
            SemanticCarrierSample("C", bad_kaku, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0)  # type: ignore[arg-type]


def test_quantizer_requires_explicit_sequence_containers():
    with pytest.raises(SemanticOrbitalCarrierError, match="boundaries must be an explicit"):
        OrbitQuantizerProfile("Q.BAD", "01234567", DEFAULT_BANDS)  # type: ignore[arg-type]
    with pytest.raises(SemanticOrbitalCarrierError, match="bands must be an explicit"):
        OrbitQuantizerProfile(
            "Q.BAD",
            (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
            "O0O1O2O3O4O5O6O7O8",  # type: ignore[arg-type]
        )


def test_quantizer_band_identity_is_not_derived_from_str():
    class LooksLikeO0:
        def __str__(self) -> str:
            return "O0"

    bands = list(DEFAULT_BANDS)
    bands[0] = LooksLikeO0()  # type: ignore[list-item]
    with pytest.raises(SemanticOrbitalCarrierError, match="exact string identities"):
        OrbitQuantizerProfile(
            "Q.BAD",
            (-4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0),
            bands,  # type: ignore[arg-type]
        )


def test_source_snapshot_requires_string_mapping_keys_at_every_depth():
    with pytest.raises(SemanticOrbitalCarrierError, match="mapping keys must be strings"):
        bind_semantic_sample(_sample(), _quantizer(), source_orbital_state={1: "x"})  # type: ignore[dict-item]
    with pytest.raises(SemanticOrbitalCarrierError, match="mapping keys must be strings"):
        bind_semantic_sample(
            _sample(),
            _quantizer(),
            source_orbital_state={"nested": {1: "x"}},  # type: ignore[dict-item]
        )


def test_source_snapshot_rejects_arbitrary_object_values():
    with pytest.raises(SemanticOrbitalCarrierError, match="unsupported canonical type"):
        bind_semantic_sample(
            _sample(),
            _quantizer(),
            source_orbital_state={"payload": object()},
        )
