from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from phasenav_natural_code.adversarial_v28 import (
    AdversarialV28Error,
    mutate_and_resign,
    validate_coupled_receipt_structure,
)
from phasenav_natural_code.execution_v20_model import BoundInternalProgram
from phasenav_natural_code.execution_orch_authority_v27 import ProgramAuthority, ResidentCoupledAuthority
from phasenav_natural_code.hydro_time_v27 import HydrodynamicPhaseGate
from phasenav_natural_code.orch_hydro_v27 import OrchHydroControlProfile
from phasenav_natural_code.orch_orbital_v27 import (
    AttractorReport,
    ReductionKernel,
    SubjectiveTimeKernel,
    TotalPotential,
)
from phasenav_natural_code.paired_snapshot_v28 import run_same_snapshot_conformance

ROOT = Path("/dev/shm/ciel_noema")
REPO_ROOT = Path(__file__).parents[2]
DEFINITION_REGISTRY = REPO_ROOT / "registry/definitions/PNCS_DEFINITION_REGISTRY_V0_11.jsonl"
ZERO = (0.0,) * 36
ATTRACTORS = (
    AttractorReport("AttractorEC", 0.75, ZERO, 0.5, "LIVE_V028_EC"),
    AttractorReport("AttractorZS", 0.80, ZERO, 0.5, "LIVE_V028_ZS"),
    AttractorReport("AttractorLLMTemp", 0.0, ZERO, 0.0, "DISABLED"),
)
PROFILE = OrchHydroControlProfile(
    SubjectiveTimeKernel(),
    1.0,
    ATTRACTORS,
    TotalPotential(0, 0, 0, 0, 0, 0),
    ReductionKernel(1, 1, 1, 1, 10.0),
    1.0,
    0.0,
)
GATE = HydrodynamicPhaseGate(0.5, 0.2, steps=1, coordinate_dt=0.01)


def _tupleize(value):
    if isinstance(value, list):
        return tuple(_tupleize(item) for item in value)
    if isinstance(value, dict):
        return {key: _tupleize(item) for key, item in value.items()}
    return value


def _definition_graph(content_id: str) -> tuple[object, ...]:
    matches = []
    for line in DEFINITION_REGISTRY.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("content_id") == content_id:
            graph = record.get("content", {}).get("canonical_graph")
            if graph is not None:
                matches.append(_tupleize(graph))
    unique = []
    for graph in matches:
        if graph not in unique:
            unique.append(graph)
    if len(unique) != 1 or not isinstance(unique[0], tuple):
        raise AssertionError("exactly one canonical Definition graph required")
    return unique[0]


def _active_chain():
    if (ROOT / "ciel_binding_status").read_text("utf-8").strip() != "ACTIVE":
        raise AssertionError("live NOEMA binding is not ACTIVE")
    active_paths = sorted((ROOT / "pncs/v0.25/runtime/active").glob("*.json"))
    if len(active_paths) != 1:
        raise AssertionError("exactly one active resident pointer required")
    active = json.loads(active_paths[0].read_text("utf-8"))

    dispatches = []
    for path in sorted((ROOT / "pncs/v0.25/runtime/receipts/dispatch").glob("*.json")):
        record = json.loads(path.read_text("utf-8"))
        if (
            record.get("handle_id") == active.get("handle_id")
            and record.get("generation_id") == active.get("generation_id")
            and record.get("program_id") == active.get("program_id")
        ):
            dispatches.append(record)
    if len(dispatches) != 1:
        raise AssertionError("exactly one dispatch for active resident pointer required")
    dispatch = dispatches[0]

    source_sha = str(dispatch["execution_receipt_sha256"])
    source = json.loads((ROOT / "pncs/v0.20/receipts" / f"{source_sha}.json").read_text("utf-8"))
    lineage_id = str(dispatch["lineage_id"])
    lineage_sha = lineage_id.rsplit(":", 1)[-1]
    lineage = json.loads((ROOT / "pncs/v0.22/lineage" / f"{lineage_sha}.json").read_text("utf-8"))
    graph = _definition_graph(str(source["program"]["content_id"]))
    authority = ProgramAuthority.from_v20_receipt(source, graph)
    resident = ResidentCoupledAuthority.from_records(authority, dispatch, lineage)
    resident.validate_active_pointer(ROOT)

    program = BoundInternalProgram(
        content_id=authority.content_id,
        canonical_graph=authority.canonical_graph,
        leaf_path=authority.leaf_path,
        realization_id=authority.realization_id,
        realization_binding_id=authority.realization_binding_id,
        mass_binding_id=authority.mass_binding_id,
        phase36_sha256=authority.phase36_sha256,
        semantic_mass=authority.semantic_mass,
    )
    values = {str(key): value for key, value in source["input_values"]}
    return source, dispatch, lineage, authority, resident, program, values


