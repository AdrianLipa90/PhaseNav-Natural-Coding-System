from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import time
from typing import Mapping, Sequence

DIM = 36
BYTES_36D = DIM * 8
DEFAULT_SURFACE_ROOT = Path("/dev/shm/ciel_noema")
DEFAULT_SOCKET = Path("/run/user/1000/noema/ciel_headless.sock")
EXECUTION_CONTRACT_ID = "PNCS_NATIVE_EXECUTION_CORE_V0_20"
EXECUTION_SCHEMA = "PNCS_NATIVE_EXECUTION_V0_20"
RECEIPT_SCHEMA = "PNCS_NATIVE_EXECUTION_RECEIPT_V0_20"
SIGMA_SCHEMA = "PNCS_SIGMA_STATE_V0_20"
STEP_SCHEMA = "PNCS_KAKU_TRANSITION_V0_20"

# v0.20 has no external-effect semantics. These are the only PNV operators with
# admitted execution semantics in this gate. Every operator must also exist in
# the live PhaseNav operator registry under /dev/shm/ciel_noema.
EXECUTABLE_INTERNAL_OPERATORS = frozenset(
    {"IDENTITY", "DIFFERENCE", "CONDITION", "NEGATION", "COMPOSITION", "ORDER", "TRANSFORM"}
)

_CONTENT_ID_RE = re.compile(r"^pncs:def:sha256:[0-9a-f]{64}$")
_TYPED_SHA_RE = re.compile(r"^pncs:[a-z0-9-]+:sha256:[0-9a-f]{64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ROUTE_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_DEFINITION_CONTENT_SCHEMA = "PNCS_DEFINITION_CONTENT_V1"


class NativeExecutionV20Error(ValueError):
    pass


class LiveSurfaceV20Error(RuntimeError):
    pass


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise NativeExecutionV20Error("non-finite value is not canonical JSON")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise NativeExecutionV20Error(f"unsupported canonical value type: {type(value).__name__}")


def _compact_json(value: object) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_compact_json(value).encode("utf-8"))


def _typed_id(prefix: str, value: object) -> str:
    return f"{prefix}:sha256:{_sha256_json(value)}"


def _finite_scalar(value: object, field: str) -> float:
    try:
        out = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise NativeExecutionV20Error(f"{field} must be finite") from exc
    if not math.isfinite(out):
        raise NativeExecutionV20Error(f"{field} must be finite")
    return out


def _route(value: object, field: str) -> str:
    if not isinstance(value, str) or not _ROUTE_RE.fullmatch(value):
        raise NativeExecutionV20Error(f"{field} must be a canonical internal route")
    return value


def _predicate_leaf_path(node: object) -> tuple[str, ...]:
    if not isinstance(node, tuple) or not node:
        raise NativeExecutionV20Error("canonical predicate must be a non-empty tuple")
    kind = node[0]
    if kind == "comparison":
        if len(node) != 4:
            raise NativeExecutionV20Error("comparison canonical tuple must have four fields")
        subject, comparator, threshold = node[1], node[2], node[3]
        if not isinstance(subject, str) or not subject:
            raise NativeExecutionV20Error("comparison subject must be non-empty")
        if comparator not in {"lt", "gt", "eq"}:
            raise NativeExecutionV20Error("unsupported canonical comparator")
        _finite_scalar(threshold, "comparison threshold")
        return ("DIFFERENCE", "CONDITION")
    if kind == "not":
        if len(node) != 2:
            raise NativeExecutionV20Error("NOT canonical tuple must contain one child")
        return _predicate_leaf_path(node[1]) + ("NEGATION",)
    if kind in {"and", "or"}:
        if len(node) < 3:
            raise NativeExecutionV20Error("compound predicate requires at least two children")
        leaves: tuple[str, ...] = ()
        for child in node[1:]:
            leaves += _predicate_leaf_path(child)
        return leaves + ("COMPOSITION",) * (len(node) - 2)
    raise NativeExecutionV20Error(f"unsupported canonical predicate kind: {kind!r}")


def expected_leaf_path(canonical_graph: tuple[object, ...]) -> tuple[str, ...]:
    if not isinstance(canonical_graph, tuple) or len(canonical_graph) != 4 or canonical_graph[0] != "branch":
        raise NativeExecutionV20Error("v0.20 executes only canonical INTERNAL_BRANCH graphs")
    predicate, true_target, false_target = canonical_graph[1], canonical_graph[2], canonical_graph[3]
    _route(true_target, "true_target")
    if false_target is not None:
        _route(false_target, "false_target")
    pred_path = _predicate_leaf_path(predicate)
    if false_target is None:
        return pred_path + ("ORDER", "TRANSFORM", "COMPOSITION")
    return pred_path + (
        "NEGATION",
        "ORDER",
        "TRANSFORM",
        "ORDER",
        "TRANSFORM",
        "COMPOSITION",
    )


