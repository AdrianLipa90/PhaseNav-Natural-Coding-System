from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .gremlin_isomorphic_codec_merge_v01 import merge_relational_isomorphisms
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
CODEC_LEFT_FRAGMENT_ID = "ISO.PNLF.PNCS.STATE"
CODEC_RIGHT_FRAGMENT_ID = "ISO.PNLF.STATE.BIOOS"
CODEC_REALIZATION_FRAGMENT_ID = "ISO.PNLF.PNH5.REALIZATION"
CODEC_INVARIANT_ID = "INV.CONTENT.IDENTITY.TAU.T36.STATE"
CODEC_MANIFEST_SCHEMA = "PNCS_GREMLIN_TAU_CODEC_MANIFEST_V0_1"
CODEC_INVARIANT_DESCRIPTION = (
    "logical file content is transported through exact scalar tau frames, "
    "whole-lane T36 witnesses and State Memory consolidation checkpoints "
    "while file identity, content commitment and checkpoint identity remain distinct"
)

EVIDENCE_REFS = (
    "receipt:PNLF_LIMINAL_STATE_TEST_RECEIPT_V0_1",
    "receipt:PNLF_ANALOG_ROBUSTNESS_RECEIPT_V0_2",
    "receipt:PNLF_TAU_SELF_CALIBRATION_RECEIPT_V0_3",
    "receipt:PNLF_BLOCK_FILE_E2E_RECEIPT_V0_4",
)


class GremlinTauCodecError(RuntimeError):
    pass


@dataclass(frozen=True)
class TauCodecCompilation:
    compilation: RelationalCompilation
    codec_manifest: Mapping[str, object]


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _vector(seed: int) -> Vector36:
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


def _nodes() -> dict[str, RelationalNode]:
    return {
        "K.TAU.FRAME": RelationalNode(
            _kaku("K.TAU.FRAME", 1, "exact_scalar_tau_content_carrier"),
            "PNCS",
            "pncs:tau-frame-codec-v0.1",
        ),
        "K.T36.WITNESS": RelationalNode(
            _kaku("K.T36.WITNESS", 2, "whole_lane_block_integrity_witness"),
            "PNCS_T36",
            "pncs:t36-block-witness-v0.1",
        ),
        "K.LIMINAL.SEGMENT": RelationalNode(
            _kaku("K.LIMINAL.SEGMENT", 3, "continuous_tau_segment_between_state_crystals"),
            "PNV_STATE_MEMORY",
            "pnv-state-memory:liminal-segment-v0.1",
        ),
        "K.PNLF.FILE": RelationalNode(
            _kaku("K.PNLF.FILE", 4, "bioos_file_persistence_spine"),
            "BIOOS",
            "bioos:pnlf-persistence-v0.1",
        ),
        "K.PNH5.VIEW": RelationalNode(
            _kaku("K.PNH5.VIEW", 5, "hierarchical_dataset_compatibility_view"),
            "PNH5_COMPAT",
            "bioos:pnh5-view-v0.1",
        ),
        "K.PNH5.CONTAINER": RelationalNode(
            _kaku("K.PNH5.CONTAINER", 6, "exact_binary_realization_container"),
            "PNH5_BINARY_REALIZATION",
            "bioos:pnh5-container-v0.1",
        ),
    }


def tau_codec_fragments() -> tuple[RelationalIsomorphism, RelationalIsomorphism, RelationalIsomorphism]:
    nodes = _nodes()
    left = RelationalIsomorphism(
        isomorphism_id=CODEC_LEFT_FRAGMENT_ID,
        invariant_id=CODEC_INVARIANT_ID,
        invariant_description=CODEC_INVARIANT_DESCRIPTION,
        nodes=(nodes["K.TAU.FRAME"], nodes["K.T36.WITNESS"], nodes["K.LIMINAL.SEGMENT"]),
        edges=(
            RelationalEdge("REL.TAU.T36", "K.TAU.FRAME", "K.T36.WITNESS", "BINDS"),
            RelationalEdge("REL.TAU.LIMINAL", "K.TAU.FRAME", "K.LIMINAL.SEGMENT", "ISOMORPHIC_TO"),
        ),
        evidence_refs=(*EVIDENCE_REFS, "fragment:pncs-state-memory"),
    )
    right = RelationalIsomorphism(
        isomorphism_id=CODEC_RIGHT_FRAGMENT_ID,
        invariant_id=CODEC_INVARIANT_ID,
        invariant_description=CODEC_INVARIANT_DESCRIPTION,
        nodes=(nodes["K.LIMINAL.SEGMENT"], nodes["K.PNLF.FILE"], nodes["K.PNH5.VIEW"]),
        edges=(
            RelationalEdge("REL.LIMINAL.FILE", "K.LIMINAL.SEGMENT", "K.PNLF.FILE", "ISOMORPHIC_TO"),
            RelationalEdge("REL.FILE.PNH5", "K.PNLF.FILE", "K.PNH5.VIEW", "MAPS_TO"),
        ),
        evidence_refs=(*EVIDENCE_REFS, "fragment:state-memory-bioos"),
    )
    realization = RelationalIsomorphism(
        isomorphism_id=CODEC_REALIZATION_FRAGMENT_ID,
        invariant_id=CODEC_INVARIANT_ID,
        invariant_description=CODEC_INVARIANT_DESCRIPTION,
        nodes=(nodes["K.PNH5.VIEW"], nodes["K.PNH5.CONTAINER"]),
        edges=(RelationalEdge("REL.PNH5.CONTAINER", "K.PNH5.VIEW", "K.PNH5.CONTAINER", "MAPS_TO"),),
        evidence_refs=("contract:PNCS_PNH5_TAU_FRAME_REALIZATION_V0_1", "contract:BIOOS_PNH5_CONTAINER_V0_1"),
    )
    return left, right, realization


