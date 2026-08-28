from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .execution_v20_model import DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT
from .gremlin_live_hydration_v03 import (
    GremlinLiveHydration,
    hydrate_gremlin_pnv_live,
    open_verified_gremlin_pnv_authoring_live,
)
from .gremlin_pnv_authoring_v02 import (
    CANDIDATE_SCHEMA,
    RECEIPT_SCHEMA,
    GremlinPNVAuthoringError,
    GremlinPNVAuthoringSession,
    build_kaku_candidate,
    build_operator_candidate,
    build_radical_candidate,
    persist_candidate,
    render_operator_program,
)
from .model import Kaku, RadicalGraph

AUTHORING_SCHEMA = "PNCS_GREMLIN_PNV_AUTHORING_V0_3"


@dataclass(frozen=True)
class GremlinPNVAuthoringSessionV03:
    """Candidate-only authoring session that revalidates the live generation per write."""

    pnv_text: str
    generation_binding: str
    surface_root: Path = DEFAULT_SURFACE_ROOT
    socket_path: Path = DEFAULT_SOCKET
    max_heartbeat_age_s: float = 2.0

    def _current(self) -> GremlinPNVAuthoringSession:
        current = open_verified_gremlin_pnv_authoring_live(
            self.pnv_text,
            surface_root=self.surface_root,
            socket_path=self.socket_path,
            max_heartbeat_age_s=self.max_heartbeat_age_s,
        )
        if current.generation_binding != self.generation_binding:
            raise GremlinPNVAuthoringError(
                "GREMLIN authoring generation changed after session admission"
            )
        return current

    @property
    def identity(self) -> str:
        return self._current().identity

    @property
    def authority(self) -> str:
        return self._current().authority

    @property
    def authoring_root(self) -> Path:
        return self.surface_root / "gremlin/candidates/pncs"

    def write_kaku(
        self,
        kaku: Kaku,
        *,
        evidence_refs: Sequence[str] = (),
    ):
        return self._current().write_kaku(kaku, evidence_refs=evidence_refs)

    def write_radical(
        self,
        radical: RadicalGraph,
        *,
        evidence_refs: Sequence[str] = (),
    ):
        return self._current().write_radical(radical, evidence_refs=evidence_refs)

    def write_operator(
        self,
        name: str,
        opcode: str,
        args: Sequence[str],
        *,
        radical_candidate_id: str | None = None,
        evidence_refs: Sequence[str] = (),
    ):
        return self._current().write_operator(
            name,
            opcode,
            args,
            radical_candidate_id=radical_candidate_id,
            evidence_refs=evidence_refs,
        )


def open_gremlin_pnv_authoring_live(
    pnv_text: str,
    *,
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
) -> GremlinPNVAuthoringSessionV03:
    current = open_verified_gremlin_pnv_authoring_live(
        pnv_text,
        surface_root=surface_root,
        socket_path=socket_path,
        max_heartbeat_age_s=max_heartbeat_age_s,
    )
    return GremlinPNVAuthoringSessionV03(
        pnv_text=pnv_text,
        generation_binding=current.generation_binding,
        surface_root=Path(surface_root),
        socket_path=Path(socket_path),
        max_heartbeat_age_s=max_heartbeat_age_s,
    )


def hydrate_and_open_gremlin_pnv_authoring_live(
    pnv_text: str,
    *,
    request: str = "GREMLIN_PNV_AUTHORING_BOOT",
    surface_root: Path | str = DEFAULT_SURFACE_ROOT,
    socket_path: Path | str = DEFAULT_SOCKET,
    max_heartbeat_age_s: float = 2.0,
) -> tuple[GremlinLiveHydration, GremlinPNVAuthoringSessionV03]:
    hydration = hydrate_gremlin_pnv_live(
        pnv_text,
        request=request,
        surface_root=surface_root,
        socket_path=socket_path,
        max_heartbeat_age_s=max_heartbeat_age_s,
    )
    session = open_gremlin_pnv_authoring_live(
        pnv_text,
        surface_root=surface_root,
        socket_path=socket_path,
        max_heartbeat_age_s=max_heartbeat_age_s,
    )
    if session.generation_binding != hydration.witness["generation_binding"]:
        raise GremlinPNVAuthoringError(
            "GREMLIN hydration/open generation binding mismatch"
        )
    return hydration, session
