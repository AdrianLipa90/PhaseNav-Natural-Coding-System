from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import math
from typing import Callable, Mapping

from .hydro_time_v27 import _sha256_json, _typed_id
from .execution_orch_authority_v27 import (
    COUPLED_EXECUTION_CONTRACT_ID,
    COUPLED_RECEIPT_SCHEMA,
    EXECUTABLE_INTERNAL_OPERATORS,
    V20_CONTRACT_ID,
    V20_RECEIPT_SCHEMA,
)

ADVERSARIAL_CONTRACT_ID = "PNCS_ADVERSARIAL_BOUNDARY_V0_28"
CASE_SCHEMA = "PNCS_ADVERSARIAL_CASE_V0_28"
RESULT_SCHEMA = "PNCS_ADVERSARIAL_RESULT_V0_28"


class AdversarialV28Error(ValueError):
    pass


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise AdversarialV28Error(f"{field} mapping required")
    return value


def _sha64(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise AdversarialV28Error(f"{field} must be a 64-character SHA-256 hex string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise AdversarialV28Error(f"{field} must be hexadecimal") from exc
    return value.lower()


def resign_coupled_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    """Recompute inner semantic-projection and outer receipt digests.

    This helper is intentionally adversarial: after a test mutation it refreshes
    the content-addressing layers that legitimately depend on the changed bytes.
    Rejection must therefore come from structural/semantic validation rather than
    from an intentionally stale outer checksum.
    """
    if not isinstance(receipt, Mapping):
        raise AdversarialV28Error("receipt mapping required")
    body = copy.deepcopy(dict(receipt))
    body.pop("receipt_sha256", None)
    projection = body.get("semantic_projection")
    if isinstance(projection, Mapping):
        body["semantic_projection_sha256"] = _sha256_json(dict(projection))
    body["receipt_sha256"] = _sha256_json(body)
    return body


def mutate_and_resign(
    receipt: Mapping[str, object],
    mutator: Callable[[dict[str, object]], None],
) -> dict[str, object]:
    if not callable(mutator):
        raise AdversarialV28Error("callable mutator required")
    out = copy.deepcopy(dict(receipt))
    mutator(out)
    return resign_coupled_receipt(out)


def cyrillic_confusable_operator(operator_id: str) -> str:
    value = str(operator_id)
    if not value:
        raise AdversarialV28Error("operator_id required")
    # U+041E CYRILLIC CAPITAL LETTER O is intentionally not canonicalized to ASCII O.
    pos = value.find("O")
    if pos < 0:
        return "О" + value
    return value[:pos] + "О" + value[pos + 1 :]


def validate_coupled_receipt_structure(
    receipt: Mapping[str, object],
    *,
    source_v20_receipt: Mapping[str, object] | None = None,
) -> str:
    """Validate the release-closed v0.27 coupled receipt without granting authority."""
    r = _mapping(receipt, "receipt")
    if r.get("schema") != COUPLED_RECEIPT_SCHEMA:
        raise AdversarialV28Error("unexpected coupled receipt schema")
    if r.get("execution_contract_id") != COUPLED_EXECUTION_CONTRACT_ID:
        raise AdversarialV28Error("unexpected coupled execution contract")

    claimed = _sha64(r.get("receipt_sha256"), "receipt_sha256")
    body = copy.deepcopy(dict(r))
    body.pop("receipt_sha256", None)
    if _sha256_json(body) != claimed:
        raise AdversarialV28Error("coupled receipt digest mismatch")

    projection = _mapping(r.get("semantic_projection"), "semantic_projection")
    projection_sha = _sha64(r.get("semantic_projection_sha256"), "semantic_projection_sha256")
    if _sha256_json(dict(projection)) != projection_sha:
        raise AdversarialV28Error("semantic projection digest mismatch")

    if source_v20_receipt is not None:
        source = _mapping(source_v20_receipt, "source_v20_receipt")
        if source.get("schema") != V20_RECEIPT_SCHEMA or source.get("execution_contract_id") != V20_CONTRACT_ID:
            raise AdversarialV28Error("exact v0.20 source receipt required")
        source_claim = _sha64(source.get("receipt_sha256"), "source v0.20 receipt_sha256")
        source_body = copy.deepcopy(dict(source))
        source_body.pop("receipt_sha256", None)
        if _sha256_json(source_body) != source_claim:
            raise AdversarialV28Error("source v0.20 receipt digest mismatch")
        if r.get("source_v20_authority_receipt_sha256") != source_claim:
            raise AdversarialV28Error("coupled receipt/source v0.20 identity mismatch")
        exact_fields = (
            "program",
            "canonical_graph_sha256",
            "canonical_leaf_path",
            "input_values",
            "admission",
            "initial_sigma_id",
            "final_sigma_id",
            "steps",
            "result",
            "external_effects",
            "semantic_mass_is_authorization",
            "free_form_nl_execution",
            "deterministic_fields_only",
        )
        for field in exact_fields:
            if projection.get(field) != source.get(field):
                raise AdversarialV28Error(f"coupled semantic projection differs from source v0.20: {field}")

    program = _mapping(projection.get("program"), "semantic_projection.program")
    graph_sha = projection.get("canonical_graph_sha256")
    leaf_path = projection.get("canonical_leaf_path")
    source_sha = r.get("source_v20_authority_receipt_sha256")
    if not isinstance(graph_sha, str) or not graph_sha:
        raise AdversarialV28Error("canonical graph SHA missing")
    if not isinstance(leaf_path, list):
        raise AdversarialV28Error("canonical leaf path missing")
    if not isinstance(source_sha, str) or not source_sha:
        raise AdversarialV28Error("source v0.20 receipt identity missing")
    expected_program_authority_id = _typed_id(
        "pncs:coupled-program-authority",
        {
            "source_v20_receipt_sha256": source_sha,
            "program": dict(program),
            "canonical_graph_sha256": graph_sha,
            "leaf_path": list(leaf_path),
        },
    )
    if r.get("program_authority_id") != expected_program_authority_id:
        raise AdversarialV28Error("program authority identity mismatch")

    steps = projection.get("steps")
    occurrences = r.get("orch_occurrences")
    occurrence_ids = r.get("orch_occurrence_ids")
    if not isinstance(steps, list) or not steps:
        raise AdversarialV28Error("semantic projection has no KAKU steps")
    if not isinstance(occurrences, list) or len(occurrences) != len(steps):
        raise AdversarialV28Error("ORCH occurrence count differs from KAKU step count")
    if not isinstance(occurrence_ids, list) or len(occurrence_ids) != len(steps):
        raise AdversarialV28Error("ORCH occurrence identity count differs from KAKU step count")
    if len(set(occurrence_ids)) != len(occurrence_ids):
        raise AdversarialV28Error("duplicate ORCH occurrence identity")

    initial_sigma = projection.get("initial_sigma_id")
    final_sigma = projection.get("final_sigma_id")
    if not isinstance(initial_sigma, str) or not initial_sigma:
        raise AdversarialV28Error("initial Sigma identity missing")
    if not isinstance(final_sigma, str) or not final_sigma:
        raise AdversarialV28Error("final Sigma identity missing")

    previous = initial_sigma
    for expected_index, (step_raw, occurrence_raw) in enumerate(zip(steps, occurrences), start=1):
        step = _mapping(step_raw, "KAKU step")
        occurrence = _mapping(occurrence_raw, "ORCH occurrence")
        if step.get("index") != expected_index:
            raise AdversarialV28Error("KAKU step index discontinuity")
        operator_id = step.get("operator_id")
        if operator_id not in EXECUTABLE_INTERNAL_OPERATORS:
            raise AdversarialV28Error("KAKU operator is outside the registered executable set")
        before_sigma = step.get("before_sigma_id")
        after_sigma = step.get("after_sigma_id")
        if before_sigma != previous:
            raise AdversarialV28Error("Sigma chain discontinuity")
        if not isinstance(after_sigma, str) or not after_sigma:
            raise AdversarialV28Error("KAKU after-Sigma identity missing")
        vector_sha = _sha64(step.get("operator_vector_sha256"), "operator_vector_sha256")

        if occurrence.get("step_index") != expected_index:
            raise AdversarialV28Error("ORCH occurrence step index mismatch")
        if occurrence.get("operator_id") != operator_id:
            raise AdversarialV28Error("ORCH/KAKU operator mismatch")
        if occurrence.get("operator_vector_sha256") != vector_sha:
            raise AdversarialV28Error("ORCH/KAKU operator-vector mismatch")
        if occurrence.get("before_sigma_id") != before_sigma:
            raise AdversarialV28Error("ORCH/KAKU before-Sigma mismatch")
        if occurrence.get("after_sigma_id") != after_sigma:
            raise AdversarialV28Error("ORCH/KAKU after-Sigma mismatch")
        if occurrence.get("semantic_identity_modified") is not False:
            raise AdversarialV28Error("ORCH occurrence modified semantic identity")
        if occurrence.get("external_effects") is not False:
            raise AdversarialV28Error("ORCH occurrence opened external effects")
        proper = occurrence.get("proper_time_advanced")
        if not isinstance(proper, (int, float)) or isinstance(proper, bool) or not math.isfinite(float(proper)) or float(proper) < 0.0:
            raise AdversarialV28Error("ORCH occurrence proper time must be finite and non-negative")
        previous = after_sigma

    if previous != final_sigma:
        raise AdversarialV28Error("final Sigma endpoint mismatch")

    projection_false = (
        "external_effects",
        "semantic_mass_is_authorization",
        "free_form_nl_execution",
    )
    for field in projection_false:
        if projection.get(field) is not False:
            raise AdversarialV28Error(f"semantic projection opened closed boundary: {field}")
    if projection.get("deterministic_fields_only") is not True:
        raise AdversarialV28Error("semantic projection is not deterministic-fields-only")

    receipt_false = (
        "routing_feedback_opened",
        "semantic_identity_modified",
        "external_effects",
        "laboratory_time_modified",
    )
    for field in receipt_false:
        if r.get(field) is not False:
            raise AdversarialV28Error(f"coupled receipt opened closed boundary: {field}")
    if r.get("deterministic_fields_only") is not True:
        raise AdversarialV28Error("coupled receipt is not deterministic-fields-only")

    total_proper = r.get("phase_proper_time_advanced")
    if not isinstance(total_proper, (int, float)) or isinstance(total_proper, bool) or not math.isfinite(float(total_proper)) or float(total_proper) < 0.0:
        raise AdversarialV28Error("coupled receipt phase proper time must be finite and non-negative")
    return claimed


@dataclass(frozen=True)
class AdversarialCase:
    attack_class: str
    target: str
    mutation: str
    expected: str = "REJECT"

    def __post_init__(self) -> None:
        for field in ("attack_class", "target", "mutation", "expected"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value:
                raise AdversarialV28Error(f"{field} required")
        if self.expected not in {"REJECT", "EQUIVALENT"}:
            raise AdversarialV28Error("expected must be REJECT or EQUIVALENT")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": CASE_SCHEMA,
            "contract_id": ADVERSARIAL_CONTRACT_ID,
            "attack_class": self.attack_class,
            "target": self.target,
            "mutation": self.mutation,
            "expected": self.expected,
            "external_effects": False,
        }

    @property
    def case_id(self) -> str:
        return _typed_id("pncs:adversarial-case", self.payload)


@dataclass(frozen=True)
class AdversarialResult:
    case: AdversarialCase
    observed: str
    validator: str
    detail: str

    def __post_init__(self) -> None:
        if self.observed not in {"REJECT", "ACCEPT_EQUIVALENT", "ACCEPT_MUTATED"}:
            raise AdversarialV28Error("invalid adversarial observation")
        if not isinstance(self.validator, str) or not self.validator:
            raise AdversarialV28Error("validator required")
        if not isinstance(self.detail, str):
            raise AdversarialV28Error("detail must be string")

    @property
    def passed(self) -> bool:
        if self.case.expected == "REJECT":
            return self.observed == "REJECT"
        return self.observed == "ACCEPT_EQUIVALENT"

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": RESULT_SCHEMA,
            "contract_id": ADVERSARIAL_CONTRACT_ID,
            "case_id": self.case.case_id,
            "observed": self.observed,
            "validator": self.validator,
            "detail_sha256": hashlib.sha256(self.detail.encode("utf-8")).hexdigest(),
            "passed": self.passed,
            "external_effects": False,
        }

    @property
    def result_id(self) -> str:
        return _typed_id("pncs:adversarial-result", self.payload)


def canonical_mapping_digest(value: Mapping[str, object]) -> str:
    if not isinstance(value, Mapping):
        raise AdversarialV28Error("mapping required")
    return _sha256_json(dict(value))
