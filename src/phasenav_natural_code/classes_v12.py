from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Iterable, Mapping, Sequence

from .definitions_v11 import DefinitionContent


class ClassV12Error(ValueError):
    pass


_ALIAS_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_CONTENT_SCHEMA = "PNCS_CLASS_CONTENT_V1"
_RECORD_SCHEMA = "PNCS_CLASS_RECORD_V1"
_DEF_PREFIX = "pncs:def:sha256:"
_CLASS_PREFIX = "pncs:class:sha256:"


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ClassV12Error(f"unsupported canonical value type: {type(value).__name__}")


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(_jsonable(dict(payload)), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_id(prefix: str, payload: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _validate_alias(alias: str) -> str:
    if not isinstance(alias, str) or not _ALIAS_RE.fullmatch(alias):
        raise ClassV12Error("class alias must match ^[a-z][a-z0-9_.:-]*$")
    return alias


def _validate_definition_ids(definition_ids: Sequence[str]) -> tuple[str, ...]:
    ids = tuple(str(x) for x in definition_ids)
    if not ids:
        raise ClassV12Error("class requires at least one definition content ID")
    bad = [x for x in ids if not x.startswith(_DEF_PREFIX) or len(x) != len(_DEF_PREFIX) + 64]
    if bad:
        raise ClassV12Error(f"invalid definition content ID(s): {bad}")
    return ids


@dataclass(frozen=True)
class ClassContent:
    definition_ids: tuple[str, ...]
    path_mode: str = "ORDERED_COMPOSITION"

    def __post_init__(self) -> None:
        object.__setattr__(self, "definition_ids", _validate_definition_ids(self.definition_ids))
        if self.path_mode != "ORDERED_COMPOSITION":
            raise ClassV12Error("v0.12 supports ORDERED_COMPOSITION class paths only")

    @property
    def semantic_payload(self) -> dict[str, object]:
        # Deliberately reference definition identities only. No definition graph is copied here.
        return {
            "schema": _CONTENT_SCHEMA,
            "level": "CLASS",
            "path_mode": self.path_mode,
            "definition_ids": list(self.definition_ids),
        }

    @property
    def content_id(self) -> str:
        return _sha256_id("pncs:class", self.semantic_payload)

    @property
    def short_id(self) -> str:
        return self.content_id.rsplit(":", 1)[-1][:16]

    @property
    def native_root_id(self) -> str:
        return f"C.{self.short_id}.ROOT"

    @property
    def level(self) -> str:
        return "CLASS"


@dataclass(frozen=True)
class ClassRecord:
    alias: str
    content: ClassContent
    provenance: tuple[str, ...] = ()
    epistemic_operator: str = "CHYBA"
    canon_allowed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "alias", _validate_alias(self.alias))
        if self.epistemic_operator != "CHYBA":
            raise ClassV12Error("v0.12 class records must remain CHYBA")
        if self.canon_allowed:
            raise ClassV12Error("v0.12 cannot self-promote class records to canon")
        for item in self.provenance:
            if not isinstance(item, str) or not item:
                raise ClassV12Error("provenance entries must be non-empty strings")

    @property
    def record_payload(self) -> dict[str, object]:
        return {
            "schema": _RECORD_SCHEMA,
            "alias": self.alias,
            "content_id": self.content.content_id,
            "definition_ids": list(self.content.definition_ids),
            "provenance": list(self.provenance),
            "epistemic_operator": self.epistemic_operator,
            "canon_allowed": self.canon_allowed,
        }

    @property
    def record_id(self) -> str:
        return _sha256_id("pncs:class-record", self.record_payload)

    def to_json_record(self) -> dict[str, object]:
        return {**self.record_payload, "record_id": self.record_id, "content": self.content.semantic_payload}


class ClassRegistry:
    def __init__(self, definitions: Mapping[str, DefinitionContent]) -> None:
        self._definitions = dict(definitions)
        self._by_alias: dict[str, ClassRecord] = {}
        self._by_content: dict[str, ClassContent] = {}

    def register(self, record: ClassRecord) -> ClassRecord:
        if record.alias in self._by_alias:
            raise ClassV12Error(f"duplicate class alias: {record.alias}")
        missing = [d for d in record.content.definition_ids if d not in self._definitions]
        if missing:
            raise ClassV12Error(f"class definition dependency not registered: {missing}")
        cid = record.content.content_id
        prior = self._by_content.get(cid)
        if prior is not None and prior.semantic_payload != record.content.semantic_payload:
            raise ClassV12Error("class content-address collision with non-identical payload")
        self._by_alias[record.alias] = record
        self._by_content.setdefault(cid, record.content)
        return record

    def resolve_alias(self, alias: str) -> str:
        alias = _validate_alias(alias)
        try:
            return self._by_alias[alias].content.content_id
        except KeyError as exc:
            raise ClassV12Error(f"unknown class alias: {alias}") from exc

    def content(self, content_id: str) -> ClassContent:
        try:
            return self._by_content[content_id]
        except KeyError as exc:
            raise ClassV12Error(f"unknown class content id: {content_id}") from exc

    def record(self, alias: str) -> ClassRecord:
        alias = _validate_alias(alias)
        try:
            return self._by_alias[alias]
        except KeyError as exc:
            raise ClassV12Error(f"unknown class alias: {alias}") from exc

    def aliases_for(self, content_id: str) -> tuple[str, ...]:
        if content_id not in self._by_content:
            raise ClassV12Error(f"unknown class content id: {content_id}")
        return tuple(sorted(a for a, r in self._by_alias.items() if r.content.content_id == content_id))

    def expand_definitions(self, alias_or_content_id: str) -> tuple[str, ...]:
        content = self.content(alias_or_content_id) if alias_or_content_id.startswith(_CLASS_PREFIX) else self.record(alias_or_content_id).content
        return content.definition_ids

    def expand_leaves(self, alias_or_content_id: str) -> tuple[str, ...]:
        ids = self.expand_definitions(alias_or_content_id)
        out: list[str] = []
        for i, definition_id in enumerate(ids):
            if i:
                out.append("ORDER")
            out.extend(self._definitions[definition_id].leaf_path)
            if i:
                out.append("COMPOSITION")
        return tuple(out)

    def jsonl(self) -> str:
        rows = [self._by_alias[k].to_json_record() for k in sorted(self._by_alias)]
        return "\n".join(_canonical_json(r) for r in rows) + ("\n" if rows else "")


def define_class(alias: str, definition_ids: Iterable[str], *, provenance: Iterable[str] = ()) -> ClassRecord:
    return ClassRecord(alias=alias, content=ClassContent(tuple(definition_ids)), provenance=tuple(provenance))


def verify_serialized_class_record(record: Mapping[str, object]) -> None:
    if record.get("schema") != _RECORD_SCHEMA:
        raise ClassV12Error("unsupported class record schema")
    content = record.get("content")
    if not isinstance(content, Mapping) or content.get("schema") != _CONTENT_SCHEMA:
        raise ClassV12Error("serialized class record missing content payload")
    definition_ids = content.get("definition_ids")
    if not isinstance(definition_ids, list):
        raise ClassV12Error("serialized class record missing definition IDs")
    rebuilt = ClassContent(tuple(str(x) for x in definition_ids), path_mode=str(content.get("path_mode")))
    if rebuilt.content_id != record.get("content_id"):
        raise ClassV12Error("class content digest mismatch")
    payload = {
        "schema": _RECORD_SCHEMA,
        "alias": record.get("alias"),
        "content_id": record.get("content_id"),
        "definition_ids": record.get("definition_ids"),
        "provenance": record.get("provenance"),
        "epistemic_operator": record.get("epistemic_operator"),
        "canon_allowed": record.get("canon_allowed"),
    }
    if _sha256_id("pncs:class-record", payload) != record.get("record_id"):
        raise ClassV12Error("class record digest mismatch")
