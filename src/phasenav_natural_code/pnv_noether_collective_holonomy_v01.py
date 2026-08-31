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
from .model import Kaku
from .pnv_holonomy_numeric_v01 import (
    checked_abs_difference_ratio,
    checked_difference,
    checked_product,
    checked_ratio,
    finite_float,
    finite_tree,
)

NOETHER_COLLECTIVE_CONTRACT = "PNCS_PNV_NOETHER_COLLECTIVE_CARRIER_V0_1"
NOETHER_COLLECTIVE_LOOP_ID = "SOURCE.PHASE_NOETHER.COLLECTIVE_CARRIER.ROUNDTRIP"


class PNVNoetherCollectiveError(PNVInformationHolonomyError):
    pass


def _finite(value: Any, field: str) -> float:
    return finite_float(value, field, PNVNoetherCollectiveError)


def _positive(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out <= 0.0:
        raise PNVNoetherCollectiveError(f"{field} must be positive")
    return out


def _nonnegative(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out < 0.0:
        raise PNVNoetherCollectiveError(f"{field} must be non-negative")
    return out


def _refs(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(value) for value in values if str(value)}))


def make_noether_collective_state(
    *,
    D: int,
    epsilon_eb: float,
    theta_i_eb: float,
    hbar: float,
    j_total: float,
    i_phi: float,
    i_a: float,
) -> dict[str, Any]:
    if isinstance(D, bool):
        raise PNVNoetherCollectiveError("Euler sector D must be integer")
    try:
        d_int = int(D)
    except (TypeError, ValueError, OverflowError) as exc:
        raise PNVNoetherCollectiveError("Euler sector D must be integer") from exc
    if d_int != D:
        raise PNVNoetherCollectiveError("Euler sector D must be integer")
    return {
        "schema": "PNCS_NOETHER_COLLECTIVE_CARRIER_STATE_V0_1",
        "representation": "EULER_CLOSED_ROTOR_INPUT",
        "D": d_int,
        "epsilon_EB": _finite(epsilon_eb, "epsilon_EB"),
        "theta_I_EB": _finite(theta_i_eb, "theta_I_EB"),
        "hbar": _positive(hbar, "hbar"),
        "J_total": _finite(j_total, "J_total"),
        "I_phi": _positive(i_phi, "I_phi"),
        "I_A": _positive(i_a, "I_A"),
    }


def _derived(state: Mapping[str, Any]) -> dict[str, float]:
    hbar = _positive(state.get("hbar"), "hbar")
    theta = _finite(state.get("theta_I_EB"), "theta_I_EB")
    j_total = _finite(state.get("J_total"), "J_total")
    i_phi = _positive(state.get("I_phi"), "I_phi")
    i_a = _positive(state.get("I_A"), "I_A")

    j_i = checked_product(
        hbar,
        theta,
        field="J_I_EB",
        error_type=PNVNoetherCollectiveError,
    )
    p_phi = checked_difference(
        j_total,
        j_i,
        "P_Phi_EB",
        PNVNoetherCollectiveError,
    )
    if p_phi <= 0.0:
        raise PNVNoetherCollectiveError("positive rotor carrier P_Phi is required")
    phase_rate = checked_ratio(
        p_phi,
        i_phi,
        "phase_rate",
        PNVNoetherCollectiveError,
    )
    q_theta = checked_product(
        i_a,
        phase_rate,
        field="Q_theta",
        error_type=PNVNoetherCollectiveError,
    )
    if q_theta <= 0.0:
        raise PNVNoetherCollectiveError("positive finite Noether charge Q_theta is required")
    p_phi_sq = checked_product(
        p_phi,
        p_phi,
        field="P_Phi_EB_squared",
        error_type=PNVNoetherCollectiveError,
    )
    two_i_phi = checked_product(
        2.0,
        i_phi,
        field="2I_phi",
        error_type=PNVNoetherCollectiveError,
    )
    h_phi = checked_ratio(
        p_phi_sq,
        two_i_phi,
        "H_Phi_EB",
        PNVNoetherCollectiveError,
    )
    epsilon_n = checked_ratio(
        h_phi,
        q_theta,
        "epsilon_N_EB",
        PNVNoetherCollectiveError,
    )
    delta_i = checked_abs_difference_ratio(
        q_theta,
        p_phi,
        p_phi,
        "Delta_I",
        PNVNoetherCollectiveError,
    )
    return finite_tree(
        {
            "J_I_EB": j_i,
            "P_Phi_EB": p_phi,
            "phase_rate": phase_rate,
            "Q_theta": q_theta,
            "H_Phi_EB": h_phi,
            "epsilon_N_EB": epsilon_n,
            "Delta_I": delta_i,
        },
        "noether_collective_derived",
        PNVNoetherCollectiveError,
    )


