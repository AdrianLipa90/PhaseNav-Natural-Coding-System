from __future__ import annotations

"""Fail-closed Round28 execution lowering v0.4.

Round28 keeps its rich semantic relation types in the source specification.
This module supplies a local execution lowering into the already admitted
native PNV COMPOSITION primitive. It does not widen the generic compiler,
create a new opcode, or grant runtime/canon authority.
"""

from typing import Mapping

from .gremlin_cross_formalism_round28_v01 import (
    Round28Compilation,
    _compilation_manifest,
    round28_bank,
    validate_round28_candidates,
)
from .gremlin_relational_compiler_v01 import (
    DEFAULT_RELATION_OPCODE,
    compile_relational_isomorphism,
)

ROUND28_V04_SCHEMA = "PNCS_GREMLIN_CROSS_FORMALISM_ROUND28_EXECUTABLE_V0_4"
ROUND28_RELATION_OPCODE_BINDINGS: Mapping[str, str] = {
    "DOUBLE_COVER_LIFT_OF": "COMPOSITION",
    "EXACT_KERNEL_ISOMORPHISM": "COMPOSITION",
    "COORDINATE_ISOMORPHIC_TO": "COMPOSITION",
}


class Round28V04Error(RuntimeError):
    pass


def required_round28_relation_types() -> frozenset[str]:
    return frozenset(
        edge.relation_type
        for entry in round28_bank()
        for edge in entry.spec.edges
    )


def validate_round28_relation_opcode_bindings(bindings: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(bindings, Mapping):
        raise Round28V04Error("Round28 relation bindings must be a mapping")
    normalized = {str(k).upper(): str(v).upper() for k, v in bindings.items()}
    required = required_round28_relation_types()
    if set(normalized) != set(required):
        raise Round28V04Error("Round28 relation binding keyset mismatch")
    if any(opcode != "COMPOSITION" for opcode in normalized.values()):
        raise Round28V04Error("Round28 semantic relations lower only to COMPOSITION in v0.4")
    if any(relation in DEFAULT_RELATION_OPCODE for relation in required):
        raise Round28V04Error("Round28 local relation leaked into generic default opcode table")
    return normalized


def compile_round28_candidates_v04(*, generation_binding: str, identity: str, authority: str) -> Round28Compilation:
    bindings = validate_round28_relation_opcode_bindings(ROUND28_RELATION_OPCODE_BINDINGS)
    compiled = {}
    for entry in round28_bank():
        compiled[entry.spec.isomorphism_id] = compile_relational_isomorphism(
            entry.spec,
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            relation_opcode_overrides=bindings,
            authoring_root=None,
        )
    result = Round28Compilation(compilations=compiled, manifest=_compilation_manifest(compiled))
    validated = validate_round28_candidates(result)
    if set(validated) != set(compiled):
        raise Round28V04Error("Round28 validation keyset mismatch")
    for iso_id, compilation in compiled.items():
        plan = compilation.receipt.get("relation_plan")
        if not isinstance(plan, list) or len(plan) != 1:
            raise Round28V04Error(f"Round28 relation plan malformed: {iso_id}")
        row = plan[0]
        if row.get("opcode") != "COMPOSITION":
            raise Round28V04Error(f"Round28 relation lowering drift: {iso_id}")
        semantic = compilation.spec.edges[0].relation_type
        if row.get("relation_type") != semantic:
            raise Round28V04Error(f"Round28 semantic relation type lost: {iso_id}")
    return result


def round28_v04_status() -> Mapping[str, object]:
    bindings = validate_round28_relation_opcode_bindings(ROUND28_RELATION_OPCODE_BINDINGS)
    return {
        "schema": ROUND28_V04_SCHEMA,
        "promotion_state": "CANDIDATE_ONLY",
        "release_class": "CLOSURE_REQUIRED_CANDIDATE",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "epistemic": "CHYBA",
        "generic_default_opcode_table_mutated": False,
        "new_opcode_count": 0,
        "bindings": bindings,
        "semantic_rule": "relation_type is preserved; COMPOSITION is execution lowering, not semantic identity",
    }
