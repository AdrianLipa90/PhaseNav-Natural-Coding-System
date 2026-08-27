from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from .gremlin_pnv_holonomy_v01 import (
    HolonomyInvariant,
    InformationHolonomyLoop,
    LawFrameNode,
    LawTransport,
    PNVInformationHolonomyError,
    information_transport_connection,
)
from .model import Kaku, Vector36

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
        raise PNVSourceHolonomyError(f"{field} must be positive")
    return out


def _nonnegative(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out < 0.0:
        raise PNVSourceHolonomyError(f"{field} must be non-negative")
    return out


def _vector36(seed: float, basis_id: str) -> Vector36:
    offset = _finite(seed, "seed")
    return Vector36(tuple(offset + i / 1000.0 for i in range(36)), basis_id)


def _phase36(seed: float) -> tuple[float, ...]:
    offset = _finite(seed, "phase seed")
    return tuple((offset + i / 360.0) % (2.0 * math.pi) for i in range(36))


def _law_kaku(kaku_id: str, basis_id: str, seed: float, role: str) -> Kaku:
    return Kaku(
        kaku_id=kaku_id,
        vector=_vector36(seed, basis_id),
        semantic_mass=abs(seed) + 1.0,
        direction="FORWARD",
        polarity=1.0,
        role=role,
        phase=_phase36(seed),
    )


def _refs(values: Sequence[str]) -> tuple[str, ...]:
    out = tuple(str(value) for value in values if str(value))
    if not out:
        raise PNVSourceHolonomyError("source holonomy loop requires evidence_refs")
    return out


def _source_connection(state_space_id: str, refs: Sequence[str]):
    evidence = _refs(refs)
    return information_transport_connection(
        state_space_id,
        evidence_refs=tuple(
            sorted(
                set(
                    (
                        *evidence,
                        f"source_holonomy_contract:{SOURCE_HOLONOMY_CONTRACT}",
                    )
                )
            )
        ),
    )


def make_extensive_carrier_state(
    charges: Sequence[float],
    *,
    q_total: float | None = None,
) -> dict[str, Any]:
    q = [_nonnegative(value, "carrier charge") for value in charges]
    if not q:
        raise PNVSourceHolonomyError("carrier state requires at least one charge")
    total = sum(q) if q_total is None else _positive(q_total, "q_total")
    if abs(sum(q) - total) > 1e-12 * max(1.0, total):
        raise PNVSourceHolonomyError("q_total must equal the extensive carrier sum")
    return {
        "state_schema": "PNCS_EXTENSIVE_CARRIER_STATE_V0_1",
        "q": q,
        "q_total": total,
    }


def carrier_normalize(state: Mapping[str, Any]) -> dict[str, Any]:
    q = [_nonnegative(value, "carrier charge") for value in state.get("q", [])]
    total = _positive(state.get("q_total"), "q_total")
    if abs(sum(q) - total) > 1e-12 * max(1.0, total):
        raise PNVSourceHolonomyError("carrier normalization requires conserved extensive total")
    return {
        **dict(state),
        "p": [value / total for value in q],
    }


def carrier_reconstruct(state: Mapping[str, Any]) -> dict[str, Any]:
    p = [_nonnegative(value, "carrier probability") for value in state.get("p", [])]
    total = _positive(state.get("q_total"), "q_total")
    if abs(sum(p) - 1.0) > 1e-12:
        raise PNVSourceHolonomyError("normalized carrier profile must sum to one")
    return make_extensive_carrier_state([total * value for value in p], q_total=total)


def carrier_normalization_transforms() -> dict[str, Any]:
    return {
        "carrier_normalize": carrier_normalize,
        "carrier_reconstruct": carrier_reconstruct,
    }


def carrier_normalization_invariants() -> dict[str, Any]:
    return {
        "CARRIER_TOTAL": lambda state: _positive(state.get("q_total"), "q_total"),
    }


def build_carrier_normalization_loop(
    *,
    basis_id: str,
    evidence_refs: Sequence[str],
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    refs = _refs(evidence_refs)
    eps = _nonnegative(tolerance, "tolerance")
    node_extensive = LawFrameNode(
        "LAW.CARRIER.EXTENSIVE",
        "RFC_SOURCE_CARRIER",
        _law_kaku("LAW.CARRIER.EXTENSIVE", basis_id, 0.11, "law_gate:carrier_extensive"),
        refs,
    )
    node_normalized = LawFrameNode(
        "LAW.IDT.NORMALIZED_PROFILE",
        "IDT",
        _law_kaku("LAW.IDT.NORMALIZED_PROFILE", basis_id, 0.12, "law_gate:idt_normalized_profile"),
        refs,
    )
    return InformationHolonomyLoop(
        loop_id="PNV_SOURCE_CARRIER_NORMALIZATION_LOOP_V0_1",
        connection=_source_connection("PNCS_EXTENSIVE_NORMALIZED_CARRIER_STATE_V0_1", (*refs, "connection:source-carrier-normalization")),
        nodes=(node_extensive, node_normalized),
        transports=(
            LawTransport(
                "EDGE.CARRIER.NORMALIZE",
                node_extensive.node_id,
                node_normalized.node_id,
                "carrier_normalize",
                refs,
            ),
            LawTransport(
                "EDGE.CARRIER.RECONSTRUCT",
                node_normalized.node_id,
                node_extensive.node_id,
                "carrier_reconstruct",
                refs,
            ),
        ),
        invariants=(HolonomyInvariant("CARRIER_TOTAL", "ABS", eps),),
        evidence_refs=refs,
    )


def q0_to_occupation(state: Mapping[str, Any]) -> dict[str, Any]:
    q0 = _positive(state.get("q0"), "q0")
    q = [_nonnegative(value, "carrier charge") for value in state.get("q", [])]
    return {
        **dict(state),
        "n": [value / q0 for value in q],
    }


def q0_from_occupation(state: Mapping[str, Any]) -> dict[str, Any]:
    q0 = _positive(state.get("q0"), "q0")
    n = [_nonnegative(value, "occupation") for value in state.get("n", [])]
    return {
        "state_schema": "PNCS_EXTENSIVE_CARRIER_STATE_V0_1",
        "q": [q0 * value for value in n],
        "q_total": _positive(state.get("q_total"), "q_total"),
        "q0": q0,
    }


def q0_occupation_transforms() -> dict[str, Any]:
    return {
        "carrier_to_occupation_q0": q0_to_occupation,
        "occupation_to_carrier_q0": q0_from_occupation,
    }


def q0_occupation_invariants() -> dict[str, Any]:
    return {
        "CARRIER_TOTAL": lambda state: _positive(state.get("q_total"), "q_total"),
        "CARRIER_QUANTUM_Q0": lambda state: _positive(state.get("q0"), "q0"),
    }


def build_q0_occupation_loop(
    *,
    basis_id: str,
    evidence_refs: Sequence[str],
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    refs = _refs(evidence_refs)
    eps = _nonnegative(tolerance, "tolerance")
    node_carrier = LawFrameNode(
        "LAW.CARRIER.Q",
        "RFC_SOURCE_CARRIER",
        _law_kaku("LAW.CARRIER.Q", basis_id, 0.21, "law_gate:carrier_q"),
        (*refs, "gate:q0:CONDITIONAL"),
    )
    node_occupation = LawFrameNode(
        "LAW.CARRIER.OCCUPATION_Q0",
        "PHASE_TIME_HAMILTONIAN",
        _law_kaku("LAW.CARRIER.OCCUPATION_Q0", basis_id, 0.22, "law_gate:occupation_q0"),
        (*refs, "gate:q0:CONDITIONAL"),
    )
    return InformationHolonomyLoop(
        loop_id="PNV_SOURCE_Q0_OCCUPATION_LOOP_V0_1",
        connection=_source_connection("PNCS_CARRIER_OCCUPATION_STATE_SPACE_V0_1", (*refs, "gate:q0:CONDITIONAL")),
        nodes=(node_carrier, node_occupation),
        transports=(
            LawTransport(
                "EDGE.Q.Q0_TO_N",
                node_carrier.node_id,
                node_occupation.node_id,
                "carrier_to_occupation_q0",
                (*refs, "gate:q0:CONDITIONAL"),
            ),
            LawTransport(
                "EDGE.N.Q0_TO_Q",
                node_occupation.node_id,
                node_carrier.node_id,
                "occupation_to_carrier_q0",
                (*refs, "gate:q0:CONDITIONAL"),
            ),
        ),
        invariants=(
            HolonomyInvariant("CARRIER_TOTAL", "ABS", eps),
            HolonomyInvariant("CARRIER_QUANTUM_Q0", "ABS", eps),
        ),
        evidence_refs=(*refs, "gate:q0:CONDITIONAL"),
    )


def make_current_density_state(
    j_q: Sequence[float],
    *,
    epsilon_q: float,
    c: float = C_LIGHT_EXACT,
) -> dict[str, Any]:
    current = [_finite(value, "j_q") for value in j_q]
    if not current:
        raise PNVSourceHolonomyError("current-density state requires at least one j_q value")
    return {
        "state_schema": "PNCS_CARRIER_CURRENT_DENSITY_STATE_V0_1",
        "j_q": current,
        "epsilon_q": _positive(epsilon_q, "epsilon_q"),
        "c": _positive(c, "c"),
    }


def epsilon_to_mass_density(state: Mapping[str, Any]) -> dict[str, Any]:
    epsilon_q = _positive(state.get("epsilon_q"), "epsilon_q")
    c = _positive(state.get("c"), "c")
    current = [_finite(value, "j_q") for value in state.get("j_q", [])]
    return {
        **dict(state),
        "rho_q": [(epsilon_q / (c * c)) * value for value in current],
    }


def epsilon_from_mass_density(state: Mapping[str, Any]) -> dict[str, Any]:
    epsilon_q = _positive(state.get("epsilon_q"), "epsilon_q")
    c = _positive(state.get("c"), "c")
    rho_q = [_finite(value, "rho_q") for value in state.get("rho_q", [])]
    return make_current_density_state(
        [(c * c / epsilon_q) * value for value in rho_q],
        epsilon_q=epsilon_q,
        c=c,
    )


def epsilon_source_transforms() -> dict[str, Any]:
    return {
        "carrier_current_to_mass_density": epsilon_to_mass_density,
        "mass_density_to_carrier_current": epsilon_from_mass_density,
    }


def epsilon_source_invariants() -> dict[str, Any]:
    return {
        "SOURCE_MASS_DENSITY": lambda state: sum(
            (state.get("rho_q") or [
                (_positive(state.get("epsilon_q"), "epsilon_q") / (_positive(state.get("c"), "c") ** 2))
                * _finite(value, "j_q")
                for value in state.get("j_q", [])
            ])
        ),
        "SOURCE_ENERGY_PER_CHARGE": lambda state: _positive(state.get("epsilon_q"), "epsilon_q"),
    }


def build_epsilon_source_loop(
    *,
    basis_id: str,
    evidence_refs: Sequence[str],
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    refs = _refs(evidence_refs)
    eps = _nonnegative(tolerance, "tolerance")
    node_current = LawFrameNode(
        "LAW.CARRIER.CURRENT_DENSITY",
        "RFC_SOURCE_CARRIER",
        _law_kaku("LAW.CARRIER.CURRENT_DENSITY", basis_id, 0.31, "law_gate:carrier_current_density"),
        (*refs, "gate:epsilon_Q:CONDITIONAL"),
    )
    node_mass_density = LawFrameNode(
        "LAW.RFC.MASS_DENSITY_FROM_EPSILON_Q",
        "RFC_SOURCE_TYPE",
        _law_kaku(
            "LAW.RFC.MASS_DENSITY_FROM_EPSILON_Q",
            basis_id,
            0.32,
            "law_gate:mass_density_epsilon_q",
        ),
        (*refs, "gate:epsilon_Q:CONDITIONAL"),
    )
    return InformationHolonomyLoop(
        loop_id="PNV_SOURCE_EPSILON_Q_LOOP_V0_1",
        connection=_source_connection("PNCS_CARRIER_SOURCE_DENSITY_STATE_SPACE_V0_1", (*refs, "gate:epsilon_Q:CONDITIONAL")),
        nodes=(node_current, node_mass_density),
        transports=(
            LawTransport(
                "EDGE.JQ.EPSILON_TO_RHO",
                node_current.node_id,
                node_mass_density.node_id,
                "carrier_current_to_mass_density",
                (*refs, "gate:epsilon_Q:CONDITIONAL"),
            ),
            LawTransport(
                "EDGE.RHO.EPSILON_TO_JQ",
                node_mass_density.node_id,
                node_current.node_id,
                "mass_density_to_carrier_current",
                (*refs, "gate:epsilon_Q:CONDITIONAL"),
            ),
        ),
        invariants=(
            HolonomyInvariant("SOURCE_MASS_DENSITY", "ABS", eps),
            HolonomyInvariant("SOURCE_ENERGY_PER_CHARGE", "ABS", eps),
        ),
        evidence_refs=(*refs, "gate:epsilon_Q:CONDITIONAL"),
    )
