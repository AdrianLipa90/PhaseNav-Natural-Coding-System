from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

try:
    from .hydro_time_v27 import _typed_id
    from .execution_orch_authority_v27 import SIGMA_SCHEMA, STEP_SCHEMA, SESSION_SCHEMA
except ImportError:  # isolated harness compatibility
    from hydro_time_v27 import _typed_id  # type: ignore
    from execution_orch_authority_v27 import SIGMA_SCHEMA, STEP_SCHEMA, SESSION_SCHEMA  # type: ignore

@dataclass(frozen=True)
class SigmaState:
    content_id: str
    realization_id: str
    mass_binding_id: str
    phase36_sha256: str
    semantic_mass: float
    surface_phi_sha256: str
    input_values: tuple[tuple[str,float],...]
    control_location: str
    step_index: int=0
    accumulator: float|None=None
    truth_stack: tuple[bool,...]=()
    selected_route: str|None=None
    last_operator: str|None=None

    @property
    def payload(self) -> dict[str,object]:
        return {
            "schema":SIGMA_SCHEMA,
            "content_id":self.content_id,
            "realization_id":self.realization_id,
            "mass_binding_id":self.mass_binding_id,
            "phase36_sha256":self.phase36_sha256,
            "semantic_mass":self.semantic_mass,
            "surface_phi_sha256":self.surface_phi_sha256,
            "input_values":[[k,v] for k,v in self.input_values],
            "control_location":self.control_location,
            "step_index":self.step_index,
            "accumulator":self.accumulator,
            "truth_stack":list(self.truth_stack),
            "selected_route":self.selected_route,
            "last_operator":self.last_operator,
        }

    @property
    def state_id(self) -> str:
        return _typed_id("pncs:sigma",self.payload)


@dataclass(frozen=True)
class SemanticExecutionStep:
    index: int
    operator_id: str
    operator_vector_sha256: str
    before_sigma_id: str
    after_sigma_id: str
    bindings: Mapping[str,object]

    @property
    def payload(self) -> dict[str,object]:
        return {
            "schema":STEP_SCHEMA,
            "index":self.index,
            "operator_id":self.operator_id,
            "operator_vector_sha256":self.operator_vector_sha256,
            "before_sigma_id":self.before_sigma_id,
            "after_sigma_id":self.after_sigma_id,
            "bindings":dict(self.bindings),
        }


@dataclass(frozen=True)
class CoupledExecutionSession:
    authority_id: str
    resident_authority_id: str
    program_content_id: str
    live_phi_sha256: str
    live_operator_registry_sha256: str
    normalized_values: tuple[tuple[str,float],...]
    admitted_target: str
    profile_id: str

    @property
    def payload(self) -> dict[str,object]:
        return {
            "schema":SESSION_SCHEMA,
            "authority_id":self.authority_id,
            "resident_authority_id":self.resident_authority_id,
            "program_content_id":self.program_content_id,
            "live_phi_sha256":self.live_phi_sha256,
            "live_operator_registry_sha256":self.live_operator_registry_sha256,
            "normalized_values":[[k,v] for k,v in self.normalized_values],
            "admitted_target":self.admitted_target,
            "profile_id":self.profile_id,
            "semantic_mass_is_authorization":False,
            "external_effects":False,
        }

    @property
    def session_id(self) -> str:
        return _typed_id("pncs:orch-coupled-session",self.payload)
