from __future__ import annotations
import re
from dataclasses import dataclass

class SurfaceV07Error(ValueError):
    pass

_WORD_REL = {"BELOW":"lt", "ABOVE":"gt", "EQUAL":"eq"}
_SYM_REL = {"<":"lt", ">":"gt", "==":"eq"}

@dataclass(frozen=True)
class ConditionalRoute:
    subject: str
    comparator: str
    threshold: float
    target: str

    @property
    def leaf_path(self):
        return ("DIFFERENCE","CONDITION","ORDER","TRANSFORM","COMPOSITION")

    @property
    def canonical_tuple(self):
        return (self.subject, self.comparator, self.threshold, self.target)

_NUM = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
_NAME = r"[^\s]+"
_PATTERNS = [
    re.compile(rf"^\s*IF\s+(?P<s>{_NAME})\s+(?P<rel>BELOW|ABOVE|EQUAL)\s+(?P<t>{_NUM})\s+THEN\s+GO\s+(?P<d>{_NAME})\s*$", re.I),
    re.compile(rf"^\s*IF\s+(?P<s>{_NAME})\s*(?P<rel>==|<|>)\s*(?P<t>{_NUM})\s+THEN\s+GO\s+(?P<d>{_NAME})\s*$", re.I),
    re.compile(rf"^\s*(?P<s>{_NAME})\s*(?P<rel>==|<|>)\s*(?P<t>{_NUM})\s*->\s*(?P<d>{_NAME})\s*$", re.I),
]

def normalize_control_surface(text: str) -> ConditionalRoute:
    if not isinstance(text, str) or not text.strip():
        raise SurfaceV07Error("non-empty control surface required")
    for pattern in _PATTERNS:
        m = pattern.match(text)
        if not m:
            continue
        raw_rel = m.group("rel")
        comparator = _WORD_REL.get(raw_rel.upper(), _SYM_REL.get(raw_rel))
        if comparator is None:
            raise SurfaceV07Error("unsupported comparator")
        threshold = float(m.group("t"))
        if threshold != threshold or threshold in (float("inf"), float("-inf")):
            raise SurfaceV07Error("finite threshold required")
        return ConditionalRoute(m.group("s"), comparator, threshold, m.group("d"))
    raise SurfaceV07Error("surface does not match frozen v0.7 conditional-route grammar")

def reference_predicate(program: ConditionalRoute, value: float) -> bool:
    delta = float(value) - program.threshold
    if program.comparator == "lt":
        return delta < 0.0
    if program.comparator == "gt":
        return delta > 0.0
    if program.comparator == "eq":
        return delta == 0.0
    raise SurfaceV07Error("unsupported canonical comparator")
