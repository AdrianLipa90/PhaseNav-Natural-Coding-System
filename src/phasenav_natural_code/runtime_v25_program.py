from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Mapping

from .runtime_v25_core import (
    DEFAULT_SURFACE_ROOT, PROGRAM_IMAGE_SCHEMA, RUNTIME_CONTRACT_ID,
    V22_LINEAGE_CONTRACT_ID, V24_BUILD_CONTRACT_ID, V24_BUILD_SCHEMA,
    PersistentRuntimeV25Error, _BUILD_RE, _COMPOSITION_RE, _DEFINITION_RE, _PROGRAM_RE,
    _digest, _load_json, _sha256_bytes, _sha256_json, _typed, _typed_id,
)

@dataclass(frozen=True)
class ProgramImage:
    program_id: str
    composition_id: str
    build_id: str
    pnv_sha256: str
    pnv_size_bytes: int
    operator_schedule_sha256: str
    control_definition_id: str
    lineage_contract_id: str
    pnv_bytes: bytes

    def __post_init__(self) -> None:
        _typed(self.program_id, _PROGRAM_RE, "program_id")
        _typed(self.composition_id, _COMPOSITION_RE, "composition_id")
        _typed(self.build_id, _BUILD_RE, "build_id")
        _digest(self.pnv_sha256, "pnv_sha256")
        _digest(self.operator_schedule_sha256, "operator_schedule_sha256")
        _typed(self.control_definition_id, _DEFINITION_RE, "control_definition_id")
        if self.lineage_contract_id != V22_LINEAGE_CONTRACT_ID:
            raise PersistentRuntimeV25Error("v0.25 requires exact v0.22 lineage contract")
        if not isinstance(self.pnv_size_bytes, int) or self.pnv_size_bytes <= 0:
            raise PersistentRuntimeV25Error("pnv_size_bytes must be positive")
        if len(self.pnv_bytes) != self.pnv_size_bytes or _sha256_bytes(self.pnv_bytes) != self.pnv_sha256:
            raise PersistentRuntimeV25Error("program image bytes/hash/size mismatch")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": PROGRAM_IMAGE_SCHEMA,
            "runtime_contract_id": RUNTIME_CONTRACT_ID,
            "program_id": self.program_id,
            "composition_id": self.composition_id,
            "build_id": self.build_id,
            "pnv_sha256": self.pnv_sha256,
            "pnv_size_bytes": self.pnv_size_bytes,
            "operator_schedule_sha256": self.operator_schedule_sha256,
            "control_definition_id": self.control_definition_id,
            "required_result_lineage_contract_id": self.lineage_contract_id,
            "source_text_is_authority": False,
            "repository_location_is_authority": False,
            "external_effects": False,
            "static_runtime_fallback": False,
        }

    @property
    def image_id(self) -> str:
        return _typed_id("pncs:program-image", self.payload)


def _parse_v24_program(raw: bytes) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PersistentRuntimeV25Error("v0.24 program bytes are not UTF-8") from exc
    if not text.endswith("\n"):
        raise PersistentRuntimeV25Error("v0.24 program bytes are not canonical newline-terminated text")
    lines = text.splitlines()
    if tuple(lines[:4]) != (
        "PNV 1",
        "PNCS PROGRAM_UNIT 0.24",
        "EPISTEMIC CHYBA",
        "MODE READ_ONLY",
    ):
        raise PersistentRuntimeV25Error("unsupported v0.24 program header")

    def one(prefix: str) -> str:
        matches = [line[len(prefix):] for line in lines if line.startswith(prefix)]
        if len(matches) != 1:
            raise PersistentRuntimeV25Error(f"expected exactly one {prefix.strip()} declaration")
        return matches[0]

    program_id = _typed(one("PROGRAM_ID "), _PROGRAM_RE, "program_id")
    composition_id = _typed(one("COMPOSITION_ID "), _COMPOSITION_RE, "composition_id")
    schedule_sha = _digest(one("OPERATOR_SCHEDULE_SHA256 "), "operator_schedule_sha256")
    lineage_contract = one("LINEAGE_CONTRACT ")
    if lineage_contract != V22_LINEAGE_CONTRACT_ID:
        raise PersistentRuntimeV25Error("serialized program lost v0.22 lineage requirement")

    definition_lines = [line.split(" ", 3)[3] for line in lines if re.fullmatch(r"DEPENDENCY \d{3} CONTROL_DEFINITION pncs:def:sha256:[0-9a-f]{64}", line)]
    if len(definition_lines) != 1:
        raise PersistentRuntimeV25Error("v0.24 program requires exactly one control Definition dependency")
    control_definition_id = _typed(definition_lines[0], _DEFINITION_RE, "control_definition_id")
    occurrence = [line.split(" ", 3)[3] for line in lines if re.fullmatch(r"OCCURRENCE 000 CONTROL_DEFINITION pncs:def:sha256:[0-9a-f]{64}", line)]
    if occurrence != [control_definition_id]:
        raise PersistentRuntimeV25Error("control Definition closure/occurrence mismatch")

    ops: list[str] = []
    for line in lines:
        match = re.fullmatch(r"OPERATOR (\d{3}) ([A-Z][A-Z0-9_]*)", line)
        if match:
            if int(match.group(1)) != len(ops):
                raise PersistentRuntimeV25Error("operator indexes are not contiguous")
            ops.append(match.group(2))
    if not ops or ops[-1] != "RETURN":
        raise PersistentRuntimeV25Error("v0.24 program operator schedule must terminate in RETURN")
    if _sha256_json(ops) != schedule_sha:
        raise PersistentRuntimeV25Error("serialized operator schedule SHA mismatch")

    for required in (
        "EXTERNAL_EFFECTS FALSE",
        "FREE_FORM_NL_EXECUTION FALSE",
        "NATIVE_EXECUTION_OPENED FALSE",
        "RETURN_EXECUTION_OPENED FALSE",
        "STATIC_RUNTIME_FALLBACK FALSE",
        "END PROGRAM_UNIT",
    ):
        if lines.count(required) != 1:
            raise PersistentRuntimeV25Error(f"missing or duplicate closed boundary: {required}")
    return {
        "program_id": program_id,
        "composition_id": composition_id,
        "operator_schedule_sha256": schedule_sha,
        "control_definition_id": control_definition_id,
        "lineage_contract_id": lineage_contract,
    }


