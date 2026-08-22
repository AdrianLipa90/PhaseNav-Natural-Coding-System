from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping

from .model import Kaku, Vector36
from .realization_v18 import PhaseVector36, RealizationBinding

PI = 3.14159265358979323846
TAU = 6.28318530717958647692
KAPPA = math.log(2) / (24.0 * PI)
L3 = 7
L4 = 2
L5 = 5
ALPHA_M = 1.0 / ((L3 * L4) ** 2 - L3 ** 2 - L4 * L5 + L4 ** 2 * KAPPA)
L_RATIO = L4 / L3

MASS_CONTRACT_ID = "PNV_SEMANTIC_MASS_V1"
RUNTIME_SOURCE_SHA256 = "0b4df86cd01db313ea46ebac0eceee9cf6df0673391edd1a3fb2667c30464a32"
RUNTIME_SOURCE_LOCATOR = "NOEMA_LIBRARY:file_00000000ea0c8210b0ff0db8ea94071a:v1:pnv_runtime.py"
_MASS_SCHEMA = "PNCS_SEMANTIC_MASS_REALIZATION_V0_19"
_BINDING_SCHEMA = "PNCS_SEMANTIC_MASS_BINDING_V0_19"


class SemanticMassV19Error(ValueError):
    pass


def _compact_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _typed_id(prefix: str, payload: Mapping[str, object]) -> str:
    return f"{prefix}:sha256:{_sha256_hex(_compact_json(dict(payload)).encode('utf-8'))}"


def _phase_index(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SemanticMassV19Error("phase_index must be an explicit positive integer")
    return value


def _runtime_sin(x: float) -> float:
    x = float(x) % TAU
    s = 0.0
    t = x
    for n in range(1, 30, 2):
        s += t
        t *= -x * x / ((n + 1) * (n + 2))
    return s


def _runtime_cos(x: float) -> float:
    x = float(x) % TAU
    s = 0.0
    t = 1.0
    for n in range(0, 30, 2):
        s += t
        t *= -x * x / ((n + 1) * (n + 2))
    return s


def phase_order_parameter(phase: PhaseVector36) -> float:
    if not isinstance(phase, PhaseVector36):
        raise SemanticMassV19Error("PhaseVector36 required")
    s = 0.0
    c = 0.0
    for value in phase.angles:
        s += _runtime_sin(value)
        c += _runtime_cos(value)
    return (s * s + c * c) ** 0.5 / len(phase.angles)


def semantic_mass_value(phase_index: int, phase: PhaseVector36) -> float:
    k = _phase_index(phase_index)
    r_k = phase_order_parameter(phase)
    return round(KAPPA * (1.0 + ALPHA_M * k) + L_RATIO * r_k, 10)


@dataclass(frozen=True)
class SemanticMassBinding:
    realization: RealizationBinding
    phase_index: int
    mass_contract_id: str = MASS_CONTRACT_ID
    runtime_source_sha256: str = RUNTIME_SOURCE_SHA256
    runtime_source_locator: str = RUNTIME_SOURCE_LOCATOR
    epistemic_operator: str = "CHYBA"
    canon_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.realization, RealizationBinding):
            raise SemanticMassV19Error("realization must be RealizationBinding")
        object.__setattr__(self, "phase_index", _phase_index(self.phase_index))
        if self.mass_contract_id != MASS_CONTRACT_ID:
            raise SemanticMassV19Error("v0.19 accepts only the validated PhaseNav semantic-mass contract")
        if self.runtime_source_sha256 != RUNTIME_SOURCE_SHA256:
            raise SemanticMassV19Error("runtime source digest does not match the validated mass contract")
        if self.runtime_source_locator != RUNTIME_SOURCE_LOCATOR:
            raise SemanticMassV19Error("runtime source locator does not match the validated mass contract")
        if self.epistemic_operator != "CHYBA":
            raise SemanticMassV19Error("v0.19 bindings must remain under CHYBA")
        if self.canon_allowed:
            raise SemanticMassV19Error("v0.19 mass binding cannot self-promote to canon")

    @property
    def order_parameter_R(self) -> float:
        return phase_order_parameter(self.realization.phase)

    @property
    def semantic_mass(self) -> float:
        return semantic_mass_value(self.phase_index, self.realization.phase)

    @property
    def mass_payload(self) -> dict[str, object]:
        return {
            "schema": _MASS_SCHEMA,
            "content_id": self.realization.content_id,
            "realization_id": self.realization.realization_id,
            "phase_index": self.phase_index,
            "mass_contract_id": self.mass_contract_id,
            "runtime_source_sha256": self.runtime_source_sha256,
            "kappa": KAPPA,
            "alpha_m": ALPHA_M,
            "l3": L3,
            "l4": L4,
            "l5": L5,
            "l_ratio": L_RATIO,
            "order_parameter_R": self.order_parameter_R,
            "semantic_mass": self.semantic_mass,
        }

    @property
    def mass_realization_id(self) -> str:
        return _typed_id("pncs:mass", self.mass_payload)

    @property
    def binding_payload(self) -> dict[str, object]:
        return {
            "schema": _BINDING_SCHEMA,
            "mass_realization_id": self.mass_realization_id,
            "content_id": self.realization.content_id,
            "realization_id": self.realization.realization_id,
            "realization_binding_id": self.realization.binding_id,
            "phase_index": self.phase_index,
            "mass_contract_id": self.mass_contract_id,
            "runtime_source_sha256": self.runtime_source_sha256,
            "runtime_source_locator": self.runtime_source_locator,
            "semantic_mass": self.semantic_mass,
            "epistemic_operator": self.epistemic_operator,
            "canon_allowed": self.canon_allowed,
        }

    @property
    def mass_binding_id(self) -> str:
        return _typed_id("pncs:mass-binding", self.binding_payload)

    @property
    def record_payload(self) -> dict[str, object]:
        return {**self.binding_payload, "mass_binding_id": self.mass_binding_id}

    def verify(self) -> None:
        fresh = semantic_mass_value(self.phase_index, self.realization.phase)
        if fresh != self.semantic_mass:
            raise SemanticMassV19Error("semantic mass recomputation mismatch")
        if self.realization.phase.phase_sha256 != self.realization.binding_payload["phase36_sha256"]:
            raise SemanticMassV19Error("realization phase digest mismatch")


