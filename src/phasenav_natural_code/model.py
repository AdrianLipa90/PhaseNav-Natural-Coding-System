from __future__ import annotations

from dataclasses import dataclass, field
from numbers import Real
from typing import Optional, Tuple
import math

DIM = 36


class PNCSIntegrityError(ValueError):
    pass


def _nonempty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PNCSIntegrityError(f"{field_name} must be a non-empty string")
    return value.strip()


def _finite_scalar(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise PNCSIntegrityError(f"{field_name} must be a finite real number")
    out = float(value)
    if not math.isfinite(out):
        raise PNCSIntegrityError(f"{field_name} must be a finite real number")
    return out


def _finite36(values: Tuple[float, ...]) -> Tuple[float, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise PNCSIntegrityError("36D vector must be a numeric sequence")
    try:
        raw = tuple(values)
    except TypeError as exc:
        raise PNCSIntegrityError("36D vector must be a numeric sequence") from exc
    if len(raw) != DIM:
        raise PNCSIntegrityError(f"expected exactly {DIM} dimensions, got {len(raw)}")
    return tuple(_finite_scalar(value, "36D coordinate") for value in raw)


@dataclass(frozen=True)
class Vector36:
    values: Tuple[float, ...]
    basis_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "basis_id", _nonempty_text(self.basis_id, "basis_id"))
        object.__setattr__(self, "values", _finite36(self.values))


@dataclass(frozen=True)
class Kaku:
    kaku_id: str
    vector: Vector36
    semantic_mass: float
    direction: str
    polarity: float
    role: str
    phase: Optional[Tuple[float, ...]] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "kaku_id", _nonempty_text(self.kaku_id, "kaku_id"))
        if not isinstance(self.vector, Vector36):
            raise PNCSIntegrityError("KAKU vector must be Vector36")
        object.__setattr__(self, "semantic_mass", _finite_scalar(self.semantic_mass, "semantic_mass"))
        object.__setattr__(self, "direction", _nonempty_text(self.direction, "direction"))
        object.__setattr__(self, "polarity", _finite_scalar(self.polarity, "polarity"))
        object.__setattr__(self, "role", _nonempty_text(self.role, "role"))
        if self.phase is not None:
            object.__setattr__(self, "phase", _finite36(self.phase))


@dataclass(frozen=True)
class Relation:
    relation_id: str
    source_id: str
    target_id: str
    relation_type: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relation_id", _nonempty_text(self.relation_id, "relation_id"))
        object.__setattr__(self, "source_id", _nonempty_text(self.source_id, "source_id"))
        object.__setattr__(self, "target_id", _nonempty_text(self.target_id, "target_id"))
        object.__setattr__(self, "relation_type", _nonempty_text(self.relation_type, "relation_type"))


@dataclass
class RadicalGraph:
    radical_id: str
    basis_id: str
    nodes: dict[str, Kaku] = field(default_factory=dict)
    edges: list[Relation] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.radical_id = _nonempty_text(self.radical_id, "radical_id")
        self.basis_id = _nonempty_text(self.basis_id, "basis_id")
        if not isinstance(self.nodes, dict):
            raise PNCSIntegrityError("radical graph nodes must be a dict")
        if not isinstance(self.edges, list):
            raise PNCSIntegrityError("radical graph edges must be a list")
        initial_nodes = dict(self.nodes)
        initial_edges = list(self.edges)
        self.nodes = {}
        self.edges = []
        for node_id, kaku in initial_nodes.items():
            if not isinstance(node_id, str) or not isinstance(kaku, Kaku):
                raise PNCSIntegrityError("radical graph node entries must be string -> Kaku")
            if node_id != kaku.kaku_id:
                raise PNCSIntegrityError("radical graph node key must equal KAKU id")
            self.add_kaku(kaku)
        for relation in initial_edges:
            self.add_relation(relation)

    def add_kaku(self, kaku: Kaku) -> None:
        if not isinstance(kaku, Kaku):
            raise PNCSIntegrityError("radical graph accepts only Kaku nodes")
        if kaku.vector.basis_id != self.basis_id:
            raise PNCSIntegrityError("basis mismatch")
        if kaku.kaku_id in self.nodes:
            raise PNCSIntegrityError(f"duplicate KAKU: {kaku.kaku_id}")
        self.nodes[kaku.kaku_id] = kaku

    def add_relation(self, relation: Relation) -> None:
        if not isinstance(relation, Relation):
            raise PNCSIntegrityError("radical graph accepts only Relation edges")
        if relation.source_id not in self.nodes or relation.target_id not in self.nodes:
            raise PNCSIntegrityError("relation endpoint missing from radical graph")
        if any(edge.relation_id == relation.relation_id for edge in self.edges):
            raise PNCSIntegrityError(f"duplicate relation: {relation.relation_id}")
        self.edges.append(relation)
