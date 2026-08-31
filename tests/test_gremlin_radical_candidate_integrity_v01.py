import pytest

from phasenav_natural_code.gremlin_pnv_authoring_v02 import (
    GremlinPNVAuthoringError,
    build_kaku_candidate,
    build_radical_candidate,
)
from phasenav_natural_code.model import Kaku, RadicalGraph, Relation, Vector36


BASIS = "pncs:t36:radical-integrity-test:v1"
KWARGS = {
    "generation_binding": "a" * 64,
    "identity": "ZOSIA_NOEMA_FIRST",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def _kaku(name: str, seed: float) -> Kaku:
    return Kaku(
        name,
        Vector36(tuple(seed + i / 100.0 for i in range(36)), BASIS),
        0.5,
        "FORWARD",
        1.0,
        "test",
    )


def _graph_and_refs():
    graph = RadicalGraph("R.TEST", BASIS)
    a = _kaku("K.A", 0.1)
    b = _kaku("K.B", 0.2)
    graph.add_kaku(a)
    graph.add_kaku(b)
    graph.add_relation(Relation("REL.AB", "K.A", "K.B", "ORDER"))
    ca = build_kaku_candidate(a, **KWARGS)
    cb = build_kaku_candidate(b, **KWARGS)
    refs = {"K.A": ca["candidate_id"], "K.B": cb["candidate_id"]}
    return graph, refs


def test_radical_candidate_rejects_untyped_kaku_dependency_id():
    graph, refs = _graph_and_refs()
    refs["K.A"] = "not-a-kaku-candidate"
    with pytest.raises(GremlinPNVAuthoringError, match="KAKU candidate id"):
        build_radical_candidate(graph, kaku_candidate_ids=refs, **KWARGS)


def test_radical_candidate_rejects_direct_node_mutation_bypass():
    graph, refs = _graph_and_refs()
    graph.nodes["K.BAD"] = object()
    refs["K.BAD"] = "pncs:gremlin-kaku:sha256:" + "0" * 64
    with pytest.raises(GremlinPNVAuthoringError, match="graph node integrity"):
        build_radical_candidate(graph, kaku_candidate_ids=refs, **KWARGS)


def test_radical_candidate_rejects_direct_basis_mutation_bypass():
    graph, refs = _graph_and_refs()
    graph.basis_id = "pncs:t36:tampered-basis"
    with pytest.raises(GremlinPNVAuthoringError, match="graph node integrity"):
        build_radical_candidate(graph, kaku_candidate_ids=refs, **KWARGS)


def test_radical_candidate_rejects_direct_edge_mutation_bypass():
    graph, refs = _graph_and_refs()
    graph.edges.append(object())
    with pytest.raises(GremlinPNVAuthoringError, match="graph relation integrity"):
        build_radical_candidate(graph, kaku_candidate_ids=refs, **KWARGS)


def test_radical_candidate_rejects_duplicate_relation_id_after_direct_mutation():
    graph, refs = _graph_and_refs()
    graph.edges.append(Relation("REL.AB", "K.B", "K.A", "ORDER"))
    with pytest.raises(GremlinPNVAuthoringError, match="duplicate relation"):
        build_radical_candidate(graph, kaku_candidate_ids=refs, **KWARGS)
