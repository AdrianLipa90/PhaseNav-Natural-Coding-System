from pathlib import Path
import json

ROOT = Path(__file__).parents[1]
PNV = ROOT / "native" / "PNCS_PRIMITIVE_CLOSURE_V0_4.pnv"
LEDGER = ROOT / "mining" / "PNCS_PRIMITIVE_CLOSURE_LEDGER_V0_4.json"
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

def op_rows():
    rows={}
    for line in active_lines():
        parts=line.split()
        if parts[0] == "OP":
            rows[parts[1]] = parts[2:]
    return rows

def test_v04_uses_only_existing_pnv_opcodes():
    for line in active_lines():
        parts=line.split()
        if parts[0] == "OP":
            assert parts[2] in ALLOWED_OPS, line

def test_minimal_v03_core_has_seven_operators():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    assert len(data["minimal_v03_core"]) == 7
    assert set(data["minimal_v03_core"]) == {"TRANSFORM","DIFFERENCE","IDENTITY","COMPOSITION","CONDITION","RESOLVE","DERIVE"}

def test_invariant_atomic_path_is_unchanged_and_promoted():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    row=data["radicals"]["R.INVARIANT"]
    assert row["path"] == ["TRANSFORM","DIFFERENCE","IDENTITY"]
    assert row["status"] == "PROMOTED_GRAMMAR_RADICAL"
    assert len(row["realizations"]) >= 3

def test_invariant_transfers_without_special_opcode():
    rows=op_rows()
    for rid in ["TIR.TRANSLATION_INVARIANCE","PNV.GLOBAL_PHASE_INVARIANCE","CD.INVARIANT_DEFINITION"]:
        assert rows[rid][0] == "COMPOSITION"
        assert rows[rid][1] == "R.INVARIANT"

def test_trajectory_candidate_has_same_path_across_two_realizations():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["radicals"]["R.TRAJECTORY"]["path"] == ["ORDER","TRANSFORM","COMPOSITION"]
    rows=op_rows()
    assert rows["PNV.SENTENCE_TRAJECTORY"][1] == "R.TRAJECTORY"
    assert rows["CD.TRAJECTORY_DEFINITION"][1] == "R.TRAJECTORY"

def test_normal_form_keeps_vector_similarity_non_authoritative():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    nf=data["normal_form"]
    assert nf["ordered_kaku_authoritative"] is True
    assert nf["argument_binding_required"] is True
    assert nf["vector_similarity_implies_semantic_equivalence"] is False
    assert nf["surface_text_is_authoritative"] is False

def test_no_duplicate_operator_ids_v04():
    ids=[x.split()[1] for x in active_lines() if x.startswith("OP ")]
    assert len(ids)==len(set(ids))
