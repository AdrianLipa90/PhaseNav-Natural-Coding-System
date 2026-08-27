from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Iterable, Mapping

from .mass_v19 import SemanticMassRegistry, materialize_kaku_mass, verify_kaku_mass
from .model import Kaku, Vector36
from .realization_v18 import RealizationRegistry

RESOLVER_SCHEMA = "PNCS_GREMLIN_KAKU_RESOLVER_V0_1"
RESOLUTION_RECEIPT_SCHEMA = "PNCS_GREMLIN_KAKU_RESOLUTION_RECEIPT_V0_1"


class GremlinKakuResolverError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _nonempty(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GremlinKakuResolverError(f"{field} must be a non-empty string")
    return value.strip()


def _vector_payload(vector: Vector36) -> dict[str, Any]:
    if not isinstance(vector, Vector36):
        raise GremlinKakuResolverError("Vector36 required")
    return {"basis_id": vector.basis_id, "values": list(vector.values)}


@dataclass(frozen=True)
class GremlinAtomKakuBinding:
    atom: str
    content_id: str
    realization_binding_id: str
    mass_binding_id: str
    vector: Vector36
    vector_source_ref: str
    direction: str = "FORWARD"
    polarity: float = 1.0
    role: str = "gremlin_relation_atom"

    def __post_init__(self) -> None:
        object.__setattr__(self, "atom", _nonempty(self.atom, "atom").upper())
        object.__setattr__(self, "content_id", _nonempty(self.content_id, "content_id"))
        object.__setattr__(self, "realization_binding_id", _nonempty(self.realization_binding_id, "realization_binding_id"))
        object.__setattr__(self, "mass_binding_id", _nonempty(self.mass_binding_id, "mass_binding_id"))
        object.__setattr__(self, "vector_source_ref", _nonempty(self.vector_source_ref, "vector_source_ref"))
        object.__setattr__(self, "direction", _nonempty(self.direction, "direction"))
        object.__setattr__(self, "role", _nonempty(self.role, "role"))
        if not isinstance(self.vector, Vector36):
            raise GremlinKakuResolverError("binding vector must be Vector36")
        try:
            polarity = float(self.polarity)
        except (TypeError, ValueError) as exc:
            raise GremlinKakuResolverError("polarity must be finite") from exc
        if not math.isfinite(polarity):
            raise GremlinKakuResolverError("polarity must be finite")
        object.__setattr__(self, "polarity", polarity)

    @property
    def vector_sha256(self) -> str:
        return _sha256(_vector_payload(self.vector))

    @property
    def binding_payload(self) -> dict[str, Any]:
        return {
            "schema": RESOLVER_SCHEMA,
            "atom": self.atom,
            "content_id": self.content_id,
            "realization_binding_id": self.realization_binding_id,
            "mass_binding_id": self.mass_binding_id,
            "vector_basis_id": self.vector.basis_id,
            "vector_sha256": self.vector_sha256,
            "vector_source_ref": self.vector_source_ref,
            "direction": self.direction,
            "polarity": self.polarity,
            "role": self.role,
            "semantic_authority": "EXPLICIT_ATOM_CONTENT_BINDING",
            "vector_semantic_authority": False,
            "phase_semantic_authority": False,
            "mass_semantic_authority": False,
        }


class GremlinKakuResolver:
    """Resolve explicit GREMLIN atom bindings into exact PNCS KAKU objects.

    Semantic identity enters through the explicit atom/content binding. Exact vector,
    phase-realization and semantic-mass layers are verified as realizations of that
    content binding and never infer the atom name themselves.
    """

    def __init__(
        self,
        bindings: Iterable[GremlinAtomKakuBinding],
        *,
        realization_registry: RealizationRegistry,
        mass_registry: SemanticMassRegistry,
    ) -> None:
        if not isinstance(realization_registry, RealizationRegistry):
            raise GremlinKakuResolverError("RealizationRegistry required")
        if not isinstance(mass_registry, SemanticMassRegistry):
            raise GremlinKakuResolverError("SemanticMassRegistry required")
        self.realization_registry = realization_registry
        self.mass_registry = mass_registry
        self._bindings: dict[str, GremlinAtomKakuBinding] = {}
        for binding in bindings:
            if not isinstance(binding, GremlinAtomKakuBinding):
                raise GremlinKakuResolverError("GremlinAtomKakuBinding required")
            if binding.atom in self._bindings:
                raise GremlinKakuResolverError(f"duplicate GREMLIN atom binding: {binding.atom}")
            self._bindings[binding.atom] = binding
        if not self._bindings:
            raise GremlinKakuResolverError("at least one GREMLIN atom binding is required")

    def binding(self, atom: str) -> GremlinAtomKakuBinding:
        key = _nonempty(atom, "atom").upper()
        try:
            return self._bindings[key]
        except KeyError as exc:
            raise GremlinKakuResolverError(f"unbound GREMLIN atom: {key}") from exc

    def resolve(self, atom: str) -> Kaku:
        binding = self.binding(atom)
        realization = self.realization_registry.binding(binding.realization_binding_id)
        mass_binding = self.mass_registry.binding(binding.mass_binding_id)

        if realization.content_id != binding.content_id:
            raise GremlinKakuResolverError("atom content_id mismatches exact realization content_id")
        if mass_binding.realization.binding_id != realization.binding_id:
            raise GremlinKakuResolverError("semantic-mass binding targets a different exact realization")
        if mass_binding.realization.content_id != binding.content_id:
            raise GremlinKakuResolverError("semantic-mass binding targets a different semantic content")
        if binding.vector.basis_id != realization.basis_id:
            raise GremlinKakuResolverError("exact Vector36 basis mismatches exact phase realization basis")

        kaku = materialize_kaku_mass(
            kaku_id=f"K.GREMLIN.{binding.atom}",
            vector=binding.vector,
            direction=binding.direction,
            polarity=binding.polarity,
            role=f"{binding.role}:{binding.atom}:{binding.content_id}",
            mass_binding=mass_binding,
        )
        verify_kaku_mass(kaku, mass_binding)
        return kaku

    def resolve_many(self, atoms: Iterable[str]) -> dict[str, Kaku]:
        keys = tuple(_nonempty(atom, "atom").upper() for atom in atoms)
        if not keys:
            raise GremlinKakuResolverError("resolve_many requires at least one atom")
        return {atom: self.resolve(atom) for atom in sorted(set(keys))}

    def deterministic_receipt(self, atoms: Iterable[str] | None = None) -> dict[str, Any]:
        selected = sorted(self._bindings) if atoms is None else sorted(set(_nonempty(atom, "atom").upper() for atom in atoms))
        resolved = self.resolve_many(selected)
        rows = []
        for atom in selected:
            binding = self.binding(atom)
            kaku = resolved[atom]
            rows.append(
                {
                    **binding.binding_payload,
                    "kaku_id": kaku.kaku_id,
                    "semantic_mass": kaku.semantic_mass,
                    "phase36_sha256": _sha256(list(kaku.phase or ())),
                }
            )
        body = {
            "schema": RESOLUTION_RECEIPT_SCHEMA,
            "resolver_contract": RESOLVER_SCHEMA,
            "atoms": selected,
            "bindings": rows,
            "semantic_authority": "EXPLICIT_ATOM_CONTENT_BINDING",
            "nearest_neighbor_resolution": False,
            "vector_to_semantics_inference": False,
            "phase_to_semantics_inference": False,
            "mass_to_semantics_inference": False,
            "epistemic": "CHYBA",
            "promotion_state": "CANDIDATE_ONLY",
        }
        return {**body, "receipt_sha256": _sha256(body)}


def required_relation_mining_atoms(ledger: Mapping[str, Any], chain_ids: Iterable[str]) -> tuple[str, ...]:
    if not isinstance(ledger, Mapping):
        raise GremlinKakuResolverError("relation-mining ledger mapping required")
    chains = ledger.get("chains")
    if not isinstance(chains, list):
        raise GremlinKakuResolverError("relation-mining ledger chains required")
    by_id: dict[str, Mapping[str, Any]] = {}
    for row in chains:
        if isinstance(row, Mapping) and isinstance(row.get("id"), str):
            by_id[str(row["id"])] = row
    atoms: set[str] = set()
    for chain_id in chain_ids:
        key = _nonempty(chain_id, "chain_id")
        row = by_id.get(key)
        if row is None:
            raise GremlinKakuResolverError(f"unknown relation-mining chain: {key}")
        raw_atoms = row.get("atoms")
        if not isinstance(raw_atoms, list) or not raw_atoms:
            raise GremlinKakuResolverError(f"relation-mining chain has no atoms: {key}")
        for atom in raw_atoms:
            atoms.add(_nonempty(str(atom), "atom").upper())
    if not atoms:
        raise GremlinKakuResolverError("no relation-mining atoms resolved")
    return tuple(sorted(atoms))
