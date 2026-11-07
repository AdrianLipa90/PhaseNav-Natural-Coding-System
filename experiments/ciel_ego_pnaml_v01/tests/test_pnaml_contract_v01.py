import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class PNAMLCompatibilityTests(unittest.TestCase):
    def test_existing_pnv_opcodes_and_readonly(self):
        text=(ROOT/'native/PNAML11_CIEL_EGO_MEMORY_READ_ONLY_V0_1.pnv').read_text()
        lines=[s.strip() for s in text.splitlines() if s.strip() and not s.startswith('#')]
        self.assertEqual(['PNV 1','EPISTEMIC CHYBA','MODE READ_ONLY'],lines[:3])
        allowed={'SOURCE','IDENTITY','ORDER','COMPOSITION'}
        for ln in lines[3:]:
            if ln.startswith('OP '):
                self.assertIn(ln.split()[2],allowed)
            else:
                self.assertIn(ln.split()[0],('ASSERT','EMIT'))
    def test_contract_has_no_runtime_side_effects(self):
        text=(ROOT/'native/PNAML11_CIEL_EGO_MEMORY_READ_ONLY_V0_1.pnv').read_text()
        self.assertIn('M8_PROTECTED',text)
        self.assertIn('FINGERPRINT_IS_DERIVED_OBSERVATION_NOT_FULL_MEMORY',text)
        self.assertIn('NATIVE_SYMBOL_REGISTRATION_NOT_VERIFIED',text)
        self.assertIn('MODE READ_ONLY',text)
if __name__=='__main__':unittest.main()
