from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping

from .gremlin_cross_formalism_bank_v02 import (
    CrossFormalismCompilation,
    compile_cross_formalism_candidates,
    validate_cross_formalism_candidates,
)

SEALED_BUNDLE_SCHEMA = "PNCS_GREMLIN_CROSS_FORMALISM_SEALED_BUNDLE_V0_1"


class CrossFormalismBundleError(RuntimeError):
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
    if len(generation_binding) != 64:
        raise CrossFormalismBundleError("generation_binding must be a 64-character hexadecimal commitment")
    try:
        int(generation_binding, 16)
    except ValueError as exc:
        raise CrossFormalismBundleError("generation_binding must be hexadecimal") from exc
    if not identity.strip():
        raise CrossFormalismBundleError("identity is required")
    if not authority.strip():
        raise CrossFormalismBundleError("authority is required")


def _candidate_payload(compiled: CrossFormalismCompilation) -> Mapping[str, object]:
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


def compile_sealed_cross_formalism_bundle(
    *,
    generation_binding: str,
    identity: str,
    authority: str,
) -> Mapping[str, object]:
    """Compile and validate the whole GREMLIN bank before producing one sealed authoring bundle."""
    _validate_provenance(generation_binding, identity, authority)

    # Deliberately compile in memory. Durable publication occurs only after every
    # candidate has compiled and the full bank has passed READ_ONLY validation.
    compiled = compile_cross_formalism_candidates(
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        authoring_root=None,
    )
    validation = validate_cross_formalism_candidates(compiled)
    if len(validation) != len(compiled.compilations):
        raise CrossFormalismBundleError("validation result count does not match compiled bank")

    validation_summary: dict[str, Mapping[str, object]] = {}
    for iso_id, result in sorted(validation.items()):
        external_effects = result.receipt["effect_boundary"]["external_effects"]
        if external_effects:
            raise CrossFormalismBundleError(f"external effect boundary violated by {iso_id}")
        if result.program.mode != "READ_ONLY":
            raise CrossFormalismBundleError(f"compiled candidate left READ_ONLY mode: {iso_id}")
        if result.program.epistemic != "CHYBA":
            raise CrossFormalismBundleError(f"compiled candidate left CHYBA epistemic mode: {iso_id}")
        validation_summary[iso_id] = {
            "external_effects": [],
            "mode": result.program.mode,
            "epistemic": result.program.epistemic,
            "receipt_sha256": compiled.compilations[iso_id].receipt["receipt_sha256"],
        }

    body = {
        "schema": SEALED_BUNDLE_SCHEMA,
        "bank_manifest": dict(compiled.manifest),
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


def verify_sealed_cross_formalism_bundle(bundle: Mapping[str, object]) -> bool:
    if bundle.get("schema") != SEALED_BUNDLE_SCHEMA:
        raise CrossFormalismBundleError("sealed bundle schema mismatch")
    if bundle.get("runtime_execution_authority") is not False:
        raise CrossFormalismBundleError("runtime authority mismatch")
    if bundle.get("canon_write_authority") is not False:
        raise CrossFormalismBundleError("canon authority mismatch")
    if bundle.get("promotion_state") != "CANDIDATE_ONLY":
        raise CrossFormalismBundleError("promotion state mismatch")
    if bundle.get("epistemic") != "CHYBA":
        raise CrossFormalismBundleError("epistemic state mismatch")

    expected = bundle.get("bundle_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise CrossFormalismBundleError("bundle commitment is missing or malformed")
    body = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    if _sha256(body) != expected:
        raise CrossFormalismBundleError("sealed bundle commitment mismatch")
    return True


def write_sealed_cross_formalism_bundle(bundle: Mapping[str, object], path: Path | str) -> Path:
    """Persist exactly one verified package using temp+fsync+atomic replace."""
    verify_sealed_cross_formalism_bundle(bundle)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise CrossFormalismBundleError(f"sealed bundle target already exists: {target}")

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
        os.replace(temporary_name, target)
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
