from __future__ import annotations

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

ROUND28_BANK_SCHEMA = "PNCS_GREMLIN_CROSS_FORMALISM_ROUND28_BANK_V0_1"
ROUND28_COMPILATION_SCHEMA = "PNCS_GREMLIN_CROSS_FORMALISM_ROUND28_COMPILATION_V0_1"
ROUND28_BASIS = "pncs:t36:gremlin-cross-formalism-round28:v1"

SOURCE_PINS: Mapping[str, Mapping[str, str]] = {
    "IDT": {
        "repository": "AdrianLipa90/Informational-Dynamics-of-Time",
        "commit": "3ac1f53af5223d16f8818dba99a63a6af2ba9498",
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

ALLOWED_CLASSES = {"EXACT", "EXACT_COORDINATE_ISOMORPHISM"}


class Round28Error(RuntimeError):
    pass


@dataclass(frozen=True)
class Round28Entry:
    spec: RelationalIsomorphism
    classification: str
    preserved_structure: tuple[str, ...]
    falsification_gate: str
    guardrails: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.classification not in ALLOWED_CLASSES:
            raise Round28Error(f"unsupported ROUND28 classification: {self.classification}")
        if not self.preserved_structure or not self.falsification_gate:
            raise Round28Error("ROUND28 entry requires preserved structure and falsification gate")


@dataclass(frozen=True)
class Round28Compilation:
    compilations: Mapping[str, RelationalCompilation]
    manifest: Mapping[str, object]


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _source(bank: str, path: str) -> str:
    pin = SOURCE_PINS[bank]
    return f"github:{pin['repository']}@{pin['commit']}:{path}"


def _vector(seed: int) -> Vector36:
    values = tuple(((seed * 61 + index * 29) % 277) / 277.0 for index in range(36))
    return Vector36(values, ROUND28_BASIS)


def _kaku(kaku_id: str, seed: int, role: str) -> Kaku:
    return Kaku(
        kaku_id,
        _vector(seed),
        1.0 + seed / 19.0,
        "FORWARD",
        1.0,
        role,
        tuple(((seed * 11 + index) % 36) / 36.0 for index in range(36)),
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
) -> Round28Entry:
    return Round28Entry(
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


def round28_bank() -> tuple[Round28Entry, ...]:
    return (
        _entry2(
            iso_id="XFI.28.01.CP1.MEMORY.TRANSPORT.SPIN.LIFT",
            invariant_id="INV.XFI.CP1.MINIMAL.GEODESIC.TRANSPORT.DOUBLE.COVER",
            invariant_description=(
                "the IDT minimal SO(3) geodesic transport of a CP1 memory frame and the ZPE SU(2) axis-angle link "
                "are the base and spin-lift realizations of the same non-antipodal Bloch-sphere geodesic rotation"
            ),
            left=_node("K.XFI28.IDT.CP1.MEMORY.TRANSPORT", 28, "cp1_minimal_so3_memory_transport", "IDT_MEMORY", "IDT:06C"),
            right=_node("K.XFI28.ZPE.SU2.GEODESIC.LINK", 29, "su2_axis_angle_spin_lift", "ZPE_PROJECTIVE_HOLONOMY", "ZPE:STAGE4"),
            relation_type="DOUBLE_COVER_LIFT_OF",
            refs=(
                _source("IDT", "formalism/06C_kahler_memory_frame_cp1.md"),
                _source("ZPE", "theory/TIR_FIELD_HOLONOMY_STAGE4.md"),
            ),
            classification="EXACT",
            preserved=(
                "Bloch endpoints",
                "minimal non-antipodal geodesic axis",
                "geodesic angle",
                "orientation-preserving tangent-frame transport",
                "antipodal ambiguity gate",
            ),
            falsifier="for an admitted non-antipodal Bloch pair, the SU(2) quaternion projection fails to equal the Rodrigues SO(3) transport",
            guardrails=(
                "comparison is restricted to the shared non-antipodal Bloch/CP1 geometry",
                "the SU(2) central sign is retained in the lifted representation",
            ),
        ),
        _entry2(
            iso_id="XFI.28.02.HALF.INTERFACE.RELATIONAL.ZERO",
            invariant_id="INV.XFI.BALANCED.TWO.CHANNEL.SPINORIAL.NULL",
            invariant_description=(
                "IDT 01I and Secret-of-a-Half SOH-X use the same balanced two-channel cancellation kernel after the exact phase substitution phi=delta_tau/2"
            ),
            left=_node("K.XFI28.IDT.HALF.INTERFACE", 30, "balanced_interface_spinorial_relational_zero", "IDT_HALF_INTERFACE", "IDT:01I"),
            right=_node("K.XFI28.SOH.SPECTRAL.NULL", 31, "balanced_two_channel_half_turn_null", "SOH_HALF_INTERFACE", "SOH:SOH-X"),
            relation_type="EXACT_KERNEL_ISOMORPHISM",
            refs=(
                _source("IDT", "formalism/01I_half_interface_relational_zero.md"),
                _source("SOH", "research/SOH_X_HALF_INTERFACE_SPECTRAL_NULLS_V0_1.md"),
                _source("SOH", "research/SOH_G013_PAULI_SPINOR_LIFT_V0_1.md"),
            ),
            classification="EXACT",
            preserved=(
                "balanced weight one-half",
                "spinorial phase half-angle",
                "2pi lifted displacement gives relative phase pi",
                "4pi spinor return",
                "relational projection zero",
            ),
            falsifier="the declared kernel fails to vanish exactly at balanced weight and a lifted half-turn, or vanishes away from that condition inside the admitted domain",
            guardrails=(
                "physical bindings of the two channels retain their source-domain admission gates",
                "central spinor sign and relational projection are separately typed",
            ),
        ),
        _entry2(
            iso_id="XFI.28.03.HYPERBOLIC.CENTERED.COORDINATE",
            invariant_id="INV.XFI.TANH.HALF.RAPIDITY.CHART",
            invariant_description=(
                "the IDT current-to-activity ratio and the Secret-of-a-Half centered Bloch coordinate use the same tanh half-rapidity chart and inverse 2*artanh map"
            ),
            left=_node("K.XFI28.IDT.NOW.HYPERBOLIC", 32, "current_activity_half_rapidity_chart", "IDT_NOW_BIFURCATION", "IDT:04A"),
            right=_node("K.XFI28.SOH.BLOCH.RAPIDITY", 33, "centered_bloch_half_rapidity_chart", "SOH_BLOCH_RAPIDITY", "SOH:G009"),
            relation_type="COORDINATE_ISOMORPHIC_TO",
            refs=(
                _source("IDT", "formalism/04A_now_bifurcation_hyperbolic_coordinates.md"),
                _source("SOH", "research/SOH_G009_BLOCH_RAPIDITY_COLLATZ_V1.md"),
            ),
            classification="EXACT_COORDINATE_ISOMORPHISM",
            preserved=(
                "open interval centered coordinate",
                "tanh(lambda/2) forward chart",
                "2*artanh inverse chart",
                "orientation reversal maps centered coordinate and rapidity to their negatives",
            ),
            falsifier="the declared centered-coordinate round trip differs under t <-> j/a and lambda <-> A for any admitted |t|<1",
            guardrails=(
                "the arithmetic and kinetic source roles remain independently typed",
                "the isomorphism concerns the exact coordinate chart and its transformation law",
            ),
        ),
    )


def round28_manifest() -> Mapping[str, object]:
    entries = round28_bank()
    body = {
        "schema": ROUND28_BANK_SCHEMA,
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
        "gremlin_role": "ROUND28_EXACT_CROSS_FORMALISM_RELATIONAL_ISOMORPHISM_BANK",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "promotion_state": "CANDIDATE_ONLY",
        "epistemic": "CHYBA",
    }
    return {**body, "manifest_sha256": hashlib.sha256(_canonical_bytes(body)).hexdigest()}


def compile_round28_candidates(
    *,
    generation_binding: str,
    identity: str,
    authority: str,
) -> Round28Compilation:
    compiled: dict[str, RelationalCompilation] = {}
    for entry in round28_bank():
        compiled[entry.spec.isomorphism_id] = compile_relational_isomorphism(
            entry.spec,
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            authoring_root=None,
        )
    manifest = {
        **round28_manifest(),
        "compilation_schema": ROUND28_COMPILATION_SCHEMA,
        "compiled_entries": {
            iso_id: {
                "receipt_sha256": compilation.receipt["receipt_sha256"],
                "radical_candidate_id": compilation.radical_candidate["candidate_id"],
                "pnv_graph_sha256": compilation.receipt["pnv_graph_sha256"],
            }
            for iso_id, compilation in sorted(compiled.items())
        },
    }
    return Round28Compilation(compilations=compiled, manifest=manifest)


def validate_round28_candidates(compiled: Round28Compilation):
    results = {}
    for iso_id, compilation in sorted(compiled.compilations.items()):
        result = validate_compiled_relational_candidate(compilation)
        if result.receipt["effect_boundary"]["external_effects"] is not False:
            raise Round28Error(f"candidate crossed external effect boundary: {iso_id}")
        if result.program.mode != "READ_ONLY":
            raise Round28Error(f"candidate left READ_ONLY mode: {iso_id}")
        if result.program.epistemic != "CHYBA":
            raise Round28Error(f"candidate left CHYBA epistemic mode: {iso_id}")
        results[iso_id] = result
    return results


def _unit3(vector: Sequence[float]) -> tuple[float, float, float]:
    values = tuple(float(value) for value in vector)
    if len(values) != 3 or any(not math.isfinite(value) for value in values):
        raise Round28Error("finite three-vector required")
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 0.0:
        raise Round28Error("nonzero three-vector required")
    return tuple(value / norm for value in values)  # type: ignore[return-value]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b))


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    ax, ay, az = (float(value) for value in a)
    bx, by, bz = (float(value) for value in b)
    return (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)


def cp1_minimal_axis_angle(a: Sequence[float], b: Sequence[float], *, tolerance: float = 1e-12) -> Mapping[str, object]:
    left = _unit3(a)
    right = _unit3(b)
    cosine = max(-1.0, min(1.0, _dot(left, right)))
    theta = math.acos(cosine)
    if abs(math.pi - theta) <= tolerance:
        raise Round28Error("antipodal CP1 endpoints are ambiguous")
    if theta <= tolerance:
        return {"a": left, "b": right, "theta": 0.0, "axis": (0.0, 0.0, 1.0)}
    axis = _unit3(_cross(left, right))
    return {"a": left, "b": right, "theta": theta, "axis": axis}


def rodrigues_rotate(vector: Sequence[float], axis: Sequence[float], theta: float) -> tuple[float, float, float]:
    v = _unit3(vector)
    k = _unit3(axis)
    angle = float(theta)
    if not math.isfinite(angle):
        raise Round28Error("finite angle required")
    cross = _cross(k, v)
    dot = _dot(k, v)
    c = math.cos(angle)
    s = math.sin(angle)
    return tuple(c * v[i] + s * cross[i] + (1.0 - c) * dot * k[i] for i in range(3))  # type: ignore[return-value]


def spin_lift_quaternion(axis: Sequence[float], theta: float) -> tuple[float, float, float, float]:
    k = _unit3(axis)
    half = 0.5 * float(theta)
    if not math.isfinite(half):
        raise Round28Error("finite angle required")
    s = math.sin(half)
    return (math.cos(half), s * k[0], s * k[1], s * k[2])


def quaternion_rotate(vector: Sequence[float], quaternion: Sequence[float]) -> tuple[float, float, float]:
    v = _unit3(vector)
    q = tuple(float(value) for value in quaternion)
    if len(q) != 4 or any(not math.isfinite(value) for value in q):
        raise Round28Error("finite quaternion required")
    norm = math.sqrt(sum(value * value for value in q))
    if norm <= 0.0:
        raise Round28Error("nonzero quaternion required")
    w, x, y, z = (value / norm for value in q)
    qv = (x, y, z)
    uv = _cross(qv, v)
    uuv = _cross(qv, uv)
    return tuple(v[i] + 2.0 * (w * uv[i] + uuv[i]) for i in range(3))  # type: ignore[return-value]


def cp1_spin_lift_projection_defect(a: Sequence[float], b: Sequence[float]) -> Mapping[str, float]:
    geometry = cp1_minimal_axis_angle(a, b)
    theta = float(geometry["theta"])
    axis = geometry["axis"]
    source = geometry["a"]
    target = geometry["b"]
    rodrigues = rodrigues_rotate(source, axis, theta)
    quaternion = spin_lift_quaternion(axis, theta)
    lifted = quaternion_rotate(source, quaternion)
    return {
        "so3_to_target": math.sqrt(sum((rodrigues[i] - target[i]) ** 2 for i in range(3))),
        "su2_projection_to_so3": math.sqrt(sum((lifted[i] - rodrigues[i]) ** 2 for i in range(3))),
        "central_sign_projection": math.sqrt(
            sum((quaternion_rotate(source, tuple(-value for value in quaternion))[i] - lifted[i]) ** 2 for i in range(3))
        ),
    }


def half_interface_defect(weight: float, delta_tau: float) -> float:
    p = float(weight)
    phase = float(delta_tau)
    if not 0.0 <= p <= 1.0 or not math.isfinite(phase):
        raise Round28Error("half-interface requires weight in [0,1] and finite phase")
    return 1.0 + 2.0 * math.sqrt(p * (1.0 - p)) * math.cos(0.5 * phase)


def half_interface_is_zero(weight: float, delta_tau: float, *, tolerance: float = 1e-12) -> bool:
    return abs(half_interface_defect(weight, delta_tau)) <= tolerance


def half_rapidity_forward(rapidity: float) -> float:
    value = float(rapidity)
    if not math.isfinite(value):
        raise Round28Error("finite rapidity required")
    return math.tanh(0.5 * value)


def half_rapidity_inverse(centered: float) -> float:
    value = float(centered)
    if not math.isfinite(value) or abs(value) >= 1.0:
        raise Round28Error("centered coordinate must satisfy |t| < 1")
    return 2.0 * math.atanh(value)


def idt_beta_from_centered(centered: float) -> float:
    return half_rapidity_inverse(centered) / (24.0 * math.pi)
