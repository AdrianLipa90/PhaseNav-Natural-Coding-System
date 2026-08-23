from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

try:
    from .hydro_time_v27 import DIM, TAU, STATE_SCHEMA as HYDRO_STATE_SCHEMA, PhaseFlowState36, _finite, _typed_id
except ImportError:  # isolated harness compatibility
    from hydro_time_v27 import DIM, TAU, STATE_SCHEMA as HYDRO_STATE_SCHEMA, PhaseFlowState36, _finite, _typed_id  # type: ignore

ORCHORBITAL_CONTRACT_ID = "PNCS_ORCHORBITAL_BINDING_V0_27"
ORCHORBITAL_FOUNDATION_REPOSITORY = "AdrianLipa90/CIEL-Omega-ApokalypOS"
ORCHORBITAL_FOUNDATION_COMMIT = "aa0da54ef29a1f80dd0390427935342225388950"
ORCHORBITAL_FOUNDATION_PATHS = (
    "src/CIEL_Orbital_Foundation_Packk/02_ONTOLOGY_AND_OBSERVABLES.md",
    "src/CIEL_Orbital_Foundation_Packk/03_STATE_SPACE_AND_BOUNDARY_CONDITIONS.md",
    "src/CIEL_Orbital_Foundation_Packk/04_INVARIANTS_POTENTIALS_AND_ATTRACTORS.md",
    "src/CIEL_Orbital_Foundation_Packk/05_ENTITY_REGISTRY_AND_SPHERE_EMBEDDING.md",
    "src/CIEL_Orbital_Foundation_Packk/06_SUBJECTIVE_TIME_WINDING_AND_SEMANTIC_MASS.md",
    "src/CIEL_Orbital_Foundation_Packk/07_OORP_PIPELINE_AND_MEMORY.md",
)
STATE_SCHEMA = "PNCS_ORCHORBITAL_STATE_V0_27"
SPHERE_SCHEMA = "PNCS_ORCHORBITAL_SPHERE_V0_27"
MODE_SCHEMA = "PNCS_ORCHORBITAL_MODE_V0_27"
OBSERVABLES_SCHEMA = "PNCS_ORCHORBITAL_OBSERVABLES_V0_27"
POTENTIAL_SCHEMA = "PNCS_ORCHORBITAL_TOTAL_POTENTIAL_V0_27"
ATTRACTOR_SCHEMA = "PNCS_ORCHORBITAL_ATTRACTOR_REPORT_V0_27"
TIME_KERNEL_SCHEMA = "PNCS_ORCHORBITAL_SUBJECTIVE_TIME_KERNEL_V0_27"
TIME_BINDING_SCHEMA = "PNCS_ORCHORBITAL_SUBJECTIVE_TIME_BINDING_V0_27"
REDUCTION_KERNEL_SCHEMA = "PNCS_ORCHORBITAL_REDUCTION_KERNEL_V0_27"
REDUCTION_SCHEMA = "PNCS_ORCHORBITAL_REDUCTION_DECISION_V0_27"
MEMORY_SCHEMA = "PNCS_ORCHORBITAL_MEMORY_RESIDUE_V0_27"

ATTRACTOR_CLASSES = ("AttractorEC", "AttractorZS", "AttractorLLMTemp")

class OrchOrbitalV27Error(ValueError):
    pass


def _bounded(value: object, field: str, low: float, high: float) -> float:
    x = _finite(value, field)
    if x < low or x > high:
        raise OrchOrbitalV27Error(f"{field} must be in [{low},{high}]")
    return x


def _phase(value: object, field: str = "phase") -> float:
    x = _finite(value, field)
    if x < 0.0 or x >= TAU:
        raise OrchOrbitalV27Error(f"{field} must be in [0,2pi)")
    return x


def _signed_phase_delta(before: float, after: float) -> float:
    raw = (after - before + math.pi) % TAU - math.pi
    if raw == -math.pi and after - before > 0:
        return math.pi
    return raw


@dataclass(frozen=True)
class OrbitalMode:
    index: int
    phase: float
    amplitude: float
    coherence: float
    truth_spin: float | None
    memory_affinity: float

    def __post_init__(self) -> None:
        if isinstance(self.index, bool) or not isinstance(self.index, int) or self.index < 0:
            raise OrchOrbitalV27Error("mode index must be a non-negative integer")
        object.__setattr__(self, "phase", _phase(self.phase))
        amp = _finite(self.amplitude, "amplitude")
        if amp < 0.0:
            raise OrchOrbitalV27Error("amplitude must be non-negative")
        object.__setattr__(self, "amplitude", amp)
        object.__setattr__(self, "coherence", _bounded(self.coherence, "coherence", 0.0, 1.0))
        if self.truth_spin is not None:
            object.__setattr__(self, "truth_spin", _bounded(self.truth_spin, "truth_spin", -1.0, 1.0))
        object.__setattr__(self, "memory_affinity", _bounded(self.memory_affinity, "memory_affinity", 0.0, 1.0))

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": MODE_SCHEMA,
            "index": self.index,
            "amplitude": self.amplitude,
            "phase": self.phase,
            "coherence": self.coherence,
            "truth_spin": self.truth_spin,
            "memory_affinity": self.memory_affinity,
        }

    @property
    def mode_id(self) -> str:
        return _typed_id("pncs:orch-orbital-mode", self.payload)


