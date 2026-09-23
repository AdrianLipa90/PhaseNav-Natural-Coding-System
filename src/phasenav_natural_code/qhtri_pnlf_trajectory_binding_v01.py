from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
import re
from typing import Any, Mapping, Sequence

from .orch_orbital_time_v27 import SubjectiveTimeBinding
from .pnlf_orbital_memory_v01 import (
    LiminalSegmentRevision,
    PNLFHeader,
    validate_segment_against_header,
)
from .semantic_htri_drive_v32 import digest


SCHEMA = "PNCS_QHTRI_PNLF_TRAJECTORY_BINDING_V0_1"
PARENT_SOURCE_COMMIT = "8855abed440e9949f576ffbe2153325f69e78963"
_BINDING_PREFIX = "pncs:qhtri-pnlf-trajectory-binding:sha256:"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class QHTRIPNLFTrajectoryBindingError(ValueError):
    pass


def _text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QHTRIPNLFTrajectoryBindingError(f"{name} must be non-empty text")
    return value.strip()


def _finite(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise QHTRIPNLFTrajectoryBindingError(f"{name} must be finite real")
    out = float(value)
    if not math.isfinite(out):
        raise QHTRIPNLFTrajectoryBindingError(f"{name} must be finite real")
    return out


def _positive(name: str, value: object) -> float:
    out = _finite(name, value)
    if out <= 0.0:
        raise QHTRIPNLFTrajectoryBindingError(f"{name} must be positive")
    return out


def _sha256(name: str, value: object) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise QHTRIPNLFTrajectoryBindingError(
            f"{name} must be lowercase SHA-256"
        )
    return value


def _typed_binding_digest(binding_id: str) -> str:
    value = _text("time binding id", binding_id)
    marker = ":sha256:"
    if marker not in value:
        raise QHTRIPNLFTrajectoryBindingError(
            "time binding id must be content addressed"
        )
    return _sha256("time binding digest", value.rsplit(marker, 1)[1])


@dataclass(frozen=True)
class QHTRIPNLFTrajectoryBinding:
    payload: Mapping[str, Any]
    commitment: str

    @property
    def binding_id(self) -> str:
        return _BINDING_PREFIX + self.commitment

    def deterministic_receipt(self) -> dict[str, Any]:
        return {
            **dict(self.payload),
            "t36_trajectory_commitment": self.commitment,
            "binding_id": self.binding_id,
            "epistemic_state": "CHYBA",
            "promotion_state": "CANDIDATE_ONLY",
            "runtime_execution_authority": False,
            "canon_write_authority": False,
            "state_memory_write_authority": False,
        }


def build_qhtri_pnlf_trajectory_binding(
    header: PNLFHeader,
    segment: LiminalSegmentRevision,
    htri_step_receipts: Sequence[Mapping[str, object]],
    time_bindings: Sequence[SubjectiveTimeBinding],
    *,
    numeric_tolerance: float = 1.0e-12,
) -> QHTRIPNLFTrajectoryBinding:
    if not isinstance(header, PNLFHeader):
        raise QHTRIPNLFTrajectoryBindingError("PNLFHeader required")
    if not isinstance(segment, LiminalSegmentRevision):
        raise QHTRIPNLFTrajectoryBindingError("LiminalSegmentRevision required")
    validate_segment_against_header(header, segment)
    if segment.resolution_state == "REJECTED":
        raise QHTRIPNLFTrajectoryBindingError(
            "rejected PNLF segment cannot receive trajectory binding"
        )

    if not isinstance(htri_step_receipts, (list, tuple)) or not htri_step_receipts:
        raise QHTRIPNLFTrajectoryBindingError(
            "HTRI step receipts must be a non-empty list or tuple"
        )
    if not isinstance(time_bindings, (list, tuple)) or not time_bindings:
        raise QHTRIPNLFTrajectoryBindingError(
            "time bindings must be a non-empty list or tuple"
        )
    if len(htri_step_receipts) != len(time_bindings):
        raise QHTRIPNLFTrajectoryBindingError(
            "HTRI step and time-binding counts must match"
        )

    tol = _finite("numeric_tolerance", numeric_tolerance)
    if tol < 0.0:
        raise QHTRIPNLFTrajectoryBindingError(
            "numeric_tolerance must be non-negative"
        )

    tau_start = _finite("segment tau_start", segment.tau_start)
    tau_end = _finite("segment tau_cursor", segment.tau_cursor)
    if tau_end <= tau_start:
        raise QHTRIPNLFTrajectoryBindingError(
            "trajectory binding requires positive PNLF proper-time span"
        )
    if segment.resolution_state == "ADMITTED":
        if segment.tau_end is None or abs(segment.tau_end - tau_end) > tol:
            raise QHTRIPNLFTrajectoryBindingError(
                "admitted segment tau_end must equal tau_cursor"
            )

    steps: list[dict[str, object]] = []
    proper_sum = 0.0

    for index, (raw_receipt, time_binding) in enumerate(
        zip(htri_step_receipts, time_bindings)
    ):
        if not isinstance(raw_receipt, Mapping):
            raise QHTRIPNLFTrajectoryBindingError(
                "HTRI step receipt must be a mapping"
            )
        if not isinstance(time_binding, SubjectiveTimeBinding):
            raise QHTRIPNLFTrajectoryBindingError(
                "SubjectiveTimeBinding required for every HTRI step"
            )
        receipt = dict(raw_receipt)
        htri_dt = _positive("HTRI step dt", receipt.get("dt"))
        h_sha = _sha256("H_sha256", receipt.get("H_sha256"))
        coordinate_dt = _positive(
            "time binding coordinate_dt",
            time_binding.coordinate_dt,
        )
        combined_g = _positive(
            "time binding combined_g",
            time_binding.combined_g,
        )
        proper_dt = _positive(
            "time binding proper_dt",
            time_binding.proper_dt,
        )
        if abs(htri_dt - coordinate_dt) > tol:
            raise QHTRIPNLFTrajectoryBindingError(
                "HTRI dt differs from ORCH coordinate_dt"
            )
        if abs(proper_dt - coordinate_dt * combined_g) > tol:
            raise QHTRIPNLFTrajectoryBindingError(
                "ORCH proper_dt differs from coordinate_dt*combined_g"
            )

        time_model_id = time_binding.kernel.kernel_id
        if time_model_id != header.proper_time_model_id:
            raise QHTRIPNLFTrajectoryBindingError(
                "time binding kernel differs from PNLF proper-time model"
            )

        step = {
            "step_index": index,
            "htri_step_receipt_sha256": digest(receipt),
            "H_sha256": h_sha,
            "htri_dt": htri_dt,
            "coordinate_dt": coordinate_dt,
            "time_binding_receipt_sha256": _typed_binding_digest(
                time_binding.binding_id
            ),
            "time_binding_model_id": time_model_id,
            "combined_g": combined_g,
            "proper_dt": proper_dt,
        }
        steps.append(step)
        proper_sum += proper_dt

    layer_span = tau_end - tau_start
    if abs(proper_sum - layer_span) > tol:
        raise QHTRIPNLFTrajectoryBindingError(
            "accumulated ORCH proper time does not close PNLF segment"
        )

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "source_pncs_commit": PARENT_SOURCE_COMMIT,
        "segment_id": segment.segment_id,
        "t36_basis_id": header.t36_basis_id,
        "proper_time_model_id": header.proper_time_model_id,
        "tau_start": tau_start,
        "tau_end": tau_end,
        "numeric_tolerance": tol,
        "steps": steps,
    }
    commitment = digest(payload)
    return QHTRIPNLFTrajectoryBinding(payload, commitment)


