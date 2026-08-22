from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Iterable, Mapping, Sequence

from .paths_v13 import ClusterRegistry


class HierarchyV14Error(ValueError):
    pass


_ALIAS_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_LEVELS = ("SUBSYSTEM", "DAEMON", "LOW_ORCHESTRATOR", "HIGH_ORCHESTRATOR", "SYSTEM")
_PREFIX = {
    "SUBSYSTEM": "pncs:subsystem:sha256:",
    "DAEMON": "pncs:daemon:sha256:",
    "LOW_ORCHESTRATOR": "pncs:low-orchestrator:sha256:",
    "HIGH_ORCHESTRATOR": "pncs:high-orchestrator:sha256:",
    "SYSTEM": "pncs:system:sha256:",
}
_ID_PREFIX = {
    "SUBSYSTEM": "SS",
    "DAEMON": "DM",
    "LOW_ORCHESTRATOR": "LO",
    "HIGH_ORCHESTRATOR": "HO",
    "SYSTEM": "SYS",
}
_CONTENT_SCHEMA = "PNCS_HIGHER_PATH_CONTENT_V1"
_RECORD_SCHEMA = "PNCS_HIGHER_PATH_RECORD_V1"
_CLUSTER_PREFIX = "pncs:cluster:sha256:"


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise HierarchyV14Error(f"unsupported canonical value type: {type(value).__name__}")


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(_jsonable(dict(payload)), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_id(prefix: str, payload: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _validate_alias(alias: str) -> str:
    if not isinstance(alias, str) or not _ALIAS_RE.fullmatch(alias):
        raise HierarchyV14Error("higher-path alias must match ^[a-z][a-z0-9_.:-]*$")
    return alias


def _validate_projection(path: str | None) -> str | None:
    if path is None:
        return None
    if not isinstance(path, str) or not path.strip() or "\x00" in path:
        raise HierarchyV14Error("projection_path must be a non-empty NUL-free string or None")
    return path


def _validate_child_ids(level: str, child_ids: Sequence[str]) -> tuple[str, ...]:
    ids=tuple(str(x) for x in child_ids)
    if not ids:
        raise HierarchyV14Error(f"{level.lower()} requires at least one child content ID")
    if level in {"SUBSYSTEM","DAEMON"}:
        allowed=(_CLUSTER_PREFIX,)
    elif level=="LOW_ORCHESTRATOR":
        allowed=(_PREFIX["SUBSYSTEM"],_PREFIX["DAEMON"])
    elif level=="HIGH_ORCHESTRATOR":
        allowed=(_PREFIX["LOW_ORCHESTRATOR"],)
    elif level=="SYSTEM":
        allowed=(_PREFIX["HIGH_ORCHESTRATOR"],)
    else:
        raise HierarchyV14Error(f"unsupported level: {level}")
    bad=[x for x in ids if not any(x.startswith(p) and len(x)==len(p)+64 for p in allowed)]
    if bad:
        raise HierarchyV14Error(f"invalid {level.lower()} child content ID(s): {bad}")
    return ids


@dataclass(frozen=True)
class HigherContent:
    level: str
    child_ids: tuple[str, ...]
    path_mode: str = "ORDERED_COMPOSITION"

    def __post_init__(self) -> None:
        if self.level not in _LEVELS:
            raise HierarchyV14Error(f"unsupported higher path level: {self.level}")
        object.__setattr__(self,"child_ids",_validate_child_ids(self.level,self.child_ids))
        if self.path_mode!="ORDERED_COMPOSITION":
            raise HierarchyV14Error("v0.14 supports ORDERED_COMPOSITION higher paths only")

    @property
    def semantic_payload(self)->dict[str,object]:
        return {
            "schema":_CONTENT_SCHEMA,
            "level":self.level,
            "path_mode":self.path_mode,
            "child_ids":list(self.child_ids),
        }

    @property
    def content_id(self)->str:
        prefix=_PREFIX[self.level][:-8]  # strip ':sha256:' for helper
        return _sha256_id(prefix,self.semantic_payload)

    @property
    def short_id(self)->str:
        return self.content_id.rsplit(":",1)[-1][:16]

    @property
    def native_root_id(self)->str:
        return f"{_ID_PREFIX[self.level]}.{self.short_id}.ROOT"


@dataclass(frozen=True)
class HigherRecord:
    alias: str
    content: HigherContent
    provenance: tuple[str,...]=()
    projection_path: str|None=None
    epistemic_operator: str="CHYBA"
    canon_allowed: bool=False

    def __post_init__(self)->None:
        object.__setattr__(self,"alias",_validate_alias(self.alias))
        object.__setattr__(self,"projection_path",_validate_projection(self.projection_path))
        if self.epistemic_operator!="CHYBA":
            raise HierarchyV14Error("v0.14 higher-path records must remain CHYBA")
        if self.canon_allowed:
            raise HierarchyV14Error("v0.14 cannot self-promote higher-path records to canon")
        for item in self.provenance:
            if not isinstance(item,str) or not item:
                raise HierarchyV14Error("provenance entries must be non-empty strings")

    @property
    def record_payload(self)->dict[str,object]:
        return {
            "schema":_RECORD_SCHEMA,
            "level":self.content.level,
            "alias":self.alias,
            "content_id":self.content.content_id,
            "child_ids":list(self.content.child_ids),
            "projection_path":self.projection_path,
            "provenance":list(self.provenance),
            "epistemic_operator":self.epistemic_operator,
            "canon_allowed":self.canon_allowed,
        }

    @property
    def record_id(self)->str:
        return _sha256_id("pncs:higher-record",self.record_payload)

    def to_json_record(self)->dict[str,object]:
        return {**self.record_payload,"record_id":self.record_id,"content":self.content.semantic_payload}


class HierarchyRegistry:
    def __init__(self, clusters: ClusterRegistry)->None:
        self._clusters=clusters
        self._by_alias:dict[str,HigherRecord]={}
        self._by_content:dict[str,HigherContent]={}

    def _child_exists(self, child_id:str)->bool:
        if child_id.startswith(_CLUSTER_PREFIX):
            try: self._clusters.content(child_id); return True
            except Exception: return False
        return child_id in self._by_content

    def register(self,record:HigherRecord)->HigherRecord:
        if record.alias in self._by_alias:
            raise HierarchyV14Error(f"duplicate higher-path alias: {record.alias}")
        missing=[x for x in record.content.child_ids if not self._child_exists(x)]
        if missing:
            raise HierarchyV14Error(f"{record.content.level.lower()} child dependency not registered: {missing}")
        cid=record.content.content_id
        prior=self._by_content.get(cid)
        if prior is not None and prior.semantic_payload!=record.content.semantic_payload:
            raise HierarchyV14Error("higher-path content-address collision with non-identical payload")
        self._by_alias[record.alias]=record
        self._by_content.setdefault(cid,record.content)
        return record

    def resolve_alias(self,alias:str)->str:
        alias=_validate_alias(alias)
        try:return self._by_alias[alias].content.content_id
        except KeyError as exc: raise HierarchyV14Error(f"unknown higher-path alias: {alias}") from exc

    def record(self,alias:str)->HigherRecord:
        alias=_validate_alias(alias)
        try:return self._by_alias[alias]
        except KeyError as exc: raise HierarchyV14Error(f"unknown higher-path alias: {alias}") from exc

    def content(self,content_id:str)->HigherContent:
        try:return self._by_content[content_id]
        except KeyError as exc: raise HierarchyV14Error(f"unknown higher-path content id: {content_id}") from exc

    def aliases_for(self,content_id:str)->tuple[str,...]:
        if content_id not in self._by_content:
            raise HierarchyV14Error(f"unknown higher-path content id: {content_id}")
        return tuple(sorted(a for a,r in self._by_alias.items() if r.content.content_id==content_id))

    def children(self,alias_or_content_id:str)->tuple[str,...]:
        c=self.content(alias_or_content_id) if alias_or_content_id.startswith("pncs:") else self.record(alias_or_content_id).content
        return c.child_ids

    def expand_clusters(self,alias_or_content_id:str)->tuple[str,...]:
        c=self.content(alias_or_content_id) if alias_or_content_id.startswith("pncs:") else self.record(alias_or_content_id).content
        out:list[str]=[]
        for child in c.child_ids:
            if child.startswith(_CLUSTER_PREFIX): out.append(child)
            else: out.extend(self.expand_clusters(child))
        return tuple(out)

    def expand_files(self,alias_or_content_id:str)->tuple[str,...]:
        out:list[str]=[]
        for cluster_id in self.expand_clusters(alias_or_content_id):
            out.extend(self._clusters.expand_files(cluster_id))
        return tuple(out)

    def expand_classes(self,alias_or_content_id:str)->tuple[str,...]:
        out:list[str]=[]
        for cluster_id in self.expand_clusters(alias_or_content_id):
            out.extend(self._clusters.expand_classes(cluster_id))
        return tuple(out)

    def expand_definitions(self,alias_or_content_id:str)->tuple[str,...]:
        out:list[str]=[]
        for cluster_id in self.expand_clusters(alias_or_content_id):
            out.extend(self._clusters.expand_definitions(cluster_id))
        return tuple(out)

    def expand_leaves(self,alias_or_content_id:str)->tuple[str,...]:
        c=self.content(alias_or_content_id) if alias_or_content_id.startswith("pncs:") else self.record(alias_or_content_id).content
        out:list[str]=[]
        for i,child in enumerate(c.child_ids):
            if i: out.append("ORDER")
            if child.startswith(_CLUSTER_PREFIX): out.extend(self._clusters.expand_leaves(child))
            else: out.extend(self.expand_leaves(child))
            if i: out.append("COMPOSITION")
        return tuple(out)

    def jsonl(self)->str:
        rows=[self._by_alias[k].to_json_record() for k in sorted(self._by_alias)]
        return "\n".join(_canonical_json(r) for r in rows)+("\n" if rows else "")


def define_higher(level:str,alias:str,child_ids:Iterable[str],*,provenance:Iterable[str]=(),projection_path:str|None=None)->HigherRecord:
    return HigherRecord(alias=alias,content=HigherContent(level,tuple(child_ids)),provenance=tuple(provenance),projection_path=projection_path)


def define_subsystem(alias:str,cluster_ids:Iterable[str],**kwargs)->HigherRecord:
    return define_higher("SUBSYSTEM",alias,cluster_ids,**kwargs)


def define_daemon(alias:str,cluster_ids:Iterable[str],**kwargs)->HigherRecord:
    return define_higher("DAEMON",alias,cluster_ids,**kwargs)


def define_low_orchestrator(alias:str,child_ids:Iterable[str],**kwargs)->HigherRecord:
    return define_higher("LOW_ORCHESTRATOR",alias,child_ids,**kwargs)


def define_high_orchestrator(alias:str,low_ids:Iterable[str],**kwargs)->HigherRecord:
    return define_higher("HIGH_ORCHESTRATOR",alias,low_ids,**kwargs)


def define_system(alias:str,high_ids:Iterable[str],**kwargs)->HigherRecord:
    return define_higher("SYSTEM",alias,high_ids,**kwargs)


def verify_serialized_higher_record(record:Mapping[str,object])->None:
    if record.get("schema")!=_RECORD_SCHEMA:
        raise HierarchyV14Error("unsupported higher-path record schema")
    content=record.get("content")
    if not isinstance(content,Mapping) or content.get("schema")!=_CONTENT_SCHEMA:
        raise HierarchyV14Error("serialized higher-path record missing content payload")
    level=str(content.get("level"))
    child_ids=content.get("child_ids")
    if not isinstance(child_ids,list):
        raise HierarchyV14Error("serialized higher-path record missing child IDs")
    rebuilt=HigherContent(level,tuple(str(x) for x in child_ids),path_mode=str(content.get("path_mode")))
    if rebuilt.content_id!=record.get("content_id"):
        raise HierarchyV14Error("higher-path content digest mismatch")
    payload={
        "schema":_RECORD_SCHEMA,
        "level":record.get("level"),
        "alias":record.get("alias"),
        "content_id":record.get("content_id"),
        "child_ids":record.get("child_ids"),
        "projection_path":record.get("projection_path"),
        "provenance":record.get("provenance"),
        "epistemic_operator":record.get("epistemic_operator"),
        "canon_allowed":record.get("canon_allowed"),
    }
    if _sha256_id("pncs:higher-record",payload)!=record.get("record_id"):
        raise HierarchyV14Error("higher-path record digest mismatch")
