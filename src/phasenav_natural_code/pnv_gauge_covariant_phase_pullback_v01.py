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

GAUGE_COVARIANT_PULLBACK_CONTRACT = "PNCS_PNV_GAUGE_COVARIANT_PHASE_PULLBACK_V0_1"
GAUGE_COVARIANT_PULLBACK_LOOP_ID = "SOURCE.PHASE.NOETHER.GAUGE_COVARIANT_PULLBACK.ROUNDTRIP"


class PNVGaugeCovariantPhasePullbackError(PNVInformationHolonomyError):
    pass


def _finite(value: Any, field: str) -> float:
    return finite_float(value, field, PNVGaugeCovariantPhasePullbackError)


def _positive(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out <= 0.0:
        raise PNVGaugeCovariantPhasePullbackError(f"{field} must be strictly positive")
    return out


def _nonnegative(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out < 0.0:
        raise PNVGaugeCovariantPhasePullbackError(f"{field} must be non-negative")
    return out


def _ids(values: Sequence[str], field: str) -> tuple[str, ...]:
    out = tuple(str(value) for value in values)
    if not out or any(not value for value in out):
        raise PNVGaugeCovariantPhasePullbackError(f"{field} requires non-empty identifiers")
    if len(set(out)) != len(out):
        raise PNVGaugeCovariantPhasePullbackError(f"{field} identifiers must be unique")
    return out


def _vector(values: Sequence[float], field: str) -> tuple[float, ...]:
    out = tuple(_finite(value, field) for value in values)
    if not out:
        raise PNVGaugeCovariantPhasePullbackError(f"{field} requires a non-empty vector")
    return out


def _refs(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(value) for value in values if str(value)}))


def _field_coefficient(amplitudes: Sequence[float], volumes: Sequence[float]) -> float:
    terms = []
    for index, (amplitude, volume) in enumerate(zip(amplitudes, volumes)):
        a_sq = checked_product(
            amplitude,
            amplitude,
            field=f"C_A.amplitude_squared[{index}]",
            error_type=PNVGaugeCovariantPhasePullbackError,
        )
        terms.append(
            checked_product(
                a_sq,
                volume,
                field=f"C_A.term[{index}]",
                error_type=PNVGaugeCovariantPhasePullbackError,
            )
        )
    return checked_sum(terms, "C_A", PNVGaugeCovariantPhasePullbackError)


