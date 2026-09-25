import math
import pytest

from phasenav_natural_code.procedural_memory_runtime_v03 import ProceduralMemoryRuntime, RouteState
from phasenav_natural_code.memory_lifecycle_v03 import (
    LatentMemoryGate,
    MemoryLifecycleError,
    causal_efficacy_delta,
    decay_memory,
    decay_from_hybrid_ir,
)


def trained():
    rt = ProceduralMemoryRuntime(
        "skill",
        [RouteState("a", ("n0", "na")), RouteState("b", ("n0", "nb"))],
        learning_rate=0.2,
    )
    for _ in range(4):
        rt.apply_trace("b", outcome="POSITIVE")
    return rt


def test_latent_trace_exists_but_is_not_expressed_outside_context():
    rt = trained()
    digest = rt.digest
    gate = LatentMemoryGate(rt, ["task.search"])
    off = gate.evaluate("task.other")
    on = gate.evaluate("task.search")
    assert off.expressed is False and off.selected_route_id is None
    assert on.expressed is True and on.selected_route_id == "b"
    assert rt.digest == digest == off.memory_digest == on.memory_digest


def test_latent_activation_does_not_create_or_modify_memory():
    rt = trained()
    gate = LatentMemoryGate(rt, ["ctx.on"])
    before = rt.snapshot()
    for _ in range(20):
        gate.evaluate("ctx.on")
        gate.evaluate("ctx.off")
    assert rt.snapshot() == before


def test_decay_uses_explicit_semantic_time_and_preserves_input_runtime():
    rt = trained()
    before = rt.digest
    result = decay_memory(rt, delta_time=2.0, tau=2.0)
    assert result.receipt.factor == pytest.approx(math.exp(-1))
    assert result.receipt.to_dict()["wall_clock_used"] is False
    assert rt.digest == before
    assert result.runtime.digest != before


def test_zero_elapsed_time_is_identity_without_threshold():
    rt = trained()
    result = decay_memory(rt, delta_time=0.0, tau=10.0)
    assert result.runtime.digest == rt.digest
    assert result.receipt.changed_routes == 0


def test_forgetting_can_be_operationalized_as_loss_of_causal_efficacy():
    rt = trained()
    assert rt.guide() == "b"
    assert causal_efficacy_delta(rt) is True
    result = decay_memory(rt, delta_time=100.0, tau=1.0, extinction_threshold=1e-4)
    assert result.runtime.guide() == "a"
    assert result.receipt.extinguished_routes >= 1
    assert result.receipt.lost_choice_preference is True
    assert causal_efficacy_delta(result.runtime) is False


def test_decay_without_threshold_is_asymptotic_and_need_not_change_choice():
    rt = trained()
    result = decay_memory(rt, delta_time=100.0, tau=1.0)
    assert result.runtime.guide() == "b"
    assert result.receipt.lost_choice_preference is False


def test_invalid_lifecycle_parameters_fail_closed():
    rt = trained()
    with pytest.raises(MemoryLifecycleError):
        decay_memory(rt, delta_time=-1, tau=1)
    with pytest.raises(MemoryLifecycleError):
        decay_memory(rt, delta_time=1, tau=0)
    with pytest.raises(MemoryLifecycleError):
        LatentMemoryGate(rt, [])


def test_latent_and_decay_compile_from_hybrid_memory_ir():
    from phasenav_natural_code.hybrid_memory_grammar_v03 import compile_hybrid_memory_program
    source = """PROGRAM lifecycle
INPUT x : TEXT
COMPUTE y : TEXT USING echo INPUT x MODE AUTO
MEMORY m RETAINS PATH PERSISTENCE PERSISTENT ACCESS LATENT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC FORMAL_EXAMPLE
ROUTE r0 : input.x compute.y
REINFORCE r0 INTO m MODE ADAPTIVE
GUIDE compute.y USING m WHEN context.search
DECAY m TAU 10 THRESHOLD 0.01
RETURN y
"""
    ir = compile_hybrid_memory_program(source).to_ir()
    runtime = ProceduralMemoryRuntime.from_hybrid_ir(ir, "m")
    runtime.apply_trace("r0", outcome="POSITIVE")
    gate = LatentMemoryGate.from_hybrid_ir(ir, runtime, "compute.y")
    assert gate.evaluate("context.other").expressed is False
    assert gate.evaluate("context.search").selected_route_id == "r0"
    result = decay_from_hybrid_ir(ir, runtime, delta_time=10.0)
    assert result.receipt.tau == 10.0
    assert result.receipt.extinction_threshold == 0.01
    assert result.receipt.to_dict()["wall_clock_used"] is False


def test_unconditional_guide_rejects_latent_only_memory():
    from phasenav_natural_code.hybrid_memory_grammar_v03 import (
        HybridMemoryGrammarError,
        compile_hybrid_memory_program,
    )
    source = """PROGRAM bad_latent
INPUT x : TEXT
COMPUTE y : TEXT USING echo INPUT x MODE AUTO
MEMORY m RETAINS PATH PERSISTENCE PERSISTENT ACCESS LATENT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC FORMAL_EXAMPLE
ROUTE r0 : input.x compute.y
REINFORCE r0 INTO m MODE ADAPTIVE
GUIDE compute.y USING m
RETURN y
"""
    with pytest.raises(HybridMemoryGrammarError):
        compile_hybrid_memory_program(source)


def test_conditional_guide_rejects_nonlatent_memory():
    from phasenav_natural_code.hybrid_memory_grammar_v03 import (
        HybridMemoryGrammarError,
        compile_hybrid_memory_program,
    )
    source = """PROGRAM bad_conditional
INPUT x : TEXT
COMPUTE y : TEXT USING echo INPUT x MODE AUTO
MEMORY m RETAINS PATH PERSISTENCE PERSISTENT ACCESS IMPLICIT PLASTICITY ADAPTIVE EFFECT ROUTING EPISTEMIC FORMAL_EXAMPLE
ROUTE r0 : input.x compute.y
REINFORCE r0 INTO m MODE ADAPTIVE
GUIDE compute.y USING m WHEN context.search
RETURN y
"""
    with pytest.raises(HybridMemoryGrammarError):
        compile_hybrid_memory_program(source)
