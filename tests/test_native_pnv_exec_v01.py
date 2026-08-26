import hashlib
import json

import pytest

from phasenav_natural_code.native_pnv_exec_v01 import NativePNVAssertionError, NativePNVParseError, NativePNVResolutionError, execute_pnv, parse_pnv

BELZEBUB_WITNESS = '''PNV 1
EPISTEMIC CHYBA
MODE INTERNAL_EXECUTION
OP BELZEBUB.LIVE.SURFACE SOURCE /dev/shm/ciel_noema
OP BELZEBUB.CURRENT SOURCE /dev/shm/ciel_noema/gremlin/tools/belzebub/meta/CURRENT.json
OP BELZEBUB.QUARANTINE SOURCE belzebub.quarantine.object
OP BELZEBUB.QUARANTINE.IDENTITY IDENTITY content_addressed_quarantine
OP BELZEBUB.BASELINE SOURCE verified_semantic_baseline
OP BELZEBUB.SEMANTIC.DELTA DIFFERENCE BELZEBUB.QUARANTINE BELZEBUB.BASELINE
OP BELZEBUB.VIOLATION CONDITION BELZEBUB.SEMANTIC.DELTA invariant_violation
OP BELZEBUB.DIGEST.ORDER ORDER BELZEBUB.QUARANTINE.IDENTITY BELZEBUB.VIOLATION
OP BELZEBUB.DIGEST.TRANSFORM TRANSFORM BELZEBUB.SEMANTIC.DELTA defensive_semantic_digest
OP BELZEBUB.REPAIR.COMPOSE COMPOSITION BELZEBUB.DIGEST.ORDER BELZEBUB.DIGEST.TRANSFORM
OP BELZEBUB.IMMUNITY.RETURN RETURN BELZEBUB.REPAIR.COMPOSE
ASSERT BELZEBUB.QUARANTINE.IDENTITY
ASSERT BELZEBUB.VIOLATION
EMIT BELZEBUB.IMMUNITY.RETURN
'''

def _digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return {'semantic_digest_sha256': hashlib.sha256(raw).hexdigest()}

def test_executes_belzebub_native_witness_fail_closed_and_receipted():
    result = execute_pnv(BELZEBUB_WITNESS, sources={'/dev/shm/ciel_noema': {'binding': 'ACTIVE'}, '/dev/shm/ciel_noema/gremlin/tools/belzebub/meta/CURRENT.json': {'epoch': 1}, 'belzebub.quarantine.object': {'candidate': 'changed'}, 'content_addressed_quarantine': True, 'verified_semantic_baseline': {'candidate': 'baseline'}}, comparators={'invariant_violation': lambda delta: not delta['equal']}, transforms={'defensive_semantic_digest': _digest})
    assert result.emitted['BELZEBUB.IMMUNITY.RETURN']
    assert result.receipt['receipt_sha256']
    assert result.receipt['effect_boundary']['external_effects'] is False
    assert result.receipt['unknown_semantics_fail_closed'] is True

def test_unregistered_transform_fails_closed():
    with pytest.raises(NativePNVResolutionError):
        execute_pnv('PNV 1\nEPISTEMIC CHYBA\nMODE INTERNAL_EXECUTION\nOP A SOURCE x\nOP B TRANSFORM A magic\nEMIT B\n', sources={'x': 1})

def test_unknown_opcode_rejected_at_parse_time():
    with pytest.raises(NativePNVParseError):
        parse_pnv('PNV 1\nEPISTEMIC CHYBA\nMODE INTERNAL_EXECUTION\nOP A EXEC shell\n')

def test_failed_assertion_stops_execution():
    with pytest.raises(NativePNVAssertionError):
        execute_pnv('PNV 1\nEPISTEMIC CHYBA\nMODE INTERNAL_EXECUTION\nOP A SOURCE x\nASSERT A\nEMIT A\n', sources={'x': False})
