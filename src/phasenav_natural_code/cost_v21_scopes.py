from __future__ import annotations

from typing import Mapping, Sequence

from .cost_v21_core import (
    CostRuntimeContext, GraphCost, MassAwareCostV21Error, MassCostRegistry, _sha,
)

def _cost(scope: str, subject_id: str, graph_payload: object, kaku_ids: Sequence[str], registry: MassCostRegistry, runtime: CostRuntimeContext, expected_roles: Sequence[str] | None = None) -> GraphCost:
    witnesses = tuple(registry.witness(kid) for kid in kaku_ids)
    if expected_roles is not None:
        roles = tuple(expected_roles)
        if len(roles) != len(witnesses):
            raise MassAwareCostV21Error('KAKU witness count does not match expanded graph leaf count')
        actual = tuple(w.operator_id for w in witnesses)
        if actual != roles:
            raise MassAwareCostV21Error(f'KAKU operator schedule does not match canonical leaf path: {actual} != {roles}')
    return GraphCost(scope, subject_id, _sha(graph_payload), witnesses, runtime)


def cost_radical(radical: object, mass_bindings: Mapping[str, object], runtime: CostRuntimeContext) -> GraphCost:
    nodes = getattr(radical, 'nodes', None)
    radical_id = getattr(radical, 'radical_id', None)
    if not isinstance(nodes, Mapping) or not isinstance(radical_id, str) or not radical_id:
        raise MassAwareCostV21Error('RadicalGraph-compatible object required')
    registry = MassCostRegistry()
    for kaku_id in sorted(nodes):
        if kaku_id not in mass_bindings:
            raise MassAwareCostV21Error(f'missing mass binding for radical KAKU {kaku_id}')
        registry.register(nodes[kaku_id], mass_bindings[kaku_id])
    ordered = tuple(sorted(nodes))
    graph_payload = {
        'radical_id': radical_id,
        'basis_id': getattr(radical, 'basis_id', None),
        'nodes': ordered,
        'edges': sorted(
            [getattr(e, 'relation_id', None), getattr(e, 'source_id', None), getattr(e, 'target_id', None), getattr(e, 'relation_type', None)]
            for e in getattr(radical, 'edges', ())
        ),
    }
    return _cost('RADICAL', radical_id, graph_payload, ordered, registry, runtime)


def cost_path(path: object, registry: MassCostRegistry, runtime: CostRuntimeContext) -> GraphCost:
    path_id = getattr(path, 'path_id', None)
    node_ids = tuple(getattr(path, 'node_ids', ()))
    if not isinstance(path_id, str) or not path_id or not node_ids:
        raise MassAwareCostV21Error('CanonicalPath-compatible object required')
    payload = {
        'path_id': path_id,
        'level': getattr(path, 'level', None),
        'node_ids': node_ids,
        'relation_ids': tuple(getattr(path, 'relation_ids', ())),
        'basis_id': getattr(path, 'basis_id', None),
    }
    return _cost('PATH', path_id, payload, node_ids, registry, runtime)


def cost_program(content: object, kaku_ids: Sequence[str], registry: MassCostRegistry, runtime: CostRuntimeContext) -> GraphCost:
    verify = getattr(content, 'verify', None)
    if callable(verify):
        verify()
    content_id = getattr(content, 'content_id', None)
    leaf_path = tuple(getattr(content, 'leaf_path', ()))
    canonical_graph = getattr(content, 'canonical_graph', None)
    if not isinstance(content_id, str) or not content_id or not leaf_path or canonical_graph is None:
        raise MassAwareCostV21Error('DefinitionContent-compatible program required')
    return _cost('PROGRAM', content_id, canonical_graph, tuple(kaku_ids), registry, runtime, leaf_path)


def _predicate_tuple(node: object) -> tuple[object, ...]:
    if isinstance(node, tuple):
        return node
    value = getattr(node, 'canonical_tuple', None)
    if isinstance(value, tuple):
        return value
    raise MassAwareCostV21Error('pure predicate canonical tuple required')


def predicate_leaf_path(node: object) -> tuple[str, ...]:
    t = _predicate_tuple(node)
    kind = t[0] if t else None
    if kind == 'comparison':
        if len(t) != 4:
            raise MassAwareCostV21Error('malformed comparison tuple')
        return ('DIFFERENCE', 'CONDITION')
    if kind == 'not':
        if len(t) != 2:
            raise MassAwareCostV21Error('malformed NOT tuple')
        return predicate_leaf_path(t[1]) + ('NEGATION',)
    if kind in {'and', 'or'}:
        if len(t) < 3:
            raise MassAwareCostV21Error('compound predicate requires at least two terms')
        leaves: tuple[str, ...] = ()
        for child in t[1:]:
            leaves += predicate_leaf_path(child)
        return leaves + ('COMPOSITION',) * (len(t) - 2)
    raise MassAwareCostV21Error(f'non-pure predicate node: {kind!r}')


def cost_predicate(predicate: object, predicate_id: str, kaku_ids: Sequence[str], registry: MassCostRegistry, runtime: CostRuntimeContext) -> GraphCost:
    graph = _predicate_tuple(predicate)
    leaves = predicate_leaf_path(graph)
    return _cost('PREDICATE', predicate_id, graph, tuple(kaku_ids), registry, runtime, leaves)
