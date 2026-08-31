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
    checked_sum,
    finite_float,
    finite_tree,
)

NOETHER_RFC_CURRENT_CONTRACT = "PNCS_PNV_NOETHER_RFC_CURRENT_BINDING_V0_1"
NOETHER_RFC_CURRENT_LOOP_ID = "SOURCE.PHASE_NOETHER.RFC_CONSERVED_CURRENT.ROUNDTRIP"


class PNVNoetherRFCCurrentError(PNVInformationHolonomyError):
    pass


def _finite(value: Any, field: str) -> float:
    return finite_float(value, field, PNVNoetherRFCCurrentError)


def _positive(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out <= 0.0:
        raise PNVNoetherRFCCurrentError(f"{field} must be strictly positive")
    return out


def _nonnegative(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out < 0.0:
        raise PNVNoetherRFCCurrentError(f"{field} must be non-negative")
    return out


def _refs(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(value) for value in values if str(value)}))


def _ids(values: Sequence[str], field: str) -> tuple[str, ...]:
    out = tuple(str(value) for value in values)
    if not out or any(not value for value in out):
        raise PNVNoetherRFCCurrentError(f"{field} requires non-empty identifiers")
    if len(set(out)) != len(out):
        raise PNVNoetherRFCCurrentError(f"{field} identifiers must be unique")
    return out


def _vector(values: Sequence[float], field: str, *, positive: bool = False) -> tuple[float, ...]:
    fn = _positive if positive else _nonnegative
    out = tuple(fn(value, field) for value in values)
    if not out:
        raise PNVNoetherRFCCurrentError(f"{field} requires at least one cell")
    return out


def _law_node(law_id: str, domain: str, kaku: Kaku, evidence_refs: Sequence[str]) -> LawFrameNode:
    if not isinstance(kaku, Kaku):
        raise PNVNoetherRFCCurrentError("Noether/RFC current law gate requires Kaku")
    return LawFrameNode(law_id, domain, kaku, _refs(evidence_refs))


def _weighted_total(
    volumes: Sequence[float], currents: Sequence[float], field: str
) -> float:
    products = (
        checked_product(
            volume,
            current,
            field=f"{field}.cell_product",
            error_type=PNVNoetherRFCCurrentError,
        )
        for volume, current in zip(volumes, currents)
    )
    return checked_sum(products, field, PNVNoetherRFCCurrentError)


def make_noether_rfc_current_state(
    *,
    slice_id: str,
    noether_measure_id: str,
    rfc_measure_id: str,
    noether_cell_ids: Sequence[str],
    rfc_cell_ids: Sequence[str],
    noether_volumes: Sequence[float],
    rfc_volumes: Sequence[float],
    j_theta_cells: Sequence[float],
    j_q_cells: Sequence[float],
    side_flux: float = 0.0,
    noether_normal_id: str = "future",
    rfc_normal_id: str = "future",
) -> dict[str, Any]:
    sid = str(slice_id)
    nmid = str(noether_measure_id)
    rmid = str(rfc_measure_id)
    nnid = str(noether_normal_id)
    rnid = str(rfc_normal_id)
    if not sid or not nmid or not rmid or not nnid or not rnid:
        raise PNVNoetherRFCCurrentError("slice, measure and normal identifiers must be non-empty")

    n_ids = _ids(noether_cell_ids, "noether_cell_ids")
    r_ids = _ids(rfc_cell_ids, "rfc_cell_ids")
    n_vol = _vector(noether_volumes, "noether volume", positive=True)
    r_vol = _vector(rfc_volumes, "RFC volume", positive=True)
    j_theta = _vector(j_theta_cells, "j_theta cell")
    j_q = _vector(j_q_cells, "j_Q cell")

    if len(n_ids) != len(n_vol) or len(n_ids) != len(j_theta):
        raise PNVNoetherRFCCurrentError("Noether cell/volume/current support mismatch")
    if len(r_ids) != len(r_vol) or len(r_ids) != len(j_q):
        raise PNVNoetherRFCCurrentError("RFC cell/volume/current support mismatch")

    q_theta = _weighted_total(n_vol, j_theta, "Q_theta")
    q_sigma = _weighted_total(r_vol, j_q, "Q_Sigma")
    if q_theta <= 0.0 or q_sigma <= 0.0:
        raise PNVNoetherRFCCurrentError("positive finite Noether and RFC carrier totals are required")

    return {
        "schema": "PNCS_NOETHER_RFC_CURRENT_STATE_V0_1",
        "representation": "PAIRED_LOCAL_CURRENTS",
        "slice_id": sid,
        "noether_measure_id": nmid,
        "rfc_measure_id": rmid,
        "noether_normal_id": nnid,
        "rfc_normal_id": rnid,
        "noether_cell_ids": list(n_ids),
        "rfc_cell_ids": list(r_ids),
        "noether_volumes": list(n_vol),
        "rfc_volumes": list(r_vol),
        "j_theta_cells": list(j_theta),
        "j_q_cells": list(j_q),
        "side_flux": _finite(side_flux, "side_flux"),
    }


