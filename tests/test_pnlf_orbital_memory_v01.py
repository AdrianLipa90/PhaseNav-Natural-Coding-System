import math

import pytest

from phasenav_natural_code.pnlf_orbital_memory_v01 import (
    OrbitalState,
    PNLFHeader,
    PNLFOrbitalMemoryError,
    admit_liminal_segment,
    advance_liminal_segment,
    build_state_checkpoint,
    logical_address,
    open_liminal_segment,
    reject_liminal_segment,
    tau_frame,
    validate_checkpoint_against_header,
    validate_segment_against_header,
)


TIME_MODEL = "pncs:orch-time-kernel:test:v1"


def d(ch: str) -> str:
    return ch * 64


def orbital(
    tau: float,
    band: str = "O4",
    *,
    mass_model: str = "pncs:test-mass:v1",
    quantizer: str = "pnlf:test-quantizer:v1",
    time_model: str = TIME_MODEL,
) -> OrbitalState:
    return OrbitalState(
        attractor_id="identity:test",
        orbital_band=band,
        r_phase=0.7,
        phase=1.25,
        E_bind=-0.8,
        L_phase=0.14,
        semantic_mass=0.42,
        orbit_period=2.5,
        winding=1.5,
        proper_time=tau,
        memory_affinity=0.75,
        mass_model_id=mass_model,
        orbit_quantizer_id=quantizer,
        proper_time_model_id=time_model,
    )


def header() -> PNLFHeader:
    return PNLFHeader(
        file_id="pnlf:file:test-lineage",
        object_id="pnlf:object:test-memory",
        genesis_anchor=d("a"),
        basis_id="pncs:t36:test-basis:v1",
        schema_binding="PNLF_ORBITAL_MEMORY_V0_1",
        storage_profile="PNLF_NATIVE",
        mass_model_id="pncs:test-mass:v1",
        orbit_quantizer_id="pnlf:test-quantizer:v1",
        proper_time_model_id=TIME_MODEL,
        t36_basis_id="pncs:t36:test-basis:v1",
    )


def checkpoint(tau: float, *, predecessor=None, band="O4", layers=("M3",), content="b"):
    return build_state_checkpoint(
        object_id="pnlf:object:test-memory",
        tau=tau,
        content_commitment=d(content),
        predecessor_checkpoint_id=predecessor,
        active_m_layers=layers,
        orbital_state=orbital(tau, band),
        t36_witness_sha256=d("c"),
        reduction_witness_sha256=d("d"),
        consolidation_witness_sha256=d("e"),
        relation_braid_commitment=d("f"),
    )


def test_m_layer_and_orbital_band_are_orthogonal():
    semantic_outer = checkpoint(0.0, band="O8", layers=("M3",))
    audit_inner = checkpoint(0.0, band="O0", layers=("M8",), content="1")
    assert semantic_outer.active_m_layers == ("M3",)
    assert semantic_outer.orbital_state.orbital_band == "O8"
    assert audit_inner.active_m_layers == ("M8",)
    assert audit_inner.orbital_state.orbital_band == "O0"


def test_checkpoint_requires_reduction_witness():
    with pytest.raises(PNLFOrbitalMemoryError):
        build_state_checkpoint(
            object_id="pnlf:object:test-memory",
            tau=0.0,
            content_commitment=d("b"),
            predecessor_checkpoint_id=None,
            active_m_layers=("M1",),
            orbital_state=orbital(0.0),
            t36_witness_sha256=d("c"),
            reduction_witness_sha256="",
            consolidation_witness_sha256=d("e"),
            relation_braid_commitment=d("f"),
        )


def test_liminal_advance_is_append_only_revision_chain():
    left = checkpoint(0.0)
    opened = open_liminal_segment(
        segment_id="pnlf:segment:test-001",
        source_checkpoint=left,
        tau_start=0.0,
        active_m_layers=("M1", "M3"),
        relation_braid_commitment=d("1"),
        trajectory_commitment=d("2"),
        modulation_commitment=d("3"),
        t36_trajectory_commitment=d("4"),
    )
    advanced = advance_liminal_segment(
        opened,
        tau_cursor=0.5,
        trajectory_commitment=d("5"),
        t36_trajectory_commitment=d("6"),
        event_commitment=d("7"),
    )
    assert advanced.segment_id == opened.segment_id
    assert advanced.segment_commitment != opened.segment_commitment
    assert advanced.previous_segment_commitment == opened.segment_commitment
    assert opened.previous_segment_commitment is None
    assert opened.tau_cursor == 0.0
    assert advanced.tau_cursor == 0.5


def test_state_commit_closes_exact_tau_without_mutating_left_state():
    left = checkpoint(0.0, band="O6")
    opened = open_liminal_segment(
        segment_id="pnlf:segment:test-002",
        source_checkpoint=left,
        tau_start=0.0,
        active_m_layers=("M2", "M3"),
        relation_braid_commitment=d("1"),
        trajectory_commitment=d("2"),
        modulation_commitment=d("3"),
        t36_trajectory_commitment=d("4"),
    )
    advanced = advance_liminal_segment(
        opened,
        tau_cursor=1.0,
        trajectory_commitment=d("5"),
        t36_trajectory_commitment=d("6"),
    )
    right = checkpoint(1.0, predecessor=left.checkpoint_object_id, band="O2", layers=("M2", "M3"), content="8")
    admitted = admit_liminal_segment(advanced, right_checkpoint=right, resolution_witness_sha256=d("9"))

    assert admitted.resolution_state == "ADMITTED"
    assert admitted.pilot_l_checkpoint_id == left.checkpoint_object_id
    assert admitted.pilot_r_checkpoint_id == right.checkpoint_object_id
    assert admitted.tau_end == admitted.tau_cursor == 1.0
    assert left.orbital_state.orbital_band == "O6"
    assert right.orbital_state.orbital_band == "O2"
    assert left.checkpoint_object_id != right.checkpoint_object_id


