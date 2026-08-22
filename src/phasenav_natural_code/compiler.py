from __future__ import annotations

class BasisNotCanonizedError(RuntimeError):
    pass


def compile_natural_language(text: str):
    """Resolve natural language into a canonical PNCS graph.

    Intentionally unavailable in FOUNDATION_V0_1. Semantic compilation must not
    guess a 36D basis, radicals, definitions, or relation paths.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("non-empty natural-language input is required")
    raise BasisNotCanonizedError(
        "PNCS 36D semantic basis and initial radical/definition canon are not yet fixed"
    )
