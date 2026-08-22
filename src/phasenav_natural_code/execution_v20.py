from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from .execution_v20_model import (
    DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT, EXECUTION_CONTRACT_ID, RECEIPT_SCHEMA,
    EXECUTABLE_INTERNAL_OPERATORS, BoundInternalProgram, NativeExecutionV20Error,
    bind_internal_program, definition_content_id, expected_leaf_path,
    _compact_json, _sha256_json,
)
from .execution_v20_live import LiveSurfaceSnapshot, LiveSurfaceV20Error, load_live_surface
from .execution_v20_state import (
    ExecutionStep, NativeExecutionResult, SigmaState, _Executor, _normalize_values,
)

def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with tmp.open("wb") as fh:
        fh.write(raw)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def execute_admitted_internal(
    program: BoundInternalProgram,
    values: Mapping[str, object],
    admitted_target: str,
    *,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    require_socket: bool = True,
    max_heartbeat_age_s: float = 2.0,
    control_location: str = "pncs.entry",
) -> NativeExecutionResult:
    if not isinstance(program, BoundInternalProgram):
        raise NativeExecutionV20Error("BoundInternalProgram required")
    if not isinstance(control_location, str) or not control_location:
        raise NativeExecutionV20Error("control_location must be non-empty")
    live = load_live_surface(
        surface_root,
        socket_path=socket_path,
        require_socket=require_socket,
        max_heartbeat_age_s=max_heartbeat_age_s,
    )
    normalized_values = _normalize_values(values)
    initial = SigmaState(
        content_id=program.content_id,
        realization_id=program.realization_id,
        mass_binding_id=program.mass_binding_id,
        phase36_sha256=program.phase36_sha256,
        semantic_mass=program.semantic_mass,
        surface_phi_sha256=live.phi_sha256,
        input_values=normalized_values,
        control_location=control_location,
    )
    executor = _Executor(program, live)
    final_state, truth_state = executor.run(initial, admitted_target)
    target = final_state.control_location
    payload = {
        "schema": RECEIPT_SCHEMA,
        "execution_contract_id": EXECUTION_CONTRACT_ID,
        "program": program.provenance_payload,
        "canonical_graph_sha256": _sha256_json(program.canonical_graph),
        "canonical_leaf_path": list(program.leaf_path),
        "live_surface": live.receipt_payload,
        "input_values": [[k, v] for k, v in normalized_values],
        "admission": {
            "branch_truth_state": truth_state,
            "admitted_target": target,
            "epistemic_operator": None,
        },
        "initial_sigma_id": initial.state_id,
        "final_sigma_id": final_state.state_id,
        "steps": [step.payload for step in executor.steps],
        "result": {"kind": "INTERNAL_TRANSFORM", "control_location": target},
        "external_effects": False,
        "semantic_mass_is_authorization": False,
        "free_form_nl_execution": False,
        "deterministic_fields_only": True,
    }
    receipt_sha = _sha256_json(payload)
    receipt = {**payload, "receipt_sha256": receipt_sha}
    runtime_root = Path(surface_root) / "pncs/v0.20"
    receipt_path = runtime_root / "receipts" / f"{receipt_sha}.json"
    state_path = runtime_root / "state/current.json"
    _atomic_write(receipt_path, (_compact_json(receipt) + "\n").encode("utf-8"))
    state_record = {
        **final_state.payload,
        "state_id": final_state.state_id,
        "execution_receipt_sha256": receipt_sha,
    }
    _atomic_write(state_path, (_compact_json(state_record) + "\n").encode("utf-8"))
    return NativeExecutionResult(
        target=target,
        branch_truth_state=truth_state,
        final_state=final_state,
        receipt=receipt,
        receipt_path=str(receipt_path),
    )


def execute_control_resolution(
    resolution: object,
    admission: object,
    realization: object,
    mass_binding: object,
    values: Mapping[str, object],
    **kwargs: object,
) -> NativeExecutionResult:
    """Execute an already-resolved and already-admitted v0.16 internal control graph.

    This function does not parse natural language and cannot create an admission.
    """
    target = getattr(admission, "admitted_target", None)
    epistemic = getattr(admission, "epistemic_operator", None)
    truth_state = getattr(admission, "truth_state", None)
    if target is None or truth_state == "UNRESOLVED" or epistemic == "CHYBA":
        raise NativeExecutionV20Error("execution requires a resolved admitted internal route")
    content = getattr(resolution, "content", None)
    if content is None:
        raise NativeExecutionV20Error("control resolution does not expose DefinitionContent")
    program = bind_internal_program(content, realization, mass_binding)
    return execute_admitted_internal(program, values, str(target), **kwargs)
