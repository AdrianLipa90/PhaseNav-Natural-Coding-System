from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from numbers import Real
from typing import Any

from .semantic_orbital_carrier_v01 import (
    KAPPA,
    OrbitQuantizerProfile,
    SemanticCarrierSample,
    SemanticOrbitalCarrierError,
    bind_semantic_sample,
    carrier_prefactor,
    semantic_value,
)


SCHEMA = "PNCS_SEMANTIC_PHASE_INVERSE_V0_2"
PHASE_PROFILE_ID = "SEMANTIC_VALUE_UNIQUE_LIFTED_PHASE_V0_2"
UNIQUE_LIFTED_PHASE = "UNIQUE_LIFTED_PHASE"
NON_IDENTIFIABLE_PHASE = "NON_IDENTIFIABLE_PHASE"
INCONSISTENT_ZERO_CARRIER = "INCONSISTENT_ZERO_CARRIER"
TAU = 2.0 * math.pi


class SemanticPhaseInverseError(ValueError):
    pass


def _finite(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise SemanticPhaseInverseError(f"{name} must be finite real")
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise SemanticPhaseInverseError(f"{name} must be finite real") from exc
    if not math.isfinite(value):
        raise SemanticPhaseInverseError(f"{name} must be finite real")
    return value


def _text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticPhaseInverseError(f"{name} must be non-empty")
    return value.strip()


def _compose_lifted_phase(wrapped_phase: float, winding: int) -> float:
    wrapped = _finite("wrapped_phase", wrapped_phase)
    if not isinstance(winding, int) or isinstance(winding, bool):
        raise SemanticPhaseInverseError("winding must be an integer")
    if not 0.0 <= wrapped < TAU:
        raise SemanticPhaseInverseError("wrapped_phase must lie in [0,2*pi)")
    try:
        lifted = wrapped + TAU * winding
    except OverflowError as exc:
        raise SemanticPhaseInverseError("lifted_phase must be finite") from exc
    return _finite("lifted_phase", lifted)


def inverse_status(
    semantic_target: float,
    B: float,
    omega: float,
    N: float,
    A_R: float,
) -> str:
    target = _finite("semantic_target", semantic_target)
    try:
        prefactor = carrier_prefactor(B, omega, N, A_R)
    except SemanticOrbitalCarrierError as exc:
        raise SemanticPhaseInverseError(str(exc)) from exc
    if prefactor != 0.0:
        return UNIQUE_LIFTED_PHASE
    if target == 0.0:
        return NON_IDENTIFIABLE_PHASE
    return INCONSISTENT_ZERO_CARRIER


def lifted_phase_from_semantic_value(
    semantic_target: float,
    B: float,
    omega: float,
    N: float,
    A_R: float,
    *,
    kappa: float = KAPPA,
) -> float:
    target = _finite("semantic_target", semantic_target)
    kappa = _finite("kappa", kappa)
    try:
        prefactor = carrier_prefactor(B, omega, N, A_R)
    except SemanticOrbitalCarrierError as exc:
        raise SemanticPhaseInverseError(str(exc)) from exc
    if prefactor == 0.0:
        status = NON_IDENTIFIABLE_PHASE if target == 0.0 else INCONSISTENT_ZERO_CARRIER
        raise SemanticPhaseInverseError(status)
    return _finite("lifted_phase", (target / prefactor) - kappa)


@dataclass(frozen=True)
class CanonicalPhaseSplit:
    lifted_phase: float
    wrapped_phase: float
    winding: int

    def __post_init__(self) -> None:
        lifted = _finite("lifted_phase", self.lifted_phase)
        wrapped = _finite("wrapped_phase", self.wrapped_phase)
        reconstructed = _compose_lifted_phase(wrapped, self.winding)
        if not math.isclose(reconstructed, lifted, rel_tol=0.0, abs_tol=2.0e-12):
            raise SemanticPhaseInverseError("lifted phase does not match wrapped phase plus winding")
        object.__setattr__(self, "lifted_phase", lifted)
        object.__setattr__(self, "wrapped_phase", wrapped)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_profile_id": PHASE_PROFILE_ID,
            "lifted_phase": self.lifted_phase,
            "wrapped_phase": self.wrapped_phase,
            "winding": self.winding,
        }


def canonical_phase_split(lifted_phase: float) -> CanonicalPhaseSplit:
    lifted = _finite("lifted_phase", lifted_phase)
    winding = math.floor(lifted / TAU)
    wrapped = lifted - TAU * winding
    # Guard only against a one-ulp boundary excursion.
    if wrapped >= TAU and math.isclose(wrapped, TAU, rel_tol=0.0, abs_tol=1.0e-14):
        winding += 1
        wrapped = 0.0
    if wrapped < 0.0 and math.isclose(wrapped, 0.0, rel_tol=0.0, abs_tol=1.0e-14):
        wrapped = 0.0
    return CanonicalPhaseSplit(lifted, wrapped, winding)


def lifted_phase_from_split(wrapped_phase: float, winding: int) -> float:
    return _compose_lifted_phase(wrapped_phase, winding)


