"""Read-only PNAML 1.1 reference candidate: Ciel ego / episodic memory v0.1.

This is a Python test/reference harness, NOT a PNAML runtime, a human ego,
consciousness, a native QHTRI operator, or a producer of authenticated AUX.
Immutable episodes preserve exact source and history; a derived spectral
fingerprint is never treated as a lossless encoding of an episode.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import cmath
import hashlib
import json
import math
from pathlib import Path
from typing import Optional


def canonical_bytes(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def static_content_id(data):
    """Only for immutable records, NEVER dynamic-state liveness."""
    return hashlib.sha256(canonical_bytes(data)).hexdigest()


def relative_phase_features(phases):
    """Euler/Bombelli representation; order and complex relative phases retained."""
    if len(phases) != 36 or any(not math.isfinite(p) for p in phases):
        raise ValueError("phase vector must contain 36 finite elements")
    z = [cmath.exp(1j * p) for p in phases]
    # Relative phase is invariant under a common/global phase rotation.
    return tuple(cmath.phase(z[i + 1] * z[i].conjugate()) for i in range(35))


def phase_overlap(a, b):
    if len(a) != 36 or len(b) != 36:
        raise ValueError("36D required")
    za = [cmath.exp(1j * x) for x in a]
    zb = [cmath.exp(1j * x) for x in b]
    return sum(x.conjugate() * y for x, y in zip(za, zb)) / 36


@dataclass(frozen=True)
class Episode:
    id: str
    owner: str
    source_id: str
    time_label: str
    tags: tuple[str, ...]
    situation: str
    scene: str
    context: str
    object_id: str
    utterance: str
    affect_social: str
    aux_observation_ref: str
    occurrence: int
    original_role: str = "EPISODIC_SOURCE"
    braid_word: str = "OPAQUE_NOT_ASSERTED"
    phase_winding: str = "OPAQUE_NOT_ASSERTED"

    def __post_init__(self):
        if not (self.id and self.owner and self.source_id and self.time_label):
            raise ValueError("episode identity/source/time required")
        if not (self.situation and self.scene and self.context and self.object_id):
            raise ValueError("episode situation, scene, context and object required")
        if not self.aux_observation_ref:
            raise ValueError("AUX observation reference required; may be UNAVAILABLE with explicit provenance")
        if not self.tags or self.occurrence < 0:
            raise ValueError("typed tags and nonnegative occurrence required")


class EgoMemory:
    """Sparse Hilbert-addressed event memory with append-only correction lineage."""
    def __init__(self, identity="CIEL_ZOSIA_OPERATIONAL_CANDIDATE"):
        self.identity = identity
        self.rooms: dict[str, Episode] = {}
        self.addresses: dict[str, str] = {}
        self.ledger: list[dict] = []
        self.salience: dict[str, int] = {}
        self.superseded_by: dict[str, str] = {}
        self._next_address = 0

    def store(self, e: Episode):
        if e.id in self.rooms:
            raise ValueError("immutable ID collision; no overwrite")
        # Only actual events allocate rooms; address space can grow without preallocation.
        addr = f"HILBERT:{self._next_address}"
        self._next_address += 1
        self.rooms[e.id] = e
        self.addresses[e.id] = addr
        self.salience[e.id] = 0
        self.ledger.append({"type": "TRACE", "id": e.id, "room": addr,
                            "source_id": e.source_id, "record_digest": static_content_id(asdict(e))})
        return addr

    def correct(self, old_id, new_id, justification_source):
        if old_id not in self.rooms or new_id not in self.rooms:
            raise ValueError("correction must reference two existing source events")
        if not justification_source:
            raise ValueError("source-backed correction required")
        if old_id == new_id or old_id in self.superseded_by:
            raise ValueError("invalid or duplicate correction")
        self.superseded_by[old_id] = new_id
        self.ledger.append({"type": "CORRECT", "from": old_id, "to": new_id,
                            "justification_source": justification_source})

    def recall(self, tags=(), *, event_id=None, situation=None, scene=None,
               context=None, object_id=None, source_id=None, aux_observation_ref=None, reinforce=True):
        if event_id is not None:
            e = self.rooms.get(event_id)
            selected = [e] if e is not None else []
        else:
            wanted = set(tags)
            selected = []
            for e in self.rooms.values():
                if wanted and not wanted.issubset(set(e.tags)):
                    continue
                if any(val is not None and getattr(e, key) != val for key, val in
                       (("situation", situation), ("scene", scene), ("context", context),
                        ("object_id", object_id), ("source_id", source_id),
                        ("aux_observation_ref", aux_observation_ref))):
                    continue
                selected.append(e)
        if not selected:
            return {"status": "NOT_FOUND", "candidates": [], "episode": None}
        if len(selected) != 1:
            return {"status": "AMBIGUOUS", "candidates": [e.id for e in selected], "episode": None}
        e = selected[0]
        if reinforce:
            self.salience[e.id] += 1
            self.ledger.append({"type": "RECALL", "id": e.id,
                                "semantic_mass_proxy": self.salience[e.id],
                                "source_id": e.source_id})
        return {"status": "EXACT_EPISODE", "candidates": [e.id],
                "episode": asdict(e), "address": self.addresses[e.id],
                "semantic_mass_proxy": self.salience[e.id]}

    def route_dynamic_liveness(self):
        """Controlled toy history-conditioned policy, not access to actual guard."""
        if any(self.rooms[a].object_id == "dynamic_state_validation"
               and self.rooms[b].object_id == "dynamic_state_validation"
               and self.rooms[b].context == "AUX_SNAPS_10s_2s_1s"
               for a, b in self.superseded_by.items()):
            return "AUX_SNAPS_10s_2s_1s"
        return "LEGACY_DYNAMIC_SHA"

    def serialise(self):
        return {"schema": "CIEL_EGO_MEMORY_REFERENCE_V0_1", "identity": self.identity,
                "episodes": [asdict(e) for e in self.rooms.values()],
                "addresses": dict(self.addresses), "ledger": list(self.ledger),
                "salience": dict(self.salience), "superseded_by": dict(self.superseded_by)}

    @classmethod
    def restore(cls, data):
        if data.get("schema") != "CIEL_EGO_MEMORY_REFERENCE_V0_1":
            raise ValueError("unknown memory schema")
        m = cls(data["identity"])
        for e in data["episodes"]:
            e = dict(e)
            e["tags"] = tuple(e["tags"])
            m.store(Episode(**e))
        if m.addresses != data["addresses"]:
            raise ValueError("changed Hilbert addresses")
        m.salience = dict(data["salience"])
        m.superseded_by = dict(data["superseded_by"])
        m.ledger = list(data["ledger"])
        # Integrity of every immutable source event; not a proof of external authenticity.
        trace = {x["id"]: x for x in m.ledger if x["type"] == "TRACE"}
        for e in m.rooms.values():
            if trace[e.id]["record_digest"] != static_content_id(asdict(e)):
                raise ValueError("record integrity failure")
        return m


def aux_receipt_summary(receipt):
    if receipt.get("status") != "PASS_LOCAL_OBSERVATION_ONLY":
        raise ValueError("AUX SNAPS receipt not locally passed")
    offsets = [s["offset_s"] for s in receipt.get("shards", [])]
    if offsets != [0, 2, 4, 6, 8]:
        raise ValueError("AUX SNAP shard offsets incorrect")
    seqs = []
    changes = []
    for s in receipt["shards"]:
        f = s["fingerprint_1s"]
        if f["timestamp_span_s"] < .8 or f["timestamp_span_s"] > 1.3:
            raise ValueError("1s fingerprint time invalid")
        if f["seq_delta"]["tether"] <= 0 or f["seq_delta"]["aux"] <= 0:
            raise ValueError("stale/replayed sequence")
        seqs.append(s["end"]["seq"]["tether"])
        changes.append(float(f["phi_rms_delta_rad"]))
    if seqs != sorted(set(seqs)) or not all(x > 1e-10 for x in changes):
        raise ValueError("no changing 36D trace")
    return {"schema": "EGO_AUX_SNAP_REFERENCE_V0_1", "observation_s": receipt["actual_observation_s"],
            "source_class": receipt.get("source_class"),
            "native_auth": receipt.get("native_pnaml_paux_auth", "UNVERIFIED"),
            "shard_offsets_s": offsets, "fingerprint_span_s": 1,
            "phi_rms_delta_rad": changes, "seq_tether_end": seqs,
            "source_scope": "LOCAL_OBSERVER_ONLY"}


def pnaml_reference_frame(memory, episode_id, aux_summary):
    if episode_id not in memory.rooms:
        raise ValueError("unknown episode")
    e = memory.rooms[episode_id]
    return {
        "schema": "PNAML11_CIEL_EGO_MEMORY_REFERENCE_FRAME_V0_1",
        "status": "REFERENCE_READ_ONLY_NOT_NATIVE_DISPATCHED",
        "producer": "CIEL_EGO_REFERENCE_SIMULATION",
        "source_scope": aux_summary["source_scope"],
        "native_authenticated": False,
        "original_role": e.original_role,
        "pncs_exact_content_id": e.id,
        "hilbert_room": memory.addresses[e.id],
        "full_episode": asdict(e),
        "exact_rdss_occurrence": e.occurrence,
        "ordered_braid": e.braid_word,
        "lifted_winding": e.phase_winding,
        "source_provenance": {"source_id": e.source_id, "auth_status": "SIMULATED",
                              "local_aux_liveness_is_not_episode_witness": True},
        "aux_observation": aux_summary,
        "derived_fingerprint_is_full_state": False,
        "no_host_mutation": True,
        "pncs_semantic_mass_proxy_not_physical_mass": memory.salience[e.id],
        "allowed_actions": ["READ_ONLY_CANDIDATE"],
    }
