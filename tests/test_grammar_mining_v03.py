from pathlib import Path
import json

ROOT = Path(__file__).parents[1]
PNV = ROOT / "native" / "PNCS_GRAMMAR_MINING_V0_3.pnv"
LEDGER = ROOT / "mining" / "PNCS_RELATION_MINING_LEDGER_V0_3.json"
ALLOWED_OPS = {
    "IDENTITY", "DIFFERENCE", "ORDER", "COMPOSITION", "ADDITION", "FORCE",
    "NEGATION", "QUESTION", "TRANSFORM", "RETURN", "FOLD", "BOUNDARY", "SCOPE",
    "AFFECT", "CONSENT", "SOURCE", "MEMORY", "RISK", "ASSERTION", "CONDITION",
    "CAUSE", "MODAL_POSSIBILITY", "MODAL_NECESSITY", "MODAL_PERMISSION",
    "MODAL_OBLIGATION", "UNCERTAINTY", "SOURCE_REQUIRED", "CANON_BLOCK",
    "CONSENT_REQUIRED", "ACTION_REQUEST", "REFUSAL", "PAUSE", "SIMULATION_BOUNDARY",
    "UNRUH_DRIVE", "WARP_DRIFT", "ATTRACTOR", "SOFT_CLIP", "RESOLVE", "DERIVE",
}

def active_lines():
    return [x.strip() for x in PNV.read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]

def test_mining_pnv_uses_only_existing_opcodes():
    for line in active_lines():
        parts=line.split()
        if parts[0] == "OP":
            assert parts[2] in ALLOWED_OPS, line

def test_no_duplicate_operator_ids():
    ids=[x.split()[1] for x in active_lines() if x.startswith("OP ")]
    assert len(ids)==len(set(ids))

def test_ledger_has_two_source_families_and_ten_chains():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    assert len(data["chains"]) >= 10
    assert any(x["id"].startswith("TIR.") for x in data["chains"])
    assert any(x["id"].startswith("SOH.") for x in data["chains"])

def test_cross_source_core_is_recurrent():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    rows={x["operator"]:x for x in data["operator_recurrence"]}
    for op in data["cross_source_core"]:
        assert rows[op]["occurrences"] >= 2
        assert rows[op]["source_families"] >= 2

def test_radicals_are_compositions_not_new_opcodes():
    text=PNV.read_text(encoding="utf-8")
    for rid in ["R.FIXED_POINT","R.INVARIANT","R.CANCELLATION","R.CONJUGACY","R.CONVERGENCE"]:
        line=next(x for x in active_lines() if x.startswith(f"OP {rid} "))
        assert line.split()[2] == "COMPOSITION"

def test_recurrence_not_promoted_to_semantic_mass():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["rules"]["recurrence_is_not_semantic_mass"] is True