def test_state_commit_rejects_unrecorded_tau_gap():
    left = checkpoint(0.0)
    opened = open_liminal_segment(
        segment_id="pnlf:segment:test-003",
        source_checkpoint=left,
        tau_start=0.0,
        active_m_layers=("M3",),
        relation_braid_commitment=d("1"),
        trajectory_commitment=d("2"),
        modulation_commitment=d("3"),
        t36_trajectory_commitment=d("4"),
    )
    right = checkpoint(1.0, predecessor=left.checkpoint_object_id, content="8")
    with pytest.raises(PNLFOrbitalMemoryError, match="tau_cursor"):
        admit_liminal_segment(opened, right_checkpoint=right, resolution_witness_sha256=d("9"))


def test_rejection_closes_without_right_checkpoint():
    left = checkpoint(0.0)
    opened = open_liminal_segment(
        segment_id="pnlf:segment:test-004",
        source_checkpoint=left,
        tau_start=0.0,
        active_m_layers=("M1",),
        relation_braid_commitment=d("1"),
        trajectory_commitment=d("2"),
        modulation_commitment=d("3"),
        t36_trajectory_commitment=d("4"),
    )
    advanced = advance_liminal_segment(
        opened,
        tau_cursor=0.25,
        trajectory_commitment=d("5"),
        t36_trajectory_commitment=d("6"),
    )
    rejected = reject_liminal_segment(advanced, resolution_witness_sha256=d("9"))
    assert rejected.resolution_state == "REJECTED"
    assert rejected.pilot_r_checkpoint_id is None
    assert rejected.target_orbital_state is None
    assert rejected.tau_end == 0.25


def test_header_binds_object_mass_model_quantizer_and_time_model():
    h = header()
    cp = checkpoint(0.0)
    validate_checkpoint_against_header(h, cp)

    wrong_mass = PNLFHeader(
        file_id="pnlf:file:test-lineage-2",
        object_id=h.object_id,
        genesis_anchor=d("a"),
        basis_id=h.basis_id,
        schema_binding=h.schema_binding,
        storage_profile=h.storage_profile,
        mass_model_id="other-mass-model",
        orbit_quantizer_id=h.orbit_quantizer_id,
        proper_time_model_id=h.proper_time_model_id,
        t36_basis_id=h.t36_basis_id,
    )
    with pytest.raises(PNLFOrbitalMemoryError, match="mass model"):
        validate_checkpoint_against_header(wrong_mass, cp)

    wrong_time = PNLFHeader(
        file_id="pnlf:file:test-lineage-3",
        object_id=h.object_id,
        genesis_anchor=d("a"),
        basis_id=h.basis_id,
        schema_binding=h.schema_binding,
        storage_profile=h.storage_profile,
        mass_model_id=h.mass_model_id,
        orbit_quantizer_id=h.orbit_quantizer_id,
        proper_time_model_id="pncs:orch-time-kernel:other:v1",
        t36_basis_id=h.t36_basis_id,
    )
    with pytest.raises(PNLFOrbitalMemoryError, match="proper-time model"):
        validate_checkpoint_against_header(wrong_time, cp)


def test_segment_header_validation_and_tau_frame():
    h = header()
    left = checkpoint(0.0)
    opened = open_liminal_segment(
        segment_id="pnlf:segment:test-005",
        source_checkpoint=left,
        tau_start=0.0,
        active_m_layers=("M1", "M7"),
        relation_braid_commitment=d("1"),
        trajectory_commitment=d("2"),
        modulation_commitment=d("3"),
        t36_trajectory_commitment=d("4"),
    )
    advanced = advance_liminal_segment(
        opened,
        tau_cursor=0.75,
        trajectory_commitment=d("5"),
        t36_trajectory_commitment=d("6"),
    )
    validate_segment_against_header(h, advanced)
    frame = tau_frame(advanced, 0.5)
    assert frame["pilot_l"] == left.checkpoint_object_id
    assert frame["pilot_r"] is None
    assert frame["lambda"]["segment_id"] == advanced.segment_id
    assert frame["lambda"]["tau"] == 0.5
    assert frame["t36"] == d("6")
    assert frame["proper_time_model_id"] == TIME_MODEL


def test_orbital_state_rejects_non_circular_phase_distance():
    with pytest.raises(PNLFOrbitalMemoryError, match="r_phase"):
        OrbitalState(
            attractor_id="identity:test",
            orbital_band="O1",
            r_phase=math.pi + 0.001,
            phase=0.0,
            E_bind=-1.0,
            L_phase=0.0,
            semantic_mass=0.2,
            orbit_period=1.0,
            winding=0.0,
            proper_time=0.0,
            memory_affinity=0.5,
            mass_model_id="pncs:test-mass:v1",
            orbit_quantizer_id="pnlf:test-quantizer:v1",
            proper_time_model_id=TIME_MODEL,
        )


def test_logical_address_is_object_tau_relation():
    assert logical_address("pnlf:object:test-memory", 1.25, "recall") == (
        "pnlf:object:test-memory",
        1.25,
        "recall",
    )
