import hashlib
import json

from phasenav_natural_code.gremlin_native_pnv_bridge_v01 import (
    compare_triple_pulse_harness,
    execute_belzebub,
    execute_gremlin_triple_pulse,
)

TRIPLE_PULSE = '''PNV 1
EPISTEMIC CHYBA
MODE INTERNAL_EXECUTION
OP TP.IDENTITY.SOURCE SOURCE current.identity
OP TP.IDENTITY.VERIFY IDENTITY verified_identity
OP TP.DOMAIN.SOURCE SOURCE current.domain
OP TP.DOMAIN.VERIFY IDENTITY verified_domain
OP TP.DOMAIN.ORDER ORDER TP.IDENTITY.VERIFY TP.DOMAIN.VERIFY
OP TP.AUTHORITY.SOURCE SOURCE current.authority
OP TP.AUTHORITY.VERIFY IDENTITY verified_authority
OP TP.AUTHORITY.ORDER ORDER TP.DOMAIN.ORDER TP.AUTHORITY.VERIFY
OP TP.REQUEST.SOURCE SOURCE user.request
OP TP.REQUEST.TRANSFORM TRANSFORM TP.REQUEST.SOURCE admitted_request_candidate
OP TP.COUPLING.TRANSFORM TRANSFORM TP.AUTHORITY.ORDER current_live_coupling
OP TP.COUPLING.COMPOSE COMPOSITION TP.REQUEST.TRANSFORM TP.COUPLING.TRANSFORM
OP TP.ADMISSION.CONDITION CONDITION TP.COUPLING.COMPOSE three_pulse_receipts_same_generation
OP TP.ADMISSION.RETURN RETURN TP.ADMISSION.CONDITION
ASSERT TP.IDENTITY.VERIFY
ASSERT TP.DOMAIN.VERIFY
ASSERT TP.AUTHORITY.VERIFY
ASSERT TP.ADMISSION.CONDITION
EMIT TP.ADMISSION.RETURN
'''

BELZEBUB = '''PNV 1
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


def test_triple_pulse_native_matches_legacy_semantic_projection():
    generation = 'a' * 64
    domain = {'surface': '/dev/shm/ciel_noema', 'tether_pid': 7}
    run = execute_gremlin_triple_pulse(
        TRIPLE_PULSE,
        identity='ZOSIA_NOEMA_FIRST',
        authority='USER_EXPLICIT_TEST',
        domain=domain,
        request='RAISE_GREMLIN',
        generation_binding=generation,
        live_payload={'root': '/dev/shm/ciel_noema', 'tether_receipt_sha256': 'b' * 64},
    )
    harness = {
        'pulses': [
            {'pulse': 'IDENTITY', 'status': 'PASS', 'generation_binding': generation, 'value': 'ZOSIA_NOEMA_FIRST'},
            {'pulse': 'DOMAIN', 'status': 'PASS', 'generation_binding': generation, 'value': domain},
            {'pulse': 'AUTHORITY', 'status': 'PASS', 'generation_binding': generation, 'value': 'USER_EXPLICIT_TEST'},
        ],
        'request': 'RAISE_GREMLIN',
        'generation_binding': generation,
        'admission': 'PASS_CONFORMANCE_ONLY',
    }
    comparison = compare_triple_pulse_harness(run, harness)
    assert run.result.emitted['TP.ADMISSION.RETURN'] is True
    assert comparison['exact_projection_match'] is True
    assert comparison['comparison_mode'] == 'EXACT_CANONICAL_SEMANTIC_PROJECTION'
    assert comparison['receipt_bytes_equal'] is False


def test_triple_pulse_generation_mismatch_is_not_hidden():
    generation = 'a' * 64
    run = execute_gremlin_triple_pulse(
        TRIPLE_PULSE,
        identity='I', authority='A', domain={'surface': '/dev/shm/ciel_noema'}, request='R',
        generation_binding=generation, live_payload={'root': '/dev/shm/ciel_noema'},
    )
    harness = {
        'pulses': [
            {'value': 'I'}, {'value': {'surface': '/dev/shm/ciel_noema'}}, {'value': 'A'}
        ],
        'request': 'R', 'generation_binding': 'c' * 64, 'admission': 'PASS_CONFORMANCE_ONLY'
    }
    assert compare_triple_pulse_harness(run, harness)['exact_projection_match'] is False


def test_belzebub_native_executes_content_addressed_quarantine():
    quarantine = {'object_sha256': '1' * 64, 'candidate': {'x': 2}}
    current = {'object_sha256': '1' * 64, 'epoch': 1}
    baseline = {'candidate': {'x': 1}}

    def digest(delta):
        raw = json.dumps(delta, sort_keys=True, separators=(',', ':')).encode()
        return {'semantic_digest_sha256': hashlib.sha256(raw).hexdigest()}

    run = execute_belzebub(
        BELZEBUB,
        current=current,
        quarantine=quarantine,
        baseline=baseline,
        live_payload={'root': '/dev/shm/ciel_noema'},
        defensive_semantic_digest=digest,
    )
    assert run.result.values['BELZEBUB.QUARANTINE.IDENTITY'] is True
    assert run.result.values['BELZEBUB.VIOLATION'] is True
    assert run.result.emitted['BELZEBUB.IMMUNITY.RETURN']
    assert run.result.receipt['effect_boundary']['external_effects'] is False
