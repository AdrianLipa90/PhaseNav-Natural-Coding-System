import pytest

from phasenav_natural_code.gremlin_noema_qhtri_isomorphism_bank_v01 import (
    SOURCE_PINS,
    NoemaQhtriBankCompilation,
    bank_manifest,
    compile_isomorphism_bank_candidates,
    isomorphism_bank,
    validate_isomorphism_bank_candidates,
)

KWARGS = {
    "generation_binding": "a" * 64,
    "identity": "ZOSIA_NOEMA_FIRST",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def test_bank_is_pinned_bounded_and_complete():
    entries = isomorphism_bank()
    assert len(entries) == 10
    assert len({entry.spec.isomorphism_id for entry in entries}) == 10
    assert set(SOURCE_PINS) == {"TIR", "IDT", "RFC", "SOH"}
    assert all(len(pin["commit"]) == 40 for pin in SOURCE_PINS.values())

    manifest = bank_manifest()
    assert manifest["entry_count"] == 10
    assert manifest["runtime_execution_authority"] is False
    assert manifest["canon_write_authority"] is False
    assert manifest["promotion_state"] == "CANDIDATE_ONLY"
    assert manifest["epistemic"] == "CHYBA"
    assert len(manifest["manifest_sha256"]) == 64


def test_cp1_poincare_entry_carries_distinct_metric_contracts():
    entry = next(x for x in isomorphism_bank() if x.spec.isomorphism_id == "ISO.NQ.03.CP1.POINCARE.CONTINUATION")
    text = " ".join(entry.guardrails).lower()
    assert "distinct metric contracts under maps_to" in text
    assert "curvature/signature/holonomy audit" in text
    assert entry.spec.edges[0].relation_type == "MAPS_TO"


def test_spinorial_sheet_is_required_by_bank():
    entry = next(x for x in isomorphism_bank() if x.spec.isomorphism_id == "ISO.NQ.04.SPINOR.SHEET.WITNESS")
    assert "central ±I sheet" in entry.preserved_structure
    assert any("requires the declared sheet witness" in guard for guard in entry.guardrails)


def test_bifurcation_preserves_magnitude_and_reverses_orientation():
    entry = next(x for x in isomorphism_bank() if x.spec.isomorphism_id == "ISO.NQ.02.IDT.BIFURCATION.NQ.RECEIPT")
    assert "M invariant under current reversal" in entry.preserved_structure
    assert "beta changes sign under current reversal" in entry.preserved_structure
    assert "B_phi(-beta)=B_phi(beta)^dagger" in entry.preserved_structure


def test_bank_compiles_only_candidate_read_only_graphs():
    compiled = compile_isomorphism_bank_candidates(**KWARGS)
    assert len(compiled.compilations) == 10
    assert len(compiled.manifest["compiled_entries"]) == 10
    for compilation in compiled.compilations.values():
        assert compilation.receipt["runtime_execution_authority"] is False
        assert compilation.receipt["canon_write_authority"] is False
        assert compilation.receipt["promotion_state"] == "CANDIDATE_ONLY"
        assert compilation.radical_candidate["kind"] == "RADICAL"
        assert compilation.operator_candidates[-1]["content"]["name"] == "ISO.RETURN"

    results = validate_isomorphism_bank_candidates(compiled)
    assert len(results) == 10
    for result in results.values():
        assert result.receipt["effect_boundary"]["external_effects"] is False
        assert result.program.mode == "READ_ONLY"
        assert result.program.epistemic == "CHYBA"


def test_direct_validator_rejects_tampered_aggregate_commitment():
    compiled = compile_isomorphism_bank_candidates(**KWARGS)
    manifest = dict(compiled.manifest)
    compiled_entries = {
        key: dict(value)
        for key, value in manifest["compiled_entries"].items()
    }
    first_id = sorted(compiled_entries)[0]
    compiled_entries[first_id]["receipt_sha256"] = "0" * 64
    manifest["compiled_entries"] = compiled_entries
    tampered = NoemaQhtriBankCompilation(
        compilations=compiled.compilations,
        manifest=manifest,
    )
    with pytest.raises(RuntimeError, match="aggregate manifest mismatch"):
        validate_isomorphism_bank_candidates(tampered)


def test_direct_validator_rejects_missing_leaf_before_execution():
    compiled = compile_isomorphism_bank_candidates(**KWARGS)
    leaves = dict(compiled.compilations)
    leaves.pop(sorted(leaves)[0])
    incomplete = NoemaQhtriBankCompilation(
        compilations=leaves,
        manifest=compiled.manifest,
    )
    with pytest.raises(RuntimeError, match="compilation keyset mismatch"):
        validate_isomorphism_bank_candidates(incomplete)
