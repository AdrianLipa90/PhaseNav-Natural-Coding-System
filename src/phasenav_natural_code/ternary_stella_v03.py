"""Balanced-ternary Stella representation candidate for PNCS memory routing.

Source intuition: Memory-Ontology TODO `ternary-stella-intuition-v0.1`.

This module keeps the distinctions explicit:
- one standard trit has three states {-1,0,+1};
- a Stella-3 is three balanced trits and therefore has 3^3 = 27 states;
- the 8 all-nonzero sign corners are a subset of that 27-state space;
- ternary representation is classical here and makes no quantum-substrate claim.

The main tested use is coarse representation of procedural route weights. A
Stella-3 encodes the balanced integer levels -13..+13 via

    level = d0 + 3*d1 + 9*d2,   di in {-1,0,+1}.

This yields exactly 27 uniformly spaced levels after normalization.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Mapping

SCHEMA = "PNCS_TERNARY_STELLA_V0_3"
TRITS = (-1, 0, 1)
MAX_LEVEL = 13


class TernaryStellaError(ValueError):
    pass


def _finite(value: float, field: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise TernaryStellaError(f"{field} must be finite")
    return out


def _trit(value: int) -> int:
    if isinstance(value, bool) or value not in TRITS:
        raise TernaryStellaError("trit must be one of -1, 0, +1")
    return int(value)


@dataclass(frozen=True)
class Stella3:
    """Three balanced trits: exactly 27 logical states."""

    d0: int
    d1: int
    d2: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "d0", _trit(self.d0))
        object.__setattr__(self, "d1", _trit(self.d1))
        object.__setattr__(self, "d2", _trit(self.d2))

    @property
    def digits(self) -> tuple[int, int, int]:
        return (self.d0, self.d1, self.d2)

    @property
    def level(self) -> int:
        return self.d0 + 3 * self.d1 + 9 * self.d2

    @property
    def code(self) -> int:
        """Canonical base-3 code in [0,26]; code == level + 13."""
        return (self.d0 + 1) + 3 * (self.d1 + 1) + 9 * (self.d2 + 1)

    @property
    def nonzero_count(self) -> int:
        return sum(d != 0 for d in self.digits)

    @property
    def shell(self) -> str:
        return {0: "CENTER", 1: "AXIS", 2: "EDGE", 3: "CORNER"}[self.nonzero_count]

    @classmethod
    def from_level(cls, level: int) -> "Stella3":
        if isinstance(level, bool) or not isinstance(level, int) or not -MAX_LEVEL <= level <= MAX_LEVEL:
            raise TernaryStellaError("Stella-3 level must be an integer in [-13,+13]")
        code = level + MAX_LEVEL
        a = code % 3
        b = (code // 3) % 3
        c = (code // 9) % 3
        return cls(a - 1, b - 1, c - 1)

    @classmethod
    def from_code(cls, code: int) -> "Stella3":
        if isinstance(code, bool) or not isinstance(code, int) or not 0 <= code < 27:
            raise TernaryStellaError("Stella-3 code must be an integer in [0,26]")
        return cls.from_level(code - MAX_LEVEL)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "digits": list(self.digits),
            "level": self.level,
            "code": self.code,
            "shell": self.shell,
            "physical_quantum_claim": False,
        }


@dataclass(frozen=True)
class QuantizedWeight:
    original: float
    scale: float
    stella: Stella3

    @property
    def reconstructed(self) -> float:
        return (self.stella.level / MAX_LEVEL) * self.scale

    @property
    def absolute_error(self) -> float:
        return abs(self.original - self.reconstructed)

    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "scale": self.scale,
            "reconstructed": self.reconstructed,
            "absolute_error": self.absolute_error,
            "stella": self.stella.to_dict(),
        }


def quantize_weight(weight: float, *, scale: float = 1.0) -> QuantizedWeight:
    value = _finite(weight, "weight")
    s = _finite(scale, "scale")
    if s <= 0:
        raise TernaryStellaError("scale must be positive")
    normalized = max(-1.0, min(1.0, value / s))
    level = int(round(MAX_LEVEL * normalized))
    level = max(-MAX_LEVEL, min(MAX_LEVEL, level))
    return QuantizedWeight(value, s, Stella3.from_level(level))


def sign_trit(weight: float, *, dead_zone: float = 0.0) -> int:
    value = _finite(weight, "weight")
    dz = _finite(dead_zone, "dead_zone")
    if dz < 0:
        raise TernaryStellaError("dead_zone must be non-negative")
    if value > dz:
        return 1
    if value < -dz:
        return -1
    return 0


def route_choice_full(weights: Mapping[str, float]) -> str:
    if not weights:
        raise TernaryStellaError("route weights cannot be empty")
    normalized = {str(k): _finite(v, "weight") for k, v in weights.items()}
    return min(normalized, key=lambda rid: (-normalized[rid], rid))


def route_choice_sign(weights: Mapping[str, float], *, dead_zone: float = 0.0) -> str:
    if not weights:
        raise TernaryStellaError("route weights cannot be empty")
    trits = {str(k): sign_trit(v, dead_zone=dead_zone) for k, v in weights.items()}
    return min(trits, key=lambda rid: (-trits[rid], rid))


def route_choice_stella3(
    weights: Mapping[str, float],
    *,
    scale: float | None = None,
) -> tuple[str, dict[str, QuantizedWeight]]:
    if not weights:
        raise TernaryStellaError("route weights cannot be empty")
    values = {str(k): _finite(v, "weight") for k, v in weights.items()}
    if scale is None:
        scale = max(1e-15, max(abs(v) for v in values.values()))
    s = _finite(scale, "scale")
    if s <= 0:
        raise TernaryStellaError("scale must be positive")
    quantized = {rid: quantize_weight(v, scale=s) for rid, v in values.items()}
    selected = min(
        quantized,
        key=lambda rid: (-quantized[rid].reconstructed, rid),
    )
    return selected, quantized


def shell_counts() -> dict[str, int]:
    counts = {"CENTER": 0, "AXIS": 0, "EDGE": 0, "CORNER": 0}
    for code in range(27):
        counts[Stella3.from_code(code).shell] += 1
    return counts


def pack_codes_5bit(states: Iterable[Stella3]) -> bytes:
    """Pack canonical 0..26 Stella codes using five binary bits per state.

    This serialization is intentionally labelled binary. It does not turn the
    underlying classical hardware into ternary hardware; it merely provides a
    compact lossless serialization of the 27-state logical alphabet.
    """
    acc = 0
    bits = 0
    out = bytearray()
    for state in states:
        if not isinstance(state, Stella3):
            raise TernaryStellaError("pack input must contain Stella3 states")
        acc |= state.code << bits
        bits += 5
        while bits >= 8:
            out.append(acc & 0xFF)
            acc >>= 8
            bits -= 8
    if bits:
        out.append(acc & 0xFF)
    return bytes(out)


def unpack_codes_5bit(payload: bytes, count: int) -> tuple[Stella3, ...]:
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise TernaryStellaError("count must be a non-negative integer")
    raw = bytes(payload)
    if len(raw) * 8 < count * 5:
        raise TernaryStellaError("payload is too short for requested Stella count")
    acc = 0
    bits = 0
    offset = 0
    out: list[Stella3] = []
    for _ in range(count):
        while bits < 5:
            if offset >= len(raw):
                raise TernaryStellaError("truncated packed payload")
            acc |= raw[offset] << bits
            bits += 8
            offset += 1
        code = acc & 0x1F
        acc >>= 5
        bits -= 5
        if code >= 27:
            raise TernaryStellaError("packed payload contains invalid 5-bit Stella code")
        out.append(Stella3.from_code(code))
    return tuple(out)


def theoretical_storage_bits(state_count: int) -> dict[str, float]:
    if isinstance(state_count, bool) or not isinstance(state_count, int) or state_count < 0:
        raise TernaryStellaError("state_count must be a non-negative integer")
    return {
        "float64_weights": 64 * state_count,
        "stella3_binary_pack": 5 * state_count,
        "stella3_shannon_floor": math.log2(27) * state_count,
    }


__all__ = [
    "SCHEMA",
    "TRITS",
    "MAX_LEVEL",
    "TernaryStellaError",
    "Stella3",
    "QuantizedWeight",
    "quantize_weight",
    "sign_trit",
    "route_choice_full",
    "route_choice_sign",
    "route_choice_stella3",
    "shell_counts",
    "pack_codes_5bit",
    "unpack_codes_5bit",
    "theoretical_storage_bits",
]
