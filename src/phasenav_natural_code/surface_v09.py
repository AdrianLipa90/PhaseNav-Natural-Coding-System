from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Mapping


class SurfaceV09Error(ValueError):
    pass


_WORD_REL = {"BELOW": "lt", "ABOVE": "gt", "EQUAL": "eq"}
_SYM_REL = {"<": "lt", ">": "gt", "==": "eq"}
_NUM_RE = re.compile(r"^-?(?:\d+(?:\.\d*)?|\.\d+)$")
_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]*$")
_TOKEN_RE = re.compile(
    r"\s*(\(|\)|==|<=|>=|!=|<|>|-?(?:\d+(?:\.\d*)?|\.\d+)|[A-Za-z_][A-Za-z0-9_.:-]*)"
)
_PROGRAM_RE = re.compile(
    r"^\s*IF\s+(?P<predicate>.+?)\s+THEN\s+GO\s+(?P<true>[^\s()]+)"
    r"(?:\s+ELSE\s+GO\s+(?P<false>[^\s()]+))?\s*$",
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
            # N terms require N-1 COMPOSITION nodes. Same-kind chains are flattened.
            if len(self.terms) < 2:
                raise SurfaceV09Error("compound predicate requires at least two terms")
            leaves: tuple[str, ...] = ()
            for term in self.terms:
                assert isinstance(term, Predicate)
                leaves += term.leaf_path
            return leaves + ("COMPOSITION",) * (len(self.terms) - 1)
        if self.kind == "not":
            (inner,) = self.terms
            assert isinstance(inner, Predicate)
            return inner.leaf_path + ("NEGATION",)
        raise SurfaceV09Error(f"unsupported predicate kind: {self.kind}")

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
        raise SurfaceV09Error("finite threshold required")
    return value


def _tokenize(text: str) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        raise SurfaceV09Error("non-empty predicate required")
    out: list[str] = []
    pos = 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise SurfaceV09Error(f"unsupported token near: {text[pos:pos+24]!r}")
        out.append(m.group(1))
        pos = m.end()
    if not out:
        raise SurfaceV09Error("non-empty predicate required")
    return out


class _Parser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self) -> str:
        tok = self.peek()
        if tok is None:
            raise SurfaceV09Error("unexpected end of predicate")
        self.i += 1
        return tok

    def parse(self) -> Predicate:
        node = self.parse_level()
        if self.peek() is not None:
            raise SurfaceV09Error(f"unexpected token: {self.peek()}")
        return node

    def parse_level(self) -> Predicate:
        first = self.parse_primary()
        connector = self.peek()
        if connector is None or connector.upper() not in {"AND", "OR"}:
            return first

        op = self.take().lower()
        terms = [first, self.parse_primary()]
        while True:
            nxt = self.peek()
            if nxt is None or nxt == ")":
                break
            up = nxt.upper()
            if up not in {"AND", "OR"}:
                raise SurfaceV09Error(f"unexpected token in compound predicate: {nxt}")
            if up.lower() != op:
                raise SurfaceV09Error("mixed AND/OR at one level requires explicit grouping")
            self.take()
            terms.append(self.parse_primary())
        return Predicate(op, tuple(terms))

    def parse_primary(self) -> Predicate:
        tok = self.peek()
        if tok is None:
            raise SurfaceV09Error("predicate term required")

        if tok.upper() == "NOT":
            self.take()
            return Predicate("not", (self.parse_primary(),))

        if tok == "(":
            self.take()
            if self.peek() == ")":
                raise SurfaceV09Error("empty predicate group")
            node = self.parse_level()
            if self.take() != ")":
                raise SurfaceV09Error("unclosed predicate group")
            return node

        return Predicate("comparison", (self.parse_comparison(),))

    def parse_comparison(self) -> Comparison:
        subject = self.take()
        if not _NAME_RE.match(subject) or subject.upper() in {"AND", "OR", "NOT", "BELOW", "ABOVE", "EQUAL"}:
            raise SurfaceV09Error(f"invalid comparison subject: {subject}")

        raw_rel = self.take()
        comparator = _WORD_REL.get(raw_rel.upper(), _SYM_REL.get(raw_rel))
        if comparator is None:
            raise SurfaceV09Error(f"unsupported comparator: {raw_rel}")

        raw_threshold = self.take()
        if not _NUM_RE.match(raw_threshold):
            raise SurfaceV09Error(f"invalid scalar threshold: {raw_threshold}")
        return Comparison(subject, comparator, _finite_number(raw_threshold))


def parse_predicate(text: str) -> Predicate:
    return _Parser(_tokenize(text)).parse()


def normalize_branch_surface(text: str) -> BranchProgram:
    if not isinstance(text, str) or not text.strip():
        raise SurfaceV09Error("non-empty branch surface required")
    m = _PROGRAM_RE.match(text)
    if not m:
        raise SurfaceV09Error("surface does not match frozen v0.9 branch grammar")
    predicate = parse_predicate(m.group("predicate"))
    return BranchProgram(predicate, m.group("true"), m.group("false"))


def evaluate_predicate(predicate: Predicate, values: Mapping[str, float]) -> bool:
    if predicate.kind == "comparison":
        term = predicate.terms[0]
        assert isinstance(term, Comparison)
        if term.subject not in values:
            raise SurfaceV09Error(f"missing value for {term.subject}")
        value = float(values[term.subject])
        if not math.isfinite(value):
            raise SurfaceV09Error(f"finite value required for {term.subject}")
        delta = value - term.threshold
        if term.comparator == "lt":
            return delta < 0.0
        if term.comparator == "gt":
            return delta > 0.0
        if term.comparator == "eq":
            return delta == 0.0
        raise SurfaceV09Error("unsupported canonical comparator")
    if predicate.kind == "and":
        return all(evaluate_predicate(term, values) for term in predicate.terms)
    if predicate.kind == "or":
        return any(evaluate_predicate(term, values) for term in predicate.terms)
    if predicate.kind == "not":
        return not evaluate_predicate(predicate.terms[0], values)
    raise SurfaceV09Error("unsupported predicate kind")


def select_route(program: BranchProgram, values: Mapping[str, float]) -> str | None:
    if evaluate_predicate(program.predicate, values):
        return program.true_target
    return program.false_target
