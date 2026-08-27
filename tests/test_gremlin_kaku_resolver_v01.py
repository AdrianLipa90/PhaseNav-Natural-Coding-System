import pytest

from phasenav_natural_code.gremlin_kaku_resolver_v01 import (
    RESOLUTION_RECEIPT_SCHEMA,
    RESOLVER_SCHEMA,
    GremlinAtomKakuBinding,
    GremlinKakuResolver,
    GremlinKakuResolverError,
    required_relation_mining_atoms,
)
from phasenav_natural_code.mass_v19 import SemanticMassBinding, SemanticMassRegistry
from phasenav_natural_code.model import Vector36
from phasenav_natural_code.realization_v18 import PhaseVector36, RealizationBinding, RealizationRegistry


BASIS = "pncs:t36:gremlin-resolver-test:v1"
CONTENT_A = "pncs:def:sha256:" + "1" * 64
CONTENT_B = "pncs:def:sha256:" + "2" * 64


def _realization(content_id: str, *, seed: float, basis: str = BASIS) -> RealizationBinding:
    return RealizationBinding(
        content_id=content_id,
        phase=PhaseVector36(tuple((seed + i / 100.0) % 6.0 for i in range(36))),
        basis_id=basis,
        derivation_id="PNCS_TEST_REALIZATION_V1",
        source_digest_sha256=("a" if content_id == CONTENT_A else "b") * 64,
        source_locator=f"test:{content_id}",
    )


def _vector(seed: float, basis: str = BASIS) -> Vector36:
    return Vector36(tuple(seed + i / 10.0 for i in range(36)), basis)


def _registries():
    realization_registry = RealizationRegistry()
    mass_registry = SemanticMassRegistry()
    ra = realization_registry.bind(_realization(CONTENT_A, seed=0.1))
    rb = realization_registry.bind(_realization(CONTENT_B, seed=0.2))
    ma = mass_registry.bind(SemanticMassBinding(realization=ra, phase_index=1))
    mb = mass_registry.bind(SemanticMassBinding(realization=rb, phase_index=2))
    return realization_registry, mass_registry, ra, rb, ma, mb


def _binding(atom, content_id, realization, mass, *, vector=None):
    return GremlinAtomKakuBinding(
        atom=atom,
        content_id=content_id,
        realization_binding_id=realization.binding_id,
        mass_binding_id=mass.mass_binding_id,
        vector=vector or _vector(0.5),
        vector_source_ref=f"test:vector:{atom}",
        role="grammar_atom",
    )


def test_resolver_schema_is_versioned():
    assert RESOLVER_SCHEMA == "PNCS_GREMLIN_KAKU_RESOLVER_V0_1"
    assert RESOLUTION_RECEIPT_SCHEMA == "PNCS_GREMLIN_KAKU_RESOLUTION_RECEIPT_V0_1"


def test_explicit_atom_content_binding_resolves_exact_kaku():
    rr, mr, ra, _, ma, _ = _registries()
    resolver = GremlinKakuResolver(
        [_binding("transform", CONTENT_A, ra, ma)],
        realization_registry=rr,
        mass_registry=mr,
    )

    kaku = resolver.resolve("TRANSFORM")
    assert kaku.kaku_id == "K.GREMLIN.TRANSFORM"
    assert kaku.vector.basis_id == BASIS
    assert kaku.semantic_mass == ma.semantic_mass
    assert tuple(kaku.phase) == ra.phase.angles
    assert CONTENT_A in kaku.role


def test_semantic_identity_is_explicit_not_inferred_from_numeric_layers():
    rr, mr, ra, _, ma, _ = _registries()
    binding = _binding("IDENTITY", CONTENT_A, ra, ma)
    resolver = GremlinKakuResolver([binding], realization_registry=rr, mass_registry=mr)
    receipt = resolver.deterministic_receipt()

    assert receipt["semantic_authority"] == "EXPLICIT_ATOM_CONTENT_BINDING"
    assert receipt["nearest_neighbor_resolution"] is False
    assert receipt["vector_to_semantics_inference"] is False
    assert receipt["phase_to_semantics_inference"] is False
    assert receipt["mass_to_semantics_inference"] is False
    assert receipt["bindings"][0]["vector_semantic_authority"] is False


def test_content_mismatch_fails_closed():
    rr, mr, ra, _, ma, _ = _registries()
    resolver = GremlinKakuResolver(
        [_binding("TRANSFORM", CONTENT_B, ra, ma)],
        realization_registry=rr,
        mass_registry=mr,
    )
    with pytest.raises(GremlinKakuResolverError, match="content_id mismatches"):
        resolver.resolve("TRANSFORM")


def test_mass_binding_for_other_realization_fails_closed():
    rr, mr, ra, _, _, mb = _registries()
    resolver = GremlinKakuResolver(
        [_binding("TRANSFORM", CONTENT_A, ra, mb)],
        realization_registry=rr,
        mass_registry=mr,
    )
    with pytest.raises(GremlinKakuResolverError, match="different exact realization"):
        resolver.resolve("TRANSFORM")


def test_vector_basis_mismatch_fails_closed():
    rr, mr, ra, _, ma, _ = _registries()
    resolver = GremlinKakuResolver(
        [_binding("TRANSFORM", CONTENT_A, ra, ma, vector=_vector(0.5, "pncs:other:basis"))],
        realization_registry=rr,
        mass_registry=mr,
    )
    with pytest.raises(GremlinKakuResolverError, match="Vector36 basis mismatches"):
        resolver.resolve("TRANSFORM")


def test_unbound_atom_fails_closed():
    rr, mr, ra, _, ma, _ = _registries()
    resolver = GremlinKakuResolver(
        [_binding("TRANSFORM", CONTENT_A, ra, ma)],
        realization_registry=rr,
        mass_registry=mr,
    )
    with pytest.raises(GremlinKakuResolverError, match="unbound GREMLIN atom"):
        resolver.resolve("IDENTITY")


def test_duplicate_atom_binding_is_rejected():
    rr, mr, ra, _, ma, _ = _registries()
    binding = _binding("TRANSFORM", CONTENT_A, ra, ma)
    with pytest.raises(GremlinKakuResolverError, match="duplicate GREMLIN atom binding"):
        GremlinKakuResolver([binding, binding], realization_registry=rr, mass_registry=mr)


def test_required_relation_mining_atoms_are_exact_union_of_selected_chains():
    ledger = {
        "chains": [
            {"id": "A", "atoms": ["TRANSFORM", "IDENTITY"]},
            {"id": "B", "atoms": ["DERIVE", "IDENTITY"]},
            {"id": "C", "atoms": ["BOUNDARY"]},
        ]
    }
    assert required_relation_mining_atoms(ledger, ("A", "B")) == (
        "DERIVE",
        "IDENTITY",
        "TRANSFORM",
    )