def semantic_value_from_phase_code(
    wrapped_phase: float,
    winding: int,
    B: float,
    omega: float,
    N: float,
    A_R: float,
    *,
    kappa: float = KAPPA,
) -> float:
    lifted = lifted_phase_from_split(wrapped_phase, winding)
    try:
        return semantic_value(B, omega, N, A_R, lifted, kappa=kappa)
    except SemanticOrbitalCarrierError as exc:
        raise SemanticPhaseInverseError(str(exc)) from exc


@dataclass(frozen=True)
class SemanticPhasePlacement:
    content_id: str
    kaku_id: str
    sample_time: float
    semantic_target: float
    B: float
    omega: float
    N: float
    A_R: float
    phase_code: CanonicalPhaseSplit
    quantizer: OrbitQuantizerProfile
    orbital_band: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_id", _text("content_id", self.content_id))
        object.__setattr__(self, "kaku_id", _text("kaku_id", self.kaku_id))
        if not isinstance(self.phase_code, CanonicalPhaseSplit):
            raise SemanticPhaseInverseError("phase_code must be CanonicalPhaseSplit")
        if not isinstance(self.quantizer, OrbitQuantizerProfile):
            raise SemanticPhaseInverseError("quantizer must be OrbitQuantizerProfile")
        if not isinstance(self.orbital_band, str):
            raise SemanticPhaseInverseError("orbital_band must be an exact string")
        target = _finite("semantic_target", self.semantic_target)
        expected_phase = lifted_phase_from_semantic_value(
            target, self.B, self.omega, self.N, self.A_R
        )
        if not math.isclose(
            expected_phase,
            self.phase_code.lifted_phase,
            rel_tol=0.0,
            abs_tol=2.0e-12,
        ):
            raise SemanticPhaseInverseError("phase code does not encode semantic target")
        expected_band = self.quantizer.quantize(target)
        if self.orbital_band != expected_band:
            raise SemanticPhaseInverseError("orbital band does not match semantic target quantizer")
        object.__setattr__(self, "semantic_target", target)
        object.__setattr__(self, "sample_time", _finite("sample_time", self.sample_time))

    def parent_binding_receipt(self) -> dict[str, Any]:
        sample = SemanticCarrierSample(
            content_id=self.content_id,
            kaku_id=self.kaku_id,
            sample_time=self.sample_time,
            B=self.B,
            omega=self.omega,
            N=self.N,
            A_R=self.A_R,
            phi=self.phase_code.lifted_phase,
        )
        return bind_semantic_sample(sample, self.quantizer).deterministic_receipt()

    def body(self) -> dict[str, Any]:
        try:
            prefactor = carrier_prefactor(self.B, self.omega, self.N, self.A_R)
        except SemanticOrbitalCarrierError as exc:
            raise SemanticPhaseInverseError(str(exc)) from exc
        return {
            "schema": SCHEMA,
            "parent_schema": "PNCS_SEMANTIC_ORBITAL_CARRIER_V0_1",
            "phase_profile_id": PHASE_PROFILE_ID,
            "content_id": self.content_id,
            "kaku_id": self.kaku_id,
            "sample_time": self.sample_time,
            "semantic_target": self.semantic_target,
            "carrier": {
                "B": float(self.B),
                "omega": float(self.omega),
                "N": float(self.N),
                "A_R": float(self.A_R),
                "kappa": KAPPA,
                "prefactor": prefactor,
            },
            "phase_code": self.phase_code.to_dict(),
            "orbit_assignment": {
                "orbital_band": self.orbital_band,
                "quantizer": self.quantizer.to_dict(),
            },
            "roundtrip_semantic_value": semantic_value_from_phase_code(
                self.phase_code.wrapped_phase,
                self.phase_code.winding,
                self.B,
                self.omega,
                self.N,
                self.A_R,
            ),
            "semantic_authority": "EXPLICIT_KAKU_CONTENT_BINDING",
            "epistemic_state": "CHYBA",
            "promotion_state": "CANDIDATE_ONLY",
            "runtime_execution_authority": False,
            "canon_write_authority": False,
        }

    def deterministic_receipt(self) -> dict[str, Any]:
        body = self.body()
        encoded = json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return {**body, "receipt_sha256": hashlib.sha256(encoded).hexdigest()}


def encode_semantic_phase_placement(
    *,
    content_id: str,
    kaku_id: str,
    sample_time: float,
    semantic_target: float,
    B: float,
    omega: float,
    N: float,
    A_R: float,
    quantizer: OrbitQuantizerProfile,
) -> SemanticPhasePlacement:
    phase = lifted_phase_from_semantic_value(semantic_target, B, omega, N, A_R)
    split = canonical_phase_split(phase)
    band = quantizer.quantize(semantic_target)
    return SemanticPhasePlacement(
        content_id=content_id,
        kaku_id=kaku_id,
        sample_time=sample_time,
        semantic_target=semantic_target,
        B=B,
        omega=omega,
        N=N,
        A_R=A_R,
        phase_code=split,
        quantizer=quantizer,
        orbital_band=band,
    )