def require_segment_trajectory_commitment(
    binding: QHTRIPNLFTrajectoryBinding,
    segment: LiminalSegmentRevision,
) -> None:
    if not isinstance(binding, QHTRIPNLFTrajectoryBinding):
        raise QHTRIPNLFTrajectoryBindingError(
            "QHTRIPNLFTrajectoryBinding required"
        )
    if not isinstance(segment, LiminalSegmentRevision):
        raise QHTRIPNLFTrajectoryBindingError(
            "LiminalSegmentRevision required"
        )
    if binding.payload["segment_id"] != segment.segment_id:
        raise QHTRIPNLFTrajectoryBindingError("segment id mismatch")
    if abs(float(binding.payload["tau_start"]) - segment.tau_start) > float(
        binding.payload["numeric_tolerance"]
    ):
        raise QHTRIPNLFTrajectoryBindingError("segment tau_start mismatch")
    if abs(float(binding.payload["tau_end"]) - segment.tau_cursor) > float(
        binding.payload["numeric_tolerance"]
    ):
        raise QHTRIPNLFTrajectoryBindingError("segment tau_cursor mismatch")
    if segment.t36_trajectory_commitment != binding.commitment:
        raise QHTRIPNLFTrajectoryBindingError(
            "PNLF t36_trajectory_commitment does not match QHTRI/ORCH binding"
        )


__all__ = [
    "SCHEMA",
    "PARENT_SOURCE_COMMIT",
    "QHTRIPNLFTrajectoryBindingError",
    "QHTRIPNLFTrajectoryBinding",
    "build_qhtri_pnlf_trajectory_binding",
    "require_segment_trajectory_commitment",
]
