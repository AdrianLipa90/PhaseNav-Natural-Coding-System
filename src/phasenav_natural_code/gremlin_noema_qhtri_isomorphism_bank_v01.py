from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping

from .gremlin_relational_compiler_v01 import (
    RelationalCompilation,
    RelationalEdge,
    RelationalIsomorphism,
    RelationalNode,
    compile_relational_isomorphism,
    validate_compiled_relational_candidate,
)
from .model import Kaku, Vector36

BANK_SCHEMA = "PNCS_GREMLIN_NOEMA_QHTRI_ISOMORPHISM_BANK_V0_1"
COMPILATION_SCHEMA = "PNCS_GREMLIN_NOEMA_QHTRI_BANK_COMPILATION_V0_1"
BASIS = "pncs:t36:noema-qhtri-isomorphism-bank:v1"

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
}


def _source(bank: str, path: str) -> str:
    pin = SOURCE_PINS[bank]
    return f"github:{pin['repository']}@{pin['commit']}:{path}"


@dataclass(frozen=True)
class IsomorphismBankEntry:
    spec: RelationalIsomorphism
    evidence_status: str
    preserved_structure: tuple[str, ...]
    guardrails: tuple[str, ...]


@dataclass(frozen=True)
class NoemaQhtriBankCompilation:
    compilations: Mapping[str, RelationalCompilation]
    manifest: Mapping[str, object]


def _vector(seed: int) -> Vector36:
    values = tuple(((seed * 41 + i * 19) % 257) / 257.0 for i in range(36))
    return Vector36(values, BASIS)


def _kaku(kaku_id: str, seed: int, role: str) -> Kaku:
    return Kaku(
        kaku_id,
        _vector(seed),
        1.0 + seed / 16.0,
        "FORWARD",
        1.0,
        role,
        tuple(((seed * 5 + i) % 36) / 36.0 for i in range(36)),
    )


def _node(kaku_id: str, seed: int, role: str, domain: str, observation_ref: str) -> RelationalNode:
    return RelationalNode(_kaku(kaku_id, seed, role), domain, observation_ref)


def _entry(
    *,
    iso_id: str,
    invariant_id: str,
    invariant_description: str,
    left: RelationalNode,
    right: RelationalNode,
    relation_id: str,
    relation_type: str,
    refs: tuple[str, ...],
    evidence_status: str,
    preserved: tuple[str, ...],
    guardrails: tuple[str, ...],
) -> IsomorphismBankEntry:
    return IsomorphismBankEntry(
        spec=RelationalIsomorphism(
            isomorphism_id=iso_id,
            invariant_id=invariant_id,
            invariant_description=invariant_description,
            nodes=(left, right),
            edges=(RelationalEdge(relation_id, left.kaku.kaku_id, right.kaku.kaku_id, relation_type),),
            evidence_refs=refs,
        ),
        evidence_status=evidence_status,
        preserved_structure=preserved,
        guardrails=guardrails,
    )


