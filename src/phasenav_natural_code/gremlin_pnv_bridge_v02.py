from __future__ import annotations

"""Unified GREMLIN <-> native PNV bridge.

v0.2 preserves the v0.1 live execution/audit entry points, adds bounded candidate
authoring for KAKU/RADICAL/OPERATOR objects, exposes deterministic relational
isomorphism compilation, adapts relation-mining findings into that compiler, and
resolves relation atoms through explicit semantic bindings plus exact PNCS
realization/mass/vector evidence.
"""

from .gremlin_native_pnv_bridge_v01 import (
    LIVE_BRIDGE_SCHEMA,
    TRIPLE_PULSE_COMPARISON_SCHEMA,
    BelzebubNativeRun,
    NativePNVLiveBridgeError,
    TriplePulseNativeRun,
    compare_triple_pulse_harness,
    execute_belzebub,
    execute_belzebub_live,
    execute_gremlin_triple_pulse,
    execute_gremlin_triple_pulse_live,
)
from .gremlin_pnv_authoring_v02 import (
    AUTHORING_SCHEMA,
    CANDIDATE_SCHEMA,
    RECEIPT_SCHEMA as AUTHORING_RECEIPT_SCHEMA,
    GremlinPNVAuthoringError,
    GremlinPNVAuthoringSession,
    build_kaku_candidate,
    build_operator_candidate,
    build_radical_candidate,
    open_gremlin_pnv_authoring_live,
    persist_candidate,
    render_operator_program,
)
from .gremlin_relational_compiler_v01 import (
    COMPILER_SCHEMA as RELATIONAL_COMPILER_SCHEMA,
    COMPILATION_RECEIPT_SCHEMA as RELATIONAL_COMPILATION_RECEIPT_SCHEMA,
    GremlinRelationalCompilerError,
    RelationalCompilation,
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
    compile_relational_isomorphism,
    compile_relational_isomorphism_live,
    validate_compiled_relational_candidate,
)
from .gremlin_relation_mining_adapter_v01 import (
    ADAPTER_SCHEMA as RELATION_MINING_ADAPTER_SCHEMA,
    GremlinRelationMiningAdapterError,
    RelationMiningAlignment,
    RelationMiningFinding,
    compile_relation_mining_finding,
    relation_mining_finding_to_isomorphism,
)
from .gremlin_kaku_resolver_v01 import (
    RESOLUTION_RECEIPT_SCHEMA as KAKU_RESOLUTION_RECEIPT_SCHEMA,
    RESOLVER_SCHEMA as KAKU_RESOLVER_SCHEMA,
    GremlinAtomKakuBinding,
    GremlinKakuResolver,
    GremlinKakuResolverError,
    compile_relation_mining_with_resolver,
    required_relation_mining_atoms,
    resolve_relation_mining_kaku,
)

BRIDGE_SCHEMA = "PNCS_GREMLIN_NATIVE_PNV_BRIDGE_V0_2"

__all__ = [
    "BRIDGE_SCHEMA",
    "LIVE_BRIDGE_SCHEMA",
    "TRIPLE_PULSE_COMPARISON_SCHEMA",
    "AUTHORING_SCHEMA",
    "CANDIDATE_SCHEMA",
    "AUTHORING_RECEIPT_SCHEMA",
    "RELATIONAL_COMPILER_SCHEMA",
    "RELATIONAL_COMPILATION_RECEIPT_SCHEMA",
    "RELATION_MINING_ADAPTER_SCHEMA",
    "KAKU_RESOLVER_SCHEMA",
    "KAKU_RESOLUTION_RECEIPT_SCHEMA",
    "NativePNVLiveBridgeError",
    "GremlinPNVAuthoringError",
    "GremlinRelationalCompilerError",
    "GremlinRelationMiningAdapterError",
    "GremlinKakuResolverError",
    "TriplePulseNativeRun",
    "BelzebubNativeRun",
    "GremlinPNVAuthoringSession",
    "RelationalNode",
    "RelationalEdge",
    "RelationalIsomorphism",
    "RelationalCompilation",
    "RelationMiningAlignment",
    "RelationMiningFinding",
    "GremlinAtomKakuBinding",
    "GremlinKakuResolver",
    "execute_gremlin_triple_pulse",
    "execute_gremlin_triple_pulse_live",
    "compare_triple_pulse_harness",
    "execute_belzebub",
    "execute_belzebub_live",
    "build_kaku_candidate",
    "build_radical_candidate",
    "build_operator_candidate",
    "persist_candidate",
    "render_operator_program",
    "open_gremlin_pnv_authoring_live",
    "compile_relational_isomorphism",
    "compile_relational_isomorphism_live",
    "validate_compiled_relational_candidate",
    "relation_mining_finding_to_isomorphism",
    "compile_relation_mining_finding",
    "required_relation_mining_atoms",
    "resolve_relation_mining_kaku",
    "compile_relation_mining_with_resolver",
]
