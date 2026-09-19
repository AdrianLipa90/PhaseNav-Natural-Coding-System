"""PNCS relational observation packet v0.1.

Typed transport only. This module does not bind chemical/spectroscopic holonomy
to PNCS semantic holonomy and never flattens observations into canonical T36.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA = "PNCS_RELATIONAL_OBSERVATION_PACKET_V0_1"


class RelationalObservationPacketError(ValueError):
    pass


def _finite(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise RelationalObservationPacketError(f"{name} must be finite")
    return value


def _nonempty(name: str, value: str) -> str:
    value = str(value).strip()
    if not value:
        raise RelationalObservationPacketError(f"{name} must be non-empty")
    return value


@dataclass(frozen=True)
class RelationalObservationPacket:
    frequency: float
    intensity: float
    phase: float
    linewidth: float
    coherence: float
    phase_count: int
    cycle_rank: int
    jacobian_rank: int
    fisher_rank: int
    fully_identifiable: bool
    upstream_repository: str
    upstream_branch: str
    upstream_commit: str
    upstream_schema: str
    upstream_receipt: str
    epistemic: str = "CHYBA"
    candidate_only: bool = True
    flatten_into_t36: bool = False

    def validate(self) -> None:
        _finite("frequency", self.frequency)
        intensity = _finite("intensity", self.intensity)
        _finite("phase", self.phase)
        linewidth = _finite("linewidth", self.linewidth)
        coherence = _finite("coherence", self.coherence)

        if intensity < 0.0:
            raise RelationalObservationPacketError("intensity must be >= 0")
        if linewidth < 0.0:
            raise RelationalObservationPacketError("linewidth must be >= 0")
        if not 0.0 <= coherence <= 1.0:
            raise RelationalObservationPacketError("coherence must lie in [0,1]")

        for name, value in (
            ("phase_count", self.phase_count),
            ("cycle_rank", self.cycle_rank),
            ("jacobian_rank", self.jacobian_rank),
            ("fisher_rank", self.fisher_rank),
        ):
            if not isinstance(value, int) or value < 0:
                raise RelationalObservationPacketError(
                    f"{name} must be a non-negative integer"
                )

        if self.cycle_rank > self.phase_count:
            raise RelationalObservationPacketError(
                "cycle_rank cannot exceed phase_count"
            )
        if self.jacobian_rank > self.phase_count:
            raise RelationalObservationPacketError(
                "jacobian_rank cannot exceed phase_count"
            )
        if self.fisher_rank > self.phase_count:
            raise RelationalObservationPacketError(
                "fisher_rank cannot exceed phase_count"
            )

        expected_identifiable = (
            self.jacobian_rank >= self.cycle_rank
            and self.fisher_rank >= self.cycle_rank
        )
        if bool(self.fully_identifiable) != expected_identifiable:
            raise RelationalObservationPacketError(
                "fully_identifiable is inconsistent with declared ranks"
            )

        _nonempty("upstream_repository", self.upstream_repository)
        _nonempty("upstream_branch", self.upstream_branch)
        commit = _nonempty("upstream_commit", self.upstream_commit)
        if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit.lower()):
            raise RelationalObservationPacketError(
                "upstream_commit must be a 40-character hexadecimal SHA"
            )
        _nonempty("upstream_schema", self.upstream_schema)
        _nonempty("upstream_receipt", self.upstream_receipt)
        _nonempty("epistemic", self.epistemic)

        if self.flatten_into_t36:
            raise RelationalObservationPacketError(
                "relational observation packets must not flatten into canonical T36"
            )

    def as_mapping(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": SCHEMA,
            "observables": {
                "frequency": float(self.frequency),
                "intensity": float(self.intensity),
                "phase": float(self.phase),
                "linewidth": float(self.linewidth),
                "coherence": float(self.coherence),
            },
            "identifiability": {
                "phase_count": self.phase_count,
                "cycle_rank": self.cycle_rank,
                "jacobian_rank": self.jacobian_rank,
                "fisher_rank": self.fisher_rank,
                "fully_identifiable": bool(self.fully_identifiable),
            },
            "provenance": {
                "repository": self.upstream_repository,
                "branch": self.upstream_branch,
                "commit": self.upstream_commit,
                "schema": self.upstream_schema,
                "receipt": self.upstream_receipt,
            },
            "epistemic": self.epistemic,
            "candidate_only": bool(self.candidate_only),
            "flatten_into_t36": False,
            "semantic_holonomy_equivalence": "OPEN",
        }


def validate_relational_observation_packet(packet: Mapping[str, Any]) -> None:
    if packet.get("schema") != SCHEMA:
        raise RelationalObservationPacketError("unexpected packet schema")
    if packet.get("flatten_into_t36") is not False:
        raise RelationalObservationPacketError(
            "flatten_into_t36 must be exactly false"
        )
    if packet.get("semantic_holonomy_equivalence") != "OPEN":
        raise RelationalObservationPacketError(
            "semantic holonomy equivalence must remain OPEN"
        )

    obs = packet.get("observables")
    ident = packet.get("identifiability")
    prov = packet.get("provenance")
    if not isinstance(obs, Mapping) or not isinstance(ident, Mapping) or not isinstance(prov, Mapping):
        raise RelationalObservationPacketError(
            "observables, identifiability and provenance must be mappings"
        )

    rebuilt = RelationalObservationPacket(
        frequency=obs.get("frequency"),
        intensity=obs.get("intensity"),
        phase=obs.get("phase"),
        linewidth=obs.get("linewidth"),
        coherence=obs.get("coherence"),
        phase_count=ident.get("phase_count"),
        cycle_rank=ident.get("cycle_rank"),
        jacobian_rank=ident.get("jacobian_rank"),
        fisher_rank=ident.get("fisher_rank"),
        fully_identifiable=ident.get("fully_identifiable"),
        upstream_repository=prov.get("repository"),
        upstream_branch=prov.get("branch"),
        upstream_commit=prov.get("commit"),
        upstream_schema=prov.get("schema"),
        upstream_receipt=prov.get("receipt"),
        epistemic=packet.get("epistemic", ""),
        candidate_only=bool(packet.get("candidate_only", False)),
        flatten_into_t36=bool(packet.get("flatten_into_t36", True)),
    )
    rebuilt.validate()
