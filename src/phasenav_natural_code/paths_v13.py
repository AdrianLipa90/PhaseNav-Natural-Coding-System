from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Iterable, Mapping, Sequence

from .classes_v12 import ClassRegistry


class PathV13Error(ValueError):
    pass


_ALIAS_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_CLASS_PREFIX = "pncs:class:sha256:"
_FILE_PREFIX = "pncs:file:sha256:"
_CLUSTER_PREFIX = "pncs:cluster:sha256:"
_FILE_CONTENT_SCHEMA = "PNCS_FILE_CONTENT_V1"
_FILE_RECORD_SCHEMA = "PNCS_FILE_RECORD_V1"
_CLUSTER_CONTENT_SCHEMA = "PNCS_CLUSTER_CONTENT_V1"
_CLUSTER_RECORD_SCHEMA = "PNCS_CLUSTER_RECORD_V1"


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise PathV13Error(f"unsupported canonical value type: {type(value).__name__}")


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(_jsonable(dict(payload)), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_id(prefix: str, payload: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _validate_alias(alias: str, level: str) -> str:
    if not isinstance(alias, str) or not _ALIAS_RE.fullmatch(alias):
        raise PathV13Error(f"{level.lower()} alias must match ^[a-z][a-z0-9_.:-]*$")
    return alias


def _validate_content_ids(values: Sequence[str], prefix: str, level: str) -> tuple[str, ...]:
    ids = tuple(str(x) for x in values)
    if not ids:
        raise PathV13Error(f"{level.lower()} requires at least one child content ID")
    bad = [x for x in ids if not x.startswith(prefix) or len(x) != len(prefix) + 64]
    if bad:
        raise PathV13Error(f"invalid {level.lower()} child content ID(s): {bad}")
    return ids


def _validate_projection_path(path: str | None) -> str | None:
    if path is None:
        return None
    if not isinstance(path, str) or not path.strip():
        raise PathV13Error("projection_path must be a non-empty string or None")
    if "\x00" in path:
        raise PathV13Error("projection_path contains NUL")
    return path


@dataclass(frozen=True)
class FileContent:
    class_ids: tuple[str, ...]
    path_mode: str = "ORDERED_COMPOSITION"

    def __post_init__(self) -> None:
        object.__setattr__(self, "class_ids", _validate_content_ids(self.class_ids, _CLASS_PREFIX, "FILE"))
        if self.path_mode != "ORDERED_COMPOSITION":
            raise PathV13Error("v0.13 supports ORDERED_COMPOSITION file paths only")

    @property
    def semantic_payload(self) -> dict[str, object]:
        return {
            "schema": _FILE_CONTENT_SCHEMA,
            "level": "FILE",
            "path_mode": self.path_mode,
            "class_ids": list(self.class_ids),
        }

    @property
    def content_id(self) -> str:
        return _sha256_id("pncs:file", self.semantic_payload)

    @property
    def short_id(self) -> str:
        return self.content_id.rsplit(":", 1)[-1][:16]

    @property
    def native_root_id(self) -> str:
        return f"F.{self.short_id}.ROOT"


@dataclass(frozen=True)
class FileRecord:
    alias: str
    content: FileContent
    provenance: tuple[str, ...] = ()
    projection_path: str | None = None
    epistemic_operator: str = "CHYBA"
    canon_allowed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "alias", _validate_alias(self.alias, "FILE"))
        object.__setattr__(self, "projection_path", _validate_projection_path(self.projection_path))
        if self.epistemic_operator != "CHYBA":
            raise PathV13Error("v0.13 file records must remain CHYBA")
        if self.canon_allowed:
            raise PathV13Error("v0.13 cannot self-promote file records to canon")
        for item in self.provenance:
            if not isinstance(item, str) or not item:
                raise PathV13Error("provenance entries must be non-empty strings")

    @property
    def record_payload(self) -> dict[str, object]:
        return {
            "schema": _FILE_RECORD_SCHEMA,
            "alias": self.alias,
            "content_id": self.content.content_id,
            "class_ids": list(self.content.class_ids),
            "projection_path": self.projection_path,
            "provenance": list(self.provenance),
            "epistemic_operator": self.epistemic_operator,
            "canon_allowed": self.canon_allowed,
        }

    @property
    def record_id(self) -> str:
        return _sha256_id("pncs:file-record", self.record_payload)

    def to_json_record(self) -> dict[str, object]:
        return {**self.record_payload, "record_id": self.record_id, "content": self.content.semantic_payload}


class FileRegistry:
    def __init__(self, classes: ClassRegistry) -> None:
        self._classes = classes
        self._by_alias: dict[str, FileRecord] = {}
        self._by_content: dict[str, FileContent] = {}

    def register(self, record: FileRecord) -> FileRecord:
        if record.alias in self._by_alias:
            raise PathV13Error(f"duplicate file alias: {record.alias}")
        missing: list[str] = []
        for cid in record.content.class_ids:
            try:
                self._classes.content(cid)
            except Exception:
                missing.append(cid)
        if missing:
            raise PathV13Error(f"file class dependency not registered: {missing}")
        cid = record.content.content_id
        prior = self._by_content.get(cid)
        if prior is not None and prior.semantic_payload != record.content.semantic_payload:
            raise PathV13Error("file content-address collision with non-identical payload")
        self._by_alias[record.alias] = record
        self._by_content.setdefault(cid, record.content)
        return record

    def resolve_alias(self, alias: str) -> str:
        alias = _validate_alias(alias, "FILE")
        try:
            return self._by_alias[alias].content.content_id
        except KeyError as exc:
            raise PathV13Error(f"unknown file alias: {alias}") from exc

    def record(self, alias: str) -> FileRecord:
        alias = _validate_alias(alias, "FILE")
        try:
            return self._by_alias[alias]
        except KeyError as exc:
            raise PathV13Error(f"unknown file alias: {alias}") from exc

    def content(self, content_id: str) -> FileContent:
        try:
            return self._by_content[content_id]
        except KeyError as exc:
            raise PathV13Error(f"unknown file content id: {content_id}") from exc

    def aliases_for(self, content_id: str) -> tuple[str, ...]:
        if content_id not in self._by_content:
            raise PathV13Error(f"unknown file content id: {content_id}")
        return tuple(sorted(a for a, r in self._by_alias.items() if r.content.content_id == content_id))

    def expand_classes(self, alias_or_content_id: str) -> tuple[str, ...]:
        content = self.content(alias_or_content_id) if alias_or_content_id.startswith(_FILE_PREFIX) else self.record(alias_or_content_id).content
        return content.class_ids

    def expand_definitions(self, alias_or_content_id: str) -> tuple[str, ...]:
        out: list[str] = []
        for class_id in self.expand_classes(alias_or_content_id):
            out.extend(self._classes.expand_definitions(class_id))
        return tuple(out)

    def expand_leaves(self, alias_or_content_id: str) -> tuple[str, ...]:
        ids = self.expand_classes(alias_or_content_id)
        out: list[str] = []
        for i, class_id in enumerate(ids):
            if i:
                out.append("ORDER")
            out.extend(self._classes.expand_leaves(class_id))
            if i:
                out.append("COMPOSITION")
        return tuple(out)

    def jsonl(self) -> str:
        rows = [self._by_alias[k].to_json_record() for k in sorted(self._by_alias)]
        return "\n".join(_canonical_json(r) for r in rows) + ("\n" if rows else "")


@dataclass(frozen=True)
class ClusterContent:
    file_ids: tuple[str, ...]
    path_mode: str = "ORDERED_COMPOSITION"

    def __post_init__(self) -> None:
        object.__setattr__(self, "file_ids", _validate_content_ids(self.file_ids, _FILE_PREFIX, "CLUSTER"))
        if self.path_mode != "ORDERED_COMPOSITION":
            raise PathV13Error("v0.13 supports ORDERED_COMPOSITION cluster paths only")

    @property
    def semantic_payload(self) -> dict[str, object]:
        return {
            "schema": _CLUSTER_CONTENT_SCHEMA,
            "level": "CLUSTER",
            "path_mode": self.path_mode,
            "file_ids": list(self.file_ids),
        }

    @property
    def content_id(self) -> str:
        return _sha256_id("pncs:cluster", self.semantic_payload)

    @property
    def short_id(self) -> str:
        return self.content_id.rsplit(":", 1)[-1][:16]

    @property
    def native_root_id(self) -> str:
        return f"CL.{self.short_id}.ROOT"


@dataclass(frozen=True)
class ClusterRecord:
    alias: str
    content: ClusterContent
    provenance: tuple[str, ...] = ()
    projection_path: str | None = None
    epistemic_operator: str = "CHYBA"
    canon_allowed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "alias", _validate_alias(self.alias, "CLUSTER"))
        object.__setattr__(self, "projection_path", _validate_projection_path(self.projection_path))
        if self.epistemic_operator != "CHYBA":
            raise PathV13Error("v0.13 cluster records must remain CHYBA")
        if self.canon_allowed:
            raise PathV13Error("v0.13 cannot self-promote cluster records to canon")
        for item in self.provenance:
            if not isinstance(item, str) or not item:
                raise PathV13Error("provenance entries must be non-empty strings")

    @property
    def record_payload(self) -> dict[str, object]:
        return {
            "schema": _CLUSTER_RECORD_SCHEMA,
            "alias": self.alias,
            "content_id": self.content.content_id,
            "file_ids": list(self.content.file_ids),
            "projection_path": self.projection_path,
            "provenance": list(self.provenance),
            "epistemic_operator": self.epistemic_operator,
            "canon_allowed": self.canon_allowed,
        }

    @property
    def record_id(self) -> str:
        return _sha256_id("pncs:cluster-record", self.record_payload)

    def to_json_record(self) -> dict[str, object]:
        return {**self.record_payload, "record_id": self.record_id, "content": self.content.semantic_payload}


