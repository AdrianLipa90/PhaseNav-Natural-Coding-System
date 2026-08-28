import hashlib
import json
import math
import pytest

from phasenav_natural_code.ordered_semantic_path_v30 import (
    OrderedSemanticPathV30Error,
    SemanticAnchorBinding,
    compile_ordered_semantic_path,
)

TAU = 2.0 * math.pi


def _sha_phase(values):
    return hashlib.sha256(json.dumps(list(values), separators=(",", ":")).encode()).hexdigest()


def _sha_tangent(values):
    return hashlib.sha256(json.dumps(list(values), separators=(",", ":")).encode()).hexdigest()


def _cid(kind, label):
    return f"pncs:{kind}:sha256:{hashlib.sha256(label.encode()).hexdigest()}"


def _fixture_db():
    # Four exact T^36 anchors in a directed canonical cycle.
    turns = {
        "M0": [0.00 + i * 0.001 for i in range(36)],
        "M1": [0.10 + i * 0.001 for i in range(36)],
        "M2": [0.20 + i * 0.001 for i in range(36)],
        "M3": [0.30 + i * 0.001 for i in range(36)],
    }
    phase = {k: [((x % 1.0) * TAU) for x in v] for k, v in turns.items()}
    vectors = {k: {"phase36": v, "sha256": _sha_phase(v)} for k, v in phase.items()}
    paths = []
    pairs = [("M0","M1"),("M1","M2"),("M2","M3"),("M3","M0")]
    for a,b in pairs:
        qa=[x/TAU for x in phase[a]]; qb=[x/TAU for x in phase[b]]
        tangent=[((y-x+0.5)%1.0)-0.5 for x,y in zip(qa,qb)]
        paths.append({
            "path_id": f"PATH_{a}_TO_{b}",
            "from": a,
            "to": b,
            "tangent36_turns": tangent,
            "tangent36_sha256": _sha_tangent(tangent),
            "length_turns_l2": math.sqrt(sum(x*x for x in tangent)),
        })
    ops=[
        "pnv.torus.normalize","pnv.torus.delta","pnv.torus.geodesic",
        "pnv.path.length_l2","pnv.orbit.arc_sample","pnv.path.compose",
    ]
    return {
        "schema":"PNV_NATIVE_FUNCTION_DB_V2",
        "dimension":36,
        "canonical":{
            "dimension":36,
            "operators":[{"id":x} for x in ops],
            "vectors":vectors,
            "paths":paths,
        },
    }


def _bindings(labels=("A","B","C"), anchors=("M0","M1","M2")):
    defs={
        _cid("def","hook-a"):("ORDER","TRANSFORM","COMPOSITION"),
        _cid("def","hook-b"):("IDENTITY",),
    }
    dids=list(defs)
    source_sha="0"*64
    out=[]
    for i,(label,anchor) in enumerate(zip(labels,anchors)):
        out.append(SemanticAnchorBinding(
            role_id=f"ROLE_{label}",
            semantic_content_id=_cid("class",f"semantic-{label}"),
            hook_definition_id=dids[i%2],
            anchor_id=anchor,
            source_digest_sha256=source_sha,
            source_locator="test:explicit-binding",
        ))
    return out,defs


def test_original_reverse_have_distinct_semantic_and_trajectory_ids():
    db=_fixture_db(); bindings,defs=_bindings()
    a=compile_ordered_semantic_path(bindings,native_db_v2=db,definition_schedules=defs)
    b=compile_ordered_semantic_path(list(reversed(bindings)),native_db_v2=db,definition_schedules=defs)
    assert a.ordered_semantic_id != b.ordered_semantic_id
    assert a.trajectory_id != b.trajectory_id
    assert a.phase36_sha256_sequence != b.phase36_sha256_sequence
    assert a.receipt["new_pnv_opcodes"] == 0
    assert a.receipt["htri_admitted"] is False


def test_surface_role_alias_does_not_change_semantic_identity():
    db=_fixture_db(); bindings,defs=_bindings()
    baseline=compile_ordered_semantic_path(bindings,native_db_v2=db,definition_schedules=defs)
    renamed=[SemanticAnchorBinding(
        role_id=f"RENAMED_{i}",
        semantic_content_id=x.semantic_content_id,
        hook_definition_id=x.hook_definition_id,
        anchor_id=x.anchor_id,
        source_digest_sha256=x.source_digest_sha256,
        source_locator=x.source_locator,
    ) for i,x in enumerate(bindings)]
    again=compile_ordered_semantic_path(renamed,native_db_v2=db,definition_schedules=defs)
    assert baseline.ordered_semantic_id == again.ordered_semantic_id
    assert baseline.trajectory_id == again.trajectory_id


def test_missing_registered_hook_definition_fails_closed():
    db=_fixture_db(); bindings,defs=_bindings()
    defs.pop(bindings[1].hook_definition_id)
    with pytest.raises(OrderedSemanticPathV30Error, match="schedule missing"):
        compile_ordered_semantic_path(bindings,native_db_v2=db,definition_schedules=defs)


def test_unadmitted_hook_leaf_fails_closed():
    db=_fixture_db(); bindings,defs=_bindings()
    defs[bindings[0].hook_definition_id] = ("AFFECT",)
    with pytest.raises(OrderedSemanticPathV30Error, match="without admitted"):
        compile_ordered_semantic_path(bindings,native_db_v2=db,definition_schedules=defs)


def test_unknown_anchor_fails_closed():
    db=_fixture_db(); bindings,defs=_bindings()
    bad=SemanticAnchorBinding(
        role_id="ROLE_BAD",
        semantic_content_id=_cid("class","bad"),
        hook_definition_id=bindings[0].hook_definition_id,
        anchor_id="M99",
        source_digest_sha256="0"*64,
        source_locator="test:bad-anchor",
    )
    with pytest.raises(OrderedSemanticPathV30Error, match="unknown canonical anchor"):
        compile_ordered_semantic_path([bindings[0],bad],native_db_v2=db,definition_schedules=defs)


def test_reverse_uses_typed_directed_composition_not_endpoint_shortcut():
    db=_fixture_db(); bindings,defs=_bindings(labels=("A","B"),anchors=("M0","M1"))
    rev=compile_ordered_semantic_path(list(reversed(bindings)),native_db_v2=db,definition_schedules=defs)
    assert rev.transitions[0].segment_ids == ("PATH_M1_TO_M2","PATH_M2_TO_M3","PATH_M3_TO_M0")


def test_same_anchor_retains_semantic_order_with_identity_geometry():
    db=_fixture_db(); bindings,defs=_bindings(labels=("A","B"),anchors=("M0","M0"))
    compiled=compile_ordered_semantic_path(bindings,native_db_v2=db,definition_schedules=defs)
    assert compiled.transitions[0].segment_ids == ()
    assert compiled.transitions[0].source_phase36_sha256 == compiled.transitions[0].target_phase36_sha256
    assert compiled.ordered_semantic_id


def test_compile_receipt_requires_live_admission_before_htri():
    db=_fixture_db(); bindings,defs=_bindings()
    compiled=compile_ordered_semantic_path(bindings,native_db_v2=db,definition_schedules=defs)
    assert compiled.receipt["live_admission_required"] is True
    assert compiled.receipt["htri_admitted"] is False


def test_tampered_native_vector_digest_fails_closed():
    db=_fixture_db(); bindings,defs=_bindings()
    db["canonical"]["vectors"]["M1"]["phase36"][0] += 0.01
    with pytest.raises(OrderedSemanticPathV30Error, match="vector digest mismatch"):
        compile_ordered_semantic_path(bindings,native_db_v2=db,definition_schedules=defs)
