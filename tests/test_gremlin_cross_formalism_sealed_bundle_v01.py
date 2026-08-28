from copy import deepcopy
import hashlib
import json

import pytest

from phasenav_natural_code.gremlin_cross_formalism_sealed_bundle_v01 import (
    CrossFormalismBundleError,
    SEALED_BUNDLE_SCHEMA,
    compile_sealed_cross_formalism_bundle,
    verify_sealed_cross_formalism_bundle,
    write_sealed_cross_formalism_bundle,
)


BASE = {
    "generation_binding": "b" * 64,
    "identity": "ZOSIA_NOEMA_FIRST",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def _reseal(bundle):
    body = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    raw = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    bundle["bundle_sha256"] = hashlib.sha256(raw).hexdigest()
    return bundle


def _reseal_bank_manifest(bundle):
    manifest = bundle["bank_manifest"]
    bank_body = {
        key: value
        for key, value in manifest.items()
        if key not in {"manifest_sha256", "compilation_schema", "compiled_entries"}
    }
    raw = json.dumps(
        bank_body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
    return _reseal(bundle)


@pytest.fixture(scope="module")
def sealed_bundle():
    return compile_sealed_cross_formalism_bundle(**BASE)


def test_sealed_bundle_binds_entire_candidate_package_and_provenance(sealed_bundle):
    assert sealed_bundle["schema"] == SEALED_BUNDLE_SCHEMA
    assert verify_sealed_cross_formalism_bundle(sealed_bundle) is True
    assert sealed_bundle["caller_provenance"] == BASE
    assert sealed_bundle["runtime_execution_authority"] is False
    assert sealed_bundle["canon_write_authority"] is False
    assert sealed_bundle["promotion_state"] == "CANDIDATE_ONLY"
    assert sealed_bundle["epistemic"] == "CHYBA"
    assert len(sealed_bundle["candidate_payload"]) == 8
    assert len(sealed_bundle["validation"]) == 8
    assert len(sealed_bundle["bundle_sha256"]) == 64

    for iso_id, validation in sealed_bundle["validation"].items():
        assert validation["external_effects"] is False
        assert validation["mode"] == "READ_ONLY"
        assert validation["epistemic"] == "CHYBA"
        assert validation["receipt_sha256"] == sealed_bundle["candidate_payload"][iso_id]["receipt"]["receipt_sha256"]


def test_caller_provenance_changes_bundle_commitment(sealed_bundle):
    changed = compile_sealed_cross_formalism_bundle(
        generation_binding=BASE["generation_binding"],
        identity="ZOSIA_NOEMA_SECOND",
        authority=BASE["authority"],
    )
    assert changed["bundle_sha256"] != sealed_bundle["bundle_sha256"]
    assert changed["caller_provenance"]["identity"] == "ZOSIA_NOEMA_SECOND"


def test_tamper_in_candidate_payload_fails_closed(sealed_bundle):
    tampered = deepcopy(sealed_bundle)
    iso_id = sorted(tampered["candidate_payload"])[0]
    tampered["candidate_payload"][iso_id]["pnv_text"] += "\n# tamper"
    with pytest.raises(CrossFormalismBundleError, match="commitment mismatch"):
        verify_sealed_cross_formalism_bundle(tampered)


def test_rehashed_pnv_tamper_fails_internal_holonomy(sealed_bundle):
    tampered = deepcopy(sealed_bundle)
    iso_id = sorted(tampered["candidate_payload"])[0]
    tampered["candidate_payload"][iso_id]["pnv_text"] += "\n# forged-and-resealed"
    _reseal(tampered)
    with pytest.raises(CrossFormalismBundleError, match="deterministic replay candidate payload mismatch"):
        verify_sealed_cross_formalism_bundle(tampered)


def test_rehashed_caller_provenance_tamper_fails_candidate_binding(sealed_bundle):
    tampered = deepcopy(sealed_bundle)
    tampered["caller_provenance"]["identity"] = "FORGED_IDENTITY"
    _reseal(tampered)
    with pytest.raises(CrossFormalismBundleError, match="deterministic replay bank manifest mismatch|candidate identity does not match caller provenance"):
        verify_sealed_cross_formalism_bundle(tampered)


def test_rehashed_candidate_envelope_tamper_fails_content_address(sealed_bundle):
    tampered = deepcopy(sealed_bundle)
    iso_id = sorted(tampered["candidate_payload"])[0]
    kaku_id = sorted(tampered["candidate_payload"][iso_id]["kaku_candidates"])[0]
    tampered["candidate_payload"][iso_id]["kaku_candidates"][kaku_id]["content"]["semantic_mass"] += 0.125
    _reseal(tampered)
    with pytest.raises(CrossFormalismBundleError, match="deterministic replay candidate payload mismatch"):
        verify_sealed_cross_formalism_bundle(tampered)


def test_rehashed_receipt_tamper_fails_receipt_commitment(sealed_bundle):
    tampered = deepcopy(sealed_bundle)
    iso_id = sorted(tampered["candidate_payload"])[0]
    tampered["candidate_payload"][iso_id]["receipt"]["pnv_graph_sha256"] = "0" * 64
    _reseal(tampered)
    with pytest.raises(CrossFormalismBundleError, match="deterministic replay candidate payload mismatch"):
        verify_sealed_cross_formalism_bundle(tampered)


def test_rehashed_source_bank_forgery_fails_deterministic_replay(sealed_bundle):
    tampered = deepcopy(sealed_bundle)
    tampered["bank_manifest"]["source_pins"]["TIR"]["commit"] = "0" * 40
    _reseal_bank_manifest(tampered)
    with pytest.raises(CrossFormalismBundleError, match="deterministic replay bank manifest mismatch"):
        verify_sealed_cross_formalism_bundle(tampered)


def test_invalid_generation_binding_fails_before_compilation():
    with pytest.raises(CrossFormalismBundleError, match="64-character"):
        compile_sealed_cross_formalism_bundle(
            generation_binding="abc",
            identity=BASE["identity"],
            authority=BASE["authority"],
        )
    with pytest.raises(CrossFormalismBundleError, match="hexadecimal"):
        compile_sealed_cross_formalism_bundle(
            generation_binding="z" * 64,
            identity=BASE["identity"],
            authority=BASE["authority"],
        )
    with pytest.raises(CrossFormalismBundleError, match="hexadecimal string"):
        compile_sealed_cross_formalism_bundle(
            generation_binding=None,
            identity=BASE["identity"],
            authority=BASE["authority"],
        )


def test_single_file_persistence_is_verified_and_no_overwrite(sealed_bundle, tmp_path):
    target = tmp_path / "round27.sealed.json"
    written = write_sealed_cross_formalism_bundle(sealed_bundle, target)
    assert written == target
    reopened = json.loads(target.read_text(encoding="utf-8"))
    assert reopened == sealed_bundle
    assert verify_sealed_cross_formalism_bundle(reopened) is True

    with pytest.raises(CrossFormalismBundleError, match="already exists"):
        write_sealed_cross_formalism_bundle(sealed_bundle, target)