class ClusterRegistry:
    def __init__(self, files: FileRegistry) -> None:
        self._files = files
        self._by_alias: dict[str, ClusterRecord] = {}
        self._by_content: dict[str, ClusterContent] = {}

    def register(self, record: ClusterRecord) -> ClusterRecord:
        if record.alias in self._by_alias:
            raise PathV13Error(f"duplicate cluster alias: {record.alias}")
        missing: list[str] = []
        for fid in record.content.file_ids:
            try:
                self._files.content(fid)
            except Exception:
                missing.append(fid)
        if missing:
            raise PathV13Error(f"cluster file dependency not registered: {missing}")
        cid = record.content.content_id
        prior = self._by_content.get(cid)
        if prior is not None and prior.semantic_payload != record.content.semantic_payload:
            raise PathV13Error("cluster content-address collision with non-identical payload")
        self._by_alias[record.alias] = record
        self._by_content.setdefault(cid, record.content)
        return record

    def resolve_alias(self, alias: str) -> str:
        alias = _validate_alias(alias, "CLUSTER")
        try:
            return self._by_alias[alias].content.content_id
        except KeyError as exc:
            raise PathV13Error(f"unknown cluster alias: {alias}") from exc

    def record(self, alias: str) -> ClusterRecord:
        alias = _validate_alias(alias, "CLUSTER")
        try:
            return self._by_alias[alias]
        except KeyError as exc:
            raise PathV13Error(f"unknown cluster alias: {alias}") from exc

    def content(self, content_id: str) -> ClusterContent:
        try:
            return self._by_content[content_id]
        except KeyError as exc:
            raise PathV13Error(f"unknown cluster content id: {content_id}") from exc

    def aliases_for(self, content_id: str) -> tuple[str, ...]:
        if content_id not in self._by_content:
            raise PathV13Error(f"unknown cluster content id: {content_id}")
        return tuple(sorted(a for a, r in self._by_alias.items() if r.content.content_id == content_id))

    def expand_files(self, alias_or_content_id: str) -> tuple[str, ...]:
        content = self.content(alias_or_content_id) if alias_or_content_id.startswith(_CLUSTER_PREFIX) else self.record(alias_or_content_id).content
        return content.file_ids

    def expand_classes(self, alias_or_content_id: str) -> tuple[str, ...]:
        out: list[str] = []
        for file_id in self.expand_files(alias_or_content_id):
            out.extend(self._files.expand_classes(file_id))
        return tuple(out)

    def expand_definitions(self, alias_or_content_id: str) -> tuple[str, ...]:
        out: list[str] = []
        for file_id in self.expand_files(alias_or_content_id):
            out.extend(self._files.expand_definitions(file_id))
        return tuple(out)

    def expand_leaves(self, alias_or_content_id: str) -> tuple[str, ...]:
        ids = self.expand_files(alias_or_content_id)
        out: list[str] = []
        for i, file_id in enumerate(ids):
            if i:
                out.append("ORDER")
            out.extend(self._files.expand_leaves(file_id))
            if i:
                out.append("COMPOSITION")
        return tuple(out)

    def jsonl(self) -> str:
        rows = [self._by_alias[k].to_json_record() for k in sorted(self._by_alias)]
        return "\n".join(_canonical_json(r) for r in rows) + ("\n" if rows else "")


