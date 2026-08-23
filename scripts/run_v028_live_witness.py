#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys

from phasenav_natural_code.adversarial_v28 import (
    AdversarialV28Error,
    mutate_and_resign,
    validate_coupled_receipt_structure,
)
from phasenav_natural_code.execution_v20_model import BoundInternalProgram, DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT, _sha256_json
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

SCHEMA = "PNCS_V0_28_LIVE_ADVERSARIAL_WITNESS_V1"
ZERO = (0.0,) * 36


class LiveWitnessError(RuntimeError):
    pass


def _tupleize(value):
    if isinstance(value, list):
        return tuple(_tupleize(item) for item in value)
    if isinstance(value, dict):
        return {key: _tupleize(item) for key, item in value.items()}
    return value


def _guard(repo_root: Path, root: Path, socket_path: Path) -> dict[str, object]:
    guard = repo_root / "scripts/noema_aux_tether_guard.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(guard),
            "--root",
            str(root),
            "--require-socket",
            "--socket",
            str(socket_path),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        record = json.loads(proc.stdout.strip())
    except json.JSONDecodeError as exc:
        raise LiveWitnessError(f"tether guard returned invalid JSON: {proc.stdout!r} {proc.stderr!r}") from exc
    if proc.returncode != 0 or record.get("tether_status") != "ACTIVE" or record.get("failures") != []:
        raise LiveWitnessError(f"tether guard blocked: {record}")
    return record


def _definition_graph(registry_path: Path, content_id: str) -> tuple[object, ...]:
    matches = []
    for line in registry_path.read_text("utf-8").splitlines():
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
        raise LiveWitnessError("exactly one canonical Definition graph required")
    return unique[0]


def _active_chain(repo_root: Path, root: Path):
    active_paths = sorted((root / "pncs/v0.25/runtime/active").glob("*.json"))
    if len(active_paths) != 1:
        raise LiveWitnessError("exactly one active resident pointer required")
    active = json.loads(active_paths[0].read_text("utf-8"))
    if active.get("schema") != "PNCS_RESIDENT_ACTIVE_POINTER_V0_25":
        raise LiveWitnessError("unexpected resident active-pointer schema")

    dispatches = []
    for path in sorted((root / "pncs/v0.25/runtime/receipts/dispatch").glob("*.json")):
        record = json.loads(path.read_text("utf-8"))
        if (
            record.get("handle_id") == active.get("handle_id")
            and record.get("generation_id") == active.get("generation_id")
            and record.get("program_id") == active.get("program_id")
        ):
            dispatches.append(record)
    if len(dispatches) != 1:
        raise LiveWitnessError("exactly one dispatch for active resident pointer required")
    dispatch = dispatches[0]

    source_sha = str(dispatch["execution_receipt_sha256"])
    source_path = root / "pncs/v0.20/receipts" / f"{source_sha}.json"
    source = json.loads(source_path.read_text("utf-8"))
    if source.get("receipt_sha256") != source_sha:
        raise LiveWitnessError("active source v0.20 receipt identity mismatch")

    lineage_id = str(dispatch["lineage_id"])
    lineage_sha = lineage_id.rsplit(":", 1)[-1]
    lineage = json.loads((root / "pncs/v0.22/lineage" / f"{lineage_sha}.json").read_text("utf-8"))

    graph = _definition_graph(
        repo_root / "registry/definitions/PNCS_DEFINITION_REGISTRY_V0_11.jsonl",
        str(source["program"]["content_id"]),
    )
    authority = ProgramAuthority.from_v20_receipt(source, graph)
    resident = ResidentCoupledAuthority.from_records(authority, dispatch, lineage)
    resident.validate_active_pointer(root)
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


def _profile() -> tuple[OrchHydroControlProfile, HydrodynamicPhaseGate]:
    attractors = (
        AttractorReport("AttractorEC", 0.75, ZERO, 0.5, "LIVE_V028_EC"),
        AttractorReport("AttractorZS", 0.80, ZERO, 0.5, "LIVE_V028_ZS"),
        AttractorReport("AttractorLLMTemp", 0.0, ZERO, 0.0, "DISABLED"),
    )
    profile = OrchHydroControlProfile(
        SubjectiveTimeKernel(),
        1.0,
        attractors,
        TotalPotential(0, 0, 0, 0, 0, 0),
        ReductionKernel(1, 1, 1, 1, 10.0),
        1.0,
        0.0,
    )
    return profile, HydrodynamicPhaseGate(0.5, 0.2, steps=1, coordinate_dt=0.01)


