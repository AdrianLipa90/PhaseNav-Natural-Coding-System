from __future__ import annotations

import cmath
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Sequence

from .gremlin_relational_compiler_v01 import (
    RelationalCompilation,
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
    compile_relational_isomorphism,
    validate_compiled_relational_candidate,
)
from .model import Kaku, Vector36

BANK_SCHEMA = "PNCS_GREMLIN_CROSS_FORMALISM_ISOMORPHISM_BANK_V0_2"
COMPILATION_SCHEMA = "PNCS_GREMLIN_CROSS_FORMALISM_COMPILATION_V0_2"
BASIS = "pncs:t36:gremlin-cross-formalism-bank:v2"

SOURCE_PINS: Mapping[str, Mapping[str, str]] = {
    "TIR": {
        "repository": "AdrianLipa90/The-Fundamental-Theory-of-Informational-Relations",
        "commit": "26bd867c10b6f6e21b54f2a4dc7b2f49df62907a",
    },
    "IDT": {
        "repository": "AdrianLipa90/Informational-Dynamics-of-Time",
        "commit": "3ac1f53af5223d16f8818dba99a63a6af2ba9498",
    },
    "RFC": {
        "repository": "AdrianLipa90/Relational-Field-Closure",
        "commit": "3ebd7761ccfa70858ab8af1933c2208a82260f9d",
    },
    "SOH": {
        "repository": "AdrianLipa90/secret-of-a-half",
        "commit": "4cf36453ee2b6d33a1f9177ca324b9ef491270be",
    },
    "ZPE": {
        "repository": "AdrianLipa90/Zero-Point-Energy",
        "commit": "7caf8474852ac733d290313d9026f5ffc03f0c9a",
    },
}

ALLOWED_CLASSES = {
    "EXACT",
    "EXACT_CONDITIONAL",
    "EXACT_STRUCTURAL",
    "STRONG_STRUCTURAL",
    "SUPPORTED_EXTENSION",
}


class CrossFormalismBankError(RuntimeError):
    pass


@dataclass(frozen=True)
class CrossFormalismEntry:
    spec: RelationalIsomorphism
    classification: str
    preserved_structure: tuple[str, ...]
    falsification_gate: str
    guardrails: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.classification not in ALLOWED_CLASSES:
            raise CrossFormalismBankError(f"unsupported classification: {self.classification}")
        if not self.preserved_structure or not self.falsification_gate:
            raise CrossFormalismBankError("entry requires preserved structure and falsification gate")


@dataclass(frozen=True)
class CrossFormalismCompilation:
    compilations: Mapping[str, RelationalCompilation]
    manifest: Mapping[str, object]


def _source(bank: str, path: str) -> str:
    pin = SOURCE_PINS[bank]
    return f"github:{pin['repository']}@{pin['commit']}:{path}"


def _vector(seed: int) -> Vector36:
    values = tuple(((seed * 53 + i * 23) % 263) / 263.0 for i in range(36))
    return Vector36(values, BASIS)


def _kaku(kaku_id: str, seed: int, role: str) -> Kaku:
    return Kaku(
        kaku_id,
        _vector(seed),
        1.0 + seed / 17.0,
        "FORWARD",
        1.0,
        role,
        tuple(((seed * 7 + i) % 36) / 36.0 for i in range(36)),
    )


def _node(kaku_id: str, seed: int, role: str, domain: str, observation_ref: str) -> RelationalNode:
    return RelationalNode(_kaku(kaku_id, seed, role), domain, observation_ref)


def _entry2(
    *,
    iso_id: str,
    invariant_id: str,
    invariant_description: str,
    left: RelationalNode,
    right: RelationalNode,
    relation_type: str,
    refs: tuple[str, ...],
    classification: str,
    preserved: tuple[str, ...],
    falsifier: str,
    guardrails: tuple[str, ...],
) -> CrossFormalismEntry:
    return CrossFormalismEntry(
        spec=RelationalIsomorphism(
            isomorphism_id=iso_id,
            invariant_id=invariant_id,
            invariant_description=invariant_description,
            nodes=(left, right),
            edges=(RelationalEdge(f"REL.{iso_id}", left.kaku.kaku_id, right.kaku.kaku_id, relation_type),),
            evidence_refs=refs,
        ),
        classification=classification,
        preserved_structure=preserved,
        falsification_gate=falsifier,
        guardrails=guardrails,
    )


