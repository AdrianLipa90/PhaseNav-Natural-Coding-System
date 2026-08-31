from dataclasses import replace

import pytest

from phasenav_natural_code.gremlin_relational_compiler_v01 import (
    GremlinRelationalCompilerError,
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
    compile_relational_isomorphism,
    validate_compiled_relational_candidate,
)
from phasenav_natural_code.model import Kaku, Vector36


BASIS = "pncs:t36:relational-integrity-test:v1"
KWARGS = {
    "generation_binding": "a" * 64,
    "identity": "ZOSIA_NOEMA_FIRST",
    "authority": "USER_EXPLICIT_AUTHORING",
}


def _kaku(name: str, seed: float) -> Kaku:
    return Kaku(
        name,
        Vector36(tuple(seed + i / 100.0 for i in range(36)), BASIS),
        0.5 + seed,
        "FORWARD",
        1.0,
        "integrity-node",
        tuple((seed + i) / 36.0 for i in range(36)),
    )


def _compiled():
    spec = RelationalIsomorphism(
        "ISO.INTEGRITY",
        "INV.INTEGRITY",
        "source binding and compilation receipt stay exact",
        (
            RelationalNode(_kaku("K.A", 0.1), "A", "obs:a"),
            RelationalNode(_kaku("K.B", 0.2), "B", "obs:b"),
        ),
        (RelationalEdge("REL.AB", "K.A", "K.B", "ISOMORPHIC_TO"),),
    )
    return compile_relational_isomorphism(spec, **KWARGS)


def test_source_binding_tamper_is_rejected_before_execution():
    compiled = _compiled()
    bindings = dict(compiled.source_bindings)
    bindings["gremlin.iso.source.000"] = {"tampered": True}
    broken = replace(compiled, source_bindings=bindings)
    with pytest.raises(GremlinRelationalCompilerError, match="SOURCE binding mismatch"):
        validate_compiled_relational_candidate(broken)


def test_shared_candidate_mutation_is_detected_by_candidate_content_hash():
    compiled = _compiled()
    compiled.kaku_candidates["K.A"]["content"]["role"] = "tampered"
    with pytest.raises(GremlinRelationalCompilerError, match="KAKU candidate content hash mismatch"):
        validate_compiled_relational_candidate(compiled)


def test_pnv_text_tamper_is_rejected_against_compilation_receipt():
    compiled = _compiled()
    tampered = compiled.pnv_text.replace("EMIT ISO.RETURN", "EMIT ISO.REL.000")
    broken = replace(compiled, pnv_text=tampered)
    with pytest.raises(GremlinRelationalCompilerError, match="source/graph no longer matches"):
        validate_compiled_relational_candidate(broken)


def test_receipt_tamper_is_rejected_before_execution():
    compiled = _compiled()
    receipt = dict(compiled.receipt)
    receipt["pnv_graph_sha256"] = "0" * 64
    broken = replace(compiled, receipt=receipt)
    with pytest.raises(GremlinRelationalCompilerError, match="receipt digest mismatch"):
        validate_compiled_relational_candidate(broken)


def test_untampered_compilation_still_executes_in_pure_mode():
    compiled = _compiled()
    result = validate_compiled_relational_candidate(compiled)
    assert result.receipt["effect_boundary"]["external_effects"] is False
    assert result.receipt["effect_boundary"]["interpreter_external_effects"] is False
