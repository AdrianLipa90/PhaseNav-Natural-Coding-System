from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

from phasenav_natural_code.composition_v23 import resolve_natural_program
from phasenav_natural_code.full_program_executor_v01 import (
    FullProgramExecutionReceipt,
    compile_full_program_plan,
    execute_prepared_program,
)
from phasenav_natural_code.program_unit_v24 import NativeProgramUnit
from phasenav_natural_code.runtime_v25_resident_model import ResidentDispatchReceipt

DEMO_SCHEMA = "PNCS_FULL_PROGRAM_DEMO_V0_1"
DEMO_STATUS = "PASS_FULL_PROGRAM_DEMO_V0_1"
CANONICAL_LIVE_ROOT = Path("/dev/shm/ciel_noema")

PROGRAM = (
    "IF (memory pressure ABOVE 90% OR risk ABOVE 80%) "
    "THEN GO safety pause ELSE GO runtime continue "
    "AND THEN GO cooling emergency "
    "AND THEN GO runtime memory relief "
    "RETURN control location"
)


def _tid(kind: str, label: str) -> str:
    return f"pncs:{kind}:sha256:{hashlib.sha256(label.encode('utf-8')).hexdigest()}"


def _demo_dispatch(program_id: str) -> ResidentDispatchReceipt:
    """Create a deterministic v0.25-compatible control-dispatch witness.

    This object exercises the exact v0.25 dispatch receipt contract consumed by
    the full-program executor. It is deliberately not presented as a live
    v0.20 kernel execution receipt.
    """
    return ResidentDispatchReceipt(
        handle_id=_tid("resident", "PNCS_FULL_PROGRAM_DEMO_V0_1::resident"),
        program_id=program_id,
        generation_id=_tid("runtime-generation", "PNCS_FULL_PROGRAM_DEMO_V0_1::generation"),
        resident_admission_id=_tid("resident-admission", "PNCS_FULL_PROGRAM_DEMO_V0_1::admission"),
        execution_receipt_sha256=hashlib.sha256(
            b"PNCS_FULL_PROGRAM_DEMO_V0_1::v0.20-compatible-control-witness"
        ).hexdigest(),
        result_id=_tid("result", "PNCS_FULL_PROGRAM_DEMO_V0_1::result"),
        lineage_id=_tid("lineage", "PNCS_FULL_PROGRAM_DEMO_V0_1::lineage"),
        target="runtime.continue",
        branch_truth_state="FALSE",
    )


def _receipt_document(
    receipt: FullProgramExecutionReceipt,
    *,
    source_program: str,
    resolution_module: str,
    program_unit_module: str,
) -> dict[str, object]:
    return {
        "schema": DEMO_SCHEMA,
        "status": DEMO_STATUS,
        "source_program": source_program,
        "program_id": receipt.plan.program_id,
        "composition_id": receipt.plan.composition_id,
        "plan_id": receipt.plan.plan_id,
        "execution_id": receipt.execution_id,
        "dispatch_mode": "DETERMINISTIC_V25_COMPATIBLE_DISPATCH_WITNESS",
        "resolution_module": resolution_module,
        "program_unit_module": program_unit_module,
        "instruction_kinds": [step.kind for step in receipt.trace],
        "trace": [step.payload for step in receipt.trace],
        "branch_truth_state": receipt.branch_truth_state,
        "final_control_location": receipt.final_control_location,
        "return_selector": receipt.return_selector,
        "return_value": receipt.return_value,
        "halted": receipt.payload["halted"],
        "continuation_execution_opened": receipt.payload["continuation_execution_opened"],
        "return_execution_opened": receipt.payload["return_execution_opened"],
        "loops_opened": receipt.payload["loops_opened"],
        "function_calls_opened": receipt.payload["function_calls_opened"],
        "external_effects": receipt.payload["external_effects"],
        "static_runtime_fallback": receipt.payload["static_runtime_fallback"],
        "evidence_boundary": {
            "real_v023_resolver": True,
            "real_v024_program_unit": True,
            "real_full_program_executor": True,
            "real_v025_dispatch_receipt_model": True,
            "live_v020_kernel_execution": False,
            "live_v025_resident_dispatch": False,
        },
    }


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def persist_live_demo_receipt(
    document: Mapping[str, object],
    *,
    root: Path = CANONICAL_LIVE_ROOT,
) -> Path:
    if root != CANONICAL_LIVE_ROOT:
        raise RuntimeError("demo receipt persistence is fixed to /dev/shm/ciel_noema")
    if not root.is_dir():
        raise RuntimeError("canonical live NOEMA root is unavailable")
    try:
        binding = (root / "ciel_binding_status").read_text("utf-8").strip()
        seal = json.loads((root / "session/fast_admission.json").read_text("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("live NOEMA admission evidence is unavailable") from exc
    if binding != "ACTIVE":
        raise RuntimeError("NOEMA↔AUX binding is not ACTIVE")
    if seal.get("status") != "ACTIVE" or seal.get("no_static_fallback") is not True:
        raise RuntimeError("live NOEMA fast admission is not ACTIVE/no-fallback")

    execution_id = document.get("execution_id")
    if not isinstance(execution_id, str) or ":sha256:" not in execution_id:
        raise RuntimeError("demo document lacks content-addressed execution_id")
    digest = execution_id.rsplit(":", 1)[-1]
    target = root / "pncs/demo/full_program_v01" / f"{digest}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = _canonical_bytes(document)
    if target.exists():
        if target.read_bytes() != raw:
            raise RuntimeError("immutable demo receipt collision")
        return target
    tmp = target.with_name(f".{target.name}.tmp")
    tmp.write_bytes(raw)
    tmp.replace(target)
    return target


def run_demo(*, persist_live: bool = False) -> dict[str, object]:
    resolution = resolve_natural_program(PROGRAM)
    composition = resolution.composition
    unit = NativeProgramUnit.from_composition(composition)
    plan = compile_full_program_plan(unit, composition)
    dispatch = _demo_dispatch(unit.program_id)
    receipt = execute_prepared_program(plan, lambda: dispatch)

    if receipt.final_control_location != "runtime.memory.relief":
        raise RuntimeError("demo continuation order did not reach runtime.memory.relief")
    if receipt.return_selector != "result.control_location":
        raise RuntimeError("demo terminal RETURN selector mismatch")
    if receipt.return_value != "runtime.memory.relief":
        raise RuntimeError("demo RETURN value mismatch")
    if tuple(step.kind for step in receipt.trace) != (
        "CONTROL_DISPATCH",
        "CONTINUATION_ROUTE",
        "CONTINUATION_ROUTE",
        "RETURN",
    ):
        raise RuntimeError("demo PC trace mismatch")

    document = _receipt_document(
        receipt,
        source_program=PROGRAM,
        resolution_module=type(composition).__module__,
        program_unit_module=type(unit).__module__,
    )
    if persist_live:
        path = persist_live_demo_receipt(document)
        document = dict(document)
        document["live_receipt_path"] = str(path)
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PNCS full-program v0.1 end-to-end demo")
    parser.add_argument(
        "--persist-live",
        action="store_true",
        help="persist the content-addressed demo receipt under /dev/shm/ciel_noema",
    )
    args = parser.parse_args()
    result = run_demo(persist_live=args.persist_live)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
