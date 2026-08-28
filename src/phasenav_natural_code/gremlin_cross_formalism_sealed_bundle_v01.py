from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping

from .gremlin_cross_formalism_bank_v02 import (
    COMPILATION_SCHEMA,
    CrossFormalismCompilation,
    compile_cross_formalism_candidates,
    validate_cross_formalism_candidates,
)
from .gremlin_pnv_authoring_v02 import CANDIDATE_SCHEMA, render_operator_program
from .gremlin_relational_compiler_v01 import COMPILATION_RECEIPT_SCHEMA
from .native_pnv_exec_v01 import parse_pnv

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
    if not isinstance(generation_binding, str):
        raise CrossFormalismBundleError("generation_binding must be a hexadecimal string")
    if len(generation_binding) != 64:
        raise CrossFormalismBundleError("generation_binding must be a 64-character hexadecimal commitment")
    try:
        int(generation_binding, 16)
    except ValueError as exc:
        raise CrossFormalismBundleError("generation_binding must be hexadecimal") from exc
    if not isinstance(identity, str) or not identity.strip():
        raise CrossFormalismBundleError("identity is required")
    if not isinstance(authority, str) or not authority.strip():
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


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CrossFormalismBundleError(f"{label} must be a mapping")
    return value


def _verify_candidate_envelope(
    candidate: Mapping[str, object],
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    expected_kind: str,
) -> str:
    kind = str(candidate.get("kind", "")).upper()
    if candidate.get("schema") != CANDIDATE_SCHEMA:
        raise CrossFormalismBundleError("candidate schema mismatch")
    if kind != expected_kind:
        raise CrossFormalismBundleError(f"candidate kind mismatch: expected {expected_kind}, observed {kind}")
    if candidate.get("promotion_state") != "CANDIDATE_ONLY":
        raise CrossFormalismBundleError("candidate promotion state mismatch")
    if candidate.get("epistemic") != "CHYBA":
        raise CrossFormalismBundleError("candidate epistemic state mismatch")
    if candidate.get("runtime_execution_authority") is not False:
        raise CrossFormalismBundleError("candidate runtime authority mismatch")
    if candidate.get("canon_write_authority") is not False:
        raise CrossFormalismBundleError("candidate canon authority mismatch")
    if candidate.get("generation_binding") != generation_binding:
        raise CrossFormalismBundleError("candidate generation binding does not match caller provenance")
    if candidate.get("identity") != identity:
        raise CrossFormalismBundleError("candidate identity does not match caller provenance")
    if candidate.get("authority") != authority:
        raise CrossFormalismBundleError("candidate authority does not match caller provenance")

    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str):
        raise CrossFormalismBundleError("candidate_id is missing")
    body = {key: value for key, value in candidate.items() if key != "candidate_id"}
    expected_id = f"pncs:gremlin-{kind.lower()}:sha256:{_sha256(body)}"
    if candidate_id != expected_id:
        raise CrossFormalismBundleError("candidate content hash mismatch")
    return candidate_id


def _verify_compilation_receipt(receipt: Mapping[str, object]) -> str:
    if receipt.get("schema") != COMPILATION_RECEIPT_SCHEMA:
        raise CrossFormalismBundleError("compilation receipt schema mismatch")
    if receipt.get("promotion_state") != "CANDIDATE_ONLY":
        raise CrossFormalismBundleError("compilation receipt promotion state mismatch")
    if receipt.get("epistemic") != "CHYBA":
        raise CrossFormalismBundleError("compilation receipt epistemic state mismatch")
    if receipt.get("runtime_execution_authority") is not False:
        raise CrossFormalismBundleError("compilation receipt runtime authority mismatch")
    if receipt.get("canon_write_authority") is not False:
        raise CrossFormalismBundleError("compilation receipt canon authority mismatch")

    receipt_sha256 = receipt.get("receipt_sha256")
    if not isinstance(receipt_sha256, str) or len(receipt_sha256) != 64:
        raise CrossFormalismBundleError("compilation receipt commitment is missing or malformed")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if _sha256(body) != receipt_sha256:
        raise CrossFormalismBundleError("compilation receipt commitment mismatch")
    return receipt_sha256


