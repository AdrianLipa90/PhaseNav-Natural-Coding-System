from pathlib import Path
import hashlib
import json
import math
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phasenav_natural_code.definitions_v11 import predicate_content
from phasenav_natural_code.model import Vector36
from phasenav_natural_code.realization_v18 import PhaseVector36, RealizationBinding
from phasenav_natural_code.mass_v19 import (
    ALPHA_M,
    KAPPA,
    L3,
    L4,
    L5,
    L_RATIO,
    MASS_CONTRACT_ID,
    RUNTIME_SOURCE_LOCATOR,
    RUNTIME_SOURCE_SHA256,
    SemanticMassBinding,
    SemanticMassRegistry,
    SemanticMassV19Error,
    materialize_kaku_mass,
    phase_order_parameter,
    semantic_mass_value,
    verify_kaku_mass,
    verify_serialized_mass_binding,
)

PNV = ROOT / "native" / "PNCS_SEMANTIC_MASS_BINDING_V0_19.pnv"
LEDGER = ROOT / "mining" / "PNCS_SEMANTIC_MASS_BINDING_LEDGER_V0_19.json"

ALLOWED = {
    "IDENTITY","DIFFERENCE","ORDER","COMPOSITION","ADDITION","FORCE","NEGATION","QUESTION","TRANSFORM","RETURN","FOLD","BOUNDARY","SCOPE","AFFECT","CONSENT","SOURCE","MEMORY","RISK","ASSERTION","CONDITION","CAUSE","MODAL_POSSIBILITY","MODAL_NECESSITY","MODAL_PERMISSION","MODAL_OBLIGATION","UNCERTAINTY","SOURCE_REQUIRED","CANON_BLOCK","CONSENT_REQUIRED","ACTION_REQUEST","REFUSAL","PAUSE","SIMULATION_BOUNDARY","UNRUH_DRIVE","WARP_DRIFT","ATTRACTOR","SOFT_CLIP","RESOLVE","DERIVE"
}

BASIS = "PNV_T36_PHASE_ANGLES_RADIANS_V1"
DERIVATION = "EXTERNAL_EVIDENCE_BINDING_V1"
SOURCE_DIGEST = hashlib.sha256(b"phase-evidence-fixture-v19").hexdigest()


def cid(surface: str = "risk ABOVE 0.8") -> str:
    return predicate_content(surface).content_id


def phase(offset: float = 0.0) -> PhaseVector36:
    return PhaseVector36(tuple(((i * 0.137) + offset) % (2.0 * math.pi) for i in range(36)))


def realization(
    content_id: str | None = None,
    *,
    vector: PhaseVector36 | None = None,
    source_locator: str = "library://phase-source-a",
) -> RealizationBinding:
    return RealizationBinding(
        content_id=content_id or cid(),
        phase=vector or phase(),
        basis_id=BASIS,
        derivation_id=DERIVATION,
        source_digest_sha256=SOURCE_DIGEST,
        source_locator=source_locator,
    )


def mass_binding(
    content_id: str | None = None,
    *,
    k: int = 7,
    vector: PhaseVector36 | None = None,
    source_locator: str = "library://phase-source-a",
) -> SemanticMassBinding:
    return SemanticMassBinding(realization(content_id, vector=vector, source_locator=source_locator), k)


def fail(fn):
    try:
        fn()
    except SemanticMassV19Error:
        return
    raise AssertionError("expected SemanticMassV19Error")


def test_contract_constants_match_validated_runtime():
    assert KAPPA == 0.009193150006360484
    assert ALPHA_M == 0.0072973113787402075
    assert (L3, L4, L5) == (7, 2, 5)
    assert L_RATIO == 2 / 7


def test_runtime_source_digest_is_frozen():
    assert RUNTIME_SOURCE_SHA256 == "0b4df86cd01db313ea46ebac0eceee9cf6df0673391edd1a3fb2667c30464a32"
    assert RUNTIME_SOURCE_LOCATOR.endswith(":v1:pnv_runtime.py")


def test_order_parameter_matches_runtime_reference_fixture():
    assert phase_order_parameter(phase()) == 0.25379124942650777


def test_mass_matches_runtime_reference_k1():
    assert semantic_mass_value(1, phase()) == 0.0817720208


def test_mass_matches_runtime_reference_k7():
    assert semantic_mass_value(7, phase()) == 0.0821745325


def test_mass_matches_runtime_reference_k515():
    assert semantic_mass_value(515, phase()) == 0.1162538538


def test_mass_matches_runtime_reference_k999():
    assert semantic_mass_value(999, phase()) == 0.1487231284


def test_phase_index_must_be_explicit_positive_integer():
    for bad in [0, -1, True, 1.0, "1", None]:
        fail(lambda bad=bad: SemanticMassBinding(realization(), bad))


