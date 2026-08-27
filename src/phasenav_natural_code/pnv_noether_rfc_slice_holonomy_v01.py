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

NOETHER_RFC_SLICE_CONTRACT = "PNCS_PNV_NOETHER_RFC_SLICE_CARRIER_V0_1"
NOETHER_RFC_SLICE_LOOP_ID = "SOURCE.NOETHER_RFC.SLICE_CARRIER.ROUNDTRIP"


class PNVNoetherRFCSliceError(PNVInformationHolonomyError):
    pass


def _finite(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise PNVNoetherRFCSliceError(f"{field} must be finite") from exc
    if not math.isfinite(out):
        raise PNVNoetherRFCSliceError(f"{field} must be finite")
    return out


def _positive(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out <= 0.0:
        raise PNVNoetherRFCSliceError(f"{field} must be strictly positive")
    return out


def _nonnegative(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out < 0.0:
        raise PNVNoetherRFCSliceError(f"{field} must be non-negative")
    return out


def _refs(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(value) for value in values if str(value)}))


def _strings(values: Sequence[Any], field: str) -> list[str]:
    out = [str(value) for value in values]
    if not out or any(not value for value in out):
        raise PNVNoetherRFCSliceError(f"{field} must be non-empty strings")
    if len(out) != len(set(out)):
        raise PNVNoetherRFCSliceError(f"{field} must be unique")
    return out


def make_noether_rfc_slice_state(
    *,
    slice_id_theta: str,
    slice_id_q: str,
    normal_theta: str,
    normal_q: str,
    cell_ids_theta: Sequence[str],
    cell_ids_q: Sequence[str],
    j_theta: Sequence[float],
    v_theta: Sequence[float],
    j_q: Sequence[float],
    v_q: Sequence[float],
) -> dict[str, Any]:
    ids_theta = _strings(cell_ids_theta, "Noether cell IDs")
    ids_q = _strings(cell_ids_q, "RFC cell IDs")
    jt = [_finite(value, "j_theta") for value in j_theta]
    jq = [_finite(value, "j_Q") for value in j_q]
    vt = [_positive(value, "V_theta") for value in v_theta]
    vq = [_positive(value, "V_Q") for value in v_q]
    n = len(ids_theta)
    if not (len(ids_q) == len(jt) == len(jq) == len(vt) == len(vq) == n):
        raise PNVNoetherRFCSliceError("Noether/RFC slice arrays must share one cell cardinality")
    if not str(slice_id_theta) or not str(slice_id_q):
        raise PNVNoetherRFCSliceError("slice IDs are required")
    if not str(normal_theta) or not str(normal_q):
        raise PNVNoetherRFCSliceError("normal orientation IDs are required")
    return {
        "schema": "PNCS_NOETHER_RFC_SLICE_CARRIER_STATE_V0_1",
        "representation": "NOETHER_RFC_SLICE_INPUT",
        "slice_id_theta": str(slice_id_theta),
        "slice_id_q": str(slice_id_q),
        "normal_theta": str(normal_theta),
        "normal_q": str(normal_q),
        "cell_ids_theta": ids_theta,
        "cell_ids_q": ids_q,
        "j_theta": jt,
        "V_theta": vt,
        "j_Q": jq,
        "V_Q": vq,
    }


def _derived(state: Mapping[str, Any]) -> dict[str, Any]:
    ids_theta = _strings(state.get("cell_ids_theta", ()), "Noether cell IDs")
    ids_q = _strings(state.get("cell_ids_q", ()), "RFC cell IDs")
    if ids_theta != ids_q:
        raise PNVNoetherRFCSliceError("Noether and RFC cell IDs/ordering must match exactly")
    if str(state.get("slice_id_theta", "")) != str(state.get("slice_id_q", "")):
        raise PNVNoetherRFCSliceError("Noether and RFC slice IDs must match exactly")
    if str(state.get("normal_theta", "")) != str(state.get("normal_q", "")):
        raise PNVNoetherRFCSliceError("Noether and RFC normal orientations must match exactly")

    jt = [_finite(value, "j_theta") for value in state.get("j_theta", ())]
    jq = [_finite(value, "j_Q") for value in state.get("j_Q", ())]
    vt = [_positive(value, "V_theta") for value in state.get("V_theta", ())]
    vq = [_positive(value, "V_Q") for value in state.get("V_Q", ())]
    n = len(ids_theta)
    if not (len(jt) == len(jq) == len(vt) == len(vq) == n):
        raise PNVNoetherRFCSliceError("Noether/RFC slice arrays must preserve one cell cardinality")

    q_theta = sum(v * j for v, j in zip(vt, jt))
    if q_theta <= 0.0:
        raise PNVNoetherRFCSliceError("positive Noether slice charge Q_theta is required")
    q_sigma = sum(v * j for v, j in zip(vq, jq))
    if q_sigma <= 0.0:
        raise PNVNoetherRFCSliceError("positive RFC slice charge Q_Sigma is required")

    delta_j = sum(v * abs(jq_i - jt_i) for jt_i, jq_i, v in zip(jt, jq, vq)) / q_theta
    delta_v = sum(abs(vq_i - vt_i) * abs(jt_i) for jt_i, vt_i, vq_i in zip(jt, vt, vq)) / q_theta
    delta_sigma = abs(q_sigma - q_theta) / q_theta
    bound_margin = max(0.0, delta_sigma - (delta_j + delta_v))
    if bound_margin > 1e-12:
        raise PNVNoetherRFCSliceError("slice defect triangle bound violated")

    p_theta = [v * j / q_theta for v, j in zip(vt, jt)]
    p_q = [v * j / q_sigma for v, j in zip(vq, jq)]
    return {
        "Q_theta": q_theta,
        "Q_Sigma": q_sigma,
        "Delta_J": delta_j,
        "Delta_V": delta_v,
        "Delta_Sigma": delta_sigma,
        "defect_bound_margin": bound_margin,
        "p_theta": p_theta,
        "p_Q": p_q,
    }


def noether_rfc_slice_defects(state: Mapping[str, Any]) -> dict[str, float]:
    values = _derived(state)
    return {
        "Delta_J": float(values["Delta_J"]),
        "Delta_V": float(values["Delta_V"]),
        "Delta_Sigma": float(values["Delta_Sigma"]),
        "defect_bound_margin": float(values["defect_bound_margin"]),
    }


def noether_rfc_slice_transforms(
    *,
    current_tolerance: float = 1e-12,
    measure_tolerance: float = 1e-12,
    charge_tolerance: float = 1e-12,
) -> dict[str, Any]:
    current_eps = _nonnegative(current_tolerance, "current_tolerance")
    measure_eps = _nonnegative(measure_tolerance, "measure_tolerance")
    charge_eps = _nonnegative(charge_tolerance, "charge_tolerance")

    def bind_slice_carrier(state: Mapping[str, Any]) -> dict[str, Any]:
        values = _derived(state)
        if values["Delta_J"] > current_eps:
            raise PNVNoetherRFCSliceError(
                f"local current defect {values['Delta_J']!r} exceeds tolerance {current_eps!r}"
            )
        if values["Delta_V"] > measure_eps:
            raise PNVNoetherRFCSliceError(
                f"measure defect {values['Delta_V']!r} exceeds tolerance {measure_eps!r}"
            )
        if values["Delta_Sigma"] > charge_eps:
            raise PNVNoetherRFCSliceError(
                f"extensive charge defect {values['Delta_Sigma']!r} exceeds tolerance {charge_eps!r}"
            )
        return {
            **dict(state),
            **values,
            "representation": "RFC_BOUND_NOETHER_SLICE_CARRIER",
            "carrier_binding_state": "LOCAL_CURRENT_MEASURE_BOUND_CANDIDATE",
        }

    def reconstruct_slice_input(state: Mapping[str, Any]) -> dict[str, Any]:
        expected = _derived(state)
        for key in (
            "Q_theta",
            "Q_Sigma",
            "Delta_J",
            "Delta_V",
            "Delta_Sigma",
            "defect_bound_margin",
        ):
            observed = _finite(state.get(key), key)
            if not math.isclose(observed, float(expected[key]), rel_tol=1e-12, abs_tol=1e-15):
                raise PNVNoetherRFCSliceError(f"{key} changed before reverse slice audit")
        for key in ("p_theta", "p_Q"):
            observed = [_finite(value, key) for value in state.get(key, ())]
            expected_values = [float(value) for value in expected[key]]
            if len(observed) != len(expected_values) or any(
                not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15)
                for a, b in zip(observed, expected_values)
            ):
                raise PNVNoetherRFCSliceError(f"{key} changed before reverse slice audit")
        return make_noether_rfc_slice_state(
            slice_id_theta=str(state["slice_id_theta"]),
            slice_id_q=str(state["slice_id_q"]),
            normal_theta=str(state["normal_theta"]),
            normal_q=str(state["normal_q"]),
            cell_ids_theta=state["cell_ids_theta"],
            cell_ids_q=state["cell_ids_q"],
            j_theta=state["j_theta"],
            v_theta=state["V_theta"],
            j_q=state["j_Q"],
            v_q=state["V_Q"],
        )

    return {
        "slice.bind_noether_to_rfc": bind_slice_carrier,
        "slice.reconstruct_noether_input": reconstruct_slice_input,
    }