def _verify_bank_manifest(manifest: Mapping[str, object]) -> Mapping[str, object]:
    if manifest.get("compilation_schema") != COMPILATION_SCHEMA:
        raise CrossFormalismBundleError("cross-formalism compilation schema mismatch")
    if manifest.get("runtime_execution_authority") is not False:
        raise CrossFormalismBundleError("bank manifest runtime authority mismatch")
    if manifest.get("canon_write_authority") is not False:
        raise CrossFormalismBundleError("bank manifest canon authority mismatch")
    if manifest.get("promotion_state") != "CANDIDATE_ONLY":
        raise CrossFormalismBundleError("bank manifest promotion state mismatch")
    if manifest.get("epistemic") != "CHYBA":
        raise CrossFormalismBundleError("bank manifest epistemic state mismatch")

    manifest_sha256 = manifest.get("manifest_sha256")
    if not isinstance(manifest_sha256, str) or len(manifest_sha256) != 64:
        raise CrossFormalismBundleError("bank manifest commitment is missing or malformed")
    bank_body = {
        key: value
        for key, value in manifest.items()
        if key not in {"manifest_sha256", "compilation_schema", "compiled_entries"}
    }
    if _sha256(bank_body) != manifest_sha256:
        raise CrossFormalismBundleError("source-bank manifest commitment mismatch")

    compiled_entries = _require_mapping(manifest.get("compiled_entries"), "compiled_entries")
    entry_count = manifest.get("entry_count")
    if not isinstance(entry_count, int) or entry_count != len(compiled_entries):
        raise CrossFormalismBundleError("bank manifest entry count mismatch")
    return compiled_entries


def _verify_internal_holonomy(bundle: Mapping[str, object]) -> None:
    caller = _require_mapping(bundle.get("caller_provenance"), "caller_provenance")
    generation_binding = caller.get("generation_binding")
    identity = caller.get("identity")
    authority = caller.get("authority")
    _validate_provenance(generation_binding, identity, authority)  # type: ignore[arg-type]

    manifest = _require_mapping(bundle.get("bank_manifest"), "bank_manifest")
    compiled_entries = _verify_bank_manifest(manifest)
    candidate_payload = _require_mapping(bundle.get("candidate_payload"), "candidate_payload")
    validation = _require_mapping(bundle.get("validation"), "validation")

    keyset = set(candidate_payload)
    if set(compiled_entries) != keyset or set(validation) != keyset:
        raise CrossFormalismBundleError("bundle entry keysets do not agree")
    if manifest.get("entry_count") != len(keyset):
        raise CrossFormalismBundleError("bundle entry count does not agree with bank manifest")

    for iso_id in sorted(keyset):
        payload = _require_mapping(candidate_payload[iso_id], f"candidate_payload[{iso_id}]")
        kaku_candidates = _require_mapping(payload.get("kaku_candidates"), f"kaku_candidates[{iso_id}]")
        if not kaku_candidates:
            raise CrossFormalismBundleError(f"candidate payload has no KAKU nodes: {iso_id}")

        kaku_ids: dict[str, str] = {}
        for kaku_id, raw_candidate in sorted(kaku_candidates.items()):
            candidate = _require_mapping(raw_candidate, f"KAKU candidate {iso_id}/{kaku_id}")
            candidate_id = _verify_candidate_envelope(
                candidate,
                generation_binding=generation_binding,  # type: ignore[arg-type]
                identity=identity,  # type: ignore[arg-type]
                authority=authority,  # type: ignore[arg-type]
                expected_kind="KAKU",
            )
            content = _require_mapping(candidate.get("content"), f"KAKU content {iso_id}/{kaku_id}")
            if content.get("kaku_id") != kaku_id:
                raise CrossFormalismBundleError(f"KAKU id/content mismatch: {iso_id}/{kaku_id}")
            kaku_ids[kaku_id] = candidate_id

        radical = _require_mapping(payload.get("radical_candidate"), f"radical_candidate[{iso_id}]")
        radical_id = _verify_candidate_envelope(
            radical,
            generation_binding=generation_binding,  # type: ignore[arg-type]
            identity=identity,  # type: ignore[arg-type]
            authority=authority,  # type: ignore[arg-type]
            expected_kind="RADICAL",
        )
        radical_content = _require_mapping(radical.get("content"), f"radical content {iso_id}")
        radical_kaku_ids = _require_mapping(radical_content.get("kaku_candidate_ids"), f"radical KAKU refs {iso_id}")
        if dict(radical_kaku_ids) != kaku_ids:
            raise CrossFormalismBundleError(f"RADICAL KAKU dependency map mismatch: {iso_id}")
        radical_dependencies = radical.get("dependency_ids")
        if not isinstance(radical_dependencies, list) or sorted(radical_dependencies) != sorted(kaku_ids.values()):
            raise CrossFormalismBundleError(f"RADICAL dependency_ids mismatch: {iso_id}")

        raw_operators = payload.get("operator_candidates")
        if not isinstance(raw_operators, list) or not raw_operators:
            raise CrossFormalismBundleError(f"operator_candidates must be a non-empty list: {iso_id}")
        operators: list[Mapping[str, object]] = []
        operator_ids: list[str] = []
        for index, raw_operator in enumerate(raw_operators):
            operator = _require_mapping(raw_operator, f"OPERATOR candidate {iso_id}/{index}")
            operator_id = _verify_candidate_envelope(
                operator,
                generation_binding=generation_binding,  # type: ignore[arg-type]
                identity=identity,  # type: ignore[arg-type]
                authority=authority,  # type: ignore[arg-type]
                expected_kind="OPERATOR",
            )
            content = _require_mapping(operator.get("content"), f"OPERATOR content {iso_id}/{index}")
            if content.get("radical_candidate_id") != radical_id:
                raise CrossFormalismBundleError(f"OPERATOR RADICAL binding mismatch: {iso_id}/{index}")
            dependencies = operator.get("dependency_ids")
            if dependencies != [radical_id]:
                raise CrossFormalismBundleError(f"OPERATOR dependency_ids mismatch: {iso_id}/{index}")
            operators.append(operator)
            operator_ids.append(operator_id)

        pnv_text = payload.get("pnv_text")
        if not isinstance(pnv_text, str):
            raise CrossFormalismBundleError(f"pnv_text must be a string: {iso_id}")
        expected_pnv = render_operator_program(tuple(operators), emits=("ISO.RETURN",), mode="READ_ONLY")
        if pnv_text != expected_pnv:
            raise CrossFormalismBundleError(f"PNV source no longer matches operator candidates: {iso_id}")
        parsed = parse_pnv(pnv_text)

        receipt = _require_mapping(payload.get("receipt"), f"receipt[{iso_id}]")
        receipt_sha256 = _verify_compilation_receipt(receipt)
        if receipt.get("isomorphism_id") != iso_id:
            raise CrossFormalismBundleError(f"receipt isomorphism id mismatch: {iso_id}")
        if receipt.get("node_candidate_ids") != kaku_ids:
            raise CrossFormalismBundleError(f"receipt KAKU candidate ids mismatch: {iso_id}")
        if receipt.get("radical_candidate_id") != radical_id:
            raise CrossFormalismBundleError(f"receipt RADICAL candidate id mismatch: {iso_id}")
        if receipt.get("operator_candidate_ids") != operator_ids:
            raise CrossFormalismBundleError(f"receipt OPERATOR candidate ids mismatch: {iso_id}")
        if receipt.get("pnv_source_sha256") != parsed.source_sha256:
            raise CrossFormalismBundleError(f"receipt PNV source commitment mismatch: {iso_id}")
        if receipt.get("pnv_graph_sha256") != parsed.graph_sha256:
            raise CrossFormalismBundleError(f"receipt PNV graph commitment mismatch: {iso_id}")

        manifest_entry = _require_mapping(compiled_entries[iso_id], f"compiled_entries[{iso_id}]")
        expected_manifest_entry = {
            "receipt_sha256": receipt_sha256,
            "radical_candidate_id": radical_id,
            "pnv_graph_sha256": parsed.graph_sha256,
        }
        if dict(manifest_entry) != expected_manifest_entry:
            raise CrossFormalismBundleError(f"compiled entry manifest mismatch: {iso_id}")

        validation_entry = _require_mapping(validation[iso_id], f"validation[{iso_id}]")
        expected_validation = {
            "external_effects": False,
            "mode": "READ_ONLY",
            "epistemic": "CHYBA",
            "receipt_sha256": receipt_sha256,
        }
        if dict(validation_entry) != expected_validation:
            raise CrossFormalismBundleError(f"validation summary mismatch: {iso_id}")