def collective_noether_binding_defect(state: Mapping[str, Any]) -> float:
    if "Delta_I" in state:
        return _nonnegative(state["Delta_I"], "Delta_I")
    return _derived(state)["Delta_I"]


def noether_collective_transforms(*, binding_tolerance: float = 1e-12) -> dict[str, Any]:
    tol = _nonnegative(binding_tolerance, "binding_tolerance")

    def resolve_rotor_carrier(state: Mapping[str, Any]) -> dict[str, Any]:
        values = _derived(state)
        return {
            **dict(state),
            **values,
            "representation": "COLLECTIVE_NOETHER_CARRIER",
        }

    def bind_rfc_carrier(state: Mapping[str, Any]) -> dict[str, Any]:
        values = _derived(state)
        for key, expected in values.items():
            observed = _finite(state.get(key), key)
            if not math.isclose(observed, expected, rel_tol=1e-12, abs_tol=1e-15):
                raise PNVNoetherCollectiveError(f"{key} changed before RFC carrier binding")
        if values["Delta_I"] > tol:
            raise PNVNoetherCollectiveError(
                f"Noether/rotor inertia binding defect {values['Delta_I']!r} exceeds tolerance {tol!r}"
            )
        return {
            **dict(state),
            "representation": "RFC_BOUND_NOETHER_CARRIER",
            "Q_RFC": values["Q_theta"],
            "epsilon_Q_candidate": values["epsilon_N_EB"],
        }

    def reconstruct_rotor_input(state: Mapping[str, Any]) -> dict[str, Any]:
        values = _derived(state)
        if values["Delta_I"] > tol:
            raise PNVNoetherCollectiveError(
                f"Noether/rotor inertia binding defect {values['Delta_I']!r} exceeds tolerance {tol!r}"
            )
        q_rfc = _positive(state.get("Q_RFC"), "Q_RFC")
        epsilon_q = _positive(state.get("epsilon_Q_candidate"), "epsilon_Q_candidate")
        if not math.isclose(q_rfc, values["Q_theta"], rel_tol=1e-12, abs_tol=1e-15):
            raise PNVNoetherCollectiveError("RFC carrier failed reverse Noether audit")
        if not math.isclose(epsilon_q, values["epsilon_N_EB"], rel_tol=1e-12, abs_tol=1e-15):
            raise PNVNoetherCollectiveError("RFC epsilon candidate failed reverse Noether audit")
        return {
            "schema": "PNCS_NOETHER_COLLECTIVE_CARRIER_STATE_V0_1",
            "representation": "EULER_CLOSED_ROTOR_INPUT",
            "D": int(state["D"]),
            "epsilon_EB": _finite(state["epsilon_EB"], "epsilon_EB"),
            "theta_I_EB": _finite(state["theta_I_EB"], "theta_I_EB"),
            "hbar": _positive(state["hbar"], "hbar"),
            "J_total": _finite(state["J_total"], "J_total"),
            "I_phi": _positive(state["I_phi"], "I_phi"),
            "I_A": _positive(state["I_A"], "I_A"),
        }

    return {
        "noether.resolve_rotor_carrier": resolve_rotor_carrier,
        "noether.bind_rfc_carrier": bind_rfc_carrier,
        "noether.reconstruct_rotor_input": reconstruct_rotor_input,
    }


def _euler_sector(state: Mapping[str, Any]) -> tuple[int, float, float]:
    return (
        int(state["D"]),
        _finite(state.get("epsilon_EB"), "epsilon_EB"),
        _finite(state.get("theta_I_EB"), "theta_I_EB"),
    )


def _rotor_charge(state: Mapping[str, Any]) -> float:
    if "P_Phi_EB" in state:
        return _positive(state["P_Phi_EB"], "P_Phi_EB")
    return _derived(state)["P_Phi_EB"]