def _slice_signature(state: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        str(state.get("slice_id_theta")),
        str(state.get("slice_id_q")),
        str(state.get("normal_theta")),
        str(state.get("normal_q")),
        tuple(_strings(state.get("cell_ids_theta", ()), "Noether cell IDs")),
        tuple(_strings(state.get("cell_ids_q", ()), "RFC cell IDs")),
    )


def _q_theta(state: Mapping[str, Any]) -> float:
    if "Q_theta" in state:
        return _positive(state.get("Q_theta"), "Q_theta")
    return float(_derived(state)["Q_theta"])


def _q_sigma(state: Mapping[str, Any]) -> float:
    if "Q_Sigma" in state:
        return _positive(state.get("Q_Sigma"), "Q_Sigma")
    return float(_derived(state)["Q_Sigma"])


def _delta(name: str):
    def evaluate(state: Mapping[str, Any]) -> float:
        if name in state:
            return _nonnegative(state.get(name), name)
        return float(_derived(state)[name])
    return evaluate


def noether_rfc_slice_invariants() -> dict[str, Any]:
    return {
        "SOURCE.SLICE_BINDING_SIGNATURE": _slice_signature,
        "SOURCE.NOETHER_SLICE_CHARGE": _q_theta,
        "SOURCE.RFC_SLICE_CHARGE": _q_sigma,
        "SOURCE.SLICE_CURRENT_DEFECT": _delta("Delta_J"),
        "SOURCE.SLICE_MEASURE_DEFECT": _delta("Delta_V"),
        "SOURCE.SLICE_EXTENSIVE_DEFECT": _delta("Delta_Sigma"),
        "SOURCE.SLICE_DEFECT_BOUND_MARGIN": _delta("defect_bound_margin"),
    }


