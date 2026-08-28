from phasenav_natural_code.gremlin_pnv_bridge_v02 import (
    HOLONOMY_AUDIT_RECEIPT_SCHEMA,
    HOLONOMY_COMPILATION_RECEIPT_SCHEMA,
    HOLONOMY_CONTRACT,
    HolonomyInvariant,
    InformationHolonomyAudit,
    InformationHolonomyLoop,
    LawFrameNode,
    LawTransport,
    PNVInformationHolonomyError,
    audit_information_holonomy,
    compile_information_holonomy_loop,
    compile_information_holonomy_loop_live,
    exact_state_metric,
    numeric_linf_metric,
    persist_information_holonomy_audit,
    persist_information_holonomy_audit_live,
)


def test_unified_bridge_exports_information_holonomy_contract():
    assert HOLONOMY_CONTRACT == "PNCS_PNV_INFORMATION_HOLONOMY_V0_1"
    assert HOLONOMY_COMPILATION_RECEIPT_SCHEMA == "PNCS_PNV_INFORMATION_HOLONOMY_COMPILATION_RECEIPT_V0_1"
    assert HOLONOMY_AUDIT_RECEIPT_SCHEMA == "PNCS_PNV_INFORMATION_HOLONOMY_AUDIT_RECEIPT_V0_1"
    assert LawFrameNode is not None
    assert LawTransport is not None
    assert HolonomyInvariant is not None
    assert InformationHolonomyLoop is not None
    assert InformationHolonomyAudit is not None
    assert PNVInformationHolonomyError is not None
    assert callable(compile_information_holonomy_loop)
    assert callable(compile_information_holonomy_loop_live)
    assert callable(audit_information_holonomy)
    assert callable(persist_information_holonomy_audit)
    assert callable(persist_information_holonomy_audit_live)
    assert callable(exact_state_metric)
    assert callable(numeric_linf_metric)
