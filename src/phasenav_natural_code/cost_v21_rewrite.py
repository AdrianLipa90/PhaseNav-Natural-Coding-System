from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Mapping

from .cost_v21_core import (
    GraphCost, MassAwareCostV21Error, _compact_json, _mass_float, _mass_units, _sha, _typed_id,
)
from .cost_v21_scopes import _predicate_tuple

EQUIV_SCHEMA = 'PNCS_PURE_BOOLEAN_EQUIVALENCE_EVIDENCE_V0_21'
REWRITE_SCHEMA = 'PNCS_COST_AWARE_REWRITE_ADMISSION_V0_21'
MAX_BOOLEAN_ATOMS = 12

def _atoms(node: tuple[object, ...], out: set[str]) -> None:
    kind = node[0]
    if kind == 'comparison':
        out.add(_compact_json(node))
        return
    if kind == 'not':
        _atoms(_predicate_tuple(node[1]), out)
        return
    if kind in {'and', 'or'}:
        for child in node[1:]:
            _atoms(_predicate_tuple(child), out)
        return
    raise MassAwareCostV21Error('equivalence proof accepts pure predicates only')


def _eval_bool(node: tuple[object, ...], assignment: Mapping[str, bool]) -> bool:
    kind = node[0]
    if kind == 'comparison':
        return assignment[_compact_json(node)]
    if kind == 'not':
        return not _eval_bool(_predicate_tuple(node[1]), assignment)
    if kind == 'and':
        return all(_eval_bool(_predicate_tuple(c), assignment) for c in node[1:])
    if kind == 'or':
        return any(_eval_bool(_predicate_tuple(c), assignment) for c in node[1:])
    raise MassAwareCostV21Error('equivalence proof accepts pure predicates only')


@dataclass(frozen=True)
class EquivalenceEvidence:
    source_graph_sha256: str
    target_graph_sha256: str
    equivalent: bool
    method: str
    atom_count: int
    valuation_count: int
    counterexample: tuple[tuple[str, bool], ...] | None = None

    @property
    def payload(self) -> dict[str, object]:
        return {
            'schema': EQUIV_SCHEMA,
            'source_graph_sha256': self.source_graph_sha256,
            'target_graph_sha256': self.target_graph_sha256,
            'equivalent': self.equivalent,
            'method': self.method,
            'atom_count': self.atom_count,
            'valuation_count': self.valuation_count,
            'counterexample': None if self.counterexample is None else [[k, v] for k, v in self.counterexample],
        }

    @property
    def evidence_id(self) -> str:
        return _typed_id('pncs:equivalence-evidence', self.payload)


def prove_pure_boolean_equivalence(left: object, right: object, *, max_atoms: int = MAX_BOOLEAN_ATOMS) -> EquivalenceEvidence:
    l = _predicate_tuple(left)
    r = _predicate_tuple(right)
    atoms: set[str] = set()
    _atoms(l, atoms); _atoms(r, atoms)
    ordered = tuple(sorted(atoms))
    if len(ordered) > max_atoms:
        raise MassAwareCostV21Error(f'boolean equivalence proof exceeds atom limit {max_atoms}')
    checked = 0
    for bits in itertools.product((False, True), repeat=len(ordered)):
        assignment = dict(zip(ordered, bits))
        checked += 1
        if _eval_bool(l, assignment) != _eval_bool(r, assignment):
            return EquivalenceEvidence(
                _sha(l), _sha(r), False, 'PURE_BOOLEAN_COMPLETE_TRUTH_TABLE_V0_21', len(ordered), checked,
                tuple((k, assignment[k]) for k in ordered),
            )
    return EquivalenceEvidence(
        _sha(l), _sha(r), True, 'PURE_BOOLEAN_COMPLETE_TRUTH_TABLE_V0_21', len(ordered), checked, None
    )


def distributive_candidate_once(predicate: object) -> tuple[object, ...]:
    node = _predicate_tuple(predicate)
    kind = node[0]
    if kind not in {'and', 'or'}:
        raise MassAwareCostV21Error('distributivity requires AND or OR root')
    opposite = 'or' if kind == 'and' else 'and'
    inner_index = None
    for i, child in enumerate(node[1:], start=1):
        ct = _predicate_tuple(child)
        if ct[0] == opposite:
            inner_index = i
            break
    if inner_index is None:
        raise MassAwareCostV21Error('no one-step distributive opportunity at root')
    inner = _predicate_tuple(node[inner_index])
    common = [node[i] for i in range(1, len(node)) if i != inner_index]
    terms = []
    for branch in inner[1:]:
        terms.append((kind, *common, branch))
    return (opposite, *terms)


