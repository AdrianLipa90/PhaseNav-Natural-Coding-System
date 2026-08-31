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

SCALAR_FIELD_ROTOR_CONTRACT = "PNCS_PNV_SCALAR_FIELD_ROTOR_INERTIA_REDUCTION_V0_1"
SCALAR_FIELD_ROTOR_LOOP_ID = "SOURCE.PHASE_NOETHER.ROTOR_INERTIA.REDUCTION.ROUNDTRIP"


class PNVScalarFieldRotorReductionError(PNVInformationHolonomyError):
    pass


def _finite(value: Any, field: str) -> float:
    return finite_float(value, field, PNVScalarFieldRotorReductionError)


def _positive(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out <= 0.0:
        raise PNVScalarFieldRotorReductionError(f"{field} must be strictly positive")
    return out


def _nonnegative(value: Any, field: str) -> float:
    out = _finite(value, field)
    if out < 0.0:
        raise PNVScalarFieldRotorReductionError(f"{field} must be non-negative")
    return out


def _refs(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(value) for value in values if str(value)}))


def _ids(values: Sequence[str], field: str) -> tuple[str, ...]:
    out = tuple(str(value) for value in values)
    if not out or any(not value for value in out):
        raise PNVScalarFieldRotorReductionError(f"{field} requires non-empty identifiers")
    if len(set(out)) != len(out):
        raise PNVScalarFieldRotorReductionError(f"{field} identifiers must be unique")
    return out


def _law_node(law_id: str, domain: str, kaku: Kaku, refs: Sequence[str]) -> LawFrameNode:
    if not isinstance(kaku, Kaku):
        raise PNVScalarFieldRotorReductionError("scalar-field/rotor law gate requires Kaku")
    return LawFrameNode(law_id, domain, kaku, _refs(refs))


def _field_coefficient(amplitudes: Sequence[float], volumes: Sequence[float]) -> float:
    terms = []
    for index, (amplitude, volume) in enumerate(zip(amplitudes, volumes)):
        a_sq = checked_product(
            amplitude,
            amplitude,
            field=f"field_coefficient.amplitude_squared[{index}]",
            error_type=PNVScalarFieldRotorReductionError,
        )
        terms.append(
            checked_product(
                a_sq,
                volume,
                field=f"field_coefficient.term[{index}]",
                error_type=PNVScalarFieldRotorReductionError,
            )
        )
    return checked_sum(terms, "field_coefficient", PNVScalarFieldRotorReductionError)


def make_scalar_field_rotor_state(
    *,
    field_phase_mode_id: str,
    rotor_phase_mode_id: str,
    field_rate_id: str,
    rotor_rate_id: str,
    field_measure_id: str,
    rotor_measure_id: str,
    field_cell_ids: Sequence[str],
    rotor_cell_ids: Sequence[str],
    amplitudes: Sequence[float],
    volumes: Sequence[float],
    d_tau_chi: float,
    i_phi: float,
    j_i: float = 0.0,
) -> dict[str, Any]:
    mode_field = str(field_phase_mode_id)
    mode_rotor = str(rotor_phase_mode_id)
    rate_field = str(field_rate_id)
    rate_rotor = str(rotor_rate_id)
    measure_field = str(field_measure_id)
    measure_rotor = str(rotor_measure_id)
    if not all((mode_field, mode_rotor, rate_field, rate_rotor, measure_field, measure_rotor)):
        raise PNVScalarFieldRotorReductionError("phase-mode, rate and measure identifiers are required")

    ids_field = _ids(field_cell_ids, "field_cell_ids")
    ids_rotor = _ids(rotor_cell_ids, "rotor_cell_ids")
    amps = tuple(_nonnegative(value, "field amplitude") for value in amplitudes)
    vols = tuple(_positive(value, "field volume") for value in volumes)
    if len(ids_field) != len(amps) or len(ids_field) != len(vols):
        raise PNVScalarFieldRotorReductionError("field cell/amplitude/volume support mismatch")
    if len(ids_rotor) != len(ids_field):
        raise PNVScalarFieldRotorReductionError("field/rotor support cardinality mismatch")

    rate = _positive(d_tau_chi, "D_tau_chi")
    rotor_inertia = _positive(i_phi, "I_phi")
    intention = _finite(j_i, "J_I")
    coefficient = _field_coefficient(amps, vols)
    i_a = checked_product(
        2.0,
        coefficient,
        field="I_A",
        error_type=PNVScalarFieldRotorReductionError,
    )
    if i_a <= 0.0:
        raise PNVScalarFieldRotorReductionError("field inertia I_A must be strictly positive")

    return {
        "schema": "PNCS_SCALAR_FIELD_ROTOR_REDUCTION_STATE_V0_1",
        "representation": "SCALAR_FIELD_ROTOR_REDUCTION_INPUT",
        "field_phase_mode_id": mode_field,
        "rotor_phase_mode_id": mode_rotor,
        "field_rate_id": rate_field,
        "rotor_rate_id": rate_rotor,
        "field_measure_id": measure_field,
        "rotor_measure_id": measure_rotor,
        "field_cell_ids": list(ids_field),
        "rotor_cell_ids": list(ids_rotor),
        "amplitudes": list(amps),
        "volumes": list(vols),
        "D_tau_chi": rate,
        "I_phi": rotor_inertia,
        "J_I": intention,
    }


