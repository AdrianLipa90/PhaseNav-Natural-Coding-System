from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping

from .runtime_v25_core import DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT, read_live_generation
from .effect_v26_core import (
    EFFECT_CONTRACT_ID,
    EFFECT_RECEIPT_SCHEMA,
    EFFECT_RECORD_SCHEMA,
    NOEMA_RUNTIME_RECORD_ADAPTER,
    EffectAdapter,
    EffectAdapterDescriptor,
    EffectAdapterRegistry,
    EffectAuthorizationGrant,
    EffectAuthorizationRegistry,
    EffectBoundaryV26Error,
    EffectOrigin,
    EffectRequest,
    _GENERATION_RE,
    _digest,
    _json_bytes,
    _sha256_bytes,
    _typed,
    _typed_id,
)
from .effect_v26_fs import _immutable_write_at, _open_fixed_directory_fd


@dataclass(frozen=True)
class EffectReceipt:
    request: EffectRequest
    grant: EffectAuthorizationGrant
    adapter: EffectAdapterDescriptor
    effect_relative_path: str
    effect_sha256: str
    effect_size_bytes: int
    generation_id_before: str
    generation_id_after: str

    def __post_init__(self) -> None:
        if self.request.request_id != self.grant.request_id:
            raise EffectBoundaryV26Error("receipt request/authorization mismatch")
        if self.adapter.adapter_id != self.request.adapter_id:
            raise EffectBoundaryV26Error("receipt adapter/request mismatch")
        _digest(self.effect_sha256, "effect_sha256")
        if not isinstance(self.effect_size_bytes, int) or self.effect_size_bytes < 1:
            raise EffectBoundaryV26Error("effect_size_bytes must be positive")
        _typed(self.generation_id_before, _GENERATION_RE, "generation_id_before")
        _typed(self.generation_id_after, _GENERATION_RE, "generation_id_after")
        if self.generation_id_before != self.generation_id_after:
            raise EffectBoundaryV26Error("runtime generation changed across effect")
        if self.generation_id_before != self.request.origin.generation_id:
            raise EffectBoundaryV26Error("effect generation differs from dispatch origin")
        if not self.effect_relative_path.startswith("pncs/v0.26/effects/records/"):
            raise EffectBoundaryV26Error("effect receipt path escaped bounded adapter root")

    @property
    def effect_id(self) -> str:
        return _typed_id("pncs:effect", {
            "schema": EFFECT_RECORD_SCHEMA,
            "request_id": self.request.request_id,
            "authorization_id": self.grant.authorization_id,
            "adapter_id": self.adapter.adapter_id,
            "effect_sha256": self.effect_sha256,
            "effect_size_bytes": self.effect_size_bytes,
        })

    @property
    def inverse_provenance(self) -> list[dict[str, str]]:
        o = self.request.origin
        return [
            {"level": "EFFECT", "id": self.effect_id},
            {"level": "AUTHORIZATION", "id": self.grant.authorization_id},
            {"level": "EFFECT_REQUEST", "id": self.request.request_id},
            {"level": "DISPATCH", "id": o.dispatch_id},
            {"level": "RESULT", "id": o.result_id},
            {"level": "LINEAGE", "id": o.lineage_id},
            {"level": "PROGRAM", "id": o.program_id},
            {"level": "RESIDENT_HANDLE", "id": o.handle_id},
            {"level": "RUNTIME_GENERATION", "id": o.generation_id},
        ]

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": EFFECT_RECEIPT_SCHEMA,
            "effect_contract_id": EFFECT_CONTRACT_ID,
            "request_id": self.request.request_id,
            "authorization_id": self.grant.authorization_id,
            "authority_id": self.grant.authority_id,
            "adapter_id": self.adapter.adapter_id,
            "effect_id": self.effect_id,
            "effect_kind": self.request.effect_kind,
            "target": self.request.target,
            "effect_relative_path": self.effect_relative_path,
            "effect_sha256": self.effect_sha256,
            "effect_size_bytes": self.effect_size_bytes,
            "generation_id_before": self.generation_id_before,
            "generation_id_after": self.generation_id_after,
            "inverse_provenance": self.inverse_provenance,
            "bounded_external_effect": True,
            "append_only": True,
            "idempotent_exact_replay": True,
            "program_supplied_path": False,
            "network_allowed": False,
            "subprocess_allowed": False,
            "git_allowed": False,
            "device_allowed": False,
            "static_runtime_fallback": False,
            "deterministic_fields_only": True,
        }

    @property
    def receipt_id(self) -> str:
        return _typed_id("pncs:effect-receipt", self.payload)


@dataclass(frozen=True)
class EffectExecutionResult:
    receipt: EffectReceipt
    receipt_path: str


