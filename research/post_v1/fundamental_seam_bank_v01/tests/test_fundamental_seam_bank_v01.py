from fundamental_seam_bank_v01 import (
    accelerated_collatz_block,
    bank_manifest,
    compile_fundamental_seam_candidates,
    fundamental_seam_bank,
    validate_accelerated_block,
    validate_fundamental_seam_candidates,
)


def test_fundamental_seam_bank_is_candidate_only_and_pinned():
    manifest = bank_manifest()
    assert manifest["schema"] == "PNCS_GREMLIN_FUNDAMENTAL_SEAM_BANK_V0_1"
    assert manifest["entry_count"] == 4
    assert manifest["promotion_state"] == "CANDIDATE_ONLY"
    assert manifest["runtime_execution_authority"] is False
    assert manifest["canon_write_authority"] is False
    assert set(manifest["source_pins"]) == {"TIR", "IDT", "RFC", "SOH", "INFINITIES"}


def test_entries_span_multiple_domains_and_have_firewalls():
    entries = fundamental_seam_bank()
    assert {entry.spec.isomorphism_id for entry in entries} == {
        "FSI.01.SE3.AFFINE.GLUE.TIR.RFC",
        "FSI.02.GLOBAL.COCYCLE.GLUE.SPINE",
        "FSI.03.REPRESENTATION.QUOTIENT.RELATIONAL.INVARIANT",
        "FSI.04.COLLATZ.ACCELERATED.BLOCK.PHASE",
    }
    for entry in entries:
        assert len({node.domain for node in entry.spec.nodes}) >= 2
        assert entry.guardrails
        assert entry.falsification_gate


def test_accelerated_collatz_block_matches_unreduced_block():
    for n in range(1, 1000, 2):
        assert validate_accelerated_block(n)


def test_known_collatz_block_examples():
    # n=3: 3 -> 10 -> 5, so a=1 and block 10.
    assert accelerated_collatz_block(3) == (5, 1, (1, 0))
    # n=5: 5 -> 16 -> 8 -> 4 -> 2 -> 1, so a=4 and block 10000.
    assert accelerated_collatz_block(5) == (1, 4, (1, 0, 0, 0, 0))


def test_all_seams_compile_through_existing_pncs_relational_graph_read_only():
    compiled = compile_fundamental_seam_candidates(
        generation_binding="test:fsi:v0.1",
        identity="test-suite",
        authority="candidate-only",
        authoring_root=None,
    )
    results = validate_fundamental_seam_candidates(compiled)
    assert len(results) == 4
    for result in results.values():
        assert result.receipt["effect_boundary"]["external_effects"] is False