def _raw(state: Mapping[str, Any]) -> dict[str, Any]:
    return make_scalar_field_rotor_state(
        field_phase_mode_id=str(state.get("field_phase_mode_id", "")),
        rotor_phase_mode_id=str(state.get("rotor_phase_mode_id", "")),
        field_rate_id=str(state.get("field_rate_id", "")),
        rotor_rate_id=str(state.get("rotor_rate_id", "")),
        field_measure_id=str(state.get("field_measure_id", "")),
        rotor_measure_id=str(state.get("rotor_measure_id", "")),
        field_cell_ids=state.get("field_cell_ids", ()),
        rotor_cell_ids=state.get("rotor_cell_ids", ()),
        amplitudes=state.get("amplitudes", ()),
        volumes=state.get("volumes", ()),
        d_tau_chi=state.get("D_tau_chi"),
        i_phi=state.get("I_phi"),
        j_i=state.get("J_I", 0.0),
    )


def _derived(state: Mapping[str, Any]) -> dict[str, Any]:
    raw = _raw(state)
    if raw["field_phase_mode_id"] != raw["rotor_phase_mode_id"]:
        raise PNVScalarFieldRotorReductionError("field and rotor phase-mode IDs differ")
    if raw["field_rate_id"] != raw["rotor_rate_id"]:
        raise PNVScalarFieldRotorReductionError("field and rotor covariant-rate IDs differ")
    if raw["field_measure_id"] != raw["rotor_measure_id"]:
        raise PNVScalarFieldRotorReductionError("field and rotor measure IDs differ")
    if raw["field_cell_ids"] != raw["rotor_cell_ids"]:
        raise PNVScalarFieldRotorReductionError("field and rotor collective supports differ")

    amps = tuple(_finite(value, "field amplitude") for value in raw["amplitudes"])
    vols = tuple(_positive(value, "field volume") for value in raw["volumes"])
    rate = _positive(raw["D_tau_chi"], "D_tau_chi")
    i_phi = _positive(raw["I_phi"], "I_phi")
    j_i = _finite(raw["J_I"], "J_I")

    field_coefficient = _field_coefficient(amps, vols)
    i_a = checked_product(
        2.0,
        field_coefficient,
        field="I_A",
        error_type=PNVScalarFieldRotorReductionError,
    )
    rotor_coefficient = checked_ratio(
        i_phi,
        2.0,
        "rotor_phase_coefficient",
        PNVScalarFieldRotorReductionError,
    )
    q_theta = checked_product(
        i_a,
        rate,
        field="Q_theta",
        error_type=PNVScalarFieldRotorReductionError,
    )
    p_phi = checked_product(
        i_phi,
        rate,
        field="P_Phi",
        error_type=PNVScalarFieldRotorReductionError,
    )
    p_phi_sq = checked_product(
        p_phi,
        p_phi,
        field="P_Phi_squared",
        error_type=PNVScalarFieldRotorReductionError,
    )
    h_phi = checked_ratio(
        p_phi_sq,
        checked_product(
            2.0,
            i_phi,
            field="2I_phi",
            error_type=PNVScalarFieldRotorReductionError,
        ),
        "H_Phi",
        PNVScalarFieldRotorReductionError,
    )
    epsilon_n = checked_ratio(
        h_phi,
        q_theta,
        "epsilon_N",
        PNVScalarFieldRotorReductionError,
    )
    half_rate = checked_ratio(
        rate,
        2.0,
        "half_phase_rate",
        PNVScalarFieldRotorReductionError,
    )

    delta_i = checked_abs_difference_ratio(
        i_phi,
        i_a,
        i_a,
        "Delta_I_reduction",
        PNVScalarFieldRotorReductionError,
    )
    delta_coefficient = checked_abs_difference_ratio(
        rotor_coefficient,
        field_coefficient,
        field_coefficient,
        "Delta_coefficient",
        PNVScalarFieldRotorReductionError,
    )
    delta_q = checked_abs_difference_ratio(
        p_phi,
        q_theta,
        q_theta,
        "Delta_Q_reduction",
        PNVScalarFieldRotorReductionError,
    )
    delta_epsilon = checked_abs_difference_ratio(
        epsilon_n,
        half_rate,
        half_rate,
        "Delta_epsilon_reduction",
        PNVScalarFieldRotorReductionError,
    )

    identity_residual = max(
        abs(
            checked_difference(
                delta_i,
                delta_coefficient,
                "Delta_identity_residual.I_coeff",
                PNVScalarFieldRotorReductionError,
            )
        ),
        abs(
            checked_difference(
                delta_i,
                delta_q,
                "Delta_identity_residual.I_Q",
                PNVScalarFieldRotorReductionError,
            )
        ),
        abs(
            checked_difference(
                delta_i,
                delta_epsilon,
                "Delta_identity_residual.I_epsilon",
                PNVScalarFieldRotorReductionError,
            )
        ),
    )
    identity_residual = _finite(identity_residual, "Delta_identity_residual")
    if identity_residual > 1e-12:
        raise PNVScalarFieldRotorReductionError("scalar-field/rotor defect identity violated")

    rate_sq = checked_product(
        rate,
        rate,
        field="phase_rate_squared",
        error_type=PNVScalarFieldRotorReductionError,
    )
    field_phase_lagrangian = checked_product(
        field_coefficient,
        rate_sq,
        field="field_phase_lagrangian",
        error_type=PNVScalarFieldRotorReductionError,
    )
    rotor_phase_kinetic = checked_product(
        rotor_coefficient,
        rate_sq,
        field="rotor_phase_kinetic",
        error_type=PNVScalarFieldRotorReductionError,
    )
    intention_term = checked_product(
        j_i,
        rate,
        field="intention_phase_term",
        error_type=PNVScalarFieldRotorReductionError,
    )
    rotor_phase_with_intention = checked_sum(
        (rotor_phase_kinetic, intention_term),
        "rotor_phase_with_intention",
        PNVScalarFieldRotorReductionError,
    )

    return finite_tree(
        {
            "I_A": i_a,
            "I_phi": i_phi,
            "field_phase_coefficient": field_coefficient,
            "rotor_phase_coefficient": rotor_coefficient,
            "Q_theta": q_theta,
            "P_Phi": p_phi,
            "H_Phi": h_phi,
            "epsilon_N": epsilon_n,
            "half_phase_rate": half_rate,
            "Delta_I_reduction": delta_i,
            "Delta_coefficient": delta_coefficient,
            "Delta_Q_reduction": delta_q,
            "Delta_epsilon_reduction": delta_epsilon,
            "Delta_identity_residual": identity_residual,
            "field_phase_lagrangian": field_phase_lagrangian,
            "rotor_phase_kinetic": rotor_phase_kinetic,
            "rotor_phase_with_intention": rotor_phase_with_intention,
        },
        "scalar_field_rotor_derived",
        PNVScalarFieldRotorReductionError,
    )


