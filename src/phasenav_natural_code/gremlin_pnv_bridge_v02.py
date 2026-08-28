from __future__ import annotations

"""Unified GREMLIN <-> native PNV bridge.

v0.2 preserves the v0.1 live execution/audit entry points, adds bounded candidate
authoring for KAKU/RADICAL/OPERATOR objects, exposes deterministic relational
isomorphism compilation, adapts relation-mining findings into that compiler,
resolves relation atoms through explicit semantic bindings plus exact PNCS
realization/mass/vector evidence, exposes candidate inverse lineage, and provides
an executable physical-law frame with information-holonomy receipts and source-law
round-trip templates including Euler-closed, collective Noether, Noether↔RFC
conserved-current, scalar-field↔rotor collective-reduction, and gauge-covariant
field↔rotor pullback gates.
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
from .gremlin_inverse_lineage_v01 import (
    LINEAGE_RECEIPT_SCHEMA as CANDIDATE_INVERSE_LINEAGE_RECEIPT_SCHEMA,
    LINEAGE_SCHEMA as CANDIDATE_INVERSE_LINEAGE_SCHEMA,
    GremlinCandidateInverseLineage,
    GremlinInverseLineageError,
    persist_gremlin_candidate_inverse_lineage,
    resolve_gremlin_candidate_inverse_lineage,
)
from .gremlin_pnv_holonomy_v01 import (
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
    exact_state_metric,
    numeric_linf_metric,
    persist_information_holonomy_audit,
)
from .pnv_source_holonomy_v01 import (
    C_LIGHT_EXACT,
    SOURCE_HOLONOMY_CONTRACT,
    PNVSourceHolonomyError,
    build_carrier_normalization_loop,
    build_epsilon_source_loop,
    build_euler_phase_intention_loop,
    build_q0_occupation_loop,
    carrier_normalization_invariants,
    carrier_normalization_transforms,
    epsilon_source_invariants,
    epsilon_source_transforms,
    euler_phase_intention_invariants,
    euler_phase_intention_transforms,
    make_current_density_state,
    make_euler_phase_intention_state,
    make_extensive_carrier_state,
    q0_occupation_invariants,
    q0_occupation_transforms,
)
from .pnv_noether_collective_holonomy_v01 import (
    NOETHER_COLLECTIVE_CONTRACT,
    PNVNoetherCollectiveError,
    build_noether_collective_loop,
    collective_noether_binding_defect,
    make_noether_collective_state,
    noether_collective_invariants,
    noether_collective_transforms,
)
from .pnv_noether_rfc_current_holonomy_v01 import (
    NOETHER_RFC_CURRENT_CONTRACT,
    NOETHER_RFC_CURRENT_LOOP_ID,
    PNVNoetherRFCCurrentError,
    build_noether_rfc_current_loop,
    make_noether_rfc_current_state,
    noether_rfc_current_invariants,
    noether_rfc_current_transforms,
)
from .pnv_scalar_field_rotor_reduction_v01 import (
    SCALAR_FIELD_ROTOR_CONTRACT,
    SCALAR_FIELD_ROTOR_LOOP_ID,
    PNVScalarFieldRotorReductionError,
    build_scalar_field_rotor_reduction_loop,
    make_scalar_field_rotor_state,
    scalar_field_rotor_reduction_defects,
    scalar_field_rotor_reduction_invariants,
    scalar_field_rotor_reduction_transforms,
)
from .pnv_gauge_covariant_phase_pullback_v01 import (
    GAUGE_COVARIANT_PULLBACK_CONTRACT,
    GAUGE_COVARIANT_PULLBACK_LOOP_ID,
    PNVGaugeCovariantPhasePullbackError,
    build_gauge_covariant_phase_pullback_loop,
    gauge_covariant_phase_pullback_defects,
    gauge_covariant_phase_pullback_invariants,
    gauge_covariant_phase_pullback_transforms,
    make_gauge_covariant_phase_pullback_state,
)

BRIDGE_SCHEMA = "PNCS_GREMLIN_NATIVE_PNV_BRIDGE_V0_2"


def persist_gremlin_candidate_inverse_lineage_live(
    lineage: GremlinCandidateInverseLineage,
    *,
    session: GremlinPNVAuthoringSession | None = None,
) -> str:
    live = session or open_gremlin_pnv_authoring_live()
    return persist_gremlin_candidate_inverse_lineage(lineage, authoring_root=live.authoring_root)


def compile_information_holonomy_loop_live(
    loop: InformationHolonomyLoop,
    *,
    session: GremlinPNVAuthoringSession | None = None,
) -> RelationalCompilation:
    live = session or open_gremlin_pnv_authoring_live()
    return compile_information_holonomy_loop(
        loop,
        generation_binding=live.generation_binding,
        identity=live.identity,
        authority=live.authority,
        authoring_root=live.authoring_root,
    )


def persist_information_holonomy_audit_live(
    audit: InformationHolonomyAudit,
    *,
    session: GremlinPNVAuthoringSession | None = None,
) -> str:
    live = session or open_gremlin_pnv_authoring_live()
    return persist_information_holonomy_audit(audit, authoring_root=live.authoring_root)


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
    "CANDIDATE_INVERSE_LINEAGE_SCHEMA",
    "CANDIDATE_INVERSE_LINEAGE_RECEIPT_SCHEMA",
    "HOLONOMY_CONTRACT",
    "HOLONOMY_COMPILATION_RECEIPT_SCHEMA",
    "HOLONOMY_AUDIT_RECEIPT_SCHEMA",
    "SOURCE_HOLONOMY_CONTRACT",
    "NOETHER_COLLECTIVE_CONTRACT",
    "NOETHER_RFC_CURRENT_CONTRACT",
    "NOETHER_RFC_CURRENT_LOOP_ID",
    "SCALAR_FIELD_ROTOR_CONTRACT",
    "SCALAR_FIELD_ROTOR_LOOP_ID",
    "GAUGE_COVARIANT_PULLBACK_CONTRACT",
    "GAUGE_COVARIANT_PULLBACK_LOOP_ID",
    "C_LIGHT_EXACT",
    "NativePNVLiveBridgeError",
    "GremlinPNVAuthoringError",
    "GremlinRelationalCompilerError",
    "GremlinRelationMiningAdapterError",
    "GremlinKakuResolverError",
    "GremlinInverseLineageError",
    "PNVInformationHolonomyError",
    "PNVSourceHolonomyError",
    "PNVNoetherCollectiveError",
    "PNVNoetherRFCCurrentError",
    "PNVScalarFieldRotorReductionError",
    "PNVGaugeCovariantPhasePullbackError",
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
    "GremlinCandidateInverseLineage",
    "LawFrameNode",
    "LawTransport",
    "HolonomyInvariant",
    "InformationHolonomyLoop",
    "InformationHolonomyAudit",
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
    "resolve_gremlin_candidate_inverse_lineage",
    "persist_gremlin_candidate_inverse_lineage",
    "persist_gremlin_candidate_inverse_lineage_live",
    "compile_information_holonomy_loop",
    "compile_information_holonomy_loop_live",
    "audit_information_holonomy",
    "persist_information_holonomy_audit",
    "persist_information_holonomy_audit_live",
    "exact_state_metric",
    "numeric_linf_metric",
    "make_extensive_carrier_state",
    "build_carrier_normalization_loop",
    "carrier_normalization_transforms",
    "carrier_normalization_invariants",
    "build_q0_occupation_loop",
    "q0_occupation_transforms",
    "q0_occupation_invariants",
    "make_current_density_state",
    "build_epsilon_source_loop",
    "epsilon_source_transforms",
    "epsilon_source_invariants",
    "make_euler_phase_intention_state",
    "build_euler_phase_intention_loop",
    "euler_phase_intention_transforms",
    "euler_phase_intention_invariants",
    "make_noether_collective_state",
    "build_noether_collective_loop",
    "noether_collective_transforms",
    "noether_collective_invariants",
    "collective_noether_binding_defect",
    "make_noether_rfc_current_state",
    "build_noether_rfc_current_loop",
    "noether_rfc_current_transforms",
    "noether_rfc_current_invariants",
    "make_scalar_field_rotor_state",
    "build_scalar_field_rotor_reduction_loop",
    "scalar_field_rotor_reduction_transforms",
    "scalar_field_rotor_reduction_invariants",
    "scalar_field_rotor_reduction_defects",
    "make_gauge_covariant_phase_pullback_state",
    "build_gauge_covariant_phase_pullback_loop",
    "gauge_covariant_phase_pullback_transforms",
    "gauge_covariant_phase_pullback_invariants",
    "gauge_covariant_phase_pullback_defects",
]
