from __future__ import annotations

"""Reference source-law loops for PNCS information-holonomy audits.

These builders instantiate the generic PNV law-frame engine with the source
factorizations used at the IDT <-> RFC interface.  OPEN physical normalizations
(q0, epsilon_Q) enter only as explicit parameters to conditional loop builders.
"""

from dataclasses import dataclass
import math
from typing import Any, Callable, Mapping, Sequence

from .gremlin_pnv_holonomy_v01 import (
    HolonomyInvariant,
    InformationHolonomyLoop,
    LawFrameNode,
    LawTransport,
    PNVInformationHolonomyError,
)
from .model import Kaku

SOURCE_HOLONOMY_CONTRACT = "PNCS_PNV_SOURCE_HOLONOMY_LOOPS_V0_1"
C_LIGHT_EXACT = 299_792_458.0


class PNVSourceHolonomyError(PNVInformationHolonomyError):
    pass


def _finite(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise PNVSourceHolonomyError(f"{field} must be finite") from exc
    if not math.isfinite(out):
        raise PNVSourceHolonomyError(f"{field} must be finite")
    return out


def _positive(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out <= 0.0:
        raise PNVSourceHolonomyError(f"{field} must be strictly positive")
    return out


def _finite_vector(values: Sequence[Any], field: str, *, nonnegative: bool = False) -> list[float]:
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence) or not values:
        raise PNVSourceHolonomyError(f"{field} must be a non-empty numeric sequence")
    out = [_finite(value, field) for value in values]
    if nonnegative and any(value < 0.0 for value in out):
        raise PNVSourceHolonomyError(f"{field} must be non-negative")
    return out


def _same_basis(left: Kaku, right: Kaku) -> None:
    if not isinstance(left, Kaku) or not isinstance(right, Kaku):
        raise PNVSourceHolonomyError("source holonomy loop requires Kaku law gates")
    if left.vector.basis_id != right.vector.basis_id:
        raise PNVSourceHolonomyError("source holonomy law gates must share one exact PNCS basis")


def make_extensive_carrier_state(q_cells: Sequence[Any]) -> dict[str, Any]:
    cells = _finite_vector(q_cells, "Q cells", nonnegative=True)
    total = math.fsum(cells)
    if total <= 0.0:
        raise PNVSourceHolonomyError("positive-source normalization requires Q_total > 0")
    return {
        "schema": "PNCS_EXTENSIVE_CARRIER_STATE_V0_1",
        "representation": "EXTENSIVE_CARRIER",
        "Q_cells": cells,
        "Q_total": total,
    }


def _normalize_carrier(state: Any) -> dict[str, Any]:
    if not isinstance(state, Mapping) or state.get("representation") != "EXTENSIVE_CARRIER":
        raise PNVSourceHolonomyError("carrier.normalize_profile requires EXTENSIVE_CARRIER state")
    cells = _finite_vector(state.get("Q_cells"), "Q cells", nonnegative=True)
    total = _positive(state.get("Q_total"), "Q_total")
    if math.fsum(cells) != total:
        raise PNVSourceHolonomyError("Q_total must equal the extensive carrier sum")
    return {
        "schema": "PNCS_NORMALIZED_CARRIER_STATE_V0_1",
        "representation": "NORMALIZED_PROFILE",
        "p_cells": [value / total for value in cells],
        "Q_total": total,
    }


def _reconstruct_carrier(state: Any) -> dict[str, Any]:
    if not isinstance(state, Mapping) or state.get("representation") != "NORMALIZED_PROFILE":
        raise PNVSourceHolonomyError("carrier.reconstruct_extensive requires NORMALIZED_PROFILE state")
    p_cells = _finite_vector(state.get("p_cells"), "p cells", nonnegative=True)
    total = _positive(state.get("Q_total"), "Q_total")
    norm = math.fsum(p_cells)
    if abs(norm - 1.0) > 1e-15:
        raise PNVSourceHolonomyError("normalized carrier profile must sum to one")
    return {
        "schema": "PNCS_EXTENSIVE_CARRIER_STATE_V0_1",
        "representation": "EXTENSIVE_CARRIER",
        "Q_cells": [total * value for value in p_cells],
        "Q_total": total,
    }


def carrier_total_invariant(state: Any) -> float:
    if not isinstance(state, Mapping):
        raise PNVSourceHolonomyError("carrier state mapping required")
    representation = state.get("representation")
    if representation in {"EXTENSIVE_CARRIER", "NORMALIZED_PROFILE"}:
        return _positive(state.get("Q_total"), "Q_total")
    if representation == "OCCUPATION_PROFILE":
        q0 = _positive(state.get("q0"), "q0")
        n_cells = _finite_vector(state.get("n_cells"), "occupation cells", nonnegative=True)
        return q0 * math.fsum(n_cells)
    raise PNVSourceHolonomyError(f"unsupported carrier representation: {representation}")


def carrier_profile_norm_invariant(state: Any) -> float:
    if not isinstance(state, Mapping):
        raise PNVSourceHolonomyError("carrier state mapping required")
    representation = state.get("representation")
    if representation == "NORMALIZED_PROFILE":
        return math.fsum(_finite_vector(state.get("p_cells"), "p cells", nonnegative=True))
    if representation == "EXTENSIVE_CARRIER":
        cells = _finite_vector(state.get("Q_cells"), "Q cells", nonnegative=True)
        total = _positive(state.get("Q_total"), "Q_total")
        return math.fsum(value / total for value in cells)
    if representation == "OCCUPATION_PROFILE":
        n_cells = _finite_vector(state.get("n_cells"), "occupation cells", nonnegative=True)
        total_n = math.fsum(n_cells)
        if total_n <= 0.0:
            raise PNVSourceHolonomyError("occupation profile requires positive total occupation")
        return math.fsum(value / total_n for value in n_cells)
    raise PNVSourceHolonomyError(f"unsupported carrier representation: {representation}")


def build_carrier_normalization_loop(
    extensive_gate: Kaku,
    normalized_gate: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
) -> InformationHolonomyLoop:
    _same_basis(extensive_gate, normalized_gate)
    refs = tuple(str(ref) for ref in evidence_refs)
    return InformationHolonomyLoop(
        loop_id="SOURCE.CARRIER.NORMALIZATION.ROUNDTRIP",
        nodes=(
            LawFrameNode(
                "LAW.RFC.CARRIER_EXTENSIVE",
                "RFC",
                extensive_gate,
                (*refs, "interface:Q_a,Q_total"),
            ),
            LawFrameNode(
                "LAW.IDT.NORMALIZED_PROFILE",
                "IDT",
                normalized_gate,
                (*refs, "interface:p_Q=Q_a/Q_total"),
            ),
        ),
        transports=(
            LawTransport(
                "EDGE.RFC_TO_IDT.NORMALIZE",
                extensive_gate.kaku_id,
                normalized_gate.kaku_id,
                "carrier.normalize_profile",
                ("equation:p_a=Q_a/Q_total",),
            ),
            LawTransport(
                "EDGE.IDT_TO_RFC.RECONSTRUCT",
                normalized_gate.kaku_id,
                extensive_gate.kaku_id,
                "carrier.reconstruct_extensive",
                ("equation:Q_a=Q_total*p_a",),
            ),
        ),
        invariants=(
            HolonomyInvariant("SOURCE.TOTAL_Q", "ABS", 0.0),
            HolonomyInvariant("SOURCE.PROFILE_NORM", "ABS", 1e-15),
        ),
        evidence_refs=refs,
    )


def carrier_normalization_transforms() -> Mapping[str, Callable[[Any], Any]]:
    return {
        "carrier.normalize_profile": _normalize_carrier,
        "carrier.reconstruct_extensive": _reconstruct_carrier,
    }


def carrier_normalization_invariants() -> Mapping[str, Callable[[Any], Any]]:
    return {
        "SOURCE.TOTAL_Q": carrier_total_invariant,
        "SOURCE.PROFILE_NORM": carrier_profile_norm_invariant,
    }


def _to_occupation(q0: float) -> Callable[[Any], dict[str, Any]]:
    q0_exact = _positive(q0, "q0")

    def transform(state: Any) -> dict[str, Any]:
        if not isinstance(state, Mapping) or state.get("representation") != "EXTENSIVE_CARRIER":
            raise PNVSourceHolonomyError("carrier.to_occupation requires EXTENSIVE_CARRIER state")
        cells = _finite_vector(state.get("Q_cells"), "Q cells", nonnegative=True)
        total = _positive(state.get("Q_total"), "Q_total")
        if math.fsum(cells) != total:
            raise PNVSourceHolonomyError("Q_total must equal the extensive carrier sum")
        return {
            "schema": "PNCS_CARRIER_OCCUPATION_STATE_V0_1",
            "representation": "OCCUPATION_PROFILE",
            "n_cells": [value / q0_exact for value in cells],
            "q0": q0_exact,
        }

    return transform


def _from_occupation(q0: float) -> Callable[[Any], dict[str, Any]]:
    q0_exact = _positive(q0, "q0")

    def transform(state: Any) -> dict[str, Any]:
        if not isinstance(state, Mapping) or state.get("representation") != "OCCUPATION_PROFILE":
            raise PNVSourceHolonomyError("carrier.from_occupation requires OCCUPATION_PROFILE state")
        state_q0 = _positive(state.get("q0"), "q0")
        if state_q0 != q0_exact:
            raise PNVSourceHolonomyError("occupation state q0 mismatches admitted loop q0")
        n_cells = _finite_vector(state.get("n_cells"), "occupation cells", nonnegative=True)
        cells = [q0_exact * value for value in n_cells]
        return {
            "schema": "PNCS_EXTENSIVE_CARRIER_STATE_V0_1",
            "representation": "EXTENSIVE_CARRIER",
            "Q_cells": cells,
            "Q_total": math.fsum(cells),
        }

    return transform


def build_q0_occupation_loop(
    extensive_gate: Kaku,
    occupation_gate: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
) -> InformationHolonomyLoop:
    _same_basis(extensive_gate, occupation_gate)
    refs = tuple(str(ref) for ref in evidence_refs)
    return InformationHolonomyLoop(
        loop_id="SOURCE.CARRIER.Q0_OCCUPATION.ROUNDTRIP",
        nodes=(
            LawFrameNode("LAW.RFC.CARRIER_EXTENSIVE", "RFC", extensive_gate, refs),
            LawFrameNode("LAW.CARRIER.QUANTIZED_OCCUPATION", "CARRIER_QUANTIZATION", occupation_gate, refs),
        ),
        transports=(
            LawTransport("EDGE.Q_TO_N", extensive_gate.kaku_id, occupation_gate.kaku_id, "carrier.to_occupation"),
            LawTransport("EDGE.N_TO_Q", occupation_gate.kaku_id, extensive_gate.kaku_id, "carrier.from_occupation"),
        ),
        invariants=(HolonomyInvariant("SOURCE.TOTAL_Q", "ABS", 0.0),),
        evidence_refs=(*refs, "gate:q0:CONDITIONAL"),
    )


def q0_occupation_transforms(q0: float) -> Mapping[str, Callable[[Any], Any]]:
    q0_exact = _positive(q0, "q0")
    return {
        "carrier.to_occupation": _to_occupation(q0_exact),
        "carrier.from_occupation": _from_occupation(q0_exact),
    }


def q0_occupation_invariants() -> Mapping[str, Callable[[Any], Any]]:
    return {"SOURCE.TOTAL_Q": carrier_total_invariant}


def make_current_density_state(j_q: Sequence[Any]) -> dict[str, Any]:
    values = _finite_vector(j_q, "j_Q")
    return {
        "schema": "PNCS_CARRIER_CURRENT_DENSITY_STATE_V0_1",
        "representation": "CARRIER_CURRENT_DENSITY",
        "j_Q": values,
    }


def _to_mass_density(epsilon_q: float, c_light: float) -> Callable[[Any], dict[str, Any]]:
    epsilon = _positive(epsilon_q, "epsilon_Q")
    c = _positive(c_light, "c")
    factor = epsilon / (c * c)

    def transform(state: Any) -> dict[str, Any]:
        if not isinstance(state, Mapping) or state.get("representation") != "CARRIER_CURRENT_DENSITY":
            raise PNVSourceHolonomyError("source.to_mass_density requires CARRIER_CURRENT_DENSITY state")
        j = _finite_vector(state.get("j_Q"), "j_Q")
        return {
            "schema": "PNCS_PHYSICAL_SOURCE_DENSITY_STATE_V0_1",
            "representation": "PHYSICAL_SOURCE_DENSITY",
            "rho_Q": [factor * value for value in j],
            "epsilon_Q": epsilon,
            "c": c,
        }

    return transform


def _from_mass_density(epsilon_q: float, c_light: float) -> Callable[[Any], dict[str, Any]]:
    epsilon = _positive(epsilon_q, "epsilon_Q")
    c = _positive(c_light, "c")
    factor = (c * c) / epsilon

    def transform(state: Any) -> dict[str, Any]:
        if not isinstance(state, Mapping) or state.get("representation") != "PHYSICAL_SOURCE_DENSITY":
            raise PNVSourceHolonomyError("source.from_mass_density requires PHYSICAL_SOURCE_DENSITY state")
        if _positive(state.get("epsilon_Q"), "epsilon_Q") != epsilon or _positive(state.get("c"), "c") != c:
            raise PNVSourceHolonomyError("mass-density state normalization mismatches admitted epsilon_Q/c")
        rho = _finite_vector(state.get("rho_Q"), "rho_Q")
        return {
            "schema": "PNCS_CARRIER_CURRENT_DENSITY_STATE_V0_1",
            "representation": "CARRIER_CURRENT_DENSITY",
            "j_Q": [factor * value for value in rho],
        }

    return transform


def equivalent_current_norm(state: Any) -> float:
    if not isinstance(state, Mapping):
        raise PNVSourceHolonomyError("source state mapping required")
    representation = state.get("representation")
    if representation == "CARRIER_CURRENT_DENSITY":
        return math.fsum(abs(value) for value in _finite_vector(state.get("j_Q"), "j_Q"))
    if representation == "PHYSICAL_SOURCE_DENSITY":
        epsilon = _positive(state.get("epsilon_Q"), "epsilon_Q")
        c = _positive(state.get("c"), "c")
        rho = _finite_vector(state.get("rho_Q"), "rho_Q")
        return math.fsum(abs((c * c / epsilon) * value) for value in rho)
    raise PNVSourceHolonomyError(f"unsupported source representation: {representation}")


def build_epsilon_source_loop(
    current_gate: Kaku,
    mass_density_gate: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
) -> InformationHolonomyLoop:
    _same_basis(current_gate, mass_density_gate)
    refs = tuple(str(ref) for ref in evidence_refs)
    return InformationHolonomyLoop(
        loop_id="SOURCE.CARRIER.EPSILON_MASS_DENSITY.ROUNDTRIP",
        nodes=(
            LawFrameNode("LAW.CARRIER.CURRENT_DENSITY", "IDT_RFC_INTERFACE", current_gate, refs),
            LawFrameNode("LAW.RFC.PHYSICAL_SOURCE_DENSITY", "RFC", mass_density_gate, refs),
        ),
        transports=(
            LawTransport("EDGE.J_TO_RHO", current_gate.kaku_id, mass_density_gate.kaku_id, "source.to_mass_density"),
            LawTransport("EDGE.RHO_TO_J", mass_density_gate.kaku_id, current_gate.kaku_id, "source.from_mass_density"),
        ),
        invariants=(HolonomyInvariant("SOURCE.EQUIVALENT_CURRENT_NORM", "ABS", 1e-12),),
        evidence_refs=(*refs, "gate:epsilon_Q:CONDITIONAL"),
    )


def epsilon_source_transforms(
    epsilon_q: float,
    *,
    c_light: float = C_LIGHT_EXACT,
) -> Mapping[str, Callable[[Any], Any]]:
    epsilon = _positive(epsilon_q, "epsilon_Q")
    c = _positive(c_light, "c")
    return {
        "source.to_mass_density": _to_mass_density(epsilon, c),
        "source.from_mass_density": _from_mass_density(epsilon, c),
    }


def epsilon_source_invariants() -> Mapping[str, Callable[[Any], Any]]:
    return {"SOURCE.EQUIVALENT_CURRENT_NORM": equivalent_current_norm}
