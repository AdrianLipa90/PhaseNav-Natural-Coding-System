from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
PNV=HERE/"native"/"PNCS_V1_RELEASE_TRAIN_V0_1.pnv"
ALLOWED={"PNV","EPISTEMIC","MODE","OP","VECTOR","EMIT"}
OPS={"BOUNDARY","TRANSFORM","CONDITION","DIFFERENCE","SCOPE","SOURCE","COMPOSITION"}

def lines():
    return [x.strip() for x in PNV.read_text().splitlines() if x.strip() and not x.lstrip().startswith("#")]

def test_pnv_directives_and_opcodes_are_native():
    for line in lines():
        parts=line.split()
        assert parts[0] in ALLOWED,line
        if parts[0]=="OP": assert parts[2] in OPS,line

def test_operator_ids_unique():
    ids=[x.split()[1] for x in lines() if x.startswith("OP ")]
    assert len(ids)==len(set(ids))

def test_release_paths_and_quarantine_present():
    text=PNV.read_text()
    for token in ["V1.SCOPE_FREEZE","V1.IDEA_QUARANTINE","PATH.V1.CLOSE_028","PATH.V1.HARDEN_029","PATH.V1.RC_030","PATH.V1.RELEASE","PATH.V1.NEW_IDEA","V1.POSTV1.ION1024"]:
        assert token in text
