from phasenav_natural_code.gremlin_pnv_bridge_v02 import (
    CANDIDATE_INVERSE_LINEAGE_RECEIPT_SCHEMA,
    CANDIDATE_INVERSE_LINEAGE_SCHEMA,
    GremlinCandidateInverseLineage,
    GremlinInverseLineageError,
    persist_gremlin_candidate_inverse_lineage,
    persist_gremlin_candidate_inverse_lineage_live,
    resolve_gremlin_candidate_inverse_lineage,
)


def test_unified_bridge_exports_candidate_inverse_lineage_contract():
    assert CANDIDATE_INVERSE_LINEAGE_SCHEMA == "PNCS_GREMLIN_CANDIDATE_INVERSE_LINEAGE_V0_1"
    assert CANDIDATE_INVERSE_LINEAGE_RECEIPT_SCHEMA == "PNCS_GREMLIN_CANDIDATE_INVERSE_LINEAGE_RECEIPT_V0_1"
    assert GremlinCandidateInverseLineage is not None
    assert GremlinInverseLineageError is not None
    assert callable(resolve_gremlin_candidate_inverse_lineage)
    assert callable(persist_gremlin_candidate_inverse_lineage)
    assert callable(persist_gremlin_candidate_inverse_lineage_live)
