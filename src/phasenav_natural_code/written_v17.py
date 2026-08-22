from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping

from .algebra_v10 import AlgebraV10Error
from .definitions_v11 import DefinitionContent, DefinitionV11Error, branch_content, predicate_content
from .surface_v09 import SurfaceV09Error, normalize_branch_surface, parse_predicate


class WrittenV17Error(ValueError):
    pass


_HEADER = "PNCS 0.17"
_KIND_RE = re.compile(r"^KIND (PREDICATE|INTERNAL_BRANCH)$")
_CID_RE = re.compile(r"^CID (pncs:def:sha256:[0-9a-f]{64})$")
_TARGET_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]*$")
_COMPARATOR_WORD = {"lt": "BELOW", "gt": "ABOVE", "eq": "EQUAL"}


def _number(value: object) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise WrittenV17Error("comparison threshold must be numeric")
    # repr(float) is a deterministic shortest round-trip decimal for IEEE-754 Python floats.
    return repr(float(value))


def _predicate_body(graph: tuple[object, ...]) -> str:
    if not graph:
        raise WrittenV17Error("empty predicate graph")
    kind = graph[0]
    if kind == "comparison":
        if len(graph) != 4:
            raise WrittenV17Error("malformed comparison graph")
        _, subject, comparator, threshold = graph
        if not isinstance(subject, str) or not _TARGET_RE.fullmatch(subject):
            raise WrittenV17Error("invalid canonical comparison subject")
        word = _COMPARATOR_WORD.get(comparator)
        if word is None:
            raise WrittenV17Error("unsupported canonical comparator")
        return f"{subject} {word} {_number(threshold)}"

    if kind in {"and", "or"}:
        if len(graph) < 3:
            raise WrittenV17Error("compound predicate requires at least two terms")
        op = str(kind).upper()
        children = []
        for child in graph[1:]:
            if not isinstance(child, tuple):
                raise WrittenV17Error("compound predicate child must be a tuple")
            children.append(_predicate_body(child))
        return "(" + f" {op} ".join(children) + ")"

    if kind == "not":
        if len(graph) != 2 or not isinstance(graph[1], tuple):
            raise WrittenV17Error("malformed NOT graph")
        return f"NOT ({_predicate_body(graph[1])})"

    raise WrittenV17Error(f"unsupported predicate graph kind: {kind}")


def _body(content: DefinitionContent) -> str:
    if content.kind == "PREDICATE":
        return _predicate_body(content.canonical_graph)

    if content.kind == "INTERNAL_BRANCH":
        graph = content.canonical_graph
        if len(graph) != 4 or graph[0] != "branch":
            raise WrittenV17Error("malformed internal branch graph")
        predicate_graph, true_target, false_target = graph[1], graph[2], graph[3]
        if not isinstance(predicate_graph, tuple):
            raise WrittenV17Error("branch predicate graph must be a tuple")
        if not isinstance(true_target, str) or not _TARGET_RE.fullmatch(true_target):
            raise WrittenV17Error("invalid canonical true route")
        if false_target is not None and (
            not isinstance(false_target, str) or not _TARGET_RE.fullmatch(false_target)
        ):
            raise WrittenV17Error("invalid canonical false route")
        body = f"IF {_predicate_body(predicate_graph)} THEN GO {true_target}"
        if false_target is not None:
            body += f" ELSE GO {false_target}"
        return body

    raise WrittenV17Error(f"unsupported definition kind: {content.kind}")


def render_written_projection(content: DefinitionContent) -> str:
    if not isinstance(content, DefinitionContent):
        raise WrittenV17Error("DefinitionContent required")
    content.verify()
    return (
        f"{_HEADER}\n"
        f"KIND {content.kind}\n"
        f"CID {content.content_id}\n"
        f"BODY {_body(content)}\n"
    )


@dataclass(frozen=True)
class WrittenProjection:
    content: DefinitionContent
    text: str

    @property
    def content_id(self) -> str:
        return self.content.content_id


class ProjectionRegistry:
    """Authority registry for v0.17 written projections.

    Text is not allowed to create semantic content. A parsed CID must already exist
    in this registry, and BODY must reconstruct exactly that registered content.
    """

    def __init__(self) -> None:
        self._by_content: dict[str, DefinitionContent] = {}

    def register(self, content: DefinitionContent) -> DefinitionContent:
        if not isinstance(content, DefinitionContent):
            raise WrittenV17Error("DefinitionContent required")
        content.verify()
        cid = content.content_id
        prior = self._by_content.get(cid)
        if prior is not None and prior.semantic_payload != content.semantic_payload:
            raise WrittenV17Error("content-address collision with non-identical payload")
        self._by_content[cid] = content
        return content

    def content(self, content_id: str) -> DefinitionContent:
        try:
            return self._by_content[content_id]
        except KeyError as exc:
            raise WrittenV17Error(f"projection CID is not registered: {content_id}") from exc

    def render(self, content_or_id: DefinitionContent | str) -> str:
        if isinstance(content_or_id, DefinitionContent):
            registered = self.content(content_or_id.content_id)
            if registered.semantic_payload != content_or_id.semantic_payload:
                raise WrittenV17Error("unregistered semantic payload")
            return render_written_projection(registered)
        return render_written_projection(self.content(content_or_id))

    def parse(self, text: str) -> WrittenProjection:
        return parse_written_projection(text, self)


def _parse_body(kind: str, body: str) -> DefinitionContent:
    try:
        if kind == "PREDICATE":
            return predicate_content(parse_predicate(body))
        if kind == "INTERNAL_BRANCH":
            return branch_content(normalize_branch_surface(body))
    except (SurfaceV09Error, DefinitionV11Error, AlgebraV10Error) as exc:
        raise WrittenV17Error(str(exc)) from exc
    raise WrittenV17Error(f"unsupported projection kind: {kind}")


def parse_written_projection(text: str, registry: ProjectionRegistry) -> WrittenProjection:
    if not isinstance(text, str) or not text:
        raise WrittenV17Error("non-empty written projection required")
    if not isinstance(registry, ProjectionRegistry):
        raise WrittenV17Error("ProjectionRegistry authority required")

    lines = text.splitlines(keepends=False)
    if len(lines) != 4 or not text.endswith("\n"):
        raise WrittenV17Error("v0.17 projection must contain exactly four canonical lines")
    if lines[0] != _HEADER:
        raise WrittenV17Error("unsupported written PNCS header")

    kind_match = _KIND_RE.fullmatch(lines[1])
    if kind_match is None:
        raise WrittenV17Error("invalid projection KIND line")
    kind = kind_match.group(1)

    cid_match = _CID_RE.fullmatch(lines[2])
    if cid_match is None:
        raise WrittenV17Error("invalid projection CID line")
    claimed_cid = cid_match.group(1)

    if not lines[3].startswith("BODY ") or len(lines[3]) <= 5:
        raise WrittenV17Error("invalid projection BODY line")
    body = lines[3][5:]

    authoritative = registry.content(claimed_cid)
    if authoritative.kind != kind:
        raise WrittenV17Error("projection KIND does not match registered content")

    reconstructed = _parse_body(kind, body)
    if reconstructed.content_id != claimed_cid:
        raise WrittenV17Error("projection BODY content ID mismatch")
    if reconstructed.semantic_payload != authoritative.semantic_payload:
        raise WrittenV17Error("projection BODY differs from registered semantic content")

    canonical_text = render_written_projection(authoritative)
    if text != canonical_text:
        raise WrittenV17Error("projection is not in canonical written form")

    return WrittenProjection(content=authoritative, text=canonical_text)
