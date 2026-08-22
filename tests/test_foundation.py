import pytest
from phasenav_natural_code import (
    BasisNotCanonizedError, CanonicalPath, Kaku, PNCSIntegrityError,
    RadicalGraph, Relation, Vector36, compile_natural_language,
)

BASIS = "PNCS_36D_BASIS_PENDING_V0_1"


def v36(x=0.0):
    return Vector36(tuple([x] * 36), BASIS)


def test_vector_requires_36():
    with pytest.raises(PNCSIntegrityError):
        Vector36((0.0,) * 35, BASIS)


def test_radical_requires_existing_endpoints():
    g = RadicalGraph("R.TEST", BASIS)
    g.add_kaku(Kaku("K1", v36(), 1.0, "FORWARD", 1.0, "SOURCE"))
    with pytest.raises(PNCSIntegrityError):
        g.add_relation(Relation("E1", "K1", "K2", "REL"))


def test_path_shape():
    p = CanonicalPath("P.TEST", "DEFINITION", ("A", "B"), ("R",), BASIS)
    assert p.level == "DEFINITION"


def test_natural_language_fails_closed_before_basis_canon():
    with pytest.raises(BasisNotCanonizedError):
        compile_natural_language("if gravity is below 0.5 then go to path")