def make_gauge_covariant_phase_pullback_state(
    *,
    field_bundle_id: str,
    rotor_bundle_id: str,
    field_phase_patch_id: str,
    rotor_phase_patch_id: str,
    field_connection_id: str,
    rotor_connection_id: str,
    field_measure_id: str,
    rotor_measure_id: str,
    field_cell_ids: Sequence[str],
    rotor_cell_ids: Sequence[str],
    phase_gradients: Sequence[float],
    connection_components: Sequence[float],
    gauge_shift_components: Sequence[float],
    trajectory_velocity: Sequence[float],
    field_normal_rate: float,
    rotor_rate: float,
    amplitudes: Sequence[float],
    volumes: Sequence[float],
    i_phi: float,
) -> dict[str, Any]:
    identifiers = {
        "field_bundle_id": str(field_bundle_id),
        "rotor_bundle_id": str(rotor_bundle_id),
        "field_phase_patch_id": str(field_phase_patch_id),
        "rotor_phase_patch_id": str(rotor_phase_patch_id),
        "field_connection_id": str(field_connection_id),
        "rotor_connection_id": str(rotor_connection_id),
        "field_measure_id": str(field_measure_id),
        "rotor_measure_id": str(rotor_measure_id),
    }
    if any(not value for value in identifiers.values()):
        raise PNVGaugeCovariantPhasePullbackError(
            "bundle, patch, connection and measure identifiers are required"
        )

    field_cells = _ids(field_cell_ids, "field_cell_ids")
    rotor_cells = _ids(rotor_cell_ids, "rotor_cell_ids")
    gradients = _vector(phase_gradients, "phase_gradients")
    connection = _vector(connection_components, "connection_components")
    gauge_shift = _vector(gauge_shift_components, "gauge_shift_components")
    velocity = _vector(trajectory_velocity, "trajectory_velocity")
    if not (
        len(gradients) == len(connection) == len(gauge_shift) == len(velocity)
    ):
        raise PNVGaugeCovariantPhasePullbackError(
            "phase/connection/gauge/trajectory coordinate dimensions differ"
        )
    if max(abs(value) for value in gauge_shift) <= 0.0:
        raise PNVGaugeCovariantPhasePullbackError("nontrivial gauge probe required")

    amps = tuple(_nonnegative(value, "field amplitude") for value in amplitudes)
    vols = tuple(_positive(value, "field volume") for value in volumes)
    if len(field_cells) != len(amps) or len(field_cells) != len(vols):
        raise PNVGaugeCovariantPhasePullbackError(
            "field cell/amplitude/volume support mismatch"
        )
    if len(rotor_cells) != len(field_cells):
        raise PNVGaugeCovariantPhasePullbackError(
            "field/rotor support cardinality mismatch"
        )

    return {
        "schema": "PNCS_GAUGE_COVARIANT_PHASE_PULLBACK_STATE_V0_1",
        "representation": "GAUGE_COVARIANT_PHASE_PULLBACK_INPUT",
        **identifiers,
        "field_cell_ids": list(field_cells),
        "rotor_cell_ids": list(rotor_cells),
        "phase_gradients": list(gradients),
        "connection_components": list(connection),
        "gauge_shift_components": list(gauge_shift),
        "trajectory_velocity": list(velocity),
        "field_normal_rate": _positive(field_normal_rate, "field_normal_rate"),
        "rotor_rate": _positive(rotor_rate, "rotor_rate"),
        "amplitudes": list(amps),
        "volumes": list(vols),
        "I_phi": _positive(i_phi, "I_phi"),
    }


def _raw(state: Mapping[str, Any]) -> dict[str, Any]:
    return make_gauge_covariant_phase_pullback_state(
        field_bundle_id=str(state.get("field_bundle_id", "")),
        rotor_bundle_id=str(state.get("rotor_bundle_id", "")),
        field_phase_patch_id=str(state.get("field_phase_patch_id", "")),
        rotor_phase_patch_id=str(state.get("rotor_phase_patch_id", "")),
        field_connection_id=str(state.get("field_connection_id", "")),
        rotor_connection_id=str(state.get("rotor_connection_id", "")),
        field_measure_id=str(state.get("field_measure_id", "")),
        rotor_measure_id=str(state.get("rotor_measure_id", "")),
        field_cell_ids=state.get("field_cell_ids", ()),
        rotor_cell_ids=state.get("rotor_cell_ids", ()),
        phase_gradients=state.get("phase_gradients", ()),
        connection_components=state.get("connection_components", ()),
        gauge_shift_components=state.get("gauge_shift_components", ()),
        trajectory_velocity=state.get("trajectory_velocity", ()),
        field_normal_rate=state.get("field_normal_rate"),
        rotor_rate=state.get("rotor_rate"),
        amplitudes=state.get("amplitudes", ()),
        volumes=state.get("volumes", ()),
        i_phi=state.get("I_phi"),
    )


def _require_common_ids(raw: Mapping[str, Any]) -> None:
    for left, right, message in (
        ("field_bundle_id", "rotor_bundle_id", "bundle IDs differ"),
        ("field_phase_patch_id", "rotor_phase_patch_id", "phase-patch IDs differ"),
        ("field_connection_id", "rotor_connection_id", "connection IDs differ"),
        ("field_measure_id", "rotor_measure_id", "measure IDs differ"),
    ):
        if raw[left] != raw[right]:
            raise PNVGaugeCovariantPhasePullbackError(message)
    if raw["field_cell_ids"] != raw["rotor_cell_ids"]:
        raise PNVGaugeCovariantPhasePullbackError(
            "field and rotor collective supports differ"
        )