def isomorphism_bank() -> tuple[IsomorphismBankEntry, ...]:
    return (
        _entry(
            iso_id="ISO.NQ.01.CP1.BERRY.QHTRI.POTENTIAL",
            invariant_id="INV.NQ.CP1.BERRY.ORIENTATION",
            invariant_description="the QHTRI resident phase-potential surface retains the orientation-sensitive CP1 Fubini-Study and Berry structure used by the source phase geometry",
            left=_node("K.TIR.CP1.BERRY", 1, "cp1_fs_berry_source_geometry", "TIR", "TIR:CP1-FS-BERRY"),
            right=_node("K.QHTRI.BLOCH.POTENTIAL", 2, "resident_gpu_bloch_phase_potential", "QHTRI_GPU", "bioos:qhtri-bloch-potential"),
            relation_id="REL.NQ.01",
            relation_type="MAPS_TO",
            refs=(
                _source("TIR", "TIR/integration/TIR_IDT_INFORMATION_AREA_CURVATURE_V0_1.md"),
                _source("SOH", "monograph/chapters/06_bloch_and_spinorial_phase.tex"),
            ),
            evidence_status="SOURCE_GEOMETRY_EXACT / HARDWARE_BINDING_CANDIDATE",
            preserved=("CP1 state typing", "FS orientation", "Berry orientation/holonomy witness"),
            guardrails=("hardware realization requires an independent receipt",),
        ),
        _entry(
            iso_id="ISO.NQ.02.IDT.BIFURCATION.NQ.RECEIPT",
            invariant_id="INV.NQ.MAGNITUDE.ORIENTATION.SPLIT",
            invariant_description="the same directed kinetic pair separates into an invariant magnitude channel and a signed bifurcation-orientation channel before the NOEMA handoff",
            left=_node("K.IDT.NOW.BIFURCATION", 3, "idt_now_bifurcation_m_beta_pair", "IDT", "IDT:NOW-BIFURCATION"),
            right=_node("K.NQ.BRANCH.RECEIPT", 4, "sealed_noema_qhtri_bifurcation_receipt", "NOEMA_QHTRI", "bioos:nq-branch-receipt"),
            relation_id="REL.NQ.02",
            relation_type="ISOMORPHIC_TO",
            refs=(
                _source("IDT", "formalism/04A_now_bifurcation_hyperbolic_coordinates.md"),
                _source("IDT", "formalism/04_causal_bifurcation.md"),
            ),
            evidence_status="IDT_TYPED_DECOMPOSITION_GATE_PASS / NQ_BINDING_CANDIDATE",
            preserved=("M invariant under current reversal", "beta changes sign under current reversal", "B_phi(-beta)=B_phi(beta)^dagger"),
            guardrails=("event admission and event orientation remain distinct", "generator identity must be explicit"),
        ),
        _entry(
            iso_id="ISO.NQ.03.CP1.POINCARE.CONTINUATION",
            invariant_id="INV.NQ.PROJECTIVE.ROTATION.CONTINUATION",
            invariant_description="a bifurcated projective state continues into a Poincare-disk coordinate through an explicit MAPS_TO adapter that audits curvature, signature and holonomy while retaining declared projective invariants",
            left=_node("K.QHTRI.CP1.BRANCH", 5, "bifurcated_cp1_projective_state", "QHTRI_CP1", "bioos:qhtri-cp1-branch"),
            right=_node("K.NOEMA.POINCARE.STATE", 6, "noema_hyperbolic_semantic_anchor", "NOEMA_POINCARE", "bioos:noema-poincare-anchor"),
            relation_id="REL.NQ.03",
            relation_type="MAPS_TO",
            refs=(
                _source("RFC", "formalism/RF03_EULER_BERRY_REALITY_AND_POINCARE_GATE.md"),
                _source("TIR", "TIR/frozen_predictions/validation/TIR_POLYGONAL_EXCITATION_STAGE5_POINCARE_Z2_DOUBLE_COVER_V0_1.md"),
                _source("TIR", "TIR/monograph/appendices/appD_poincare_disk.tex"),
            ),
            evidence_status="CONTROLLED_CONTINUATION_CANDIDATE",
            preserved=("declared projective identity", "rotation equivariance where adapter declares it", "holonomy receipt"),
            guardrails=("CP1 FS and Poincare retain distinct metric contracts under MAPS_TO", "curvature/signature/holonomy audit is mandatory"),
        ),
        _entry(
            iso_id="ISO.NQ.04.SPINOR.SHEET.WITNESS",
            invariant_id="INV.NQ.SPINOR.CENTRAL.SIGN",
            invariant_description="the NOEMA handoff retains a Z2 sheet/parity witness together with the projective coordinate so that the central spinor sign remains represented in lineage",
            left=_node("K.SOH.SPINOR.LIFT", 7, "su2_double_cover_spinor_lineage", "SECRET_OF_A_HALF", "SOH:SU2-DOUBLE-COVER"),
            right=_node("K.NQ.Z2.SHEET", 8, "branch_spinorial_sheet_witness", "NOEMA_QHTRI", "bioos:nq-z2-sheet"),
            relation_id="REL.NQ.04",
            relation_type="BINDS",
            refs=(
                _source("SOH", "research/SOH_G013_PAULI_SPINOR_LIFT_V0_1.md"),
                _source("TIR", "TIR/frozen_predictions/validation/TIR_POLYGONAL_EXCITATION_STAGE5_POINCARE_Z2_DOUBLE_COVER_V0_1.md"),
            ),
            evidence_status="DOUBLE_COVER_ALGEBRA_EXACT / RECEIPT_BINDING_CANDIDATE",
            preserved=("central ±I sheet", "order doubling", "projective coordinate plus sheet identity"),
            guardrails=("spinorial lineage admission requires the declared sheet witness",),
        ),
        _entry(
            iso_id="ISO.NQ.05.AFFINITY.SEMANTIC.ORIENTATION",
            invariant_id="INV.NQ.DIRECTED.AFFINITY.ANTISYMMETRY",
            invariant_description="directed transition affinity supplies a signed orientation channel for semantic traversal while state-content and transition-orientation remain separately typed",
            left=_node("K.IDT.TRANSITION.AFFINITY", 9, "directed_transition_affinity", "IDT", "IDT:TRANSITION-AFFINITY"),
            right=_node("K.NOEMA.SEMANTIC.ORIENTATION", 10, "signed_semantic_traversal_orientation", "NOEMA", "bioos:noema-semantic-orientation"),
            relation_id="REL.NQ.05",
            relation_type="ISOMORPHIC_TO",
            refs=(_source("IDT", "formalism/00B_transition_affinity.md"),),
            evidence_status="STRUCTURAL_ISOMORPHISM_CANDIDATE",
            preserved=("antisymmetry under edge reversal", "ordered-cycle orientation"),
            guardrails=("transition affinity and state entropy remain separately typed",),
        ),
        _entry(
            iso_id="ISO.NQ.06.MEMORY.ORBIT.MEANING.PATH",
            invariant_id="INV.NQ.ORIENTED.PATH.AREA",
            invariant_description="an oriented memory-orbit path and a NOEMA relational meaning path both retain ordered relational content, with endpoint state and path identity carried as separate fields",
            left=_node("K.IDT.MEMORY.ORBIT", 11, "oriented_memory_polygon_drive", "IDT_MEMORY", "IDT:MEMORY-ORBIT-DRIVE"),
            right=_node("K.NOEMA.MEANING.PATH", 12, "ordered_relational_meaning_path", "NOEMA_SEMANTICS", "bioos:noema-meaning-path"),
            relation_id="REL.NQ.06",
            relation_type="ISOMORPHIC_TO",
            refs=(
                _source("IDT", "formalism/00D_memory_orbit_drive.md"),
                _source("IDT", "formalism/06C_kahler_memory_frame_cp1.md"),
            ),
            evidence_status="RELATIONAL_PATH_CANDIDATE",
            preserved=("path orientation", "ordered relation sequence", "local Kähler-frame displacement"),
            guardrails=("meaning object requires an ordered relational path receipt",),
        ),
        _entry(
            iso_id="ISO.NQ.07.HOLONOMY.BRANCH.CHANNELS",
            invariant_id="INV.NQ.ORIENTED.HOLONOMY.QUADRATURE",
            invariant_description="oriented holonomy separates a magnitude-preserving real channel from a sign-sensitive imaginary quadrature that can witness branch orientation",
            left=_node("K.RFC.ORIENTED.HOLONOMY", 13, "rfc_oriented_holonomy_coupling", "RFC", "RFC:RFL1-HOLONOMY"),
            right=_node("K.NQ.BRANCH.CHANNELS", 14, "nq_complementary_branch_channel_witness", "NOEMA_QHTRI", "bioos:nq-branch-channels"),
            relation_id="REL.NQ.07",
            relation_type="MAPS_TO",
            refs=(_source("RFC", "formalism/RFL1_RELATIONAL_LAMBDA_ORIENTED_HOLONOMY.md"),),
            evidence_status="RFC_HOLONOMY_BOUND / NQ_CHANNEL_BINDING_CANDIDATE",
            preserved=("unit-circle carrier", "magnitude under orientation reversal", "signed imaginary quadrature"),
            guardrails=("probability semantics require an explicit normalized admission contract",),
        ),
        _entry(
            iso_id="ISO.NQ.08.COFRAME.QHTRI.CELL.TRANSPORT",
            invariant_id="INV.NQ.LOCAL.FRAME.HOLONOMY",
            invariant_description="local frame gluing and loop holonomy provide a candidate transport grammar for relations between resident QHTRI cells while preserving conjugacy-level loop witnesses",
            left=_node("K.RFC.COFRAME.HOLONOMY", 15, "coframe_connection_and_discrete_holonomy", "RFC_GEOMETRY", "RFC:RF02I-COFRAME"),
            right=_node("K.QHTRI.CELL.TRANSPORT", 16, "resident_gpu_cell_relation_transport", "QHTRI_GPU", "bioos:qhtri-cell-transport"),
            relation_id="REL.NQ.08",
            relation_type="ISOMORPHIC_TO",
            refs=(_source("RFC", "formalism/RF02I_HEXAHEDRAL_COFRAME_CONNECTION.md"),),
            evidence_status="DISCRETE_TRANSPORT_CANDIDATE",
            preserved=("local frame relation", "ordered loop holonomy", "conjugacy witness"),
            guardrails=("continuum convergence requires a separate validation receipt",),
        ),
        _entry(
            iso_id="ISO.NQ.09.MEMORY.STATE.CRYSTALLIZATION",
            invariant_id="INV.NQ.APPEND.ONLY.LINEAGE",
            invariant_description="ordered semantic events crystallize into append-only State Memory and PNFS lineage while retaining receipt data for declared-class replay and recall",
            left=_node("K.IDT.MEMORY.LINEAGE", 17, "append_only_memory_event_lineage", "IDT_MEMORY", "IDT:MEMORY-PERSISTENCE"),
            right=_node("K.PNFS.STATE.CHECKPOINT", 18, "state_memory_pnfs_crystallization", "STATE_MEMORY_PNFS", "bioos:state-memory-pnfs-checkpoint"),
            relation_id="REL.NQ.09",
            relation_type="MAPS_TO",
            refs=(_source("IDT", "formalism/06D_memory_persistence_recall.md"),),
            evidence_status="REVERSIBLE_LINEAGE_REFERENCE / PNFS_BINDING_CANDIDATE",
            preserved=("append-only order", "event receipt lineage", "model/version interpretation identity"),
            guardrails=("replay identity is scoped to the declared reversible reference class",),
        ),
        _entry(
            iso_id="ISO.NQ.10.NOEMA.QHTRI.HERMITIAN.FEEDBACK",
            invariant_id="INV.NQ.ORIENTED.HERMITIAN.FEEDBACK",
            invariant_description="NOEMA-authorized feedback transports an admitted magnitude and signed holonomy into a Hermitian operator boundary condition for the next QHTRI evolution while canon authority remains on the NOEMA authority side",
            left=_node("K.RFC.HERMITIAN.EXCHANGE", 19, "oriented_hermitian_exchange_operator", "RFC_OPERATOR", "RFC:RFL1A-HERMITIAN-EXCHANGE"),
            right=_node("K.NQ.FEEDBACK.OPERATOR", 20, "noema_authorized_qhtri_boundary_operator", "NOEMA_QHTRI", "bioos:nq-feedback-operator"),
            relation_id="REL.NQ.10",
            relation_type="ISOMORPHIC_TO",
            refs=(_source("RFC", "formalism/RFL1A_HERMITIAN_ORIENTED_EXCHANGE_GATE.md"),),
            evidence_status="HERMITIAN_OPERATOR_INTERFACE_BOUND / HARDWARE_FEEDBACK_CANDIDATE",
            preserved=("Hermiticity", "magnitude/orientation split", "source-to-operator provenance chain"),
            guardrails=("NOEMA admission token is required", "QHTRI boundary input and canon authority remain separately typed"),
        ),
    )