def tau_codec_isomorphism() -> RelationalIsomorphism:
    fragments = tau_codec_fragments()
    return merge_relational_isomorphisms(fragments, merged_isomorphism_id=CODEC_ISOMORPHISM_ID)


def _codec_manifest_body(compilation: RelationalCompilation) -> dict[str, object]:
    if not isinstance(compilation, RelationalCompilation):
        raise GremlinTauCodecError("RelationalCompilation required")
    try:
        return {
            "schema": CODEC_MANIFEST_SCHEMA,
            "isomorphism_id": CODEC_ISOMORPHISM_ID,
            "source_isomorphism_fragments": [
                CODEC_LEFT_FRAGMENT_ID,
                CODEC_RIGHT_FRAGMENT_ID,
                CODEC_REALIZATION_FRAGMENT_ID,
            ],
            "invariant_id": CODEC_INVARIANT_ID,
            "kaku_candidate_ids": {
                key: value["candidate_id"] for key, value in sorted(compilation.kaku_candidates.items())
            },
            "radical_candidate_id": compilation.radical_candidate["candidate_id"],
            "operator_candidate_ids": [op["candidate_id"] for op in compilation.operator_candidates],
            "compilation_receipt_sha256": compilation.receipt["receipt_sha256"],
            "pnv_source_sha256": compilation.receipt["pnv_source_sha256"],
            "pnv_graph_sha256": compilation.receipt["pnv_graph_sha256"],
            "isomorphic_merge_applied": True,
            "shared_merge_nodes": ["K.LIMINAL.SEGMENT", "K.PNH5.VIEW"],
            "tau_is_content_carrier": True,
            "t36_is_whole_lane_witness": True,
            "state_memory_is_consolidation_boundary": True,
            "pnh5_binary_realization_bound": True,
            "file_identity_distinct_from_content_and_checkpoint": True,
            "wall_clock_in_semantic_identity": False,
            "runtime_execution_authority": False,
            "canon_write_authority": False,
            "promotion_state": "CANDIDATE_ONLY",
            "epistemic": "CHYBA",
        }
    except (KeyError, TypeError) as exc:
        raise GremlinTauCodecError("tau codec compilation is missing committed provenance fields") from exc


def _validate_tau_codec_manifest(candidate: TauCodecCompilation) -> None:
    if not isinstance(candidate, TauCodecCompilation):
        raise GremlinTauCodecError("TauCodecCompilation required")
    if not isinstance(candidate.codec_manifest, Mapping):
        raise GremlinTauCodecError("tau codec manifest mapping required")

    expected_body = _codec_manifest_body(candidate.compilation)
    observed = dict(candidate.codec_manifest)
    manifest_sha256 = observed.pop("manifest_sha256", None)
    if observed != expected_body:
        raise GremlinTauCodecError("tau codec manifest no longer matches exact compilation provenance")
    if not isinstance(manifest_sha256, str) or manifest_sha256 != _sha256(expected_body):
        raise GremlinTauCodecError("tau codec manifest commitment mismatch")


def compile_tau_codec_candidate(
    *,
    generation_binding: str,
    identity: str,
    authority: str,
    authoring_root=None,
) -> TauCodecCompilation:
    merged = tau_codec_isomorphism()
    compilation = compile_relational_isomorphism(
        merged,
        generation_binding=generation_binding,
        identity=identity,
        authority=authority,
        authoring_root=authoring_root,
    )
    manifest_body = _codec_manifest_body(compilation)
    manifest = {**manifest_body, "manifest_sha256": _sha256(manifest_body)}
    return TauCodecCompilation(compilation=compilation, codec_manifest=manifest)


def validate_tau_codec_candidate(candidate: TauCodecCompilation):
    _validate_tau_codec_manifest(candidate)
    result = validate_compiled_relational_candidate(candidate.compilation)
    if result.receipt["effect_boundary"]["external_effects"] is not False:
        raise GremlinTauCodecError("GREMLIN tau codec conformance crossed effect boundary")
    return result
