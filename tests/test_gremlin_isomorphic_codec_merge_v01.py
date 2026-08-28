from dataclasses import replace

import pytest

from phasenav_natural_code.gremlin_isomorphic_codec_merge_v01 import (
    GremlinIsomorphicCodecMergeError,
    merge_relational_isomorphisms,
)
from phasenav_natural_code.gremlin_relational_compiler_v01 import (
    RelationalIsomorphism,
    compile_relational_isomorphism,
)
from phasenav_natural_code.gremlin_tau_codec_v01 import tau_codec_isomorphism

KWARGS = {
    "generation_binding": "b" * 64,
    "identity": "ZOSIA_NOEMA_FIRST",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def _fragments():
    full = tau_codec_isomorphism()
    by_node = {node.kaku.kaku_id: node for node in full.nodes}
    by_edge = {edge.relation_id: edge for edge in full.edges}
    left = RelationalIsomorphism(
        "ISO.PNLF.LEFT",
        full.invariant_id,
        full.invariant_description,
        (
            by_node["K.TAU.FRAME"],
            by_node["K.T36.WITNESS"],
            by_node["K.LIMINAL.SEGMENT"],
        ),
        (
            by_edge["REL.TAU.T36"],
            by_edge["REL.TAU.LIMINAL"],
        ),
        ("fragment:left",),
    )
    right = RelationalIsomorphism(
        "ISO.PNLF.RIGHT",
        full.invariant_id,
        full.invariant_description,
        (
            by_node["K.LIMINAL.SEGMENT"],
            by_node["K.PNLF.FILE"],
            by_node["K.PNH5.VIEW"],
        ),
        (
            by_edge["REL.LIMINAL.FILE"],
            by_edge["REL.FILE.PNH5"],
        ),
        ("fragment:right",),
    )
    return full, left, right


def test_partial_codec_isomorphisms_merge_to_full_union_graph():
    full, left, right = _fragments()
    merged = merge_relational_isomorphisms((left, right), merged_isomorphism_id="ISO.PNLF.MERGED")
    assert {n.kaku.kaku_id for n in merged.nodes} == {n.kaku.kaku_id for n in full.nodes}
    assert {e.relation_id for e in merged.edges} == {e.relation_id for e in full.edges}
    assert set(merged.evidence_refs) >= {
        "fragment:left",
        "fragment:right",
        "isomorphism-fragment:ISO.PNLF.LEFT",
        "isomorphism-fragment:ISO.PNLF.RIGHT",
    }


def test_merged_isomorphism_compiles_to_one_radical():
    _, left, right = _fragments()
    merged = merge_relational_isomorphisms((left, right))
    compiled = compile_relational_isomorphism(merged, **KWARGS)
    assert len(compiled.kaku_candidates) == 5
    assert compiled.radical_candidate["kind"] == "RADICAL"
    assert len(compiled.radical_candidate["dependency_ids"]) == 5
    assert compiled.operator_candidates[-1]["content"]["name"] == "ISO.RETURN"


def test_conflicting_duplicate_kaku_fails_closed():
    full, left, right = _fragments()
    shared = next(node for node in right.nodes if node.kaku.kaku_id == "K.LIMINAL.SEGMENT")
    conflict = replace(shared, kaku=replace(shared.kaku, role="conflicting_role"))
    altered = RelationalIsomorphism(
        "ISO.PNLF.CONFLICT",
        full.invariant_id,
        full.invariant_description,
        (conflict, next(node for node in right.nodes if node.kaku.kaku_id == "K.PNLF.FILE")),
        (),
    )
    with pytest.raises(GremlinIsomorphicCodecMergeError, match="conflicting KAKU node"):
        merge_relational_isomorphisms((left, altered))


def test_different_invariant_fails_closed():
    full, left, right = _fragments()
    altered = RelationalIsomorphism(
        right.isomorphism_id,
        "INV.DIFFERENT",
        full.invariant_description,
        right.nodes,
        right.edges,
        right.evidence_refs,
    )
    with pytest.raises(GremlinIsomorphicCodecMergeError, match="share one invariant_id"):
        merge_relational_isomorphisms((left, altered))


def test_single_fragment_is_not_called_a_merge():
    _, left, _ = _fragments()
    with pytest.raises(GremlinIsomorphicCodecMergeError, match="at least two"):
        merge_relational_isomorphisms((left,))
