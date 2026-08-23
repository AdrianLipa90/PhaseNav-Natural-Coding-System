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
SOURCE_V20_SHA = "84d40f600a8aa9e59ebc6dc42c856bcffec9265d04f791e7f5c49cdba2d583ad"
RECEIPT_PATH = ROOT / "pncs/v0.20/receipts" / f"{SOURCE_V20_SHA}.json"
THETA = tuple((i + 1) * 0.1 for i in range(36))
STATE = PhaseFlowState36(THETA)
ZERO = (0.0,) * 36
ATTRACTORS = (
    AttractorReport("AttractorEC", 0.75, ZERO, 0.5, "LIVE_EC"),
    AttractorReport("AttractorZS", 0.80, ZERO, 0.5, "LIVE_ZS"),
    AttractorReport("AttractorLLMTemp", 0.0, ZERO, 0.0, "DISABLED"),
)
POTENTIAL = TotalPotential(0, 0, 0, 0, 0, 0)
TIME_KERNEL = SubjectiveTimeKernel(
    beta_radius=-0.1,
    beta_coherence=0.4,
    beta_defect=-0.4,
    beta_mass=-0.2,
    beta_attractor=0.2,
)
PROFILE = OrchHydroControlProfile(
    TIME_KERNEL,
    1.0,
    ATTRACTORS,
    POTENTIAL,
    ReductionKernel(1, 1, 1, 1, 10.0),
    1.0,
    0.0,
)
GATE = HydrodynamicPhaseGate(0.5, 0.2, steps=1, coordinate_dt=0.01)


def _receipt() -> dict[str, object]:
    assert (ROOT / "ciel_binding_status").read_text("utf-8").strip() == "ACTIVE"
    return json.loads(RECEIPT_PATH.read_text("utf-8"))


def _trace():
    receipt = _receipt()
    schedule = uniform_schedule_for_receipt(receipt, GATE)
    return receipt, replay_v20_orchorbital_hydrodynamic_schedule(receipt, STATE, schedule, PROFILE)


def test_live_exact_schedule_has_nine_occurrences():
    _, trace = _trace()
    assert len(trace.occurrence_ids) == 9


def test_live_exact_schedule_operator_order_preserved():
    receipt, trace = _trace()
    assert trace.operator_names == tuple(step["operator_id"] for step in receipt["steps"])


def test_live_exact_schedule_receipt_and_program_bound():
    receipt, trace = _trace()
    assert trace.execution_receipt_sha256 == receipt["receipt_sha256"] == SOURCE_V20_SHA
    assert trace.program_content_id == receipt["program"]["content_id"]
    assert trace.semantic_mass == receipt["program"]["semantic_mass"]


def test_live_exact_schedule_keeps_closed_boundaries():
    _, trace = _trace()
    assert trace.payload["semantic_identity_modified"] is False
    assert trace.payload["external_effects"] is False
    assert trace.payload["laboratory_time_modified"] is False
    assert trace.stable_memory_update_count == 0


def test_live_operator_vector_bytes_match_exact_v020_receipt():
    receipt = _receipt()
    operators, _ = load_live_operator_vectors()
    for step in receipt["steps"]:
        raw = struct.pack("<36d", *operators[step["operator_id"]])
        assert hashlib.sha256(raw).hexdigest() == step["operator_vector_sha256"]


def test_live_tampered_v020_receipt_rejected():
    receipt = _receipt()
    attacked = copy.deepcopy(receipt)
    attacked["result"]["control_location"] = "runtime.tampered"
    schedule = uniform_schedule_for_receipt(receipt, GATE)
    with pytest.raises(Exception):
        replay_v20_orchorbital_hydrodynamic_schedule(attacked, STATE, schedule, PROFILE)
