import math

import pytest

from phasenav_natural_code.model import (
    Kaku,
    PNCSIntegrityError,
    RadicalGraph,
    Relation,
    Vector36,
)


BASIS = "pncs:t36:model-integrity-test:v1"


def _values(seed=0.0):
    return tuple(seed + i / 100.0 for i in range(36))


def _kaku(name="K.A"):
    return Kaku(
        name,
        Vector36(_values(), BASIS),
        0.5,
        "FORWARD",
        1.0,
        "test",
        _values(0.1),
    )


def test_vector36_normalizes_finite_real_coordinates_and_basis_text():
    vector = Vector36(tuple(range(36)), "  basis:test  ")
    assert vector.basis_id == "basis:test"
    assert all(isinstance(value, float) for value in vector.values)
    assert vector.values[1] == 1.0


@pytest.mark.parametrize("bad", [True, "1.0", object(), math.nan, math.inf])
def test_vector36_rejects_non_real_or_nonfinite_coordinates(bad):
    values = list(_values())
    values[7] = bad
    with pytest.raises(PNCSIntegrityError, match="36D coordinate"):
        Vector36(tuple(values), BASIS)


def test_vector36_rejects_non_string_basis_id():
    with pytest.raises(PNCSIntegrityError, match="basis_id"):
        Vector36(_values(), 123)


def test_kaku_normalizes_scalar_and_text_fields():
    kaku = Kaku(
        " K.A ",
        Vector36(_values(), BASIS),
        1,
        " FORWARD ",
        -1,
        " role ",
        _values(0.2),
    )
    assert kaku.kaku_id == "K.A"
    assert kaku.semantic_mass == 1.0
    assert isinstance(kaku.semantic_mass, float)
    assert kaku.direction == "FORWARD"
    assert kaku.polarity == -1.0
    assert kaku.role == "role"


@pytest.mark.parametrize("field,value", [("semantic_mass", "0.5"), ("polarity", False)])
def test_kaku_rejects_implicitly_coercible_non_reals(field, value):
    kwargs = {
        "kaku_id": "K.A",
        "vector": Vector36(_values(), BASIS),
        "semantic_mass": 0.5,
        "direction": "FORWARD",
        "polarity": 1.0,
        "role": "test",
    }
    kwargs[field] = value
    with pytest.raises(PNCSIntegrityError, match=field):
        Kaku(**kwargs)


def test_radical_graph_validates_own_identity_and_node_types():
    with pytest.raises(PNCSIntegrityError, match="radical_id"):
        RadicalGraph(" ", BASIS)
    with pytest.raises(PNCSIntegrityError, match="basis_id"):
        RadicalGraph("R.A", 7)
    with pytest.raises(PNCSIntegrityError, match="string -> Kaku"):
        RadicalGraph("R.A", BASIS, nodes={"K.A": object()})


def test_radical_graph_rejects_duplicate_relation_ids():
    graph = RadicalGraph("R.A", BASIS)
    graph.add_kaku(_kaku("K.A"))
    graph.add_kaku(_kaku("K.B"))
    graph.add_relation(Relation("REL.AB", "K.A", "K.B", "ORDER"))
    with pytest.raises(PNCSIntegrityError, match="duplicate relation"):
        graph.add_relation(Relation("REL.AB", "K.B", "K.A", "ORDER"))


def test_radical_graph_snapshots_initial_node_and_edge_containers():
    a = _kaku("K.A")
    b = _kaku("K.B")
    source_nodes = {"K.A": a, "K.B": b}
    source_edges = [Relation("REL.AB", "K.A", "K.B", "ORDER")]
    graph = RadicalGraph("R.A", BASIS, nodes=source_nodes, edges=source_edges)
    source_nodes.clear()
    source_edges.clear()
    assert set(graph.nodes) == {"K.A", "K.B"}
    assert [edge.relation_id for edge in graph.edges] == ["REL.AB"]
