from phasenav_natural_code.gremlin_inverse_lineage_v01 import resolve_gremlin_candidate_inverse_lineage
from phasenav_natural_code.gremlin_kaku_resolver_v01 import (
    GremlinAtomKakuBinding,
    GremlinKakuResolver,
    compile_relation_mining_with_resolver,
)
from phasenav_natural_code.gremlin_relation_mining_adapter_v01 import (
    RelationMiningAlignment,
    RelationMiningFinding,
)
from phasenav_natural_code.gremlin_relational_compiler_v01 import validate_compiled_relational_candidate
from phasenav_natural_code.mass_v19 import SemanticMassBinding, SemanticMassRegistry
from phasenav_natural_code.model import Vector36
from phasenav_natural_code.realization_v18 import PhaseVector36, RealizationBinding, RealizationRegistry


BASIS = "pncs:t36:gremlin-resolver-pipeline:v1"
CONTENT = "pncs:def:sha256:" + "3" * 64
LEDGER = {
    "schema": "PNCS_RELATION_MINING_LEDGER_V0_3",
    "chains": [
        {"id": "DOMAIN_A.IDENTITY", "source": "DOMAIN_A", "status": "EXACT_A", "atoms": ["IDENTITY"]},
        {"id": "DOMAIN_B.IDENTITY", "source": "DOMAIN_B", "status": "EXACT_B", "atoms": ["IDENTITY"]},
    ],
}
FINDING = RelationMiningFinding(
    finding_id="CROSS_DOMAIN.IDENTITY",
    invariant_id="INV.IDENTITY.ROLE",
    invariant_description="two source domains expose the same admitted identity role",
    chain_ids=("DOMAIN_A.IDENTITY", "DOMAIN_B.IDENTITY"),
    alignments=(RelationMiningAlignment("DOMAIN_A.IDENTITY", 0, "DOMAIN_B.IDENTITY", 0),),
    evidence_refs=("test:resolver-pipeline",),
)


def _resolver() -> GremlinKakuResolver:
    realization = RealizationBinding(
        content_id=CONTENT,
        phase=PhaseVector36(tuple(0.1 + i / 100.0 for i in range(36))),
        basis_id=BASIS,
        derivation_id="PNCS_TEST_RESOLVER_PIPELINE_V1",
        source_digest_sha256="c" * 64,
        source_locator="test:resolver-pipeline:phase",
    )
    rr = RealizationRegistry()
    rr.bind(realization)
    mass = SemanticMassBinding(realization=realization, phase_index=1)
    mr = SemanticMassRegistry()
    mr.bind(mass)
    binding = GremlinAtomKakuBinding(
        atom="IDENTITY",
        content_id=CONTENT,
        realization_binding_id=realization.binding_id,
        mass_binding_id=mass.mass_binding_id,
        vector=Vector36(tuple(1.0 + i / 10.0 for i in range(36)), BASIS),
        vector_source_ref="test:resolver-pipeline:vector",
        role="grammar_atom",
    )
    return GremlinKakuResolver([binding], realization_registry=rr, mass_registry=mr)


def test_resolver_adapter_compiler_pipeline_executes_purely_and_round_trips_lineage():
    compiled = compile_relation_mining_with_resolver(
        LEDGER,
        FINDING,
        resolver=_resolver(),
        generation_binding="d" * 64,
        identity="ZOSIA_NOEMA_FIRST",
        authority="USER_EXPLICIT_AUTHORING",
    )

    assert compiled.spec.invariant_id == "INV.IDENTITY.ROLE"
    assert len(compiled.kaku_candidates) == 2
    assert any(row["relation_type"] == "ISOMORPHIC_TO" for row in compiled.receipt["relation_plan"])

    execution = validate_compiled_relational_candidate(compiled)
    assert execution.receipt["effect_boundary"]["external_effects"] is False
    assert execution.receipt["unknown_semantics_fail_closed"] is True
    assert "ISO.RETURN" in execution.emitted

    lineage = resolve_gremlin_candidate_inverse_lineage(compiled, execution)
    assert lineage.operator_rows[0]["name"] == "ISO.RETURN"
    assert lineage.payload["explicit_content_ids"] == [CONTENT]
    assert lineage.payload["v22_join_state"] == "CONTENT_ID_AVAILABLE"
    assert {row["node_id"] for row in lineage.kaku_rows} == {
        "RM.DOMAIN_A_IDENTITY.000.IDENTITY",
        "RM.DOMAIN_B_IDENTITY.000.IDENTITY",
    }