def build_noether_rfc_slice_carrier_loop(
    noether_kaku: Kaku,
    rfc_kaku: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    if not isinstance(noether_kaku, Kaku) or not isinstance(rfc_kaku, Kaku):
        raise PNVNoetherRFCSliceError("Noether/RFC slice law gates require Kaku")
    eps = _nonnegative(tolerance, "tolerance")
    refs = _refs(
        (
            *evidence_refs,
            f"contract:{NOETHER_RFC_SLICE_CONTRACT}",
            "gate:common_slice:CONDITIONAL",
            "gate:common_normal_orientation:CONDITIONAL",
            "gate:common_cell_ids:CONDITIONAL",
            "gate:local_current_binding:OPEN_MEASURED",
            "gate:measure_binding:OPEN_MEASURED",
        )
    )
    noether = LawFrameNode(
        "LAW.NOETHER.SLICE_CARRIER",
        "EULER_NOETHER_FIELD",
        noether_kaku,
        refs,
    )
    rfc = LawFrameNode(
        "LAW.RFC.SLICE_CARRIER",
        "RFC_SOURCE_CARRIER",
        rfc_kaku,
        refs,
    )
    return InformationHolonomyLoop(
        loop_id=NOETHER_RFC_SLICE_LOOP_ID,
        connection=information_transport_connection(
            "PNCS_NOETHER_RFC_SLICE_CARRIER_STATE_SPACE_V0_1",
            evidence_refs=refs,
        ),
        nodes=(noether, rfc),
        transports=(
            LawTransport(
                "EDGE.NOETHER_SLICE.TO_RFC",
                noether.node_id,
                rfc.node_id,
                "slice.bind_noether_to_rfc",
                refs,
            ),
            LawTransport(
                "EDGE.RFC_SLICE.TO_NOETHER_INPUT",
                rfc.node_id,
                noether.node_id,
                "slice.reconstruct_noether_input",
                refs,
            ),
        ),
        invariants=(
            HolonomyInvariant("SOURCE.SLICE_BINDING_SIGNATURE", "EXACT", 0.0),
            HolonomyInvariant("SOURCE.NOETHER_SLICE_CHARGE", "ABS", eps),
            HolonomyInvariant("SOURCE.RFC_SLICE_CHARGE", "ABS", eps),
            HolonomyInvariant("SOURCE.SLICE_CURRENT_DEFECT", "ABS", eps),
            HolonomyInvariant("SOURCE.SLICE_MEASURE_DEFECT", "ABS", eps),
            HolonomyInvariant("SOURCE.SLICE_EXTENSIVE_DEFECT", "ABS", eps),
            HolonomyInvariant("SOURCE.SLICE_DEFECT_BOUND_MARGIN", "ABS", eps),
        ),
        evidence_refs=refs,
    )
