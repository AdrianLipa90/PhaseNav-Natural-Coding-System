from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
from pathlib import Path
from typing import Mapping

from .adversarial_v28 import validate_coupled_receipt_structure
from .execution_v20_live import LiveSurfaceSnapshot, load_live_surface
from .execution_v20_model import (
    BoundInternalProgram,
    DEFAULT_SOCKET,
    DEFAULT_SURFACE_ROOT,
    EXECUTION_CONTRACT_ID,
    RECEIPT_SCHEMA,
    _sha256_json,
)
from .execution_v20_state import SigmaState as V20SigmaState, _Executor as V20Executor, _normalize_values
from .execution_orch_authority_v27 import (
    COUPLED_EXECUTION_CONTRACT_ID,
    COUPLED_RECEIPT_SCHEMA,
    ProgramAuthority,
)
from .execution_orch_executor_v27 import _CoupledExecutor
from .execution_orch_state_v27 import CoupledExecutionSession, SigmaState as CoupledSigmaState
from .hydro_time_v27 import HydrodynamicPhaseGate, PhaseFlowState36
from .orch_hydro_v27 import OrchHydroControlProfile

PAIRED_SNAPSHOT_CONTRACT_ID = "PNCS_V0_28_SAME_LIVE_SNAPSHOT_CONFORMANCE"
PAIRED_RESIDENT_SENTINEL = "PAIRED_SNAPSHOT_CONFORMANCE_ONLY_NO_RESIDENT_EXECUTION_AUTHORITY"


class PairedSnapshotV28Error(RuntimeError):
    pass


def _capture_live_snapshot(
    root: Path,
    *,
    socket_path: Path,
    max_heartbeat_age_s: float,
    attempts: int = 16,
) -> tuple[LiveSurfaceSnapshot, bytes]:
    if root != DEFAULT_SURFACE_ROOT:
        raise PairedSnapshotV28Error("paired live conformance is fixed to /dev/shm/ciel_noema")
    for _ in range(attempts):
        live = load_live_surface(
            root,
            socket_path=socket_path,
            require_socket=True,
            max_heartbeat_age_s=max_heartbeat_age_s,
        )
        raw = (root / "phi").read_bytes()
        if len(raw) != 36 * 8:
            continue
        if hashlib.sha256(raw).hexdigest() == live.phi_sha256:
            return live, raw
    raise PairedSnapshotV28Error("could not capture a coherent live phi snapshot")


def _baseline_receipt(
    program: BoundInternalProgram,
    live: LiveSurfaceSnapshot,
    values: Mapping[str, object],
    admitted_target: str,
    *,
    control_location: str,
) -> dict[str, object]:
    normalized = _normalize_values(values)
    initial = V20SigmaState(
        content_id=program.content_id,
        realization_id=program.realization_id,
        mass_binding_id=program.mass_binding_id,
        phase36_sha256=program.phase36_sha256,
        semantic_mass=program.semantic_mass,
        surface_phi_sha256=live.phi_sha256,
        input_values=normalized,
        control_location=control_location,
    )
    executor = V20Executor(program, live)
    final_state, truth_state = executor.run(initial, admitted_target)
    payload = {
        "schema": RECEIPT_SCHEMA,
        "execution_contract_id": EXECUTION_CONTRACT_ID,
        "program": program.provenance_payload,
        "canonical_graph_sha256": _sha256_json(program.canonical_graph),
        "canonical_leaf_path": list(program.leaf_path),
        "live_surface": live.receipt_payload,
        "input_values": [[k, v] for k, v in normalized],
        "admission": {
            "branch_truth_state": truth_state,
            "admitted_target": final_state.control_location,
            "epistemic_operator": None,
        },
        "initial_sigma_id": initial.state_id,
        "final_sigma_id": final_state.state_id,
        "steps": [step.payload for step in executor.steps],
        "result": {"kind": "INTERNAL_TRANSFORM", "control_location": final_state.control_location},
        "external_effects": False,
        "semantic_mass_is_authorization": False,
        "free_form_nl_execution": False,
        "deterministic_fields_only": True,
    }
    return {**payload, "receipt_sha256": _sha256_json(payload)}


