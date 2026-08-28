import math

import pytest

from phasenav_natural_code.gremlin_pnv_holonomy_v01 import (
    HOLONOMY_AUDIT_RECEIPT_SCHEMA,
    HOLONOMY_CONTRACT,
    INFORMATION_TRANSPORT_CONNECTION_ID,
    LEGACY_TYPED_CONNECTION_CONTRACT_SHA256,
    HolonomyConnection,
    HolonomyInvariant,
    InformationHolonomyLoop,
    LawFrameNode,
    LawTransport,
    PNVInformationHolonomyError,
    audit_information_holonomy,
    compile_information_holonomy_loop,
    information_transport_connection,
    numeric_linf_metric,
    persist_information_holonomy_audit,
)
from phasenav_natural_code.model import Kaku, Vector36
from phasenav_natural_code.native_pnv_exec_v01 import parse_pnv


BASIS = "pncs:t36:law-frame-test:v1"
CONTENT = "pncs:def:sha256:" + "4" * 64
GENERATION = "e" * 64


def _kaku(kaku_id: str, seed: float, role: str, basis: str = BASIS) -> Kaku:
    return Kaku(
        kaku_id=kaku_id,
        vector=Vector36(tuple(seed + i / 100.0 for i in range(36)), basis),
        semantic_mass=0.4 + seed,
        direction="FORWARD",
        polarity=1.0,
        role=role,
        phase=tuple((seed + i) / 36.0 for i in range(36)),
    )


def _connection():
    return information_transport_connection(
        "pncs:test:information-state:v1",
        evidence_refs=("evidence:typed-information-connection",),
    )


def _loop(*, invariants=(), connection=None):
    left = LawFrameNode(
        "LAW.IDT.NORMALIZATION",
        "IDT",
        _kaku("LAW.IDT", 0.1, f"law_gate:normalization:{CONTENT}"),
        ("evidence:idt",),
    )
    right = LawFrameNode(
        "LAW.RFC.SOURCE",
        "RFC",
        _kaku("LAW.RFC", 0.2, "law_gate:source"),
        ("evidence:rfc",),
    )
    return InformationHolonomyLoop(
        "IDT_RFC_TEST_LOOP",
        connection or _connection(),
        (left, right),
        (
            LawTransport("EDGE.IDT.RFC", "LAW.IDT", "LAW.RFC", "scale2"),
            LawTransport("EDGE.RFC.IDT", "LAW.RFC", "LAW.IDT", "scale_half"),
        ),
        tuple(invariants),
        ("evidence:law-frame",),
    )


def _compile(loop):
    return compile_information_holonomy_loop(
        loop,
        generation_binding=GENERATION,
        identity="ZOSIA_NOEMA_FIRST",
        authority="USER_EXPLICIT_AUTHORING",
    )


def test_closed_law_frame_compiles_to_source_transforms_return():
    loop = _loop()
    compiled = _compile(loop)
    program = parse_pnv(compiled.pnv_text)
    assert [op.opcode for op in program.ops] == ["SOURCE", "TRANSFORM", "TRANSFORM", "RETURN"]
    assert [op.name for op in program.ops] == ["HOL.START", "HOL.EDGE.000", "HOL.EDGE.001", "HOL.RETURN"]
    assert compiled.receipt["holonomy_contract"] == HOLONOMY_CONTRACT
    assert compiled.receipt["loop_id"] == loop.loop_id


def test_connection_is_explicit_and_bound_into_compilation_receipt():
    loop = _loop()
    compiled = _compile(loop)
    connection = compiled.receipt["connection"]
    assert connection["connection_id"] == INFORMATION_TRANSPORT_CONNECTION_ID
    assert connection["connection_sha256"] == loop.connection.connection_sha256
    assert connection["state_space_id"] == "pncs:test:information-state:v1"
    assert compiled.receipt["legacy_connection_firewall"]["contract_sha256"] == LEGACY_TYPED_CONNECTION_CONTRACT_SHA256
    assert all(row["connection_id"] == INFORMATION_TRANSPORT_CONNECTION_ID for row in compiled.receipt["transport_plan"])


