from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Iterable, Mapping, Sequence

TAU = 2.0 * math.pi
DIM = 36

class RealizationV18Error(ValueError):
    pass

_CONTENT_ID_RE = re.compile(
    r"^pncs:(?:def|class|file|cluster|subsystem|daemon|low-orchestrator|high-orchestrator|system):sha256:[0-9a-f]{64}$"
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CONTRACT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/+-]{0,191}$")
_BINDING_SCHEMA = "PNCS_EXACT_36D_BINDING_V0_18"
_REALIZATION_SCHEMA = "PNCS_EXACT_36D_REALIZATION_V0_18"
_COORDINATE_SEMANTICS = "phase_angles_radians"
_SPACE = "T^36"
_RANGE = "[0,2π)"


def _compact_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _typed_id(prefix: str, payload: Mapping[str, object]) -> str:
    return f"{prefix}:sha256:{_sha256_hex(_compact_json(dict(payload)).encode('utf-8'))}"


def _contract_id(value: str, field: str) -> str:
    if not isinstance(value, str) or not _CONTRACT_RE.fullmatch(value):
        raise RealizationV18Error(f"{field} must be a non-empty stable contract identifier")
    return value


def _content_id(value: str) -> str:
    if not isinstance(value, str) or not _CONTENT_ID_RE.fullmatch(value):
        raise RealizationV18Error("content_id must be a typed PNCS sha256 content ID")
    return value


def _digest(value: str, field: str) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise RealizationV18Error(f"{field} must be lowercase 64-hex SHA-256")
    return value