def _raw(state: Mapping[str, Any]) -> dict[str, Any]:
    return make_noether_rfc_current_state(
        slice_id=str(state.get("slice_id", "")),
        noether_measure_id=str(state.get("noether_measure_id", "")),
        rfc_measure_id=str(state.get("rfc_measure_id", "")),
        noether_normal_id=str(state.get("noether_normal_id", "future")),
        rfc_normal_id=str(state.get("rfc_normal_id", "future")),
        noether_cell_ids=state.get("noether_cell_ids", ()),
        rfc_cell_ids=state.get("rfc_cell_ids", ()),
        noether_volumes=state.get("noether_volumes", ()),
        rfc_volumes=state.get("rfc_volumes", ()),
        j_theta_cells=state.get("j_theta_cells", ()),
        j_q_cells=state.get("j_q_cells", ()),
        side_flux=state.get("side_flux", 0.0),
    )


def _derived(state: Mapping[str, Any]) -> dict[str, Any]:
    raw = _raw(state)
    if raw["noether_measure_id"] != raw["rfc_measure_id"]:
        raise PNVNoetherRFCCurrentError("Noether and RFC measure IDs differ")
    if raw["noether_normal_id"] != raw["rfc_normal_id"]:
        raise PNVNoetherRFCCurrentError("Noether and RFC normal orientations differ")
    if raw["noether_cell_ids"] != raw["rfc_cell_ids"]:
        raise PNVNoetherRFCCurrentError("Noether and RFC cell partitions differ")

    n_vol = tuple(raw["noether_volumes"])
    r_vol = tuple(raw["rfc_volumes"])
    j_theta = tuple(raw["j_theta_cells"])
    j_q = tuple(raw["j_q_cells"])

    q_theta = _weighted_total(n_vol, j_theta, "Q_theta")
    q_sigma = _weighted_total(r_vol, j_q, "Q_Sigma")

    measure_terms = []
    local_terms = []
    for index, (v_theta, v_q, j_theta_i, j_q_i) in enumerate(
        zip(n_vol, r_vol, j_theta, j_q)
    ):
        dv = abs(
            checked_difference(
                v_q,
                v_theta,
                f"Delta_measure.volume[{index}]",
                PNVNoetherRFCCurrentError,
            )
        )
        dj = abs(
            checked_difference(
                j_q_i,
                j_theta_i,
                f"Delta_local_current.current[{index}]",
                PNVNoetherRFCCurrentError,
            )
        )
        measure_terms.append(
            checked_product(
                dv,
                abs(j_theta_i),
                field=f"Delta_measure.term[{index}]",
                error_type=PNVNoetherRFCCurrentError,
            )
        )
        local_terms.append(
            checked_product(
                v_q,
                dj,
                field=f"Delta_local_current.term[{index}]",
                error_type=PNVNoetherRFCCurrentError,
            )
        )

    measure_defect = checked_ratio(
        checked_sum(measure_terms, "Delta_measure.sum", PNVNoetherRFCCurrentError),
        q_theta,
        "Delta_measure",
        PNVNoetherRFCCurrentError,
    )
    local_defect = checked_ratio(
        checked_sum(local_terms, "Delta_local_current.sum", PNVNoetherRFCCurrentError),
        q_theta,
        "Delta_local_current",
        PNVNoetherRFCCurrentError,
    )
    total_defect = checked_abs_difference_ratio(
        q_sigma,
        q_theta,
        q_theta,
        "Delta_total_charge",
        PNVNoetherRFCCurrentError,
    )
    defect_sum = checked_sum(
        (local_defect, measure_defect),
        "Delta_bound_components",
        PNVNoetherRFCCurrentError,
    )
    defect_bound_margin = max(
        0.0,
        checked_difference(
            total_defect,
            defect_sum,
            "Delta_bound_margin",
            PNVNoetherRFCCurrentError,
        ),
    )
    if defect_bound_margin > 1e-12:
        raise PNVNoetherRFCCurrentError("Noether/RFC current-measure defect bound violated")

    p_theta = [
        checked_ratio(
            checked_product(
                v,
                j,
                field=f"p_theta.cell[{index}]",
                error_type=PNVNoetherRFCCurrentError,
            ),
            q_theta,
            f"p_theta[{index}]",
            PNVNoetherRFCCurrentError,
        )
        for index, (v, j) in enumerate(zip(n_vol, j_theta))
    ]
    p_q = [
        checked_ratio(
            checked_product(
                v,
                j,
                field=f"p_Q.cell[{index}]",
                error_type=PNVNoetherRFCCurrentError,
            ),
            q_sigma,
            f"p_Q[{index}]",
            PNVNoetherRFCCurrentError,
        )
        for index, (v, j) in enumerate(zip(r_vol, j_q))
    ]

    return finite_tree(
        {
            "Q_theta": q_theta,
            "Q_Sigma": q_sigma,
            "Delta_measure": measure_defect,
            "Delta_local_current": local_defect,
            "Delta_total_charge": total_defect,
            "Delta_bound_margin": defect_bound_margin,
            "side_flux_abs": abs(_finite(raw["side_flux"], "side_flux")),
            "p_theta": p_theta,
            "p_Q": p_q,
        },
        "noether_rfc_current_derived",
        PNVNoetherRFCCurrentError,
    )


