from fractions import Fraction

import pytest

from phasenav_natural_code.tau_frame_codec_v01 import (
    TauFrameCodecError,
    block_witness,
    commitment_pair,
    decode_exact_delta_tau,
    decode_frame,
    encode_byte,
    encode_frame,
    frame_commitment,
    tau_accept_radius,
    tau_spacing,
    verify_affine_invariance,
    verify_block_witness,
    witness_commitment,
)


def test_all_byte_symbols_roundtrip_exact_tau():
    for value in range(256):
        symbol = encode_byte(value)
        assert decode_exact_delta_tau(symbol.delta_tau) == value


def test_tau_alphabet_spacing_and_guard_radius():
    assert tau_spacing() == Fraction(1, 257)
    assert tau_accept_radius() == Fraction(45, 100 * 257)
    assert tau_accept_radius() < tau_spacing() / 2


def test_frame_roundtrip_and_whole_lane_witness():
    payload = bytes(range(256))
    frame = encode_frame(payload, 7)
    assert decode_frame(frame) == payload
    assert len(frame.witness.phase_turns) == 36
    assert frame.witness.block_index == 7


def test_frame_and_witness_commitments_are_distinct_and_deterministic():
    frame = encode_frame(b"BioOS-PNLF", 9)
    fc1, wc1 = commitment_pair(frame)
    fc2, wc2 = commitment_pair(encode_frame(b"BioOS-PNLF", 9))
    assert (fc1, wc1) == (fc2, wc2)
    assert fc1 == frame_commitment(frame)
    assert wc1 == witness_commitment(frame.witness)
    assert fc1 != wc1
    assert len(fc1) == len(wc1) == 64


def test_block_index_changes_frame_and_witness_commitments():
    a = encode_frame(b"same-content", 1)
    b = encode_frame(b"same-content", 2)
    assert block_witness(a.payload, 1).phase_turns != block_witness(b.payload, 2).phase_turns
    assert frame_commitment(a) != frame_commitment(b)
    assert witness_commitment(a.witness) != witness_commitment(b.witness)


def test_witness_tamper_fails_closed():
    frame = encode_frame(b"BioOS", 3)
    bad = type(frame.witness)(
        block_index=frame.witness.block_index,
        phase_turns=frame.witness.phase_turns[:-1] + (Fraction(7, 13),),
        block_commitment=frame.witness.block_commitment,
    )
    with pytest.raises(TauFrameCodecError, match="whole-lane witness mismatch"):
        verify_block_witness(frame.payload, bad)


def test_affine_tau_reparameterization_is_invariant():
    for value in (0, 1, 17, 127, 255):
        assert verify_affine_invariance(
            value,
            scale=Fraction(7919, 997),
            offset=Fraction(-12345, 37),
        )


def test_non_symbol_delta_tau_fails_closed():
    with pytest.raises(TauFrameCodecError, match="outside exact PNCS byte alphabet"):
        decode_exact_delta_tau(Fraction(1, 2))
