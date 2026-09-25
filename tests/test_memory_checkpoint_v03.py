import json
import pytest

from phasenav_natural_code.procedural_memory_runtime_v03 import (
    ProceduralMemoryRuntime,
    RouteState,
)
from phasenav_natural_code.memory_checkpoint_v03 import (
    MemoryCheckpointError,
    export_checkpoint,
    restore_checkpoint,
)


def _trained():
    rt = ProceduralMemoryRuntime(
        "skill",
        [
            RouteState("a", ("n0", "na", "target")),
            RouteState("b", ("n0", "nb", "target")),
        ],
        learning_rate=0.2,
    )
    rt.apply_trace("b", outcome="POSITIVE", event_id="e1")
    rt.apply_trace("b", outcome="POSITIVE", event_id="e2")
    rt.apply_trace("a", outcome="NEGATIVE", event_id="e3")
    return rt


def test_checkpoint_roundtrip_preserves_state_choice_and_provenance():
    rt = _trained()
    env = export_checkpoint(rt)
    restored = restore_checkpoint(env.raw)

    assert restored.digest == rt.digest
    assert restored.guide() == rt.guide() == "b"
    assert restored.snapshot() == rt.snapshot()
    assert [x.to_dict() for x in restored.receipts] == [
        x.to_dict() for x in rt.receipts
    ]
    assert env.state_digest == rt.digest
    assert env.receipt_count == 3


def test_restore_then_continue_preserves_receipt_chain():
    rt = _trained()
    restored = restore_checkpoint(export_checkpoint(rt).raw)
    prior = restored.receipts[-1].after_digest
    new = restored.apply_trace("a", outcome="POSITIVE", event_id="e4")
    assert new.sequence == 4
    assert new.before_digest == prior
    assert new.after_digest == restored.digest


def test_checkpoint_is_deterministic_for_same_state_and_provenance():
    rt = _trained()
    a = export_checkpoint(rt)
    b = export_checkpoint(rt)
    assert a.raw == b.raw
    assert a.sha256 == b.sha256


def test_tampered_state_fails_digest_validation():
    rt = _trained()
    env = export_checkpoint(rt)
    obj = json.loads(env.raw)
    obj["runtime_snapshot"]["routes"][0]["weight"] = 999.0
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(MemoryCheckpointError):
        restore_checkpoint(raw)


def test_broken_receipt_chain_fails_closed():
    rt = _trained()
    obj = json.loads(export_checkpoint(rt).raw)
    obj["receipts"][1]["before_digest"] = "0" * 64
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(MemoryCheckpointError):
        restore_checkpoint(raw)


def test_checkpoint_never_claims_implicit_durable_write():
    rt = _trained()
    env = export_checkpoint(rt)
    meta = env.to_dict()
    assert meta["durable_write_performed"] is False
    obj = json.loads(env.raw)
    assert obj["durable_write_performed"] is False