def test_binding_uses_only_validated_mass_contract():
    fail(lambda: SemanticMassBinding(realization(), 1, mass_contract_id="OTHER"))


def test_binding_rejects_runtime_digest_drift():
    fail(lambda: SemanticMassBinding(realization(), 1, runtime_source_sha256="0" * 64))


def test_binding_rejects_runtime_locator_drift():
    fail(lambda: SemanticMassBinding(realization(), 1, runtime_source_locator="other"))


def test_binding_remains_chyba_and_cannot_self_canonize():
    fail(lambda: SemanticMassBinding(realization(), 1, epistemic_operator="VERIFIED"))
    fail(lambda: SemanticMassBinding(realization(), 1, canon_allowed=True))


def test_mass_realization_id_is_deterministic():
    assert mass_binding().mass_realization_id == mass_binding().mass_realization_id


def test_mass_binding_id_is_deterministic():
    assert mass_binding().mass_binding_id == mass_binding().mass_binding_id


def test_realization_provenance_changes_mass_binding_not_mass_realization():
    a = mass_binding(source_locator="library://a")
    b = mass_binding(source_locator="library://b")
    assert a.mass_realization_id == b.mass_realization_id
    assert a.mass_binding_id != b.mass_binding_id


def test_phase_index_changes_mass_and_mass_identity():
    a = mass_binding(k=1)
    b = mass_binding(k=7)
    assert a.semantic_mass != b.semantic_mass
    assert a.mass_realization_id != b.mass_realization_id


def test_phase_realization_changes_mass_identity():
    a = mass_binding(vector=phase(0.0))
    b = mass_binding(vector=phase(0.31))
    assert a.mass_realization_id != b.mass_realization_id


def test_registry_idempotent_for_same_binding():
    r = SemanticMassRegistry()
    a = r.bind(mass_binding())
    b = r.bind(mass_binding())
    assert a.mass_binding_id == b.mass_binding_id


def test_registry_preserves_multiple_provenance_bindings():
    r = SemanticMassRegistry()
    a = r.bind(mass_binding(source_locator="library://a"))
    b = r.bind(mass_binding(source_locator="library://b"))
    assert a.mass_realization_id == b.mass_realization_id
    assert a.mass_binding_id != b.mass_binding_id


def test_equal_mass_does_not_merge_semantic_content():
    a_id = cid("risk ABOVE 0.8")
    b_id = cid("temperature ABOVE 80")
    r = SemanticMassRegistry()
    a = r.bind(mass_binding(a_id, k=7, source_locator="library://a"))
    b = r.bind(mass_binding(b_id, k=7, source_locator="library://b"))
    assert a.semantic_mass == b.semantic_mass
    assert a.realization.content_id != b.realization.content_id
    assert r.semantic_ids_for_exact_mass(a.semantic_mass) == tuple(sorted([a_id, b_id]))


def test_mass_semantic_equivalence_api_fails_by_design():
    r = SemanticMassRegistry()
    fail(lambda: r.semantic_equivalent(mass_binding(), mass_binding()))


def test_registry_unknown_binding_fails_closed():
    r = SemanticMassRegistry()
    fail(lambda: r.binding("pncs:mass-binding:sha256:" + "0" * 64))


def test_registry_exact_mass_query_rejects_nonfinite():
    r = SemanticMassRegistry()
    for bad in [float("nan"), float("inf"), "not-a-number"]:
        fail(lambda bad=bad: r.semantic_ids_for_exact_mass(bad))


def test_registry_receipt_is_insertion_order_deterministic():
    a = mass_binding(cid("risk ABOVE 0.8"), source_locator="library://a")
    b = mass_binding(cid("temperature ABOVE 80"), source_locator="library://b")
    r1, r2 = SemanticMassRegistry(), SemanticMassRegistry()
    r1.bind(a); r1.bind(b)
    r2.bind(b); r2.bind(a)
    assert r1.deterministic_receipt() == r2.deterministic_receipt()


def test_registry_receipt_blocks_mass_semantic_authority():
    r = SemanticMassRegistry(); r.bind(mass_binding())
    receipt = r.deterministic_receipt()
    assert receipt["semantic_equivalence_from_mass"] is False
    assert receipt["mass_contract_id"] == MASS_CONTRACT_ID
    assert receipt["runtime_source_sha256"] == RUNTIME_SOURCE_SHA256


def test_materialize_kaku_sets_mass_from_binding():
    b = mass_binding(k=7)
    v = Vector36(tuple(float(i) for i in range(36)), BASIS)
    k = materialize_kaku_mass(
        kaku_id="K.TEST",
        vector=v,
        direction="forward",
        polarity=1.0,
        role="predicate",
        mass_binding=b,
    )
    assert k.semantic_mass == 0.0821745325
    assert tuple(k.phase) == b.realization.phase.angles
    verify_kaku_mass(k, b)


