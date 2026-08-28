from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
from typing import Sequence

TAU_DENOMINATOR = 257
PHASE_DENOMINATOR = 256
TAU_ACCEPT_NUMERATOR = 45
TAU_ACCEPT_DENOMINATOR = 100
PHASE_ACCEPT_NUMERATOR = 45
PHASE_ACCEPT_DENOMINATOR = 100
BLOCK_WITNESS_DOMAIN = b"PNCS-TAU-FRAME-BLOCK-WITNESS/v0.1\x00"


class TauFrameCodecError(ValueError):
    pass


@dataclass(frozen=True)
class TauSymbol:
    value: int
    delta_tau: Fraction


@dataclass(frozen=True)
class TauFrameWitness:
    block_index: int
    phase_turns: tuple[Fraction, ...]
    block_commitment: str


@dataclass(frozen=True)
class TauFrame:
    block_index: int
    payload: bytes
    symbols: tuple[TauSymbol, ...]
    witness: TauFrameWitness


def encode_byte(value: int) -> TauSymbol:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
        raise TauFrameCodecError("byte value must be an integer in [0,255]")
    return TauSymbol(value=value, delta_tau=Fraction(TAU_DENOMINATOR + value, TAU_DENOMINATOR))


def decode_exact_delta_tau(delta_tau: Fraction) -> int:
    if not isinstance(delta_tau, Fraction):
        raise TauFrameCodecError("exact tau decode requires Fraction")
    value = (delta_tau - 1) * TAU_DENOMINATOR
    if value.denominator != 1 or not 0 <= value.numerator <= 255:
        raise TauFrameCodecError("delta_tau is outside exact PNCS byte alphabet")
    return value.numerator


def tau_spacing() -> Fraction:
    return Fraction(1, TAU_DENOMINATOR)


def tau_accept_radius() -> Fraction:
    return tau_spacing() * Fraction(TAU_ACCEPT_NUMERATOR, TAU_ACCEPT_DENOMINATOR)


def phase_accept_radius() -> Fraction:
    return Fraction(1, PHASE_DENOMINATOR) * Fraction(PHASE_ACCEPT_NUMERATOR, PHASE_ACCEPT_DENOMINATOR)


def block_commitment(payload: bytes | bytearray | memoryview) -> str:
    return hashlib.blake2b(BLOCK_WITNESS_DOMAIN + bytes(payload), digest_size=32).hexdigest()


def block_witness(payload: bytes | bytearray | memoryview, block_index: int) -> TauFrameWitness:
    if isinstance(block_index, bool) or not isinstance(block_index, int) or not 0 <= block_index <= 0xFFFFFFFF:
        raise TauFrameCodecError("block_index must fit uint32")
    raw_payload = bytes(payload)
    digest = bytes.fromhex(block_commitment(raw_payload))
    raw = digest + block_index.to_bytes(4, "little")
    assert len(raw) == 36
    return TauFrameWitness(
        block_index=block_index,
        phase_turns=tuple(Fraction(v, PHASE_DENOMINATOR) for v in raw),
        block_commitment=digest.hex(),
    )


def verify_block_witness(payload: bytes | bytearray | memoryview, witness: TauFrameWitness) -> None:
    expected = block_witness(payload, witness.block_index)
    if witness.block_commitment != expected.block_commitment:
        raise TauFrameCodecError("T36 block commitment mismatch")
    if witness.phase_turns != expected.phase_turns:
        raise TauFrameCodecError("T36 whole-lane witness mismatch")


def encode_frame(payload: bytes | bytearray | memoryview, block_index: int) -> TauFrame:
    raw = bytes(payload)
    return TauFrame(
        block_index=block_index,
        payload=raw,
        symbols=tuple(encode_byte(v) for v in raw),
        witness=block_witness(raw, block_index),
    )


def decode_frame(frame: TauFrame) -> bytes:
    decoded = bytes(decode_exact_delta_tau(symbol.delta_tau) for symbol in frame.symbols)
    if decoded != frame.payload:
        raise TauFrameCodecError("tau symbol payload mismatch")
    verify_block_witness(decoded, frame.witness)
    return decoded


def local_tau_ratio(delta_tau_data: Fraction, delta_tau_reference: Fraction) -> Fraction:
    if not isinstance(delta_tau_data, Fraction) or not isinstance(delta_tau_reference, Fraction):
        raise TauFrameCodecError("local tau ratio requires exact rational inputs")
    if delta_tau_reference <= 0:
        raise TauFrameCodecError("tau reference must be positive")
    return delta_tau_data / delta_tau_reference


def decode_affine_invariant_ratio(ratio: Fraction) -> int:
    return decode_exact_delta_tau(ratio)


def reparameterize_tau(value: Fraction, *, scale: Fraction, offset: Fraction) -> Fraction:
    if scale <= 0:
        raise TauFrameCodecError("tau reparameterization scale must be positive")
    return scale * value + offset


def verify_affine_invariance(value: int, *, scale: Fraction, offset: Fraction) -> bool:
    symbol = encode_byte(value)
    tau0 = Fraction(7, 13)
    ref0 = reparameterize_tau(tau0, scale=scale, offset=offset)
    ref1 = reparameterize_tau(tau0 + 1, scale=scale, offset=offset)
    data0 = reparameterize_tau(tau0 + 1, scale=scale, offset=offset)
    data1 = reparameterize_tau(tau0 + 1 + symbol.delta_tau, scale=scale, offset=offset)
    ratio = local_tau_ratio(data1 - data0, ref1 - ref0)
    return decode_affine_invariant_ratio(ratio) == value