def _paired():
    source_template, dispatch, _, _, _, program, values = _active_chain()
    paired = run_same_snapshot_conformance(
        program,
        values,
        str(dispatch["target"]),
        PROFILE,
        {"*": GATE},
    )
    return source_template, dispatch, paired


def test_live_active_v025_resident_authority_is_exact_and_active():
    source, dispatch, lineage, authority, resident, _, _ = _active_chain()
    assert resident.program_authority.authority_id == authority.authority_id
    assert resident.dispatch_id == dispatch["dispatch_id"]
    assert resident.lineage_id == lineage["lineage_id"]
    assert dispatch["execution_receipt_sha256"] == source["receipt_sha256"]


def test_live_same_snapshot_v020_and_coupled_semantic_projection_are_equal():
    _, _, paired = _paired()
    assert paired.semantic_projection_equal is True
    assert paired.source_receipt["live_surface"]["phi_sha256"] == paired.live_phi_sha256
    assert paired.coupled_receipt["live_surface"]["phi_sha256"] == paired.live_phi_sha256
    assert validate_coupled_receipt_structure(
        paired.coupled_receipt,
        source_v20_receipt=paired.source_receipt,
    ) == paired.coupled_receipt["receipt_sha256"]


def test_live_same_snapshot_vector_substitution_rejected_after_resign():
    _, _, paired = _paired()
    attacked = mutate_and_resign(
        paired.coupled_receipt,
        lambda r: r["orch_occurrences"][0].__setitem__("operator_vector_sha256", "0" * 64),
    )
    with pytest.raises(AdversarialV28Error):
        validate_coupled_receipt_structure(attacked, source_v20_receipt=paired.source_receipt)


def test_live_same_snapshot_negative_local_proper_time_rejected_after_resign():
    _, _, paired = _paired()
    attacked = mutate_and_resign(
        paired.coupled_receipt,
        lambda r: r["orch_occurrences"][0].__setitem__("proper_time_advanced", -0.01),
    )
    with pytest.raises(AdversarialV28Error):
        validate_coupled_receipt_structure(attacked, source_v20_receipt=paired.source_receipt)


def test_live_same_snapshot_external_effect_substitution_rejected_after_resign():
    _, _, paired = _paired()
    attacked = mutate_and_resign(
        paired.coupled_receipt,
        lambda r: r.__setitem__("external_effects", True),
    )
    with pytest.raises(AdversarialV28Error):
        validate_coupled_receipt_structure(attacked, source_v20_receipt=paired.source_receipt)


def test_live_same_snapshot_source_tamper_rejected():
    _, _, paired = _paired()
    attacked_source = copy.deepcopy(paired.source_receipt)
    attacked_source["result"]["control_location"] = "runtime.tampered"
    with pytest.raises(AdversarialV28Error, match="source v0.20 receipt digest"):
        validate_coupled_receipt_structure(paired.coupled_receipt, source_v20_receipt=attacked_source)


def test_paired_conformance_never_claims_resident_execution_authority():
    _, _, paired = _paired()
    assert paired.coupled_receipt["paired_snapshot_conformance_only"] is True
    assert paired.coupled_receipt["operational_resident_authority_opened"] is False
    assert paired.coupled_receipt["external_effects"] is False
    assert paired.coupled_receipt["routing_feedback_opened"] is False
