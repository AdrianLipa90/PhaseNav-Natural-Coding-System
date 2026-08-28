from __future__ import annotations

from fractions import Fraction
import hashlib
import struct

from .tau_frame_codec_v01 import (
    PHASE_DENOMINATOR,
    TAU_DENOMINATOR,
    TauFrame,
    TauFrameWitness,
    TauSymbol,
    decode_exact_delta_tau,
    decode_frame,
    frame_commitment,
    witness_commitment,
)

RECORD_MAGIC = b"PTF1"
RECORD_DOMAIN = b"PNCS-PNH5-TAU-FRAME/v0.1\x00"
RECORD_HEADER = struct.Struct("<4sII32s32s")
RECORD_SCHEMA = "PNCS_PNH5_TAU_FRAME_REALIZATION_V0_1"


class PNH5TauRealizationError(ValueError):
    pass


def _phase_lane_bytes(witness: TauFrameWitness) -> bytes:
    values: list[int] = []
    for phase in witness.phase_turns:
        raw = phase * PHASE_DENOMINATOR
        if raw.denominator != 1 or not 0 <= raw.numerator <= 255:
            raise PNH5TauRealizationError("phase lane is outside the exact 1/256 grid")
        values.append(raw.numerator)
    if len(values) != 36:
        raise PNH5TauRealizationError("T36 witness requires exactly 36 phase coordinates")
    return bytes(values)


def pack_tau_frame(frame: TauFrame) -> bytes:
    if not isinstance(frame, TauFrame):
        raise PNH5TauRealizationError("TauFrame required")
    decode_frame(frame)

    numerators: list[int] = []
    for symbol in frame.symbols:
        scaled = symbol.delta_tau * TAU_DENOMINATOR
        if scaled.denominator != 1 or not TAU_DENOMINATOR <= scaled.numerator <= TAU_DENOMINATOR + 255:
            raise PNH5TauRealizationError("tau symbol is outside the exact 1/257 alphabet")
        numerators.append(scaled.numerator)

    body = RECORD_HEADER.pack(
        RECORD_MAGIC,
        frame.block_index,
        len(numerators),
        bytes.fromhex(frame_commitment(frame)),
        bytes.fromhex(witness_commitment(frame.witness)),
    )
    if numerators:
        body += struct.pack("<" + "H" * len(numerators), *numerators)
    body += _phase_lane_bytes(frame.witness)
    seal = hashlib.blake2b(RECORD_DOMAIN + body, digest_size=32).digest()
    return body + seal


def unpack_tau_frame(raw: bytes | bytearray | memoryview) -> TauFrame:
    record = bytes(raw)
    minimum = RECORD_HEADER.size + 36 + 32
    if len(record) < minimum:
        raise PNH5TauRealizationError("tau-frame realization is too short")

    magic, block_index, symbol_count, expected_frame, expected_witness = RECORD_HEADER.unpack_from(record, 0)
    if magic != RECORD_MAGIC:
        raise PNH5TauRealizationError("tau-frame realization magic mismatch")

    expected_length = RECORD_HEADER.size + 2 * symbol_count + 36 + 32
    if len(record) != expected_length:
        raise PNH5TauRealizationError("tau-frame realization length mismatch")

    body, seal = record[:-32], record[-32:]
    actual_seal = hashlib.blake2b(RECORD_DOMAIN + body, digest_size=32).digest()
    if actual_seal != seal:
        raise PNH5TauRealizationError("tau-frame realization seal mismatch")

    offset = RECORD_HEADER.size
    numerators = struct.unpack_from("<" + "H" * symbol_count, record, offset) if symbol_count else ()
    offset += 2 * symbol_count
    lane = record[offset : offset + 36]

    if int.from_bytes(lane[32:36], "little") != block_index:
        raise PNH5TauRealizationError("T36 witness block index mismatch")

    symbols: list[TauSymbol] = []
    payload_values: list[int] = []
    for numerator in numerators:
        delta_tau = Fraction(numerator, TAU_DENOMINATOR)
        value = decode_exact_delta_tau(delta_tau)
        symbols.append(TauSymbol(value=value, delta_tau=delta_tau))
        payload_values.append(value)

    witness = TauFrameWitness(
        block_index=block_index,
        phase_turns=tuple(Fraction(value, PHASE_DENOMINATOR) for value in lane),
        block_commitment=lane[:32].hex(),
    )
    frame = TauFrame(
        block_index=block_index,
        payload=bytes(payload_values),
        symbols=tuple(symbols),
        witness=witness,
    )
    decode_frame(frame)

    if bytes.fromhex(frame_commitment(frame)) != expected_frame:
        raise PNH5TauRealizationError("tau-frame commitment mismatch")
    if bytes.fromhex(witness_commitment(witness)) != expected_witness:
        raise PNH5TauRealizationError("T36 witness commitment mismatch")
    return frame
