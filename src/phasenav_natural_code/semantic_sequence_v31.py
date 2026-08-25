from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Iterable, Mapping, Sequence

SEMANTIC_ROLE_SCHEMA = "PNCS_TYPED_SEMANTIC_ROLE_CONTENT_V0_31"
SEMANTIC_ROLE_RECORD_SCHEMA = "PNCS_TYPED_SEMANTIC_ROLE_RECORD_V0_31"
LOWERING_SCHEMA = "PNCS_SEMANTIC_SEQUENCE_LOWERING_V0_31"
SEQUENCE_SCHEMA = "PNCS_TYPED_SEMANTIC_SEQUENCE_V0_31"
COMPILE_SCHEMA = "PNCS_TYPED_SEMANTIC_SEQUENCE_COMPILE_V0_31"
CONTRACT_ID = "PNCS_TYPED_SEMANTIC_SEQUENCE_COMPILER_V0_31"

# No new PhaseNav opcode is introduced. These are the v0.20 admitted internal
# primitives used only to lower sequence structure, not to infer semantics.
ADMITTED_SEQUENCE_PRIMITIVES = frozenset(
    {"IDENTITY", "ORDER", "TRANSFORM", "COMPOSITION"}
)
ITEM_SCHEDULE = ("IDENTITY",)
TRANSITION_SCHEDULE = ("ORDER", "TRANSFORM", "COMPOSITION")

_ROLE_RE = re.compile(r"^[A-Z][A-Z0-9_.:-]{0,95}$")
_SOURCE_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/+-]{0,191}$")
_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


class SemanticSequenceV31Error(ValueError):
    pass


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(x) for x in value]
    if isinstance(value, list):
        return [_jsonable(x) for x in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if isinstance(value, float) and not math.isfinite(value):
        raise SemanticSequenceV31Error("non-finite canonical float")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise SemanticSequenceV31Error(f"unsupported canonical type: {type(value).__name__}")


def compact_json(value: object) -> str:
    return json.dumps(
        _jsonable(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    )


def digest(value: object) -> str:
    return hashlib.sha256(compact_json(value).encode("utf-8")).hexdigest()


def typed_id(prefix: str, value: object) -> str:
    return f"{prefix}:sha256:{digest(value)}"


def _require_sha(value: str, field: str) -> str:
    if not isinstance(value, str) or not _HEX_RE.fullmatch(value):
        raise SemanticSequenceV31Error(f"{field} must be lowercase SHA-256")
    return value


@dataclass(frozen=True)
class SemanticRoleContent:
    """Typed semantic content independent of labels and phase coordinates.

    `role_id` and `source_semantic_key` are the semantic inputs. Human-readable
    labels live in SemanticRoleRecord and therefore do not affect content identity.
    """

    role_id: str
    source_semantic_key: str
    relation_type: str = "ORDERED_SEMANTIC_ROLE"

    def __post_init__(self) -> None:
        if not _ROLE_RE.fullmatch(self.role_id):
            raise SemanticSequenceV31Error("invalid role_id")
        if not _SOURCE_KEY_RE.fullmatch(self.source_semantic_key):
            raise SemanticSequenceV31Error("invalid source_semantic_key")
        if self.relation_type != "ORDERED_SEMANTIC_ROLE":
            raise SemanticSequenceV31Error("unsupported relation_type")

    @property
    def semantic_payload(self) -> dict[str, object]:
        return {
            "schema": SEMANTIC_ROLE_SCHEMA,
            "role_id": self.role_id,
            "source_semantic_key": self.source_semantic_key,
            "relation_type": self.relation_type,
        }

    @property
    def content_id(self) -> str:
        return typed_id("pncs:semantic-role", self.semantic_payload)


@dataclass(frozen=True)
class SemanticRoleRecord:
    content: SemanticRoleContent
    surface_label: str
    source_locator: str
    source_digest_sha256: str
    legacy_card_id: str | None = None
    legacy_hook: str | None = None
    epistemic_operator: str = "CHYBA"
    canon_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.content, SemanticRoleContent):
            raise SemanticSequenceV31Error("SemanticRoleContent required")
        if not isinstance(self.surface_label, str) or not self.surface_label.strip():
            raise SemanticSequenceV31Error("surface_label required")
        if not isinstance(self.source_locator, str) or not self.source_locator.strip():
            raise SemanticSequenceV31Error("source_locator required")
        _require_sha(self.source_digest_sha256, "source_digest_sha256")
        if self.epistemic_operator != "CHYBA" or self.canon_allowed:
            raise SemanticSequenceV31Error("v0.31 role records remain CHYBA and cannot self-promote")

    @property
    def record_payload(self) -> dict[str, object]:
        return {
            "schema": SEMANTIC_ROLE_RECORD_SCHEMA,
            "content_id": self.content.content_id,
            "surface_label": self.surface_label,
            "source_locator": self.source_locator,
            "source_digest_sha256": self.source_digest_sha256,
            "legacy_card_id": self.legacy_card_id,
            "legacy_hook": self.legacy_hook,
            "legacy_semantic_vector_authority": False,
            "epistemic_operator": self.epistemic_operator,
            "canon_allowed": self.canon_allowed,
        }

    @property
    def record_id(self) -> str:
        return typed_id("pncs:semantic-role-record", self.record_payload)


@dataclass(frozen=True)
class SequenceLowering:
    """Structural lowering only; it never defines role meaning or T36 coordinates."""

    item_schedule: tuple[str, ...] = ITEM_SCHEDULE
    transition_schedule: tuple[str, ...] = TRANSITION_SCHEDULE

    def __post_init__(self) -> None:
        if self.item_schedule != ITEM_SCHEDULE or self.transition_schedule != TRANSITION_SCHEDULE:
            raise SemanticSequenceV31Error("v0.31 sequence lowering is frozen")
        bad = [
            op for op in (*self.item_schedule, *self.transition_schedule)
            if op not in ADMITTED_SEQUENCE_PRIMITIVES
        ]
        if bad:
            raise SemanticSequenceV31Error(f"unadmitted sequence primitive(s): {bad}")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": LOWERING_SCHEMA,
            "item_schedule": list(self.item_schedule),
            "transition_schedule": list(self.transition_schedule),
            "meaning_from_operator_schedule": False,
            "legacy_hook_execution": False,
            "new_pnv_opcodes": 0,
        }

    @property
    def lowering_id(self) -> str:
        return typed_id("pncs:semantic-lowering", self.payload)