def noether_rfc_current_defects(state: Mapping[str, Any]) -> dict[str, float]:
    values = _derived(state)
    return {
        "Delta_measure": float(values["Delta_measure"]),
        "Delta_local_current": float(values["Delta_local_current"]),
        "Delta_total_charge": float(values["Delta_total_charge"]),
        "Delta_bound_margin": float(values["Delta_bound_margin"]),
        "side_flux_abs": float(values["side_flux_abs"]),
    }


def noether_rfc_current_transforms(
    *,
    measure_tolerance: float = 0.0,
    local_current_tolerance: float = 0.0,
    total_charge_tolerance: float = 0.0,
    side_flux_tolerance: float = 0.0,
) -> dict[str, Any]:
    measure_tol = _nonnegative(measure_tolerance, "measure_tolerance")
    local_tol = _nonnegative(local_current_tolerance, "local_current_tolerance")
    total_tol = _nonnegative(total_charge_tolerance, "total_charge_tolerance")
    flux_tol = _nonnegative(side_flux_tolerance, "side_flux_tolerance")

    def enforce(values: Mapping[str, Any]) -> None:
        if values["Delta_measure"] > measure_tol:
            raise PNVNoetherRFCCurrentError(
                f"common-measure defect {values['Delta_measure']!r} exceeds tolerance {measure_tol!r}"
            )
        if values["Delta_local_current"] > local_tol:
            raise PNVNoetherRFCCurrentError(
                f"local-current defect {values['Delta_local_current']!r} exceeds tolerance {local_tol!r}"
            )
        if values["Delta_total_charge"] > total_tol:
            raise PNVNoetherRFCCurrentError(
                f"total-charge defect {values['Delta_total_charge']!r} exceeds tolerance {total_tol!r}"
            )
        if values["side_flux_abs"] > flux_tol:
            raise PNVNoetherRFCCurrentError(
                f"side-flux defect {values['side_flux_abs']!r} exceeds tolerance {flux_tol!r}"
            )

    def resolve_common_measure(state: Mapping[str, Any]) -> dict[str, Any]:
        raw = _raw(state)
        values = _derived(raw)
        if values["Delta_measure"] > measure_tol:
            raise PNVNoetherRFCCurrentError(
                f"common-measure defect {values['Delta_measure']!r} exceeds tolerance {measure_tol!r}"
            )
        return {
            **raw,
            **values,
            "representation": "COMMON_SLICE_CURRENT_PAIR",
        }

    def bind_conserved_current(state: Mapping[str, Any]) -> dict[str, Any]:
        raw = _raw(state)
        values = _derived(raw)
        for key in (
            "Q_theta",
            "Q_Sigma",
            "Delta_measure",
            "Delta_local_current",
            "Delta_total_charge",
            "Delta_bound_margin",
            "side_flux_abs",
        ):
            observed = _finite(state.get(key), key)
            expected = _finite(values[key], key)
            if not math.isclose(observed, expected, rel_tol=1e-12, abs_tol=1e-15):
                raise PNVNoetherRFCCurrentError(f"{key} changed before conserved-current binding")
        enforce(values)
        return {
            **raw,
            **values,
            "representation": "RFC_NOETHER_CONSERVED_CURRENT_BOUND",
            "Q_RFC": values["Q_Sigma"],
            "Q_NOETHER": values["Q_theta"],
        }

    def reconstruct_pair(state: Mapping[str, Any]) -> dict[str, Any]:
        raw = _raw(state)
        values = _derived(raw)
        enforce(values)
        q_rfc = _positive(state.get("Q_RFC"), "Q_RFC")
        q_noether = _positive(state.get("Q_NOETHER"), "Q_NOETHER")
        if not math.isclose(q_rfc, values["Q_Sigma"], rel_tol=1e-12, abs_tol=1e-15):
            raise PNVNoetherRFCCurrentError("RFC total failed reverse current audit")
        if not math.isclose(q_noether, values["Q_theta"], rel_tol=1e-12, abs_tol=1e-15):
            raise PNVNoetherRFCCurrentError("Noether total failed reverse current audit")
        for key in ("p_theta", "p_Q"):
            observed = tuple(_finite(value, key) for value in state.get(key, ()))
            expected = tuple(_finite(value, key) for value in values[key])
            if len(observed) != len(expected) or any(
                not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15)
                for a, b in zip(observed, expected)
            ):
                raise PNVNoetherRFCCurrentError(f"{key} failed reverse current audit")
        return raw

    return {
        "noether_rfc.resolve_common_measure": resolve_common_measure,
        "noether_rfc.bind_conserved_current": bind_conserved_current,
        "noether_rfc.reconstruct_pair": reconstruct_pair,
    }


