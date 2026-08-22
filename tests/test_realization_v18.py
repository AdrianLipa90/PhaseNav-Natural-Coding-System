from pathlib import Path
import hashlib
import json
import math
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phasenav_natural_code.definitions_v11 import predicate_content
from phasenav_natural_code.classes_v12 import define_class, ClassRegistry
from phasenav_natural_code.realization_v18 import (
    DIM,
    TAU,
    PhaseVector36,
    RealizationBinding,
    RealizationRegistry,
    RealizationV18Error,
    verify_serialized_binding,
)

PNV = ROOT / "native" / "PNCS_EXACT_36D_BINDING_V0_18.pnv"
LEDGER = ROOT / "mining" / "PNCS_EXACT_36D_BINDING_LEDGER_V0_18.json"

ALLOWED = {
    "IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION","QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT","SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY","MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY","SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL","PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR","SOFT_CLIP","RESOLVE","DERIVE"
}

BASIS = "PNV_T36_PHASE_ANGLES_RADIANS_V1"
DERIVATION = "EXTERNAL_EVIDENCE_BINDING_V1"
SOURCE_DIGEST = hashlib.sha256(b"phase-evidence-fixture-v18").hexdigest()


def phase(offset: float = 0.0) -> PhaseVector36:
    return PhaseVector36(tuple(((i * 0.137) + offset) % TAU for i in range(DIM)))


def cid(surface: str = "risk ABOVE 0.8") -> str:
    return predicate_content(surface).content_id


def binding(
    content_id: str | None = None,
    *,
    vector: PhaseVector36 | None = None,
    source_digest: str = SOURCE_DIGEST,
    source_locator: str = "library://NOEMA/evidence/phase36_fixture",
    basis_id: str = BASIS,
    derivation_id: str = DERIVATION,
) -> RealizationBinding:
    return RealizationBinding(
        content_id=content_id or cid(),
        phase=vector or phase(),
        basis_id=basis_id,
        derivation_id=derivation_id,
        source_digest_sha256=source_digest,
        source_locator=source_locator,
    )


def fail(fn):
    try:
        fn()
    except RealizationV18Error:
        return
    raise AssertionError("expected RealizationV18Error")


def test_phase_vector_is_exactly_36():
    assert len(phase().angles) == 36


def test_35d_and_37d_fail_closed():
    fail(lambda: PhaseVector36([0.0] * 35))
    fail(lambda: PhaseVector36([0.0] * 37))


def test_nonfinite_phase_fails_closed():
    for bad in [float("nan"), float("inf"), float("-inf")]:
        vals = [0.0] * 36
        vals[3] = bad
        fail(lambda vals=vals: PhaseVector36(vals))


def test_phase_range_is_half_open_zero_to_tau():
    PhaseVector36([0.0] * 36)
    vals = [0.0] * 36
    vals[0] = -1e-12
    fail(lambda: PhaseVector36(vals))
    vals = [0.0] * 36
    vals[0] = TAU
    fail(lambda: PhaseVector36(vals))


