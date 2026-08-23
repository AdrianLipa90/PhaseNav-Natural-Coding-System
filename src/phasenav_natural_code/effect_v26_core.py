from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Mapping, Protocol

from .runtime_v25_core import RUNTIME_CONTRACT_ID as V25_RUNTIME_CONTRACT_ID

EFFECT_CONTRACT_ID = "PNCS_EFFECT_BOUNDARY_V0_26"
REQUEST_SCHEMA = "PNCS_EFFECT_REQUEST_V0_26"
AUTHORIZATION_SCHEMA = "PNCS_EFFECT_AUTHORIZATION_V0_26"
ADAPTER_SCHEMA = "PNCS_EFFECT_ADAPTER_DESCRIPTOR_V0_26"
EFFECT_RECORD_SCHEMA = "PNCS_EFFECT_RECORD_V0_26"
EFFECT_RECEIPT_SCHEMA = "PNCS_EFFECT_RECEIPT_V0_26"
V25_DISPATCH_SCHEMA = "PNCS_RESIDENT_CONTROL_DISPATCH_RECEIPT_V0_25"
EFFECT_KIND_NOEMA_RUNTIME_RECORD_WRITE = "NOEMA_RUNTIME_RECORD_WRITE"
EFFECT_TARGET_NOEMA_RUNTIME_RECORD = "pncs.v0.26.runtime-record"
MAX_EFFECT_PAYLOAD_BYTES = 4096

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DISPATCH_RE = re.compile(r"^pncs:resident-dispatch:sha256:[0-9a-f]{64}$")
_RESULT_RE = re.compile(r"^pncs:result:sha256:[0-9a-f]{64}$")
_LINEAGE_RE = re.compile(r"^pncs:lineage:sha256:[0-9a-f]{64}$")
_PROGRAM_RE = re.compile(r"^pncs:program:sha256:[0-9a-f]{64}$")
_HANDLE_RE = re.compile(r"^pncs:resident:sha256:[0-9a-f]{64}$")
_ADMISSION_RE = re.compile(r"^pncs:resident-admission:sha256:[0-9a-f]{64}$")
_GENERATION_RE = re.compile(r"^pncs:runtime-generation:sha256:[0-9a-f]{64}$")
_ADAPTER_RE = re.compile(r"^pncs:effect-adapter:sha256:[0-9a-f]{64}$")
_REQUEST_RE = re.compile(r"^pncs:effect-request:sha256:[0-9a-f]{64}$")
_AUTHORITY_RE = re.compile(r"^[A-Z0-9][A-Z0-9_.:/+-]{0,191}$")


class EffectBoundaryV26Error(RuntimeError):
    pass


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, Mapping):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EffectBoundaryV26Error("non-finite value is not canonical JSON")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise EffectBoundaryV26Error(f"unsupported canonical value type: {type(value).__name__}")


def _compact_json(value: object) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _json_bytes(value: object) -> bytes:
    return (_compact_json(value) + "\n").encode("utf-8")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_compact_json(value).encode("utf-8"))


def _typed_id(prefix: str, payload: object) -> str:
    return f"{prefix}:sha256:{_sha256_json(payload)}"


def _typed(value: object, regex: re.Pattern[str], field: str) -> str:
    if not isinstance(value, str) or not regex.fullmatch(value):
        raise EffectBoundaryV26Error(f"invalid {field}")
    return value


def _digest(value: object, field: str) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise EffectBoundaryV26Error(f"{field} must be lowercase SHA-256")
    return value


def _authority_id(value: object) -> str:
    if not isinstance(value, str) or not _AUTHORITY_RE.fullmatch(value):
        raise EffectBoundaryV26Error("authority_id must be a stable uppercase contract identifier")
    return value


def _payload_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise EffectBoundaryV26Error("effect payload must be a mapping")
    canonical = _jsonable(value)
    if not isinstance(canonical, dict):
        raise EffectBoundaryV26Error("effect payload must canonicalize to a JSON object")
    return canonical


