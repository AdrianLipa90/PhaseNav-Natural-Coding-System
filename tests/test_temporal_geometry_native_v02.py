from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PNV = ROOT / "native/experimental/PNCS_TEMPORAL_GEOMETRY_V0_2.pnv"
SPEC = ROOT / "spec/experimental/PNCS_TEMPORAL_GEOMETRY_V0_2.md"


def test_native_contract_headers() -> None:
    text = PNV.read_text(encoding="utf-8")
    assert text.startswith("PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\n")
    assert "OP PATH.TG.CONFORMAL_TIME COMPOSITION" in text
    assert "OP PATH.TG.T36 COMPOSITION" in text
    assert "OP PATH.TG.OBSERVATION COMPOSITION" in text


def test_native_uses_existing_opcode_families() -> None:
    allowed = {"TRANSFORM", "CONDITION", "DERIVE", "COMPOSITION"}
    text = PNV.read_text(encoding="utf-8")
    op_lines = [line for line in text.splitlines() if line.startswith("OP ")]
    kinds = {line.split()[2] for line in op_lines}
    assert kinds <= allowed
    assert kinds == allowed


def test_native_contains_temporal_duality_and_now_projector() -> None:
    text = PNV.read_text(encoding="utf-8")
    required = [
        "TG.TIME_CENTER",
        "TG.TIME_IMAGINARY_LIFT",
        "TG.TIME_CAYLEY",
        "TG.PAST_FUTURE_DUAL",
        "TG.NOW_FIXED_POINT",
        "TG.T36_DUAL_PROJECT",
        "TG.OBSERVE_NOW",
        "TG.WAVE_CORPUSCLE_RECEIPT",
    ]
    for token in required:
        assert token in text


def test_native_keeps_experimental_scope_explicit() -> None:
    text = PNV.read_text(encoding="utf-8")
    assert "epistemic_status equals CHYBA" in text
    assert "promotion_track equals POST_V1_EXPERIMENTAL" in text
    assert "authority_scope equals PURE_MEASUREMENT_PROJECTION" in text


def test_spec_marks_interpretation_and_source_template() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "## 1. Source-derived conformal template" in text
    assert "## 2. INTERPRETACJA" in text
    assert r"z(1-s)=\frac{1}{z(s)}" in text
    assert r"\Re(s)=\frac12" in text
    assert r"z_T=-1" in text


def test_spec_uses_required_epistemic_qualifier() -> None:
    text = SPEC.read_text(encoding="utf-8")
    expected = "The formalism may suggest a wave–corpuscle temporal duality, yet does not state it as an established result."
    assert expected in text


def test_spec_has_exact_t36_and_observation_equations() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert r"k=1,\ldots,36" in text
    assert "18 non-negative offsets" in text
    assert r"P_{\mathrm{NOW}}" in text
    assert r"\sum_k |a_k|^2=1" in text


def test_native_emit_targets_are_defined() -> None:
    text = PNV.read_text(encoding="utf-8")
    paths = set(re.findall(r"^OP (PATH\.[A-Z0-9_.]+) COMPOSITION", text, flags=re.MULTILINE))
    emitted = set(re.findall(r"^EMIT (PATH\.[A-Z0-9_.]+)$", text, flags=re.MULTILINE))
    assert emitted == paths
