from __future__ import annotations
import re
from dataclasses import dataclass

class SurfaceV06Error(ValueError):
    pass

@dataclass(frozen=True)
class ConditionalRoute:
    subject: str
    threshold: float
    target: str
    relation: str = "lt"
    action: str = "route"

    @property
    def leaf_path(self):
        return ("DIFFERENCE","CONDITION","ORDER","ACTION_REQUEST","COMPOSITION")

_PATTERNS = [
    re.compile(r"^\s*IF\s+(?P<s>[^\s]+)\s+BELOW\s+(?P<t>-?(?:\d+(?:\.\d*)?|\.\d+))\s+THEN\s+GO\s+(?P<d>[^\s]+)\s*$", re.I),
    re.compile(r"^\s*IF\s+(?P<s>[^\s]+)\s*<\s*(?P<t>-?(?:\d+(?:\.\d*)?|\.\d+))\s+THEN\s+GO\s+(?P<d>[^\s]+)\s*$", re.I),
    re.compile(r"^\s*(?P<s>[^\s]+)\s*<\s*(?P<t>-?(?:\d+(?:\.\d*)?|\.\d+))\s*->\s*(?P<d>[^\s]+)\s*$", re.I),
]

def normalize_control_surface(text: str) -> ConditionalRoute:
    if not isinstance(text,str) or not text.strip():
        raise SurfaceV06Error("non-empty control surface required")
    for pattern in _PATTERNS:
        m=pattern.match(text)
        if m:
            threshold=float(m.group("t"))
            if threshold != threshold or threshold in (float("inf"),float("-inf")):
                raise SurfaceV06Error("finite threshold required")
            return ConditionalRoute(m.group("s"), threshold, m.group("d"))
    raise SurfaceV06Error("surface does not match frozen v0.6 conditional-route grammar")

def reference_predicate(program: ConditionalRoute, value: float) -> bool:
    # Test harness only; native PNV graph is authoritative.
    return float(value) - program.threshold < 0.0
