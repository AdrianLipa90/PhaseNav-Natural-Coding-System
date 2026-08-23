from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Mapping, Sequence

try:
    from .hydro_time_v27 import (
        DEFAULT_SURFACE_ROOT,
        HydrodynamicPhaseGate,
        HydrodynamicProperTimeV27Error,
        HydrodynamicTrace,
        PhaseFlowState36,
        _compact_json,
        _sha256_bytes,
        _sha256_json,
        _typed_id,
        _normalize_drive,
        run_hydrodynamic_gate,
    )
except ImportError:  # isolated harness compatibility
    from hydro_time_v27 import (  # type: ignore
        DEFAULT_SURFACE_ROOT,
        HydrodynamicPhaseGate,
        HydrodynamicProperTimeV27Error,
        HydrodynamicTrace,
        PhaseFlowState36,
        _compact_json,
        _sha256_bytes,
        _sha256_json,
        _typed_id,
        _normalize_drive,
        run_hydrodynamic_gate,
    )

SCHEDULE_CONTRACT_ID = "PNCS_HYDRODYNAMIC_KAKU_SCHEDULE_V0_27"
SCHEDULE_SCHEMA = "PNCS_HYDRODYNAMIC_KAKU_SCHEDULE_V0_27"
SCHEDULE_ENTRY_SCHEMA = "PNCS_HYDRODYNAMIC_KAKU_SCHEDULE_ENTRY_V0_27"
EXECUTION_TRACE_SCHEMA = "PNCS_HYDRODYNAMIC_EXECUTION_TRACE_V0_27"
V20_RECEIPT_SCHEMA = "PNCS_NATIVE_EXECUTION_RECEIPT_V0_20"
V20_CONTRACT_ID = "PNCS_NATIVE_EXECUTION_CORE_V0_20"

class HydrodynamicScheduleV27Error(ValueError):
    pass


def _validate_v20_receipt(receipt: Mapping[str, object]) -> str:
    if not isinstance(receipt, Mapping):
        raise HydrodynamicScheduleV27Error("v0.20 receipt mapping required")
    if receipt.get("schema") != V20_RECEIPT_SCHEMA or receipt.get("execution_contract_id") != V20_CONTRACT_ID:
        raise HydrodynamicScheduleV27Error("exact v0.20 execution receipt required")
    claimed = receipt.get("receipt_sha256")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise HydrodynamicScheduleV27Error("v0.20 receipt SHA-256 missing")
    body = dict(receipt); body.pop("receipt_sha256", None)
    actual = _sha256_json(body)
    if actual != claimed:
        raise HydrodynamicScheduleV27Error("v0.20 receipt digest mismatch")
    if receipt.get("external_effects") is not False or receipt.get("free_form_nl_execution") is not False:
        raise HydrodynamicScheduleV27Error("v0.20 receipt crossed closed execution boundary")
    steps = receipt.get("steps")
    if not isinstance(steps, list) or not steps:
        raise HydrodynamicScheduleV27Error("v0.20 receipt has no execution steps")
    previous_after = receipt.get("initial_sigma_id")
    for expected_index, step in enumerate(steps, start=1):
        if not isinstance(step, Mapping) or step.get("schema") != "PNCS_KAKU_TRANSITION_V0_20":
            raise HydrodynamicScheduleV27Error("invalid v0.20 KAKU step")
        if step.get("index") != expected_index:
            raise HydrodynamicScheduleV27Error("v0.20 KAKU step index discontinuity")
        if step.get("before_sigma_id") != previous_after:
            raise HydrodynamicScheduleV27Error("v0.20 Sigma chain discontinuity")
        previous_after = step.get("after_sigma_id")
    if previous_after != receipt.get("final_sigma_id"):
        raise HydrodynamicScheduleV27Error("v0.20 final Sigma mismatch")
    return claimed


