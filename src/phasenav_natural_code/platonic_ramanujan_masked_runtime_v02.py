from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np

from .platonic_ramanujan_stabilizer_v01 import support_mask
from .semantic_htri_drive_v32 import (
    ControlledStep,
    DriveSnapshot,
    array_sha,
    controlled_step,
    qhtri_graph_hamiltonian,
)

SCHEMA = "PNCS_PLATONIC_RAMANUJAN_MASKED_RUNTIME_V0_2"
STATUS = "CANDIDATE"
CANDIDATE_ID = "PNCS_SUPPORT_MASK_PARENT_G_V0_2"


class PlatonicRamanujanMaskedRuntimeV02Error(ValueError):
    pass


@dataclass(frozen=True)
class CandidateRuntimeMetadata:
    schema: str = SCHEMA
    status: str = STATUS
    candidate_id: str = CANDIDATE_ID
    executable: bool = True
    default_enabled: bool = False
    parent_contract: str = "PNCS_ORDERED_T36_TO_HTRI_DRIVE_V0_32"
    physical_binding: bool = False


def _require_candidate_enabled(candidate_enabled: bool) -> None:
    if candidate_enabled is not True:
        raise PlatonicRamanujanMaskedRuntimeV02Error(
            "masked PhaseNav runtime is CANDIDATE; pass candidate_enabled=True explicitly"
        )


def masked_parent_g(
    g: Sequence[Sequence[float]],
    *,
    candidate_enabled: bool,
) -> np.ndarray:
    """Return a non-mutating sparse candidate copy of the parent 36x36 coupling.

    The canonical v0.32 matrix is never modified. The mask is the already
    canonized I_12 square K_3 structural support.
    """
    _require_candidate_enabled(candidate_enabled)
    try:
        x = np.asarray(g, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise PlatonicRamanujanMaskedRuntimeV02Error(
            "g must be a finite real 36x36 matrix"
        ) from exc
    if x.shape != (36, 36) or not np.isfinite(x).all():
        raise PlatonicRamanujanMaskedRuntimeV02Error(
            "g must be a finite real 36x36 matrix"
        )
    return np.where(support_mask(), x, 0.0)


def candidate_masked_controlled_step(
    snapshot: DriveSnapshot,
    target36: Sequence[float],
    *,
    dt: float = 0.01,
    candidate_enabled: bool,
) -> ControlledStep:
    """Execute parent v0.32 while preserving sparse support as a candidate invariant.

    The parent dynamics are not edited. This wrapper:
      1. masks only a copy of the input coupling matrix;
      2. executes the existing v0.32 controlled step;
      3. re-applies the same mask after the adaptive g update;
      4. rebuilds the QHTRI Hamiltonian from the masked g_next;
      5. preserves CANDIDATE provenance in the returned receipt.

    This specifically tests the previously open support_mask_parent_g gate. It
    does not revive the rejected additive C_PR v0.1 term.
    """
    _require_candidate_enabled(candidate_enabled)
    if not isinstance(snapshot, DriveSnapshot):
        raise PlatonicRamanujanMaskedRuntimeV02Error("snapshot must be DriveSnapshot")
    if not math.isfinite(float(dt)) or float(dt) <= 0.0:
        raise PlatonicRamanujanMaskedRuntimeV02Error("dt must be positive finite")

    mask = support_mask()
    g0 = masked_parent_g(snapshot.g, candidate_enabled=True)
    candidate_snapshot = DriveSnapshot.build(
        phi=snapshot.phi,
        omega=snapshot.omega,
        g=g0,
        flavor=snapshot.flavor,
        tau=snapshot.tau,
        gravity=snapshot.gravity,
        source_id=f"{snapshot.source_id}:candidate:{CANDIDATE_ID}",
    )

    parent = controlled_step(candidate_snapshot, target36, dt=float(dt))

    # Keep the candidate support invariant after the parent's adaptive update.
    g_next = np.where(mask, parent.g_next, 0.0)
    H, hmeta = qhtri_graph_hamiltonian(snapshot.omega, g_next)
    herm = float(np.max(np.abs(H - H.conj().T)))

    receipt = dict(parent.receipt)
    receipt.update(
        {
            "schema": SCHEMA,
            "status": STATUS,
            "candidate_id": CANDIDATE_ID,
            "candidate_executable": True,
            "default_enabled": False,
            "parent_contract": "PNCS_ORDERED_T36_TO_HTRI_DRIVE_V0_32",
            "parent_snapshot_id": snapshot.snapshot_id,
            "masked_snapshot_id": candidate_snapshot.snapshot_id,
            "support_mask_degree": 7,
            "support_mask_directed_nonzeros": int(mask.sum()),
            "support_mask_parent_g_invariant": True,
            "outside_mask_nonzeros_g_next": int(np.count_nonzero(g_next[~mask])),
            "g_next_sha256": array_sha(g_next),
            "H_sha256": array_sha(H),
            "hermiticity_error": herm,
            "qhtri_hamiltonian": hmeta,
            "additive_C_PR_v0_1": "NOT_USED",
            "physical_binding": False,
        }
    )
    return ControlledStep(
        parent.phi_next,
        g_next,
        parent.gravity_next,
        parent.control,
        H,
        receipt,
    )


def candidate_metadata() -> dict[str, object]:
    meta = CandidateRuntimeMetadata()
    return {
        "schema": meta.schema,
        "status": meta.status,
        "candidate_id": meta.candidate_id,
        "executable": meta.executable,
        "default_enabled": meta.default_enabled,
        "parent_contract": meta.parent_contract,
        "physical_binding": meta.physical_binding,
        "gate_target": "support_mask_parent_g_activation",
        "replaces": None,
        "preserves_rejection": "additive_C_PR_activation=REJECTED_V0_1",
    }
