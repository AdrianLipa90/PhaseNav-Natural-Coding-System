from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping

from .gremlin_cross_formalism_round28_v01 import (
    Round28Compilation,
    compile_round28_candidates,
    validate_round28_candidates,
)

ROUND28_SEALED_SCHEMA = "PNCS_GREMLIN_ROUND28_SEALED_BUNDLE_V0_1"


class Round28BundleError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _validate_provenance(generation_binding: str, identity: str, authority: str) -> None:
    if not isinstance(generation_binding, str) or len(generation_binding) != 64:
        raise Round28BundleError("generation_binding must be a 64-character hexadecimal string")
    try:
        int(generation_binding, 16)
    except ValueError as exc:
        raise Round28BundleError("generation_binding must be hexadecimal") from exc
    if not isinstance(identity, str) or not identity.strip():
        raise Round28BundleError("identity is required")
    if not isinstance(authority, str) or not authority.strip():
        raise Round28BundleError("authority is required")


def _candidate_payload(compiled: Round28Compilation) -> Mapping[str, object]:
    return {
        iso_id: {
            "kaku_candidates": {
                kaku_id: dict(candidate)
                for kaku_id, candidate in sorted(compilation.kaku_candidates.items())
            },
            "radical_candidate": dict(compilation.radical_candidate),
            "operator_candidates": [dict(candidate) for candidate in compilation.operator_candidates],
            "pnv_text": compilation.pnv_text,
            "receipt": dict(compilation.receipt),
        }
        for iso_id, compilation in sorted(compiled.compilations.items())
    }


def compile_round28_sealed_bundle(
    *,
    generation_binding: str,
    identity: str,
    authority: str,
) -> Mapping[str, object]:
    _validate_provenance(generation_binding, identity, authority)
    compiled = compile_round28_candidates(
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
    )
    validation = validate_round28_candidates(compiled)
    if len(validation) != len(compiled.compilations):
        raise Round28BundleError("validation result count does not match compiled ROUND28 bank")

    validation_summary: dict[str, Mapping[str, object]] = {}
    for iso_id, result in sorted(validation.items()):
        if result.receipt["effect_boundary"]["external_effects"] is not False:
            raise Round28BundleError(f"external effect boundary violated by {iso_id}")
        if result.program.mode != "READ_ONLY":
            raise Round28BundleError(f"compiled candidate left READ_ONLY mode: {iso_id}")
        if result.program.epistemic != "CHYBA":
            raise Round28BundleError(f"compiled candidate left CHYBA epistemic mode: {iso_id}")
        validation_summary[iso_id] = {
            "external_effects": False,
            "mode": result.program.mode,
            "epistemic": result.program.epistemic,
            "receipt_sha256": compiled.compilations[iso_id].receipt["receipt_sha256"],
        }

    body = {
        "schema": ROUND28_SEALED_SCHEMA,
        "round28_manifest": dict(compiled.manifest),
        "caller_provenance": {
            "generation_binding": generation_binding,
            "identity": identity,
            "authority": authority,
        },
        "validation": validation_summary,
        "candidate_payload": _candidate_payload(compiled),
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "promotion_state": "CANDIDATE_ONLY",
        "epistemic": "CHYBA",
    }
    return {**body, "bundle_sha256": _sha256(body)}


def verify_round28_sealed_bundle(bundle: Mapping[str, object]) -> bool:
    if bundle.get("schema") != ROUND28_SEALED_SCHEMA:
        raise Round28BundleError("ROUND28 sealed bundle schema mismatch")
    if bundle.get("runtime_execution_authority") is not False:
        raise Round28BundleError("runtime authority mismatch")
    if bundle.get("canon_write_authority") is not False:
        raise Round28BundleError("canon authority mismatch")
    if bundle.get("promotion_state") != "CANDIDATE_ONLY":
        raise Round28BundleError("promotion state mismatch")
    if bundle.get("epistemic") != "CHYBA":
        raise Round28BundleError("epistemic state mismatch")

    expected = bundle.get("bundle_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise Round28BundleError("bundle commitment is missing or malformed")
    body = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    if _sha256(body) != expected:
        raise Round28BundleError("ROUND28 sealed bundle commitment mismatch")
    return True


def write_round28_sealed_bundle(bundle: Mapping[str, object], path: Path | str) -> Path:
    verify_round28_sealed_bundle(bundle)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical_bytes(bundle) + b"\n"
    temporary_name: str | None = None
    try:
        with NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

        try:
            os.link(temporary_name, target)
        except FileExistsError as exc:
            raise Round28BundleError(f"ROUND28 sealed target already exists: {target}") from exc
        os.unlink(temporary_name)
        temporary_name = None

        directory_fd = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
    return target
