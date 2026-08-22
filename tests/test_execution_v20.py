from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import time
from types import SimpleNamespace

import pytest

from phasenav_natural_code.execution_v20 import (
    BoundInternalProgram,
    EXECUTABLE_INTERNAL_OPERATORS,
    LiveSurfaceV20Error,
    NativeExecutionV20Error,
    bind_internal_program,
    definition_content_id,
    execute_admitted_internal,
    execute_control_resolution,
    expected_leaf_path,
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_live(root: Path, *, active: bool = True, omit_operator: str | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "session").mkdir()
    (root / "phasenav").mkdir()
    (root / "ciel_binding_status").write_text("ACTIVE\n" if active else "BLOCKED\n", encoding="utf-8")
    (root / "session/startpoint.json").write_text(json.dumps({"status": "VERIFIED"}), encoding="utf-8")
    (root / "session/system_message.txt").write_text("status: VERIFIED\n", encoding="utf-8")

    phi = struct.pack("<36d", *[0.01 * (i + 1) for i in range(36)])
    aux = struct.pack("<36d", *[0.02 * (i + 1) for i in range(36)])
    feedback = struct.pack("<36d", *[0.03 * (i + 1) for i in range(36)])
    (root / "phi").write_bytes(phi)
    (root / "aux_phi").write_bytes(aux)
    (root / "aux_feedback_phi").write_bytes(feedback)
    now = time.time_ns()
    (root / "aux_stream_status.json").write_text(
        json.dumps({
            "schema": "noema.aux-stream-status/v2",
            "status": "ACTIVE",
            "pid": os.getpid(),
            "heartbeat_ns": now,
            "state_sha256": _sha(aux),
        }), encoding="utf-8"
    )
    (root / "tether_runtime_status.json").write_text(
        json.dumps({
            "schema": "noema.tether-runtime-status/v1",
            "status": "ACTIVE",
            "pid": os.getpid(),
            "heartbeat_ns": now,
            "phi_sha256": _sha(phi),
            "aux_phi_sha256": _sha(aux),
            "aux_feedback_phi_sha256": _sha(feedback),
            "receipt_sha256": "a" * 64,
        }), encoding="utf-8"
    )
    rows = []
    for j, op in enumerate(sorted(EXECUTABLE_INTERNAL_OPERATORS), start=1):
        if op == omit_operator:
            continue
        rows.append(json.dumps({
            "schema": "PHASENAV_OPERATOR_VECTOR_V1",
            "card_id": op,
            "operator_name": op,
            "orbit_vector": [round((j * 0.1 + i * 0.01) % 6.0, 10) for i in range(36)],
            "vector_dim": 36,
        }, sort_keys=True))
    (root / "phasenav/CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )


def _program(graph: tuple[object, ...]) -> BoundInternalProgram:
    leaves = expected_leaf_path(graph)
    return BoundInternalProgram(
        content_id=definition_content_id(graph, leaves),
        canonical_graph=graph,
        leaf_path=leaves,
        realization_id="pncs:realization36:sha256:" + "1" * 64,
        realization_binding_id="pncs:binding36:sha256:" + "2" * 64,
        mass_binding_id="pncs:mass-binding:sha256:" + "3" * 64,
        phase36_sha256="4" * 64,
        semantic_mass=0.123456789,
    )


def test_true_route_executes_existing_pnv_kaku_only(tmp_path: Path) -> None:
    _write_live(tmp_path)
    graph = ("branch", ("comparison", "gravity", "lt", 0.5), "physics.gravity.low", None)
    result = execute_admitted_internal(
        _program(graph), {"gravity": 0.25}, "physics.gravity.low",
        surface_root=tmp_path, require_socket=False,
    )
    assert result.target == "physics.gravity.low"
    assert result.branch_truth_state == "TRUE"
    assert [s["operator_id"] for s in result.receipt["steps"]] == [
        "DIFFERENCE", "CONDITION", "ORDER", "TRANSFORM", "COMPOSITION"
    ]
    assert result.receipt["external_effects"] is False
    assert result.receipt["semantic_mass_is_authorization"] is False
    assert Path(result.receipt_path).is_file()
    assert (tmp_path / "pncs/v0.20/state/current.json").is_file()


def test_false_else_executes_negated_false_arm(tmp_path: Path) -> None:
    _write_live(tmp_path)
    graph = (
        "branch",
        ("comparison", "risk", "gt", 0.8),
        "safety.pause",
        "runtime.continue",
    )
    result = execute_admitted_internal(
        _program(graph), {"risk": 0.2}, "runtime.continue",
        surface_root=tmp_path, require_socket=False,
    )
    assert result.branch_truth_state == "FALSE"
    assert result.target == "runtime.continue"
    assert [s["operator_id"] for s in result.receipt["steps"]] == [
        "DIFFERENCE", "CONDITION", "NEGATION", "ORDER", "TRANSFORM", "COMPOSITION"
    ]


def test_nested_boolean_reduces_by_existing_composition_and_negation(tmp_path: Path) -> None:
    _write_live(tmp_path)
    predicate = (
        "and",
        ("comparison", "risk", "lt", 0.8),
        ("not", ("comparison", "gravity", "gt", 0.5)),
    )
    graph = ("branch", predicate, "runtime.continue", "safety.pause")
    result = execute_admitted_internal(
        _program(graph), {"risk": 0.4, "gravity": 0.2}, "runtime.continue",
        surface_root=tmp_path, require_socket=False,
    )
    ops = [s["operator_id"] for s in result.receipt["steps"]]
    assert ops[:6] == ["DIFFERENCE", "CONDITION", "DIFFERENCE", "CONDITION", "NEGATION", "COMPOSITION"]
    assert ops[-3:] == ["ORDER", "TRANSFORM", "COMPOSITION"]


def test_admission_mismatch_fails_closed(tmp_path: Path) -> None:
    _write_live(tmp_path)
    graph = ("branch", ("comparison", "risk", "gt", 0.8), "safety.pause", "runtime.continue")
    with pytest.raises(NativeExecutionV20Error, match="admission/graph mismatch"):
        execute_admitted_internal(
            _program(graph), {"risk": 0.9}, "runtime.continue",
            surface_root=tmp_path, require_socket=False,
        )


def test_false_without_else_has_no_admitted_execution(tmp_path: Path) -> None:
    _write_live(tmp_path)
    graph = ("branch", ("comparison", "gravity", "lt", 0.5), "physics.gravity.low", None)
    with pytest.raises(NativeExecutionV20Error, match="no admitted internal route"):
        execute_admitted_internal(
            _program(graph), {"gravity": 0.7}, "physics.gravity.low",
            surface_root=tmp_path, require_socket=False,
        )


def test_missing_runtime_value_fails_closed(tmp_path: Path) -> None:
    _write_live(tmp_path)
    graph = ("branch", ("comparison", "risk", "gt", 0.8), "safety.pause", "runtime.continue")
    with pytest.raises(NativeExecutionV20Error, match="missing runtime value"):
        execute_admitted_internal(
            _program(graph), {}, "safety.pause", surface_root=tmp_path, require_socket=False,
        )


def test_inactive_tether_blocks_execution(tmp_path: Path) -> None:
    _write_live(tmp_path, active=False)
    graph = ("branch", ("comparison", "risk", "gt", 0.8), "safety.pause", "runtime.continue")
    with pytest.raises(LiveSurfaceV20Error, match="binding is not ACTIVE"):
        execute_admitted_internal(
            _program(graph), {"risk": 0.9}, "safety.pause",
            surface_root=tmp_path, require_socket=False,
        )


def test_missing_live_operator_blocks_execution(tmp_path: Path) -> None:
    _write_live(tmp_path, omit_operator="TRANSFORM")
    graph = ("branch", ("comparison", "risk", "gt", 0.8), "safety.pause", "runtime.continue")
    with pytest.raises(LiveSurfaceV20Error, match="missing v0.20 internal operators"):
        execute_admitted_internal(
            _program(graph), {"risk": 0.9}, "safety.pause",
            surface_root=tmp_path, require_socket=False,
        )


def test_receipt_is_deterministic_for_same_program_inputs_and_surface_snapshot(tmp_path: Path) -> None:
    _write_live(tmp_path)
    graph = ("branch", ("comparison", "risk", "gt", 0.8), "safety.pause", "runtime.continue")
    program = _program(graph)
    a = execute_admitted_internal(
        program, {"risk": 0.9}, "safety.pause", surface_root=tmp_path, require_socket=False,
    )
    b = execute_admitted_internal(
        program, {"risk": 0.9}, "safety.pause", surface_root=tmp_path, require_socket=False,
    )
    assert a.receipt["receipt_sha256"] == b.receipt["receipt_sha256"]
    assert a.final_state.state_id == b.final_state.state_id
    assert a.receipt == b.receipt


def test_content_identity_is_recomputed_from_exact_graph_and_leaf_path() -> None:
    graph = ("branch", ("comparison", "risk", "gt", 0.8), "safety.pause", "runtime.continue")
    good = _program(graph)
    with pytest.raises(NativeExecutionV20Error, match="canonical graph/content ID mismatch"):
        BoundInternalProgram(
            content_id="pncs:def:sha256:" + "f" * 64,
            canonical_graph=good.canonical_graph,
            leaf_path=good.leaf_path,
            realization_id=good.realization_id,
            realization_binding_id=good.realization_binding_id,
            mass_binding_id=good.mass_binding_id,
            phase36_sha256=good.phase36_sha256,
            semantic_mass=good.semantic_mass,
        )


def test_effect_request_is_not_executable_in_v020() -> None:
    assert "ACTION_REQUEST" not in EXECUTABLE_INTERNAL_OPERATORS
    assert "SOURCE" not in EXECUTABLE_INTERNAL_OPERATORS
    assert "RETURN" not in EXECUTABLE_INTERNAL_OPERATORS


def test_unresolved_control_admission_cannot_enter_executor() -> None:
    resolution = SimpleNamespace(content=object())
    admission = SimpleNamespace(truth_state="UNRESOLVED", admitted_target=None, epistemic_operator="CHYBA")
    with pytest.raises(NativeExecutionV20Error, match="resolved admitted internal route"):
        execute_control_resolution(resolution, admission, object(), object(), {})


class _Verified:
    def verify(self) -> None:
        return None


def _verified_chain(graph: tuple[object, ...]):
    leaves = expected_leaf_path(graph)
    cid = definition_content_id(graph, leaves)
    content = _Verified()
    content.kind = "INTERNAL_BRANCH"
    content.content_id = cid
    content.canonical_graph = graph
    content.leaf_path = leaves

    phase = SimpleNamespace(phase_sha256="4" * 64)
    realization = _Verified()
    realization.content_id = cid
    realization.phase = phase
    realization.realization_id = "pncs:realization36:sha256:" + "1" * 64
    realization.binding_id = "pncs:binding36:sha256:" + "2" * 64

    mass = _Verified()
    mass.realization = realization
    mass.mass_binding_id = "pncs:mass-binding:sha256:" + "3" * 64
    mass.semantic_mass = 0.123456789
    return content, realization, mass


def test_v018_v019_lineage_is_bound_before_execution() -> None:
    graph = ("branch", ("comparison", "risk", "gt", 0.8), "safety.pause", "runtime.continue")
    content, realization, mass = _verified_chain(graph)
    program = bind_internal_program(content, realization, mass)
    assert program.content_id == content.content_id
    assert program.realization_binding_id == realization.binding_id
    assert program.mass_binding_id == mass.mass_binding_id
    assert program.semantic_mass == mass.semantic_mass


def test_control_resolution_bridge_executes_only_resolved_admission(tmp_path: Path) -> None:
    _write_live(tmp_path)
    graph = ("branch", ("comparison", "risk", "gt", 0.8), "safety.pause", "runtime.continue")
    content, realization, mass = _verified_chain(graph)
    resolution = SimpleNamespace(content=content)
    admission = SimpleNamespace(truth_state="TRUE", admitted_target="safety.pause", epistemic_operator=None)
    result = execute_control_resolution(
        resolution, admission, realization, mass, {"risk": 0.9},
        surface_root=tmp_path, require_socket=False,
    )
    assert result.target == "safety.pause"