def _derived(state: Mapping[str, Any]) -> dict[str, Any]:
    raw = _raw(state)
    _require_common_ids(raw)

    grad = tuple(_finite(v, "phase_gradients") for v in raw["phase_gradients"])
    conn = tuple(_finite(v, "connection_components") for v in raw["connection_components"])
    shift = tuple(_finite(v, "gauge_shift_components") for v in raw["gauge_shift_components"])
    velocity = tuple(_finite(v, "trajectory_velocity") for v in raw["trajectory_velocity"])

    transformed_grad = tuple(
        checked_sum(
            (g, lam),
            f"transformed_phase_gradients[{index}]",
            PNVGaugeCovariantPhasePullbackError,
        )
        for index, (g, lam) in enumerate(zip(grad, shift))
    )
    transformed_conn = tuple(
        checked_difference(
            a,
            lam,
            f"transformed_connection_components[{index}]",
            PNVGaugeCovariantPhasePullbackError,
        )
        for index, (a, lam) in enumerate(zip(conn, shift))
    )
    covariant_before = tuple(
        checked_sum(
            (g, a),
            f"covariant_before[{index}]",
            PNVGaugeCovariantPhasePullbackError,
        )
        for index, (g, a) in enumerate(zip(grad, conn))
    )
    covariant_after = tuple(
        checked_sum(
            (g, a),
            f"covariant_after[{index}]",
            PNVGaugeCovariantPhasePullbackError,
        )
        for index, (g, a) in enumerate(zip(transformed_grad, transformed_conn))
    )
    delta_gauge = max(
        abs(
            checked_difference(
                a,
                b,
                f"Delta_gauge[{index}]",
                PNVGaugeCovariantPhasePullbackError,
            )
        )
        for index, (a, b) in enumerate(zip(covariant_before, covariant_after))
    )

    opposite_before = tuple(
        checked_difference(
            g,
            a,
            f"opposite_before[{index}]",
            PNVGaugeCovariantPhasePullbackError,
        )
        for index, (g, a) in enumerate(zip(grad, conn))
    )
    opposite_after = tuple(
        checked_difference(
            g,
            a,
            f"opposite_after[{index}]",
            PNVGaugeCovariantPhasePullbackError,
        )
        for index, (g, a) in enumerate(zip(transformed_grad, transformed_conn))
    )
    opposite_sign_residual = max(
        abs(
            checked_difference(
                a,
                b,
                f"opposite_sign_residual[{index}]",
                PNVGaugeCovariantPhasePullbackError,
            )
        )
        for index, (a, b) in enumerate(zip(opposite_before, opposite_after))
    )
    if opposite_sign_residual <= 0.0:
        raise PNVGaugeCovariantPhasePullbackError(
            "gauge probe does not discriminate the admitted connection sign"
        )

    pullback_terms = [
        checked_product(
            component,
            speed,
            field=f"field_pullback_rate.term[{index}]",
            error_type=PNVGaugeCovariantPhasePullbackError,
        )
        for index, (component, speed) in enumerate(zip(covariant_before, velocity))
    ]
    field_pullback_rate = _positive(
        checked_sum(
            pullback_terms,
            "field_pullback_rate",
            PNVGaugeCovariantPhasePullbackError,
        ),
        "field_pullback_rate",
    )
    normal_rate = _positive(raw["field_normal_rate"], "field_normal_rate")
    rotor_rate = _positive(raw["rotor_rate"], "rotor_rate")

    amps = tuple(_nonnegative(v, "field amplitude") for v in raw["amplitudes"])
    vols = tuple(_positive(v, "field volume") for v in raw["volumes"])
    c_a = _field_coefficient(amps, vols)
    i_a = checked_product(
        2.0,
        c_a,
        field="I_A",
        error_type=PNVGaugeCovariantPhasePullbackError,
    )
    if i_a <= 0.0:
        raise PNVGaugeCovariantPhasePullbackError(
            "field inertia I_A must be strictly positive"
        )
    i_phi = _positive(raw["I_phi"], "I_phi")

    q_theta = checked_product(
        i_a,
        normal_rate,
        field="Q_theta",
        error_type=PNVGaugeCovariantPhasePullbackError,
    )
    p_phi = checked_product(
        i_phi,
        rotor_rate,
        field="P_Phi",
        error_type=PNVGaugeCovariantPhasePullbackError,
    )
    h_phi = checked_ratio(
        checked_product(
            p_phi,
            p_phi,
            field="P_Phi_squared",
            error_type=PNVGaugeCovariantPhasePullbackError,
        ),
        checked_product(
            2.0,
            i_phi,
            field="2I_phi",
            error_type=PNVGaugeCovariantPhasePullbackError,
        ),
        "H_Phi",
        PNVGaugeCovariantPhasePullbackError,
    )
    epsilon_n = checked_ratio(
        h_phi,
        q_theta,
        "epsilon_N",
        PNVGaugeCovariantPhasePullbackError,
    )
    half_rate = checked_ratio(
        rotor_rate,
        2.0,
        "half_rotor_rate",
        PNVGaugeCovariantPhasePullbackError,
    )

    moment_map_ratio = checked_ratio(
        q_theta,
        p_phi,
        "moment_map_ratio",
        PNVGaugeCovariantPhasePullbackError,
    )
    factorized_ratio = checked_product(
        checked_ratio(
            i_a,
            i_phi,
            "factorized_inertia_ratio",
            PNVGaugeCovariantPhasePullbackError,
        ),
        checked_ratio(
            normal_rate,
            rotor_rate,
            "factorized_rate_ratio",
            PNVGaugeCovariantPhasePullbackError,
        ),
        field="factorized_moment_map_ratio",
        error_type=PNVGaugeCovariantPhasePullbackError,
    )
    field_action = checked_product(
        c_a,
        field_pullback_rate,
        field_pullback_rate,
        field="field_phase_action",
        error_type=PNVGaugeCovariantPhasePullbackError,
    )
    rotor_action = checked_product(
        0.5,
        i_phi,
        rotor_rate,
        rotor_rate,
        field="rotor_phase_action",
        error_type=PNVGaugeCovariantPhasePullbackError,
    )

    values = {
        "transformed_phase_gradients": list(transformed_grad),
        "transformed_connection_components": list(transformed_conn),
        "gauge_probe_norm": max(abs(v) for v in shift),
        "Delta_gauge": delta_gauge,
        "opposite_sign_residual": opposite_sign_residual,
        "field_pullback_rate": field_pullback_rate,
        "field_normal_rate": normal_rate,
        "rotor_rate": rotor_rate,
        "C_A": c_a,
        "I_A": i_a,
        "I_phi": i_phi,
        "Q_theta": q_theta,
        "P_Phi": p_phi,
        "H_Phi": h_phi,
        "epsilon_N": epsilon_n,
        "half_rotor_rate": half_rate,
        "Delta_I_reduction": checked_abs_difference_ratio(
            i_phi, i_a, i_a, "Delta_I_reduction", PNVGaugeCovariantPhasePullbackError
        ),
        "Delta_rate": checked_abs_difference_ratio(
            field_pullback_rate,
            rotor_rate,
            rotor_rate,
            "Delta_rate",
            PNVGaugeCovariantPhasePullbackError,
        ),
        "Delta_normal": checked_abs_difference_ratio(
            normal_rate,
            field_pullback_rate,
            field_pullback_rate,
            "Delta_normal",
            PNVGaugeCovariantPhasePullbackError,
        ),
        "Delta_Q": checked_abs_difference_ratio(
            q_theta, p_phi, p_phi, "Delta_Q", PNVGaugeCovariantPhasePullbackError
        ),
        "Delta_epsilon": checked_abs_difference_ratio(
            epsilon_n,
            half_rate,
            half_rate,
            "Delta_epsilon",
            PNVGaugeCovariantPhasePullbackError,
        ),
        "moment_map_ratio": moment_map_ratio,
        "factorized_moment_map_ratio": factorized_ratio,
        "Delta_factorization": abs(
            checked_difference(
                moment_map_ratio,
                factorized_ratio,
                "Delta_factorization",
                PNVGaugeCovariantPhasePullbackError,
            )
        ),
        "field_phase_action": field_action,
        "rotor_phase_action": rotor_action,
        "Delta_action": checked_abs_difference_ratio(
            field_action,
            rotor_action,
            rotor_action,
            "Delta_action",
            PNVGaugeCovariantPhasePullbackError,
        ),
    }
    return finite_tree(
        values,
        "gauge_covariant_pullback_derived",
        PNVGaugeCovariantPhasePullbackError,
    )


