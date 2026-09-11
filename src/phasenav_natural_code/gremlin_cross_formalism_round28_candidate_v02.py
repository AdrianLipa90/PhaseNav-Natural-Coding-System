from __future__ import annotations

from typing import Mapping

from .gremlin_cross_formalism_round28_v01 import (
    ROUND28_COMPILATION_SCHEMA,
    Round28Compilation,
    round28_bank,
    round28_manifest,
    validate_round28_candidates,
)
from .gremlin_relational_compiler_v01 import compile_relational_isomorphism

SCHEMA = "PNCS_GREMLIN_CROSS_FORMALISM_ROUND28_CANDIDATE_V0_2"
STATUS = "CANDIDATE"

# Explicit lowering into the already admitted deterministic PNV subset.
# No new opcode is introduced. These relations are map/isomorphism/lift
# relations, so COMPOSITION is the conservative relational primitive.
ROUND28_RELATION_OPCODE_OVERRIDES: Mapping[str, str] = {
    "DOUBLE_COVER_LIFT_OF": "COMPOSITION",
    "EXACT_KERNEL_ISOMORPHISM": "COMPOSITION",
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
            relation_opcode_overrides=ROUND28_RELATION_OPCODE_OVERRIDES,
            authoring_root=None,
        )

    manifest = {
        **round28_manifest(),
        "compilation_schema": ROUND28_COMPILATION_SCHEMA,
        "compiled_entries": {
            iso_id: {
                "receipt_sha256": compilation.receipt["receipt_sha256"],
                "radical_candidate_id": compilation.radical_candidate["candidate_id"],
                "pnv_graph_sha256": compilation.receipt["pnv_graph_sha256"],
            }
            for iso_id, compilation in sorted(compiled.items())
        },
    }
    return Round28Compilation(compilations=compiled, manifest=manifest)


def validate_round28_candidates_v02(compiled: Round28Compilation):
    """Reuse the v0.1 integrity/effect-boundary validator on the repaired route."""
    return validate_round28_candidates(compiled)


def candidate_metadata() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "active_working": True,
        "default_enabled": False,
        "new_opcode_count": 0,
        "relation_opcode_overrides": dict(ROUND28_RELATION_OPCODE_OVERRIDES),
        "preserves_v01_failure": "UNKNOWN_RELATION_TYPES_FAIL_CLOSED",
        "physical_binding": False,
    }
