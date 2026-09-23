
# PNCS QHTRI -> ORCH Proper Time -> PNLF Trajectory Binding v0.1

Status: CANDIDATE / READ_ONLY_PROVENANCE_EMITTER / FAIL_CLOSED / NO_STATE_MEMORY_WRITE_AUTHORITY

## 1. Purpose

This module binds an ordered sequence of existing HTRI/QHTRI step receipts to
existing ORCH subjective/proper-time bindings and emits one deterministic
candidate commitment for a PNLF liminal T36 trajectory.

It does not mutate a PNLF segment and does not admit State Memory.

The pipeline is:

QHTRI step receipts
-> ORCH SubjectiveTimeBinding sequence
-> PNLF header + liminal interval identity
-> canonical ordered payload
-> t36_trajectory_commitment candidate.

## 2. Source contracts

The implementation composes existing PNCS contracts:

- PNCS_ORDERED_T36_TO_HTRI_DRIVE_V0_32
- PNCS_BOUNDED_MULTI_TICK_HTRI_DRIVE_V0_33
- PNCS_ORCHORBITAL_HYDRO_RUNTIME_V0_27
- PNLF_ORBITAL_MEMORY_V0_1

Parent source pin:

8855abed440e9949f576ffbe2153325f69e78963

## 3. Per-step identity

For every ordered HTRI step the emitter records:

- zero-based contiguous step index;
- SHA-256 of the complete HTRI step receipt;
- H_sha256 from that receipt;
- HTRI dt;
- ORCH coordinate_dt;
- SHA-256 extracted from the content-addressed ORCH time binding ID;
- ORCH time kernel ID;
- combined_g;
- proper_dt.

The exact gates are

[
dt_{m HTRI}=dt_{m coord}
]

and

[
Delta	au=dt_{m coord}g_{m combined}
]

within the declared numerical tolerance.

Every time-binding kernel ID must equal the PNLF header
proper_time_model_id.

## 4. PNLF interval closure

The emitter validates the supplied PNLF header against the liminal segment.

REJECTED segments fail closed.

For an OPEN candidate segment, the prospective layer endpoint is tau_cursor.
For an ADMITTED segment, the existing PNLF invariant additionally requires

[
	au_{m end}=	au_{m cursor}.
]

The ordered proper-time increments must satisfy

[
oxed{
sum_k Delta	au_k
=
	au_{m cursor}-	au_{m start}.
}
]

Thus raw HTRI tick count is not used as PNLF proper time.

## 5. Canonical candidate commitment

The emitted identity payload contains:

- schema;
- parent source commit;
- segment_id;
- PNLF t36_basis_id;
- PNLF proper_time_model_id;
- tau_start;
- prospective tau_end = tau_cursor;
- numeric tolerance;
- ordered step records.

It is hashed with the canonical PNCS digest function.

The raw 64-character digest is the candidate

[
oxed{
mathrm{t36_trajectory_commitment}.
}
]

The typed bridge identity is

pncs:qhtri-pnlf-trajectory-binding:sha256:<digest>.

## 6. Explicit non-cyclic workflow

The emitter does not consume the segment's current t36 trajectory commitment
when constructing the new candidate. This avoids circular identity.

The intended append-only workflow is:

1. OPEN/advance liminal segment to the desired tau_cursor;
2. build QHTRI/ORCH trajectory binding candidate;
3. advance/revise the OPEN segment with the emitted commitment;
4. verify exact commitment equality;
5. perform the ordinary PNLF State Commit / admission path.

No direct State Memory write occurs in this module.

## 7. Authority boundary

The deterministic receipt states:

epistemic_state = CHYBA
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
state_memory_write_authority = false

The module does not derive a physical time law and does not alter HTRI,
ORCH, or PNLF dynamics.

## 8. Validation gates

Reference tests require:

1. real HTRI step receipts from the v0.32 controlled-step implementation;
2. exact ORCH coordinate/proper-time arithmetic;
3. exact closure on a real PNLF OPEN segment;
4. deterministic candidate commitment;
5. successful re-binding of the candidate commitment into a revised segment;
6. successful preservation through ordinary PNLF admission;
7. failure on mixed time kernels;
8. failure on HTRI dt / ORCH coordinate_dt mismatch;
9. failure on proper-time span mismatch;
10. failure on stale segment trajectory commitment;
11. commitment sensitivity to ordered step sequence and T36 basis identity;
12. candidate-only authority fields.

Reference implementation:
src/phasenav_natural_code/qhtri_pnlf_trajectory_binding_v01.py

Reference tests:
tests/test_qhtri_pnlf_trajectory_binding_v01.py