def _coupled_receipt_same_snapshot(
    source_receipt: Mapping[str, object],
    program: BoundInternalProgram,
    live: LiveSurfaceSnapshot,
    phi_raw: bytes,
    values: Mapping[str, object],
    admitted_target: str,
    profile: OrchHydroControlProfile,
    gate_policy: Mapping[str, object],
    *,
    control_location: str,
) -> dict[str, object]:
    authority = ProgramAuthority.from_v20_receipt(source_receipt, program.canonical_graph)
    normalized = _normalize_values(values)
    session = CoupledExecutionSession(
        authority.authority_id,
        PAIRED_RESIDENT_SENTINEL,
        authority.content_id,
        live.phi_sha256,
        live.operator_registry_sha256,
        normalized,
        admitted_target,
        profile.profile_id,
    )
    theta = struct.unpack("<36d", phi_raw)
    phase_state = PhaseFlowState36(theta)
    initial = CoupledSigmaState(
        authority.content_id,
        authority.realization_id,
        authority.mass_binding_id,
        authority.phase36_sha256,
        authority.semantic_mass,
        live.phi_sha256,
        normalized,
        control_location,
    )
    executor = _CoupledExecutor(
        authority,
        live.operator_vectors,
        live.phi_sha256,
        phase_state,
        profile,
        gate_policy,
        session.session_id,
    )
    final_state, truth_state = executor.run(initial, admitted_target)
    semantic_projection = {
        "program": authority.provenance_payload,
        "canonical_graph_sha256": authority.canonical_graph_sha256,
        "canonical_leaf_path": list(authority.leaf_path),
        "input_values": [[k, v] for k, v in normalized],
        "admission": {
            "branch_truth_state": truth_state,
            "admitted_target": final_state.control_location,
            "epistemic_operator": None,
        },
        "initial_sigma_id": initial.state_id,
        "final_sigma_id": final_state.state_id,
        "steps": [step.payload for step in executor.steps],
        "result": {"kind": "INTERNAL_TRANSFORM", "control_location": final_state.control_location},
        "external_effects": False,
        "semantic_mass_is_authorization": False,
        "free_form_nl_execution": False,
        "deterministic_fields_only": True,
    }
    payload = {
        "schema": COUPLED_RECEIPT_SCHEMA,
        "execution_contract_id": COUPLED_EXECUTION_CONTRACT_ID,
        "source_v20_authority_receipt_sha256": source_receipt["receipt_sha256"],
        "program_authority_id": authority.authority_id,
        "resident_authority_id": PAIRED_RESIDENT_SENTINEL,
        "resident_dispatch_id": None,
        "resident_handle_id": None,
        "runtime_generation_id": None,
        "resident_program_id": None,
        "v22_result_id": None,
        "v22_lineage_id": None,
        "session_id": session.session_id,
        "profile_id": profile.profile_id,
        "live_surface": {
            "root": live.root,
            "phi_sha256": live.phi_sha256,
            "operator_registry_sha256": live.operator_registry_sha256,
        },
        "semantic_projection": semantic_projection,
        "semantic_projection_sha256": _sha256_json(semantic_projection),
        "orch_occurrences": [occurrence.payload for occurrence in executor.occurrences],
        "orch_occurrence_ids": [occurrence.occurrence_id for occurrence in executor.occurrences],
        "final_phase_state_id": executor.phase_state.state_id,
        "phase_proper_time_advanced": executor.phase_state.phase_proper_time - phase_state.phase_proper_time,
        "stable_memory_update_count": sum(int(occurrence.memory_residue is not None) for occurrence in executor.occurrences),
        "routing_feedback_opened": False,
        "semantic_identity_modified": False,
        "external_effects": False,
        "laboratory_time_modified": False,
        "deterministic_fields_only": True,
        "paired_snapshot_conformance_only": True,
        "operational_resident_authority_opened": False,
    }
    # v0.28 validator intentionally ignores the two paired-harness audit fields;
    # they make the non-operational scope explicit without affecting semantic authority.
    return {**payload, "receipt_sha256": _sha256_json(payload)}


@dataclass(frozen=True)
class PairedSnapshotResult:
    live_phi_sha256: str
    operator_registry_sha256: str
    source_receipt: Mapping[str, object]
    coupled_receipt: Mapping[str, object]

    @property
    def semantic_projection_equal(self) -> bool:
        coupled = self.coupled_receipt["semantic_projection"]
        if not isinstance(coupled, Mapping):
            return False
        fields = (
            "program",
            "canonical_graph_sha256",
            "canonical_leaf_path",
            "input_values",
            "admission",
            "initial_sigma_id",
            "final_sigma_id",
            "steps",
            "result",
            "external_effects",
            "semantic_mass_is_authorization",
            "free_form_nl_execution",
            "deterministic_fields_only",
        )
        return all(coupled.get(field) == self.source_receipt.get(field) for field in fields)


def run_same_snapshot_conformance(
    program: BoundInternalProgram,
    values: Mapping[str, object],
    admitted_target: str,
    profile: OrchHydroControlProfile,
    gate_policy: Mapping[str, HydrodynamicPhaseGate],
    *,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
    control_location: str = "pncs.entry",
) -> PairedSnapshotResult:
    if not isinstance(program, BoundInternalProgram):
        raise PairedSnapshotV28Error("BoundInternalProgram required")
    root = Path(surface_root)
    live, phi_raw = _capture_live_snapshot(
        root,
        socket_path=Path(socket_path),
        max_heartbeat_age_s=max_heartbeat_age_s,
    )
    source = _baseline_receipt(
        program,
        live,
        values,
        admitted_target,
        control_location=control_location,
    )
    coupled = _coupled_receipt_same_snapshot(
        source,
        program,
        live,
        phi_raw,
        values,
        admitted_target,
        profile,
        gate_policy,
        control_location=control_location,
    )
    result = PairedSnapshotResult(live.phi_sha256, live.operator_registry_sha256, source, coupled)
    if not result.semantic_projection_equal:
        raise PairedSnapshotV28Error("same-snapshot coupled semantic projection differs from v0.20 baseline")
    validate_coupled_receipt_structure(coupled, source_v20_receipt=source)
    return result
