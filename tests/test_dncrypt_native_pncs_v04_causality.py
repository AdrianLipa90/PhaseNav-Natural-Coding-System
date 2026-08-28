from pathlib import Path

ALLOWED_RELATIONS = {"IDENTITY","DIFFERENCE","COMPOSITION","TRANSFORM","CONDITION","RESOLVE","DERIVE","ORDER"}


def parse(path: Path):
    ops = {}
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s.startswith("OP "):
            continue
        parts = s.split()
        assert len(parts) >= 4, s
        name, relation = parts[1], parts[2]
        assert relation in ALLOWED_RELATIONS, (name, relation)
        assert name not in ops, name
        ops[name] = parts[3:]
    return ops


def test_dncrypt_v04_causality_path():
    root = Path(__file__).resolve().parents[1]
    p = root / "native" / "programs" / "DNCRYPT_NATIVE_PNCS_V0_4.pnv"
    ops = parse(p)
    required = {
        "DNC.FITNESS.DIAGNOSTIC",
        "DNC.CAUSALITY.REGISTRY",
        "DNC.CAUSALITY.FIREWALL",
        "DNC.FITNESS.ADMISSION",
        "DNC.EVALUATION.PAIRED_ENTROPY",
        "DNC.EVALUATION.PAIRED_BINDING",
        "DNC.GENERALIZATION.GATE",
        "DNC.HOLDOUT.FIREWALL",
        "DNC.PROMOTION.SELECT",
        "PATH.DNCRYPT.ADAPT",
        "PATH.DNCRYPT.RESIDENT",
    }
    assert required <= set(ops)
    adapt = ops["PATH.DNCRYPT.ADAPT"]
    for token in (
        "DNC.EVALUATION.PAIRED_ENTROPY",
        "DNC.EVALUATION.PAIRED_BINDING",
        "DNC.CAUSALITY.FIREWALL",
        "DNC.FITNESS.ADMISSION",
        "DNC.GENERALIZATION.GATE",
        "DNC.HOLDOUT.FIREWALL",
        "DNC.PROMOTION.SELECT",
    ):
        assert token in adapt
    text = p.read_text()
    assert 'VECTOR V.DNC.CAUSALITY "PNCS.DNCrypt.v0.4.fitness_causality" PRECISE' in text
    assert "EMIT PATH.DNCRYPT.RESIDENT" in text