def test_same_cycle_under_different_connection_gets_distinct_provenance():
    a = _compile(_loop())
    other_connection = HolonomyConnection(
        connection_id="PNCS_SECOND_TEST_CONNECTION_V0_1",
        connection_kind="INFORMATION_TRANSPORT",
        state_space_id="pncs:test:information-state:v1",
        contract_ref="test:second-connection",
        execution_state="READY_CANDIDATE",
    )
    b = _compile(_loop(connection=other_connection))
    assert a.receipt["connection"]["connection_sha256"] != b.receipt["connection"]["connection_sha256"]
    assert a.receipt["receipt_sha256"] != b.receipt["receipt_sha256"]
    assert a.radical_candidate["candidate_id"] != b.radical_candidate["candidate_id"]


def test_open_connection_blocks_holonomy_execution_gate():
    open_connection = HolonomyConnection(
        connection_id="BERRY_CP1",
        connection_kind="BERRY",
        state_space_id="CP1",
        contract_ref="PNV_CONNECTION_TYPED_HOLONOMY_CONTRACT_V1_CANDIDATE",
        execution_state="OPEN",
        evidence_refs=("gate:berry-pullback-open",),
    )
    loop = _loop(connection=open_connection)
    compiled = _compile(loop)
    with pytest.raises(PNVInformationHolonomyError, match="connection execution gate OPEN"):
        audit_information_holonomy(
            loop,
            compiled,
            initial_state=[1.0, 2.0],
            transforms={"scale2": lambda x: x, "scale_half": lambda x: x},
            state_metric=numeric_linf_metric,
            metric_id="L_INF",
        )


def test_zero_defect_loop_passes_and_binds_inverse_lineage():
    loop = _loop(invariants=(HolonomyInvariant("RATIO", "ABS", 0.0),))
    compiled = _compile(loop)
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=[2.0, 4.0],
        transforms={
            "scale2": lambda x: [2.0 * v for v in x],
            "scale_half": lambda x: [0.5 * v for v in x],
        },
        state_metric=numeric_linf_metric,
        metric_id="L_INF",
        invariant_evaluators={"RATIO": lambda x: x[1] / x[0]},
    )
    assert audit.state_defect == 0.0
    assert audit.receipt["status"] == "PASS"
    assert audit.receipt["schema"] == HOLONOMY_AUDIT_RECEIPT_SCHEMA
    assert audit.receipt["connection_id"] == INFORMATION_TRANSPORT_CONNECTION_ID
    assert audit.invariant_results[0]["passed"] is True
    assert audit.inverse_lineage.operator_rows[0]["name"] == "HOL.RETURN"
    assert CONTENT in audit.inverse_lineage.payload["explicit_content_ids"]


def test_positive_holonomy_defect_fails_audit_without_promotion():
    loop = _loop()
    compiled = _compile(loop)
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=[1.0, 2.0],
        transforms={
            "scale2": lambda x: [2.0 * v for v in x],
            "scale_half": lambda x: [0.5 * v + 0.25 for v in x],
        },
        state_metric=numeric_linf_metric,
        metric_id="L_INF",
        state_tolerance=0.0,
    )
    assert audit.state_defect == pytest.approx(0.25)
    assert audit.receipt["status"] == "FAIL"
    assert audit.receipt["promotion_state"] == "CANDIDATE_ONLY"
    assert audit.receipt["canon_write_authority"] is False


def test_invariant_drift_can_fail_even_when_loop_final_state_closes():
    loop = _loop(invariants=(HolonomyInvariant("FIRST", "ABS", 0.0),))
    compiled = _compile(loop)
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=[2.0, 4.0],
        transforms={
            "scale2": lambda x: [2.0 * v for v in x],
            "scale_half": lambda x: [0.5 * v for v in x],
        },
        state_metric=numeric_linf_metric,
        metric_id="L_INF",
        invariant_evaluators={"FIRST": lambda x: x[0]},
    )
    assert audit.state_defect == 0.0
    assert audit.invariant_results[0]["max_defect"] == pytest.approx(2.0)
    assert audit.invariant_results[0]["passed"] is False
    assert audit.receipt["status"] == "FAIL"