def _q_theta(state: Mapping[str, Any]) -> float:
    if "Q_theta" in state:
        return _positive(state["Q_theta"], "Q_theta")
    return _positive(_derived(state)["Q_theta"], "Q_theta")


def _q_sigma(state: Mapping[str, Any]) -> float:
    if "Q_Sigma" in state:
        return _positive(state["Q_Sigma"], "Q_Sigma")
    return _positive(_derived(state)["Q_Sigma"], "Q_Sigma")


def _delta(name: str):
    def evaluate(state: Mapping[str, Any]) -> float:
        if name in state:
            return _nonnegative(state[name], name)
        return _nonnegative(_derived(state)[name], name)
    return evaluate


def _profile_norm(name: str):
    def evaluate(state: Mapping[str, Any]) -> float:
        if name in state:
            values = tuple(_finite(value, name) for value in state[name])
        else:
            values = tuple(_finite(value, name) for value in _derived(state)[name])
        return checked_sum(values, f"{name}.norm", PNVNoetherRFCCurrentError)
    return evaluate


def noether_rfc_current_invariants() -> dict[str, Any]:
    return {
        "SOURCE.NOETHER_TOTAL_CHARGE": _q_theta,
        "SOURCE.RFC_TOTAL_CHARGE": _q_sigma,
        "SOURCE.COMMON_MEASURE_DEFECT": _delta("Delta_measure"),
        "SOURCE.LOCAL_CURRENT_BINDING_DEFECT": _delta("Delta_local_current"),
        "SOURCE.TOTAL_CHARGE_BINDING_DEFECT": _delta("Delta_total_charge"),
        "SOURCE.CURRENT_MEASURE_BOUND_MARGIN": _delta("Delta_bound_margin"),
        "SOURCE.NOETHER_PROFILE_NORM": _profile_norm("p_theta"),
        "SOURCE.RFC_PROFILE_NORM": _profile_norm("p_Q"),
        "SOURCE.SIDE_FLUX_DEFECT": _delta("side_flux_abs"),
    }


