from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Mapping

from .definitions_v11 import DefinitionContent, branch_content
from .natural_v15 import (
    NaturalRegistry,
    NaturalResolution,
    NaturalV15Error,
    default_natural_registry,
    resolve_natural_predicate,
)
from .surface_v09 import BranchProgram, Comparison, Predicate


class NaturalControlV16Error(ValueError):
    pass


_ROUTE_NAME_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_CONTROL_RE = re.compile(
    r"^\s*IF\s+(?P<predicate>.+?)\s+THEN\s+"
    r"(?P<true_verb>GO(?:\s+TO)?|ROUTE\s+TO)\s+(?P<true_route>.+?)"
    r"(?:\s+ELSE\s+(?P<false_verb>GO(?:\s+TO)?|ROUTE\s+TO)\s+(?P<false_route>.+?))?\s*$",
    re.IGNORECASE,
)


def _phrase(raw: str) -> str:
    if not isinstance(raw, str):
        raise NaturalControlV16Error("route phrase must be a string")
    return " ".join(raw.strip().lower().replace("_", " ").split())


@dataclass(frozen=True)
class RouteSpec:
    canonical: str
    aliases: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _ROUTE_NAME_RE.fullmatch(self.canonical):
            raise NaturalControlV16Error("canonical route must be a PNCS identifier")
        if not self.aliases:
            raise NaturalControlV16Error("route requires at least one alias")

    @property
    def route_kind(self) -> str:
        return "INTERNAL_TRANSFORM"


class RouteRegistry:
    def __init__(self) -> None:
        self._routes: dict[str, RouteSpec] = {}
        self._aliases: dict[str, str] = {}

    def register(self, spec: RouteSpec) -> RouteSpec:
        if spec.canonical in self._routes:
            raise NaturalControlV16Error(f"duplicate canonical route: {spec.canonical}")
        aliases = {_phrase(spec.canonical), *(_phrase(x) for x in spec.aliases)}
        for alias in aliases:
            if not alias:
                raise NaturalControlV16Error("empty route alias")
            prior = self._aliases.get(alias)
            if prior is not None and prior != spec.canonical:
                raise NaturalControlV16Error(f"ambiguous route alias: {alias}")
        self._routes[spec.canonical] = spec
        for alias in aliases:
            self._aliases[alias] = spec.canonical
        return spec

    def resolve(self, phrase: str) -> RouteSpec:
        alias = _phrase(phrase)
        canonical = self._aliases.get(alias)
        if canonical is None:
            raise NaturalControlV16Error(f"unknown internal route: {phrase}")
        return self._routes[canonical]


@dataclass(frozen=True)
class NaturalControlRegistry:
    predicates: NaturalRegistry
    routes: RouteRegistry


@dataclass(frozen=True)
class RouteResolutionStep:
    branch: str
    surface_route: str
    canonical_route: str
    route_kind: str = "INTERNAL_TRANSFORM"


@dataclass(frozen=True)
class NaturalControlResolution:
    source_text: str
    predicate_resolution: NaturalResolution
    true_route: RouteSpec
    false_route: RouteSpec | None
    content: DefinitionContent
    route_trace: tuple[RouteResolutionStep, ...]

    @property
    def content_id(self) -> str:
        return self.content.content_id

    @property
    def canonical_graph(self) -> tuple[object, ...]:
        return self.content.canonical_graph

    @property
    def leaf_path(self) -> tuple[str, ...]:
        return self.content.leaf_path

    @property
    def candidate_targets(self) -> tuple[str, ...]:
        if self.false_route is None:
            return (self.true_route.canonical,)
        return (self.true_route.canonical, self.false_route.canonical)

    @property
    def branch_program(self) -> BranchProgram:
        return BranchProgram(
            predicate=self.predicate_resolution.predicate,
            true_target=self.true_route.canonical,
            false_target=None if self.false_route is None else self.false_route.canonical,
        )


@dataclass(frozen=True)
class RouteAdmission:
    truth_state: str
    admitted_target: str | None
    epistemic_operator: str | None

    def __post_init__(self) -> None:
        if self.truth_state not in {"TRUE", "FALSE", "UNRESOLVED"}:
            raise NaturalControlV16Error("invalid truth state")
        if self.truth_state == "UNRESOLVED":
            if self.admitted_target is not None or self.epistemic_operator != "CHYBA":
                raise NaturalControlV16Error("unresolved branch must remain CHYBA with no admitted route")
        elif self.epistemic_operator is not None:
            raise NaturalControlV16Error("resolved branch must not carry CHYBA")