@dataclass(frozen=True)
class EffectOrigin:
    dispatch_id: str
    program_id: str
    handle_id: str
    generation_id: str
    resident_admission_id: str
    result_id: str
    lineage_id: str
    execution_receipt_sha256: str
    target: str
    branch_truth_state: str

    def __post_init__(self) -> None:
        _typed(self.dispatch_id, _DISPATCH_RE, "dispatch_id")
        _typed(self.program_id, _PROGRAM_RE, "program_id")
        _typed(self.handle_id, _HANDLE_RE, "handle_id")
        _typed(self.generation_id, _GENERATION_RE, "generation_id")
        _typed(self.resident_admission_id, _ADMISSION_RE, "resident_admission_id")
        _typed(self.result_id, _RESULT_RE, "result_id")
        _typed(self.lineage_id, _LINEAGE_RE, "lineage_id")
        _digest(self.execution_receipt_sha256, "execution_receipt_sha256")
        if not self.target or self.branch_truth_state not in {"TRUE", "FALSE"}:
            raise EffectBoundaryV26Error("invalid v0.25 dispatch result fields")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "dispatch_id": self.dispatch_id,
            "program_id": self.program_id,
            "handle_id": self.handle_id,
            "generation_id": self.generation_id,
            "resident_admission_id": self.resident_admission_id,
            "result_id": self.result_id,
            "lineage_id": self.lineage_id,
            "execution_receipt_sha256": self.execution_receipt_sha256,
            "target": self.target,
            "branch_truth_state": self.branch_truth_state,
        }

    @classmethod
    def from_dispatch_receipt(cls, receipt: Mapping[str, object]) -> "EffectOrigin":
        if not isinstance(receipt, Mapping):
            raise EffectBoundaryV26Error("v0.25 dispatch receipt mapping required")
        if receipt.get("schema") != V25_DISPATCH_SCHEMA or receipt.get("runtime_contract_id") != V25_RUNTIME_CONTRACT_ID:
            raise EffectBoundaryV26Error("effect origin requires exact v0.25 resident dispatch receipt")
        dispatch_id = _typed(receipt.get("dispatch_id"), _DISPATCH_RE, "dispatch_id")
        body = dict(receipt); body.pop("dispatch_id", None)
        if _typed_id("pncs:resident-dispatch", body) != dispatch_id:
            raise EffectBoundaryV26Error("v0.25 dispatch receipt digest mismatch")
        if receipt.get("external_effects") is not False:
            raise EffectBoundaryV26Error("v0.25 dispatch receipt unexpectedly opened effects")
        if receipt.get("continuation_execution_opened") is not False or receipt.get("return_execution_opened") is not False:
            raise EffectBoundaryV26Error("v0.25 dispatch receipt crossed closed continuation/return boundary")
        if receipt.get("static_runtime_fallback") is not False or receipt.get("deterministic_fields_only") is not True:
            raise EffectBoundaryV26Error("v0.25 dispatch receipt violates deterministic/no-fallback boundary")
        return cls(
            dispatch_id=dispatch_id,
            program_id=str(receipt.get("program_id", "")),
            handle_id=str(receipt.get("handle_id", "")),
            generation_id=str(receipt.get("generation_id", "")),
            resident_admission_id=str(receipt.get("resident_admission_id", "")),
            result_id=str(receipt.get("result_id", "")),
            lineage_id=str(receipt.get("lineage_id", "")),
            execution_receipt_sha256=str(receipt.get("execution_receipt_sha256", "")),
            target=str(receipt.get("target", "")),
            branch_truth_state=str(receipt.get("branch_truth_state", "")),
        )