def _expect_reject(source: dict[str, object], coupled: dict[str, object], name: str) -> dict[str, object]:
    if name == "operator_vector_substitution":
        attacked = mutate_and_resign(
            coupled,
            lambda r: r["orch_occurrences"][0].__setitem__("operator_vector_sha256", "0" * 64),
        )
        attacked_source = source
    elif name == "negative_local_proper_time":
        attacked = mutate_and_resign(
            coupled,
            lambda r: r["orch_occurrences"][0].__setitem__("proper_time_advanced", -0.01),
        )
        attacked_source = source
    elif name == "external_effect_boundary":
        attacked = mutate_and_resign(coupled, lambda r: r.__setitem__("external_effects", True))
        attacked_source = source
    elif name == "source_v20_tamper":
        attacked = coupled
        attacked_source = copy.deepcopy(source)
        attacked_source["result"]["control_location"] = "runtime.tampered"
    else:
        raise LiveWitnessError(f"unknown adversarial case: {name}")
    try:
        validate_coupled_receipt_structure(attacked, source_v20_receipt=attacked_source)
    except AdversarialV28Error as exc:
        return {
            "case": name,
            "expected": "REJECT",
            "observed": "REJECT",
            "pass": True,
            "detail_sha256": _sha256_json(str(exc)),
        }
    raise LiveWitnessError(f"adversarial case was accepted: {name}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_SURFACE_ROOT))
    ap.add_argument("--socket", default=str(DEFAULT_SOCKET))
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--persist", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    repo_root = Path(args.repo_root).resolve()
    socket_path = Path(args.socket)
    try:
        guard_before = _guard(repo_root, root, socket_path)
        source_template, dispatch, lineage, authority, resident, program, values = _active_chain(repo_root, root)
        profile, gate = _profile()
        paired = run_same_snapshot_conformance(
            program,
            values,
            str(dispatch["target"]),
            profile,
            {"*": gate},
            surface_root=root,
            socket_path=socket_path,
        )
        if not paired.semantic_projection_equal:
            raise LiveWitnessError("same-snapshot semantic projection mismatch")
        baseline_id = validate_coupled_receipt_structure(
            paired.coupled_receipt,
            source_v20_receipt=paired.source_receipt,
        )
        cases = [
            _expect_reject(paired.source_receipt, dict(paired.coupled_receipt), name)
            for name in (
                "operator_vector_substitution",
                "negative_local_proper_time",
                "external_effect_boundary",
                "source_v20_tamper",
            )
        ]
        guard_after = _guard(repo_root, root, socket_path)
        body = {
            "schema": SCHEMA,
            "status": "PASS_LIVE_V56_ADVERSARIAL_WITNESS",
            "paired_snapshot_contract_id": "PNCS_V0_28_SAME_LIVE_SNAPSHOT_CONFORMANCE",
            "live_root": str(root),
            "live_phi_sha256": paired.live_phi_sha256,
            "operator_registry_sha256": paired.operator_registry_sha256,
            "paired_source_v20_receipt_sha256": paired.source_receipt["receipt_sha256"],
            "paired_coupled_receipt_sha256": baseline_id,
            "semantic_projection_equal": True,
            "active_resident_source_v20_receipt_sha256": source_template["receipt_sha256"],
            "active_resident_authority_id": resident.authority_id,
            "active_dispatch_id": dispatch["dispatch_id"],
            "active_lineage_id": lineage["lineage_id"],
            "active_program_authority_id": authority.authority_id,
            "adversarial_cases": cases,
            "guard_before": guard_before,
            "guard_after": guard_after,
            "operational_resident_authority_opened_by_paired_harness": False,
            "routing_feedback_opened": False,
            "external_effects": False,
            "laboratory_time_modified": False,
            "static_runtime_fallback": False,
            "fail_closed": True,
        }
        witness_sha = _sha256_json(body)
        witness = {**body, "witness_sha256": witness_sha}
        if args.persist:
            out = root / "pncs/v0.28/live_witness" / f"{witness_sha}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(witness, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n", "utf-8")
            witness["witness_path"] = str(out)
        print(json.dumps(witness, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({
            "schema": SCHEMA,
            "status": "FAIL_CLOSED",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "fail_closed": True,
        }, sort_keys=True, ensure_ascii=False), file=sys.stderr)
        return 23


if __name__ == "__main__":
    raise SystemExit(main())
