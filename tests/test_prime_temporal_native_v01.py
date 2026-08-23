from pathlib import Path

MODULE = Path(__file__).parents[1] / "native" / "experimental" / "PNCS_PRIME_TEMPORAL_HYDRO_V0_1.pnv"

ALLOWED = {"PNV", "EPISTEMIC", "MODE", "OP", "VECTOR", "EMIT"}
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
    return [
        x.strip()
        for x in MODULE.read_text(encoding="utf-8").splitlines()
        if x.strip() and not x.lstrip().startswith("#")
    ]


def test_experimental_native_directives_are_pnv1_only():
    assert MODULE.exists()
    for line in lines():
        assert line.split()[0] in ALLOWED, line


def test_experimental_native_opcodes_use_existing_vocabulary():
    for line in lines():
        parts = line.split()
        if parts[0] == "OP":
            assert len(parts) >= 3
            assert parts[2] in ALLOWED_OPS, line


def test_experimental_operator_ids_are_unique():
    ids = [line.split()[1] for line in lines() if line.startswith("OP ")]
    assert len(ids) == len(set(ids))


def test_prime_temporal_language_path_and_boundaries_are_present():
    text = MODULE.read_text(encoding="utf-8")
    for token in (
        "PTH.PRIME_VALUATION",
        "PTH.PRIME_FLUX",
        "PTH.ODD_PRIME_SCATTER",
        "PTH.SPECTRAL_LIFT",
        "PTH.TEMPORAL_FUZZINESS",
        "PTH.FS_TEMPORAL_SPEED",
        "PTH.CONTINUITY_ACCUMULATOR",
        "PTH.T36_TEMPORAL_PROJECTION",
        "PTH.TEMPORAL_HYDRO_OBSERVABLE",
        "PTH.HYDRO_LAPSE_BOUNDARY",
        "PTH.ROUTING_BOUNDARY",
        "PTH.EFFECT_BOUNDARY",
        "PTH.SEMANTIC_BOUNDARY",
        "PTH.LAB_TIME_BOUNDARY",
    ):
        assert token in text
    assert "EPISTEMIC CHYBA" in text
    assert "MODE READ_ONLY" in text