def definition_content_id(canonical_graph: tuple[object, ...], leaf_path: Sequence[str]) -> str:
    leaves = tuple(str(x) for x in leaf_path)
    if leaves != expected_leaf_path(canonical_graph):
        raise NativeExecutionV20Error("leaf_path does not exactly match canonical INTERNAL_BRANCH graph")
    payload = {
        "schema": _DEFINITION_CONTENT_SCHEMA,
        "kind": "INTERNAL_BRANCH",
        "canonical_graph": canonical_graph,
        "leaf_path": list(leaves),
    }
    return f"pncs:def:sha256:{_sha256_json(payload)}"


@dataclass(frozen=True)
class BoundInternalProgram:
    content_id: str
    canonical_graph: tuple[object, ...]
    leaf_path: tuple[str, ...]
    realization_id: str
    realization_binding_id: str
    mass_binding_id: str
    phase36_sha256: str
    semantic_mass: float

    def __post_init__(self) -> None:
        if not _CONTENT_ID_RE.fullmatch(self.content_id):
            raise NativeExecutionV20Error("content_id must be a PNCS Definition content ID")
        expected = definition_content_id(self.canonical_graph, self.leaf_path)
        if expected != self.content_id:
            raise NativeExecutionV20Error("canonical graph/content ID mismatch")
        for field in ("realization_id", "realization_binding_id", "mass_binding_id"):
            value = getattr(self, field)
            if not isinstance(value, str) or not _TYPED_SHA_RE.fullmatch(value):
                raise NativeExecutionV20Error(f"{field} must be a typed PNCS SHA-256 ID")
        if not isinstance(self.phase36_sha256, str) or not _DIGEST_RE.fullmatch(self.phase36_sha256):
            raise NativeExecutionV20Error("phase36_sha256 must be lowercase 64-hex SHA-256")
        object.__setattr__(self, "semantic_mass", _finite_scalar(self.semantic_mass, "semantic_mass"))

    @property
    def provenance_payload(self) -> dict[str, object]:
        return {
            "content_id": self.content_id,
            "realization_id": self.realization_id,
            "realization_binding_id": self.realization_binding_id,
            "mass_binding_id": self.mass_binding_id,
            "phase36_sha256": self.phase36_sha256,
            "semantic_mass": self.semantic_mass,
        }


def bind_internal_program(content: object, realization: object, mass_binding: object) -> BoundInternalProgram:
    """Bind the stabilized v0.11/v0.18/v0.19 lineage into an executable v0.20 unit.

    Mass is carried as verified provenance. It is not execution authorization.
    """
    if getattr(content, "kind", None) != "INTERNAL_BRANCH":
        raise NativeExecutionV20Error("v0.20 requires INTERNAL_BRANCH DefinitionContent")
    for obj, name in ((content, "content"), (realization, "realization"), (mass_binding, "mass_binding")):
        verify = getattr(obj, "verify", None)
        if not callable(verify):
            raise NativeExecutionV20Error(f"{name} does not expose its frozen verification contract")
        verify()

    content_id = str(getattr(content, "content_id"))
    if str(getattr(realization, "content_id", "")) != content_id:
        raise NativeExecutionV20Error("realization is not bound to the program content ID")
    mass_realization = getattr(mass_binding, "realization", None)
    if mass_realization is None:
        raise NativeExecutionV20Error("mass binding does not expose its exact realization")
    if str(getattr(mass_realization, "binding_id", "")) != str(getattr(realization, "binding_id", "")):
        raise NativeExecutionV20Error("mass binding realization does not match exact program realization")

    phase = getattr(realization, "phase", None)
    phase_sha = getattr(phase, "phase_sha256", None)
    if not isinstance(phase_sha, str):
        raise NativeExecutionV20Error("realization does not expose phase36_sha256")

    return BoundInternalProgram(
        content_id=content_id,
        canonical_graph=tuple(getattr(content, "canonical_graph")),
        leaf_path=tuple(getattr(content, "leaf_path")),
        realization_id=str(getattr(realization, "realization_id")),
        realization_binding_id=str(getattr(realization, "binding_id")),
        mass_binding_id=str(getattr(mass_binding, "mass_binding_id")),
        phase36_sha256=phase_sha,
        semantic_mass=_finite_scalar(getattr(mass_binding, "semantic_mass"), "semantic_mass"),
    )
