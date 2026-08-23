from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PNV = ROOT / "native/experimental/PNCS_FULL_PROGRAM_EXECUTOR_V0_1.pnv"
SPEC = ROOT / "spec/experimental/PNCS_FULL_PROGRAM_EXECUTOR_V0_1.md"


def test_native_headers_and_track():
    text = PNV.read_text("utf-8")
    assert text.startswith("PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\n")
    assert "POST_V1_LANGUAGE_ENGINEERING" in text


def test_native_uses_only_existing_kaku_families():
    text = PNV.read_text("utf-8")
    allowed = {"SOURCE", "ORDER", "TRANSFORM", "COMPOSITION", "RETURN", "CONDITION"}
    kinds = {line.split()[2] for line in text.splitlines() if line.startswith("OP ")}
    assert kinds <= allowed
    assert {"ORDER", "TRANSFORM", "COMPOSITION", "RETURN"} <= kinds


def test_native_continuation_exact_path():
    text = PNV.read_text("utf-8")
    assert "OP PATH.FPE.CONTINUATION COMPOSITION FPE.CONTINUATION_ORDER FPE.CONTINUATION_TRANSFORM FPE.CONTINUATION_COMPOSE" in text


def test_native_has_terminal_return_and_closed_future_layers():
    text = PNV.read_text("utf-8")
    assert "OP FPE.RETURN_VALUE RETURN" in text
    assert "external_effects equals FALSE" in text
    assert "static_runtime_fallback equals FALSE" in text
    assert "loops_opened equals FALSE" in text
    assert "function_calls_opened equals FALSE" in text


def test_native_emit_targets_defined():
    text = PNV.read_text("utf-8")
    paths = set(re.findall(r"^OP (PATH\.[A-Z0-9_.]+) COMPOSITION", text, re.MULTILINE))
    emitted = set(re.findall(r"^EMIT (PATH\.[A-Z0-9_.]+)$", text, re.MULTILINE))
    assert emitted <= paths
    assert emitted == {"PATH.FPE.PROGRAM"}


def test_spec_preserves_exact_current_scope():
    text = SPEC.read_text("utf-8")
    assert "complete **currently admitted bounded v0.23/v0.24 program grammar**" in text
    assert "39/39 PASS" in text
    assert "full repository integration replay" in text
    assert "No such PASS is inferred" in text


def test_spec_opens_continuation_and_return_only():
    text = SPEC.read_text("utf-8")
    assert "continuation_execution_opened = true" in text
    assert "return_execution_opened = true" in text
    assert "loops_opened = false" in text
    assert "function_calls_opened = false" in text
    assert "external_effects = false" in text
