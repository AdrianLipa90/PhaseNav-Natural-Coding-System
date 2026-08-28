from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from .pnlf_orbital_memory_v01 import ORBITAL_BANDS, PNLFOrbitalMemoryError


GOVERNOR_SCHEMA = "PNLF_ORBIT_GOVERNOR_V0_1"
CLASSIFICATION_SCHEMA = "PNLF_ORBIT_CLASSIFICATION_V0_1"
PHASE9_QUANTIZER_ID = "PNLF_PHASE9_UNIFORM_V0_1"


class PNLFOrbitGovernorError(PNLFOrbitalMemoryError):
    pass


def _finite(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise PNLFOrbitGovernorError(f"{field} must be finite") from exc
    if not math.isfinite(out):
        raise PNLFOrbitGovernorError(f"{field} must be finite")
    return out


def wrap_phase(value: Any) -> float:
    return _finite(value, "phase") % (2.0 * math.pi)


def phase_distance(phi_memory: Any, phi_attractor: Any) -> float:
    """Circular S1 distance in [0, pi]."""
    a = wrap_phase(phi_memory)
    b = wrap_phase(phi_attractor)
    delta = abs((a - b + math.pi) % (2.0 * math.pi) - math.pi)
    return min(math.pi, max(0.0, delta))


def quantize_phase9(r_phase: Any) -> str:
    """Map circular phase distance [0, pi] deterministically to O0..O8."""
    r = _finite(r_phase, "r_phase")
    if r < 0.0 or r > math.pi:
        raise PNLFOrbitGovernorError("r_phase must be in [0,pi]")
    if r == math.pi:
        return "O8"
    index = min(8, int(math.floor(9.0 * r / math.pi)))
    return f"O{index}"


def band_index(band: str) -> int:
    value = str(band)
    if value not in ORBITAL_BANDS:
        raise PNLFOrbitGovernorError(f"orbital band must be one of {sorted(ORBITAL_BANDS)}")
    return int(value[1:])


def transition_kind(source_band: str, target_band: str) -> str:
    source = band_index(source_band)
    target = band_index(target_band)
    if target < source:
        return "PNLF.ORBIT_PROMOTE"
    if target > source:
        return "PNLF.ORBIT_DEMOTE"
    return "PNLF.ORBIT_BIND"


@dataclass(frozen=True)
class OrbitClassification:
    phi_memory: float
    phi_attractor: float
    r_phase: float
    orbital_band: str
    quantizer_id: str = PHASE9_QUANTIZER_ID

    def __post_init__(self) -> None:
        memory = wrap_phase(self.phi_memory)
        attractor = wrap_phase(self.phi_attractor)
        expected_r = phase_distance(memory, attractor)
        given_r = _finite(self.r_phase, "r_phase")
        if abs(expected_r - given_r) > 1e-12:
            raise PNLFOrbitGovernorError("r_phase does not match memory/attractor phase distance")
        expected_band = quantize_phase9(given_r)
        if self.quantizer_id != PHASE9_QUANTIZER_ID:
            raise PNLFOrbitGovernorError("OrbitClassification v0.1 supports only the explicit PHASE9 quantizer")
        if self.orbital_band != expected_band:
            raise PNLFOrbitGovernorError("orbital_band does not match PHASE9 classification")
        object.__setattr__(self, "phi_memory", memory)
        object.__setattr__(self, "phi_attractor", attractor)
        object.__setattr__(self, "r_phase", given_r)

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "schema": CLASSIFICATION_SCHEMA,
            "governor_contract": GOVERNOR_SCHEMA,
            "quantizer_id": self.quantizer_id,
            "phi_memory": self.phi_memory,
            "phi_attractor": self.phi_attractor,
            "r_phase": self.r_phase,
            "orbital_band": self.orbital_band,
            "classification_only": True,
            "stable_memory_admission": False,
            "runtime_execution_authority": False,
            "canon_write_authority": False,
        }


def classify_phase9(phi_memory: Any, phi_attractor: Any) -> OrbitClassification:
    memory = wrap_phase(phi_memory)
    attractor = wrap_phase(phi_attractor)
    r = phase_distance(memory, attractor)
    return OrbitClassification(
        phi_memory=memory,
        phi_attractor=attractor,
        r_phase=r,
        orbital_band=quantize_phase9(r),
    )


def classify_transition(source_band: str, phi_memory: Any, phi_attractor: Any) -> dict[str, Any]:
    classification = classify_phase9(phi_memory, phi_attractor)
    return {
        "schema": GOVERNOR_SCHEMA,
        "source_band": str(source_band),
        "target_band": classification.orbital_band,
        "transition": transition_kind(source_band, classification.orbital_band),
        "classification": classification.payload,
        "requires_reduction_admission": True,
        "stable_memory_update": False,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
    }


__all__ = [
    "GOVERNOR_SCHEMA",
    "CLASSIFICATION_SCHEMA",
    "PHASE9_QUANTIZER_ID",
    "PNLFOrbitGovernorError",
    "OrbitClassification",
    "wrap_phase",
    "phase_distance",
    "quantize_phase9",
    "band_index",
    "transition_kind",
    "classify_phase9",
    "classify_transition",
]
