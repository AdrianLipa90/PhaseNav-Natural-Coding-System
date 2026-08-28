from phasenav_natural_code.gremlin_tau_codec_v01 import (
    CODEC_INVARIANT_ID,
    CODEC_LEFT_FRAGMENT_ID,
    CODEC_RIGHT_FRAGMENT_ID,
    compile_tau_codec_candidate,
    tau_codec_fragments,
    tau_codec_isomorphism,
    validate_tau_codec_candidate,
)

KWARGS = {
    "generation_binding": "a" * 64,
    "identity": "ZOSIA_NOEMA_FIRST",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def test_tau_codec_fragments_share_state_memory_join_node():
    left, right = tau_codec_fragments()
    assert left.invariant_id == right.invariant_id == CODEC_INVARIANT_ID
    assert {n.kaku.kaku_id for n in left.nodes}.intersection(
        {n.kaku.kaku_id for n in right.nodes}
    ) == {"K.LIMINAL.SEGMENT"}


def test_tau_codec_isomorphism_spans_required_domains():
    spec = tau_codec_isomorphism()
    assert spec.invariant_id == CODEC_INVARIANT_ID
    assert {node.domain for node in spec.nodes} == {
        "PNCS",
        "PNCS_T36",
        "PNV_STATE_MEMORY",
        "BIOOS",
        "PNH5_COMPAT",
    }
    assert f"isomorphism-fragment:{CODEC_LEFT_FRAGMENT_ID}" in spec.evidence_refs
    assert f"isomorphism-fragment:{CODEC_RIGHT_FRAGMENT_ID}" in spec.evidence_refs


def test_GREMLIN_builds_kaku_radical_and_operators_for_merged_codec():
    candidate = compile_tau_codec_candidate(**KWARGS)
    compilation = candidate.compilation
    assert set(compilation.kaku_candidates) == {
        "K.TAU.FRAME",
        "K.T36.WITNESS",
        "K.LIMINAL.SEGMENT",
        "K.PNLF.FILE",
        "K.PNH5.VIEW",
    }
    assert compilation.radical_candidate["kind"] == "RADICAL"
    assert compilation.operator_candidates[-1]["content"]["name"] == "ISO.RETURN"
    assert candidate.codec_manifest["isomorphic_merge_applied"] is True
    assert candidate.codec_manifest["shared_merge_node"] == "K.LIMINAL.SEGMENT"
    assert candidate.codec_manifest["source_isomorphism_fragments"] == [
        CODEC_LEFT_FRAGMENT_ID,
        CODEC_RIGHT_FRAGMENT_ID,
    ]
    assert candidate.codec_manifest["promotion_state"] == "CANDIDATE_ONLY"
    assert candidate.codec_manifest["runtime_execution_authority"] is False
    assert candidate.codec_manifest["canon_write_authority"] is False


def test_isomorphic_edges_lower_to_composition():
    candidate = compile_tau_codec_candidate(**KWARGS)
    plan = {row["relation_id"]: row["opcode"] for row in candidate.compilation.receipt["relation_plan"]}
    assert plan["REL.TAU.LIMINAL"] == "COMPOSITION"
    assert plan["REL.LIMINAL.FILE"] == "COMPOSITION"
    assert plan["REL.TAU.T36"] == "COMPOSITION"
    assert plan["REL.FILE.PNH5"] == "COMPOSITION"


def test_compiled_codec_executes_only_in_conformance_mode():
    candidate = compile_tau_codec_candidate(**KWARGS)
    result = validate_tau_codec_candidate(candidate)
    assert "ISO.RETURN" in result.emitted
    assert result.receipt["effect_boundary"]["external_effects"] is False
    assert result.program.mode == "READ_ONLY"
    assert result.program.epistemic == "CHYBA"


def test_content_addressed_codec_authoring_is_idempotent(tmp_path):
    first = compile_tau_codec_candidate(authoring_root=tmp_path, **KWARGS)
    second = compile_tau_codec_candidate(authoring_root=tmp_path, **KWARGS)
    assert first.compilation.receipt["receipt_sha256"] == second.compilation.receipt["receipt_sha256"]
    assert len(list((tmp_path / "kaku").glob("*.json"))) == 5
    assert len(list((tmp_path / "radical").glob("*.json"))) == 1
