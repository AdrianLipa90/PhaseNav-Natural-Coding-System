from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

from .gremlin_relational_compiler_v01 import (
    RelationalCompilation,
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
    compile_relational_isomorphism,
)
from .model import Kaku

ADAPTER_SCHEMA = "PNCS_GREMLIN_RELATION_MINING_ADAPTER_V0_1"
EXPECTED_LEDGER_SCHEMA = "PNCS_RELATION_MINING_LEDGER_V0_3"


class GremlinRelationMiningAdapterError(RuntimeError):
    pass


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GremlinRelationMiningAdapterError(
            f"{field} must be a non-empty string"
        )
    return value.strip()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GremlinRelationMiningAdapterError(
                "relation-mining ledger contains non-finite float"
            )
        return value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise GremlinRelationMiningAdapterError(
                "relation-mining ledger mapping keys must be strings"
            )
        return {key: _jsonable(value[key]) for key in sorted(value)}
    raise GremlinRelationMiningAdapterError(
        f"relation-mining ledger contains unsupported value: {type(value).__name__}"
    )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _safe(value: str) -> str:
    value = _text(value, "canonical token source")
    token = "".join(
        ch if ch.isalnum() else "_" for ch in value.upper()
    ).strip("_")
    if not token:
        raise GremlinRelationMiningAdapterError("empty canonical token")
    return token


def _canonical_refs(values: Any, field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise GremlinRelationMiningAdapterError(
            f"{field} must be a sequence of strings"
        )
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise GremlinRelationMiningAdapterError(
            f"{field} must be a sequence of strings"
        ) from exc
    return tuple(sorted({_text(value, field) for value in rows}))


@dataclass(frozen=True)
class RelationMiningAlignment:
    left_chain_id: str
    left_atom_index: int
    right_chain_id: str
    right_atom_index: int
    relation_type: str = "ISOMORPHIC_TO"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "left_chain_id",
            _text(self.left_chain_id, "left_chain_id"),
        )
        object.__setattr__(
            self,
            "right_chain_id",
            _text(self.right_chain_id, "right_chain_id"),
        )
        if (
            not isinstance(self.left_atom_index, int)
            or isinstance(self.left_atom_index, bool)
            or self.left_atom_index < 0
        ):
            raise GremlinRelationMiningAdapterError(
                "left_atom_index must be a non-negative integer"
            )
        if (
            not isinstance(self.right_atom_index, int)
            or isinstance(self.right_atom_index, bool)
            or self.right_atom_index < 0
        ):
            raise GremlinRelationMiningAdapterError(
                "right_atom_index must be a non-negative integer"
            )
        object.__setattr__(
            self,
            "relation_type",
            _text(self.relation_type, "alignment relation_type"),
        )


@dataclass(frozen=True)
class RelationMiningFinding:
    finding_id: str
    invariant_id: str
    invariant_description: str
    chain_ids: tuple[str, ...]
    alignments: tuple[RelationMiningAlignment, ...]
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "finding_id",
            _text(self.finding_id, "finding_id"),
        )
        object.__setattr__(
            self,
            "invariant_id",
            _text(self.invariant_id, "invariant_id"),
        )
        object.__setattr__(
            self,
            "invariant_description",
            _text(self.invariant_description, "invariant_description"),
        )
        if isinstance(self.chain_ids, (str, bytes, bytearray)):
            raise GremlinRelationMiningAdapterError(
                "finding chain_ids must be a sequence of strings"
            )
        try:
            chain_ids = tuple(_text(value, "finding chain_id") for value in self.chain_ids)
        except TypeError as exc:
            raise GremlinRelationMiningAdapterError(
                "finding chain_ids must be a sequence of strings"
            ) from exc
        if len(chain_ids) < 2:
            raise GremlinRelationMiningAdapterError(
                "finding requires at least two relation-mining chains"
            )
        if len(set(chain_ids)) != len(chain_ids):
            raise GremlinRelationMiningAdapterError(
                "finding chain_ids must be unique"
            )
        object.__setattr__(self, "chain_ids", chain_ids)

        if isinstance(self.alignments, (str, bytes, bytearray)):
            raise GremlinRelationMiningAdapterError(
                "finding alignments must be RelationMiningAlignment entries"
            )
        try:
            alignments = tuple(self.alignments)
        except TypeError as exc:
            raise GremlinRelationMiningAdapterError(
                "finding alignments must be RelationMiningAlignment entries"
            ) from exc
        if not alignments:
            raise GremlinRelationMiningAdapterError(
                "finding requires explicit cross-chain alignments"
            )
        if any(not isinstance(item, RelationMiningAlignment) for item in alignments):
            raise GremlinRelationMiningAdapterError(
                "finding alignments must be RelationMiningAlignment entries"
            )
        object.__setattr__(self, "alignments", alignments)
        object.__setattr__(
            self,
            "evidence_refs",
            _canonical_refs(self.evidence_refs, "evidence_ref"),
        )