def scalar_field_rotor_reduction_defects(state: Mapping[str, Any]) -> dict[str, float]:
    values = _derived(state)
    return {
        "Delta_I_reduction": _finite(values["Delta_I_reduction"], "Delta_I_reduction"),
        "Delta_coefficient": _finite(values["Delta_coefficient"], "Delta_coefficient"),
        "Delta_Q_reduction": _finite(values["Delta_Q_reduction"], "Delta_Q_reduction"),
        "Delta_epsilon_reduction": _finite(values["Delta_epsilon_reduction"], "Delta_epsilon_reduction"),
        "Delta_identity_residual": _finite(values["Delta_identity_residual"], "Delta_identity_residual"),
    }


def scalar_field_rotor_reduction_transforms(*, reduction_tolerance: float = 0.0) -> dict[str, Any]:
    tolerance = _nonnegative(reduction_tolerance, "reduction_tolerance")

    def field_to_rotor(state: Mapping[str, Any]) -> dict[str, Any]:
        raw = _raw(state)
        values = _derived(raw)
        if values["Delta_I_reduction"] > tolerance:
            raise PNVScalarFieldRotorReductionError(
                f"inertia reduction defect {values['Delta_I_reduction']!r} exceeds tolerance {tolerance!r}"
            )
        return {
            **raw,
            **values,
            "representation": "SCALAR_FIELD_ROTOR_REDUCTION_BOUND",
            "reduction_state": "COLLECTIVE_COEFFICIENT_BOUND_CANDIDATE",
        }

    def rotor_to_field(state: Mapping[str, Any]) -> dict[str, Any]:
        raw = _raw(state)
        values = _derived(raw)
        for key in (
            "I_A",
            "I_phi",
            "field_phase_coefficient",
            "rotor_phase_coefficient",
            "Q_theta",
            "P_Phi",
            "H_Phi",
            "epsilon_N",
            "half_phase_rate",
            "Delta_I_reduction",
            "Delta_coefficient",
            "Delta_Q_reduction",
            "Delta_epsilon_reduction",
            "Delta_identity_residual",
            "field_phase_lagrangian",
            "rotor_phase_kinetic",
            "rotor_phase_with_intention",
        ):
            observed = _finite(state.get(key), key)
            expected = _finite(values[key], key)
            if not math.isclose(observed, expected, rel_tol=1e-12, abs_tol=1e-15):
                raise PNVScalarFieldRotorReductionError(f"{key} changed before reverse reduction audit")
        if values["Delta_I_reduction"] > tolerance:
            raise PNVScalarFieldRotorReductionError(
                f"inertia reduction defect {values['Delta_I_reduction']!r} exceeds tolerance {tolerance!r}"
            )
        return raw

    return {
        "scalar_field.bind_rotor_inertia": field_to_rotor,
        "scalar_field.reconstruct_reduction_input": rotor_to_field,
    }


