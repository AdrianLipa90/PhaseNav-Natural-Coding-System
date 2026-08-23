from __future__ import annotations

from dataclasses import dataclass

try:
    from .hydro_time_v27 import _finite, _typed_id
    from .orch_orbital_core_v27 import OrchOrbitalV27Error, OrchOrbitalState, _bounded, REDUCTION_KERNEL_SCHEMA, REDUCTION_SCHEMA, MEMORY_SCHEMA
except ImportError:  # isolated harness compatibility
    from hydro_time_v27 import _finite, _typed_id  # type: ignore
    from orch_orbital_core_v27 import OrchOrbitalV27Error, OrchOrbitalState, _bounded, REDUCTION_KERNEL_SCHEMA, REDUCTION_SCHEMA, MEMORY_SCHEMA  # type: ignore

@dataclass(frozen=True)
class ReductionKernel:
    lambda1: float
    lambda2: float
    lambda3: float
    lambda4: float
    omega_crit: float

    def __post_init__(self) -> None:
        for name in ("lambda1","lambda2","lambda3","lambda4","omega_crit"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": REDUCTION_KERNEL_SCHEMA,
            "contract_expression": "Omega=lambda1*C+lambda2*R(S,I)-lambda3*Delta-lambda4*Xi",
            "lambda1": self.lambda1,
            "lambda2": self.lambda2,
            "lambda3": self.lambda3,
            "lambda4": self.lambda4,
            "omega_crit": self.omega_crit,
        }

    @property
    def kernel_id(self) -> str:
        return _typed_id("pncs:orch-reduction-kernel", self.payload)

    def omega(self, *, coherence: float, relation_alignment: float, defect: float, xi: float) -> float:
        c = _bounded(coherence, "coherence", 0.0, 1.0)
        r = _finite(relation_alignment, "relation_alignment")
        d = _bounded(defect, "defect", 0.0, 1.0)
        x = _finite(xi, "xi")
        return self.lambda1*c + self.lambda2*r - self.lambda3*d - self.lambda4*x


@dataclass(frozen=True)
class ReductionDecision:
    kernel: ReductionKernel
    state_id: str
    omega: float
    reduce_ready: bool
    relation_alignment: float
    xi: float
    selected_orbital_index: int | None

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": REDUCTION_SCHEMA,
            "kernel_id": self.kernel.kernel_id,
            "state_id": self.state_id,
            "omega": self.omega,
            "omega_crit": self.kernel.omega_crit,
            "reduce_ready": self.reduce_ready,
            "relation_alignment": self.relation_alignment,
            "xi": self.xi,
            "selected_orbital_index": self.selected_orbital_index,
            "selection_implicit": False,
        }

    @property
    def decision_id(self) -> str:
        return _typed_id("pncs:orch-reduction", self.payload)


def decide_reduction(
    state: OrchOrbitalState,
    kernel: ReductionKernel,
    *,
    relation_alignment: float,
    xi: float,
    selected_orbital_index: int | None = None,
) -> ReductionDecision:
    omega = kernel.omega(
        coherence=state.observables.global_coherence,
        relation_alignment=relation_alignment,
        defect=state.observables.defect,
        xi=xi,
    )
    ready = omega >= kernel.omega_crit
    if selected_orbital_index is not None:
        if isinstance(selected_orbital_index, bool) or not isinstance(selected_orbital_index, int):
            raise OrchOrbitalV27Error("selected_orbital_index must be integer or null")
        if selected_orbital_index < 0 or selected_orbital_index >= len(state.orbitals):
            raise OrchOrbitalV27Error("selected_orbital_index out of range")
        if not ready:
            raise OrchOrbitalV27Error("selection cannot occur before reduction threshold")
    return ReductionDecision(
        kernel=kernel,
        state_id=state.state_id,
        omega=omega,
        reduce_ready=ready,
        relation_alignment=_finite(relation_alignment, "relation_alignment"),
        xi=_finite(xi, "xi"),
        selected_orbital_index=selected_orbital_index,
    )


@dataclass(frozen=True)
class MemoryResidue:
    reduction_decision_id: str
    prior_memory_id: str | None
    selected_orbital_id: str
    program_content_id: str
    identity_input_id: str

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": MEMORY_SCHEMA,
            "reduction_decision_id": self.reduction_decision_id,
            "prior_memory_id": self.prior_memory_id,
            "selected_orbital_id": self.selected_orbital_id,
            "program_content_id": self.program_content_id,
            "identity_input_id": self.identity_input_id,
            "memory_semantics": "REDUCTION_RESIDUE_NOT_RAW_INPUT_STORAGE",
            "stable_memory_update": True,
            "external_effects": False,
        }

    @property
    def residue_id(self) -> str:
        return _typed_id("pncs:orch-memory-residue", self.payload)


def memory_residue_after_reduction(
    state: OrchOrbitalState,
    decision: ReductionDecision,
    *,
    identity_input_id: str,
    prior_memory_id: str | None = None,
) -> MemoryResidue | None:
    if decision.state_id != state.state_id:
        raise OrchOrbitalV27Error("reduction decision/state mismatch")
    if not decision.reduce_ready or decision.selected_orbital_index is None:
        return None
    if not isinstance(identity_input_id, str) or not identity_input_id:
        raise OrchOrbitalV27Error("identity_input_id required")
    selected = state.orbitals[decision.selected_orbital_index]
    return MemoryResidue(
        decision.decision_id,
        prior_memory_id,
        selected.mode_id,
        state.program_content_id,
        identity_input_id,
    )