def program_image_from_artifacts(
    program_path: Path | str,
    build_receipt_path: Path | str,
    *,
    expected_program_id: str,
) -> ProgramImage:
    expected_program_id = _typed(expected_program_id, _PROGRAM_RE, "expected_program_id")
    ppath = Path(program_path)
    rpath = Path(build_receipt_path)
    try:
        raw = ppath.read_bytes()
    except OSError as exc:
        raise PersistentRuntimeV25Error(f"cannot read v0.24 program artifact: {ppath}") from exc
    parsed = _parse_v24_program(raw)
    if parsed["program_id"] != expected_program_id:
        raise PersistentRuntimeV25Error("v0.24 PROGRAM_ID differs from registered authority")

    receipt = _load_json(rpath, "v0.24 build receipt")
    if receipt.get("schema") != V24_BUILD_SCHEMA or receipt.get("build_contract_id") != V24_BUILD_CONTRACT_ID:
        raise PersistentRuntimeV25Error("v0.24 build receipt schema/contract mismatch")
    build_id = _typed(receipt.get("build_id"), _BUILD_RE, "build_id")
    body = dict(receipt)
    body.pop("build_id", None)
    if _typed_id("pncs:program-build", body) != build_id:
        raise PersistentRuntimeV25Error("v0.24 build receipt digest mismatch")
    if receipt.get("program_id") != expected_program_id or receipt.get("composition_id") != parsed["composition_id"]:
        raise PersistentRuntimeV25Error("v0.24 build receipt program/composition mismatch")
    pnv_sha = _sha256_bytes(raw)
    if receipt.get("pnv_sha256") != pnv_sha or int(receipt.get("pnv_size_bytes", -1)) != len(raw):
        raise PersistentRuntimeV25Error("v0.24 build receipt program bytes mismatch")
    if receipt.get("operator_schedule_sha256") != parsed["operator_schedule_sha256"]:
        raise PersistentRuntimeV25Error("v0.24 build receipt operator schedule mismatch")
    if receipt.get("roundtrip_byte_identical") is not True or receipt.get("deterministic_fields_only") is not True:
        raise PersistentRuntimeV25Error("v0.24 build receipt is not deterministic round-trip authority")
    for field in ("execution_opened", "return_execution_opened", "external_effects", "static_runtime_fallback"):
        if receipt.get(field) is not False:
            raise PersistentRuntimeV25Error(f"v0.24 build receipt opens forbidden boundary: {field}")
    live = receipt.get("live_surface")
    if not isinstance(live, Mapping) or live.get("root") != str(DEFAULT_SURFACE_ROOT):
        raise PersistentRuntimeV25Error("v0.24 build receipt is not bound to canonical /dev/shm surface")

    return ProgramImage(
        program_id=expected_program_id,
        composition_id=str(parsed["composition_id"]),
        build_id=build_id,
        pnv_sha256=pnv_sha,
        pnv_size_bytes=len(raw),
        operator_schedule_sha256=str(parsed["operator_schedule_sha256"]),
        control_definition_id=str(parsed["control_definition_id"]),
        lineage_contract_id=str(parsed["lineage_contract_id"]),
        pnv_bytes=raw,
    )

