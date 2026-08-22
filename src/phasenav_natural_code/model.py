from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple
import math

DIM = 36


class PNCSIntegrityError(ValueError):
    pass


def _finite36(values: Tuple[float, ...]) -> Tuple[float, ...]:
    if len(values) != DIM:
        raise PNCSIntegrityError(f"expected exactly {DIM} dimensions, got {len(values)}")
    out = tuple(float(x) for x in values)
    if not all(math.isfinite(x) for x in out):
        raise PNCSIntegrityError("36D vector contains non-finite value")
    return out


@dataclass(frozen=True)
class Vector36:
    values: Tuple[float, ...]
    basis_id: str

    def __post_init__(self) -> None:
        if not self.basis_id:
            raise PNCSIntegrityError("basis_id is required")
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
        if not self.kaku_id or not self.direction or not self.role:
            raise PNCSIntegrityError("kaku_id, direction and role are required")
        if not math.isfinite(float(self.semantic_mass)):
            raise PNCSIntegrityError("semantic_mass must be finite")
        if not math.isfinite(float(self.polarity)):
            raise PNCSIntegrityError("polarity must be finite")
        if self.phase is not None:
            object.__setattr__(self, "phase", _finite36(tuple(self.phase)))


@dataclass(frozen=True)
class Relation:
    relation_id: str
    source_id: str
    target_id: str
    relation_type: str

    def __post_init__(self) -> None:
        if not all((self.relation_id, self.source_id, self.target_id, self.relation_type)):
            raise PNCSIntegrityError("relation fields must be non-empty")


@dataclass
class RadicalGraph:
    radical_id: str
    basis_id: str
    nodes: dict[str, Kaku] = field(default_factory=dict)
    edges: list[Relation] = field(default_factory=list)

    def add_kaku(self, kaku: Kaku) -> None:
        if kaku.vector.basis_id != self.basis_id:
            raise PNCSIntegrityError("basis mismatch")
        if kaku.kaku_id in self.nodes:
            raise PNCSIntegrityError(f"duplicate KAKU: {kaku.kaku_id}")
        self.nodes[kaku.kaku_id] = kaku

    def add_relation(self, relation: Relation) -> None:
        if relation.source_id not in self.nodes or relation.target_id not in self.nodes:
            raise PNCSIntegrityError("relation endpoint missing from radical graph")
        self.edges.append(relation)
