from __future__ import annotations

import hashlib
from typing import Iterable

from .gremlin_relational_compiler_v01 import (
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
)


class GremlinIsomorphicCodecMergeError(RuntimeError):
    pass


def _node_signature(node: RelationalNode):
    k = node.kaku
    return (
        k.kaku_id,
        tuple(k.vector.values),
        k.vector.basis_id,
        float(k.semantic_mass),
        k.direction,
        float(k.polarity),
        k.role,
        None if k.phase is None else tuple(k.phase),
        node.domain,
        node.observation_ref,
    )


def _edge_signature(edge: RelationalEdge):
    return (edge.relation_id, edge.source_id, edge.target_id, edge.relation_type)


def merge_relational_isomorphisms(
    specs: Iterable[RelationalIsomorphism],
    *,
    merged_isomorphism_id: str | None = None,
) -> RelationalIsomorphism:
    parts = tuple(specs)
    if len(parts) < 2:
        raise GremlinIsomorphicCodecMergeError("at least two isomorphism fragments are required")

    invariant_ids = {spec.invariant_id for spec in parts}
    if len(invariant_ids) != 1:
        raise GremlinIsomorphicCodecMergeError("isomorphism fragments must share one invariant_id")

    descriptions = {spec.invariant_description for spec in parts}
    if len(descriptions) != 1:
        raise GremlinIsomorphicCodecMergeError("isomorphism fragments must share one invariant description")

    nodes: dict[str, RelationalNode] = {}
    node_sigs: dict[str, tuple] = {}
    edges: dict[str, RelationalEdge] = {}
    edge_sigs: dict[str, tuple] = {}
    evidence: set[str] = set()

    for spec in parts:
        evidence.update(spec.evidence_refs)
        evidence.add(f"isomorphism-fragment:{spec.isomorphism_id}")
        for node in spec.nodes:
            key = node.kaku.kaku_id
            sig = _node_signature(node)
            if key in node_sigs and node_sigs[key] != sig:
                raise GremlinIsomorphicCodecMergeError(f"conflicting KAKU node during isomorphic merge: {key}")
            nodes[key] = node
            node_sigs[key] = sig
        for edge in spec.edges:
            key = edge.relation_id
            sig = _edge_signature(edge)
            if key in edge_sigs and edge_sigs[key] != sig:
                raise GremlinIsomorphicCodecMergeError(f"conflicting relation during isomorphic merge: {key}")
            edges[key] = edge
            edge_sigs[key] = sig

    invariant_id = next(iter(invariant_ids))
    description = next(iter(descriptions))
    if merged_isomorphism_id is None:
        digest = hashlib.sha256(
            "|".join(sorted(spec.isomorphism_id for spec in parts)).encode("utf-8")
        ).hexdigest()[:16]
        merged_isomorphism_id = f"ISO.MERGED.{digest.upper()}"

    return RelationalIsomorphism(
        isomorphism_id=merged_isomorphism_id,
        invariant_id=invariant_id,
        invariant_description=description,
        nodes=tuple(nodes[key] for key in sorted(nodes)),
        edges=tuple(edges[key] for key in sorted(edges)),
        evidence_refs=tuple(sorted(evidence)),
    )