def cross_formalism_bank() -> tuple[CrossFormalismEntry, ...]:
    soh = _node("K.XFI.SOH.SPINOR", 5, "su2_double_cover_central_sign", "SOH", "SOH:G013-SPINOR-LIFT")
    horizon = _node("K.XFI.IDT.HORIZON.SPIN", 6, "horizon_spin_half_antiperiodicity", "IDT_HORIZON", "IDT:01AI")
    zpe_wilson = _node("K.XFI.ZPE.WILSON", 7, "field_bound_su2_wilson_sector", "ZPE_FIELD", "ZPE:STAGE4-WILSON")

    idt_action = _node("K.XFI.IDT.ACTION.AREA", 14, "memory_action_area_holonomy", "IDT_ACTION_AREA", "IDT:GREMLIN-ACTION-AREA")
    zpe_bargmann = _node("K.XFI.ZPE.BARGMANN", 15, "projective_bargmann_loop", "ZPE_PROJECTIVE", "ZPE:STAGE3-BARGMANN")
    zpe_field = _node("K.XFI.ZPE.FIELD.WILSON", 16, "field_derived_wilson_loop", "ZPE_FIELD_HOLONOMY", "ZPE:STAGE4-WILSON")

    idt_scale = _node("K.XFI.IDT.EXTENSIVE.SHAPE", 11, "extensive_scale_normalized_shape", "IDT_EXTENSIVE", "IDT:01X")
    zpe_direction = _node("K.XFI.ZPE.FIELD.DIRECTION", 12, "field_magnitude_projective_direction", "ZPE_FIELD", "ZPE:STAGE4")
    zpe_rotor = _node("K.XFI.ZPE.ROTOR.SCALE", 13, "rotor_scale_normalized_ratio", "ZPE_ROTOR", "ZPE:STAGE2")

    return (
        _entry2(
            iso_id="XFI.01.EXACT.COBOUNDARY.HOLONOMY.NULL",
            invariant_id="INV.XFI.EXACT.ONE.COBBOUNDARY.CLOSURE",
            invariant_description="an exact edge difference has zero additive circulation and its exponentiated representation has trivial multiplicative loop holonomy",
            left=_node("K.XFI.IDT.EXACT.DRIVE", 1, "exact_scalar_edge_drive", "IDT_KINETICS", "IDT:00C-T009A"),
            right=_node("K.XFI.ZPE.SCALAR.LINK", 2, "scalar_phase_difference_link", "ZPE_U1", "ZPE:STAGE2-U1"),
            relation_type="ISOMORPHIC_TO",
            refs=(
                _source("IDT", "formalism/00C_relational_density_viscosity.md"),
                _source("ZPE", "theory/TIR_DERIVATION_STAGE2.md"),
            ),
            classification="EXACT",
            preserved=("closed exact circulation = 0", "exponentiated closed holonomy = 1"),
            falsifier="closed exact cycle with nonzero additive circulation or non-unit exponentiated closure",
            guardrails=("edge field must be explicitly constructed from one scalar state function",),
        ),
        _entry2(
            iso_id="XFI.02.TIR.CP.PLAQUETTE.BARGMANN.QUAD",
            invariant_id="INV.XFI.LOCAL.REPHASING.CANCELS",
            invariant_description="under the explicit overlap realization W_ab=<psi_a|psi_b>, the TIR CP plaquette is a four-vertex Bargmann closed product",
            left=_node("K.XFI.TIR.CP.PLAQUETTE", 3, "tir_rephasing_invariant_cp_plaquette", "TIR_CP", "TIR:STAGE36-PLAQUETTE"),
            right=_node("K.XFI.ZPE.BARGMANN.QUAD", 4, "four_vertex_bargmann_product", "ZPE_PROJECTIVE", "ZPE:STAGE3-BARGMANN"),
            relation_type="ISOMORPHIC_TO",
            refs=(
                _source("TIR", "TIR/frozen_predictions/validation/TIR_POLYGONAL_EXCITATION_STAGE36_COMPLEX_HOLONOMY_CP_V0_1.md"),
                _source("ZPE", "theory/TIR_PROJECTIVE_HOLONOMY_STAGE3.md"),
            ),
            classification="EXACT_CONDITIONAL",
            preserved=("complex closed-product value", "local U(1) rephasing invariance", "loop orientation"),
            falsifier="independent local rephasing changes the plaquette after overlap realization",
            guardrails=("exact identity activates only after W_ab is explicitly realized as a state overlap",),
        ),
        CrossFormalismEntry(
            spec=RelationalIsomorphism(
                isomorphism_id="XFI.03.SPINOR.CENTRAL.SIGN.TRIPLE",
                invariant_id="INV.XFI.SPINOR.TWO.PI.MINUS.FOUR.PI.PLUS",
                invariant_description="the SU2 double cover, the Euclidean-horizon spin-half thermal circle and field-bound Wilson sectors share the central 2pi->-1 and 4pi->+1 spinor lift",
                nodes=(soh, horizon, zpe_wilson),
                edges=(
                    RelationalEdge("REL.XFI.03.A", soh.kaku.kaku_id, horizon.kaku.kaku_id, "ISOMORPHIC_TO"),
                    RelationalEdge("REL.XFI.03.B", horizon.kaku.kaku_id, zpe_wilson.kaku.kaku_id, "ISOMORPHIC_TO"),
                ),
                evidence_refs=(
                    _source("SOH", "research/SOH_G013_PAULI_SPINOR_LIFT_V0_1.md"),
                    _source("IDT", "formalism/01AI_horizon_spin_half_thermal_antiperiodicity.md"),
                    _source("ZPE", "theory/TIR_FIELD_HOLONOMY_STAGE4.md"),
                ),
            ),
            classification="EXACT_STRUCTURAL",
            preserved_structure=("central -I after 2pi", "central +I after 4pi", "integer-turn parity witness"),
            falsification_gate="spin-half lift returns +1 at 2pi or -1 at 4pi",
            guardrails=("physical connections remain source-typed while representation-theoretic central sign is compared",),
        ),
        _entry2(
            iso_id="XFI.04.SHAPE.SCALE.DEFECT.TRIANGLE",
            invariant_id="INV.XFI.EXTENSIVE.DEFECT.BOUNDED.BY.SHAPE.PLUS.SCALE",
            invariant_description="for normalized positive shapes, the relative extensive L1 defect is bounded by normalized-shape drift plus positive-scale drift",
            left=_node("K.XFI.IDT.SHAPE.SCALE", 8, "normalized_shape_explicit_scale_lift", "IDT_SHAPE_SCALE", "IDT:01X"),
            right=_node("K.XFI.IDT.DEFECT.SPLIT", 9, "independent_local_global_defect_accounting", "IDT_DEFECT_THEOREM", "IDT:01AA"),
            relation_type="ISOMORPHIC_TO",
            refs=(
                _source("IDT", "formalism/01X_RFC_normalized_shape_extensive_scale_interface.md"),
                _source("IDT", "formalism/01AA_noether_rfc_conserved_current_binding.md"),
            ),
            classification="EXACT",
            preserved=("shape/scale coordinate independence", "triangle-inequality defect bound", "positive normalized shape"),
            falsifier="positive normalized shapes and positive scales violate D_ext <= D_shape + D_scale",
            guardrails=("shape vectors are validated on the positive normalized simplex before applying the theorem",),
        ),
        _entry2(
            iso_id="XFI.05.RAY.QUOTIENT.PROJECTIVE.QUOTIENT",
            invariant_id="INV.XFI.GLOBAL.ONE.PARAMETER.FIBER.QUOTIENT",
            invariant_description="positive-ray normalization and U1 projectivization both quotient one global one-parameter orbit while preserving relational shape",
            left=_node("K.XFI.IDT.POSITIVE.RAY", 10, "positive_ray_to_simplex_quotient", "IDT_SIMPLEX", "IDT:01X-RAY"),
            right=_node("K.XFI.ZPE.U1.PROJECTIVE", 17, "global_phase_to_projective_quotient", "ZPE_CP", "ZPE:STAGE3-PROJECTIVE"),
            relation_type="ISOMORPHIC_TO",
            refs=(
                _source("IDT", "formalism/01X_RFC_normalized_shape_extensive_scale_interface.md"),
                _source("ZPE", "theory/TIR_PROJECTIVE_HOLONOMY_STAGE3.md"),
            ),
            classification="STRONG_STRUCTURAL",
            preserved=("relational shape", "one global fiber coordinate removed", "quotient-state identity"),
            falsifier="positive rescaling changes simplex shape or global phase changes projective overlap magnitudes",
            guardrails=("quotient groups and metric structures retain their source-domain types",),
        ),
        CrossFormalismEntry(
            spec=RelationalIsomorphism(
                isomorphism_id="XFI.06.SCALE.DIRECTION.FIBRATION",
                invariant_id="INV.XFI.POSITIVE.SCALE.NORMALIZED.DIRECTION",
                invariant_description="extensive carriers, field vectors and rotor rates independently factor into a positive/global scale coordinate and a normalized relational shape or direction coordinate",
                nodes=(idt_scale, zpe_direction, zpe_rotor),
                edges=(
                    RelationalEdge("REL.XFI.06.A", idt_scale.kaku.kaku_id, zpe_direction.kaku.kaku_id, "ISOMORPHIC_TO"),
                    RelationalEdge("REL.XFI.06.B", idt_scale.kaku.kaku_id, zpe_rotor.kaku.kaku_id, "ISOMORPHIC_TO"),
                ),
                evidence_refs=(
                    _source("IDT", "formalism/01X_RFC_normalized_shape_extensive_scale_interface.md"),
                    _source("ZPE", "theory/TIR_FIELD_HOLONOMY_STAGE4.md"),
                    _source("ZPE", "theory/TIR_DERIVATION_STAGE2.md"),
                ),
            ),
            classification="STRONG_STRUCTURAL",
            preserved_structure=("normalized direction under positive rescaling", "separate scale fiber", "explicit scale provenance"),
            falsification_gate="positive scale-only transformation changes the declared normalized relational coordinate",
            guardrails=("direction and scale drift are audited as separate coordinates",),
        ),
        CrossFormalismEntry(
            spec=RelationalIsomorphism(
                isomorphism_id="XFI.07.ACTION.AREA.HOLONOMY.EXTENSION",
                invariant_id="INV.XFI.ORIENTED.CLOSED.PATH.HOLONOMY",
                invariant_description="the existing action-area-memory-Berry GREMLIN spine extends to projective Bargmann loops and field-derived Wilson loops as separately typed oriented closed-path observables",
                nodes=(idt_action, zpe_bargmann, zpe_field),
                edges=(
                    RelationalEdge("REL.XFI.07.A", idt_action.kaku.kaku_id, zpe_bargmann.kaku.kaku_id, "MAPS_TO"),
                    RelationalEdge("REL.XFI.07.B", idt_action.kaku.kaku_id, zpe_field.kaku.kaku_id, "MAPS_TO"),
                ),
                evidence_refs=(
                    _source("IDT", "validation/gremlin/ACTION_AREA_HOLONOMY_V0_1.md"),
                    _source("IDT", "formalism/00D_memory_orbit_drive.md"),
                    _source("ZPE", "theory/TIR_PROJECTIVE_HOLONOMY_STAGE3.md"),
                    _source("ZPE", "theory/TIR_FIELD_HOLONOMY_STAGE4.md"),
                ),
            ),
            classification="SUPPORTED_EXTENSION",
            preserved_structure=("oriented closed path", "gauge-invariant loop witness", "orientation-sensitive holonomy"),
            falsification_gate="orientation reversal violates the transformation law declared by the source representation",
            guardrails=("Abelian, projective and non-Abelian carriers retain distinct source types", "numerical identification requires explicit pullback and normalization"),
        ),
        _entry2(
            iso_id="XFI.08.MAGNITUDE.ORIENTATION.FACTORIZATION",
            invariant_id="INV.XFI.POSITIVE.MAGNITUDE.ORIENTATION.SENSITIVE.CHANNEL",
            invariant_description="IDT kinetics and TIR complex holonomy links both expose a positive magnitude or pace coordinate together with a separately transforming orientation-sensitive coordinate",
            left=_node("K.XFI.IDT.MOBILITY.AFFINITY", 18, "positive_mobility_signed_affinity", "IDT_KINETICS", "IDT:00C"),
            right=_node("K.XFI.TIR.MAGNITUDE.PHASE", 19, "positive_overlap_magnitude_complex_phase", "TIR_HOLONOMY", "TIR:STAGE36"),
            relation_type="ISOMORPHIC_TO",
            refs=(
                _source("IDT", "formalism/00C_relational_density_viscosity.md"),
                _source("TIR", "TIR/frozen_predictions/validation/TIR_POLYGONAL_EXCITATION_STAGE36_COMPLEX_HOLONOMY_CP_V0_1.md"),
            ),
            classification="STRONG_STRUCTURAL",
            preserved=("positive magnitude/pace coordinate", "orientation-sensitive coordinate", "reversal-aware decomposition"),
            falsifier="source-domain reversal changes the invariant magnitude channel or fails its declared orientation involution",
            guardrails=("real exponential affinity and unitary phase remain separately typed",),
        ),
    )


