from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable

from .algebra_v10 import normalize_boolean
from .definitions_v11 import DefinitionContent, predicate_content
from .surface_v09 import Comparison, Predicate


class NaturalV15Error(ValueError):
    pass


_TOKEN_RE = re.compile(
    r"\s*(\(|\)|==|<=|>=|!=|<|>|-?(?:\d+(?:\.\d*)?|\.\d+)%?|[A-Za-z_][A-Za-z0-9_.:-]*)"
)
_NAME_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")


def _phrase(parts: Iterable[str] | str) -> str:
    if isinstance(parts, str):
        raw = parts
    else:
        raw = " ".join(parts)
    raw = raw.strip().lower().replace("_", " ")
    return " ".join(raw.split())


@dataclass(frozen=True)
class SymbolSpec:
    canonical: str
    aliases: tuple[str, ...]
    percent_is_fraction: bool = False

    def __post_init__(self) -> None:
        if not _NAME_RE.fullmatch(self.canonical):
            raise NaturalV15Error("canonical symbol must be a PNCS identifier")
        if not self.aliases:
            raise NaturalV15Error("symbol requires at least one alias")


class SymbolRegistry:
    def __init__(self) -> None:
        self._symbols: dict[str, SymbolSpec] = {}
        self._aliases: dict[str, str] = {}

    def register(self, spec: SymbolSpec) -> SymbolSpec:
        if spec.canonical in self._symbols:
            raise NaturalV15Error(f"duplicate canonical symbol: {spec.canonical}")
        aliases = {_phrase(spec.canonical), *(_phrase(x) for x in spec.aliases)}
        for alias in aliases:
            if not alias:
                raise NaturalV15Error("empty symbol alias")
            prior = self._aliases.get(alias)
            if prior is not None and prior != spec.canonical:
                raise NaturalV15Error(f"ambiguous symbol alias: {alias}")
        self._symbols[spec.canonical] = spec
        for alias in aliases:
            self._aliases[alias] = spec.canonical
        return spec

    def resolve(self, phrase: str) -> SymbolSpec:
        alias = _phrase(phrase)
        canonical = self._aliases.get(alias)
        if canonical is None:
            raise NaturalV15Error(f"unknown natural symbol: {phrase}")
        return self._symbols[canonical]


@dataclass(frozen=True)
class RelationSpec:
    comparator: str
    aliases: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.comparator not in {"lt", "gt", "eq"}:
            raise NaturalV15Error("v0.15 admits only lt/gt/eq relations")
        if not self.aliases:
            raise NaturalV15Error("relation requires at least one alias")


class RelationRegistry:
    def __init__(self) -> None:
        self._aliases: dict[str, str] = {}

    def register(self, spec: RelationSpec) -> RelationSpec:
        for raw in spec.aliases:
            alias = _phrase(raw) if raw not in {"<", ">", "=="} else raw
            if not alias:
                raise NaturalV15Error("empty relation alias")
            prior = self._aliases.get(alias)
            if prior is not None and prior != spec.comparator:
                raise NaturalV15Error(f"ambiguous relation alias: {alias}")
            self._aliases[alias] = spec.comparator
        return spec

    def candidates(self, tokens: list[str]) -> tuple[tuple[int, int, str, str], ...]:
        out: list[tuple[int, int, str, str]] = []
        for i in range(len(tokens)):
            for j in range(i + 1, len(tokens) + 1):
                raw = " ".join(tokens[i:j])
                key = raw if raw in {"<", ">", "=="} else _phrase(raw)
                comparator = self._aliases.get(key)
                if comparator is not None:
                    out.append((i, j, comparator, key))
        return tuple(out)


@dataclass(frozen=True)
class ResolutionStep:
    surface_subject: str
    canonical_subject: str
    surface_relation: str
    comparator: str
    surface_scalar: str
    canonical_scalar: float


@dataclass(frozen=True)
class NaturalResolution:
    source_text: str
    predicate: Predicate
    content: DefinitionContent
    trace: tuple[ResolutionStep, ...]

    @property
    def content_id(self) -> str:
        return self.content.content_id

    @property
    def canonical_graph(self) -> tuple[object, ...]:
        return self.content.canonical_graph

    @property
    def leaf_path(self) -> tuple[str, ...]:
        return self.content.leaf_path


@dataclass(frozen=True)
class NaturalRegistry:
    symbols: SymbolRegistry
    relations: RelationRegistry


def default_natural_registry() -> NaturalRegistry:
    symbols = SymbolRegistry()
    symbols.register(SymbolSpec("risk", ("risk",), percent_is_fraction=True))
    symbols.register(SymbolSpec("phase_coherence", ("phase coherence", "phase_coherence"), percent_is_fraction=True))
    symbols.register(SymbolSpec("memory_pressure", ("memory pressure", "memory_pressure"), percent_is_fraction=True))
    symbols.register(SymbolSpec("temperature", ("temperature",)))
    symbols.register(SymbolSpec("phase_error", ("phase error", "phase_error")))
    symbols.register(SymbolSpec("gravity", ("gravity",)))

    relations = RelationRegistry()
    relations.register(RelationSpec("gt", (">", "above", "is above", "greater than", "is greater than", "exceeds")))
    relations.register(RelationSpec("lt", ("<", "below", "is below", "less than", "is less than", "under")))
    relations.register(RelationSpec("eq", ("==", "equal", "equal to", "is equal to", "equals")))
    return NaturalRegistry(symbols=symbols, relations=relations)


