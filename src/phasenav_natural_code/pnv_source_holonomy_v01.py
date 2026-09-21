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


def _strictly_positive(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out <= 0.0:
        raise PNVSourceHolonomyError(f"{field} must be strictly positive")
    return out


def _nonnegative(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out < 0.0:
        raise PNVSourceHolonomyError(f"{field} must be non-negative")
    return out


def _refs(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(value) for value in values if str(value)}))


def _connection(state_space_id: str, evidence_refs: Sequence[str]):
    return information_transport_connection(
        state_space_id,
        evidence_refs=tuple(
            sorted(
                set(
                    (
                        *_refs(evidence_refs),
                        f"source_holonomy_contract:{SOURCE_HOLONOMY_CONTRACT}",
                    )
                )
            )
        ),
    )


def _law_node(law_id: str, domain: str, kaku: Kaku, evidence_refs: Sequence[str]) -> LawFrameNode:
    if not isinstance(kaku, Kaku):
        raise PNVSourceHolonomyError("source holonomy law gate requires Kaku")
    return LawFrameNode(law_id, domain, kaku, _refs(evidence_refs))


def _require_common_basis(*kakus: Kaku) -> None:
    if not kakus or any(not isinstance(kaku, Kaku) for kaku in kakus):
        raise PNVSourceHolonomyError("source holonomy law gate requires Kaku")
    basis_ids = {kaku.vector.basis_id for kaku in kakus}
    if len(basis_ids) != 1:
        raise PNVSourceHolonomyError(
            "law-frame KAKU nodes must share one exact PNCS basis"
        )


# ---------------------------------------------------------------------------
# 1. Extensive carrier <-> normalized profile
# ---------------------------------------------------------------------------


def make_extensive_carrier_state(charges: Sequence[float]) -> dict[str, Any]:
    cells = [_nonnegative(value, "Q cell") for value in charges]
    if not cells:
        raise PNVSourceHolonomyError("carrier state requires at least one Q cell")
    total = sum(cells)
    if total <= 0.0:
        raise PNVSourceHolonomyError("Q_total > 0 is required")
    return {
        "schema": "PNCS_EXTENSIVE_CARRIER_STATE_V0_1",
        "representation": "EXTENSIVE_CARRIER",
        "Q_cells": cells,
        "Q_total": total,
    }


def _carrier_normalize(state: Mapping[str, Any]) -> dict[str, Any]:
    cells = [_nonnegative(value, "Q cell") for value in state.get("Q_cells", ())]
    total = _strictly_positive(state.get("Q_total"), "Q_total")
    if not cells or not math.isclose(sum(cells), total, rel_tol=1e-12, abs_tol=1e-15):
        raise PNVSourceHolonomyError("extensive carrier total mismatch")
    return {
        "schema": "PNCS_NORMALIZED_CARRIER_STATE_V0_1",
        "representation": "NORMALIZED_PROFILE",
        "p_cells": [value / total for value in cells],
        "Q_total": total,
    }


