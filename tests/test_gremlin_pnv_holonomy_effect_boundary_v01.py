import pytest

from phasenav_natural_code.gremlin_pnv_holonomy_v01 import (
    InformationHolonomyLoop,
    LawFrameNode,
    LawTransport,
    PNVInformationHolonomyError,
    audit_information_holonomy,
    compile_information_holonomy_loop,
    exact_state_metric,
    information_transport_connection,
    numeric_linf_metric,
)
from phasenav_natural_code.model import Kaku, Vector36


BASIS = "pncs:t36:holonomy-effect-boundary-test:v1"
GENERATION = "e" * 64


def _kaku() -> Kaku:
    return Kaku(
        kaku_id="LAW.LOCAL",
        vector=Vector36(tuple(0.1 + i / 100.0 for i in range(36)), BASIS),
        semantic_mass=0.5,
        direction="FORWARD",
        polarity=1.0,
        role="law_gate:local",
        phase=tuple((0.1 + i) / 36.0 for i in range(36)),
    )


def _loop() -> InformationHolonomyLoop:
    node = LawFrameNode("LAW.LOCAL.IDENTITY", "IDT", _kaku())
    return InformationHolonomyLoop(
        "LOCAL_EFFECT_BOUNDARY_LOOP",
        information_transport_connection("pncs:test:local-state:v1"),
        (node,),
        (LawTransport("E0", "LAW.LOCAL", "LAW.LOCAL", "identity"),),
    )


def _compile(loop: InformationHolonomyLoop):
    return compile_information_holonomy_loop(
        loop,
        generation_binding=GENERATION,
        identity="ZOSIA_NOEMA_FIRST",
        authority="USER_EXPLICIT_AUTHORING",
    )


def test_holonomy_propagates_unverified_callback_effect_boundary():
    loop = _loop()
    audit = audit_information_holonomy(
        loop,
        _compile(loop),
        initial_state=[1.0, 2.0],
        transforms={"identity": lambda x: x},
        state_metric=numeric_linf_metric,
        metric_id="L_INF",
    )

    native = audit.execution.receipt["effect_boundary"]
    assert native["external_effects"] is None
    assert native["external_effects_status"] == "UNVERIFIED_CALLBACK_BOUNDARY"
    assert native["callbacks_invoked"] == ["transform:identity"]

    boundary = audit.receipt["effect_boundary"]
    assert audit.receipt["external_effects"] is None
    assert audit.receipt["external_effects_status"] == "UNVERIFIED_CALLBACK_BOUNDARY"
    assert audit.receipt["deterministic_fields_only"] is False
    assert audit.receipt["deterministic_serialization"] is True
    assert audit.receipt["callback_determinism_verified"] is False
    assert boundary["native_callbacks_invoked"] == ["transform:identity"]
    assert boundary["audit_callbacks_invoked"] == ["state_metric:L_INF"]
    assert boundary["callback_effects_verified"] is False


def test_numeric_linf_overflow_fails_closed():
    with pytest.raises(PNVInformationHolonomyError, match="overflowed"):
        numeric_linf_metric(1.0e308, -1.0e308)
    with pytest.raises(PNVInformationHolonomyError, match="overflowed"):
        numeric_linf_metric([1.0e308], [-1.0e308])


def test_holonomy_metric_callback_exception_is_wrapped_fail_closed():
    loop = _loop()

    def broken_metric(_left, _right):
        raise RuntimeError("boom")

    with pytest.raises(PNVInformationHolonomyError, match="state metric L_INF callback failed"):
        audit_information_holonomy(
            loop,
            _compile(loop),
            initial_state=[1.0, 2.0],
            transforms={"identity": lambda x: x},
            state_metric=broken_metric,
            metric_id="L_INF",
        )


def test_metric_id_and_canonical_state_identity_are_normalized():
    assert exact_state_metric((1, 2), [1, 2]) == 0.0
    loop = _loop()
    with pytest.raises(PNVInformationHolonomyError, match="metric_id must be a non-empty string"):
        audit_information_holonomy(
            loop,
            _compile(loop),
            initial_state=[1.0, 2.0],
            transforms={"identity": lambda x: x},
            state_metric=numeric_linf_metric,
            metric_id="   ",
        )