def test_phase_digest_is_compact_json_sha256():
    p = phase()
    expected = hashlib.sha256(
        json.dumps(list(p.angles), separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()
    assert p.phase_sha256 == expected


def test_phase_contract_labels_are_exact():
    p = phase()
    assert p.space == "T^36"
    assert p.coordinate_semantics == "phase_angles_radians"
    assert p.coordinate_range == "[0,2π)"


def test_binding_requires_typed_content_id():
    fail(lambda: binding("risk"))
    fail(lambda: binding("pncs:def:sha256:" + "g" * 64))


def test_binding_accepts_definition_content_id():
    b = binding()
    assert b.content_id.startswith("pncs:def:sha256:")


def test_binding_accepts_higher_typed_content_ids():
    for prefix in [
        "pncs:class:sha256:",
        "pncs:file:sha256:",
        "pncs:cluster:sha256:",
        "pncs:subsystem:sha256:",
        "pncs:daemon:sha256:",
        "pncs:low-orchestrator:sha256:",
        "pncs:high-orchestrator:sha256:",
        "pncs:system:sha256:",
    ]:
        b = binding(prefix + "a" * 64)
        assert b.content_id == prefix + "a" * 64


def test_binding_requires_basis_derivation_source_digest_and_locator():
    fail(lambda: binding(basis_id="bad space"))
    fail(lambda: binding(derivation_id=""))
    fail(lambda: binding(source_digest="x" * 64))
    fail(lambda: binding(source_locator="   "))


def test_binding_remains_chyba_and_cannot_self_canonize():
    fail(lambda: RealizationBinding(cid(), phase(), BASIS, DERIVATION, SOURCE_DIGEST, "x", "VERIFIED", False))
    fail(lambda: RealizationBinding(cid(), phase(), BASIS, DERIVATION, SOURCE_DIGEST, "x", "CHYBA", True))


def test_realization_id_is_deterministic():
    a = binding()
    b = binding()
    assert a.realization_id == b.realization_id
    assert a.binding_id == b.binding_id


def test_source_provenance_changes_binding_id_not_realization_id():
    a = binding(source_locator="library://a")
    b = binding(source_locator="library://b")
    assert a.realization_id == b.realization_id
    assert a.binding_id != b.binding_id


def test_different_phase_changes_realization_id():
    assert binding(vector=phase(0.0)).realization_id != binding(vector=phase(1e-6)).realization_id


def test_same_content_same_contract_exact_phase_is_idempotent():
    r = RealizationRegistry()
    a = r.bind(binding())
    b = r.bind(binding())
    assert a.binding_id == b.binding_id
    assert len(r.bindings_for(a.content_id)) == 1


def test_same_content_same_contract_conflicting_phase_fails_closed():
    r = RealizationRegistry()
    r.bind(binding(vector=phase(0.0)))
    fail(lambda: r.bind(binding(vector=phase(0.01))))


def test_same_content_exact_phase_can_preserve_multiple_provenance_records():
    r = RealizationRegistry()
    a = r.bind(binding(source_locator="library://source-a"))
    b = r.bind(binding(source_locator="library://source-b"))
    assert a.realization_id == b.realization_id
    assert a.binding_id != b.binding_id
    assert len(r.bindings_for(a.content_id)) == 2


def test_same_phase_different_semantic_content_ids_do_not_merge():
    a_id = cid("risk ABOVE 0.8")
    b_id = cid("temperature ABOVE 80")
    p = phase()
    r = RealizationRegistry()
    a = r.bind(binding(a_id, vector=p, source_locator="library://a"))
    b = r.bind(binding(b_id, vector=p, source_locator="library://b"))
    assert a.content_id != b.content_id
    assert r.same_exact_realization(a.binding_id, b.binding_id) is True
    assert r.semantic_ids_for_exact_phase(p) == tuple(sorted([a_id, b_id]))


def test_near_phase_different_semantic_content_ids_do_not_merge():
    a_id = cid("risk ABOVE 0.8")
    b_id = cid("temperature ABOVE 80")
    r = RealizationRegistry()
    a = r.bind(binding(a_id, vector=phase(0.0), source_locator="library://a"))
    b = r.bind(binding(b_id, vector=phase(1e-12), source_locator="library://b"))
    assert a.content_id != b.content_id
    assert a.realization_id != b.realization_id
    assert r.semantic_ids_for_exact_phase(phase(0.0)) == (a_id,)


def test_vector_semantic_equivalence_api_fails_by_design():
    r = RealizationRegistry()
    fail(lambda: r.semantic_equivalent(binding(), binding()))


def test_registry_lookup_requires_exact_binding_id():
    r = RealizationRegistry()
    b = r.bind(binding())
    assert r.binding(b.binding_id) == b
    fail(lambda: r.binding("pncs:binding36:sha256:" + "0" * 64))


def test_registry_filter_by_basis_and_derivation():
    r = RealizationRegistry()
    b = r.bind(binding())
    assert r.bindings_for(b.content_id, basis_id=BASIS, derivation_id=DERIVATION) == (b,)
    assert r.bindings_for(b.content_id, basis_id="OTHER_BASIS") == ()


def test_serialized_binding_roundtrip_verifies_exactly():
    b = binding()
    recovered = verify_serialized_binding(b.record_payload, phase36=b.phase.angles)
    assert recovered.binding_id == b.binding_id
    assert recovered.realization_id == b.realization_id


def test_serialized_phase_tamper_is_detected():
    b = binding()
    vals = list(b.phase.angles)
    vals[0] += 0.01
    fail(lambda: verify_serialized_binding(b.record_payload, phase36=vals))


def test_serialized_metadata_tamper_is_detected():
    b = binding()
    payload = dict(b.record_payload)
    payload["source_locator"] = "library://tampered"
    fail(lambda: verify_serialized_binding(payload, phase36=b.phase.angles))


def test_serialized_key_addition_fails_closed():
    b = binding()
    payload = dict(b.record_payload)
    payload["extra"] = True
    fail(lambda: verify_serialized_binding(payload, phase36=b.phase.angles))


def test_registry_receipt_is_insertion_order_deterministic():
    a = binding(cid("risk ABOVE 0.8"), source_locator="library://a")
    b = binding(cid("temperature ABOVE 80"), vector=phase(0.2), source_locator="library://b")
    r1, r2 = RealizationRegistry(), RealizationRegistry()
    r1.bind(a); r1.bind(b)
    r2.bind(b); r2.bind(a)
    assert r1.deterministic_receipt() == r2.deterministic_receipt()


def test_registry_receipt_explicitly_blocks_vector_semantic_authority():
    r = RealizationRegistry()
    r.bind(binding())
    assert r.deterministic_receipt()["semantic_equivalence_from_vectors"] is False


def test_no_11d_truncation_literal_in_v18_module():
    source = (ROOT / "src" / "phasenav_natural_code" / "realization_v18.py").read_text(encoding="utf-8")
    assert "[:11]" not in source
    assert "v36[:11]" not in source


def test_no_broad_exception_handler_in_v18_module():
    source = (ROOT / "src" / "phasenav_natural_code" / "realization_v18.py").read_text(encoding="utf-8")
    assert "except Exception" not in source


def test_native_binding_witness_uses_only_recovered_opcodes():
    ops = []
    for raw in PNV.read_text(encoding="utf-8").splitlines():
        parts = raw.strip().split()
        if parts[:1] == ["OP"]:
            ops.append(parts[2])
    assert ops
    assert set(ops) <= ALLOWED


def test_native_binding_does_not_claim_vector_generator_replay():
    text = PNV.read_text(encoding="utf-8")
    opcodes = []
    for raw in text.splitlines():
        parts = raw.strip().split()
        if parts[:1] == ["OP"]:
            opcodes.append(parts[2])
    assert "VECTOR" not in opcodes
    assert "HISTORICAL_GENERATOR_REPLAY NOT_CLAIMED" in text
    assert "SIMILARITY_SEMANTIC_AUTHORITY FALSE" in text


def test_ledger_records_generator_gap_and_exact_binding_scope():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["generator_status"] == "DEFERRED_SOURCE_BYTES"
    assert data["historical_native_runtime_replay"] == "NOT_CLAIMED"
    assert data["semantic_equivalence_from_vector_similarity"] is False
    assert data["phase_dimension"] == 36
    assert data["space"] == "T^36"


def test_generic_natural_language_compiler_stays_disabled():
    from phasenav_natural_code.compiler import BasisNotCanonizedError, compile_natural_language
    try:
        compile_natural_language("risk above 0.8")
    except BasisNotCanonizedError:
        pass
    else:
        raise AssertionError("generic NL compiler unexpectedly enabled")