def load_live_operator_vectors(surface_root: Path | str = DEFAULT_SURFACE_ROOT, *, require_canonical_root: bool = True) -> tuple[dict[str, tuple[float, ...]], str]:
    root = Path(surface_root)
    if require_canonical_root and root != DEFAULT_SURFACE_ROOT:
        raise HydrodynamicScheduleV27Error("live schedule runtime is fixed to /dev/shm/ciel_noema")
    try:
        if (root / "ciel_binding_status").read_text("utf-8").strip() != "ACTIVE":
            raise HydrodynamicScheduleV27Error("live NOEMA binding is not ACTIVE")
        raw = (root / "phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl").read_bytes()
    except OSError as exc:
        raise HydrodynamicScheduleV27Error("live operator registry unavailable") from exc
    out: dict[str, tuple[float, ...]] = {}
    for line_no, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try: rec = json.loads(line)
        except json.JSONDecodeError as exc: raise HydrodynamicScheduleV27Error(f"invalid operator JSONL line {line_no}") from exc
        if not isinstance(rec, dict) or rec.get("schema") != "PHASENAV_OPERATOR_VECTOR_V1":
            raise HydrodynamicScheduleV27Error("unexpected live operator schema")
        name = str(rec.get("operator_name", rec.get("operator_id", rec.get("card_id", "")))).strip().upper()
        vec = rec.get("orbit_vector", rec.get("vector_36d"))
        if not name or not isinstance(vec, list) or len(vec) != 36:
            raise HydrodynamicScheduleV27Error("invalid live operator vector")
        vals = tuple(float(x) for x in vec)
        if not all(math.isfinite(x) for x in vals) or name in out:
            raise HydrodynamicScheduleV27Error("non-finite or duplicate live operator")
        out[name] = vals
    if not out:
        raise HydrodynamicScheduleV27Error("empty live operator registry")
    return out, _sha256_bytes(raw)


@dataclass(frozen=True)
class HydrodynamicKakuScheduleEntry:
    step_index: int
    operator_id: str
    operator_vector_sha256: str
    gate: HydrodynamicPhaseGate

    def __post_init__(self) -> None:
        if isinstance(self.step_index, bool) or not isinstance(self.step_index, int) or self.step_index < 1:
            raise HydrodynamicScheduleV27Error("step_index must be positive integer")
        if not isinstance(self.operator_id, str) or not self.operator_id.strip():
            raise HydrodynamicScheduleV27Error("operator_id required")
        if not isinstance(self.operator_vector_sha256, str) or len(self.operator_vector_sha256) != 64:
            raise HydrodynamicScheduleV27Error("operator_vector_sha256 required")
        if not isinstance(self.gate, HydrodynamicPhaseGate):
            raise HydrodynamicScheduleV27Error("HydrodynamicPhaseGate required")

    @property
    def payload(self) -> dict[str, object]:
        return {"schema":SCHEDULE_ENTRY_SCHEMA,"step_index":self.step_index,"operator_id":self.operator_id,"operator_vector_sha256":self.operator_vector_sha256,"gate_id":self.gate.gate_id}


@dataclass(frozen=True)
class HydrodynamicKakuSchedule:
    execution_receipt_sha256: str
    program_content_id: str
    entries: tuple[HydrodynamicKakuScheduleEntry, ...]

    @property
    def payload(self) -> dict[str, object]:
        return {"schema":SCHEDULE_SCHEMA,"contract_id":SCHEDULE_CONTRACT_ID,"execution_receipt_sha256":self.execution_receipt_sha256,"program_content_id":self.program_content_id,"entries":[e.payload for e in self.entries],"semantic_identity_modified":False,"external_effects":False}

    @property
    def schedule_id(self) -> str:
        return _typed_id("pncs:hydro-schedule", self.payload)