def _source_locator(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RealizationV18Error("source_locator must be a non-empty provenance locator")
    return value.strip()


@dataclass(frozen=True)
class PhaseVector36:
    """Exact PhaseNav torus coordinate vector.

    The vector is a realization address, not semantic authority.
    """

    angles: tuple[float, ...]

    def __init__(self, angles: Sequence[float]) -> None:
        vals = tuple(float(v) for v in angles)
        if len(vals) != DIM:
            raise RealizationV18Error(f"phase vector must contain exactly {DIM} angles")
        for i, value in enumerate(vals):
            if not math.isfinite(value):
                raise RealizationV18Error(f"phase[{i}] is not finite")
            if value < 0.0 or value >= TAU:
                raise RealizationV18Error(f"phase[{i}] must be in [0, 2π)")
        object.__setattr__(self, "angles", vals)

    @property
    def compact_payload(self) -> list[float]:
        return list(self.angles)

    @property
    def phase_sha256(self) -> str:
        # Matches the frozen-vector evidence convention: SHA256(compact_json(phase36)).
        return _sha256_hex(_compact_json(self.compact_payload).encode("utf-8"))

    @property
    def space(self) -> str:
        return _SPACE

    @property
    def coordinate_semantics(self) -> str:
        return _COORDINATE_SEMANTICS

    @property
    def coordinate_range(self) -> str:
        return _RANGE


@dataclass(frozen=True)
class RealizationBinding:
    content_id: str
    phase: PhaseVector36
    basis_id: str
    derivation_id: str
    source_digest_sha256: str
    source_locator: str
    epistemic_operator: str = "CHYBA"
    canon_allowed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_id", _content_id(self.content_id))
        if not isinstance(self.phase, PhaseVector36):
            raise RealizationV18Error("phase must be PhaseVector36")
        object.__setattr__(self, "basis_id", _contract_id(self.basis_id, "basis_id"))
        object.__setattr__(self, "derivation_id", _contract_id(self.derivation_id, "derivation_id"))
        object.__setattr__(
            self, "source_digest_sha256", _digest(self.source_digest_sha256, "source_digest_sha256")
        )
        object.__setattr__(self, "source_locator", _source_locator(self.source_locator))
        if self.epistemic_operator != "CHYBA":
            raise RealizationV18Error("v0.18 bindings must remain under CHYBA")
        if self.canon_allowed:
            raise RealizationV18Error("v0.18 evidence binding cannot self-promote to canon")

    @property
    def realization_payload(self) -> dict[str, object]:
        return {
            "schema": _REALIZATION_SCHEMA,
            "content_id": self.content_id,
            "basis_id": self.basis_id,
            "derivation_id": self.derivation_id,
            "space": self.phase.space,
            "coordinate_semantics": self.phase.coordinate_semantics,
            "coordinate_range": self.phase.coordinate_range,
            "phase36": self.phase.compact_payload,
            "phase36_sha256": self.phase.phase_sha256,
        }

    @property
    def realization_id(self) -> str:
        # Semantic content ID and phase realization ID remain separate identities.
        return _typed_id("pncs:realization36", self.realization_payload)

    @property
    def binding_payload(self) -> dict[str, object]:
        return {
            "schema": _BINDING_SCHEMA,
            "realization_id": self.realization_id,
            "content_id": self.content_id,
            "basis_id": self.basis_id,
            "derivation_id": self.derivation_id,
            "phase36_sha256": self.phase.phase_sha256,
            "source_digest_sha256": self.source_digest_sha256,
            "source_locator": self.source_locator,
            "epistemic_operator": self.epistemic_operator,
            "canon_allowed": self.canon_allowed,
        }

    @property
    def binding_id(self) -> str:
        return _typed_id("pncs:binding36", self.binding_payload)

    @property
    def record_payload(self) -> dict[str, object]:
        return {
            **self.binding_payload,
            "binding_id": self.binding_id,
        }

    def verify(self) -> None:
        _content_id(self.content_id)
        _contract_id(self.basis_id, "basis_id")
        _contract_id(self.derivation_id, "derivation_id")
        _digest(self.phase.phase_sha256, "phase36_sha256")
        _digest(self.source_digest_sha256, "source_digest_sha256")
        _source_locator(self.source_locator)
        if self.epistemic_operator != "CHYBA" or self.canon_allowed:
            raise RealizationV18Error("epistemic binding invariant violated")


class RealizationRegistry:
    """Fail-closed exact binding registry.

    Exact phase equality can be queried, but it never promotes semantic equivalence.
    No nearest-neighbour or similarity-to-semantics API exists in v0.18.
    """

    def __init__(self) -> None:
        self._by_binding: dict[str, RealizationBinding] = {}
        self._by_key: dict[tuple[str, str, str], list[str]] = {}
        self._by_phase: dict[str, set[str]] = {}

    def bind(self, binding: RealizationBinding) -> RealizationBinding:
        if not isinstance(binding, RealizationBinding):
            raise RealizationV18Error("RealizationBinding required")
        binding.verify()
        key = (binding.content_id, binding.basis_id, binding.derivation_id)
        existing_ids = self._by_key.get(key, [])
        for binding_id in existing_ids:
            prior = self._by_binding[binding_id]
            if prior.phase.angles != binding.phase.angles:
                raise RealizationV18Error(
                    "conflicting exact phase realization for same content/basis/derivation"
                )
        if binding.binding_id not in self._by_binding:
            self._by_binding[binding.binding_id] = binding
            self._by_key.setdefault(key, []).append(binding.binding_id)
            self._by_phase.setdefault(binding.phase.phase_sha256, set()).add(binding.content_id)
        return self._by_binding[binding.binding_id]

    def binding(self, binding_id: str) -> RealizationBinding:
        try:
            return self._by_binding[binding_id]
        except KeyError as exc:
            raise RealizationV18Error(f"unknown binding_id: {binding_id}") from exc

    def bindings_for(
        self, content_id: str, *, basis_id: str | None = None, derivation_id: str | None = None
    ) -> tuple[RealizationBinding, ...]:
        cid = _content_id(content_id)
        out: list[RealizationBinding] = []
        for (registered_cid, basis, derivation), ids in sorted(self._by_key.items()):
            if registered_cid != cid:
                continue
            if basis_id is not None and basis != basis_id:
                continue
            if derivation_id is not None and derivation != derivation_id:
                continue
            out.extend(self._by_binding[i] for i in ids)
        return tuple(out)

    def semantic_ids_for_exact_phase(self, phase: PhaseVector36) -> tuple[str, ...]:
        if not isinstance(phase, PhaseVector36):
            raise RealizationV18Error("PhaseVector36 required")
        return tuple(sorted(self._by_phase.get(phase.phase_sha256, set())))

    def same_exact_realization(self, left_binding_id: str, right_binding_id: str) -> bool:
        left = self.binding(left_binding_id)
        right = self.binding(right_binding_id)
        return (
            left.basis_id == right.basis_id
            and left.derivation_id == right.derivation_id
            and left.phase.angles == right.phase.angles
        )

    def semantic_equivalent(self, *_: object) -> bool:
        raise RealizationV18Error(
            "36D realization equality/similarity is not semantic equivalence authority"
        )

    def deterministic_receipt(self) -> dict[str, object]:
        rows = [self._by_binding[k].binding_payload for k in sorted(self._by_binding)]
        payload = {
            "schema": "PNCS_REALIZATION_REGISTRY_RECEIPT_V0_18",
            "binding_ids": sorted(self._by_binding),
            "bindings": rows,
            "semantic_equivalence_from_vectors": False,
        }
        return {
            **payload,
            "receipt_sha256": _sha256_hex(_compact_json(payload).encode("utf-8")),
        }


def verify_serialized_binding(
    payload: Mapping[str, object],
    *,
    phase36: Sequence[float],
) -> RealizationBinding:
    if not isinstance(payload, Mapping):
        raise RealizationV18Error("binding payload mapping required")
    required = {
        "schema",
        "realization_id",
        "content_id",
        "basis_id",
        "derivation_id",
        "phase36_sha256",
        "source_digest_sha256",
        "source_locator",
        "epistemic_operator",
        "canon_allowed",
        "binding_id",
    }
    if set(payload) != required:
        raise RealizationV18Error("serialized binding keys do not match v0.18 schema")
    if payload.get("schema") != _BINDING_SCHEMA:
        raise RealizationV18Error("serialized binding schema mismatch")
    phase = PhaseVector36(phase36)
    if payload.get("phase36_sha256") != phase.phase_sha256:
        raise RealizationV18Error("serialized phase36 digest mismatch")
    binding = RealizationBinding(
        content_id=str(payload["content_id"]),
        phase=phase,
        basis_id=str(payload["basis_id"]),
        derivation_id=str(payload["derivation_id"]),
        source_digest_sha256=str(payload["source_digest_sha256"]),
        source_locator=str(payload["source_locator"]),
        epistemic_operator=str(payload["epistemic_operator"]),
        canon_allowed=bool(payload["canon_allowed"]),
    )
    if payload.get("realization_id") != binding.realization_id:
        raise RealizationV18Error("serialized realization_id mismatch")
    if payload.get("binding_id") != binding.binding_id:
        raise RealizationV18Error("serialized binding_id mismatch")
    if dict(payload) != binding.record_payload:
        raise RealizationV18Error("serialized binding payload mismatch")
    return binding
