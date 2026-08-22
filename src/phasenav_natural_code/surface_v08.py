from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Mapping


class SurfaceV08Error(ValueError):
    pass


_WORD_REL = {"BELOW": "lt", "ABOVE": "gt", "EQUAL": "eq"}
_SYM_REL = {"<": "lt", ">": "gt", "==": "eq"}
_NUM = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
_NAME = r"[^\s]+"
_CLAUSE = rf"(?P<s>{_NAME})\s*(?P<rel>BELOW|ABOVE|EQUAL|==|<|>)\s*(?P<t>{_NUM})"

_SIMPLE_RE = re.compile(rf"^\s*{_CLAUSE}\s*$", re.I)
_NOT_RE = re.compile(rf"^\s*NOT\s+{_CLAUSE}\s*$", re.I)
_COMPOUND_RE = re.compile(
    rf"^\s*(?P<left>{_NAME}\s*(?:BELOW|ABOVE|EQUAL|==|<|>)\s*{_NUM})\s+"
    rf"(?P<logic>AND|OR)\s+"
    rf"(?P<right>{_NAME}\s*(?:BELOW|ABOVE|EQUAL|==|<|>)\s*{_NUM})\s*$",
    re.I,
)
_PROGRAM_RE = re.compile(
    r"^\s*IF\s+(?P<predicate>.+?)\s+THEN\s+GO\s+(?P<true>[^\s]+)"
    r"(?:\s+ELSE\s+GO\s+(?P<false>[^\s]+))?\s*$",
    re.I,
)


@dataclass(frozen=True)
class Comparison:
    subject: str
    comparator: str
    threshold: float

    @property
    def leaf_path(self) -> tuple[str, ...]:
        return ("DIFFERENCE", "CONDITION")

    @property
    def canonical_tuple(self) -> tuple[object, ...]:
        return ("comparison", self.subject, self.comparator, self.threshold)


@dataclass(frozen=True)
class Predicate:
    kind: str
    terms: tuple[Comparison | "Predicate", ...]

    @property
    def leaf_path(self) -> tuple[str, ...]:
        if self.kind == "comparison":
            term = self.terms[0]
            assert isinstance(term, Comparison)
            return term.leaf_path
        if self.kind in {"and", "or"}:
            left, right = self.terms
            return left.leaf_path + right.leaf_path + ("COMPOSITION",)
        if self.kind == "not":
            (inner,) = self.terms
            return inner.leaf_path + ("NEGATION",)
        raise SurfaceV08Error(f"unsupported predicate kind: {self.kind}")

    @property
    def canonical_tuple(self) -> tuple[object, ...]:
        if self.kind == "comparison":
            term = self.terms[0]
            assert isinstance(term, Comparison)
            return term.canonical_tuple
        return (self.kind,) + tuple(term.canonical_tuple for term in self.terms)


@dataclass(frozen=True)
class BranchProgram:
    predicate: Predicate
    true_target: str
    false_target: str | None = None

    @property
    def leaf_path(self) -> tuple[str, ...]:
        if self.false_target is None:
            return self.predicate.leaf_path + ("ORDER", "TRANSFORM", "COMPOSITION")
        return self.predicate.leaf_path + (
            "NEGATION",
            "ORDER",
            "TRANSFORM",
            "ORDER",
            "TRANSFORM",
            "COMPOSITION",
        )

    @property
    def canonical_tuple(self) -> tuple[object, ...]:
        return (self.predicate.canonical_tuple, self.true_target, self.false_target)


def _finite_number(raw: str) -> float:
    value = float(raw)
    if not math.isfinite(value):
        raise SurfaceV08Error("finite threshold required")
    return value


def _comparison_from_match(m: re.Match[str]) -> Comparison:
    raw_rel = m.group("rel")
    comparator = _WORD_REL.get(raw_rel.upper(), _SYM_REL.get(raw_rel))
    if comparator is None:
        raise SurfaceV08Error("unsupported comparator")
    return Comparison(m.group("s"), comparator, _finite_number(m.group("t")))


def _parse_simple_clause(text: str) -> Comparison:
    m = _SIMPLE_RE.match(text)
    if not m:
        raise SurfaceV08Error("invalid comparison clause")
    return _comparison_from_match(m)


def parse_predicate(text: str) -> Predicate:
    if not isinstance(text, str) or not text.strip():
        raise SurfaceV08Error("non-empty predicate required")
    text = text.strip()

    m = _NOT_RE.match(text)
    if m:
        inner = Predicate("comparison", (_comparison_from_match(m),))
        return Predicate("not", (inner,))

    m = _COMPOUND_RE.match(text)
    if m:
        left = Predicate("comparison", (_parse_simple_clause(m.group("left")),))
        right = Predicate("comparison", (_parse_simple_clause(m.group("right")),))
        return Predicate(m.group("logic").lower(), (left, right))

    return Predicate("comparison", (_parse_simple_clause(text),))


def normalize_branch_surface(text: str) -> BranchProgram:
    if not isinstance(text, str) or not text.strip():
        raise SurfaceV08Error("non-empty branch surface required")
    m = _PROGRAM_RE.match(text)
    if not m:
        raise SurfaceV08Error("surface does not match frozen v0.8 branch grammar")
    predicate = parse_predicate(m.group("predicate"))
    return BranchProgram(predicate, m.group("true"), m.group("false"))


def evaluate_predicate(predicate: Predicate, values: Mapping[str, float]) -> bool:
    if predicate.kind == "comparison":
        term = predicate.terms[0]
        assert isinstance(term, Comparison)
        if term.subject not in values:
            raise SurfaceV08Error(f"missing value for {term.subject}")
        delta = float(values[term.subject]) - term.threshold
        if term.comparator == "lt":
            return delta < 0.0
        if term.comparator == "gt":
            return delta > 0.0
        if term.comparator == "eq":
            return delta == 0.0
        raise SurfaceV08Error("unsupported canonical comparator")
    if predicate.kind == "and":
        return all(evaluate_predicate(term, values) for term in predicate.terms)
    if predicate.kind == "or":
        return any(evaluate_predicate(term, values) for term in predicate.terms)
    if predicate.kind == "not":
        return not evaluate_predicate(predicate.terms[0], values)
    raise SurfaceV08Error("unsupported predicate kind")


def select_route(program: BranchProgram, values: Mapping[str, float]) -> str | None:
    if evaluate_predicate(program.predicate, values):
        return program.true_target
    return program.false_target
