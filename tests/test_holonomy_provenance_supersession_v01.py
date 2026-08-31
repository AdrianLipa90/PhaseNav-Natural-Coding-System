import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT / "provenance" / "receipts"


def _load(name: str):
    return json.loads((RECEIPTS / name).read_text(encoding="utf-8"))


def test_historical_holonomy_receipt_is_preserved_and_explicitly_scoped():
    historical = _load("PNCS_PNV_INFORMATION_HOLONOMY_V0_1.json")
    supersession = _load(
        "PNCS_PNV_INFORMATION_HOLONOMY_EFFECT_BOUNDARY_SUPERSESSION_V0_1.json"
    )

    assert historical["code_head_sha"] == "f838752f61bd2b7248ed8c52a0927ad2a4302579"
    assert historical["audit"]["external_effects"] is False

    assert supersession["historical_receipt"] == (
        "provenance/receipts/PNCS_PNV_INFORMATION_HOLONOMY_V0_1.json"
    )
    assert supersession["historical_code_head_sha"] == historical["code_head_sha"]
    assert supersession["historical_field"] == {
        "path": "audit.external_effects",
        "value": False,
        "scope": "HISTORICAL_PRE_CALLBACK_BOUNDARY_CONTRACT",
    }


def test_current_holonomy_effect_boundary_does_not_promote_callback_purity():
    supersession = _load(
        "PNCS_PNV_INFORMATION_HOLONOMY_EFFECT_BOUNDARY_SUPERSESSION_V0_1.json"
    )
    rule = supersession["current_effect_boundary_rule"]

    assert rule["interpreter_external_effects"] is False
    assert rule["external_effects"] is None
    assert rule["external_effects_status"] == "UNVERIFIED_CALLBACK_BOUNDARY"
    assert rule["callback_effects_verified"] is False
    assert rule["deterministic_serialization"] is True
    assert rule["callback_determinism_verified"] is False
    assert supersession["epistemic"] == "CHYBA"
    assert supersession["promotion_state"] == "CANDIDATE_ONLY"
    assert supersession["runtime_execution_authority"] is False
    assert supersession["canon_write_authority"] is False