def uniform_schedule_for_receipt(receipt: Mapping[str, object], gate: HydrodynamicPhaseGate) -> HydrodynamicKakuSchedule:
    receipt_sha = _validate_v20_receipt(receipt)
    program = receipt.get("program")
    if not isinstance(program, Mapping) or not isinstance(program.get("content_id"), str):
        raise HydrodynamicScheduleV27Error("v0.20 program content ID missing")
    entries=[]
    for step in receipt["steps"]:  # type: ignore[index]
        assert isinstance(step, Mapping)
        entries.append(HydrodynamicKakuScheduleEntry(int(step["index"]),str(step["operator_id"]),str(step["operator_vector_sha256"]),gate))
    return HydrodynamicKakuSchedule(receipt_sha,str(program["content_id"]),tuple(entries))


@dataclass(frozen=True)
class HydrodynamicExecutionTrace:
    schedule: HydrodynamicKakuSchedule
    initial_state_id: str
    final_state: PhaseFlowState36
    operator_trace_ids: tuple[str, ...]
    operator_names: tuple[str, ...]
    coordinate_time: float
    phase_proper_time_advanced: float
    live_operator_registry_sha256: str

    @property
    def program_content_id(self) -> str:
        return self.schedule.program_content_id

    @property
    def payload(self) -> dict[str, object]:
        return {"schema":EXECUTION_TRACE_SCHEMA,"contract_id":SCHEDULE_CONTRACT_ID,"schedule_id":self.schedule.schedule_id,"execution_receipt_sha256":self.schedule.execution_receipt_sha256,"program_content_id":self.schedule.program_content_id,"initial_state_id":self.initial_state_id,"final_state_id":self.final_state.state_id,"operator_trace_ids":list(self.operator_trace_ids),"operator_names":list(self.operator_names),"coordinate_time":self.coordinate_time,"phase_proper_time_advanced":self.phase_proper_time_advanced,"live_operator_registry_sha256":self.live_operator_registry_sha256,"semantic_identity_modified":False,"external_effects":False,"laboratory_time_modified":False}

    @property
    def trace_id(self) -> str:
        return _typed_id("pncs:hydro-execution-trace", self.payload)


def replay_v20_hydrodynamic_schedule(
    receipt: Mapping[str, object],
    initial_state: PhaseFlowState36,
    schedule: HydrodynamicKakuSchedule,
    *,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
) -> HydrodynamicExecutionTrace:
    receipt_sha = _validate_v20_receipt(receipt)
    if schedule.execution_receipt_sha256 != receipt_sha:
        raise HydrodynamicScheduleV27Error("schedule does not bind this v0.20 receipt")
    steps = receipt.get("steps"); assert isinstance(steps, list)
    if len(schedule.entries) != len(steps):
        raise HydrodynamicScheduleV27Error("schedule length differs from v0.20 execution")
    operators, registry_sha = load_live_operator_vectors(surface_root)
    current=initial_state; trace_ids=[]; names=[]; coordinate=0.0
    for step, entry in zip(steps, schedule.entries):
        assert isinstance(step, Mapping)
        if int(step["index"]) != entry.step_index or str(step["operator_id"]) != entry.operator_id or str(step["operator_vector_sha256"]) != entry.operator_vector_sha256:
            raise HydrodynamicScheduleV27Error("schedule entry differs from exact v0.20 occurrence")
        vec = operators.get(entry.operator_id.upper())
        if vec is None:
            raise HydrodynamicScheduleV27Error(f"live operator missing: {entry.operator_id}")
        live_vector_sha = hashlib.sha256(struct.pack("<36d", *vec)).hexdigest()
        if live_vector_sha != entry.operator_vector_sha256:
            raise HydrodynamicScheduleV27Error("live operator vector bytes differ from v0.20 witness")
        sub = run_hydrodynamic_gate(current, entry.gate, vec)
        trace_ids.append(sub.trace_id); names.append(entry.operator_id); coordinate += sub.coordinate_time; current=sub.final_state
    return HydrodynamicExecutionTrace(schedule,initial_state.state_id,current,tuple(trace_ids),tuple(names),coordinate,current.phase_proper_time-initial_state.phase_proper_time,registry_sha)