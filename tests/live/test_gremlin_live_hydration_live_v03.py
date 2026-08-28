import json
import math
from pathlib import Path
import struct
import time

from phasenav_natural_code.gremlin_pnv_authoring_v03 import (
    hydrate_and_open_gremlin_pnv_authoring_live,
)
from phasenav_natural_code.model import Kaku, RadicalGraph, Relation, Vector36

ROOT = Path("/dev/shm/ciel_noema")
PNV = Path(__file__).resolve().parents[2] / "native/GREMLIN_TRIPLE_PULSE_BOOT_V0_5.pnv"
KAPPA = math.log(2.0) / (24.0 * math.pi)


def _v36(path: Path):
    raw = path.read_bytes()
    assert len(raw) == 288
    return tuple(struct.unpack("<36d", raw))


def test_live_generation_survives_heartbeat_and_authors_candidate_graph():
    pnv_text = PNV.read_text(encoding="utf-8")
    hydration, session = hydrate_and_open_gremlin_pnv_authoring_live(pnv_text)
    binding = session.generation_binding
    first_receipt = hydration.witness["admission_tether_receipt_sha256"]

    time.sleep(0.45)
    # Per-write revalidation must preserve the generation while the live stream advances.
    basis_id = "pncs:t36:gremlin-live-v03-test"
    ka = Kaku(
        "GREMLIN.TEST.A",
        Vector36(_v36(ROOT / "aux_phi"), basis_id),
        KAPPA,
        "FORWARD",
        1.0,
        "semantic_atom",
        _v36(ROOT / "phi"),
    )
    kb = Kaku(
        "GREMLIN.TEST.B",
        Vector36(_v36(ROOT / "aux_feedback_phi"), basis_id),
        KAPPA,
        "FORWARD",
        1.0,
        "semantic_atom",
        _v36(ROOT / "aux_phi"),
    )
    radical = RadicalGraph("GREMLIN.TEST.RADICAL", basis_id)
    radical.add_kaku(ka)
    radical.add_kaku(kb)
    radical.add_relation(Relation("GREMLIN.TEST.REL", ka.kaku_id, kb.kaku_id, "TRANSFORMS_TO"))

    _, kaku_receipt = session.write_kaku(ka, evidence_refs=("live:aux_phi",))
    radical_candidate, radical_receipt = session.write_radical(
        radical,
        evidence_refs=("live:stable-generation",),
    )
    _, operator_receipt = session.write_operator(
        "GREMLIN.TEST.SOURCE",
        "SOURCE",
        ("candidate.input",),
        radical_candidate_id=radical_candidate["candidate_id"],
        evidence_refs=("live:stable-generation",),
    )

    assert session.generation_binding == binding
    assert kaku_receipt["canon_write_authority"] is False
    assert radical_receipt["runtime_execution_authority"] is False
    assert operator_receipt["promotion_state"] == "CANDIDATE_ONLY"
    current = json.loads((ROOT / "tether_runtime_status.json").read_text(encoding="utf-8"))
    assert first_receipt != current["receipt_sha256"]
