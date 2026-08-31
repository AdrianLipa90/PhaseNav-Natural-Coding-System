import pytest

from phasenav_natural_code.gremlin_pnv_authoring_v02 import (
    GremlinPNVAuthoringError,
    build_kaku_candidate,
    build_operator_candidate,
    persist_candidate,
)
from phasenav_natural_code.model import Kaku, Vector36


GENERATION = "a" * 64
IDENTITY = "ZOSIA_NOEMA_FIRST"
AUTHORITY = "USER_EXPLICIT_AUTHORING"
BASIS = "pncs:t36:canonical-boundary-test:v1"


def _kaku() -> Kaku:
    return Kaku(
        kaku_id="K.CANONICAL",
        vector=Vector36(tuple(i / 100.0 for i in range(36)), BASIS),
        semantic_mass=0.25,
        direction="FORWARD",
        polarity=1.0,
        role="semantic_atom",
        phase=tuple(i / 36.0 for i in range(36)),
    )


def _kwargs():
    return {
        "generation_binding": GENERATION,
        "identity": IDENTITY,
        "authority": AUTHORITY,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("generation_binding", 1),
        ("identity", object()),
        ("authority", False),
    ],
)
def test_candidate_identity_fields_reject_non_strings(field, value):
    kwargs = _kwargs()
    kwargs[field] = value
    with pytest.raises(GremlinPNVAuthoringError, match=field):
        build_kaku_candidate(_kaku(), **kwargs)


def test_evidence_refs_reject_non_strings_instead_of_stringifying_them():
    with pytest.raises(GremlinPNVAuthoringError, match="evidence_ref"):
        build_kaku_candidate(_kaku(), evidence_refs=("evidence:ok", 7), **_kwargs())


def test_operator_args_reject_non_strings_instead_of_stringifying_them():
    with pytest.raises(GremlinPNVAuthoringError, match="string argument"):
        build_operator_candidate("OP.TEST", "SOURCE", (7,), **_kwargs())


def test_non_string_nested_mapping_key_fails_closed_without_raw_typeerror(tmp_path):
    candidate = build_kaku_candidate(_kaku(), **_kwargs())
    candidate["content"]["ambiguous"] = {1: "integer-key", "1": "string-key"}
    with pytest.raises(GremlinPNVAuthoringError, match="mapping keys must be strings"):
        persist_candidate(candidate, authoring_root=tmp_path)


def test_identity_and_refs_are_trimmed_before_hashing():
    candidate = build_kaku_candidate(
        _kaku(),
        generation_binding=f"  {GENERATION}  ",
        identity=f"  {IDENTITY}  ",
        authority=f"  {AUTHORITY}  ",
        evidence_refs=(" evidence:b ", "evidence:a", "evidence:a"),
    )
    assert candidate["generation_binding"] == GENERATION
    assert candidate["identity"] == IDENTITY
    assert candidate["authority"] == AUTHORITY
    assert candidate["evidence_refs"] == ["evidence:a", "evidence:b"]