def _carrier_reconstruct(state: Mapping[str, Any]) -> dict[str, Any]:
    profile = [_nonnegative(value, "p cell") for value in state.get("p_cells", ())]
    total = _strictly_positive(state.get("Q_total"), "Q_total")
    if not profile or not math.isclose(sum(profile), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise PNVSourceHolonomyError("normalized carrier profile must sum to one")
    return {
        "schema": "PNCS_EXTENSIVE_CARRIER_STATE_V0_1",
        "representation": "EXTENSIVE_CARRIER",
        "Q_cells": [total * value for value in profile],
        "Q_total": total,
    }


def carrier_normalization_transforms() -> dict[str, Any]:
    return {
        "carrier.normalize_profile": _carrier_normalize,
        "carrier.reconstruct_extensive": _carrier_reconstruct,
    }


def _equivalent_total_q(state: Mapping[str, Any]) -> float:
    return _strictly_positive(state.get("Q_total"), "Q_total")


def _equivalent_profile_norm(state: Mapping[str, Any]) -> float:
    if "p_cells" in state:
        return sum(_nonnegative(value, "p cell") for value in state["p_cells"])
    cells = [_nonnegative(value, "Q cell") for value in state.get("Q_cells", ())]
    total = _strictly_positive(state.get("Q_total"), "Q_total")
    return sum(cells) / total


def carrier_normalization_invariants() -> dict[str, Any]:
    return {
        "SOURCE.TOTAL_Q": _equivalent_total_q,
        "SOURCE.PROFILE_NORM": _equivalent_profile_norm,
    }


def build_carrier_normalization_loop(
    extensive_kaku: Kaku,
    normalized_kaku: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    _require_common_basis(extensive_kaku, normalized_kaku)
    eps = _nonnegative(tolerance, "tolerance")
    refs = _refs(evidence_refs)
    extensive = _law_node("LAW.RFC.CARRIER_EXTENSIVE", "RFC", extensive_kaku, refs)
    normalized = _law_node("LAW.IDT.NORMALIZED_PROFILE", "IDT", normalized_kaku, refs)
    return InformationHolonomyLoop(
        loop_id="PNV_SOURCE_CARRIER_NORMALIZATION_LOOP_V0_1",
        connection=_connection("PNCS_EXTENSIVE_NORMALIZED_CARRIER_STATE_V0_1", refs),
        nodes=(extensive, normalized),
        transports=(
            LawTransport(
                "EDGE.CARRIER.NORMALIZE",
                extensive.node_id,
                normalized.node_id,
                "carrier.normalize_profile",
                refs,
            ),
            LawTransport(
                "EDGE.CARRIER.RECONSTRUCT",
                normalized.node_id,
                extensive.node_id,
                "carrier.reconstruct_extensive",
                refs,
            ),
        ),
        invariants=(
            HolonomyInvariant("SOURCE.TOTAL_Q", "ABS", eps),
            HolonomyInvariant("SOURCE.PROFILE_NORM", "ABS", eps),
        ),
        evidence_refs=refs,
    )


# ---------------------------------------------------------------------------
# 2. Conditional q0 occupation
# ---------------------------------------------------------------------------


def q0_occupation_transforms(q0: float) -> dict[str, Any]:
    quantum = _strictly_positive(q0, "q0")

    def to_occupation(state: Mapping[str, Any]) -> dict[str, Any]:
        cells = [_nonnegative(value, "Q cell") for value in state.get("Q_cells", ())]
        total = _strictly_positive(state.get("Q_total"), "Q_total")
        if not cells or not math.isclose(sum(cells), total, rel_tol=1e-12, abs_tol=1e-15):
            raise PNVSourceHolonomyError("extensive carrier total mismatch")
        return {
            "schema": "PNCS_CARRIER_OCCUPATION_STATE_V0_1",
            "representation": "OCCUPATION_PROFILE",
            "n_cells": [value / quantum for value in cells],
            "q0": quantum,
            "Q_total": total,
        }

    def from_occupation(state: Mapping[str, Any]) -> dict[str, Any]:
        state_q0 = _strictly_positive(state.get("q0"), "q0")
        if not math.isclose(state_q0, quantum, rel_tol=0.0, abs_tol=0.0):
            raise PNVSourceHolonomyError("q0 transport binding changed inside round trip")
        occupation = [_nonnegative(value, "occupation") for value in state.get("n_cells", ())]
        total = _strictly_positive(state.get("Q_total"), "Q_total")
        cells = [quantum * value for value in occupation]
        if not math.isclose(sum(cells), total, rel_tol=1e-12, abs_tol=1e-15):
            raise PNVSourceHolonomyError("q0 reconstruction total mismatch")
        return {
            "schema": "PNCS_EXTENSIVE_CARRIER_STATE_V0_1",
            "representation": "EXTENSIVE_CARRIER",
            "Q_cells": cells,
            "Q_total": total,
        }

    return {
        "carrier.to_occupation": to_occupation,
        "carrier.from_occupation": from_occupation,
    }


def q0_occupation_invariants() -> dict[str, Any]:
    return {"SOURCE.TOTAL_Q": _equivalent_total_q}


def build_q0_occupation_loop(
    extensive_kaku: Kaku,
    occupation_kaku: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    _require_common_basis(extensive_kaku, occupation_kaku)
    eps = _nonnegative(tolerance, "tolerance")
    refs = _refs((*evidence_refs, "gate:q0:CONDITIONAL"))
    extensive = _law_node("LAW.RFC.CARRIER_EXTENSIVE", "RFC", extensive_kaku, refs)
    occupation = _law_node("LAW.CARRIER.QUANTIZED_OCCUPATION", "PHASE_TIME_HAMILTONIAN", occupation_kaku, refs)
    return InformationHolonomyLoop(
        loop_id="PNV_SOURCE_Q0_OCCUPATION_LOOP_V0_1",
        connection=_connection("PNCS_CARRIER_OCCUPATION_STATE_SPACE_V0_1", refs),
        nodes=(extensive, occupation),
        transports=(
            LawTransport("EDGE.Q.TO_OCCUPATION", extensive.node_id, occupation.node_id, "carrier.to_occupation", refs),
            LawTransport("EDGE.N.FROM_OCCUPATION", occupation.node_id, extensive.node_id, "carrier.from_occupation", refs),
        ),
        invariants=(HolonomyInvariant("SOURCE.TOTAL_Q", "ABS", eps),),
        evidence_refs=refs,
    )


# ---------------------------------------------------------------------------
# 3. Conditional epsilon_Q current <-> mass density
# ---------------------------------------------------------------------------


def make_current_density_state(j_q: Sequence[float]) -> dict[str, Any]:
    current = [_finite(value, "j_Q") for value in j_q]
    if not current:
        raise PNVSourceHolonomyError("current-density state requires at least one j_Q value")
    return {
        "schema": "PNCS_CARRIER_CURRENT_DENSITY_STATE_V0_1",
        "representation": "CARRIER_CURRENT_DENSITY",
        "j_Q": current,
    }


def epsilon_source_transforms(epsilon_q: float, *, c_light: float = C_LIGHT_EXACT) -> dict[str, Any]:
    epsilon = _strictly_positive(epsilon_q, "epsilon_Q")
    c = _strictly_positive(c_light, "c")

    def to_mass_density(state: Mapping[str, Any]) -> dict[str, Any]:
        current = [_finite(value, "j_Q") for value in state.get("j_Q", ())]
        if not current:
            raise PNVSourceHolonomyError("current density is required")
        return {
            "schema": "PNCS_PHYSICAL_SOURCE_DENSITY_STATE_V0_1",
            "representation": "PHYSICAL_SOURCE_DENSITY",
            "rho_Q": [(epsilon / (c * c)) * value for value in current],
            "epsilon_Q": epsilon,
            "c": c,
        }

    def from_mass_density(state: Mapping[str, Any]) -> dict[str, Any]:
        state_epsilon = _strictly_positive(state.get("epsilon_Q"), "epsilon_Q")
        state_c = _strictly_positive(state.get("c"), "c")
        if not math.isclose(state_epsilon, epsilon, rel_tol=0.0, abs_tol=0.0):
            raise PNVSourceHolonomyError("epsilon_Q transport binding changed inside round trip")
        if not math.isclose(state_c, c, rel_tol=0.0, abs_tol=0.0):
            raise PNVSourceHolonomyError("c transport binding changed inside round trip")
        density = [_finite(value, "rho_Q") for value in state.get("rho_Q", ())]
        if not density:
            raise PNVSourceHolonomyError("mass density is required")
        return make_current_density_state([(c * c / epsilon) * value for value in density])

    return {
        "source.to_mass_density": to_mass_density,
        "source.from_mass_density": from_mass_density,
    }


def _equivalent_current_norm(state: Mapping[str, Any]) -> float:
    if "j_Q" in state:
        return sum(abs(_finite(value, "j_Q")) for value in state["j_Q"])
    epsilon = _strictly_positive(state.get("epsilon_Q"), "epsilon_Q")
    c = _strictly_positive(state.get("c"), "c")
    density = [_finite(value, "rho_Q") for value in state.get("rho_Q", ())]
    return sum(abs((c * c / epsilon) * value) for value in density)


def epsilon_source_invariants() -> dict[str, Any]:
    return {"SOURCE.EQUIVALENT_CURRENT_NORM": _equivalent_current_norm}


def build_epsilon_source_loop(
    current_kaku: Kaku,
    density_kaku: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    _require_common_basis(current_kaku, density_kaku)
    eps = _nonnegative(tolerance, "tolerance")
    refs = _refs((*evidence_refs, "gate:epsilon_Q:CONDITIONAL"))
    current = _law_node("LAW.CARRIER.CURRENT_DENSITY", "RFC_SOURCE_CARRIER", current_kaku, refs)
    density = _law_node("LAW.RFC.PHYSICAL_SOURCE_DENSITY", "RFC_SOURCE_TYPE", density_kaku, refs)
    return InformationHolonomyLoop(
        loop_id="PNV_SOURCE_EPSILON_Q_LOOP_V0_1",
        connection=_connection("PNCS_CARRIER_SOURCE_DENSITY_STATE_SPACE_V0_1", refs),
        nodes=(current, density),
        transports=(
            LawTransport("EDGE.JQ.TO_RHO", current.node_id, density.node_id, "source.to_mass_density", refs),
            LawTransport("EDGE.RHO.TO_JQ", density.node_id, current.node_id, "source.from_mass_density", refs),
        ),
        invariants=(HolonomyInvariant("SOURCE.EQUIVALENT_CURRENT_NORM", "ABS", eps),),
        evidence_refs=refs,
    )


# ---------------------------------------------------------------------------
# 4. Euler/Berry -> action charge -> rotor energy -> epsilon -> effective time
# ---------------------------------------------------------------------------


def make_euler_phase_intention_state(
    *,
    D: int,
    epsilon_eb: float,
    phi_ab: float,
    phi_berry: float,
    phi_euler: float,
    theta_prior: float,
    hbar: float,
    j_total: float,
    i_phi: float,
) -> dict[str, Any]:
    if isinstance(D, bool) or int(D) != D:
        raise PNVSourceHolonomyError("Euler closure sector D must be integer")
    return {
        "schema": "PNCS_EULER_PHASE_INTENTION_STATE_V0_1",
        "representation": "EULER_BERRY_CLOSURE_INPUT",
        "D": int(D),
        "epsilon_EB": _finite(epsilon_eb, "epsilon_EB"),
        "phi_AB": _finite(phi_ab, "phi_AB"),
        "phi_Berry": _finite(phi_berry, "phi_Berry"),
        "phi_Euler": _finite(phi_euler, "phi_Euler"),
        "theta_prior": _finite(theta_prior, "theta_prior"),
        "hbar": _strictly_positive(hbar, "hbar"),
        "J_total": _finite(j_total, "J_total"),
        "I_phi": _strictly_positive(i_phi, "I_phi"),
    }


def _euler_theta(state: Mapping[str, Any]) -> float:
    return (
        2.0 * math.pi * (_finite(state.get("D"), "D") + _finite(state.get("epsilon_EB"), "epsilon_EB"))
        - _finite(state.get("phi_AB"), "phi_AB")
        - _finite(state.get("phi_Berry"), "phi_Berry")
        - _finite(state.get("phi_Euler"), "phi_Euler")
        - _finite(state.get("theta_prior"), "theta_prior")
    )


def _expected_j_i(state: Mapping[str, Any]) -> float:
    return _strictly_positive(state.get("hbar"), "hbar") * _euler_theta(state)


def _expected_h_phi(state: Mapping[str, Any]) -> float:
    j_i = _expected_j_i(state)
    i_phi = _strictly_positive(state.get("I_phi"), "I_phi")
    j_total = _finite(state.get("J_total"), "J_total")
    return (j_total - j_i) ** 2 / (2.0 * i_phi)


def _expected_epsilon_i(state: Mapping[str, Any]) -> float:
    j_i = _expected_j_i(state)
    h_phi = _expected_h_phi(state)
    if j_i <= 0.0 or h_phi <= 0.0:
        raise PNVSourceHolonomyError("Euler energy-per-charge ratio requires positive non-degenerate sector")
    return h_phi / j_i


def euler_phase_intention_transforms() -> dict[str, Any]:
    def resolve_charge(state: Mapping[str, Any]) -> dict[str, Any]:
        theta_i = _euler_theta(state)
        j_i = _strictly_positive(state.get("hbar"), "hbar") * theta_i
        if j_i <= 0.0:
            raise PNVSourceHolonomyError("Euler-closed intention action charge must be positive")
        return {
            **dict(state),
            "representation": "EULER_CLOSED_ACTION_CHARGE",
            "theta_I_EB": theta_i,
            "J_I_EB": j_i,
        }

    def derive_energy(state: Mapping[str, Any]) -> dict[str, Any]:
        j_i = _finite(state.get("J_I_EB"), "J_I_EB")
        expected_j = _expected_j_i(state)
        if not math.isclose(j_i, expected_j, rel_tol=1e-12, abs_tol=1e-15):
            raise PNVSourceHolonomyError("Euler action-charge binding changed before rotor energy")
        h_phi = _expected_h_phi(state)
        if h_phi <= 0.0:
            raise PNVSourceHolonomyError("rotor phase energy must be positive in ratio sector")
        epsilon_i = h_phi / j_i
        return {
            **dict(state),
            "representation": "EULER_CLOSED_ROTOR_ENERGY",
            "H_Phi_EB": h_phi,
            "epsilon_I_EB": epsilon_i,
            "Delta_tau_eff_EB": 1.0 / epsilon_i,
        }

    def reconstruct_input(state: Mapping[str, Any]) -> dict[str, Any]:
        j_i = _finite(state.get("J_I_EB"), "J_I_EB")
        h_phi = _finite(state.get("H_Phi_EB"), "H_Phi_EB")
        epsilon_i = _strictly_positive(state.get("epsilon_I_EB"), "epsilon_I_EB")
        delta_tau = _strictly_positive(state.get("Delta_tau_eff_EB"), "Delta_tau_eff_EB")
        expected_j = _expected_j_i(state)
        expected_h = _expected_h_phi(state)
        expected_epsilon = _expected_epsilon_i(state)
        if not math.isclose(j_i, expected_j, rel_tol=1e-12, abs_tol=1e-15):
            raise PNVSourceHolonomyError("Euler action charge failed reverse audit")
        if not math.isclose(h_phi, expected_h, rel_tol=1e-12, abs_tol=1e-15):
            raise PNVSourceHolonomyError("rotor phase energy failed reverse audit")
        if not math.isclose(epsilon_i, expected_epsilon, rel_tol=1e-12, abs_tol=1e-15):
            raise PNVSourceHolonomyError("energy-per-action-charge failed reverse audit")
        if not math.isclose(delta_tau * h_phi, j_i, rel_tol=1e-12, abs_tol=1e-15):
            raise PNVSourceHolonomyError("effective Floquet step failed reverse audit")
        return {
            "schema": "PNCS_EULER_PHASE_INTENTION_STATE_V0_1",
            "representation": "EULER_BERRY_CLOSURE_INPUT",
            "D": int(state["D"]),
            "epsilon_EB": float(state["epsilon_EB"]),
            "phi_AB": float(state["phi_AB"]),
            "phi_Berry": float(state["phi_Berry"]),
            "phi_Euler": float(state["phi_Euler"]),
            "theta_prior": float(state["theta_prior"]),
            "hbar": float(state["hbar"]),
            "J_total": float(state["J_total"]),
            "I_phi": float(state["I_phi"]),
        }

    return {
        "euler.resolve_intention_charge": resolve_charge,
        "rotor.derive_energy_per_charge": derive_energy,
        "rotor.reconstruct_euler_input": reconstruct_input,
    }


def _closure_sector_invariant(state: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        int(state["D"]),
        _finite(state.get("epsilon_EB"), "epsilon_EB"),
        _finite(state.get("phi_AB"), "phi_AB"),
        _finite(state.get("phi_Berry"), "phi_Berry"),
        _finite(state.get("phi_Euler"), "phi_Euler"),
        _finite(state.get("theta_prior"), "theta_prior"),
    )


def _action_charge_invariant(state: Mapping[str, Any]) -> float:
    if "J_I_EB" in state:
        return _finite(state["J_I_EB"], "J_I_EB")
    return _expected_j_i(state)


def _rotor_energy_invariant(state: Mapping[str, Any]) -> float:
    if "H_Phi_EB" in state:
        return _finite(state["H_Phi_EB"], "H_Phi_EB")
    return _expected_h_phi(state)


def _epsilon_invariant(state: Mapping[str, Any]) -> float:
    if "epsilon_I_EB" in state:
        return _strictly_positive(state["epsilon_I_EB"], "epsilon_I_EB")
    return _expected_epsilon_i(state)


def euler_phase_intention_invariants() -> dict[str, Any]:
    return {
        "SOURCE.EULER_CLOSURE_SECTOR": _closure_sector_invariant,
        "SOURCE.INTENTION_ACTION_CHARGE": _action_charge_invariant,
        "SOURCE.ROTOR_PHASE_ENERGY": _rotor_energy_invariant,
        "SOURCE.ENERGY_PER_ACTION_CHARGE": _epsilon_invariant,
    }


def build_euler_phase_intention_loop(
    closure_kaku: Kaku,
    charge_kaku: Kaku,
    energy_kaku: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    _require_common_basis(closure_kaku, charge_kaku, energy_kaku)
    eps = _nonnegative(tolerance, "tolerance")
    refs = _refs((*evidence_refs, "gate:epsilon_Q:AFTER_EULER", "gate:Q_Sigma_to_J_I:OPEN"))
    closure = _law_node("LAW.EULER.BERRY_CLOSURE", "PHASE_TOPOLOGY", closure_kaku, refs)
    charge = _law_node("LAW.PHASE.INTENTION_ACTION_CHARGE", "PHASE_TIME_HAMILTONIAN", charge_kaku, refs)
    energy = _law_node("LAW.PHASE.ROTOR_ENERGY_PER_CHARGE", "PHASE_TIME_HAMILTONIAN", energy_kaku, refs)
    return InformationHolonomyLoop(
        loop_id="PNV_SOURCE_EULER_PHASE_INTENTION_ENERGY_LOOP_V0_1",
        connection=_connection("PNCS_EULER_PHASE_INTENTION_ENERGY_STATE_SPACE_V0_1", refs),
        nodes=(closure, charge, energy),
        transports=(
            LawTransport(
                "EDGE.EULER.TO_ACTION_CHARGE",
                closure.node_id,
                charge.node_id,
                "euler.resolve_intention_charge",
                refs,
            ),
            LawTransport(
                "EDGE.ACTION_CHARGE.TO_ROTOR_ENERGY",
                charge.node_id,
                energy.node_id,
                "rotor.derive_energy_per_charge",
                refs,
            ),
            LawTransport(
                "EDGE.ROTOR_ENERGY.TO_EULER_INPUT",
                energy.node_id,
                closure.node_id,
                "rotor.reconstruct_euler_input",
                refs,
            ),
        ),
        invariants=(
            HolonomyInvariant("SOURCE.EULER_CLOSURE_SECTOR", "EXACT", 0.0),
            HolonomyInvariant("SOURCE.INTENTION_ACTION_CHARGE", "ABS", eps),
            HolonomyInvariant("SOURCE.ROTOR_PHASE_ENERGY", "ABS", eps),
            HolonomyInvariant("SOURCE.ENERGY_PER_ACTION_CHARGE", "ABS", eps),
        ),
        evidence_refs=refs,
    )
