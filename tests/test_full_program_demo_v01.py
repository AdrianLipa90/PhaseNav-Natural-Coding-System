from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples/pncs_full_program_demo_v01.py"


def _load_demo_module():
    spec = importlib.util.spec_from_file_location("pncs_full_program_demo_v01", DEMO)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_full_program_demo_runs_to_terminal_return() -> None:
    demo = _load_demo_module()
    out = demo.run_demo(persist_live=False)
    assert out["schema"] == "PNCS_FULL_PROGRAM_DEMO_V0_1"
    assert out["status"] == "PASS_FULL_PROGRAM_DEMO_V0_1"
    assert out["resolution_module"] == "phasenav_natural_code.composition_v23"
    assert out["program_unit_module"] == "phasenav_natural_code.program_unit_v24"
    assert out["instruction_kinds"] == [
        "CONTROL_DISPATCH",
        "CONTINUATION_ROUTE",
        "CONTINUATION_ROUTE",
        "RETURN",
    ]
    assert out["branch_truth_state"] == "FALSE"
    assert out["final_control_location"] == "runtime.memory.relief"
    assert out["return_selector"] == "result.control_location"
    assert out["return_value"] == "runtime.memory.relief"
    assert out["halted"] is True
    assert out["continuation_execution_opened"] is True
    assert out["return_execution_opened"] is True
    assert out["loops_opened"] is False
    assert out["function_calls_opened"] is False
    assert out["external_effects"] is False
    assert out["static_runtime_fallback"] is False
    assert len(out["trace"]) == 4


def test_demo_evidence_boundary_is_explicit() -> None:
    demo = _load_demo_module()
    out = demo.run_demo(persist_live=False)
    boundary = out["evidence_boundary"]
    assert boundary == {
        "real_v023_resolver": True,
        "real_v024_program_unit": True,
        "real_full_program_executor": True,
        "real_v025_dispatch_receipt_model": True,
        "live_v020_kernel_execution": False,
        "live_v025_resident_dispatch": False,
    }