@dataclass(frozen=True)
class EffectAdapterDescriptor:
    effect_kind: str
    target: str
    runtime_relative_root: str
    max_payload_bytes: int
    append_only: bool = True
    path_from_program: bool = False
    symlinks_allowed: bool = False
    network_allowed: bool = False
    subprocess_allowed: bool = False
    git_allowed: bool = False
    device_allowed: bool = False

    def __post_init__(self) -> None:
        if self.effect_kind != EFFECT_KIND_NOEMA_RUNTIME_RECORD_WRITE:
            raise EffectBoundaryV26Error("unsupported v0.26 effect kind")
        if self.target != EFFECT_TARGET_NOEMA_RUNTIME_RECORD:
            raise EffectBoundaryV26Error("unsupported v0.26 effect target")
        if self.runtime_relative_root != "pncs/v0.26/effects/records":
            raise EffectBoundaryV26Error("v0.26 adapter root is fixed")
        if not isinstance(self.max_payload_bytes, int) or self.max_payload_bytes < 1 or self.max_payload_bytes > MAX_EFFECT_PAYLOAD_BYTES:
            raise EffectBoundaryV26Error("invalid adapter payload bound")
        if not self.append_only or self.path_from_program or self.symlinks_allowed:
            raise EffectBoundaryV26Error("adapter violates append-only/no-path/no-symlink boundary")
        if self.network_allowed or self.subprocess_allowed or self.git_allowed or self.device_allowed:
            raise EffectBoundaryV26Error("v0.26 first adapter cannot open network/subprocess/Git/device")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": ADAPTER_SCHEMA,
            "effect_contract_id": EFFECT_CONTRACT_ID,
            "effect_kind": self.effect_kind,
            "target": self.target,
            "runtime_relative_root": self.runtime_relative_root,
            "max_payload_bytes": self.max_payload_bytes,
            "append_only": self.append_only,
            "path_from_program": self.path_from_program,
            "symlinks_allowed": self.symlinks_allowed,
            "network_allowed": self.network_allowed,
            "subprocess_allowed": self.subprocess_allowed,
            "git_allowed": self.git_allowed,
            "device_allowed": self.device_allowed,
        }

    @property
    def adapter_id(self) -> str:
        return _typed_id("pncs:effect-adapter", self.payload)


NOEMA_RUNTIME_RECORD_ADAPTER = EffectAdapterDescriptor(
    effect_kind=EFFECT_KIND_NOEMA_RUNTIME_RECORD_WRITE,
    target=EFFECT_TARGET_NOEMA_RUNTIME_RECORD,
    runtime_relative_root="pncs/v0.26/effects/records",
    max_payload_bytes=MAX_EFFECT_PAYLOAD_BYTES,
)


@dataclass(frozen=True)
class EffectRequest:
    origin: EffectOrigin
    effect_kind: str
    target: str
    adapter_id: str
    payload_data: Mapping[str, object]

    def __post_init__(self) -> None:
        if not isinstance(self.origin, EffectOrigin):
            raise EffectBoundaryV26Error("EffectOrigin required")
        if self.effect_kind != EFFECT_KIND_NOEMA_RUNTIME_RECORD_WRITE:
            raise EffectBoundaryV26Error("effect kind is not admitted by v0.26")
        if self.target != EFFECT_TARGET_NOEMA_RUNTIME_RECORD:
            raise EffectBoundaryV26Error("effect target is not admitted by v0.26")
        _typed(self.adapter_id, _ADAPTER_RE, "adapter_id")
        payload = _payload_mapping(self.payload_data)
        raw = _compact_json(payload).encode("utf-8")
        if len(raw) > MAX_EFFECT_PAYLOAD_BYTES:
            raise EffectBoundaryV26Error("effect payload exceeds v0.26 maximum")
        object.__setattr__(self, "payload_data", payload)

    @property
    def payload_sha256(self) -> str:
        return _sha256_json(self.payload_data)

    @property
    def payload_size_bytes(self) -> int:
        return len(_compact_json(self.payload_data).encode("utf-8"))

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": REQUEST_SCHEMA,
            "effect_contract_id": EFFECT_CONTRACT_ID,
            "origin": self.origin.payload,
            "effect_kind": self.effect_kind,
            "target": self.target,
            "adapter_id": self.adapter_id,
            "payload": dict(self.payload_data),
            "payload_sha256": self.payload_sha256,
            "payload_size_bytes": self.payload_size_bytes,
            "explicit_authorization_required": True,
            "default_policy": "DENY",
            "program_supplied_path": False,
            "network_allowed": False,
            "subprocess_allowed": False,
            "git_allowed": False,
            "device_allowed": False,
            "static_runtime_fallback": False,
        }

    @property
    def request_id(self) -> str:
        return _typed_id("pncs:effect-request", self.payload)


