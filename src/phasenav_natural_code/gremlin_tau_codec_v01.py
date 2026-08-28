from __future__ import annotations

from dataclasses import dataclass
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

BASIS = "pncs:t36:liminal-file-codec:v1"
CODEC_ISOMORPHISM_ID = "ISO.PNCS.TAU.LIMINAL.FILE"
CODEC_INVARIANT_ID = "INV.CONTENT.IDENTITY.TAU.T36.STATE"
CODEC_INVARIANT_DESCRIPTION = (
    "logical file content is transported through exact scalar tau frames, "
    "whole-lane T36 witnesses and State Memory consolidation checkpoints "
    "while file identity, content commitment and checkpoint identity remain distinct"
)


@dataclass(frozen=True)
class TauCodecCompilation:
    compilation: RelationalCompilation
    codec_manifest: Mapping[str, object]


def _vector(seed: int) -> Vector36:
    # Deterministic role coordinate, used only as the common PNCS authoring basis.
    values = tuple(((seed * 37 + i * 17) % 257) / 257.0 for i in range(36))
    return Vector36(values, BASIS)


def _kaku(kaku_id: str, seed: int, role: str) -> Kaku:
    return Kaku(
        kaku_id,
        _vector(seed),
        1.0 + seed / 10.0,
        "FORWARD",
        1.0,
        role,
        tuple(((seed + i) % 36) / 36.0 for i in range(36)),
    )


def tau_codec_isomorphism() -> RelationalIsomorphism:
    return RelationalIsomorphism(
        isomorphism_id=CODEC_ISOMORPHISM_ID,
        invariant_id=CODEC_INVARIANT_ID,
        invariant_description=CODEC_INVARIANT_DESCRIPTION,
        nodes=(
            RelationalNode(
                _kaku("K.TAU.FRAME", 1, "exact_scalar_tau_content_carrier"),
                "PNCS",
                "pncs:tau-frame-codec-v0.1",
            ),
            RelationalNode(
                _kaku("K.T36.WITNESS", 2, "whole_lane_block_integrity_witness"),
                "PNCS_T36",
                "pncs:t36-block-witness-v0.1",
            ),
            RelationalNode(
                _kaku("K.LIMINAL.SEGMENT", 3, "continuous_tau_segment_between_state_crystals"),
                "PNV_STATE_MEMORY",
                "pnv-state-memory:liminal-segment-v0.1",
            ),
            RelationalNode(
                _kaku("K.PNLF.FILE", 4, "bioos_file_persistence_spine"),
                "BIOOS",
                "bioos:pnlf-persistence-v0.1",
            ),
            RelationalNode(
                _kaku("K.PNH5.VIEW", 5, "hierarchical_dataset_compatibility_view"),
                "PNH5_COMPAT",
                "bioos:pnh5-view-v0.1",
            ),
        ),
        edges=(
            RelationalEdge("REL.TAU.T36", "K.TAU.FRAME", "K.T36.WITNESS", "BINDS"),
            RelationalEdge("REL.TAU.LIMINAL", "K.TAU.FRAME", "K.LIMINAL.SEGMENT", "ISOMORPHIC_TO"),
            RelationalEdge("REL.LIMINAL.FILE", "K.LIMINAL.SEGMENT", "K.PNLF.FILE", "ISOMORPHIC_TO"),
            RelationalEdge("REL.FILE.PNH5", "K.PNLF.FILE", "K.PNH5.VIEW", "MAPS_TO"),
        ),
        evidence_refs=(
            "receipt:PNLF_LIMINAL_STATE_TEST_RECEIPT_V0_1",
            "receipt:PNLF_ANALOG_ROBUSTNESS_RECEIPT_V0_2",
            "receipt:PNLF_TAU_SELF_CALIBRATION_RECEIPT_V0_3",
            "receipt:PNLF_BLOCK_FILE_E2E_RECEIPT_V0_4",
        ),
    )


def compile_tau_codec_candidate(
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    authoring_root=None,
) -> TauCodecCompilation:
    compilation = compile_relational_isomorphism(
        tau_codec_isomorphism(),
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        authoring_root=authoring_root,
    )
    manifest = {
        "schema": "PNCS_GREMLIN_TAU_CODEC_MANIFEST_V0_1",
        "isomorphism_id": CODEC_ISOMORPHISM_ID,
        "invariant_id": CODEC_INVARIANT_ID,
        "kaku_candidate_ids": {
            key: value["candidate_id"] for key, value in sorted(compilation.kaku_candidates.items())
        },
        "radical_candidate_id": compilation.radical_candidate["candidate_id"],
        "operator_candidate_ids": [op["candidate_id"] for op in compilation.operator_candidates],
        "pnv_source_sha256": compilation.receipt["pnv_source_sha256"],
        "pnv_graph_sha256": compilation.receipt["pnv_graph_sha256"],
        "tau_is_content_carrier": True,
        "t36_is_whole_lane_witness": True,
        "state_memory_is_consolidation_boundary": True,
        "file_identity_distinct_from_content_and_checkpoint": True,
        "wall_clock_in_semantic_identity": False,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "promotion_state": "CANDIDATE_ONLY",
        "epistemic": "CHYBA",
    }
    return TauCodecCompilation(compilation=compilation, codec_manifest=manifest)


def validate_tau_codec_candidate(candidate: TauCodecCompilation):
    result = validate_compiled_relational_candidate(candidate.compilation)
    if result.receipt["effect_boundary"]["external_effects"] is not False:
        raise RuntimeError("GREMLIN tau codec conformance crossed effect boundary")
    return result
