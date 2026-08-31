from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
import hashlib
import json
import math
from numbers import Real
from typing import Any, Mapping

from .pnlf_orbital_memory_v01 import ORBITAL_BANDS, OrbitalState


SCHEMA = "PNCS_SEMANTIC_ORBITAL_CARRIER_V0_1"
FORMULA_ID = "S=(B*omega*N/A_R)*(phi+kappa)"
KAPPA = math.log(2.0) / (24.0 * math.pi)
ASCENDING_BAND_ORDER = tuple(f"O{i}" for i in range(9))
DEFAULT_BANDS = ASCENDING_BAND_ORDER


class SemanticOrbitalCarrierError(ValueError):
    pass


def _finite(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise SemanticOrbitalCarrierError(f"{name} must be finite real")
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise SemanticOrbitalCarrierError(f"{name} must be finite real") from exc
    if not math.isfinite(out):
        raise SemanticOrbitalCarrierError(f"{name} must be finite real")
    return out


def _text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticOrbitalCarrierError(f"{name} must be a non-empty string")
    return value.strip()


def _explicit_sequence(name: str, value: object) -> tuple[object, ...]:
    if not isinstance(value, (tuple, list)):
        raise SemanticOrbitalCarrierError(f"{name} must be an explicit list or tuple")
    return tuple(value)


def _canonical_json_value(value: object, *, path: str) -> object:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SemanticOrbitalCarrierError(
                "source_orbital_state must be finite canonical JSON"
            )
        return value
    if isinstance(value, (list, tuple)):
        return [
            _canonical_json_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise SemanticOrbitalCarrierError(
                "source_orbital_state mapping keys must be strings"
            )
        return {
            key: _canonical_json_value(value[key], path=f"{path}.{key}")
            for key in sorted(value)
        }
    raise SemanticOrbitalCarrierError(
        f"source_orbital_state contains unsupported canonical type at {path}: "
        f"{type(value).__name__}"
    )


def _canonical_source_snapshot(value: Mapping[str, Any] | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise SemanticOrbitalCarrierError("source_orbital_state must be a mapping")
    canonical = _canonical_json_value(value, path="source_orbital_state")
    try:
        return json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise SemanticOrbitalCarrierError(
            "source_orbital_state must be finite canonical JSON"
        ) from exc


def carrier_prefactor(B: float, omega: float, N: float, A_R: float) -> float:
    B = _finite("B", B)
    omega = _finite("omega", omega)
    N = _finite("N", N)
    A_R = _finite("A_R", A_R)
    if A_R == 0.0:
        raise SemanticOrbitalCarrierError("A_R must be nonzero")
    return _finite("carrier_prefactor", (B * omega * N) / A_R)


def shifted_phase(phi: float, kappa: float = KAPPA) -> float:
    phi = _finite("phi", phi)
    kappa = _finite("kappa", kappa)
    return _finite("phase_plus_kappa", phi + kappa)


def semantic_value(
    B: float,
    omega: float,
    N: float,
    A_R: float,
    phi: float,
    *,
    kappa: float = KAPPA,
) -> float:
    value = carrier_prefactor(B, omega, N, A_R) * shifted_phase(phi, kappa)
    return _finite("semantic_value", value)


@dataclass(frozen=True)
class SemanticCarrierSample:
    content_id: str
    kaku_id: str
    sample_time: float
    B: float
    omega: float
    N: float
    A_R: float
    phi: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_id", _text("content_id", self.content_id))
        object.__setattr__(self, "kaku_id", _text("kaku_id", self.kaku_id))
        object.__setattr__(self, "sample_time", _finite("sample_time", self.sample_time))
        object.__setattr__(self, "B", _finite("B", self.B))
        object.__setattr__(self, "omega", _finite("omega", self.omega))
        object.__setattr__(self, "N", _finite("N", self.N))
        A_R = _finite("A_R", self.A_R)
        if A_R == 0.0:
            raise SemanticOrbitalCarrierError("A_R must be nonzero")
        object.__setattr__(self, "A_R", A_R)
        object.__setattr__(self, "phi", _finite("phi", self.phi))

    @property
    def prefactor(self) -> float:
        return carrier_prefactor(self.B, self.omega, self.N, self.A_R)

    @property
    def phase_kappa(self) -> float:
        return shifted_phase(self.phi)

    @property
    def value(self) -> float:
        return semantic_value(self.B, self.omega, self.N, self.A_R, self.phi)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_id": self.content_id,
            "kaku_id": self.kaku_id,
            "sample_time": self.sample_time,
            "B": self.B,
            "omega": self.omega,
            "N": self.N,
            "A_R": self.A_R,
            "phi": self.phi,
            "kappa": KAPPA,
            "carrier_prefactor": self.prefactor,
            "phase_plus_kappa": self.phase_kappa,
            "semantic_value": self.value,
        }


@dataclass(frozen=True)
class OrbitQuantizerProfile:
    quantizer_id: str
    boundaries: tuple[float, ...]
    bands: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantizer_id", _text("quantizer_id", self.quantizer_id))
        raw_boundaries = _explicit_sequence("boundaries", self.boundaries)
        boundaries = tuple(
            _finite(f"boundaries[{i}]", x) for i, x in enumerate(raw_boundaries)
        )
        if len(boundaries) != 8:
            raise SemanticOrbitalCarrierError("nine orbital bands require exactly eight boundaries")
        if any(b >= c for b, c in zip(boundaries, boundaries[1:])):
            raise SemanticOrbitalCarrierError("boundaries must be strictly increasing")
        object.__setattr__(self, "boundaries", boundaries)

        raw_bands = _explicit_sequence("bands", self.bands)
        if any(not isinstance(item, str) for item in raw_bands):
            raise SemanticOrbitalCarrierError("bands must contain exact string identities")
        bands = tuple(raw_bands)
        if len(bands) != 9:
            raise SemanticOrbitalCarrierError("bands must contain exactly nine entries")
        if len(set(bands)) != 9 or set(bands) != set(ORBITAL_BANDS):
            raise SemanticOrbitalCarrierError("bands must be a permutation of O0..O8")
        object.__setattr__(self, "bands", bands)

    def quantize(self, value: float) -> str:
        value = _finite("semantic_value", value)
        return self.bands[bisect_right(self.boundaries, value)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "quantizer_id": self.quantizer_id,
            "boundaries": list(self.boundaries),
            "bands": list(self.bands),
        }


@dataclass(frozen=True)
class SemanticOrbitalBinding:
    sample: SemanticCarrierSample
    quantizer: OrbitQuantizerProfile
    orbital_band: str
    source_orbital_state: Mapping[str, Any] | None = None
    _source_snapshot_json: str | None = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.sample, SemanticCarrierSample):
            raise SemanticOrbitalCarrierError("sample must be SemanticCarrierSample")
        if not isinstance(self.quantizer, OrbitQuantizerProfile):
            raise SemanticOrbitalCarrierError("quantizer must be OrbitQuantizerProfile")
        if not isinstance(self.orbital_band, str):
            raise SemanticOrbitalCarrierError("orbital_band must be an exact string identity")
        expected = self.quantizer.quantize(self.sample.value)
        if self.orbital_band != expected:
            raise SemanticOrbitalCarrierError("orbital_band must equal quantized semantic value")
        object.__setattr__(
            self,
            "_source_snapshot_json",
            _canonical_source_snapshot(self.source_orbital_state),
        )

    def body(self) -> dict[str, Any]:
        source_snapshot = (
            None
            if self._source_snapshot_json is None
            else json.loads(self._source_snapshot_json)
        )
        return {
            "schema": SCHEMA,
            "formula_id": FORMULA_ID,
            "sample": self.sample.to_dict(),
            "orbit_assignment": {
                "orbital_band": self.orbital_band,
                "quantizer": self.quantizer.to_dict(),
            },
            "source_orbital_state": source_snapshot,
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
        return {
            **body,
            "receipt_sha256": hashlib.sha256(encoded).hexdigest(),
        }


def bind_semantic_sample(
    sample: SemanticCarrierSample,
    quantizer: OrbitQuantizerProfile,
    *,
    source_orbital_state: Mapping[str, Any] | None = None,
) -> SemanticOrbitalBinding:
    if not isinstance(sample, SemanticCarrierSample):
        raise SemanticOrbitalCarrierError("sample must be SemanticCarrierSample")
    if not isinstance(quantizer, OrbitQuantizerProfile):
        raise SemanticOrbitalCarrierError("quantizer must be OrbitQuantizerProfile")
    return SemanticOrbitalBinding(
        sample=sample,
        quantizer=quantizer,
        orbital_band=quantizer.quantize(sample.value),
        source_orbital_state=source_orbital_state,
    )


def sample_from_orbital_state(
    *,
    content_id: str,
    kaku_id: str,
    orbital_state: OrbitalState,
    B: float,
    N: float,
    A_R: float,
    sample_time: float | None = None,
) -> tuple[SemanticCarrierSample, dict[str, Any]]:
    if not isinstance(orbital_state, OrbitalState):
        raise SemanticOrbitalCarrierError("orbital_state must be OrbitalState")
    omega = (2.0 * math.pi) / orbital_state.orbit_period
    t = orbital_state.proper_time if sample_time is None else _finite("sample_time", sample_time)
    sample = SemanticCarrierSample(
        content_id=content_id,
        kaku_id=kaku_id,
        sample_time=t,
        B=B,
        omega=omega,
        N=N,
        A_R=A_R,
        phi=orbital_state.phase,
    )
    source = {
        "attractor_id": orbital_state.attractor_id,
        "orbital_band": orbital_state.orbital_band,
        "phase": orbital_state.phase,
        "winding": orbital_state.winding,
        "orbit_period": orbital_state.orbit_period,
        "proper_time": orbital_state.proper_time,
        "orbit_quantizer_id": orbital_state.orbit_quantizer_id,
        "omega_projection": "2*pi/orbit_period",
    }
    return sample, source


def bind_orbital_state_sample(
    *,
    content_id: str,
    kaku_id: str,
    orbital_state: OrbitalState,
    B: float,
    N: float,
    A_R: float,
    quantizer: OrbitQuantizerProfile,
    sample_time: float | None = None,
) -> SemanticOrbitalBinding:
    if not isinstance(quantizer, OrbitQuantizerProfile):
        raise SemanticOrbitalCarrierError("quantizer must be OrbitQuantizerProfile")
    sample, source = sample_from_orbital_state(
        content_id=content_id,
        kaku_id=kaku_id,
        orbital_state=orbital_state,
        B=B,
        N=N,
        A_R=A_R,
        sample_time=sample_time,
    )
    return bind_semantic_sample(sample, quantizer, source_orbital_state=source)
