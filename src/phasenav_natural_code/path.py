from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
from .model import PNCSIntegrityError

LEVELS = {
    "KAKU", "RADICAL", "DEFINITION", "CLASS", "FILE", "CLUSTER",
    "SUBSYSTEM", "DAEMON", "LOW_ORCHESTRATOR", "HIGH_ORCHESTRATOR", "SYSTEM"
}

@dataclass(frozen=True)
class CanonicalPath:
    path_id: str
    level: str
    node_ids: Tuple[str, ...]
    relation_ids: Tuple[str, ...]
    basis_id: str
    status: str = "CANDIDATE"

    def __post_init__(self) -> None:
        if self.level not in LEVELS:
            raise PNCSIntegrityError(f"unknown path level: {self.level}")
        if not self.path_id or not self.basis_id:
            raise PNCSIntegrityError("path_id and basis_id are required")
        if len(self.node_ids) == 0:
            raise PNCSIntegrityError("canonical path requires at least one node")
        if len(self.relation_ids) not in (0, len(self.node_ids) - 1):
            raise PNCSIntegrityError("relation count must be node_count - 1")