class SemanticMassRegistry:
    def __init__(self) -> None:
        self._by_binding: dict[str, SemanticMassBinding] = {}
        self._by_key: dict[tuple[str, str, int, str], list[str]] = {}
        self._by_value: dict[float, set[str]] = {}

    def bind(self, binding: SemanticMassBinding) -> SemanticMassBinding:
        if not isinstance(binding, SemanticMassBinding):
            raise SemanticMassV19Error("SemanticMassBinding required")
        binding.verify()
        key = (
            binding.realization.content_id,
            binding.realization.realization_id,
            binding.phase_index,
            binding.mass_contract_id,
        )
        existing = self._by_key.get(key, [])
        for binding_id in existing:
            prior = self._by_binding[binding_id]
            if prior.mass_realization_id != binding.mass_realization_id:
                raise SemanticMassV19Error("conflicting mass realization for the same semantic/phase/index contract")
        if binding.mass_binding_id not in self._by_binding:
            self._by_binding[binding.mass_binding_id] = binding
            self._by_key.setdefault(key, []).append(binding.mass_binding_id)
            self._by_value.setdefault(binding.semantic_mass, set()).add(binding.realization.content_id)
        return self._by_binding[binding.mass_binding_id]

    def binding(self, mass_binding_id: str) -> SemanticMassBinding:
        try:
            return self._by_binding[mass_binding_id]
        except KeyError as exc:
            raise SemanticMassV19Error(f"unknown mass_binding_id: {mass_binding_id}") from exc

    def semantic_ids_for_exact_mass(self, value: float) -> tuple[str, ...]:
        try:
            mass = float(value)
        except (TypeError, ValueError) as exc:
            raise SemanticMassV19Error("finite semantic-mass value required") from exc
        if not math.isfinite(mass):
            raise SemanticMassV19Error("finite semantic-mass value required")
        return tuple(sorted(self._by_value.get(mass, set())))

    def semantic_equivalent(self, *_: object) -> bool:
        raise SemanticMassV19Error("semantic-mass equality is not semantic equivalence authority")

    def deterministic_receipt(self) -> dict[str, object]:
        rows = [self._by_binding[key].binding_payload for key in sorted(self._by_binding)]
        payload = {
            "schema": "PNCS_SEMANTIC_MASS_REGISTRY_RECEIPT_V0_19",
            "mass_binding_ids": sorted(self._by_binding),
            "bindings": rows,
            "semantic_equivalence_from_mass": False,
            "mass_contract_id": MASS_CONTRACT_ID,
            "runtime_source_sha256": RUNTIME_SOURCE_SHA256,
        }
        return {**payload, "receipt_sha256": _sha256_hex(_compact_json(payload).encode("utf-8"))}


