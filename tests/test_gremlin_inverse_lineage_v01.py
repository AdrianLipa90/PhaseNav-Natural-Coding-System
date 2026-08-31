from dataclasses import replace

import pytest

from phasenav_natural_code.gremlin_inverse_lineage_v01 import (
    LINEAGE_SCHEMA,
    GremlinInverseLineageError,
    _sha256,
    persist_gremlin_candidate_inverse_lineage,
    resolve_gremlin_candidate_inverse_lineage,
)
from phasenav_natural_code.gremlin_relational_compiler_v01 import (
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
    compile_relational_isomorphism,
    validate_compiled_relational_candidate,
)
from phasenav_natural_code.model import Kaku, Vector36
from phasenav_natural_code.native_pnv_exec_v01 import NativePNVExecutionResult


GENERATION = "a" * 64
CONTENT_ID = "pncs:def:sha256:" + "1" * 64
BASIS = "pncs:t36:gremlin-inverse-test:v1"


def _kaku(kaku_id: str, seed: float, role: str) -> Kaku:
    return Kaku(
        kaku_id=kaku_id,
        vector=Vector36(tuple(seed + i / 100.0 for i in range(36)), BASIS),
        semantic_mass=0.25 + seed,
        direction="FORWARD",
        polarity=1.0,
        role=role,
        phase=tuple((seed + i) / 36.0 for i in range(36)),
    )


def _compiled():
    left = _kaku("K.LEFT", 0.1, f"gremlin_relation_atom:IDENTITY:{CONTENT_ID}")
    right = _kaku("K.RIGHT", 0.2, "gremlin_relation_atom:ORDER")
    spec = RelationalIsomorphism(
        isomorphism_id="ISO.INVERSE",
        invariant_id="INV.INVERSE",
        invariant_description="candidate inverse-lineage invariant",
        nodes=(
            RelationalNode(left, "DOMAIN_A", "obs:a"),
            RelationalNode(right, "DOMAIN_B", "obs:b"),
        ),
        edges=(RelationalEdge("REL.0", "K.LEFT", "K.RIGHT", "ISOMORPHIC_TO"),),
        evidence_refs=("evidence:inverse",),
    )
    compilation = compile_relational_isomorphism(
        spec,
        generation_binding=GENERATION,
        identity="ZOSIA_NOEMA_FIRST",
        authority="USER_EXPLICIT_AUTHORING",
    )
    result = validate_compiled_relational_candidate(compilation)
    return compilation, result


def _with_receipt(result: NativePNVExecutionResult, receipt):
    return NativePNVExecutionResult(
        program=result.program,
        values=result.values,
        emitted=result.emitted,
        receipt=receipt,
    )


def test_inverse_lineage_round_trips_result_to_explicit_content_provenance():
    compilation, result = _compiled()
    lineage = resolve_gremlin_candidate_inverse_lineage(compilation, result)

    assert lineage.payload["schema"] == LINEAGE_SCHEMA
    assert lineage.inverse_chain[0]["level"] == "RESULT"
    assert lineage.operator_rows[0]["name"] == "ISO.RETURN"
    assert lineage.radical_row["level"] == "RADICAL"
    assert {row["node_id"] for row in lineage.kaku_rows} == {"K.LEFT", "K.RIGHT"}
    assert lineage.payload["explicit_content_ids"] == [CONTENT_ID]
    assert lineage.payload["v22_join_state"] == "CONTENT_ID_AVAILABLE"
    assert lineage.payload["promotion_state"] == "CANDIDATE_ONLY"
    assert lineage.payload["runtime_execution_authority"] is False


def test_inverse_lineage_id_is_deterministic():
    compilation, result = _compiled()
    a = resolve_gremlin_candidate_inverse_lineage(compilation, result)
    b = resolve_gremlin_candidate_inverse_lineage(compilation, result)
    assert a.lineage_id == b.lineage_id
    assert a.receipt == b.receipt


def test_inverse_lineage_persistence_is_content_addressed_and_idempotent(tmp_path):
    compilation, result = _compiled()
    lineage = resolve_gremlin_candidate_inverse_lineage(compilation, result)
    first = persist_gremlin_candidate_inverse_lineage(lineage, authoring_root=tmp_path)
    second = persist_gremlin_candidate_inverse_lineage(lineage, authoring_root=tmp_path)
    assert first == second
    assert first.endswith(lineage.lineage_id.rsplit(":", 1)[-1] + ".json")


def test_tampered_execution_receipt_fails_closed():
    compilation, result = _compiled()
    receipt = dict(result.receipt)
    receipt["mode"] = "WRITE"
    with pytest.raises(GremlinInverseLineageError, match="execution receipt digest mismatch"):
        resolve_gremlin_candidate_inverse_lineage(compilation, _with_receipt(result, receipt))


