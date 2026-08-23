from __future__ import annotations

import copy
import hashlib
import json
import struct
from pathlib import Path

import pytest

from phasenav_natural_code.hydro_schedule_v27 import load_live_operator_vectors, uniform_schedule_for_receipt
from phasenav_natural_code.hydro_time_v27 import HydrodynamicPhaseGate, PhaseFlowState36
from phasenav_natural_code.orch_hydro_v27 import OrchHydroControlProfile, replay_v20_orchorbital_hydrodynamic_schedule
from phasenav_natural_code.orch_orbital_v27 import AttractorReport, ReductionKernel, SubjectiveTimeKernel, TotalPotential

ROOT = Path("/dev/shm/ciel_noema")
THETA = tuple((i + 1) * 0.1 for i in range(36))
STATE = PhaseFlowState36(THETA)
ZERO = (0.0,) * 36
ATTRACTORS = (
    AttractorReport("AttractorEC", 0.75, ZERO, 0.5, "LIVE_EC"),
    AttractorReport("AttractorZS", 0.80, ZERO, 0.5, "LIVE_ZS"),
    AttractorReport("AttractorLLMTemp", 0.0, ZERO, 0.0, "DISABLED"),
)
PROFILE = OrchHydroControlProfile(
    SubjectiveTimeKernel(
        beta_radius=-0.1,
        beta_coherence=0.4,
        beta_defect=-0.4,
        beta_mass=-0.2,
        beta_attractor=0.2,
    ),
    1.0,
    ATTRACTORS,
    TotalPotential(0, 0, 0, 0, 0, 0),
    ReductionKernel(1, 1, 1, 1, 10.0),
    1.0,
    0.0,
)
GATE = HydrodynamicPhaseGate(0.5, 0.2, steps=1, coordinate_dt=0.01)


def _active_source_receipt() -> dict[str, object]:
    assert (ROOT / "ciel_binding_status").read_text("utf-8").strip() == "ACTIVE"
    active_paths = sorted((ROOT / "pncs/v0.25/runtime/active").glob("*.json"))
    assert len(active_paths) == 1
    active = json.loads(active_paths[0].read_text("utf-8"))
    matches = []
    for path in sorted((ROOT / "pncs/v0.25/runtime/receipts/dispatch").glob("*.json")):
        dispatch = json.loads(path.read_text("utf-8"))
        if (
            dispatch.get("handle_id") == active.get("handle_id")
            and dispatch.get("generation_id") == active.get("generation_id")
            and dispatch.get("program_id") == active.get("program_id")
        ):
            matches.append(dispatch)
    assert len(matches) == 1
    source_sha = str(matches[0]["execution_receipt_sha256"])
    receipt = json.loads((ROOT / "pncs/v0.20/receipts" / f"{source_sha}.json").read_text("utf-8"))
    assert receipt["receipt_sha256"] == source_sha
    return receipt


def _trace():
    receipt = _active_source_receipt()
    schedule = uniform_schedule_for_receipt(receipt, GATE)
    return receipt, replay_v20_orchorbital_hydrodynamic_schedule(receipt, STATE, schedule, PROFILE)


def test_live_exact_schedule_occurrence_count_matches_semantic_steps():
    receipt, trace = _trace()
    assert len(trace.occurrence_ids) == len(receipt["steps"])


def test_live_exact_schedule_operator_order_preserved():
    receipt, trace = _trace()
    assert trace.operator_names == tuple(step["operator_id"] for step in receipt["steps"])


def test_live_exact_schedule_receipt_and_program_bound():
    receipt, trace = _trace()
    assert trace.execution_receipt_sha256 == receipt["receipt_sha256"]
    assert trace.program_content_id == receipt["program"]["content_id"]
    assert trace.semantic_mass == receipt["program"]["semantic_mass"]


def test_live_exact_schedule_keeps_closed_boundaries():
    _, trace = _trace()
    assert trace.payload["semantic_identity_modified"] is False
    assert trace.payload["external_effects"] is False
    assert trace.payload["laboratory_time_modified"] is False
    assert trace.stable_memory_update_count == 0


def test_live_operator_vector_bytes_match_active_v020_receipt():
    receipt = _active_source_receipt()
    operators, _ = load_live_operator_vectors()
    for step in receipt["steps"]:
        raw = struct.pack("<36d", *operators[step["operator_id"]])
        assert hashlib.sha256(raw).hexdigest() == step["operator_vector_sha256"]


def test_live_tampered_active_v020_receipt_rejected():
    receipt = _active_source_receipt()
    attacked = copy.deepcopy(receipt)
    attacked["result"]["control_location"] = "runtime.tampered"
    schedule = uniform_schedule_for_receipt(receipt, GATE)
    with pytest.raises(Exception):
        replay_v20_orchorbital_hydrodynamic_schedule(attacked, STATE, schedule, PROFILE)
