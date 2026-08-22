from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import re
from typing import Mapping, Sequence

MASS_SCALE = 10_000_000_000
MASS_QUANTUM = Decimal('0.0000000001')
COST_SCHEMA = 'PNCS_MASS_AWARE_GRAPH_COST_V0_21'
COST_RECEIPT_SCHEMA = 'PNCS_MASS_AWARE_GRAPH_COST_RECEIPT_V0_21'
COST_CONTRACT_ID = 'PNCS_MASS_AWARE_GRAPH_COST_V0_21'
_SCOPE = {'RADICAL', 'PATH', 'PROGRAM', 'PREDICATE'}
_OPERATOR_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_DIGEST_RE = re.compile(r'^[0-9a-f]{64}$')

class MassAwareCostV21Error(ValueError):
    pass


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(x) for x in value]
    if isinstance(value, list):
        return [_jsonable(x) for x in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(value[k]) for k in sorted(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise MassAwareCostV21Error('non-finite canonical value')
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise MassAwareCostV21Error(f'unsupported canonical value type: {type(value).__name__}')


def _compact_json(value: object) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def _sha(value: object) -> str:
    return hashlib.sha256(_compact_json(value).encode('utf-8')).hexdigest()


def _typed_id(prefix: str, value: object) -> str:
    return f'{prefix}:sha256:{_sha(value)}'


def _mass_units(value: object) -> int:
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise MassAwareCostV21Error('semantic mass must be finite') from exc
    if not math.isfinite(f) or f < 0.0:
        raise MassAwareCostV21Error('semantic mass must be finite and non-negative')
    try:
        d = Decimal(str(f))
    except InvalidOperation as exc:
        raise MassAwareCostV21Error('invalid semantic mass') from exc
    q = d.quantize(MASS_QUANTUM)
    if d != q:
        raise MassAwareCostV21Error('v0.21 cost accepts only v0.19 10-decimal mass values')
    return int(q * MASS_SCALE)


def _mass_float(units: int) -> float:
    return float(Decimal(units) / MASS_SCALE)


def _verify_mass_pair(kaku: object, binding: object) -> None:
    verify = getattr(binding, 'verify', None)
    if not callable(verify):
        raise MassAwareCostV21Error('SemanticMassBinding-compatible object required')
    verify()
    realization = getattr(binding, 'realization', None)
    phase = getattr(realization, 'phase', None)
    phase_angles = getattr(phase, 'angles', None)
    kaku_phase = getattr(kaku, 'phase', None)
    kaku_vector = getattr(kaku, 'vector', None)
    kaku_basis = getattr(kaku_vector, 'basis_id', None)
    realization_basis = getattr(realization, 'basis_id', None)
    if phase_angles is None or kaku_phase is None or tuple(kaku_phase) != tuple(phase_angles):
        raise MassAwareCostV21Error('KAKU phase does not match exact mass realization')
    if kaku_basis != realization_basis:
        raise MassAwareCostV21Error('KAKU basis does not match exact mass realization')
    if float(getattr(kaku, 'semantic_mass', float('nan'))) != float(getattr(binding, 'semantic_mass', float('nan'))):
        raise MassAwareCostV21Error('KAKU semantic_mass does not match v0.19 binding')
    _mass_units(getattr(binding, 'semantic_mass'))


@dataclass(frozen=True)
class KakuMassWitness:
    kaku_id: str
    operator_id: str
    mass_binding_id: str
    semantic_mass_units: int
    phase36_sha256: str
    realization_id: str

    @property
    def semantic_mass(self) -> float:
        return _mass_float(self.semantic_mass_units)

    @property
    def witness_payload(self) -> dict[str, object]:
        return {
            'kaku_id': self.kaku_id,
            'operator_id': self.operator_id,
            'mass_binding_id': self.mass_binding_id,
            'semantic_mass_units': self.semantic_mass_units,
            'phase36_sha256': self.phase36_sha256,
            'realization_id': self.realization_id,
        }

    @property
    def witness_id(self) -> str:
        return _typed_id('pncs:mass-witness', self.witness_payload)


def bind_kaku_mass_witness(kaku: object, mass_binding: object) -> KakuMassWitness:
    _verify_mass_pair(kaku, mass_binding)
    kaku_id = getattr(kaku, 'kaku_id', None)
    role = getattr(kaku, 'role', None)
    if not isinstance(kaku_id, str) or not kaku_id:
        raise MassAwareCostV21Error('KAKU kaku_id required')
    if not isinstance(role, str) or not _OPERATOR_RE.fullmatch(role):
        raise MassAwareCostV21Error('KAKU role must be the canonical PNV operator ID')
    realization = getattr(mass_binding, 'realization')
    phase = getattr(realization, 'phase')
    phase_sha = getattr(phase, 'phase_sha256', None)
    realization_id = getattr(realization, 'realization_id', None)
    mass_binding_id = getattr(mass_binding, 'mass_binding_id', None)
    if not isinstance(phase_sha, str) or not _DIGEST_RE.fullmatch(phase_sha):
        raise MassAwareCostV21Error('mass witness requires exact phase36 SHA-256')
    if not isinstance(realization_id, str) or ':sha256:' not in realization_id:
        raise MassAwareCostV21Error('mass witness requires exact realization ID')
    if not isinstance(mass_binding_id, str) or ':sha256:' not in mass_binding_id:
        raise MassAwareCostV21Error('mass witness requires mass binding ID')
    return KakuMassWitness(
        kaku_id=kaku_id,
        operator_id=role,
        mass_binding_id=mass_binding_id,
        semantic_mass_units=_mass_units(getattr(mass_binding, 'semantic_mass')),
        phase36_sha256=phase_sha,
        realization_id=realization_id,
    )


class MassCostRegistry:
    def __init__(self) -> None:
        self._by_kaku: dict[str, KakuMassWitness] = {}

    def register(self, kaku: object, mass_binding: object) -> KakuMassWitness:
        witness = bind_kaku_mass_witness(kaku, mass_binding)
        prior = self._by_kaku.get(witness.kaku_id)
        if prior is not None and prior != witness:
            raise MassAwareCostV21Error(f'conflicting mass witness for KAKU {witness.kaku_id}')
        self._by_kaku[witness.kaku_id] = witness
        return witness

    def witness(self, kaku_id: str) -> KakuMassWitness:
        try:
            return self._by_kaku[kaku_id]
        except KeyError as exc:
            raise MassAwareCostV21Error(f'missing explicit mass witness for KAKU {kaku_id}') from exc


@dataclass(frozen=True)
class CostRuntimeContext:
    surface_root: str
    operator_registry_sha256: str
    tether_receipt_sha256: str
    live_operator_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.surface_root != '/dev/shm/ciel_noema':
            raise MassAwareCostV21Error('operational v0.21 cost surface must be /dev/shm/ciel_noema')
        for value, field in ((self.operator_registry_sha256, 'operator_registry_sha256'), (self.tether_receipt_sha256, 'tether_receipt_sha256')):
            if not _DIGEST_RE.fullmatch(value):
                raise MassAwareCostV21Error(f'{field} must be lowercase SHA-256')
        if not self.live_operator_ids or len(set(self.live_operator_ids)) != len(self.live_operator_ids):
            raise MassAwareCostV21Error('live operator IDs must be unique and non-empty')

    @property
    def payload(self) -> dict[str, object]:
        return {
            'surface_root': self.surface_root,
            'operator_registry_sha256': self.operator_registry_sha256,
            'tether_receipt_sha256': self.tether_receipt_sha256,
            'live_operator_ids': list(self.live_operator_ids),
            'static_runtime_fallback': False,
        }


def live_cost_context(surface_root: object = '/dev/shm/ciel_noema') -> CostRuntimeContext:
    from .execution_v20 import load_live_surface
    snap = load_live_surface(surface_root)
    return CostRuntimeContext(
        surface_root=snap.root,
        operator_registry_sha256=snap.operator_registry_sha256,
        tether_receipt_sha256=snap.tether_receipt_sha256,
        live_operator_ids=tuple(sorted(snap.operator_vectors)),
    )


@dataclass(frozen=True)
class GraphCost:
    scope: str
    subject_id: str
    graph_sha256: str
    witnesses: tuple[KakuMassWitness, ...]
    runtime: CostRuntimeContext

    def __post_init__(self) -> None:
        if self.scope not in _SCOPE:
            raise MassAwareCostV21Error(f'unsupported cost scope: {self.scope}')
        if not self.subject_id:
            raise MassAwareCostV21Error('subject_id required')
        if not _DIGEST_RE.fullmatch(self.graph_sha256):
            raise MassAwareCostV21Error('graph_sha256 must be lowercase SHA-256')
        live = set(self.runtime.live_operator_ids)
        missing = sorted({w.operator_id for w in self.witnesses} - live)
        if missing:
            raise MassAwareCostV21Error(f'cost witness operator absent from live PhaseNav registry: {missing}')

    @property
    def node_count(self) -> int:
        return len(self.witnesses)

    @property
    def total_mass_units(self) -> int:
        return sum(w.semantic_mass_units for w in self.witnesses)

    @property
    def total_mass(self) -> float:
        return _mass_float(self.total_mass_units)

    @property
    def unique_kaku_count(self) -> int:
        return len({w.kaku_id for w in self.witnesses})

    @property
    def duplicate_node_count(self) -> int:
        return self.node_count - self.unique_kaku_count

    @property
    def duplicate_mass_units(self) -> int:
        seen: set[str] = set()
        total = 0
        for witness in self.witnesses:
            if witness.kaku_id in seen:
                total += witness.semantic_mass_units
            else:
                seen.add(witness.kaku_id)
        return total

    @property
    def cost_payload(self) -> dict[str, object]:
        return {
            'schema': COST_SCHEMA,
            'cost_contract_id': COST_CONTRACT_ID,
            'scope': self.scope,
            'subject_id': self.subject_id,
            'graph_sha256': self.graph_sha256,
            'ordered_witness_ids': [w.witness_id for w in self.witnesses],
            'ordered_kaku_ids': [w.kaku_id for w in self.witnesses],
            'operator_ids': [w.operator_id for w in self.witnesses],
            'mass_units': [w.semantic_mass_units for w in self.witnesses],
            'mass_scale': MASS_SCALE,
            'node_count': self.node_count,
            'unique_kaku_count': self.unique_kaku_count,
            'duplicate_node_count': self.duplicate_node_count,
            'duplicate_mass_units': self.duplicate_mass_units,
            'total_mass_units': self.total_mass_units,
            'total_mass': self.total_mass,
            'semantic_identity_affected': False,
            'semantic_equivalence_from_cost': False,
        }

    @property
    def cost_id(self) -> str:
        return _typed_id('pncs:graph-cost', self.cost_payload)

    @property
    def deterministic_receipt(self) -> dict[str, object]:
        payload = {
            'schema': COST_RECEIPT_SCHEMA,
            'cost_id': self.cost_id,
            'cost': self.cost_payload,
            'live_runtime': self.runtime.payload,
        }
        return {**payload, 'receipt_sha256': _sha(payload)}
