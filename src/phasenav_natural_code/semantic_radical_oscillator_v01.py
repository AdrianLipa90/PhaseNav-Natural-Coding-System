from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping

from .model import RadicalGraph
from .semantic_orbital_carrier_v01 import SemanticOrbitalBinding


SCHEMA = "PNCS_SEMANTIC_RADICAL_OSCILLATOR_V0_1"


class SemanticRadicalOscillatorError(ValueError):
    pass


def _finite(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise SemanticRadicalOscillatorError(f"{name} must be finite")
    return value


def _text(name: str, value: str) -> str:
    value = str(value).strip()
    if not value:
        raise SemanticRadicalOscillatorError(f"{name} must be non-empty")
    return value


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def validate_radical_bindings(
    radical: RadicalGraph,
    bindings: Mapping[str, SemanticOrbitalBinding],
) -> None:
    if not isinstance(radical, RadicalGraph):
        raise SemanticRadicalOscillatorError("radical must be RadicalGraph")
    expected = set(radical.nodes)
    supplied = set(bindings)
    if expected != supplied:
        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        raise SemanticRadicalOscillatorError(
            f"semantic binding coverage mismatch: missing={missing}, extra={extra}"
        )
    for kaku_id in sorted(expected):
        binding = bindings[kaku_id]
        if not isinstance(binding, SemanticOrbitalBinding):
            raise SemanticRadicalOscillatorError(
                f"binding for {kaku_id} must be SemanticOrbitalBinding"
            )
        if binding.sample.kaku_id != kaku_id:
            raise SemanticRadicalOscillatorError(
                f"binding KAKU id mismatch for graph node {kaku_id}"
            )


def relation_oscillator_deltas(
    radical: RadicalGraph,
    bindings: Mapping[str, SemanticOrbitalBinding],
) -> tuple[dict[str, Any], ...]:
    validate_radical_bindings(radical, bindings)
    out: list[dict[str, Any]] = []
    for edge in sorted(
        radical.edges,
        key=lambda e: (e.relation_id, e.source_id, e.target_id, e.relation_type),
    ):
        source = bindings[edge.source_id]
        target = bindings[edge.target_id]
        delta_phi = target.sample.phi - source.sample.phi
        delta_shifted_phase = target.sample.phase_kappa - source.sample.phase_kappa
        if not math.isclose(delta_phi, delta_shifted_phase, rel_tol=0.0, abs_tol=1e-15):
            raise SemanticRadicalOscillatorError("common kappa phase shift failed to cancel")
        out.append(
            {
                "relation_id": edge.relation_id,
                "relation_type": edge.relation_type,
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "source_orbital_band": source.orbital_band,
                "target_orbital_band": target.orbital_band,
                "delta_phi": delta_phi,
                "delta_phase_plus_kappa": delta_shifted_phase,
                "delta_omega": target.sample.omega - source.sample.omega,
                "delta_semantic_value": target.sample.value - source.sample.value,
            }
        )
    return tuple(out)


@dataclass(frozen=True)
class RadicalAggregationProfile:
    aggregation_profile_id: str
    weights: Mapping[str, float]
    normalization: str = "NONE"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "aggregation_profile_id",
            _text("aggregation_profile_id", self.aggregation_profile_id),
        )
        normalization = str(self.normalization).upper()
        if normalization not in {"NONE", "UNIT_SUM"}:
            raise SemanticRadicalOscillatorError(
                "normalization must be NONE or UNIT_SUM"
            )
        object.__setattr__(self, "normalization", normalization)
        clean = {str(k): _finite(f"weight[{k}]", v) for k, v in self.weights.items()}
        if not clean:
            raise SemanticRadicalOscillatorError("aggregation weights must be non-empty")
        object.__setattr__(self, "weights", clean)

    def validated_weights(self, radical: RadicalGraph) -> dict[str, float]:
        expected = set(radical.nodes)
        supplied = set(self.weights)
        if expected != supplied:
            missing = sorted(expected - supplied)
            extra = sorted(supplied - expected)
            raise SemanticRadicalOscillatorError(
                f"aggregation weight coverage mismatch: missing={missing}, extra={extra}"
            )
        weights = {k: float(self.weights[k]) for k in sorted(expected)}
        if self.normalization == "UNIT_SUM":
            total = math.fsum(weights.values())
            if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-12):
                raise SemanticRadicalOscillatorError(
                    f"UNIT_SUM aggregation weights must sum to 1, got {total}"
                )
        return weights

    def to_dict(self, radical: RadicalGraph) -> dict[str, Any]:
        return {
            "aggregation_profile_id": self.aggregation_profile_id,
            "normalization": self.normalization,
            "weights": self.validated_weights(radical),
        }


def aggregate_radical_semantic_value(
    radical: RadicalGraph,
    bindings: Mapping[str, SemanticOrbitalBinding],
    profile: RadicalAggregationProfile,
) -> float:
    validate_radical_bindings(radical, bindings)
    if not isinstance(profile, RadicalAggregationProfile):
        raise SemanticRadicalOscillatorError(
            "explicit RadicalAggregationProfile is required"
        )
    weights = profile.validated_weights(radical)
    return math.fsum(weights[k] * bindings[k].sample.value for k in sorted(weights))


def radical_semantic_receipt(
    radical: RadicalGraph,
    bindings: Mapping[str, SemanticOrbitalBinding],
    *,
    aggregation_profile: RadicalAggregationProfile | None = None,
) -> dict[str, Any]:
    validate_radical_bindings(radical, bindings)
    nodes = {
        kaku_id: bindings[kaku_id].deterministic_receipt()
        for kaku_id in sorted(radical.nodes)
    }
    aggregate: dict[str, Any] | None = None
    if aggregation_profile is not None:
        aggregate = {
            "profile": aggregation_profile.to_dict(radical),
            "semantic_value": aggregate_radical_semantic_value(
                radical, bindings, aggregation_profile
            ),
        }
    body = {
        "schema": SCHEMA,
        "radical_id": radical.radical_id,
        "basis_id": radical.basis_id,
        "node_bindings": nodes,
        "relation_oscillator_deltas": list(
            relation_oscillator_deltas(radical, bindings)
        ),
        "aggregate": aggregate,
        "aggregation_authority": "EXPLICIT_PROFILE_ONLY",
        "epistemic_state": "CHYBA",
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
    }
    return {**body, "receipt_sha256": _sha256(body)}
