from __future__ import annotations

import math

from phasenav_natural_code.semantic_address_v31 import (
    DIM,
    SemanticAddressV31Error,
    build_semantic_trajectory,
    generate_semantic_address,
)
from phasenav_natural_code.semantic_sequence_v31 import (
    build_nisaba_frozen_roles,
    compile_semantic_sequence,
)

SOURCE_SHA = "0a6c02eda6b5e0b890e1ea5106a9c5b302cc4ef52de426cea0187134ae27750d"


def compiled_original():
    roles = build_nisaba_frozen_roles(source_digest_sha256=SOURCE_SHA)
    return compile_semantic_sequence(roles)


def test_address_generator_is_deterministic_and_exact_36d():
    content_id = compiled_original().content_ids[0]
    a = generate_semantic_address(content_id)
    b = generate_semantic_address(content_id)
    assert a == b
    assert len(a.phase36) == DIM
    assert all(math.isfinite(x) and 0.0 <= x < 2.0 * math.pi for x in a.phase36)
    assert a.phase36_sha256 == b.phase36_sha256
    assert a.address_id == b.address_id


def test_seven_semantic_roles_have_seven_distinct_computational_addresses():
    compiled = compiled_original()
    addresses = [generate_semantic_address(x) for x in compiled.content_ids]
    assert len({x.phase36_sha256 for x in addresses}) == 7
    assert len({x.address_id for x in addresses}) == 7


def test_original_reverse_and_shuffle_have_distinct_trajectory_identities():
    roles = build_nisaba_frozen_roles(source_digest_sha256=SOURCE_SHA)
    original = compile_semantic_sequence(roles)
    reverse = compile_semantic_sequence(tuple(reversed(roles)))
    shuffle = compile_semantic_sequence((roles[3], roles[6], roles[0], roles[4], roles[2], roles[5], roles[1]))

    a = build_semantic_trajectory(original.ordered_semantic_id, original.content_ids)
    b = build_semantic_trajectory(reverse.ordered_semantic_id, reverse.content_ids)
    c = build_semantic_trajectory(shuffle.ordered_semantic_id, shuffle.content_ids)

    assert a.trajectory_id != b.trajectory_id
    assert a.trajectory_id != c.trajectory_id
    assert b.trajectory_id != c.trajectory_id
    assert a.payload["htri_admitted"] is False
    assert a.payload["blocked_next_gate"] == "MISSING_NATIVE_ORDERED_T36_TO_HTRI_DRIVE_PRIMITIVE"


def test_reverse_reuses_same_addresses_but_reverses_order():
    original = compiled_original()
    a = build_semantic_trajectory(original.ordered_semantic_id, original.content_ids)
    reverse_ids = tuple(reversed(original.content_ids))
    b = build_semantic_trajectory("pncs:semantic-sequence:sha256:" + "0" * 64, reverse_ids)
    assert [x.address_id for x in b.addresses] == list(reversed([x.address_id for x in a.addresses]))


def test_transition_geometry_is_exact_wrapped_shortest_torus_delta():
    original = compiled_original()
    traj = build_semantic_trajectory(original.ordered_semantic_id, original.content_ids)
    for i, t in enumerate(traj.transitions):
        a = traj.addresses[i]
        b = traj.addresses[i + 1]
        assert len(t.tangent36_turns) == 36
        assert all(-0.5 <= x < 0.5 for x in t.tangent36_turns)
        expected = math.sqrt(sum(x * x for x in t.tangent36_turns))
        assert abs(t.length_turns_l2 - expected) < 1e-15


def test_generator_never_promotes_semantics_or_htri_authority():
    original = compiled_original()
    traj = build_semantic_trajectory(original.ordered_semantic_id, original.content_ids)
    for address in traj.addresses:
        assert address.payload["semantic_authority"] is False
        assert address.payload["semantic_similarity_from_geometry"] is False
        assert address.payload["canon_allowed"] is False
    assert traj.payload["geometry_creates_semantics"] is False
    assert traj.payload["htri_drive_defined"] is False
    assert traj.payload["htri_admitted"] is False
    assert traj.payload["new_pnv_opcodes"] == 0


def test_untyped_content_id_is_rejected():
    try:
        generate_semantic_address("Awe")
    except SemanticAddressV31Error:
        pass
    else:
        raise AssertionError("untyped label must fail closed")
