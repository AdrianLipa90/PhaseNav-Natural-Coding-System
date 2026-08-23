from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
from typing import Callable, Mapping

from .execution_v20_model import _sha256_json, _typed_id
from .orchorbital_executor_v27 import DirectCoupledTrace

ADVERSARIAL_CONTRACT_ID = "PNCS_ADVERSARIAL_BOUNDARY_V0_28"
CASE_SCHEMA = "PNCS_ADVERSARIAL_CASE_V0_28"
RESULT_SCHEMA = "PNCS_ADVERSARIAL_RESULT_V0_28"


class AdversarialV28Error(ValueError):
    pass


def resign_v20_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    """Recompute the canonical v0.20 receipt digest after an intentional mutation.

    This prevents adversarial tests from passing merely because the outer digest was stale.
    The downstream semantic/binding validator must still reject the mutated content.
    """
    if not isinstance(receipt, Mapping):
        raise AdversarialV28Error("receipt mapping required")
    body = copy.deepcopy(dict(receipt))
    body.pop("receipt_sha256", None)
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
    return resign_v20_receipt(out)


def cyrillic_confusable_operator(operator_id: str) -> str:
    value = str(operator_id)
    if not value:
        raise AdversarialV28Error("operator_id required")
    # U+041E CYRILLIC CAPITAL LETTER O is intentionally not normalized to Latin O.
    pos = value.find("O")
    if pos < 0:
        return "О" + value
    return value[:pos] + "О" + value[pos + 1 :]


def validate_direct_trace_structure(trace: DirectCoupledTrace) -> str:
    if not isinstance(trace, DirectCoupledTrace):
        raise AdversarialV28Error("DirectCoupledTrace required")
    steps = trace.base_steps
    if not steps:
        raise AdversarialV28Error("direct trace has no v0.20 steps")
    if len(trace.transition_ids) != len(steps):
        raise AdversarialV28Error("ORCH transition count differs from v0.20 step count")
    if len(set(trace.transition_ids)) != len(trace.transition_ids):
        raise AdversarialV28Error("duplicate ORCH transition identity")
    if len(trace.final_orch.orbitals) != len(steps):
        raise AdversarialV28Error("ORCH orbital count differs from v0.20 step count")
    mode_ids = tuple(o.mode_id for o in trace.final_orch.orbitals)
    if len(set(mode_ids)) != len(mode_ids):
        raise AdversarialV28Error("duplicate ORCH occurrence identity")
    if tuple(trace.final_orch.sphere.mode_ids) != mode_ids:
        raise AdversarialV28Error("ORCH process sphere mode order differs from orbitals")

    previous = trace.initial_sigma_id
    for expected_index, step in enumerate(steps, start=1):
        if step.index != expected_index:
            raise AdversarialV28Error("v0.20 step index discontinuity in direct trace")
        if step.before_sigma_id != previous:
            raise AdversarialV28Error("v0.20 Sigma chain discontinuity in direct trace")
        previous = step.after_sigma_id
    if previous != trace.final_sigma_id:
        raise AdversarialV28Error("direct trace final Sigma endpoint mismatch")

    payload = trace.payload
    closed_false = (
        "v020_sigma_semantics_modified",
        "routing_authority_opened",
        "effect_authority_opened",
        "persistent_memory_write_performed",
        "external_effects",
        "laboratory_time_modified",
    )
    for field in closed_false:
        if payload.get(field) is not False:
            raise AdversarialV28Error(f"authority boundary opened in direct trace: {field}")
    if trace.final_phase.phase_proper_time < 0.0:
        raise AdversarialV28Error("negative T^36 phase proper time")
    return trace.trace_id


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
