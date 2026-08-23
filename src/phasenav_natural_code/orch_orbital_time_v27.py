from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

try:
    from .hydro_time_v27 import TAU, _finite, _typed_id
    from .orch_orbital_core_v27 import (
        ORCHORBITAL_CONTRACT_ID, TIME_KERNEL_SCHEMA, TIME_BINDING_SCHEMA,
        OrchOrbitalV27Error, OrchOrbitalState, effective_attractor_weight,
        _signed_phase_delta, _phase, _bounded,
    )
except ImportError:  # isolated harness compatibility
    from hydro_time_v27 import TAU, _finite, _typed_id  # type: ignore
    from orch_orbital_core_v27 import (  # type: ignore
        ORCHORBITAL_CONTRACT_ID, TIME_KERNEL_SCHEMA, TIME_BINDING_SCHEMA,
        OrchOrbitalV27Error, OrchOrbitalState, effective_attractor_weight,
        _signed_phase_delta, _phase, _bounded,
    )

@dataclass(frozen=True)
class SubjectiveTimeKernel:
    bias: float = 0.0
    beta_radius: float = 0.0
    beta_coherence: float = 0.0
    beta_defect: float = 0.0
    beta_mass: float = 0.0
    beta_attractor: float = 0.0
    scale_min: float = 1.0 / 16.0
    scale_max: float = 16.0

    def __post_init__(self) -> None:
        for name in ("bias","beta_radius","beta_coherence","beta_defect","beta_mass","beta_attractor"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        lo = _finite(self.scale_min, "scale_min")
        hi = _finite(self.scale_max, "scale_max")
        if lo <= 0.0 or hi < lo:
            raise OrchOrbitalV27Error("invalid subjective-time scale bounds")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TIME_KERNEL_SCHEMA,
            "contract_id": ORCHORBITAL_CONTRACT_ID,
            "family": "PARAMETRIC_EXPONENTIAL_G",
            "foundation_contract": "Delta_tau_i=Delta_t*g(r_i,C_i,Delta_i,m_i,A_i)",
            "bias": self.bias,
            "beta_radius": self.beta_radius,
            "beta_coherence": self.beta_coherence,
            "beta_defect": self.beta_defect,
            "beta_mass": self.beta_mass,
            "beta_attractor": self.beta_attractor,
            "scale_min": self.scale_min,
            "scale_max": self.scale_max,
            "coefficient_signs_are_explicit_policy": True,
            "physical_calibration_claimed": False,
        }

    @property
    def kernel_id(self) -> str:
        return _typed_id("pncs:orch-time-kernel", self.payload)

    def evaluate(self, *, radius: float, coherence: float, defect: float, semantic_mass: float, attractor_influence: float) -> float:
        r = _finite(radius, "radius")
        if r < 0.0:
            raise OrchOrbitalV27Error("radius must be non-negative")
        c = _bounded(coherence, "coherence", 0.0, 1.0)
        d = _bounded(defect, "defect", 0.0, 1.0)
        m = _finite(semantic_mass, "semantic_mass")
        if m < 0.0:
            raise OrchOrbitalV27Error("semantic_mass must be non-negative")
        a = _bounded(attractor_influence, "attractor_influence", 0.0, 1.0)
        exponent = (
            self.bias
            + self.beta_radius * r
            + self.beta_coherence * c
            + self.beta_defect * d
            + self.beta_mass * m
            + self.beta_attractor * a
        )
        raw = math.exp(exponent)
        return min(self.scale_max, max(self.scale_min, raw))


@dataclass(frozen=True)
class SubjectiveTimeBinding:
    kernel: SubjectiveTimeKernel
    radius: float
    coherence: float
    defect: float
    semantic_mass: float
    attractor_influence: float
    substrate_lapse: float
    coordinate_dt: float
    combined_g: float
    proper_dt: float

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TIME_BINDING_SCHEMA,
            "kernel_id": self.kernel.kernel_id,
            "radius": self.radius,
            "coherence": self.coherence,
            "defect": self.defect,
            "semantic_mass": self.semantic_mass,
            "attractor_influence": self.attractor_influence,
            "substrate_lapse": self.substrate_lapse,
            "coordinate_dt": self.coordinate_dt,
            "orbital_scale": self.kernel.evaluate(
                radius=self.radius,
                coherence=self.coherence,
                defect=self.defect,
                semantic_mass=self.semantic_mass,
                attractor_influence=self.attractor_influence,
            ),
            "combined_g": self.combined_g,
            "proper_dt": self.proper_dt,
            "foundation_contract": "Delta_tau_i=Delta_t*g(r_i,C_i,Delta_i,m_i,A_i)",
            "laboratory_time_modified": False,
        }

    @property
    def binding_id(self) -> str:
        return _typed_id("pncs:orch-time-binding", self.payload)


def bind_subjective_time(
    state: OrchOrbitalState,
    kernel: SubjectiveTimeKernel,
    *,
    orbital_radius: float,
    substrate_lapse: float,
    coordinate_dt: float,
    combined_min: float = 1.0 / 64.0,
    combined_max: float = 8.0,
) -> SubjectiveTimeBinding:
    radius = _finite(orbital_radius, "orbital_radius")
    if radius < 0.0:
        raise OrchOrbitalV27Error("orbital_radius must be non-negative")
    substrate = _finite(substrate_lapse, "substrate_lapse")
    dt = _finite(coordinate_dt, "coordinate_dt")
    lo = _finite(combined_min, "combined_min")
    hi = _finite(combined_max, "combined_max")
    if substrate <= 0.0 or dt <= 0.0 or lo <= 0.0 or hi < lo:
        raise OrchOrbitalV27Error("invalid subjective-time binding bounds")
    c = state.observables.global_coherence
    d = state.observables.defect
    a = effective_attractor_weight(state.attractor_reports)
    scale = kernel.evaluate(radius=radius, coherence=c, defect=d, semantic_mass=state.semantic_mass, attractor_influence=a)
    combined = min(hi, max(lo, substrate * scale))
    return SubjectiveTimeBinding(kernel, radius, c, d, state.semantic_mass, a, substrate, dt, combined, dt * combined)


def winding_increment(delta_phase: float, coordinate_dt: float, proper_dt: float) -> float:
    dphi = _finite(delta_phase, "delta_phase")
    dt = _finite(coordinate_dt, "coordinate_dt")
    d_tau = _finite(proper_dt, "proper_dt")
    if dt <= 0.0 or d_tau <= 0.0:
        raise OrchOrbitalV27Error("winding time increments must be positive")
    return (dphi / TAU) * (dt / d_tau)


def winding_vector(before: Sequence[float], after: Sequence[float], *, coordinate_dt: float, proper_dt: float) -> tuple[float, ...]:
    if len(before) != len(after):
        raise OrchOrbitalV27Error("winding phase sets must have equal length")
    return tuple(winding_increment(_signed_phase_delta(_phase(a), _phase(b)), coordinate_dt, proper_dt) for a, b in zip(before, after))
