import pytest

from phasenav_natural_code.pnh5_tau_realization_v01 import (
    PNH5TauRealizationError,
    pack_tau_frame,
    unpack_tau_frame,
)
from phasenav_natural_code.tau_frame_codec_v01 import encode_frame, frame_commitment, witness_commitment


def test_tau_frame_realization_roundtrip_exact():
    for size in (0, 1, 64, 255):
        payload = bytes((i * 17 + 3) % 256 for i in range(size))
        frame = encode_frame(payload, 7)
        restored = unpack_tau_frame(pack_tau_frame(frame))
        assert restored == frame
        assert restored.payload == payload


def test_realization_preserves_frame_and_witness_commitments():
    frame = encode_frame(bytes(range(64)), 11)
    restored = unpack_tau_frame(pack_tau_frame(frame))
    assert frame_commitment(restored) == frame_commitment(frame)
    assert witness_commitment(restored.witness) == witness_commitment(frame.witness)


def test_realization_seal_tamper_fails_closed():
    frame = encode_frame(b"PNH5", 2)
    raw = bytearray(pack_tau_frame(frame))
    raw[-1] ^= 0x01
    with pytest.raises(PNH5TauRealizationError, match="seal mismatch"):
        unpack_tau_frame(raw)


def test_realization_payload_tamper_fails_closed():
    frame = encode_frame(b"PNH5", 2)
    raw = bytearray(pack_tau_frame(frame))
    raw[80] ^= 0x01
    with pytest.raises(PNH5TauRealizationError):
        unpack_tau_frame(raw)


def test_block_index_is_bound_inside_T36_lane():
    frame = encode_frame(b"same", 3)
    raw = bytearray(pack_tau_frame(frame))
    lane_index_offset = len(raw) - 32 - 36 + 32
    raw[lane_index_offset] ^= 0x01
    with pytest.raises(PNH5TauRealizationError):
        unpack_tau_frame(raw)
