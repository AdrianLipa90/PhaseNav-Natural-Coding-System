from pathlib import Path

SEED = Path(__file__).parents[1] / "native" / "PNCS_TIR_SOH_SEED_V0_2.pnv"

ALLOWED = {
    "PNV", "EPISTEMIC", "MODE", "OP", "VECTOR", "EMIT",
}
ALLOWED_OPS = {
    "IDENTITY", "DIFFERENCE", "ORDER", "COMPOSITION", "ADDITION", "FORCE",
    "NEGATION", "QUESTION", "TRANSFORM", "RETURN", "FOLD", "BOUNDARY", "SCOPE",
    "AFFECT", "CONSENT", "SOURCE", "MEMORY", "RISK", "ASSERTION", "CONDITION",
    "CAUSE", "MODAL_POSSIBILITY", "MODAL_NECESSITY", "MODAL_PERMISSION",
    "MODAL_OBLIGATION", "UNCERTAINTY", "SOURCE_REQUIRED", "CANON_BLOCK",
    "CONSENT_REQUIRED", "ACTION_REQUEST", "REFUSAL", "PAUSE", "SIMULATION_BOUNDARY",
    "UNRUH_DRIVE", "WARP_DRIFT", "ATTRACTOR", "SOFT_CLIP", "RESOLVE", "DERIVE",
}


def lines():
    return [x.strip() for x in SEED.read_text(encoding="utf-8").splitlines()
            if x.strip() and not x.lstrip().startswith("#")]


def test_native_directives_only():
    assert SEED.exists()
    for line in lines():
        assert line.split()[0] in ALLOWED, line


def test_opcodes_are_existing_pnv1_vocabulary():
    for line in lines():
        parts = line.split()
        if parts[0] == "OP":
            assert len(parts) >= 3
            assert parts[2] in ALLOWED_OPS, line


def test_unique_operator_ids():
    ids = [line.split()[1] for line in lines() if line.startswith("OP ")]
    assert len(ids) == len(set(ids))


def test_sources_and_cross_paths_present():
    text = SEED.read_text(encoding="utf-8")
    for token in [
        "TIR.BINARY_DISTINCTION",
        "TIR.KAPPA",
        "SOH.COMPLEMENT",
        "SOH.HALF",
        "SOH.OMEGA",
        "SOH.RECIPROCAL_INVERSION",
        "SOH.SELF_DUAL",
        "PATH.TIR.INFORMATION_TO_ACTION",
        "PATH.SOH.BOUNDARY_TO_SELF_DUAL",
        "PATH.PNCS.RELATION_TO_RESOLUTION",
    ]:
        assert token in text