def build_noether_rfc_current_loop(
    noether_kaku: Kaku,
    measure_kaku: Kaku,
    rfc_kaku: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    eps = _nonnegative(tolerance, "tolerance")
    refs = _refs(
        (
            *evidence_refs,
            f"contract:{NOETHER_RFC_CURRENT_CONTRACT}",
            "gate:common_slice_measure:EXPLICIT",
            "gate:common_normal_orientation:EXPLICIT",
            "gate:local_current_binding:CONDITIONAL",
            "gate:side_flux:CONDITIONAL_ZERO",
        )
    )
    noether = _law_node("LAW.NOETHER.LOCAL_NORMAL_CURRENT", "IDT_NOETHER_FIELD", noether_kaku, refs)
    measure = _law_node("LAW.SOURCE.COMMON_SLICE_MEASURE", "IDT_RFC_INTERFACE", measure_kaku, refs)
    rfc = _law_node("LAW.RFC.CONSERVED_LOCAL_CURRENT", "RFC_SOURCE_CARRIER", rfc_kaku, refs)
    return InformationHolonomyLoop(
        loop_id=NOETHER_RFC_CURRENT_LOOP_ID,
        connection=information_transport_connection(
            "PNCS_NOETHER_RFC_CURRENT_STATE_SPACE_V0_1",
            evidence_refs=refs,
        ),
        nodes=(noether, measure, rfc),
        transports=(
            LawTransport(
                "EDGE.NOETHER.TO_COMMON_MEASURE",
                noether.node_id,
                measure.node_id,
                "noether_rfc.resolve_common_measure",
                refs,
            ),
            LawTransport(
                "EDGE.COMMON_MEASURE.TO_RFC_CURRENT",
                measure.node_id,
                rfc.node_id,
                "noether_rfc.bind_conserved_current",
                refs,
            ),
            LawTransport(
                "EDGE.RFC_CURRENT.TO_NOETHER_PAIR",
                rfc.node_id,
                noether.node_id,
                "noether_rfc.reconstruct_pair",
                refs,
            ),
        ),
        invariants=(
            HolonomyInvariant("SOURCE.NOETHER_TOTAL_CHARGE", "ABS", eps),
            HolonomyInvariant("SOURCE.RFC_TOTAL_CHARGE", "ABS", eps),
            HolonomyInvariant("SOURCE.COMMON_MEASURE_DEFECT", "ABS", eps),
            HolonomyInvariant("SOURCE.LOCAL_CURRENT_BINDING_DEFECT", "ABS", eps),
            HolonomyInvariant("SOURCE.TOTAL_CHARGE_BINDING_DEFECT", "ABS", eps),
            HolonomyInvariant("SOURCE.CURRENT_MEASURE_BOUND_MARGIN", "ABS", eps),
            HolonomyInvariant("SOURCE.NOETHER_PROFILE_NORM", "ABS", eps),
            HolonomyInvariant("SOURCE.RFC_PROFILE_NORM", "ABS", eps),
            HolonomyInvariant("SOURCE.SIDE_FLUX_DEFECT", "ABS", eps),
        ),
        evidence_refs=refs,
    )