def _noether_charge(state: Mapping[str, Any]) -> float:
    if "Q_theta" in state:
        return _positive(state["Q_theta"], "Q_theta")
    return _derived(state)["Q_theta"]


def _rotor_energy(state: Mapping[str, Any]) -> float:
    if "H_Phi_EB" in state:
        return _positive(state["H_Phi_EB"], "H_Phi_EB")
    return _derived(state)["H_Phi_EB"]


def _epsilon_noether(state: Mapping[str, Any]) -> float:
    if "epsilon_N_EB" in state:
        return _positive(state["epsilon_N_EB"], "epsilon_N_EB")
    return _derived(state)["epsilon_N_EB"]


def noether_collective_invariants() -> dict[str, Any]:
    return {
        "SOURCE.EULER_CLOSURE_SECTOR": _euler_sector,
        "SOURCE.ROTOR_KINETIC_CHARGE": _rotor_charge,
        "SOURCE.NOETHER_FINITE_CHARGE": _noether_charge,
        "SOURCE.ROTOR_PHASE_ENERGY": _rotor_energy,
        "SOURCE.NOETHER_ENERGY_PER_CHARGE": _epsilon_noether,
        "SOURCE.NOETHER_INERTIA_BINDING_DEFECT": collective_noether_binding_defect,
    }


def build_noether_collective_loop(
    rotor_kaku: Kaku,
    noether_kaku: Kaku,
    rfc_kaku: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    if not all(isinstance(item, Kaku) for item in (rotor_kaku, noether_kaku, rfc_kaku)):
        raise PNVNoetherCollectiveError("Noether collective law gates require Kaku")
    tol = _nonnegative(tolerance, "tolerance")
    refs = _refs(
        (
            *evidence_refs,
            f"contract:{NOETHER_COLLECTIVE_CONTRACT}",
            "gate:collective_phase_rate:CONDITIONAL",
            "gate:I_A_to_I_phi:CONDITIONAL",
            "gate:Q_Sigma_to_Q_theta:OPEN",
        )
    )
    rotor = LawFrameNode("LAW.PHASE.ROTOR_KINETIC_CHARGE", "PHASE_TIME_HAMILTONIAN", rotor_kaku, refs)
    noether = LawFrameNode("LAW.NOETHER.COLLECTIVE_PHASE_CHARGE", "EULER_NOETHER_FIELD", noether_kaku, refs)
    rfc = LawFrameNode("LAW.RFC.CONSERVED_CARRIER_CANDIDATE", "RFC_SOURCE_CARRIER", rfc_kaku, refs)
    connection = information_transport_connection(
        "PNCS_NOETHER_COLLECTIVE_CARRIER_STATE_SPACE_V0_1",
        evidence_refs=refs,
    )
    return InformationHolonomyLoop(
        loop_id=NOETHER_COLLECTIVE_LOOP_ID,
        connection=connection,
        nodes=(rotor, noether, rfc),
        transports=(
            LawTransport(
                "EDGE.ROTOR.TO_NOETHER_CHARGE",
                rotor.node_id,
                noether.node_id,
                "noether.resolve_rotor_carrier",
                refs,
            ),
            LawTransport(
                "EDGE.NOETHER.TO_RFC_CARRIER",
                noether.node_id,
                rfc.node_id,
                "noether.bind_rfc_carrier",
                refs,
            ),
            LawTransport(
                "EDGE.RFC.TO_ROTOR_INPUT",
                rfc.node_id,
                rotor.node_id,
                "noether.reconstruct_rotor_input",
                refs,
            ),
        ),
        invariants=(
            HolonomyInvariant("SOURCE.EULER_CLOSURE_SECTOR", "EXACT", 0.0),
            HolonomyInvariant("SOURCE.ROTOR_KINETIC_CHARGE", "ABS", tol),
            HolonomyInvariant("SOURCE.NOETHER_FINITE_CHARGE", "ABS", tol),
            HolonomyInvariant("SOURCE.ROTOR_PHASE_ENERGY", "ABS", tol),
            HolonomyInvariant("SOURCE.NOETHER_ENERGY_PER_CHARGE", "ABS", tol),
            HolonomyInvariant("SOURCE.NOETHER_INERTIA_BINDING_DEFECT", "ABS", tol),
        ),
        evidence_refs=refs,
    )