def define_file(alias: str, class_ids: Iterable[str], *, provenance: Iterable[str] = (), projection_path: str | None = None) -> FileRecord:
    return FileRecord(alias=alias, content=FileContent(tuple(class_ids)), provenance=tuple(provenance), projection_path=projection_path)


def define_cluster(alias: str, file_ids: Iterable[str], *, provenance: Iterable[str] = (), projection_path: str | None = None) -> ClusterRecord:
    return ClusterRecord(alias=alias, content=ClusterContent(tuple(file_ids)), provenance=tuple(provenance), projection_path=projection_path)


def verify_serialized_file_record(record: Mapping[str, object]) -> None:
    if record.get("schema") != _FILE_RECORD_SCHEMA:
        raise PathV13Error("unsupported file record schema")
    content = record.get("content")
    if not isinstance(content, Mapping) or content.get("schema") != _FILE_CONTENT_SCHEMA:
        raise PathV13Error("serialized file record missing content payload")
    class_ids = content.get("class_ids")
    if not isinstance(class_ids, list):
        raise PathV13Error("serialized file record missing class IDs")
    rebuilt = FileContent(tuple(str(x) for x in class_ids), path_mode=str(content.get("path_mode")))
    if rebuilt.content_id != record.get("content_id"):
        raise PathV13Error("file content digest mismatch")
    payload = {
        "schema": _FILE_RECORD_SCHEMA,
        "alias": record.get("alias"),
        "content_id": record.get("content_id"),
        "class_ids": record.get("class_ids"),
        "projection_path": record.get("projection_path"),
        "provenance": record.get("provenance"),
        "epistemic_operator": record.get("epistemic_operator"),
        "canon_allowed": record.get("canon_allowed"),
    }
    if _sha256_id("pncs:file-record", payload) != record.get("record_id"):
        raise PathV13Error("file record digest mismatch")