def gauge_covariant_phase_pullback_defects(state: Mapping[str, Any]) -> dict[str, float]:
    values = _derived(state)
    names = (
        "Delta_gauge",
        "Delta_I_reduction",
        "Delta_rate",
        "Delta_normal",
        "Delta_Q",
        "Delta_epsilon",
        "Delta_factorization",
        "Delta_action",
    )
    return {name: _finite(values[name], name) for name in names}


def gauge_covariant_phase_pullback_transforms(*, tolerance: float = 1e-12) -> dict[str, Any]:
    eps = _nonnegative(tolerance, "tolerance")
    defect_names = (
        "Delta_gauge",
        "Delta_I_reduction",
        "Delta_rate",
        "Delta_normal",
        "Delta_Q",
        "Delta_epsilon",
        "Delta_factorization",
        "Delta_action",
    )

    def field_to_rotor(state: Mapping[str, Any]) -> dict[str, Any]:
        raw = _raw(state)
        values = _derived(raw)
        for name in defect_names:
            if _finite(values[name], name) > eps:
                raise PNVGaugeCovariantPhasePullbackError(
                    f"{name} {values[name]!r} exceeds tolerance {eps!r}"
                )
        return {
            **raw,
            **values,
            "representation": "GAUGE_COVARIANT_PHASE_PULLBACK_BOUND",
            "reduction_state": "COMMON_U1_MOMENT_MAP_BOUND_CANDIDATE",
        }

    def rotor_to_field(state: Mapping[str, Any]) -> dict[str, Any]:
        raw = _raw(state)
        values = _derived(raw)
        for key, expected in values.items():
            observed = state.get(key)
            if isinstance(expected, list):
                if list(observed or ()) != expected:
                    raise PNVGaugeCovariantPhasePullbackError(
                        f"{key} changed before reverse pullback audit"
                    )
            else:
                if not math.isclose(
                    _finite(observed, key),
                    _finite(expected, key),
                    rel_tol=1e-12,
                    abs_tol=1e-15,
                ):
                    raise PNVGaugeCovariantPhasePullbackError(
                        f"{key} changed before reverse pullback audit"
                    )
        for name in defect_names:
            if _finite(values[name], name) > eps:
                raise PNVGaugeCovariantPhasePullbackError(
                    f"{name} {values[name]!r} exceeds tolerance {eps!r}"
                )
        return raw

    return {
        "gauge_phase.bind_common_u1_generator": field_to_rotor,
        "gauge_phase.reconstruct_pullback_input": rotor_to_field,
    }