@dataclass(frozen=True)
class EffectAuthorizationGrant:
    request_id: str
    generation_id: str
    adapter_id: str
    authority_id: str
    effect_kind: str
    target: str
    max_payload_bytes: int
    decision: str = "ALLOW"
    exact_request_only: bool = True
    no_delegation: bool = True

    def __post_init__(self) -> None:
        _typed(self.request_id, _REQUEST_RE, "request_id")
        _typed(self.generation_id, _GENERATION_RE, "generation_id")
        _typed(self.adapter_id, _ADAPTER_RE, "adapter_id")
        _authority_id(self.authority_id)
        if self.effect_kind != EFFECT_KIND_NOEMA_RUNTIME_RECORD_WRITE or self.target != EFFECT_TARGET_NOEMA_RUNTIME_RECORD:
            raise EffectBoundaryV26Error("authorization effect scope is not admitted")
        if not isinstance(self.max_payload_bytes, int) or self.max_payload_bytes < 1 or self.max_payload_bytes > MAX_EFFECT_PAYLOAD_BYTES:
            raise EffectBoundaryV26Error("authorization payload bound is invalid")
        if self.decision != "ALLOW":
            raise EffectBoundaryV26Error("only explicit ALLOW grants can enter the authorization registry")
        if not self.exact_request_only or not self.no_delegation:
            raise EffectBoundaryV26Error("v0.26 authorization must be exact-request/no-delegation")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": AUTHORIZATION_SCHEMA,
            "effect_contract_id": EFFECT_CONTRACT_ID,
            "request_id": self.request_id,
            "generation_id": self.generation_id,
            "adapter_id": self.adapter_id,
            "authority_id": self.authority_id,
            "effect_kind": self.effect_kind,
            "target": self.target,
            "max_payload_bytes": self.max_payload_bytes,
            "decision": self.decision,
            "exact_request_only": self.exact_request_only,
            "no_delegation": self.no_delegation,
            "default_policy": "DENY",
        }

    @property
    def authorization_id(self) -> str:
        return _typed_id("pncs:effect-authorization", self.payload)


class EffectAuthorizationRegistry:
    def __init__(self) -> None:
        self._by_id: dict[str, EffectAuthorizationGrant] = {}
        self._by_request: dict[str, list[str]] = {}

    def register(self, grant: EffectAuthorizationGrant) -> EffectAuthorizationGrant:
        if not isinstance(grant, EffectAuthorizationGrant):
            raise EffectBoundaryV26Error("EffectAuthorizationGrant required")
        aid = grant.authorization_id
        if aid not in self._by_id:
            self._by_id[aid] = grant
            self._by_request.setdefault(grant.request_id, []).append(aid)
        return self._by_id[aid]

    def exact_grant(self, request: EffectRequest) -> EffectAuthorizationGrant:
        if not isinstance(request, EffectRequest):
            raise EffectBoundaryV26Error("EffectRequest required")
        ids = self._by_request.get(request.request_id, [])
        if not ids:
            raise EffectBoundaryV26Error("effect request has no explicit authorization grant")
        if len(ids) != 1:
            raise EffectBoundaryV26Error("effect request has ambiguous authorization grants")
        grant = self._by_id[ids[0]]
        if grant.request_id != request.request_id:
            raise EffectBoundaryV26Error("authorization/request mismatch")
        if grant.generation_id != request.origin.generation_id:
            raise EffectBoundaryV26Error("authorization generation mismatch")
        if grant.adapter_id != request.adapter_id or grant.effect_kind != request.effect_kind or grant.target != request.target:
            raise EffectBoundaryV26Error("authorization scope mismatch")
        if request.payload_size_bytes > grant.max_payload_bytes:
            raise EffectBoundaryV26Error("effect payload exceeds authorization bound")
        return grant


class EffectAdapter(Protocol):
    descriptor: EffectAdapterDescriptor
    def apply(self, request: EffectRequest, grant: EffectAuthorizationGrant, root) -> tuple[str, bytes]: ...


class EffectAdapterRegistry:
    def __init__(self) -> None:
        self._by_id: dict[str, EffectAdapter] = {}

    def register(self, adapter: EffectAdapter) -> EffectAdapter:
        descriptor = getattr(adapter, "descriptor", None)
        if not isinstance(descriptor, EffectAdapterDescriptor):
            raise EffectBoundaryV26Error("effect adapter must expose EffectAdapterDescriptor")
        aid = descriptor.adapter_id
        prior = self._by_id.get(aid)
        if prior is not None and prior is not adapter:
            raise EffectBoundaryV26Error("effect adapter ID collision")
        self._by_id[aid] = adapter
        return adapter

    def adapter(self, adapter_id: str) -> EffectAdapter:
        _typed(adapter_id, _ADAPTER_RE, "adapter_id")
        try:
            return self._by_id[adapter_id]
        except KeyError as exc:
            raise EffectBoundaryV26Error("effect adapter is not registered") from exc