def _signature(state: Mapping[str, Any]) -> tuple[Any, ...]:
    raw = _raw(state)
    return (
        raw["field_phase_mode_id"],
        raw["rotor_phase_mode_id"],
        raw["field_rate_id"],
        raw["rotor_rate_id"],
        raw["field_measure_id"],
        raw["rotor_measure_id"],
        tuple(raw["field_cell_ids"]),
        tuple(raw["rotor_cell_ids"]),
    )


def _value(name: str):
    def evaluate(state: Mapping[str, Any]) -> float:
        if name in state:
            return _finite(state[name], name)
        return _finite(_derived(state)[name], name)
    return evaluate


def scalar_field_rotor_reduction_invariants() -> dict[str, Any]:
    return {
        "SOURCE.COLLECTIVE_REDUCTION_SIGNATURE": _signature,
        "SOURCE.FIELD_PHASE_COEFFICIENT": _value("field_phase_coefficient"),
        "SOURCE.ROTOR_PHASE_COEFFICIENT": _value("rotor_phase_coefficient"),
        "SOURCE.FIELD_INERTIA": _value("I_A"),
        "SOURCE.ROTOR_INERTIA": _value("I_phi"),
        "SOURCE.NOETHER_COLLECTIVE_CHARGE": _value("Q_theta"),
        "SOURCE.ROTOR_KINETIC_MOMENTUM": _value("P_Phi"),
        "SOURCE.ROTOR_PHASE_ENERGY": _value("H_Phi"),
        "SOURCE.NOETHER_ENERGY_PER_CHARGE": _value("epsilon_N"),
        "SOURCE.HALF_PHASE_RATE": _value("half_phase_rate"),
        "SOURCE.INERTIA_REDUCTION_DEFECT": _value("Delta_I_reduction"),
        "SOURCE.CARRIER_REDUCTION_DEFECT": _value("Delta_Q_reduction"),
        "SOURCE.EPSILON_REDUCTION_DEFECT": _value("Delta_epsilon_reduction"),
        "SOURCE.REDUCTION_DEFECT_IDENTITY_RESIDUAL": _value("Delta_identity_residual"),
    }