def materialize_kaku_mass(
    *,
    kaku_id: str,
    vector: Vector36,
    direction: str,
    polarity: float,
    role: str,
    mass_binding: SemanticMassBinding,
) -> Kaku:
    if not isinstance(vector, Vector36):
        raise SemanticMassV19Error("Vector36 required")
    if not isinstance(mass_binding, SemanticMassBinding):
        raise SemanticMassV19Error("SemanticMassBinding required")
    mass_binding.verify()
    if vector.basis_id != mass_binding.realization.basis_id:
        raise SemanticMassV19Error("KAKU vector basis does not match mass realization basis")
    return Kaku(
        kaku_id=kaku_id,
        vector=vector,
        semantic_mass=mass_binding.semantic_mass,
        direction=direction,
        polarity=polarity,
        role=role,
        phase=mass_binding.realization.phase.angles,
    )


def verify_kaku_mass(kaku: Kaku, mass_binding: SemanticMassBinding) -> None:
    if not isinstance(kaku, Kaku):
        raise SemanticMassV19Error("Kaku required")
    if not isinstance(mass_binding, SemanticMassBinding):
        raise SemanticMassV19Error("SemanticMassBinding required")
    mass_binding.verify()
    if kaku.vector.basis_id != mass_binding.realization.basis_id:
        raise SemanticMassV19Error("KAKU vector basis mismatch")
    if kaku.phase is None or tuple(kaku.phase) != mass_binding.realization.phase.angles:
        raise SemanticMassV19Error("KAKU phase does not match exact realization")
    if float(kaku.semantic_mass) != mass_binding.semantic_mass:
        raise SemanticMassV19Error("KAKU semantic_mass does not match PhaseNav mass binding")


def verify_serialized_mass_binding(
    payload: Mapping[str, object],
    *,
    realization: RealizationBinding,
) -> SemanticMassBinding:
    if not isinstance(payload, Mapping):
        raise SemanticMassV19Error("mass binding payload mapping required")
    required = {
        "schema",
        "mass_realization_id",
        "content_id",
        "realization_id",
        "realization_binding_id",
        "phase_index",
        "mass_contract_id",
        "runtime_source_sha256",
        "runtime_source_locator",
        "semantic_mass",
        "epistemic_operator",
        "canon_allowed",
        "mass_binding_id",
    }
    if set(payload) != required:
        raise SemanticMassV19Error("serialized mass binding keys do not match v0.19 schema")
    if payload.get("schema") != _BINDING_SCHEMA:
        raise SemanticMassV19Error("serialized mass binding schema mismatch")
    if payload.get("content_id") != realization.content_id:
        raise SemanticMassV19Error("serialized content_id mismatch")
    if payload.get("realization_id") != realization.realization_id:
        raise SemanticMassV19Error("serialized realization_id mismatch")
    if payload.get("realization_binding_id") != realization.binding_id:
        raise SemanticMassV19Error("serialized realization_binding_id mismatch")
    binding = SemanticMassBinding(
        realization=realization,
        phase_index=_phase_index(payload.get("phase_index")),
        mass_contract_id=str(payload.get("mass_contract_id")),
        runtime_source_sha256=str(payload.get("runtime_source_sha256")),
        runtime_source_locator=str(payload.get("runtime_source_locator")),
        epistemic_operator=str(payload.get("epistemic_operator")),
        canon_allowed=bool(payload.get("canon_allowed")),
    )
    if payload.get("semantic_mass") != binding.semantic_mass:
        raise SemanticMassV19Error("serialized semantic_mass mismatch")
    if payload.get("mass_realization_id") != binding.mass_realization_id:
        raise SemanticMassV19Error("serialized mass_realization_id mismatch")
    if payload.get("mass_binding_id") != binding.mass_binding_id:
        raise SemanticMassV19Error("serialized mass_binding_id mismatch")
    if dict(payload) != binding.record_payload:
        raise SemanticMassV19Error("serialized mass binding payload mismatch")
    return binding
