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


@pytest.mark.parametrize("n", [0, 1, 2**53 - 2, 2**53 - 1, 2**53, 2**53 + 1, 2**63, 10**100, 10**400])
def test_pip_integer_winding_preserves_identity_and_half_time(n):
    # Same integer relations used by Pip's PNV/1 serial step.
    program = (
        "PNV 1\nEPISTEMIC CHYBA\nMODE INTERNAL_EXECUTION\n"
        "OP WINDING_BEFORE SOURCE now.winding\n"
        "OP SIGN_BEFORE SOURCE now.spinor_i_sign\n"
        "OP WINDING DIFFERENCE WINDING_BEFORE -1\n"
        "OP SIGN DIFFERENCE 0 SIGN_BEFORE\n"
        "OP NEG_WINDING DIFFERENCE 0 WINDING\n"
        "OP THETA DIFFERENCE WINDING NEG_WINDING\n"
        "OP INDEX IDENTITY WINDING\n"
        "EMIT WINDING\nEMIT SIGN\nEMIT THETA\nEMIT INDEX\n"
    )
    sign = (-1)**(n % 2)
    indices = []
    receipts = []
    for _ in range(3):
        result = execute_pnv(program, sources={
            "now.winding": n, "now.spinor_i_sign": sign,
        })
        n += 1
        sign = -sign
        assert result.emitted == {
            "WINDING": n, "SIGN": sign, "THETA": 2*n, "INDEX": n,
        }
        assert all(type(v) is int for v in result.emitted.values())
        indices.append(result.emitted["INDEX"])
        receipts.append(result.receipt["receipt_sha256"])
    assert len(set(indices)) == len(set(receipts)) == 3


def test_exact_large_integer_literal_and_difference():
    n = 10**400 + 1
    program = (
        f"PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\n"
        f"OP A SOURCE {n}\nOP D DIFFERENCE A -1\nEMIT D\n"
    )
    result = execute_pnv(program)
    assert type(result.emitted["D"]) is int
    assert result.emitted["D"] == n + 1


def test_mixed_numeric_difference_keeps_float_semantics():
    program = (
        "PNV 1\nEPISTEMIC CHYBA\nMODE READ_ONLY\n"
        "OP A SOURCE left\nOP B SOURCE right\n"
        "OP D DIFFERENCE A B\nEMIT D\n"
    )
    result = execute_pnv(program, sources={"left": 3, "right": 0.5})
    assert type(result.emitted["D"]) is float
    assert result.emitted["D"] == 2.5
    with pytest.raises(NativePNVResolutionError, match="numeric difference must be finite"):
        execute_pnv(program, sources={"left": 10**400, "right": 0.5})


# PNAML 1.0 source integration: existing PNCS generator, existing PNV executor.
# These immutable input fixtures do not represent a live AUX or a socket exchange.
from pathlib import Path as _Path
from phasenav_natural_code.semantic_address_v31 import (
    generate_semantic_address as _generate_semantic_address,
    GENERATOR_ID as _PNAML_ADDRESS_GENERATOR_ID,
)

_PNAML_ROUTER = (_Path(__file__).resolve().parents[1] / "native"
                 / "PNAML10_PNCS_MACHINE_SEMANTIC_ROUTER.pnv")
_PNAML_BEFORE = "pncs:semantic-role:sha256:" + "1" * 64
_PNAML_AFTER = "pncs:semantic-role:sha256:" + "2" * 64


def _pnaml_test_sources(before, after, n):
    return {
        "typed_semantic_role_content": before,
        "semantic_role_before": before,
        "semantic_role_after": after,
        "rdss_exact_typed_relational_occurrence": {
            "index": n, "parent": n - 1, "content_id": after},
        "rdss_ordered_braid_word_and_sector": [n - 1, n],
    }


def _pnaml_address_callback(content_id):
    # Adapt only the existing dataclass's payload to the PNV1 value domain.
    # No additional address algorithm or runtime transport.
    return _generate_semantic_address(content_id).payload


def test_pnaml10_router_has_existing_transform_arity():
    p = parse_pnv(_PNAML_ROUTER.read_text())
    assert all(len(op.args) == 2 for op in p.ops if op.opcode == "TRANSFORM")
    assert [op.opcode for op in p.ops if op.name.startswith("PNAML10.PNCS.ADDRESS")] == [
        "TRANSFORM", "TRANSFORM", "COMPOSITION"]


@pytest.mark.parametrize("before,after", [
    (_PNAML_BEFORE, _PNAML_AFTER),
    (_PNAML_AFTER, _PNAML_BEFORE),
    (_PNAML_BEFORE, _PNAML_BEFORE),
])
@pytest.mark.parametrize("n", [1, 2**53+1, 2**63+1, 10**100])
def test_pnaml10_real_generator_and_exact_occurrence_prefix(before, after, n):
    # Execute the exact PNCS/RDSS prefix of the source; no simulated QHTRI callback.
    text = _PNAML_ROUTER.read_text().split("OP PNAML10.QHTRI.SOURCE ", 1)[0]
    text += "EMIT PNAML10.PNCS.BIND\nEMIT PNAML10.RDSS.COMPOSE\n"
    r = execute_pnv(text, sources=_pnaml_test_sources(before, after, n),
                    transforms={_PNAML_ADDRESS_GENERATOR_ID: _pnaml_address_callback})
    pair = r.emitted["PNAML10.PNCS.BIND"]
    assert pair[0] == [before, after]
    assert pair[1] == [_generate_semantic_address(before).payload,
                       _generate_semantic_address(after).payload]
    assert len(pair[1][0]["phase36"]) == len(pair[1][1]["phase36"]) == 36
    occurrence, braid = r.emitted["PNAML10.RDSS.COMPOSE"]
    assert occurrence == {"index": n, "parent": n-1, "content_id": after}
    assert type(occurrence["index"]) is int
    assert braid == [n-1,n]
    if before == after:
        assert pair[1][0] == pair[1][1]
        assert occurrence["index"] != occurrence["parent"]


def test_pnaml10_missing_drive_is_not_substituted():
    src = _pnaml_test_sources(_PNAML_BEFORE, _PNAML_AFTER, 1)
    # Explicit immutable fixture, not a producer or a QHTRI drive.
    src["typed_semantic_t36_trajectory"] = [_generate_semantic_address(_PNAML_BEFORE).payload,
                                            _generate_semantic_address(_PNAML_AFTER).payload]
    with pytest.raises(NativePNVResolutionError, match="exact_one_step_inverse_dynamics_control"):
        execute_pnv(_PNAML_ROUTER.read_text(), sources=src,
                    transforms={_PNAML_ADDRESS_GENERATOR_ID: _pnaml_address_callback})
