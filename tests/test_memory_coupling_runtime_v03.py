import pytest

from phasenav_natural_code.procedural_memory_runtime_v03 import ProceduralMemoryRuntime, RouteState
from phasenav_natural_code.memory_coupling_runtime_v03 import (
    CouplingSpec,
    MemoryCouplingRuntime,
    MemoryCouplingRuntimeError,
)


def _runtime(mid):
    return ProceduralMemoryRuntime(
        mid,
        [RouteState("a", ("n0", "na")), RouteState("b", ("n0", "nb"))],
        learning_rate=0.1,
    )


def test_consolidation_transfers_only_new_trace_deltas():
    fast, slow = _runtime("fast"), _runtime("slow")
    fast.apply_trace("b", outcome="POSITIVE", magnitude=2)
    fast.apply_trace("b", outcome="POSITIVE", magnitude=1)
    c = MemoryCouplingRuntime(
        runtimes={"fast": fast, "slow": slow},
        couplings=(CouplingSpec("fast", "slow", "CONSOLIDATE", "slow"),),
    )
    r1 = c.consolidate("fast->slow:consolidate", transfer_fraction=0.5)
    assert r1.transferred_traces == 2
    assert slow.route("b").weight == pytest.approx(0.15)
    digest = slow.digest
    r2 = c.consolidate("fast->slow:consolidate", transfer_fraction=0.5)
    assert r2.transferred_traces == 0
    assert slow.digest == digest


def test_later_trace_consolidates_incrementally_without_double_counting():
    fast, slow = _runtime("fast"), _runtime("slow")
    c = MemoryCouplingRuntime(
        runtimes={"fast": fast, "slow": slow},
        couplings=(CouplingSpec("fast", "slow", "CONSOLIDATE"),),
    )
    fast.apply_trace("a", outcome="POSITIVE")
    c.consolidate("fast->slow:consolidate")
    assert slow.route("a").weight == pytest.approx(0.1)
    fast.apply_trace("a", outcome="POSITIVE")
    r = c.consolidate("fast->slow:consolidate")
    assert r.transferred_traces == 1
    assert slow.route("a").weight == pytest.approx(0.2)


def test_negative_trace_consolidates_with_sign_preserved():
    fast, slow = _runtime("fast"), _runtime("slow")
    fast.apply_trace("a", outcome="NEGATIVE", magnitude=3)
    c = MemoryCouplingRuntime(
        runtimes={"fast": fast, "slow": slow},
        couplings=(CouplingSpec("fast", "slow", "CONSOLIDATE"),),
    )
    c.consolidate("fast->slow:consolidate", transfer_fraction=0.5)
    assert slow.route("a").weight == pytest.approx(-0.15)


def test_reactivation_reads_slow_preference_without_mutating_target():
    slow, active = _runtime("slow"), _runtime("active")
    slow.apply_trace("b", outcome="POSITIVE", magnitude=4)
    c = MemoryCouplingRuntime(
        runtimes={"slow": slow, "active": active},
        couplings=(CouplingSpec("slow", "active", "REACTIVATE", "fast"),),
    )
    digest = active.digest
    assert c.reactivate("slow->active:reactivate") == "b"
    assert active.digest == digest


def test_missing_target_route_fails_closed():
    fast = _runtime("fast")
    slow = ProceduralMemoryRuntime("slow", [RouteState("a", ("n0", "na"))])
    fast.apply_trace("b", outcome="POSITIVE")
    c = MemoryCouplingRuntime(
        runtimes={"fast": fast, "slow": slow},
        couplings=(CouplingSpec("fast", "slow", "CONSOLIDATE"),),
    )
    with pytest.raises(MemoryCouplingRuntimeError):
        c.consolidate("fast->slow:consolidate")


def test_from_hybrid_ir_binds_declared_coupling():
    fast, slow = _runtime("fast"), _runtime("slow")
    ir = {
        "memory_model": {
            "operations": [
                {
                    "kind": "COUPLE",
                    "attributes": {
                        "source_memory": "fast",
                        "target_memory": "slow",
                        "relation": "consolidate",
                        "timescale": "slow",
                    },
                }
            ]
        }
    }
    c = MemoryCouplingRuntime.from_hybrid_ir(ir, runtimes={"fast": fast, "slow": slow})
    fast.apply_trace("b", outcome="POSITIVE")
    r = c.consolidate("fast->slow:consolidate")
    assert r.transferred_traces == 1
    assert slow.guide() == "b"
