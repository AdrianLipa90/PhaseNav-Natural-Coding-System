from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
import struct
from typing import Sequence

DIM = 36
TAU = 2.0 * math.pi
GENERATOR_ID = "PNCS_SEMANTIC_CONTENT_ADDRESS_GENERATOR_V2"
GENERATOR_SCHEMA = "PNCS_SEMANTIC_CONTENT_ADDRESS_V2"
TRANSITION_SCHEMA = "PNCS_TYPED_SEMANTIC_T36_TRANSITION_V0_31"
TRAJECTORY_SCHEMA = "PNCS_TYPED_SEMANTIC_T36_TRAJECTORY_V0_31"
DOMAIN = b"PNCS_SEMANTIC_CONTENT_ADDRESS_V2\x00"
CONTENT_RE = re.compile(r"^pncs:semantic-role:sha256:[0-9a-f]{64}$")


class SemanticAddressV31Error(ValueError):
    pass


def _canon(value: object) -> object:
    if isinstance(value, tuple):
        return [_canon(x) for x in value]
    if isinstance(value, list):
        return [_canon(x) for x in value]
    if isinstance(value, dict):
        return {str(k): _canon(value[k]) for k in sorted(value)}
    if isinstance(value, float) and not math.isfinite(value):
        raise SemanticAddressV31Error("non-finite canonical float")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise SemanticAddressV31Error(f"unsupported canonical type: {type(value).__name__}")


def compact_json(value: object) -> str:
    return json.dumps(_canon(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value: object) -> str:
    return hashlib.sha256(compact_json(value).encode("utf-8")).hexdigest()


def typed_id(prefix: str, value: object) -> str:
    return f"{prefix}:sha256:{digest(value)}"


def phase_sha(phase: Sequence[float]) -> str:
    return hashlib.sha256(json.dumps(list(phase), separators=(",", ":")).encode("utf-8")).hexdigest()


def wrapped_delta_turns(a_rad: float, b_rad: float) -> float:
    a = a_rad / TAU
    b = b_rad / TAU
    return ((b - a + 0.5) % 1.0) - 0.5


@dataclass(frozen=True)
class SemanticAddress36:
    content_id: str
    phase36: tuple[float, ...]
    phase36_sha256: str

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": GENERATOR_SCHEMA,
            "generator_id": GENERATOR_ID,
            "content_id": self.content_id,
            "space": "T^36",
            "coordinate_semantics": "computational_phase_address_radians",
            "coordinate_range": "[0,2pi)",
            "phase36": list(self.phase36),
            "phase36_sha256": self.phase36_sha256,
            "semantic_authority": "TYPED_CONTENT_ID",
            "geometry_role": "COMPUTATIONAL_ADDRESS",
            "promotion_status": "CANDIDATE_CHYBA",
        }

    @property
    def address_id(self) -> str:
        return typed_id("pncs:semantic-address36", self.payload)


@dataclass(frozen=True)
class SemanticTransition36:
    index: int
    source_content_id: str
    target_content_id: str
    source_address_id: str
    target_address_id: str
    tangent36_turns: tuple[float, ...]
    tangent36_sha256: str
    length_turns_l2: float

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TRANSITION_SCHEMA,
            "index": self.index,
            "source_content_id": self.source_content_id,
            "target_content_id": self.target_content_id,
            "source_address_id": self.source_address_id,
            "target_address_id": self.target_address_id,
            "tangent36_turns": list(self.tangent36_turns),
            "tangent36_sha256": self.tangent36_sha256,
            "length_turns_l2": self.length_turns_l2,
            "relation_authority": "TYPED_ORDERED_SEMANTIC_EDGE",
            "geometry_role": "SHORTEST_WRAPPED_T36_REALIZATION",
        }

    @property
    def transition_id(self) -> str:
        return typed_id("pncs:semantic-t36-transition", self.payload)


@dataclass(frozen=True)
class SemanticTrajectory36:
    ordered_semantic_id: str
    addresses: tuple[SemanticAddress36, ...]
    transitions: tuple[SemanticTransition36, ...]

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": TRAJECTORY_SCHEMA,
            "generator_id": GENERATOR_ID,
            "ordered_semantic_id": self.ordered_semantic_id,
            "address_ids": [x.address_id for x in self.addresses],
            "phase36_sha256_sequence": [x.phase36_sha256 for x in self.addresses],
            "transition_ids": [x.transition_id for x in self.transitions],
            "semantic_authority": "TYPED_CONTENT_AND_ORDER",
            "geometry_role": "ORDERED_SHORTEST_WRAPPED_T36_REALIZATION",
            "htri_drive_status": "BLOCKED_MISSING_NATIVE_ORDERED_T36_TO_HTRI_DRIVE_PRIMITIVE",
            "htri_admission_status": "BLOCKED_UPSTREAM_DRIVE",
            "new_pnv_opcodes": 0,
        }

    @property
    def trajectory_id(self) -> str:
        return typed_id("pncs:semantic-trajectory36", self.payload)


def generate_semantic_address(content_id: str) -> SemanticAddress36:
    if not isinstance(content_id, str) or not CONTENT_RE.fullmatch(content_id):
        raise SemanticAddressV31Error("typed semantic-role content ID required")
    raw = hashlib.shake_256(DOMAIN + content_id.encode("ascii")).digest(DIM * 8)
    words = struct.unpack("<" + "Q" * DIM, raw)
    denom = float((1 << 64) - 1)
    phase = tuple((w / denom) * TAU for w in words)
    if len(phase) != DIM or any((not math.isfinite(x) or x < 0.0 or x >= TAU) for x in phase):
        raise SemanticAddressV31Error("generated address violates T36 range")
    return SemanticAddress36(content_id, phase, phase_sha(phase))


def transition(index: int, source: SemanticAddress36, target: SemanticAddress36) -> SemanticTransition36:
    t = tuple(wrapped_delta_turns(a, b) for a, b in zip(source.phase36, target.phase36))
    th = hashlib.sha256(json.dumps(list(t), separators=(",", ":")).encode("utf-8")).hexdigest()
    length = math.sqrt(sum(x * x for x in t))
    return SemanticTransition36(
        int(index), source.content_id, target.content_id,
        source.address_id, target.address_id, t, th, length,
    )


def build_semantic_trajectory(ordered_semantic_id: str, content_ids: Sequence[str]) -> SemanticTrajectory36:
    ids = tuple(str(x) for x in content_ids)
    if len(ids) < 2 or len(set(ids)) != len(ids):
        raise SemanticAddressV31Error("at least two distinct typed semantic-role content IDs required")
    addresses = tuple(generate_semantic_address(x) for x in ids)
    transitions = tuple(transition(i, addresses[i], addresses[i + 1]) for i in range(len(addresses) - 1))
    return SemanticTrajectory36(ordered_semantic_id, addresses, transitions)
