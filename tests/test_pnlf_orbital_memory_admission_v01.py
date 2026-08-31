import pytest

from phasenav_natural_code.pnlf_orbital_memory_v01 import (
    OrbitalState,
    PNLFHeader,
    PNLFOrbitalMemoryError,
    _canonical_bytes,
    _layers,
    build_state_checkpoint,
    logical_address,
)


TIME_MODEL = "pncs:orch-time-kernel:test:v1"
EXPECTED_CANONICAL_CHECKPOINT_ID = (
    "pnlf:checkpoint:sha256:122beb86d43106392551678d761b289014f1daa842738cc30cd9e1d690591d25"
)


def _orbital(*, tau=0.0, band="O4", r_phase=0.7):
    return OrbitalState(
        attractor_id="identity:test",
        orbital_band=band,
        r_phase=r_phase,
        phase=1.25,
        E_bind=-0.8,
        L_phase=0.14,
        semantic_mass=0.42,
        orbit_period=2.5,
        winding=1.5,
        proper_time=tau,
        memory_affinity=0.75,
        mass_model_id="pncs:test-mass:v1",
        orbit_quantizer_id="pnlf:test-quantizer:v1",
        proper_time_model_id=TIME_MODEL,
    )


def _checkpoint(*, tau=0.0, layers=("M3",)):
    return build_state_checkpoint(
        object_id="pnlf:object:test-memory",
        tau=tau,
        content_commitment="b" * 64,
        predecessor_checkpoint_id=None,
        active_m_layers=layers,
        orbital_state=_orbital(tau=tau),
        t36_witness_sha256="c" * 64,
        reduction_witness_sha256="d" * 64,
        consolidation_witness_sha256="e" * 64,
        relation_braid_commitment="f" * 64,
    )


class _LooksNumeric:
    def __float__(self):
        return 0.7


class _LooksTextual:
    def __str__(self):
        return "O4"


def test_numeric_admission_rejects_bool_strings_and_float_coercible_objects():
    for bad in (True, "0.7", _LooksNumeric()):
        with pytest.raises(PNLFOrbitalMemoryError, match="finite real"):
            _orbital(r_phase=bad)


def test_numeric_admission_rejects_finite_conversion_overflow():
    with pytest.raises(PNLFOrbitalMemoryError, match="finite real"):
        _orbital(r_phase=10**400)


def test_orbital_band_requires_exact_string_identity():
    with pytest.raises(PNLFOrbitalMemoryError, match="exact string"):
        _orbital(band=_LooksTextual())


def test_text_and_digest_boundaries_reject_string_like_objects():
    with pytest.raises(PNLFOrbitalMemoryError, match="non-empty string"):
        PNLFHeader(
            file_id=_LooksTextual(),
            object_id="pnlf:object:test-memory",
            genesis_anchor="a" * 64,
            basis_id="pncs:t36:test-basis:v1",
            schema_binding="PNLF_ORBITAL_MEMORY_V0_1",
            storage_profile="PNLF_NATIVE",
            mass_model_id="pncs:test-mass:v1",
            orbit_quantizer_id="pnlf:test-quantizer:v1",
            proper_time_model_id=TIME_MODEL,
            t36_basis_id="pncs:t36:test-basis:v1",
        )

    with pytest.raises(PNLFOrbitalMemoryError, match="lowercase SHA-256"):
        PNLFHeader(
            file_id="pnlf:file:test",
            object_id="pnlf:object:test-memory",
            genesis_anchor=_LooksTextual(),
            basis_id="pncs:t36:test-basis:v1",
            schema_binding="PNLF_ORBITAL_MEMORY_V0_1",
            storage_profile="PNLF_NATIVE",
            mass_model_id="pncs:test-mass:v1",
            orbit_quantizer_id="pnlf:test-quantizer:v1",
            proper_time_model_id=TIME_MODEL,
            t36_basis_id="pncs:t36:test-basis:v1",
        )


def test_active_layers_require_explicit_container_and_exact_string_members():
    for bad in ("M3", {"M3"}, iter(("M3",))):
        with pytest.raises(PNLFOrbitalMemoryError, match="list or tuple"):
            _layers(bad)

    with pytest.raises(PNLFOrbitalMemoryError, match="exact strings"):
        _layers(("M3", _LooksTextual()))


def test_canonical_pnlf_json_requires_exact_string_mapping_keys():
    with pytest.raises(PNLFOrbitalMemoryError, match="mapping keys must be strings"):
        _canonical_bytes({1: "value"})
    with pytest.raises(PNLFOrbitalMemoryError, match="mapping keys must be strings"):
        _canonical_bytes({_LooksTextual(): "value"})


def test_public_tau_address_rejects_numeric_string_and_bool():
    for bad in (True, "1.25", _LooksNumeric()):
        with pytest.raises(PNLFOrbitalMemoryError, match="finite real"):
            logical_address("pnlf:object:test-memory", bad, "recall")


def test_legal_checkpoint_content_identity_is_stable_after_admission_hardening():
    checkpoint = _checkpoint()
    assert checkpoint.checkpoint_object_id == EXPECTED_CANONICAL_CHECKPOINT_ID
    assert checkpoint.state_commitment == EXPECTED_CANONICAL_CHECKPOINT_ID.rsplit(":", 1)[1]


def test_legal_layer_normalization_remains_deterministic():
    checkpoint = _checkpoint(layers=("M3", "M1", "M3"))
    assert checkpoint.active_m_layers == ("M1", "M3")