def _signature(state: Mapping[str, Any]) -> tuple[Any, ...]:
    raw = _raw(state)
    return (
        raw["field_bundle_id"], raw["rotor_bundle_id"],
        raw["field_phase_patch_id"], raw["rotor_phase_patch_id"],
        raw["field_connection_id"], raw["rotor_connection_id"],
        raw["field_measure_id"], raw["rotor_measure_id"],
        tuple(raw["field_cell_ids"]), tuple(raw["rotor_cell_ids"]),
    )


def _value(name: str):
    def evaluate(state: Mapping[str, Any]) -> float:
        if name in state:
            return _finite(state[name], name)
        return _finite(_derived(state)[name], name)
    return evaluate


def gauge_covariant_phase_pullback_invariants() -> dict[str, Any]:
    return {
        "SOURCE.GAUGE_PULLBACK_SIGNATURE": _signature,
        "SOURCE.GAUGE_INVARIANCE_DEFECT": _value("Delta_gauge"),
        "SOURCE.GAUGE_SIGN_DISCRIMINATION": _value("opposite_sign_residual"),
        "SOURCE.FIELD_PULLBACK_RATE": _value("field_pullback_rate"),
        "SOURCE.FIELD_NORMAL_RATE": _value("field_normal_rate"),
        "SOURCE.ROTOR_COVARIANT_RATE": _value("rotor_rate"),
        "SOURCE.FIELD_INERTIA": _value("I_A"),
        "SOURCE.ROTOR_INERTIA": _value("I_phi"),
        "SOURCE.NOETHER_COLLECTIVE_CHARGE": _value("Q_theta"),
        "SOURCE.ROTOR_KINETIC_MOMENTUM": _value("P_Phi"),
        "SOURCE.RATE_BINDING_DEFECT": _value("Delta_rate"),
        "SOURCE.NORMAL_PROJECTION_DEFECT": _value("Delta_normal"),
        "SOURCE.MOMENT_MAP_DEFECT": _value("Delta_Q"),
        "SOURCE.MOMENT_MAP_FACTORIZATION_DEFECT": _value("Delta_factorization"),
        "SOURCE.ACTION_REDUCTION_DEFECT": _value("Delta_action"),
        "SOURCE.EPSILON_PULLBACK_DEFECT": _value("Delta_epsilon"),
    }


