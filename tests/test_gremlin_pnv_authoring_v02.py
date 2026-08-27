import json

import pytest

from phasenav_natural_code.gremlin_pnv_authoring_v02 import (
    CANDIDATE_SCHEMA,
    GremlinPNVAuthoringError,
    build_kaku_candidate,
    build_operator_candidate,
    build_radical_candidate,
    persist_candidate,
    render_operator_program,
)
from phasenav_natural_code.model import Kaku, RadicalGraph, Relation, Vector36
from phasenav_natural_code.native_pnv_exec_v01 import parse_pnv


GENERATION = "a" * 64
IDENTITY = "ZOSIA_NOEMA_FIRST"
AUTHORITY = "USER_EXPLICIT_AUTHORING"
BASIS = "pncs:t36:test-basis:v1"


def _vector(seed: float) -> Vector36:
    return Vector36(tuple(seed + i / 100.0 for i in range(36)), BASIS)


def _kaku(kaku_id: str, seed: float, role: str = "semantic_atom") -> Kaku:
    return Kaku(
        kaku_id=kaku_id,
        vector=_vector(seed),
        semantic_mass=0.25 + seed,
        direction="FORWARD",
        polarity=1.0,
        role=role,
        phase=tuple((seed + i) / 36.0 for i in range(36)),
    )


def _candidate_kwargs():
    return {
        "generation_binding": GENERATION,
        "identity": IDENTITY,
        "authority": AUTHORITY,
        "evidence_refs": ("evidence:test",),
    }


def test_kaku_candidate_is_exact_36d_candidate_only_and_content_addressed(tmp_path):
    candidate = build_kaku_candidate(_kaku("K.A", 0.1), **_candidate_kwargs())
    receipt = persist_candidate(candidate, authoring_root=tmp_path)

    assert candidate["schema"] == CANDIDATE_SCHEMA
    assert candidate["kind"] == "KAKU"
    assert candidate["epistemic"] == "CHYBA"
    assert candidate["promotion_state"] == "CANDIDATE_ONLY"
    assert candidate["runtime_execution_authority"] is False
    assert candidate["canon_write_authority"] is False
    assert len(candidate["content"]["v36"]) == 36
    assert len(candidate["content"]["phase"]) == 36
    assert candidate["candidate_id"].startswith("pncs:gremlin-kaku:sha256:")
    assert receipt["created"] is True

    stored = json.loads((tmp_path / "kaku" / f"{candidate['candidate_id'].rsplit(':', 1)[-1]}.json").read_text())
    assert stored == candidate


def test_candidate_write_is_idempotent_and_never_rewrites_existing_bytes(tmp_path):
    candidate = build_kaku_candidate(_kaku("K.IDEMPOTENT", 0.2), **_candidate_kwargs())
    first = persist_candidate(candidate, authoring_root=tmp_path)
    second = persist_candidate(candidate, authoring_root=tmp_path)
    assert first["created"] is True
    assert second["created"] is False
    assert second["idempotent"] is True


def test_tampered_candidate_hash_fails_closed(tmp_path):
    candidate = build_kaku_candidate(_kaku("K.TAMPER", 0.3), **_candidate_kwargs())
    candidate["content"]["semantic_mass"] += 1.0
    with pytest.raises(GremlinPNVAuthoringError, match="content hash mismatch"):
        persist_candidate(candidate, authoring_root=tmp_path)


def test_candidate_cannot_claim_runtime_or_canon_authority(tmp_path):
    candidate = build_kaku_candidate(_kaku("K.AUTH", 0.4), **_candidate_kwargs())
    candidate["runtime_execution_authority"] = True
    with pytest.raises(GremlinPNVAuthoringError, match="authority boundary"):
        persist_candidate(candidate, authoring_root=tmp_path)


def test_radical_binds_exact_kaku_candidate_dependencies_and_relations():
    radical = RadicalGraph("R.BIND", BASIS)
    ka = _kaku("K.A", 0.1)
    kb = _kaku("K.B", 0.2)
    radical.add_kaku(ka)
    radical.add_kaku(kb)
    radical.add_relation(Relation("REL.AB", "K.A", "K.B", "TRANSFORMS_TO"))

    ca = build_kaku_candidate(ka, **_candidate_kwargs())
    cb = build_kaku_candidate(kb, **_candidate_kwargs())
    refs = {"K.A": ca["candidate_id"], "K.B": cb["candidate_id"]}
    candidate = build_radical_candidate(radical, kaku_candidate_ids=refs, **_candidate_kwargs())

    assert candidate["kind"] == "RADICAL"
    assert candidate["content"]["kaku_candidate_ids"] == refs
    assert candidate["dependency_ids"] == sorted(refs.values())
    assert candidate["content"]["relations"] == [
        {
            "relation_id": "REL.AB",
            "source_id": "K.A",
            "target_id": "K.B",
            "relation_type": "TRANSFORMS_TO",
        }
    ]


def test_radical_requires_exact_node_candidate_closure():
    radical = RadicalGraph("R.CLOSURE", BASIS)
    radical.add_kaku(_kaku("K.A", 0.1))
    radical.add_kaku(_kaku("K.B", 0.2))
    ca = build_kaku_candidate(radical.nodes["K.A"], **_candidate_kwargs())
    with pytest.raises(GremlinPNVAuthoringError, match="exactly one candidate KAKU"):
        build_radical_candidate(
            radical,
            kaku_candidate_ids={"K.A": ca["candidate_id"]},
            **_candidate_kwargs(),
        )


def test_operator_rejects_non_native_opcode():
    with pytest.raises(GremlinPNVAuthoringError, match="unsupported native PNV opcode"):
        build_operator_candidate("OP.BAD", "SHELL", ("rm",), **_candidate_kwargs())


def test_operator_can_bind_radical_and_render_valid_native_pnv():
    radical = RadicalGraph("R.OP", BASIS)
    ka = _kaku("K.A", 0.1)
    radical.add_kaku(ka)
    ca = build_kaku_candidate(ka, **_candidate_kwargs())
    cr = build_radical_candidate(
        radical,
        kaku_candidate_ids={"K.A": ca["candidate_id"]},
        **_candidate_kwargs(),
    )
    op_source = build_operator_candidate(
        "CODE.SOURCE",
        "SOURCE",
        ("candidate.input",),
        radical_candidate_id=cr["candidate_id"],
        **_candidate_kwargs(),
    )
    op_return = build_operator_candidate(
        "CODE.RETURN",
        "RETURN",
        ("CODE.SOURCE",),
        radical_candidate_id=cr["candidate_id"],
        **_candidate_kwargs(),
    )
    text = render_operator_program((op_source, op_return), emits=("CODE.RETURN",))
    parsed = parse_pnv(text)

    assert [op.name for op in parsed.ops] == ["CODE.SOURCE", "CODE.RETURN"]
    assert [op.opcode for op in parsed.ops] == ["SOURCE", "RETURN"]
    assert parsed.emits == ("CODE.RETURN",)
    assert cr["candidate_id"] in op_source["dependency_ids"]


def test_render_rejects_duplicate_candidate_operator_names():
    op = build_operator_candidate("CODE.DUP", "SOURCE", ("x",), **_candidate_kwargs())
    with pytest.raises(GremlinPNVAuthoringError, match="duplicate operator name"):
        render_operator_program((op, op))