@dataclass(frozen=True)
class SphereBinding:
    sphere_id: str
    parent_sphere_id: str | None
    child_sphere_ids: tuple[str, ...]
    internal_modes: tuple[str, ...]
    leak_mode: str
    effective_attractor_weight: float

    def __post_init__(self) -> None:
        if not isinstance(self.sphere_id, str) or not self.sphere_id:
            raise OrchOrbitalV27Error("sphere_id required")
        if self.parent_sphere_id is not None and (not isinstance(self.parent_sphere_id, str) or not self.parent_sphere_id):
            raise OrchOrbitalV27Error("parent_sphere_id must be non-empty or null")
        if not isinstance(self.leak_mode, str) or not self.leak_mode:
            raise OrchOrbitalV27Error("leak_mode required")
        object.__setattr__(
            self,
            "effective_attractor_weight",
            _bounded(self.effective_attractor_weight, "effective_attractor_weight", 0.0, 1.0),
        )
        if len(set(self.child_sphere_ids)) != len(self.child_sphere_ids):
            raise OrchOrbitalV27Error("duplicate child sphere ids")
        if len(set(self.internal_modes)) != len(self.internal_modes):
            raise OrchOrbitalV27Error("duplicate internal mode ids")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": SPHERE_SCHEMA,
            "sphere_id": self.sphere_id,
            "parent_sphere_id": self.parent_sphere_id,
            "child_sphere_ids": list(self.child_sphere_ids),
            "internal_modes": list(self.internal_modes),
            "leak_mode": self.leak_mode,
            "effective_attractor_weight": self.effective_attractor_weight,
            "base_relational_manifold": "M_rel",
            "geometric_anchor": "projective_Hilbert_Kahler_Fubini_Study",
            "bloch_chart_role": "LOCAL_REDUCED_CHART_ONLY",
            "poincare_chart_role": "OPERATIONAL_NOT_ONTOLOGICAL",
        }


@dataclass(frozen=True)
class AttractorReport:
    attractor_class: str
    compatibility_score: float
    force_contribution: tuple[float, ...]
    attractor_weight: float
    diagnostic_code: str

    def __post_init__(self) -> None:
        if self.attractor_class not in ATTRACTOR_CLASSES:
            raise OrchOrbitalV27Error("unsupported attractor class")
        object.__setattr__(
            self, "compatibility_score",
            _bounded(self.compatibility_score, "compatibility_score", 0.0, 1.0)
        )
        force = tuple(_finite(v, "force_contribution") for v in self.force_contribution)
        if len(force) != DIM:
            raise OrchOrbitalV27Error(f"force_contribution must contain exactly {DIM} values")
        object.__setattr__(self, "force_contribution", force)
        object.__setattr__(
            self, "attractor_weight",
            _bounded(self.attractor_weight, "attractor_weight", 0.0, 1.0)
        )
        if not isinstance(self.diagnostic_code, str) or not self.diagnostic_code:
            raise OrchOrbitalV27Error("diagnostic_code required")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": ATTRACTOR_SCHEMA,
            "attractor_class": self.attractor_class,
            "compatibility_score": self.compatibility_score,
            "force_contribution": list(self.force_contribution),
            "attractor_weight": self.attractor_weight,
            "diagnostic_code": self.diagnostic_code,
        }

    @property
    def report_id(self) -> str:
        return _typed_id("pncs:orch-attractor", self.payload)


def effective_attractor_weight(reports: Sequence[AttractorReport]) -> float:
    rs = tuple(reports)
    if not rs:
        raise OrchOrbitalV27Error("at least one attractor report required")
    denom = sum(r.attractor_weight for r in rs)
    if denom <= 0.0:
        raise OrchOrbitalV27Error("attractor weights must have positive total")
    return sum(r.attractor_weight * r.compatibility_score for r in rs) / denom


