from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .surface_v09 import Comparison, Predicate, SurfaceV09Error, parse_predicate


class AlgebraV10Error(ValueError):
    pass


@dataclass(frozen=True)
class EquivalenceResult:
    equivalent: bool
    left_key: tuple[object, ...]
    right_key: tuple[object, ...]


def _pred(kind: str, terms: Iterable[Predicate]) -> Predicate:
    return Predicate(kind, tuple(terms))


def _key(node: Predicate) -> tuple[object, ...]:
    return node.canonical_tuple


def _dedupe_sorted(terms: Iterable[Predicate]) -> tuple[Predicate, ...]:
    by_key: dict[tuple[object, ...], Predicate] = {}
    for term in terms:
        by_key[_key(term)] = term
    return tuple(by_key[k] for k in sorted(by_key, key=repr))


def _flatten(kind: str, terms: Iterable[Predicate]) -> tuple[Predicate, ...]:
    out: list[Predicate] = []
    for term in terms:
        if term.kind == kind:
            out.extend(term.terms)  # type: ignore[arg-type]
        else:
            out.append(term)
    return tuple(out)


def to_nnf(node: Predicate) -> Predicate:
    """Return negation normal form for the pure v0.9 predicate subset.

    This transformation is scoped to comparison predicates composed by AND/OR/NOT.
    It does not apply to action/effect nodes or arbitrary PNV COMPOSITION graphs.
    """
    if node.kind == "comparison":
        return node
    if node.kind in {"and", "or"}:
        return _pred(node.kind, (to_nnf(t) for t in node.terms))
    if node.kind == "not":
        inner = node.terms[0]
        assert isinstance(inner, Predicate)
        if inner.kind == "comparison":
            return node
        if inner.kind == "not":
            grand = inner.terms[0]
            assert isinstance(grand, Predicate)
            return to_nnf(grand)
        if inner.kind == "and":
            return _pred("or", (to_nnf(_pred("not", (t,))) for t in inner.terms))
        if inner.kind == "or":
            return _pred("and", (to_nnf(_pred("not", (t,))) for t in inner.terms))
    raise AlgebraV10Error(f"unsupported predicate kind: {node.kind}")


def _absorb(kind: str, terms: tuple[Predicate, ...]) -> tuple[Predicate, ...]:
    """Apply Boolean absorption for pure predicates only.

    AND: A AND (A OR B) = A
    OR:  A OR  (A AND B) = A
    """
    opposite = "or" if kind == "and" else "and"
    simple_keys = {_key(t) for t in terms if t.kind != opposite}
    out: list[Predicate] = []
    for term in terms:
        if term.kind == opposite:
            child_keys = {_key(c) for c in term.terms}
            if simple_keys & child_keys:
                continue
        out.append(term)
    return tuple(out)


def normalize_boolean(node: Predicate) -> Predicate:
    """Canonical Boolean form for the frozen pure-predicate subset.

    Admitted rewrites:
    - double negation elimination,
    - De Morgan pushdown,
    - associative flattening of same operator,
    - commutative ordering by structural key,
    - idempotent duplicate removal,
    - absorption.

    Distribution and constant folding are intentionally not performed in v0.10.
    """
    node = to_nnf(node)
    if node.kind == "comparison":
        return node
    if node.kind == "not":
        inner = node.terms[0]
        assert isinstance(inner, Predicate) and inner.kind == "comparison"
        return node
    if node.kind in {"and", "or"}:
        terms = tuple(normalize_boolean(t) for t in node.terms)
        terms = _flatten(node.kind, terms)
        terms = _dedupe_sorted(terms)
        terms = _absorb(node.kind, terms)
        terms = _dedupe_sorted(terms)
        if not terms:
            raise AlgebraV10Error("constant-folding boundary reached; no TRUE/FALSE primitive admitted")
        if len(terms) == 1:
            return terms[0]
        return Predicate(node.kind, terms)
    raise AlgebraV10Error(f"unsupported predicate kind: {node.kind}")


def equivalence_key(node: Predicate | str) -> tuple[object, ...]:
    if isinstance(node, str):
        node = parse_predicate(node)
    return normalize_boolean(node).canonical_tuple


def equivalent(left: Predicate | str, right: Predicate | str) -> EquivalenceResult:
    lk = equivalence_key(left)
    rk = equivalence_key(right)
    return EquivalenceResult(lk == rk, lk, rk)


def assert_pure_predicate(node: Predicate) -> None:
    if node.kind == "comparison":
        term = node.terms[0]
        if not isinstance(term, Comparison):
            raise AlgebraV10Error("malformed comparison predicate")
        return
    if node.kind in {"and", "or", "not"}:
        for term in node.terms:
            if not isinstance(term, Predicate):
                raise AlgebraV10Error("non-predicate term in Boolean algebra")
            assert_pure_predicate(term)
        return
    raise AlgebraV10Error(f"non-pure predicate node: {node.kind}")