def default_route_registry() -> RouteRegistry:
    routes = RouteRegistry()
    routes.register(RouteSpec("safety.pause", ("safety pause", "pause safety")))
    routes.register(RouteSpec("runtime.continue", ("runtime continue", "continue runtime")))
    routes.register(RouteSpec("cooling.emergency", ("cooling emergency", "emergency cooling")))
    routes.register(RouteSpec("runtime.memory.relief", ("runtime memory relief", "memory relief")))
    routes.register(RouteSpec("phasenav.coherence.recover", ("phasenav coherence recover", "coherence recovery")))
    routes.register(RouteSpec("physics.gravity.low", ("physics gravity low", "low gravity path")))
    return routes


def default_control_registry() -> NaturalControlRegistry:
    return NaturalControlRegistry(
        predicates=default_natural_registry(),
        routes=default_route_registry(),
    )


def _strip_terminal_period(text: str) -> str:
    text = text.strip()
    if text.endswith("."):
        return text[:-1].rstrip()
    return text


def resolve_natural_control(
    text: str,
    registry: NaturalControlRegistry | None = None,
) -> NaturalControlResolution:
    if not isinstance(text, str) or not text.strip():
        raise NaturalControlV16Error("non-empty natural control statement required")
    active = registry or default_control_registry()
    source = _strip_terminal_period(text)
    match = _CONTROL_RE.fullmatch(source)
    if match is None:
        raise NaturalControlV16Error(
            "surface does not match bounded v0.16 IF/THEN/ELSE internal-route grammar"
        )

    try:
        predicate_resolution = resolve_natural_predicate(match.group("predicate"), active.predicates)
    except NaturalV15Error as exc:
        raise NaturalControlV16Error(str(exc)) from exc

    true_surface = match.group("true_route")
    false_surface = match.group("false_route")
    true_route = active.routes.resolve(true_surface)
    false_route = active.routes.resolve(false_surface) if false_surface is not None else None

    program = BranchProgram(
        predicate=predicate_resolution.predicate,
        true_target=true_route.canonical,
        false_target=None if false_route is None else false_route.canonical,
    )
    content = branch_content(program)
    trace = [
        RouteResolutionStep("TRUE", true_surface, true_route.canonical),
    ]
    if false_route is not None and false_surface is not None:
        trace.append(RouteResolutionStep("FALSE", false_surface, false_route.canonical))
    return NaturalControlResolution(
        source_text=text,
        predicate_resolution=predicate_resolution,
        true_route=true_route,
        false_route=false_route,
        content=content,
        route_trace=tuple(trace),
    )


def _finite_value(values: Mapping[str, object], subject: str) -> float | None:
    if subject not in values:
        return None
    raw = values[subject]
    try:
        value = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return value


def _truth(predicate: Predicate, values: Mapping[str, object]) -> str:
    if predicate.kind == "comparison":
        term = predicate.terms[0]
        if not isinstance(term, Comparison):
            raise NaturalControlV16Error("malformed comparison predicate")
        value = _finite_value(values, term.subject)
        if value is None:
            return "UNRESOLVED"
        delta = value - term.threshold
        if term.comparator == "lt":
            return "TRUE" if delta < 0.0 else "FALSE"
        if term.comparator == "gt":
            return "TRUE" if delta > 0.0 else "FALSE"
        if term.comparator == "eq":
            return "TRUE" if delta == 0.0 else "FALSE"
        raise NaturalControlV16Error("unsupported canonical comparator")

    if predicate.kind == "not":
        inner = _truth(predicate.terms[0], values)
        if inner == "UNRESOLVED":
            return inner
        return "FALSE" if inner == "TRUE" else "TRUE"

    if predicate.kind == "and":
        states = tuple(_truth(term, values) for term in predicate.terms)
        if "FALSE" in states:
            return "FALSE"
        if "UNRESOLVED" in states:
            return "UNRESOLVED"
        return "TRUE"

    if predicate.kind == "or":
        states = tuple(_truth(term, values) for term in predicate.terms)
        if "TRUE" in states:
            return "TRUE"
        if "UNRESOLVED" in states:
            return "UNRESOLVED"
        return "FALSE"

    raise NaturalControlV16Error(f"unsupported predicate kind: {predicate.kind}")


def admit_internal_route(
    resolution: NaturalControlResolution,
    values: Mapping[str, object],
) -> RouteAdmission:
    state = _truth(resolution.predicate_resolution.predicate, values)
    if state == "UNRESOLVED":
        return RouteAdmission("UNRESOLVED", None, "CHYBA")
    if state == "TRUE":
        return RouteAdmission("TRUE", resolution.true_route.canonical, None)
    target = None if resolution.false_route is None else resolution.false_route.canonical
    return RouteAdmission("FALSE", target, None)