def _tokenize(text: str) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        raise NaturalV15Error("non-empty natural predicate required")
    text = text.strip()
    if text.endswith("."):
        text = text[:-1].rstrip()
    out: list[str] = []
    pos = 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise NaturalV15Error(f"unsupported token near: {text[pos:pos+24]!r}")
        out.append(m.group(1))
        pos = m.end()
    if not out:
        raise NaturalV15Error("non-empty natural predicate required")
    return out


def _scalar(raw: str, symbol: SymbolSpec) -> float:
    is_percent = raw.endswith("%")
    number = raw[:-1] if is_percent else raw
    try:
        value = float(number)
    except ValueError as exc:
        raise NaturalV15Error(f"numeric scalar required: {raw}") from exc
    if not math.isfinite(value):
        raise NaturalV15Error("finite scalar required")
    if is_percent:
        if not symbol.percent_is_fraction:
            raise NaturalV15Error(f"percent surface is not admitted for {symbol.canonical}")
        value /= 100.0
    return value


def _resolve_atom(tokens: list[str], registry: NaturalRegistry) -> tuple[Predicate, ResolutionStep]:
    if len(tokens) < 3:
        raise NaturalV15Error("natural comparison requires subject, relation and scalar")
    scalar_raw = tokens[-1]
    relation_space = tokens[:-1]
    if any(x in {">=", "<=", "!="} for x in relation_space):
        raise NaturalV15Error("v0.15 does not admit >=, <= or !=")

    valid: list[tuple[Predicate, ResolutionStep]] = []
    for i, j, comparator, relation_surface in registry.relations.candidates(relation_space):
        if j != len(relation_space):
            continue
        subject_tokens = relation_space[:i]
        if not subject_tokens:
            continue
        subject_surface = " ".join(subject_tokens)
        try:
            symbol = registry.symbols.resolve(subject_surface)
        except NaturalV15Error:
            continue
        value = _scalar(scalar_raw, symbol)
        comparison = Comparison(symbol.canonical, comparator, value)
        predicate = Predicate("comparison", (comparison,))
        step = ResolutionStep(
            surface_subject=subject_surface,
            canonical_subject=symbol.canonical,
            surface_relation=relation_surface,
            comparator=comparator,
            surface_scalar=scalar_raw,
            canonical_scalar=value,
        )
        valid.append((predicate, step))

    unique: dict[tuple[object, ...], tuple[Predicate, ResolutionStep]] = {}
    for predicate, step in valid:
        unique[predicate.canonical_tuple] = (predicate, step)
    if not unique:
        raise NaturalV15Error("natural comparison did not resolve to a registered relation")
    if len(unique) != 1:
        raise NaturalV15Error("natural comparison is semantically ambiguous")
    return next(iter(unique.values()))


class _NaturalParser:
    def __init__(self, tokens: list[str], registry: NaturalRegistry):
        self.tokens = tokens
        self.registry = registry
        self.i = 0
        self.trace: list[ResolutionStep] = []

    def peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self) -> str:
        tok = self.peek()
        if tok is None:
            raise NaturalV15Error("unexpected end of natural predicate")
        self.i += 1
        return tok

    def parse(self) -> Predicate:
        node = self.parse_level()
        if self.peek() is not None:
            raise NaturalV15Error(f"unexpected token: {self.peek()}")
        return node

    def parse_level(self) -> Predicate:
        first = self.parse_primary()
        connector = self.peek()
        if connector is None or connector.lower() not in {"and", "or"}:
            return first
        op = self.take().lower()
        terms = [first, self.parse_primary()]
        while True:
            nxt = self.peek()
            if nxt is None or nxt == ")":
                break
            low = nxt.lower()
            if low not in {"and", "or"}:
                raise NaturalV15Error(f"unexpected token in compound predicate: {nxt}")
            if low != op:
                raise NaturalV15Error("mixed AND/OR at one level requires explicit grouping")
            self.take()
            terms.append(self.parse_primary())
        return Predicate(op, tuple(terms))

    def parse_primary(self) -> Predicate:
        tok = self.peek()
        if tok is None:
            raise NaturalV15Error("predicate term required")
        if tok.lower() == "not":
            self.take()
            return Predicate("not", (self.parse_primary(),))
        if tok == "(":
            self.take()
            if self.peek() == ")":
                raise NaturalV15Error("empty predicate group")
            node = self.parse_level()
            if self.take() != ")":
                raise NaturalV15Error("unclosed predicate group")
            return node

        start = self.i
        depth = 0
        while self.i < len(self.tokens):
            cur = self.tokens[self.i]
            if cur == "(":
                depth += 1
            elif cur == ")":
                if depth == 0:
                    break
                depth -= 1
            if depth == 0 and cur.lower() in {"and", "or"}:
                break
            self.i += 1
        atom_tokens = self.tokens[start:self.i]
        predicate, step = _resolve_atom(atom_tokens, self.registry)
        self.trace.append(step)
        return predicate


def resolve_natural_predicate(text: str, registry: NaturalRegistry | None = None) -> NaturalResolution:
    active = registry or default_natural_registry()
    parser = _NaturalParser(_tokenize(text), active)
    parsed = parser.parse()
    normalized = normalize_boolean(parsed)
    content = predicate_content(normalized)
    return NaturalResolution(
        source_text=text,
        predicate=normalized,
        content=content,
        trace=tuple(parser.trace),
    )
