from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Sequence

from .semantic_phase_inverse_v02 import SemanticPhasePlacement


SCHEMA = "PNCS_SEMANTIC_ORBITAL_TRAJECTORY_V0_3"
INTRABAND_PHASE_TRANSPORT = "INTRABAND_PHASE_TRANSPORT"
ORBIT_PROMOTE_CANDIDATE = "ORBIT_PROMOTE_CANDIDATE"
ORBIT_DEMOTE_CANDIDATE = "ORBIT_DEMOTE_CANDIDATE"


class SemanticOrbitalTrajectoryError(ValueError):
    pass


def _finite(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise SemanticOrbitalTrajectoryError(f"{name} must be finite")
    return value


def _band_index(band: str) -> int:
    text = str(band)
    if len(text) != 2 or text[0] != "O" or text[1] not in "012345678":
        raise SemanticOrbitalTrajectoryError("orbital band must be O0..O8")
    return int(text[1])


def transition_class(source_band: str, target_band: str) -> str:
    source = _band_index(source_band)
    target = _band_index(target_band)
    if target == source:
        return INTRABAND_PHASE_TRANSPORT
    if target < source:
        return ORBIT_PROMOTE_CANDIDATE
    return ORBIT_DEMOTE_CANDIDATE


def pnlf_verb_candidate(kind: str) -> str | None:
    if kind == INTRABAND_PHASE_TRANSPORT:
        return None
    if kind == ORBIT_PROMOTE_CANDIDATE:
        return "PNLF.ORBIT_PROMOTE"
    if kind == ORBIT_DEMOTE_CANDIDATE:
        return "PNLF.ORBIT_DEMOTE"
    raise SemanticOrbitalTrajectoryError(f"unknown transition class: {kind}")


@dataclass(frozen=True)
class SemanticOrbitalTransition:
    index: int
    source: SemanticPhasePlacement
    target: SemanticPhasePlacement

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or isinstance(self.index, bool) or self.index < 0:
            raise SemanticOrbitalTrajectoryError("transition index must be a non-negative integer")
        if not isinstance(self.source, SemanticPhasePlacement) or not isinstance(
            self.target, SemanticPhasePlacement
        ):
            raise SemanticOrbitalTrajectoryError("transition endpoints must be SemanticPhasePlacement")
        if self.source.content_id != self.target.content_id or self.source.kaku_id != self.target.kaku_id:
            raise SemanticOrbitalTrajectoryError("transition endpoints must preserve KAKU/content identity")
        if self.source.quantizer.to_dict() != self.target.quantizer.to_dict():
            raise SemanticOrbitalTrajectoryError("transition endpoints must use one quantizer profile")
        if not self.target.sample_time > self.source.sample_time:
            raise SemanticOrbitalTrajectoryError("transition time must increase strictly")

    @property
    def delta_time(self) -> float:
        return self.target.sample_time - self.source.sample_time

    @property
    def delta_semantic(self) -> float:
        return self.target.semantic_target - self.source.semantic_target

    @property
    def delta_lifted_phase(self) -> float:
        return self.target.phase_code.lifted_phase - self.source.phase_code.lifted_phase

    @property
    def delta_winding(self) -> int:
        return self.target.phase_code.winding - self.source.phase_code.winding

    @property
    def kind(self) -> str:
        return transition_class(self.source.orbital_band, self.target.orbital_band)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "source_time": self.source.sample_time,
            "target_time": self.target.sample_time,
            "source_band": self.source.orbital_band,
            "target_band": self.target.orbital_band,
            "transition_class": self.kind,
            "pnlf_radical_candidate": pnlf_verb_candidate(self.kind),
            "delta_time": self.delta_time,
            "delta_semantic": self.delta_semantic,
            "delta_lifted_phase": self.delta_lifted_phase,
            "delta_winding": self.delta_winding,
            "source_wrapped_phase": self.source.phase_code.wrapped_phase,
            "target_wrapped_phase": self.target.phase_code.wrapped_phase,
            "source_carrier": {
                "B": float(self.source.B),
                "omega": float(self.source.omega),
                "N": float(self.source.N),
                "A_R": float(self.source.A_R),
            },
            "target_carrier": {
                "B": float(self.target.B),
                "omega": float(self.target.omega),
                "N": float(self.target.N),
                "A_R": float(self.target.A_R),
            },
        }


@dataclass(frozen=True)
class SemanticOrbitalTrajectory:
    placements: tuple[SemanticPhasePlacement, ...]

    def __post_init__(self) -> None:
        if not self.placements:
            raise SemanticOrbitalTrajectoryError("trajectory requires at least one placement")
        if any(not isinstance(p, SemanticPhasePlacement) for p in self.placements):
            raise SemanticOrbitalTrajectoryError("all trajectory samples must be SemanticPhasePlacement")
        first = self.placements[0]
        quantizer = first.quantizer.to_dict()
        previous_time = _finite("sample_time[0]", first.sample_time)
        for index, placement in enumerate(self.placements):
            if placement.content_id != first.content_id or placement.kaku_id != first.kaku_id:
                raise SemanticOrbitalTrajectoryError("trajectory must preserve one KAKU/content identity")
            if placement.quantizer.to_dict() != quantizer:
                raise SemanticOrbitalTrajectoryError("trajectory must preserve one quantizer profile")
            current_time = _finite(f"sample_time[{index}]", placement.sample_time)
            if index > 0 and not current_time > previous_time:
                raise SemanticOrbitalTrajectoryError("trajectory sample times must increase strictly")
            previous_time = current_time

    @property
    def transitions(self) -> tuple[SemanticOrbitalTransition, ...]:
        return tuple(
            SemanticOrbitalTransition(i, self.placements[i], self.placements[i + 1])
            for i in range(len(self.placements) - 1)
        )

    def body(self) -> dict[str, Any]:
        first = self.placements[0]
        return {
            "schema": SCHEMA,
            "parent_schema": "PNCS_SEMANTIC_PHASE_INVERSE_V0_2",
            "content_id": first.content_id,
            "kaku_id": first.kaku_id,
            "quantizer": first.quantizer.to_dict(),
            "samples": [placement.body() for placement in self.placements],
            "transitions": [transition.to_dict() for transition in self.transitions],
            "epistemic_state": "CHYBA",
            "promotion_state": "CANDIDATE_ONLY",
            "runtime_execution_authority": False,
            "canon_write_authority": False,
            "state_memory_write_authority": False,
        }

    def deterministic_receipt(self) -> dict[str, Any]:
        body = self.body()
        encoded = json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return {**body, "trajectory_sha256": hashlib.sha256(encoded).hexdigest()}


def build_semantic_orbital_trajectory(
    placements: Sequence[SemanticPhasePlacement],
) -> SemanticOrbitalTrajectory:
    return SemanticOrbitalTrajectory(tuple(placements))
