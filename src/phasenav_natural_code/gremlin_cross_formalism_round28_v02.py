from __future__ import annotations

"""Executable candidate repair for Round28 relation bindings.

v0.1 is intentionally retained as the historical fail-closed surface.  This
module supplies explicit, local bindings for the three Round28 semantic
relations without widening DEFAULT_RELATION_OPCODE in the generic compiler.
The result remains READ_ONLY / CHYBA / CANDIDATE_ONLY.
"""

from typing import Mapping

from .gremlin_cross_formalism_round28_v01 import (
    Round28Compilation,
    _compilation_manifest,
    round28_bank,
    validate_round28_candidates,
)
from .gremlin_relational_compiler_v01 import compile_relational_isomorphism

ROUND28_V02_SCHEMA = "PNCS_GREMLIN_CROSS_FORMALISM_ROUND28_EXECUTABLE_V0_2"

# These bindings describe execution algebra only; the richer semantic relation
# remains preserved in RelationalEdge.relation_type and in the evidence bundle.
# No entry is promoted into the generic compiler's default relation vocabulary.
ROUND28_RELATION_OPCODE_BINDINGS: Mapping[str, str] = {
    "DOUBLE_COVER_LIFT_OF": "COMPOSITION",
    "EXACT_KERNEL_ISOMORPHISM": "IDENTITY",
    "COORDINATE_ISOMORPHIC_TO": "COMPOSITION",
}


def compile_round28_candidates_v02(
    *,
    generation_binding: str,
    identity: str,
    authority: str,
) -> Round28Compilation:
    compiled = {}
    for entry in round28_bank():
        compiled[entry.spec.isomorphism_id] = compile_relational_isomorphism(
            entry.spec,
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            relation_opcode_overrides=ROUND28_RELATION_OPCODE_BINDINGS,
            authoring_root=None,
        )
    result = Round28Compilation(
        compilations=compiled,
        manifest=_compilation_manifest(compiled),
    )
    # Reuse the full v0.1 integrity validator: this checks content-addressed
    # candidates, aggregate receipts, READ_ONLY mode and CHYBA epistemics.
    validate_round28_candidates(result)
    return result


def round28_v02_status() -> Mapping[str, object]:
    return {
        "schema": ROUND28_V02_SCHEMA,
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "epistemic": "CHYBA",
        "generic_default_opcode_table_mutated": False,
        "bindings": dict(ROUND28_RELATION_OPCODE_BINDINGS),
    }
