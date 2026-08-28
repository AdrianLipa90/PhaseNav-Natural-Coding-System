from __future__ import annotations

"""GREMLIN <-> native PNV bridge v0.3 with stable live-generation authoring."""

from pathlib import Path

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
from .gremlin_relational_compiler_v01 import (
    GremlinRelationalCompilerError,
    RelationalCompilation,
    RelationalIsomorphism,
    compile_relational_isomorphism as _compile_relational_isomorphism_v01,
)

BRIDGE_SCHEMA_V03 = "PNCS_GREMLIN_NATIVE_PNV_BRIDGE_V0_3"


def compile_relational_isomorphism_live(
    spec: RelationalIsomorphism,
    *,
    session: GremlinPNVAuthoringSessionV03 | None = None,
    pnv_text: str | None = None,
    relation_opcode_overrides=None,
) -> RelationalCompilation:
    """Compile a relational candidate with pre/post live-generation revalidation.

    Candidate objects may be written during compilation, but the compilation
    receipt is persisted only after the same admitted runtime generation is
    verified again.  A runtime restart therefore fails closed; any objects
    already written remain CANDIDATE_ONLY content-addressed evidence and do not
    gain runtime or canon authority.
    """
    if session is None:
        if not pnv_text or not pnv_text.strip():
            raise GremlinRelationalCompilerError(
                "v0.3 live compilation requires exact triple-pulse PNV source or v0.3 authoring session"
            )
        session = open_gremlin_pnv_authoring_live(pnv_text)
    if not isinstance(session, GremlinPNVAuthoringSessionV03):
        raise GremlinRelationalCompilerError(
            "v0.3 live compilation requires a generation-revalidating authoring session"
        )

    admitted_generation = session.generation_binding
    identity = session.identity
    authority = session.authority
    authoring_root = session.authoring_root

    compilation = _compile_relational_isomorphism_v01(
        spec,
        generation_binding=admitted_generation,
        identity=identity,
        authority=authority,
        relation_opcode_overrides=relation_opcode_overrides,
        authoring_root=authoring_root,
    )

    # Property access performs a fresh live check and rejects a changed runtime generation.
    _ = session.identity
    if session.generation_binding != admitted_generation:
        raise GremlinRelationalCompilerError(
            "GREMLIN runtime generation changed during relational compilation"
        )

    receipt_dir = Path(authoring_root) / "compilation"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    target = receipt_dir / f"{compilation.receipt['receipt_sha256']}.json"
    import json
    raw = (
        json.dumps(
            dict(compilation.receipt),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    try:
        with target.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        if target.read_bytes() != raw:
            raise GremlinRelationalCompilerError(
                "content-addressed compilation receipt collision"
            )
    return compilation