def bank_manifest() -> Mapping[str, object]:
    entries = cross_formalism_bank()
    body = {
        "schema": BANK_SCHEMA,
        "source_pins": {name: dict(pin) for name, pin in sorted(SOURCE_PINS.items())},
        "entry_count": len(entries),
        "entries": [
            {
                "isomorphism_id": entry.spec.isomorphism_id,
                "invariant_id": entry.spec.invariant_id,
                "classification": entry.classification,
                "preserved_structure": list(entry.preserved_structure),
                "falsification_gate": entry.falsification_gate,
                "guardrails": list(entry.guardrails),
                "evidence_refs": list(entry.spec.evidence_refs),
            }
            for entry in entries
        ],
        "gremlin_role": "CROSS_FORMALISM_RELATIONAL_ISOMORPHISM_DISCOVERY_BANK",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "promotion_state": "CANDIDATE_ONLY",
        "epistemic": "CHYBA",
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return {**body, "manifest_sha256": digest}


def compile_cross_formalism_candidates(
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    authoring_root=None,
) -> CrossFormalismCompilation:
    compiled: dict[str, RelationalCompilation] = {}
    for entry in cross_formalism_bank():
        compiled[entry.spec.isomorphism_id] = compile_relational_isomorphism(
            entry.spec,
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            authoring_root=authoring_root,
        )
    manifest = {
        **bank_manifest(),
        "compilation_schema": COMPILATION_SCHEMA,
        "compiled_entries": {
            iso_id: {
                "receipt_sha256": compilation.receipt["receipt_sha256"],
                "radical_candidate_id": compilation.radical_candidate["candidate_id"],
                "pnv_graph_sha256": compilation.receipt["pnv_graph_sha256"],
            }
            for iso_id, compilation in sorted(compiled.items())
        },
    }
    return CrossFormalismCompilation(compilations=compiled, manifest=manifest)


def validate_cross_formalism_candidates(bank: CrossFormalismCompilation):
    results = {}
    for iso_id, compilation in sorted(bank.compilations.items()):
        result = validate_compiled_relational_candidate(compilation)
        if result.receipt["effect_boundary"]["external_effects"] is not False:
            raise CrossFormalismBankError(f"candidate crossed external effect boundary: {iso_id}")
        results[iso_id] = result
    return results


def coboundary_cycle_defects(potentials: Sequence[float]) -> tuple[float, float]:
    values = tuple(float(value) for value in potentials)
    if len(values) < 2 or not all(math.isfinite(value) for value in values):
        raise CrossFormalismBankError("finite cycle potentials with length >= 2 are required")
    differences = tuple(values[(index + 1) % len(values)] - values[index] for index in range(len(values)))
    additive = abs(sum(differences))
    multiplicative = abs(math.prod([cmath.exp(1j * delta) for delta in differences]) - 1.0)
    return additive, multiplicative


def _normalize_state(state: Sequence[complex]) -> tuple[complex, ...]:
    values = tuple(complex(value) for value in state)
    norm2 = sum(abs(value) ** 2 for value in values)
    if not values or not math.isfinite(norm2) or norm2 <= 0.0:
        raise CrossFormalismBankError("nonzero finite complex state is required")
    norm = math.sqrt(norm2)
    return tuple(value / norm for value in values)


def _inner(left: Sequence[complex], right: Sequence[complex]) -> complex:
    if len(left) != len(right):
        raise CrossFormalismBankError("state dimensions must match")
    return sum(a.conjugate() * b for a, b in zip(left, right))


def bargmann_quadrilateral(states: Sequence[Sequence[complex]]) -> complex:
    if len(states) != 4:
        raise CrossFormalismBankError("Bargmann quadrilateral requires four states")
    i, k, j, l = tuple(_normalize_state(state) for state in states)
    return _inner(i, k) * _inner(k, j) * _inner(j, l) * _inner(l, i)


def rephase_state(state: Sequence[complex], phase: float) -> tuple[complex, ...]:
    if not math.isfinite(float(phase)):
        raise CrossFormalismBankError("finite phase is required")
    carrier = cmath.exp(1j * float(phase))
    return tuple(carrier * complex(value) for value in state)


def spinor_central_phase(rotation_angle: float) -> complex:
    angle = float(rotation_angle)
    if not math.isfinite(angle):
        raise CrossFormalismBankError("finite rotation angle is required")
    return cmath.exp(0.5j * angle)


def shape_scale_defects(
    shape: Sequence[float],
    candidate_shape: Sequence[float],
    scale: float,
    candidate_scale: float,
    *,
    tolerance: float = 1e-12,
) -> Mapping[str, float]:
    p = tuple(float(value) for value in shape)
    q = tuple(float(value) for value in candidate_shape)
    if not p or len(p) != len(q):
        raise CrossFormalismBankError("shape vectors must be nonempty and have equal dimension")
    if any((not math.isfinite(value)) or value <= 0.0 for value in (*p, *q)):
        raise CrossFormalismBankError("shape coordinates must be finite and strictly positive")
    if abs(sum(p) - 1.0) > tolerance or abs(sum(q) - 1.0) > tolerance:
        raise CrossFormalismBankError("shape vectors must be normalized")
    s = float(scale)
    shat = float(candidate_scale)
    if not math.isfinite(s) or not math.isfinite(shat) or s <= 0.0 or shat <= 0.0:
        raise CrossFormalismBankError("scales must be finite and strictly positive")
    ratio = shat / s
    d_shape = sum(abs(a - b) for a, b in zip(p, q))
    d_scale = abs(1.0 - ratio)
    d_ext = sum(abs(a - ratio * b) for a, b in zip(p, q))
    margin = d_shape + d_scale - d_ext
    return {
        "D_ext": d_ext,
        "D_shape": d_shape,
        "D_scale": d_scale,
        "bound_margin": margin,
    }