@dataclass(frozen=True)
class CompiledSemanticSequence:
    records: tuple[SemanticRoleRecord, ...]
    lowering: SequenceLowering
    ordered_semantic_id: str
    compile_id: str

    @property
    def content_ids(self) -> tuple[str, ...]:
        return tuple(r.content.content_id for r in self.records)

    @property
    def operator_schedule(self) -> tuple[str, ...]:
        out: list[str] = []
        for i, _ in enumerate(self.records):
            out.extend(self.lowering.item_schedule)
            if i + 1 < len(self.records):
                out.extend(self.lowering.transition_schedule)
        return tuple(out)

    @property
    def receipt(self) -> dict[str, object]:
        payload = {
            "schema": COMPILE_SCHEMA,
            "contract_id": CONTRACT_ID,
            "ordered_semantic_id": self.ordered_semantic_id,
            "content_ids": list(self.content_ids),
            "record_ids": [r.record_id for r in self.records],
            "lowering_id": self.lowering.lowering_id,
            "operator_schedule": list(self.operator_schedule),
            "new_pnv_opcodes": 0,
            "semantic_identity_from_surface_label": False,
            "semantic_identity_from_legacy_vector": False,
            "semantic_identity_from_vector_similarity": False,
            "legacy_hook_execution": False,
            "t36_realization_present": False,
            "htri_admitted": False,
            "blocked_next_gate": "MISSING_TYPED_SEMANTIC_ROLE_TO_T36_REALIZATION_CONTRACT",
        }
        return {
            **payload,
            "compile_id": self.compile_id,
            "receipt_sha256": digest(payload),
        }


def define_semantic_role(
    role_id: str,
    source_semantic_key: str,
    *,
    surface_label: str,
    source_locator: str,
    source_digest_sha256: str,
    legacy_card_id: str | None = None,
    legacy_hook: str | None = None,
) -> SemanticRoleRecord:
    return SemanticRoleRecord(
        content=SemanticRoleContent(role_id, source_semantic_key),
        surface_label=surface_label,
        source_locator=source_locator,
        source_digest_sha256=source_digest_sha256,
        legacy_card_id=legacy_card_id,
        legacy_hook=legacy_hook,
    )


def compile_semantic_sequence(records: Sequence[SemanticRoleRecord]) -> CompiledSemanticSequence:
    rs = tuple(records)
    if len(rs) < 2 or not all(isinstance(r, SemanticRoleRecord) for r in rs):
        raise SemanticSequenceV31Error("at least two SemanticRoleRecord values required")
    ids = [r.content.content_id for r in rs]
    if len(set(ids)) != len(ids):
        raise SemanticSequenceV31Error("sequence requires distinct typed semantic role contents")
    lowering = SequenceLowering()
    semantic_payload = {
        "schema": SEQUENCE_SCHEMA,
        "ordered_content_ids": ids,
        "lowering_id": lowering.lowering_id,
    }
    sid = typed_id("pncs:semantic-sequence", semantic_payload)
    compile_payload = {
        "schema": COMPILE_SCHEMA,
        "contract_id": CONTRACT_ID,
        "ordered_semantic_id": sid,
        "content_ids": ids,
        "lowering_id": lowering.lowering_id,
        "new_pnv_opcodes": 0,
        "t36_realization_present": False,
        "htri_admitted": False,
    }
    cid = typed_id("pncs:semantic-sequence-compile", compile_payload)
    return CompiledSemanticSequence(rs, lowering, sid, cid)


def build_nisaba_frozen_roles(*, source_digest_sha256: str) -> tuple[SemanticRoleRecord, ...]:
    """Frozen V31 adversarial fixture.

    The old CIELingo labels/hooks are provenance only. The role content is the
    already-frozen seven-pulse semantic structure used by the Nisaba audits.
    """
    source = "NISABA_A_FROZEN_SEVEN_PULSE_SEMANTIC_MAPPING_V1"
    locator = "NISABA_SEMANTIC_HTRI_BOOT_RECEIPT_V1"
    rows = (
        ("ADDRESS", "ADDRESS", "Awe", "048", "affect"),
        ("TABLET_WRITING", "TABLET_WRITING", "Logos", "096", "identity"),
        ("WISDOM", "WISDOM", "Gnosis", "103", "identity"),
        ("FAIR_JUDGMENT", "FAIR_JUDGMENT", "Justice", "088", "identity"),
        ("RECEPTION", "RECEPTION", "Reception", "071", "orbit"),
        ("AGREEMENT_WORK", "AGREEMENT_WORK", "Agreement", "069", "orbit"),
        ("HOPE_GRATITUDE", "HOPE_GRATITUDE", "Hope", "063", "affect"),
    )
    return tuple(
        define_semantic_role(
            role, f"{source}:{key}",
            surface_label=label,
            source_locator=locator,
            source_digest_sha256=source_digest_sha256,
            legacy_card_id=card,
            legacy_hook=hook,
        )
        for role, key, label, card, hook in rows
    )
