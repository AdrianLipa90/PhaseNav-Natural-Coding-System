from copy import deepcopy
import json

import pytest

from phasenav_natural_code.gremlin_round28_sealed_bundle_v01 import (
    ROUND28_SEALED_SCHEMA,
    Round28BundleError,
    compile_round28_sealed_bundle,
    verify_round28_sealed_bundle,
    write_round28_sealed_bundle,
)


BASE = {
    "generation_binding": "d" * 64,
    "identity": "ZOSIA_NOEMA_ROUND28",
    "authority": "USER_EXPLICIT_AUTHORING",
}


@pytest.fixture(scope="module")
def bundle():
    return compile_round28_sealed_bundle(**BASE)


def test_round28_bundle_binds_three_compiled_candidates(bundle):
    assert bundle["schema"] == ROUND28_SEALED_SCHEMA
    assert verify_round28_sealed_bundle(bundle) is True
    assert bundle["caller_provenance"] == BASE
    assert bundle["runtime_execution_authority"] is False
    assert bundle["canon_write_authority"] is False
    assert bundle["promotion_state"] == "CANDIDATE_ONLY"
    assert bundle["epistemic"] == "CHYBA"
    assert len(bundle["candidate_payload"]) == 3
    assert len(bundle["validation"]) == 3
    assert len(bundle["bundle_sha256"]) == 64

    for iso_id, validation in bundle["validation"].items():
        assert validation["external_effects"] is False
        assert validation["mode"] == "READ_ONLY"
        assert validation["epistemic"] == "CHYBA"
        assert validation["receipt_sha256"] == bundle["candidate_payload"][iso_id]["receipt"]["receipt_sha256"]


def test_round28_provenance_changes_seal(bundle):
    changed = compile_round28_sealed_bundle(
        generation_binding=BASE["generation_binding"],
        identity="ZOSIA_NOEMA_ROUND28_ALT",
        authority=BASE["authority"],
    )
    assert changed["bundle_sha256"] != bundle["bundle_sha256"]


def test_round28_candidate_tamper_fails_closed(bundle):
    tampered = deepcopy(bundle)
    iso_id = sorted(tampered["candidate_payload"])[0]
    tampered["candidate_payload"][iso_id]["pnv_text"] += "\n# tamper"
    with pytest.raises(Round28BundleError, match="commitment mismatch"):
        verify_round28_sealed_bundle(tampered)


def test_round28_invalid_generation_binding_fails_closed():
    with pytest.raises(Round28BundleError, match="64-character"):
        compile_round28_sealed_bundle(
            generation_binding="abc",
            identity=BASE["identity"],
            authority=BASE["authority"],
        )
    with pytest.raises(Round28BundleError, match="hexadecimal"):
        compile_round28_sealed_bundle(
            generation_binding="z" * 64,
            identity=BASE["identity"],
            authority=BASE["authority"],
        )


def test_round28_atomic_create_once_persistence(bundle, tmp_path):
    target = tmp_path / "round28.sealed.json"
    written = write_round28_sealed_bundle(bundle, target)
    assert written == target
    reopened = json.loads(target.read_text(encoding="utf-8"))
    assert reopened == bundle
    assert verify_round28_sealed_bundle(reopened) is True

    with pytest.raises(Round28BundleError, match="already exists"):
        write_round28_sealed_bundle(bundle, target)