def compile_sealed_cross_formalism_bundle(
    *,
    generation_binding: str,
    identity: str,
    authority: str,
) -> Mapping[str, object]:
    """Compile and validate the whole GREMLIN bank before producing one sealed authoring bundle."""
    _validate_provenance(generation_binding, identity, authority)

    # Compile in memory. Durable publication occurs only after every candidate
    # has compiled and the full bank has passed READ_ONLY validation.
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
        if external_effects is not False:
            raise CrossFormalismBundleError(f"external effect boundary violated by {iso_id}")
        if result.program.mode != "READ_ONLY":
            raise CrossFormalismBundleError(f"compiled candidate left READ_ONLY mode: {iso_id}")
        if result.program.epistemic != "CHYBA":
            raise CrossFormalismBundleError(f"compiled candidate left CHYBA epistemic mode: {iso_id}")
        validation_summary[iso_id] = {
            "external_effects": False,
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
    bundle = {**body, "bundle_sha256": _sha256(body)}
    _verify_internal_holonomy(bundle)
    return bundle


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

    _verify_internal_holonomy(bundle)
    return True


def write_sealed_cross_formalism_bundle(bundle: Mapping[str, object], path: Path | str) -> Path:
    """Persist one verified package with fsync and atomic create-once publication."""
    verify_sealed_cross_formalism_bundle(bundle)
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

        # Same-directory hard-link publication is atomic and fails if another
        # writer has already claimed the final create-once path.
        try:
            os.link(temporary_name, target)
        except FileExistsError as exc:
            raise CrossFormalismBundleError(f"sealed bundle target already exists: {target}") from exc
        except OSError as exc:
            raise CrossFormalismBundleError(f"cannot atomically publish sealed bundle: {target}") from exc
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