def build_scalar_field_rotor_reduction_loop(
    field_kaku: Kaku,
    rotor_kaku: Kaku,
    *,
    evidence_refs: Sequence[str] = (),
    tolerance: float = 1e-12,
) -> InformationHolonomyLoop:
    if not isinstance(field_kaku, Kaku) or not isinstance(rotor_kaku, Kaku):
        raise PNVScalarFieldRotorReductionError("scalar-field/rotor reduction law gates require Kaku")
    eps = _nonnegative(tolerance, "tolerance")
    refs = _refs(
        (
            *evidence_refs,
            f"contract:{SCALAR_FIELD_ROTOR_CONTRACT}",
            "gate:same_phase_mode:CONDITIONAL",
            "gate:same_covariant_rate:CONDITIONAL",
            "gate:same_measure:CONDITIONAL",
            "gate:same_collective_support:CONDITIONAL",
        )
    )
    field = _law_node(
        "LAW.NOETHER.SCALAR_FIELD_PHASE_MODE",
        "EULER_NOETHER_FIELD",
        field_kaku,
        refs,
    )
    rotor = _law_node(
        "LAW.PHASE.CANONICAL_ROTOR_MODE",
        "IDT_PHASE_HAMILTONIAN",
        rotor_kaku,
        refs,
    )
    return InformationHolonomyLoop(
        loop_id=SCALAR_FIELD_ROTOR_LOOP_ID,
        connection=information_transport_connection(
            "PNCS_SCALAR_FIELD_ROTOR_REDUCTION_STATE_SPACE_V0_1",
            evidence_refs=refs,
        ),
        nodes=(field, rotor),
        transports=(
            LawTransport(
                "EDGE.FIELD_PHASE.TO_ROTOR_INERTIA",
                field.node_id,
                rotor.node_id,
                "scalar_field.bind_rotor_inertia",
                refs,
            ),
            LawTransport(
                "EDGE.ROTOR_INERTIA.TO_FIELD_INPUT",
                rotor.node_id,
                field.node_id,
                "scalar_field.reconstruct_reduction_input",
                refs,
            ),
        ),
        invariants=(
            HolonomyInvariant("SOURCE.COLLECTIVE_REDUCTION_SIGNATURE", "EXACT", 0.0),
            HolonomyInvariant("SOURCE.FIELD_PHASE_COEFFICIENT", "ABS", eps),
            HolonomyInvariant("SOURCE.ROTOR_PHASE_COEFFICIENT", "ABS", eps),
            HolonomyInvariant("SOURCE.FIELD_INERTIA", "ABS", eps),
            HolonomyInvariant("SOURCE.ROTOR_INERTIA", "ABS", eps),
            HolonomyInvariant("SOURCE.NOETHER_COLLECTIVE_CHARGE", "ABS", eps),
            HolonomyInvariant("SOURCE.ROTOR_KINETIC_MOMENTUM", "ABS", eps),
            HolonomyInvariant("SOURCE.ROTOR_PHASE_ENERGY", "ABS", eps),
            HolonomyInvariant("SOURCE.NOETHER_ENERGY_PER_CHARGE", "ABS", eps),
            HolonomyInvariant("SOURCE.HALF_PHASE_RATE", "ABS", eps),
            HolonomyInvariant("SOURCE.INERTIA_REDUCTION_DEFECT", "ABS", eps),
            HolonomyInvariant("SOURCE.CARRIER_REDUCTION_DEFECT", "ABS", eps),
            HolonomyInvariant("SOURCE.EPSILON_REDUCTION_DEFECT", "ABS", eps),
            HolonomyInvariant("SOURCE.REDUCTION_DEFECT_IDENTITY_RESIDUAL", "ABS", eps),
        ),
        evidence_refs=refs,
    )
