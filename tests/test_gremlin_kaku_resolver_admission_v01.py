import pytest

from phasenav_natural_code.gremlin_kaku_resolver_v01 import (
    EXPECTED_LEDGER_SCHEMA,
    GremlinAtomKakuBinding,
    GremlinKakuResolverError,
    required_relation_mining_atoms,
)
from phasenav_natural_code.model import Vector36


BASIS = "pncs:t36:kaku-resolver-admission-test:v1"


def _binding(polarity):
    return GremlinAtomKakuBinding(
        atom="IDENTITY",
        content_id="pncs:def:sha256:" + "1" * 64,
        realization_binding_id="pncs:realization:sha256:" + "2" * 64,
        mass_binding_id="pncs:semantic-mass:sha256:" + "3" * 64,
        vector=Vector36(tuple(i / 100.0 for i in range(36)), BASIS),
        vector_source_ref="test:vector",
        polarity=polarity,
    )


@pytest.mark.parametrize("bad", [True, "1.0", object()])
def test_binding_polarity_rejects_implicitly_coercible_non_reals(bad):
    with pytest.raises(GremlinKakuResolverError, match="polarity"):
        _binding(bad)


def test_required_atoms_reject_non_string_atoms_instead_of_stringifying_them():
    ledger = {
        "schema": EXPECTED_LEDGER_SCHEMA,
        "chains": [{"id": "A", "atoms": [1]}],
    }
    with pytest.raises(GremlinKakuResolverError, match="atom"):
        required_relation_mining_atoms(ledger, ("A",))


def test_required_atoms_normalize_chain_ids_and_detect_collisions():
    ledger = {
        "schema": EXPECTED_LEDGER_SCHEMA,
        "chains": [
            {"id": " A ", "atoms": ["IDENTITY"]},
            {"id": "A", "atoms": ["TRANSFORM"]},
        ],
    }
    with pytest.raises(GremlinKakuResolverError, match="duplicate relation-mining chain id"):
        required_relation_mining_atoms(ledger, ("A",))


def test_required_atoms_trim_and_uppercase_exact_string_atoms():
    ledger = {
        "schema": EXPECTED_LEDGER_SCHEMA,
        "chains": [{"id": " A ", "atoms": [" identity ", "Transform"]}],
    }
    assert required_relation_mining_atoms(ledger, (" A ",)) == (
        "IDENTITY",
        "TRANSFORM",
    )


def test_chain_id_selection_rejects_string_as_iterable_container():
    ledger = {
        "schema": EXPECTED_LEDGER_SCHEMA,
        "chains": [{"id": "A", "atoms": ["IDENTITY"]}],
    }
    with pytest.raises(GremlinKakuResolverError, match="chain_ids"):
        required_relation_mining_atoms(ledger, "A")