class EffectBoundaryRuntime:
    def __init__(self, surface_root: Path | str = DEFAULT_SURFACE_ROOT, *, socket_path: Path | str = DEFAULT_SOCKET,
                 max_heartbeat_age_s: float = 2.0, require_socket: bool = True, require_canonical_root: bool = True,
                 generation_reader=read_live_generation) -> None:
        self.root = Path(surface_root)
        self.socket_path = Path(socket_path)
        self.max_heartbeat_age_s = max_heartbeat_age_s
        self.require_socket = require_socket
        self.require_canonical_root = require_canonical_root
        self.generation_reader = generation_reader
        if require_canonical_root and self.root != DEFAULT_SURFACE_ROOT:
            raise EffectBoundaryV26Error("v0.26 operational effect boundary is fixed to /dev/shm/ciel_noema")
        self.authorization = EffectAuthorizationRegistry()
        self.adapters = EffectAdapterRegistry()

    def register_adapter(self, adapter: EffectAdapter) -> EffectAdapter:
        return self.adapters.register(adapter)

    def register_authorization(self, grant: EffectAuthorizationGrant) -> EffectAuthorizationGrant:
        return self.authorization.register(grant)

    def generation(self):
        try:
            return self.generation_reader(self.root, socket_path=self.socket_path, max_heartbeat_age_s=self.max_heartbeat_age_s,
                                          require_socket=self.require_socket, require_canonical_root=self.require_canonical_root)
        except EffectBoundaryV26Error:
            raise
        except Exception as exc:
            raise EffectBoundaryV26Error("live v0.25 generation admission failed") from exc

    def execute(self, request: EffectRequest) -> EffectExecutionResult:
        if not isinstance(request, EffectRequest):
            raise EffectBoundaryV26Error("EffectRequest required")
        before = self.generation()
        generation_before = _typed(getattr(before, "generation_id", None), _GENERATION_RE, "live generation_id")
        if generation_before != request.origin.generation_id:
            raise EffectBoundaryV26Error("effect request is stale for current live runtime generation")
        grant = self.authorization.exact_grant(request)
        adapter = self.adapters.adapter(request.adapter_id)
        descriptor = getattr(adapter, "descriptor", None)
        if not isinstance(descriptor, EffectAdapterDescriptor) or descriptor.adapter_id != request.adapter_id:
            raise EffectBoundaryV26Error("registered adapter identity mismatch")
        precommit = self.generation()
        generation_precommit = _typed(getattr(precommit, "generation_id", None), _GENERATION_RE, "precommit generation_id")
        if generation_precommit != generation_before:
            raise EffectBoundaryV26Error("live generation changed before effect commit")
        relative_path, raw = adapter.apply(request, grant, self.root)
        after = self.generation()
        generation_after = _typed(getattr(after, "generation_id", None), _GENERATION_RE, "post-effect generation_id")
        if generation_after != generation_before:
            raise EffectBoundaryV26Error("live generation changed during effect commit")
        receipt = EffectReceipt(request, grant, descriptor, relative_path, _sha256_bytes(raw), len(raw), generation_before, generation_after)
        receipt_relative = ["pncs", "v0.26", "receipts"]
        receipt_filename = f"{receipt.receipt_id.rsplit(':', 1)[-1]}.json"
        receipt_raw = _json_bytes({**receipt.payload, "receipt_id": receipt.receipt_id})
        receipt_dir_fd = _open_fixed_directory_fd(self.root, receipt_relative)
        try:
            _immutable_write_at(receipt_dir_fd, receipt_filename, receipt_raw, collision="immutable effect receipt collision")
        finally:
            os.close(receipt_dir_fd)
        return EffectExecutionResult(receipt, str(self.root.joinpath(*receipt_relative, receipt_filename)))


def make_effect_request(dispatch_receipt: Mapping[str, object], payload: Mapping[str, object], *,
                        adapter: EffectAdapterDescriptor = NOEMA_RUNTIME_RECORD_ADAPTER) -> EffectRequest:
    if not isinstance(adapter, EffectAdapterDescriptor):
        raise EffectBoundaryV26Error("EffectAdapterDescriptor required")
    return EffectRequest(EffectOrigin.from_dispatch_receipt(dispatch_receipt), adapter.effect_kind, adapter.target, adapter.adapter_id, payload)


def authorize_exact_request(request: EffectRequest, *, authority_id: str, max_payload_bytes: int | None = None) -> EffectAuthorizationGrant:
    if not isinstance(request, EffectRequest):
        raise EffectBoundaryV26Error("EffectRequest required")
    bound = request.payload_size_bytes if max_payload_bytes is None else max_payload_bytes
    if bound < request.payload_size_bytes:
        raise EffectBoundaryV26Error("authorization bound is smaller than exact request payload")
    return EffectAuthorizationGrant(request.request_id, request.origin.generation_id, request.adapter_id, authority_id,
                                    request.effect_kind, request.target, bound)
