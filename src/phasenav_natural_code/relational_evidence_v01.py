"""PNCS relational evidence packet v0.1.

This module validates a GREMLIN cross-modal evidence packet and wraps it as a
non-promoting PNCS routing object. It never selects a physical source and never
flattens the diagnostic into canonical T36.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

UPSTREAM_SCHEMA = "GREMLIN_CROSS_MODAL_RELATIONAL_EVIDENCE_PACKET_V0_1"
SCHEMA = "PNCS_RELATIONAL_EVIDENCE_PACKET_V0_1"
_ALLOWED_STATES = {"CONSISTENT", "INCONSISTENT", "UNDERDETERMINED"}


class RelationalEvidencePacketError(ValueError):
    pass


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _nonempty(name: str, value: Any) -> str:
    text = str(value).strip()
    if not text:
        raise RelationalEvidencePacketError(f"{name} must be non-empty")
    return text


def verify_gremlin_evidence_packet(packet: Mapping[str, Any]) -> None:
    if packet.get("schema") != UPSTREAM_SCHEMA:
        raise RelationalEvidencePacketError("unexpected GREMLIN evidence schema")
    if packet.get("physical_source_selected") is not False:
        raise RelationalEvidencePacketError(
            "physical_source_selected must be exactly false"
        )

    state = packet.get("consistency_state")
    if state not in _ALLOWED_STATES:
        raise RelationalEvidencePacketError("invalid consistency_state")

    digest = packet.get("packet_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise RelationalEvidencePacketError(
            "packet_sha256 must be a 64-character hexadecimal digest"
        )
    if any(ch not in "0123456789abcdef" for ch in digest.lower()):
        raise RelationalEvidencePacketError("packet_sha256 must be hexadecimal")

    base = dict(packet)
    base.pop("packet_sha256", None)
    expected = hashlib.sha256(_canonical_json(base)).hexdigest()
    if digest.lower() != expected:
        raise RelationalEvidencePacketError("GREMLIN evidence packet hash mismatch")

    phase = packet.get("phase_identifiability")
    if not isinstance(phase, Mapping):
        raise RelationalEvidencePacketError(
            "phase_identifiability must be a mapping"
        )
    for name in ("phase_count", "cycle_rank", "jacobian_rank", "fisher_rank"):
        value = phase.get(name)
        if not isinstance(value, int) or value < 0:
            raise RelationalEvidencePacketError(
                f"phase_identifiability.{name} must be a non-negative integer"
            )
    if phase["cycle_rank"] > phase["phase_count"]:
        raise RelationalEvidencePacketError(
            "cycle_rank cannot exceed phase_count"
        )
    if phase["jacobian_rank"] > phase["phase_count"]:
        raise RelationalEvidencePacketError(
            "jacobian_rank cannot exceed phase_count"
        )
    if phase["fisher_rank"] > phase["phase_count"]:
        raise RelationalEvidencePacketError(
            "fisher_rank cannot exceed phase_count"
        )

    expected_identifiable = (
        phase["jacobian_rank"] >= phase["cycle_rank"]
        and phase["fisher_rank"] >= phase["cycle_rank"]
    )
    if bool(phase.get("fully_identifiable")) != expected_identifiable:
        raise RelationalEvidencePacketError(
            "fully_identifiable inconsistent with declared phase ranks"
        )

    channels = packet.get("channels")
    if not isinstance(channels, list) or not channels:
        raise RelationalEvidencePacketError(
            "channels must be a non-empty list"
        )
    for index, channel in enumerate(channels):
        if not isinstance(channel, Mapping):
            raise RelationalEvidencePacketError(
                f"channels[{index}] must be a mapping"
            )
        _nonempty(f"channels[{index}].name", channel.get("name"))
        prov = channel.get("provenance")
        if not isinstance(prov, Mapping):
            raise RelationalEvidencePacketError(
                f"channels[{index}].provenance must be a mapping"
            )
        for key in ("repository", "branch", "commit", "schema", "receipt"):
            _nonempty(f"channels[{index}].provenance.{key}", prov.get(key))
        commit = str(prov.get("commit"))
        if len(commit) != 40 or any(
            ch not in "0123456789abcdef" for ch in commit.lower()
        ):
            raise RelationalEvidencePacketError(
                f"channels[{index}].provenance.commit must be a 40-char SHA"
            )

    source = packet.get("source_attribution")
    if not isinstance(source, Mapping):
        raise RelationalEvidencePacketError(
            "source_attribution must be a mapping"
        )
    if source.get("admissible") is not packet.get(
        "source_attribution_admissible"
    ):
        raise RelationalEvidencePacketError(
            "source attribution admissibility fields disagree"
        )


def routing_decision(packet: Mapping[str, Any]) -> str:
    """Return a conservative PNCS route without selecting a physical source."""

    verify_gremlin_evidence_packet(packet)
    state = packet["consistency_state"]
    admissible = bool(packet["source_attribution_admissible"])

    if state == "INCONSISTENT":
        return "STOP_DECLARED_MODEL"
    if state == "UNDERDETERMINED":
        return "REQUEST_MORE_CONSTRAINTS"
    if not admissible:
        return "NO_SOURCE_ROUTE"
    return "ALLOW_CANDIDATE_SOURCE_TESTS"


@dataclass(frozen=True)
class PNCSRelationalEvidencePacket:
    gremlin_packet: Mapping[str, Any]
    upstream_repository: str
    upstream_branch: str
    upstream_commit: str
    upstream_receipt: str
    epistemic: str = "CHYBA"
    candidate_only: bool = True
    flatten_into_t36: bool = False

    def validate(self) -> None:
        verify_gremlin_evidence_packet(self.gremlin_packet)
        _nonempty("upstream_repository", self.upstream_repository)
        _nonempty("upstream_branch", self.upstream_branch)
        commit = _nonempty("upstream_commit", self.upstream_commit)
        if len(commit) != 40 or any(
            ch not in "0123456789abcdef" for ch in commit.lower()
        ):
            raise RelationalEvidencePacketError(
                "upstream_commit must be a 40-character hexadecimal SHA"
            )
        _nonempty("upstream_receipt", self.upstream_receipt)
        _nonempty("epistemic", self.epistemic)
        if self.flatten_into_t36:
            raise RelationalEvidencePacketError(
                "relational evidence must not flatten into canonical T36"
            )

    def as_mapping(self) -> dict[str, Any]:
        self.validate()
        route = routing_decision(self.gremlin_packet)
        return {
            "schema": SCHEMA,
            "status": "CANDIDATE_ONLY",
            "route": route,
            "consistency_state": self.gremlin_packet["consistency_state"],
            "source_attribution_admissible": bool(
                self.gremlin_packet["source_attribution_admissible"]
            ),
            "physical_source_selected": False,
            "flatten_into_t36": False,
            "semantic_holonomy_equivalence": "OPEN",
            "epistemic": self.epistemic,
            "candidate_only": bool(self.candidate_only),
            "upstream": {
                "repository": self.upstream_repository,
                "branch": self.upstream_branch,
                "commit": self.upstream_commit,
                "receipt": self.upstream_receipt,
                "schema": UPSTREAM_SCHEMA,
                "packet_sha256": self.gremlin_packet["packet_sha256"],
            },
            "gremlin_evidence": dict(self.gremlin_packet),
        }