def verify_serialized_cluster_record(record: Mapping[str, object]) -> None:
    if record.get("schema") != _CLUSTER_RECORD_SCHEMA:
        raise PathV13Error("unsupported cluster record schema")
    content = record.get("content")
    if not isinstance(content, Mapping) or content.get("schema") != _CLUSTER_CONTENT_SCHEMA:
        raise PathV13Error("serialized cluster record missing content payload")
    file_ids = content.get("file_ids")
    if not isinstance(file_ids, list):
        raise PathV13Error("serialized cluster record missing file IDs")
    rebuilt = ClusterContent(tuple(str(x) for x in file_ids), path_mode=str(content.get("path_mode")))
    if rebuilt.content_id != record.get("content_id"):
        raise PathV13Error("cluster content digest mismatch")
    payload = {
        "schema": _CLUSTER_RECORD_SCHEMA,
        "alias": record.get("alias"),
        "content_id": record.get("content_id"),
        "file_ids": record.get("file_ids"),
        "projection_path": record.get("projection_path"),
        "provenance": record.get("provenance"),
        "epistemic_operator": record.get("epistemic_operator"),
        "canon_allowed": record.get("canon_allowed"),
    }
    if _sha256_id("pncs:cluster-record", payload) != record.get("record_id"):
        raise PathV13Error("cluster record digest mismatch")
