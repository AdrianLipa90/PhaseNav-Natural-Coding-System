from __future__ import annotations

"""GREMLIN <-> native PNV bridge v0.3 with stable live-generation authoring."""

from .gremlin_pnv_bridge_v02 import *  # noqa: F401,F403
from .gremlin_live_hydration_v03 import (
    GENERATION_BASIS_SCHEMA,
    LIVE_WITNESS_SCHEMA,
    GremlinLiveHydration,
    GremlinLiveHydrationError,
    build_generation_basis,
    generation_binding_from_basis,
    hydrate_gremlin_pnv_live,
    open_verified_gremlin_pnv_authoring_live,
    validate_witness_against_basis,
)
from .gremlin_pnv_authoring_v03 import (
    AUTHORING_SCHEMA as AUTHORING_SCHEMA_V03,
    GremlinPNVAuthoringSessionV03,
    hydrate_and_open_gremlin_pnv_authoring_live,
    open_gremlin_pnv_authoring_live,
)

BRIDGE_SCHEMA_V03 = "PNCS_GREMLIN_NATIVE_PNV_BRIDGE_V0_3"