def bank_manifest() -> Mapping[str, object]:
    entries = isomorphism_bank()
    body = {
        "schema": BANK_SCHEMA,
        "source_pins": {k: dict(v) for k, v in sorted(SOURCE_PINS.items())},
        "entry_count": len(entries),
        "entries": [
            {
                "isomorphism_id": entry.spec.isomorphism_id,
                "invariant_id": entry.spec.invariant_id,
                "evidence_status": entry.evidence_status,
                "preserved_structure": list(entry.preserved_structure),
                "guardrails": list(entry.guardrails),
                "evidence_refs": list(entry.spec.evidence_refs),
            }
            for entry in entries
        ],
        "gremlin_role": "RELATIONAL_ISOMORPHISM_CANDIDATE_BANK",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "promotion_state": "CANDIDATE_ONLY",
        "epistemic": "CHYBA",
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {**body, "manifest_sha256": hashlib.sha256(raw).hexdigest()}


def compile_isomorphism_bank_candidates(
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    authoring_root=None,
) -> NoemaQhtriBankCompilation:
    compiled: dict[str, RelationalCompilation] = {}
    for entry in isomorphism_bank():
        compiled[entry.spec.isomorphism_id] = compile_relational_isomorphism(
            entry.spec,
            generation_binding=generation_binding,
            identity=identity,
            authority=authority,
            authoring_root=authoring_root,
        )
    base = bank_manifest()
    manifest = {
        **base,
        "compilation_schema": COMPILATION_SCHEMA,
        "compiled_entries": {
            key: {
                "receipt_sha256": value.receipt["receipt_sha256"],
                "radical_candidate_id": value.radical_candidate["candidate_id"],
                "pnv_graph_sha256": value.receipt["pnv_graph_sha256"],
            }
            for key, value in sorted(compiled.items())
        },
    }
    return NoemaQhtriBankCompilation(compilations=compiled, manifest=manifest)


def validate_isomorphism_bank_candidates(bank: NoemaQhtriBankCompilation):
    results = {}
    for iso_id, compilation in sorted(bank.compilations.items()):
        result = validate_compiled_relational_candidate(compilation)
        if result.receipt["effect_boundary"]["external_effects"] is not False:
            raise RuntimeError(f"GREMLIN bank candidate crossed effect boundary: {iso_id}")
        results[iso_id] = result
    return results