def test_missing_transform_fails_closed_before_execution():
    loop = _loop()
    compiled = _compile(loop)
    with pytest.raises(PNVInformationHolonomyError, match="missing admitted holonomy transform"):
        audit_information_holonomy(
            loop,
            compiled,
            initial_state=[1.0, 2.0],
            transforms={"scale2": lambda x: x},
            state_metric=numeric_linf_metric,
            metric_id="L_INF",
        )


def test_transport_order_must_close_declared_cycle():
    left = LawFrameNode("A", "IDT", _kaku("A", 0.1, "a"))
    right = LawFrameNode("B", "RFC", _kaku("B", 0.2, "b"))
    with pytest.raises(PNVInformationHolonomyError, match="does not close loop"):
        InformationHolonomyLoop(
            "BROKEN",
            _connection(),
            (left, right),
            (
                LawTransport("E0", "A", "A", "identity"),
                LawTransport("E1", "B", "A", "identity"),
            ),
        )


def test_local_single_node_self_loop_is_admitted_and_can_close_exactly():
    node = LawFrameNode("LAW.LOCAL.IDENTITY", "IDT", _kaku("LAW.LOCAL", 0.1, f"local:{CONTENT}"))
    loop = InformationHolonomyLoop(
        "LOCAL_SELF_LOOP",
        information_transport_connection("pncs:test:local-state:v1"),
        (node,),
        (LawTransport("E0", "LAW.LOCAL", "LAW.LOCAL", "identity"),),
    )
    compiled = _compile(loop)
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=[1.0, 2.0],
        transforms={"identity": lambda x: x},
        state_metric=numeric_linf_metric,
        metric_id="L_INF",
    )
    assert audit.state_defect == 0.0
    assert audit.receipt["status"] == "PASS"
    assert compiled.receipt["law_frame"][0]["domain"] == "IDT"


def test_law_frame_requires_exact_shared_basis():
    left = LawFrameNode("A", "IDT", _kaku("A", 0.1, "a"))
    right = LawFrameNode("B", "RFC", _kaku("B", 0.2, "b", basis="pncs:other:basis"))
    with pytest.raises(PNVInformationHolonomyError, match="share one exact PNCS basis"):
        InformationHolonomyLoop(
            "MIXED_BASIS",
            _connection(),
            (left, right),
            (LawTransport("E0", "A", "B", "identity"), LawTransport("E1", "B", "A", "identity")),
        )


def test_nonfinite_state_metric_fails_closed():
    loop = _loop()
    compiled = _compile(loop)
    with pytest.raises(PNVInformationHolonomyError, match="state holonomy defect"):
        audit_information_holonomy(
            loop,
            compiled,
            initial_state=[1.0, 2.0],
            transforms={"scale2": lambda x: x, "scale_half": lambda x: x},
            state_metric=lambda _a, _b: math.nan,
            metric_id="BAD_METRIC",
        )


def test_holonomy_audit_persistence_is_content_addressed_and_idempotent(tmp_path):
    loop = _loop()
    compiled = _compile(loop)
    audit = audit_information_holonomy(
        loop,
        compiled,
        initial_state=[1.0, 2.0],
        transforms={"scale2": lambda x: [2.0 * v for v in x], "scale_half": lambda x: [0.5 * v for v in x]},
        state_metric=numeric_linf_metric,
        metric_id="L_INF",
    )
    first = persist_information_holonomy_audit(audit, authoring_root=tmp_path)
    second = persist_information_holonomy_audit(audit, authoring_root=tmp_path)
    assert first == second
    assert first.endswith(str(audit.receipt["receipt_sha256"]) + ".json")