@dataclass(frozen=True)
class TotalPotential:
    v_ec: float
    v_zs: float
    v_rel: float
    v_mem: float
    v_def: float
    v_ext: float

    def __post_init__(self) -> None:
        for name in ("v_ec", "v_zs", "v_rel", "v_mem", "v_def", "v_ext"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))

    @property
    def total(self) -> float:
        return self.v_ec + self.v_zs + self.v_rel + self.v_mem + self.v_def + self.v_ext

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": POTENTIAL_SCHEMA,
            "contract_expression": "V_tot=V_EC+V_ZS+V_rel+V_mem+V_def+V_ext",
            "V_EC": self.v_ec,
            "V_ZS": self.v_zs,
            "V_rel": self.v_rel,
            "V_mem": self.v_mem,
            "V_def": self.v_def,
            "V_ext": self.v_ext,
            "V_tot": self.total,
        }

    @property
    def potential_id(self) -> str:
        return _typed_id("pncs:orch-potential", self.payload)


@dataclass(frozen=True)
class OrchOrbitalObservables:
    global_coherence: float
    defect: float
    holonomic_defect_real: float
    holonomic_defect_imag: float
    relational_decoherence: float
    truth_scalar: float | None

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": OBSERVABLES_SCHEMA,
            "global_coherence": self.global_coherence,
            "defect": self.defect,
            "holonomic_defect": [self.holonomic_defect_real, self.holonomic_defect_imag],
            "relational_decoherence": self.relational_decoherence,
            "truth_scalar": self.truth_scalar,
            "euler_phase_constraint": "sum_k exp(i*gamma_k)=0",
        }

    @property
    def observables_id(self) -> str:
        return _typed_id("pncs:orch-observables", self.payload)


def compute_observables(
    phases: Sequence[float],
    *,
    amplitudes: Sequence[float] | None = None,
    truth_scalar: float | None = None,
) -> OrchOrbitalObservables:
    ps = tuple(_phase(v) for v in phases)
    if not ps:
        raise OrchOrbitalV27Error("phase set must be non-empty")
    if amplitudes is None:
        amps = (1.0,) * len(ps)
    else:
        amps = tuple(_finite(v, "amplitude") for v in amplitudes)
        if len(amps) != len(ps) or any(a < 0.0 for a in amps):
            raise OrchOrbitalV27Error("amplitude set must match phases and be non-negative")
    amp_sum = sum(amps)
    if amp_sum <= 0.0:
        raise OrchOrbitalV27Error("amplitude sum must be positive")
    weighted_real = sum(a * math.cos(p) for a, p in zip(amps, ps)) / amp_sum
    weighted_imag = sum(a * math.sin(p) for a, p in zip(amps, ps)) / amp_sum
    coherence = min(1.0, math.hypot(weighted_real, weighted_imag))
    defect = 1.0 - coherence
    hreal = sum(math.cos(p) for p in ps)
    himag = sum(math.sin(p) for p in ps)
    rh = hreal * hreal + himag * himag
    ts = None if truth_scalar is None else _bounded(truth_scalar, "truth_scalar", 0.0, 1.0)
    return OrchOrbitalObservables(coherence, defect, hreal, himag, rh, ts)


def phase_proximity_couplings(phases: Sequence[float], *, scale: float = 0.15) -> tuple[tuple[float, ...], ...]:
    ps = tuple(_phase(v) for v in phases)
    s = _bounded(scale, "coupling_scale", 0.0, 1.0)
    out: list[tuple[float, ...]] = []
    for i, a in enumerate(ps):
        row = []
        for j, b in enumerate(ps):
            if i == j:
                row.append(0.0)
                continue
            delta = abs(a - b) % TAU
            delta = min(delta, TAU - delta)
            proximity = 1.0 - delta / math.pi
            row.append(max(0.0, proximity) * s)
        out.append(tuple(row))
    return tuple(out)


