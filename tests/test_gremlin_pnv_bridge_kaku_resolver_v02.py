from phasenav_natural_code.gremlin_pnv_bridge_v02 import (
    KAKU_RESOLUTION_RECEIPT_SCHEMA,
    KAKU_RESOLVER_SCHEMA,
    GremlinAtomKakuBinding,
    GremlinKakuResolver,
    compile_relation_mining_with_resolver,
    required_relation_mining_atoms,
    resolve_relation_mining_kaku,
)


def test_unified_bridge_exports_kaku_resolver_contract():
    assert KAKU_RESOLVER_SCHEMA == "PNCS_GREMLIN_KAKU_RESOLVER_V0_1"
    assert KAKU_RESOLUTION_RECEIPT_SCHEMA == "PNCS_GREMLIN_KAKU_RESOLUTION_RECEIPT_V0_1"
    assert GremlinAtomKakuBinding.__name__ == "GremlinAtomKakuBinding"
    assert GremlinKakuResolver.__name__ == "GremlinKakuResolver"
    assert callable(required_relation_mining_atoms)
    assert callable(resolve_relation_mining_kaku)
    assert callable(compile_relation_mining_with_resolver)
