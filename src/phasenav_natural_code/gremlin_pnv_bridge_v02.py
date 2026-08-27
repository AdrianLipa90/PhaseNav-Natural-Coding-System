from __future__ import annotations

"""Unified GREMLIN <-> native PNV bridge.

v0.2 preserves the v0.1 live execution/audit entry points and adds the bounded
candidate authoring plane for KAKU, RADICAL and native PNV OPERATOR objects.
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

BRIDGE_SCHEMA = "PNCS_GREMLIN_NATIVE_PNV_BRIDGE_V0_2"

__all__ = [
    "BRIDGE_SCHEMA",
    "LIVE_BRIDGE_SCHEMA",
    "TRIPLE_PULSE_COMPARISON_SCHEMA",
    "AUTHORING_SCHEMA",
    "CANDIDATE_SCHEMA",
    "AUTHORING_RECEIPT_SCHEMA",
    "NativePNVLiveBridgeError",
    "GremlinPNVAuthoringError",
    "TriplePulseNativeRun",
    "BelzebubNativeRun",
    "GremlinPNVAuthoringSession",
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
]