@dataclass(frozen=True)
class OrchOrbitalState:
    tick: int
    program_content_id: str
    semantic_mass: float
    sphere: SphereBinding
    orbitals: tuple[OrbitalMode, ...]
    couplings: tuple[tuple[float, ...], ...]
    observables: OrchOrbitalObservables
    attractor_reports: tuple[AttractorReport, ...]
    potential: TotalPotential

    def __post_init__(self) -> None:
        if isinstance(self.tick, bool) or not isinstance(self.tick, int) or self.tick < 0:
            raise OrchOrbitalV27Error("tick must be a non-negative integer")
        if not isinstance(self.program_content_id, str) or not self.program_content_id:
            raise OrchOrbitalV27Error("program_content_id required")
        mass = _finite(self.semantic_mass, "semantic_mass")
        if mass < 0.0:
            raise OrchOrbitalV27Error("semantic_mass must be non-negative")
        object.__setattr__(self, "semantic_mass", mass)
        n = len(self.orbitals)
        if n != DIM:
            raise OrchOrbitalV27Error(f"PNCS T^36 binding requires exactly {DIM} orbital modes")
        if len(self.couplings) != n or any(len(row) != n for row in self.couplings):
            raise OrchOrbitalV27Error("coupling matrix must be square over all modes")
        for i, row in enumerate(self.couplings):
            for j, value in enumerate(row):
                v = _finite(value, "coupling")
                if v < 0.0 or v > 1.0:
                    raise OrchOrbitalV27Error("coupling must be in [0,1]")
                if i == j and v != 0.0:
                    raise OrchOrbitalV27Error("coupling diagonal must be zero")
                if abs(v - self.couplings[j][i]) > 1e-12:
                    raise OrchOrbitalV27Error("coupling matrix must be symmetric")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": STATE_SCHEMA,
            "contract_id": ORCHORBITAL_CONTRACT_ID,
            "foundation_repository": ORCHORBITAL_FOUNDATION_REPOSITORY,
            "foundation_commit": ORCHORBITAL_FOUNDATION_COMMIT,
            "foundation_paths": list(ORCHORBITAL_FOUNDATION_PATHS),
            "tick": self.tick,
            "program_content_id": self.program_content_id,
            "semantic_mass": self.semantic_mass,
            "sphere": self.sphere.payload,
            "orbitals": [o.payload for o in self.orbitals],
            "couplings": [list(row) for row in self.couplings],
            "observables": self.observables.payload,
            "attractor_reports": [a.payload for a in self.attractor_reports],
            "effective_attractor_weight": effective_attractor_weight(self.attractor_reports),
            "potential": self.potential.payload,
            "oorp_pipeline": "relation->orbital_superposition->orchestration->reduction->memory_update",
            "external_effects": False,
        }

    @property
    def state_id(self) -> str:
        return _typed_id("pncs:orch-state", self.payload)


def bind_t36_state(
    state: PhaseFlowState36,
    *,
    tick: int,
    program_content_id: str,
    semantic_mass: float,
    attractor_reports: Sequence[AttractorReport],
    potential: TotalPotential,
    sphere_id: str = "pncs:process-sphere:v0.27",
    parent_sphere_id: str | None = "pncs:program-sphere:v0.27",
    leak_mode: str = "PARENT_EMBEDDING_CHANNEL_BOUND",
    memory_affinity: Sequence[float] | None = None,
    truth_spin: Sequence[float | None] | None = None,
    coupling_scale: float = 0.15,
    truth_scalar: float | None = None,
) -> OrchOrbitalState:
    try:
        state_payload = state.payload
        theta = tuple(state.theta)
        velocity = tuple(state.velocity)
    except (AttributeError, TypeError) as exc:
        raise OrchOrbitalV27Error("PhaseFlowState36 contract required") from exc
    if not isinstance(state_payload, dict) or state_payload.get("schema") != HYDRO_STATE_SCHEMA:
        raise OrchOrbitalV27Error("PhaseFlowState36 schema mismatch")
    if len(theta) != DIM or len(velocity) != DIM:
        raise OrchOrbitalV27Error(f"PhaseFlowState36 must contain exactly {DIM} phase and velocity values")
    reports = tuple(attractor_reports)
    aeff = effective_attractor_weight(reports)
    obs = compute_observables(state.theta, truth_scalar=truth_scalar)
    mem = (0.0,) * DIM if memory_affinity is None else tuple(_bounded(v, "memory_affinity", 0.0, 1.0) for v in memory_affinity)
    if len(mem) != DIM:
        raise OrchOrbitalV27Error(f"memory_affinity must contain {DIM} values")
    spins = (None,) * DIM if truth_spin is None else tuple(truth_spin)
    if len(spins) != DIM:
        raise OrchOrbitalV27Error(f"truth_spin must contain {DIM} values")
    orbitals = tuple(
        OrbitalMode(i, state.theta[i], 1.0, obs.global_coherence, spins[i], mem[i])
        for i in range(DIM)
    )
    sphere = SphereBinding(
        sphere_id=sphere_id,
        parent_sphere_id=parent_sphere_id,
        child_sphere_ids=(),
        internal_modes=tuple(o.mode_id for o in orbitals),
        leak_mode=leak_mode,
        effective_attractor_weight=aeff,
    )
    couplings = phase_proximity_couplings(state.theta, scale=coupling_scale)
    return OrchOrbitalState(
        tick=tick,
        program_content_id=program_content_id,
        semantic_mass=semantic_mass,
        sphere=sphere,
        orbitals=orbitals,
        couplings=couplings,
        observables=obs,
        attractor_reports=reports,
        potential=potential,
    )
