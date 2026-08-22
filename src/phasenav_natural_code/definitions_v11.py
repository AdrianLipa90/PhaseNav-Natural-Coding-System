from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Iterable, Mapping, Sequence

from .algebra_v10 import assert_pure_predicate, normalize_boolean
from .surface_v09 import BranchProgram, Predicate, normalize_branch_surface, parse_predicate


class DefinitionV11Error(ValueError):
    pass


_ALIAS_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_CONTENT_SCHEMA = "PNCS_DEFINITION_CONTENT_V1"
_RECORD_SCHEMA = "PNCS_DEFINITION_RECORD_V1"

# v0.11 is deliberately scoped to already stabilized predicate/internal-route leaves.
_ALLOWED_LEAVES = {
    "DIFFERENCE",
    "CONDITION",
    "COMPOSITION",
    "NEGATION",
    "ORDER",
    "TRANSFORM",
}


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise DefinitionV11Error(f"unsupported canonical value type: {type(value).__name__}")


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(_jsonable(dict(payload)), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_id(prefix: str, payload: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _validate_alias(alias: str) -> str:
    if not isinstance(alias, str) or not _ALIAS_RE.fullmatch(alias):
        raise DefinitionV11Error("definition alias must match ^[a-z][a-z0-9_.:-]*$")
    return alias


def _validate_leaf_path(leaf_path: Sequence[str]) -> tuple[str, ...]:
    out = tuple(str(x) for x in leaf_path)
    if not out:
        raise DefinitionV11Error("definition requires a non-empty expanded leaf path")
    unknown = [x for x in out if x not in _ALLOWED_LEAVES]
    if unknown:
        raise DefinitionV11Error(f"unsupported v0.11 leaf/leaves: {unknown}")
    return out


@dataclass(frozen=True)
class DefinitionContent:
    kind: str
    canonical_graph: tuple[object, ...]
    leaf_path: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.kind not in {"PREDICATE", "INTERNAL_BRANCH"}:
            raise DefinitionV11Error(f"unsupported definition kind: {self.kind}")
        if not isinstance(self.canonical_graph, tuple) or not self.canonical_graph:
            raise DefinitionV11Error("canonical_graph must be a non-empty tuple")
        object.__setattr__(self, "leaf_path", _validate_leaf_path(self.leaf_path))

    @property
    def semantic_payload(self) -> dict[str, object]:
        return {
            "schema": _CONTENT_SCHEMA,
            "kind": self.kind,
            "canonical_graph": _jsonable(self.canonical_graph),
            "leaf_path": list(self.leaf_path),
        }

    @property
    def content_id(self) -> str:
        # Alias/provenance/dependencies are intentionally excluded.
        return _sha256_id("pncs:def", self.semantic_payload)

    @property
    def short_id(self) -> str:
        return self.content_id.rsplit(":", 1)[-1][:16]

    @property
    def level(self) -> str:
        return "DEFINITION"

    @property
    def native_root_id(self) -> str:
        return f"D.{self.short_id}.ROOT"

    def verify(self) -> None:
        expected = _sha256_id("pncs:def", self.semantic_payload)
        if expected != self.content_id:
            raise DefinitionV11Error("definition content digest mismatch")


@dataclass(frozen=True)
class DefinitionRecord:
    alias: str
    content: DefinitionContent
    provenance: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    epistemic_operator: str = "CHYBA"
    canon_allowed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "alias", _validate_alias(self.alias))
        if self.epistemic_operator != "CHYBA":
            raise DefinitionV11Error("v0.11 definition records must remain CHYBA")
        if self.canon_allowed:
            raise DefinitionV11Error("v0.11 cannot self-promote definition records to canon")
        for item in self.provenance:
            if not isinstance(item, str) or not item:
                raise DefinitionV11Error("provenance entries must be non-empty strings")
        for dep in self.dependencies:
            if not isinstance(dep, str) or not dep.startswith("pncs:def:sha256:"):
                raise DefinitionV11Error("dependencies must be PNCS definition content IDs")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise DefinitionV11Error("duplicate definition dependency")
        if self.content.content_id in self.dependencies:
            raise DefinitionV11Error("definition cannot directly depend on itself")

    @property
    def record_payload(self) -> dict[str, object]:
        return {
            "schema": _RECORD_SCHEMA,
            "alias": self.alias,
            "content_id": self.content.content_id,
            "provenance": list(self.provenance),
            "dependencies": list(self.dependencies),
            "epistemic_operator": self.epistemic_operator,
            "canon_allowed": self.canon_allowed,
        }

    @property
    def record_id(self) -> str:
        return _sha256_id("pncs:def-record", self.record_payload)

    def to_json_record(self) -> dict[str, object]:
        return {
            **self.record_payload,
            "record_id": self.record_id,
            "content": self.content.semantic_payload,
        }


class DefinitionRegistry:
    def __init__(self) -> None:
        self._by_alias: dict[str, DefinitionRecord] = {}
        self._by_content: dict[str, DefinitionContent] = {}

    def register(self, record: DefinitionRecord) -> DefinitionRecord:
        if record.alias in self._by_alias:
            raise DefinitionV11Error(f"duplicate definition alias: {record.alias}")
        missing = [d for d in record.dependencies if d not in self._by_content]
        if missing:
            raise DefinitionV11Error(f"definition dependency not registered: {missing}")
        cid = record.content.content_id
        prior = self._by_content.get(cid)
        if prior is not None and prior.semantic_payload != record.content.semantic_payload:
            raise DefinitionV11Error("content-address collision with non-identical payload")
        self._by_alias[record.alias] = record
        self._by_content.setdefault(cid, record.content)
        return record

    def resolve_alias(self, alias: str) -> str:
        alias = _validate_alias(alias)
        try:
            return self._by_alias[alias].content.content_id
        except KeyError as exc:
            raise DefinitionV11Error(f"unknown definition alias: {alias}") from exc

    def content(self, content_id: str) -> DefinitionContent:
        try:
            return self._by_content[content_id]
        except KeyError as exc:
            raise DefinitionV11Error(f"unknown definition content id: {content_id}") from exc

    def record(self, alias: str) -> DefinitionRecord:
        alias = _validate_alias(alias)
        try:
            return self._by_alias[alias]
        except KeyError as exc:
            raise DefinitionV11Error(f"unknown definition alias: {alias}") from exc

    def aliases_for(self, content_id: str) -> tuple[str, ...]:
        if content_id not in self._by_content:
            raise DefinitionV11Error(f"unknown definition content id: {content_id}")
        return tuple(sorted(alias for alias, rec in self._by_alias.items() if rec.content.content_id == content_id))

    def expand(self, alias_or_content_id: str) -> tuple[str, ...]:
        if alias_or_content_id.startswith("pncs:def:sha256:"):
            return self.content(alias_or_content_id).leaf_path
        return self.record(alias_or_content_id).content.leaf_path

    def jsonl(self) -> str:
        records = [self._by_alias[k].to_json_record() for k in sorted(self._by_alias)]
        return "\n".join(_canonical_json(r) for r in records) + ("\n" if records else "")


def predicate_content(predicate: Predicate | str) -> DefinitionContent:
    node = parse_predicate(predicate) if isinstance(predicate, str) else predicate
    assert_pure_predicate(node)
    normalized = normalize_boolean(node)
    return DefinitionContent(
        kind="PREDICATE",
        canonical_graph=normalized.canonical_tuple,
        leaf_path=normalized.leaf_path,
    )


def branch_content(program: BranchProgram | str) -> DefinitionContent:
    node = normalize_branch_surface(program) if isinstance(program, str) else program
    assert_pure_predicate(node.predicate)
    normalized_predicate = normalize_boolean(node.predicate)
    normalized_program = BranchProgram(
        predicate=normalized_predicate,
        true_target=node.true_target,
        false_target=node.false_target,
    )
    return DefinitionContent(
        kind="INTERNAL_BRANCH",
        canonical_graph=("branch",) + normalized_program.canonical_tuple,
        leaf_path=normalized_program.leaf_path,
    )


def define_predicate(
    alias: str,
    predicate: Predicate | str,
    *,
    provenance: Iterable[str] = (),
    dependencies: Iterable[str] = (),
) -> DefinitionRecord:
    return DefinitionRecord(
        alias=alias,
        content=predicate_content(predicate),
        provenance=tuple(provenance),
        dependencies=tuple(dependencies),
    )


def define_branch(
    alias: str,
    program: BranchProgram | str,
    *,
    provenance: Iterable[str] = (),
    dependencies: Iterable[str] = (),
) -> DefinitionRecord:
    return DefinitionRecord(
        alias=alias,
        content=branch_content(program),
        provenance=tuple(provenance),
        dependencies=tuple(dependencies),
    )


def verify_serialized_record(record: Mapping[str, object]) -> None:
    if record.get("schema") != _RECORD_SCHEMA:
        raise DefinitionV11Error("unsupported definition record schema")
    content_raw = record.get("content")
    if not isinstance(content_raw, Mapping):
        raise DefinitionV11Error("serialized definition record missing content payload")
    if content_raw.get("schema") != _CONTENT_SCHEMA:
        raise DefinitionV11Error("unsupported definition content schema")
    expected_content = _sha256_id("pncs:def", content_raw)
    if record.get("content_id") != expected_content:
        raise DefinitionV11Error("serialized definition content digest mismatch")

    expected_record_payload = {
        "schema": record.get("schema"),
        "alias": record.get("alias"),
        "content_id": record.get("content_id"),
        "provenance": record.get("provenance"),
        "dependencies": record.get("dependencies"),
        "epistemic_operator": record.get("epistemic_operator"),
        "canon_allowed": record.get("canon_allowed"),
    }
    expected_record = _sha256_id("pncs:def-record", expected_record_payload)
    if record.get("record_id") != expected_record:
        raise DefinitionV11Error("serialized definition record digest mismatch")