def _ledger_chains(ledger: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    if not isinstance(ledger, Mapping):
        raise GremlinRelationMiningAdapterError(
            "relation-mining ledger must be a mapping"
        )
    if ledger.get("schema") != EXPECTED_LEDGER_SCHEMA:
        raise GremlinRelationMiningAdapterError(
            "relation-mining ledger schema mismatch"
        )
    chains = ledger.get("chains")
    if not isinstance(chains, list) or not chains:
        raise GremlinRelationMiningAdapterError(
            "relation-mining ledger has no chains"
        )
    out: dict[str, Mapping[str, Any]] = {}
    for row in chains:
        if not isinstance(row, Mapping):
            raise GremlinRelationMiningAdapterError(
                "relation-mining chain is not an object"
            )
        chain_id = _text(row.get("id"), "chain id")
        source = _text(row.get("source"), "chain source")
        atoms_raw = row.get("atoms")
        if not isinstance(atoms_raw, list) or not atoms_raw:
            raise GremlinRelationMiningAdapterError(
                f"relation-mining chain has no atoms: {chain_id}"
            )
        atoms = [_text(atom, "chain atom") for atom in atoms_raw]
        status_raw = row.get("status", "")
        if status_raw is None:
            status = ""
        elif isinstance(status_raw, str):
            status = status_raw.strip()
        else:
            raise GremlinRelationMiningAdapterError(
                "chain status must be a string when present"
            )
        if chain_id in out:
            raise GremlinRelationMiningAdapterError(
                f"duplicate relation-mining chain id: {chain_id}"
            )
        normalized = dict(row)
        normalized["id"] = chain_id
        normalized["source"] = source
        normalized["atoms"] = atoms
        normalized["status"] = status
        out[chain_id] = normalized
    return out


def _occurrence_id(chain_id: str, index: int, atom: str) -> str:
    return f"RM.{_safe(chain_id)}.{index:03d}.{_safe(atom)}"


def _clone_occurrence(
    base: Kaku,
    *,
    occurrence_id: str,
    atom: str,
    chain_id: str,
) -> Kaku:
    if not isinstance(base, Kaku):
        raise GremlinRelationMiningAdapterError(
            f"KAKU resolver returned invalid value for atom {atom!r}"
        )
    return Kaku(
        kaku_id=occurrence_id,
        vector=base.vector,
        semantic_mass=base.semantic_mass,
        direction=base.direction,
        polarity=base.polarity,
        role=f"relation_mining:{chain_id}:{atom}:{base.role}",
        phase=base.phase,
    )


def relation_mining_finding_to_isomorphism(
    ledger: Mapping[str, Any],
    finding: RelationMiningFinding,
    *,
    kaku_by_atom: Mapping[str, Kaku],
) -> RelationalIsomorphism:
    if not isinstance(finding, RelationMiningFinding):
        raise GremlinRelationMiningAdapterError(
            "RelationMiningFinding required"
        )
    if not isinstance(kaku_by_atom, Mapping):
        raise GremlinRelationMiningAdapterError(
            "kaku_by_atom must be a mapping"
        )
    chains = _ledger_chains(ledger)
    ledger_sha256 = _sha256(dict(ledger))

    selected: dict[str, Mapping[str, Any]] = {}
    for chain_id in finding.chain_ids:
        row = chains.get(chain_id)
        if row is None:
            raise GremlinRelationMiningAdapterError(
                f"finding references unknown relation-mining chain: {chain_id}"
            )
        selected[chain_id] = row

    domains = {row["source"] for row in selected.values()}
    if len(domains) < 2:
        raise GremlinRelationMiningAdapterError(
            "finding must span at least two source domains"
        )

    atoms_required = sorted(
        {atom for row in selected.values() for atom in row["atoms"]}
    )
    missing_atoms = [atom for atom in atoms_required if atom not in kaku_by_atom]
    if missing_atoms:
        raise GremlinRelationMiningAdapterError(
            "canonical KAKU mapping required before relation-mining compilation: "
            + ", ".join(missing_atoms)
        )
    invalid_atoms = [
        atom for atom in atoms_required if not isinstance(kaku_by_atom[atom], Kaku)
    ]
    if invalid_atoms:
        raise GremlinRelationMiningAdapterError(
            "KAKU resolver returned invalid value for atom(s): "
            + ", ".join(invalid_atoms)
        )

    basis_ids = {kaku_by_atom[atom].vector.basis_id for atom in atoms_required}
    if len(basis_ids) != 1:
        raise GremlinRelationMiningAdapterError(
            "resolved relation-mining KAKU atoms must share one exact PNCS basis"
        )

    nodes: list[RelationalNode] = []
    node_ids: dict[tuple[str, int], str] = {}
    occurrence_ids: set[str] = set()
    edges: list[RelationalEdge] = []
    evidence = set(finding.evidence_refs)
    evidence.add(
        f"relation_mining_ledger:{EXPECTED_LEDGER_SCHEMA}:{ledger_sha256}"
    )

    for chain_id in finding.chain_ids:
        row = selected[chain_id]
        source = row["source"]
        status = row["status"]
        evidence.add(f"chain:{chain_id}:{status}")
        atoms = row["atoms"]
        for index, atom in enumerate(atoms):
            occurrence_id = _occurrence_id(chain_id, index, atom)
            if occurrence_id in occurrence_ids:
                raise GremlinRelationMiningAdapterError(
                    f"canonical occurrence id collision: {occurrence_id}"
                )
            occurrence_ids.add(occurrence_id)
            node_ids[(chain_id, index)] = occurrence_id
            nodes.append(
                RelationalNode(
                    _clone_occurrence(
                        kaku_by_atom[atom],
                        occurrence_id=occurrence_id,
                        atom=atom,
                        chain_id=chain_id,
                    ),
                    source,
                    f"{EXPECTED_LEDGER_SCHEMA}:{chain_id}:atom:{index}:{atom}",
                )
            )
            if index > 0:
                edges.append(
                    RelationalEdge(
                        relation_id=(
                            f"RM.ORDER.{_safe(chain_id)}.{index - 1:03d}.{index:03d}"
                        ),
                        source_id=node_ids[(chain_id, index - 1)],
                        target_id=occurrence_id,
                        relation_type="ORDER",
                    )
                )

    selected_ids = set(finding.chain_ids)
    for index, alignment in enumerate(finding.alignments):
        if (
            alignment.left_chain_id not in selected_ids
            or alignment.right_chain_id not in selected_ids
        ):
            raise GremlinRelationMiningAdapterError(
                "alignment references a chain outside finding.chain_ids"
            )
        left_atoms = selected[alignment.left_chain_id]["atoms"]
        right_atoms = selected[alignment.right_chain_id]["atoms"]
        if (
            alignment.left_atom_index >= len(left_atoms)
            or alignment.right_atom_index >= len(right_atoms)
        ):
            raise GremlinRelationMiningAdapterError(
                "alignment atom index is out of range"
            )
        if alignment.left_chain_id == alignment.right_chain_id:
            raise GremlinRelationMiningAdapterError(
                "cross-domain alignment cannot bind a chain to itself"
            )
        left_domain = selected[alignment.left_chain_id]["source"]
        right_domain = selected[alignment.right_chain_id]["source"]
        if left_domain == right_domain:
            raise GremlinRelationMiningAdapterError(
                "alignment must cross distinct source domains"
            )
        edges.append(
            RelationalEdge(
                relation_id=f"RM.ALIGN.{index:03d}",
                source_id=node_ids[
                    (alignment.left_chain_id, alignment.left_atom_index)
                ],
                target_id=node_ids[
                    (alignment.right_chain_id, alignment.right_atom_index)
                ],
                relation_type=alignment.relation_type,
            )
        )

    return RelationalIsomorphism(
        isomorphism_id=f"RM.{finding.finding_id}",
        invariant_id=finding.invariant_id,
        invariant_description=finding.invariant_description,
        nodes=tuple(nodes),
        edges=tuple(edges),
        evidence_refs=tuple(sorted(evidence)),
    )


def compile_relation_mining_finding(
    ledger: Mapping[str, Any],
    finding: RelationMiningFinding,
    *,
    kaku_by_atom: Mapping[str, Kaku],
    generation_binding: str,
    identity: str,
    authority: str,
    authoring_root: Path | str | None = None,
) -> RelationalCompilation:
    isomorphism = relation_mining_finding_to_isomorphism(
        ledger,
        finding,
        kaku_by_atom=kaku_by_atom,
    )
    return compile_relational_isomorphism(
        isomorphism,
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        authoring_root=authoring_root,
    )
