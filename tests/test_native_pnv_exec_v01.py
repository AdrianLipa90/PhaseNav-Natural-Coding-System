import hashlib
import json

import pytest

from phasenav_natural_code.native_pnv_exec_v01 import (
    NativePNVAssertionError,
    NativePNVExecutor,
    NativePNVParseError,
    NativePNVResolutionError,
    PNVOp,
    PNVProgram,
    execute_pnv,
    parse_pnv,
)

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


def test_executes_belzebub_native_witness_and_marks_callback_effect_boundary_unverified():
    result = execute_pnv(
        BELZEBUB_WITNESS,
        sources={
            '/dev/shm/ciel_noema': {'binding': 'ACTIVE'},
            '/dev/shm/ciel_noema/gremlin/tools/belzebub/meta/CURRENT.json': {'epoch': 1},
            'belzebub.quarantine.object': {'candidate': 'changed'},
            'content_addressed_quarantine': True,
            'verified_semantic_baseline': {'candidate': 'baseline'},
        },
        comparators={'invariant_violation': lambda delta: not delta['equal']},
        transforms={'defensive_semantic_digest': _digest},
    )
    assert result.emitted['BELZEBUB.IMMUNITY.RETURN']
    assert result.receipt['receipt_sha256']
    boundary = result.receipt['effect_boundary']
    assert boundary['interpreter_external_effects'] is False
    assert boundary['external_effects'] is None
    assert boundary['external_effects_status'] == 'UNVERIFIED_CALLBACK_BOUNDARY'
    assert boundary['callback_effects_verified'] is False
    assert boundary['callbacks_invoked'] == [
        'comparator:invariant_violation',
        'transform:defensive_semantic_digest',
    ]
    assert result.receipt['unknown_semantics_fail_closed'] is True


def test_callback_free_execution_has_verified_zero_effect_boundary():
    result = execute_pnv(
        'PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\nOP A SOURCE x\nOP B RETURN A\nEMIT B\n',
        sources={'x': {'value': 1}},
    )
    boundary = result.receipt['effect_boundary']
    assert boundary['external_effects'] is False
    assert boundary['external_effects_status'] == 'VERIFIED_NONE_WITHIN_INTERPRETER_BOUNDARY'
    assert boundary['callbacks_invoked'] == []
    assert boundary['callback_effects_verified'] is True


def test_unregistered_transform_fails_closed():
    with pytest.raises(NativePNVResolutionError):
        execute_pnv(
            'PNV 1\nEPISTEMIC CHYBA\nMODE INTERNAL_EXECUTION\nOP A SOURCE x\nOP B TRANSFORM A magic\nEMIT B\n',
            sources={'x': 1},
        )


def test_unknown_opcode_rejected_at_parse_time():
    with pytest.raises(NativePNVParseError):
        parse_pnv('PNV 1\nEPISTEMIC CHYBA\nMODE INTERNAL_EXECUTION\nOP A EXEC shell\n')


@pytest.mark.parametrize(
    'header',
    [
        'EPISTEMIC CANON\nMODE INTERNAL_EXECUTION',
        'EPISTEMIC CHYBA\nMODE SHELL',
    ],
)
def test_unsupported_execution_headers_fail_closed(header):
    with pytest.raises(NativePNVParseError, match='unsupported'):
        parse_pnv(f'PNV 1\n{header}\nOP A SOURCE x\nEMIT A\n')


def test_failed_assertion_stops_execution():
    with pytest.raises(NativePNVAssertionError):
        execute_pnv(
            'PNV 1\nEPISTEMIC CHYBA\nMODE INTERNAL_EXECUTION\nOP A SOURCE x\nASSERT A\nEMIT A\n',
            sources={'x': False},
        )


def test_numeric_difference_overflow_fails_closed():
    program = (
        'PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\n'
        'OP A SOURCE left\nOP B SOURCE right\nOP D DIFFERENCE A B\nEMIT D\n'
    )
    with pytest.raises(NativePNVResolutionError, match='numeric difference must be finite'):
        execute_pnv(program, sources={'left': 1.0e308, 'right': -1.0e308})


def test_huge_numeric_literal_fails_as_unresolved_not_raw_overflow():
    huge = '9' * 5000
    with pytest.raises(NativePNVResolutionError, match='unresolved PNV token'):
        execute_pnv(
            f'PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\nOP A SOURCE {huge}\nEMIT A\n'
        )


def test_noncanonical_source_and_callback_results_fail_closed():
    with pytest.raises(NativePNVResolutionError, match='source'):
        execute_pnv(
            'PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\nOP A SOURCE x\nEMIT A\n',
            sources={'x': float('nan')},
        )
    with pytest.raises(NativePNVResolutionError, match='result'):
        execute_pnv(
            'PNV 1\nEPISTEMIC CHYBA\nMODE INTERNAL_EXECUTION\nOP A SOURCE x\nOP B TRANSFORM A bad\nEMIT B\n',
            sources={'x': 1},
            transforms={'bad': lambda _: object()},
        )


def test_runtime_values_use_one_canonical_json_domain():
    result = execute_pnv(
        'PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\n'
        'OP A SOURCE left\nOP B SOURCE right\nOP C IDENTITY A B\nEMIT C\n',
        sources={'left': (1, 2), 'right': [1, 2]},
    )
    assert result.emitted['C'] is True
    with pytest.raises(NativePNVResolutionError, match='non-string JSON object key'):
        execute_pnv(
            'PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\nOP A SOURCE x\nEMIT A\n',
            sources={'x': {1: 'ambiguous'}},
        )


def test_reserved_literals_cannot_be_shadowed_by_operation_names():
    with pytest.raises(NativePNVParseError, match='reserved literal'):
        parse_pnv(
            'PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\nOP TRUE SOURCE x\nEMIT TRUE\n'
        )


def test_public_program_must_match_exact_source_graph():
    text = 'PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\nOP A SOURCE x\nEMIT A\n'
    parsed = parse_pnv(text)
    forged = PNVProgram(
        version=parsed.version,
        epistemic=parsed.epistemic,
        mode=parsed.mode,
        ops=(PNVOp('B', 'SOURCE', ('x',), 4),),
        assertions=(),
        emits=('B',),
        metadata=parsed.metadata,
        source_text=text,
    )
    with pytest.raises(NativePNVParseError, match='does not match exact source_text'):
        NativePNVExecutor(sources={'x': 1}).execute(forged)


def test_duplicate_emit_is_rejected_as_noncanonical_graph():
    with pytest.raises(NativePNVParseError, match='EMIT references must be unique'):
        parse_pnv(
            'PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\nOP A SOURCE x\nEMIT A\nEMIT A\n'
        )