def test_materialize_kaku_rejects_basis_mismatch():
    b = mass_binding()
    v = Vector36(tuple(float(i) for i in range(36)), "OTHER_BASIS")
    fail(lambda: materialize_kaku_mass(
        kaku_id="K.TEST", vector=v, direction="forward", polarity=1.0, role="predicate", mass_binding=b
    ))


def test_verify_kaku_detects_mass_tamper():
    b = mass_binding()
    v = Vector36(tuple(float(i) for i in range(36)), BASIS)
    k = materialize_kaku_mass(kaku_id="K.TEST", vector=v, direction="forward", polarity=1.0, role="predicate", mass_binding=b)
    bad = type(k)(k.kaku_id, k.vector, k.semantic_mass + 1e-6, k.direction, k.polarity, k.role, k.phase)
    fail(lambda: verify_kaku_mass(bad, b))


def test_verify_kaku_detects_phase_tamper():
    b = mass_binding()
    v = Vector36(tuple(float(i) for i in range(36)), BASIS)
    k = materialize_kaku_mass(kaku_id="K.TEST", vector=v, direction="forward", polarity=1.0, role="predicate", mass_binding=b)
    altered = list(k.phase); altered[0] += 1e-6
    bad = type(k)(k.kaku_id, k.vector, k.semantic_mass, k.direction, k.polarity, k.role, tuple(altered))
    fail(lambda: verify_kaku_mass(bad, b))


def test_serialized_mass_binding_roundtrip():
    b = mass_binding()
    recovered = verify_serialized_mass_binding(b.record_payload, realization=b.realization)
    assert recovered.mass_binding_id == b.mass_binding_id
    assert recovered.mass_realization_id == b.mass_realization_id


def test_serialized_semantic_mass_tamper_is_detected():
    b = mass_binding()
    payload = dict(b.record_payload); payload["semantic_mass"] += 1e-6
    fail(lambda: verify_serialized_mass_binding(payload, realization=b.realization))


def test_serialized_phase_index_tamper_is_detected():
    b = mass_binding()
    payload = dict(b.record_payload); payload["phase_index"] = b.phase_index + 1
    fail(lambda: verify_serialized_mass_binding(payload, realization=b.realization))


def test_serialized_binding_id_tamper_is_detected():
    b = mass_binding()
    payload = dict(b.record_payload); payload["mass_binding_id"] = "pncs:mass-binding:sha256:" + "0" * 64
    fail(lambda: verify_serialized_mass_binding(payload, realization=b.realization))


def test_serialized_extra_key_fails_closed():
    b = mass_binding()
    payload = dict(b.record_payload); payload["extra"] = True
    fail(lambda: verify_serialized_mass_binding(payload, realization=b.realization))


def test_no_11d_truncation_literal_in_v19_module():
    source = (ROOT / "src" / "phasenav_natural_code" / "mass_v19.py").read_text(encoding="utf-8")
    assert "[:11]" not in source
    assert "v36[:11]" not in source


def test_no_broad_exception_handler_in_v19_module():
    source = (ROOT / "src" / "phasenav_natural_code" / "mass_v19.py").read_text(encoding="utf-8")
    assert "except Exception" not in source


def test_no_content_hash_to_phase_index_mapping_in_v19_module():
    source = (ROOT / "src" / "phasenav_natural_code" / "mass_v19.py").read_text(encoding="utf-8")
    assert "int(content" not in source
    assert "hash(content" not in source
    assert "phase_index must be an explicit positive integer" in source


def test_native_mass_witness_uses_only_recovered_opcodes():
    ops = []
    for raw in PNV.read_text(encoding="utf-8").splitlines():
        parts = raw.strip().split()
        if parts[:1] == ["OP"]:
            ops.append(parts[2])
    assert ops
    assert set(ops) <= ALLOWED


def test_native_mass_witness_keeps_identity_separate():
    text = PNV.read_text(encoding="utf-8")
    assert "MASS_EQUALITY_SEMANTIC_AUTHORITY FALSE" in text
    assert "PHASE_INDEX EXPLICIT_POSITIVE_INTEGER" in text
    assert "PHYSICAL_MASS_CLAIM FALSE" in text


def test_ledger_records_exact_contract_scope():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["formula"] == "m_k = kappa*(1 + alpha_M*k) + (L4/L3)*R_k"
    assert data["phase_index_policy"] == "EXPLICIT_POSITIVE_INTEGER"
    assert data["semantic_equivalence_from_mass_equality"] is False
    assert data["physical_mass_claim"] is False
    assert data["runtime_source_sha256"] == RUNTIME_SOURCE_SHA256


def test_generic_natural_language_compiler_stays_disabled():
    from phasenav_natural_code.compiler import BasisNotCanonizedError, compile_natural_language
    try:
        compile_natural_language("risk above 0.8")
    except BasisNotCanonizedError:
        pass
    else:
        raise AssertionError("generic NL compiler unexpectedly enabled")
