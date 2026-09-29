from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "PNCS_QUANTUM_APPLICATION_RUNTIME_V0_31.md"
PNV = ROOT / "native" / "PNCS_QUANTUM_APPLICATION_RUNTIME_V0_31.pnv"
ALLOWED = {"IDENTITY", "DIFFERENCE", "CONDITION", "NEGATION", "COMPOSITION", "ORDER", "TRANSFORM", "RETURN", "SOURCE"}


def test_quantum_application_contract_preserves_state_until_measurement() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    native = PNV.read_text(encoding="utf-8")
    assert "NEVER COLLAPSE EARLY" in spec
    assert "NEVER_COLLAPSE_EARLY TRUE" in native
    assert "BOOLEAN_INTERNAL_ONTOLOGY FALSE" in native
    assert "BOOLEAN_BOUNDARY_PROJECTION TRUE" in native
    assert "REMOTE_RUNTIME REQUIRED_FALSE" in native
    assert "QPU_PHYSICAL" in native


def test_quantum_application_contract_introduces_no_new_pnv_opcode() -> None:
    native = PNV.read_text(encoding="utf-8")
    opcodes = {
        match.group(1)
        for match in re.finditer(r"^OP\s+\S+\s+(\S+)", native, flags=re.MULTILINE)
    }
    assert opcodes <= ALLOWED