def test_execution_compilation_program_hash_mismatch_fails_closed():
    compilation, result = _compiled()
    receipt = dict(result.receipt)
    body = dict(receipt)
    body.pop("receipt_sha256")
    body["program_source_sha256"] = "0" * 64

    bad = {**body, "receipt_sha256": _sha256(body)}
    with pytest.raises(GremlinInverseLineageError, match="source hash mismatch"):
        resolve_gremlin_candidate_inverse_lineage(compilation, _with_receipt(result, bad))


def test_tampered_operator_candidate_fails_closed():
    compilation, result = _compiled()
    operators = list(compilation.operator_candidates)
    bad = dict(operators[0])
    bad_content = dict(bad["content"])
    bad_content["opcode"] = "RETURN"
    bad["content"] = bad_content
    operators[0] = bad
    broken = replace(compilation, operator_candidates=tuple(operators))
    with pytest.raises(GremlinInverseLineageError, match="content hash mismatch"):
        resolve_gremlin_candidate_inverse_lineage(broken, result)


def test_radical_to_kaku_closure_tamper_fails_closed():
    compilation, result = _compiled()
    bad = dict(compilation.radical_candidate)
    bad_content = dict(bad["content"])
    refs = dict(bad_content["kaku_candidate_ids"])
    refs["K.LEFT"] = "pncs:gremlin-kaku:sha256:" + "0" * 64
    bad_content["kaku_candidate_ids"] = refs
    bad["content"] = bad_content
    broken = replace(compilation, radical_candidate=bad)
    with pytest.raises(GremlinInverseLineageError, match="content hash mismatch"):
        resolve_gremlin_candidate_inverse_lineage(broken, result)


def test_false_emitted_receipt_hash_fails_closed():
    compilation, result = _compiled()
    receipt = dict(result.receipt)
    body = dict(receipt)
    body.pop("receipt_sha256")
    body["emitted"] = [["ISO.RETURN", "0" * 64]]

    bad_receipt = {**body, "receipt_sha256": _sha256(body)}
    bad_result = _with_receipt(result, bad_receipt)
    with pytest.raises(GremlinInverseLineageError, match="emitted value/receipt mismatch"):
        resolve_gremlin_candidate_inverse_lineage(compilation, bad_result)


def test_inverse_lineage_rejects_nonstring_candidate_evidence_even_with_valid_content_hash():
    compilation, result = _compiled()
    kaku_candidates = dict(compilation.kaku_candidates)
    bad = dict(kaku_candidates["K.LEFT"])
    bad["evidence_refs"] = [[CONTENT_ID]]
    body = {key: value for key, value in bad.items() if key != "candidate_id"}
    bad["candidate_id"] = "pncs:gremlin-kaku:sha256:" + _sha256(body)
    kaku_candidates["K.LEFT"] = bad
    broken = replace(compilation, kaku_candidates=kaku_candidates)

    with pytest.raises(GremlinInverseLineageError, match=r"KAKU evidence_refs\[0\]"):
        resolve_gremlin_candidate_inverse_lineage(broken, result)


def test_inverse_lineage_rejects_nonstring_kaku_mapping_identity_before_coercion():
    compilation, result = _compiled()
    kaku_candidates = dict(compilation.kaku_candidates)
    left = kaku_candidates.pop("K.LEFT")
    kaku_candidates[7] = left
    broken = replace(compilation, kaku_candidates=kaku_candidates)

    with pytest.raises(GremlinInverseLineageError, match="compilation KAKU node id"):
        resolve_gremlin_candidate_inverse_lineage(broken, result)


def test_no_explicit_content_binding_keeps_v22_join_open():
    left = _kaku("K.LEFT", 0.1, "gremlin_relation_atom:IDENTITY")
    right = _kaku("K.RIGHT", 0.2, "gremlin_relation_atom:ORDER")
    spec = RelationalIsomorphism(
        isomorphism_id="ISO.NO.CONTENT",
        invariant_id="INV.NO.CONTENT",
        invariant_description="candidate with no explicit canonical content binding",
        nodes=(RelationalNode(left, "A", "a"), RelationalNode(right, "B", "b")),
        edges=(RelationalEdge("REL.0", "K.LEFT", "K.RIGHT", "ORDER"),),
    )
    compilation = compile_relational_isomorphism(
        spec,
        generation_binding=GENERATION,
        identity="ZOSIA_NOEMA_FIRST",
        authority="USER_EXPLICIT_AUTHORING",
    )
    result = validate_compiled_relational_candidate(compilation)
    lineage = resolve_gremlin_candidate_inverse_lineage(compilation, result)
    assert lineage.payload["explicit_content_ids"] == []
    assert lineage.payload["v22_join_state"] == "CONTENT_ID_OPEN"