def _law_node(law_id: str, domain: str, kaku: Kaku, refs: Sequence[str]) -> LawFrameNode:
    if not isinstance(kaku, Kaku):
        raise PNVGaugeCovariantPhasePullbackError(
            "gauge-covariant pullback law gate requires Kaku"
        )
    return LawFrameNode(law_id, domain, kaku, _refs(refs))


def build_gauge_covariant_phase_pullback_loop(
    field_kaku: Kaku,
    rotor_kaku: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    eps = _nonnegative(tolerance, "tolerance")
    refs = _refs((
        *evidence_refs,
        f"contract:{GAUGE_COVARIANT_PULLBACK_CONTRACT}",
        "gate:common_u1_bundle:CONDITIONAL",
        "gate:common_phase_patch:CONDITIONAL",
        "gate:common_abe_connection:CONDITIONAL",
        "gate:common_measure_support:CONDITIONAL",
        "gate:normal_flow_alignment:CONDITIONAL",
    ))
    field = _law_node(
        "LAW.NOETHER.GAUGE_COVARIANT_SCALAR_PHASE",
        "EULER_NOETHER_FIELD",
        field_kaku,
        refs,
    )
    rotor = _law_node(
        "LAW.PHASE.GAUGE_COVARIANT_CANONICAL_ROTOR",
        "IDT_PHASE_HAMILTONIAN",
        rotor_kaku,
        refs,
    )
    return InformationHolonomyLoop(
        loop_id=GAUGE_COVARIANT_PULLBACK_LOOP_ID,
        connection=information_transport_connection(
            "PNCS_GAUGE_COVARIANT_PHASE_PULLBACK_STATE_SPACE_V0_1",
            evidence_refs=refs,
        ),
        nodes=(field, rotor),
        transports=(
            LawTransport(
                "EDGE.GAUGE_FIELD.TO_ROTOR_PULLBACK",
                field.node_id,
                rotor.node_id,
                "gauge_phase.bind_common_u1_generator",
                refs,
            ),
            LawTransport(
                "EDGE.ROTOR.TO_GAUGE_FIELD_INPUT",
                rotor.node_id,
                field.node_id,
                "gauge_phase.reconstruct_pullback_input",
                refs,
            ),
        ),
        invariants=tuple(
            HolonomyInvariant(invariant_id, tolerance=eps)
            for invariant_id in gauge_covariant_phase_pullback_invariants()
        ),
        evidence_refs=refs,
    )


__all__ = [
    "GAUGE_COVARIANT_PULLBACK_CONTRACT",
    "GAUGE_COVARIANT_PULLBACK_LOOP_ID",
    "PNVGaugeCovariantPhasePullbackError",
    "make_gauge_covariant_phase_pullback_state",
    "gauge_covariant_phase_pullback_defects",
    "gauge_covariant_phase_pullback_transforms",
    "gauge_covariant_phase_pullback_invariants",
    "build_gauge_covariant_phase_pullback_loop",
]