@dataclass(frozen=True)
class GrowthBudget:
    max_added_nodes: int = 0
    max_added_mass_units: int = 0
    justification: str = 'NO_GROWTH_DEFAULT'

    def __post_init__(self) -> None:
        if isinstance(self.max_added_nodes, bool) or not isinstance(self.max_added_nodes, int) or self.max_added_nodes < 0:
            raise MassAwareCostV21Error('max_added_nodes must be a non-negative integer')
        if isinstance(self.max_added_mass_units, bool) or not isinstance(self.max_added_mass_units, int) or self.max_added_mass_units < 0:
            raise MassAwareCostV21Error('max_added_mass_units must be a non-negative integer')
        if (self.max_added_nodes > 0 or self.max_added_mass_units > 0) and self.justification == 'NO_GROWTH_DEFAULT':
            raise MassAwareCostV21Error('positive growth budget requires explicit justification')
        if not isinstance(self.justification, str) or not self.justification.strip():
            raise MassAwareCostV21Error('growth budget justification required')

    @classmethod
    def from_mass(cls, *, max_added_nodes: int, max_added_mass: float, justification: str) -> 'GrowthBudget':
        return cls(max_added_nodes=max_added_nodes, max_added_mass_units=_mass_units(max_added_mass), justification=justification)


@dataclass(frozen=True)
class RewriteAdmission:
    source_cost_id: str
    target_cost_id: str
    equivalence_evidence_id: str
    delta_nodes: int
    delta_mass_units: int
    budget: GrowthBudget
    admitted: bool
    classification: str
    unjustified_growth_detected: bool

    @property
    def payload(self) -> dict[str, object]:
        return {
            'schema': REWRITE_SCHEMA,
            'source_cost_id': self.source_cost_id,
            'target_cost_id': self.target_cost_id,
            'equivalence_evidence_id': self.equivalence_evidence_id,
            'delta_nodes': self.delta_nodes,
            'delta_mass_units': self.delta_mass_units,
            'delta_mass': _mass_float(self.delta_mass_units),
            'budget': {
                'max_added_nodes': self.budget.max_added_nodes,
                'max_added_mass_units': self.budget.max_added_mass_units,
                'justification': self.budget.justification,
            },
            'admitted': self.admitted,
            'classification': self.classification,
            'unjustified_growth_detected': self.unjustified_growth_detected,
            'cost_proves_semantic_equivalence': False,
        }

    @property
    def receipt_sha256(self) -> str:
        return _sha(self.payload)


def assess_cost_aware_rewrite(source: GraphCost, target: GraphCost, evidence: EquivalenceEvidence, budget: GrowthBudget | None = None) -> RewriteAdmission:
    if source.runtime != target.runtime:
        raise MassAwareCostV21Error('rewrite costs must use the same live runtime snapshot')
    if evidence.source_graph_sha256 != source.graph_sha256 or evidence.target_graph_sha256 != target.graph_sha256:
        raise MassAwareCostV21Error('equivalence evidence does not bind the costed source/target graphs')
    active_budget = budget or GrowthBudget()
    dn = target.node_count - source.node_count
    dm = target.total_mass_units - source.total_mass_units
    growth = dn > 0 or dm > 0
    if not evidence.equivalent:
        admitted = False; classification = 'NON_EQUIVALENT'
    elif dn <= 0 and dm <= 0:
        admitted = True; classification = 'NON_GROWING_EQUIVALENT'
    elif dn <= active_budget.max_added_nodes and dm <= active_budget.max_added_mass_units:
        admitted = True; classification = 'BUDGETED_GROWTH'
    elif active_budget == GrowthBudget():
        admitted = False; classification = 'UNJUSTIFIED_GROWTH'
    else:
        admitted = False; classification = 'BUDGET_EXCEEDED'
    unjustified = bool(growth and not admitted)
    return RewriteAdmission(
        source.cost_id, target.cost_id, evidence.evidence_id, dn, dm, active_budget,
        admitted, classification, unjustified,
    )

def assess_cost_aware_distributivity(
    source: GraphCost,
    target: GraphCost,
    evidence: EquivalenceEvidence,
    budget: GrowthBudget | None = None,
) -> RewriteAdmission:
    if source.scope != 'PREDICATE' or target.scope != 'PREDICATE':
        raise MassAwareCostV21Error('cost-aware distributivity requires PREDICATE costs')
    source_ids = {w.kaku_id for w in source.witnesses}
    target_ids = {w.kaku_id for w in target.witnesses}
    if source_ids != target_ids:
        raise MassAwareCostV21Error(
            'distributive rewrite must reuse the exact source KAKU witness set; new/substituted KAKU are forbidden'
        )
    return assess_cost_aware_rewrite(source, target, evidence, budget)
