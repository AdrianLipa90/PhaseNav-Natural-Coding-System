# PNCS Semantic Orbital Trajectory v0.3

Status: `CANDIDATE / ORDERED_SEMANTIC_PHASE_TRAJECTORY / ORBIT_TRANSITION_RECEIPTS / PNLF_VERB_CANDIDATES / NO_STATE_MUTATION`

Stack parent: `PNCS_SEMANTIC_PHASE_INVERSE_V0_2`.

## 1. Trajectory state

For one explicit KAKU/content identity, each ordered sample carries

\[
\boxed{
X_i=
\bigl(
 t_i,
 \mathcal S_i,
 B_i,
 \omega_i,
 N_i,
 A_{R,i},
 O_i,
 \phi_{wrap,i},
 w_i
\bigr).
}
\]

`O_i`, `phi_wrap,i` and `w_i` are obtained through the v0.1/v0.2 carrier and inverse contracts.

The trajectory is

\[
\boxed{\Gamma_S=(X_0,X_1,\ldots,X_n),\qquad t_{i+1}>t_i.}
\]

All samples use one explicit orbit-quantizer profile so orbital transitions have one replayable provenance.

## 2. Adjacent transition receipt

For each ordered pair define

\[
\Delta t_i=t_{i+1}-t_i>0,
\]

\[
\Delta\mathcal S_i=\mathcal S_{i+1}-\mathcal S_i,
\]

\[
\Delta\phi_{lift,i}=\phi_{lift,i+1}-\phi_{lift,i},
\qquad
\Delta w_i=w_{i+1}-w_i.
\]

The transition receipt preserves both endpoints and these exact differences.

## 3. Orbital transition class

PNLF defines lower orbital-band index as stronger binding under the declared quantizer profile. Therefore for

\[
O_a\to O_b
\]

v0.3 classifies:

```text
b = a  -> INTRABAND_PHASE_TRANSPORT
b < a  -> ORBIT_PROMOTE_CANDIDATE
b > a  -> ORBIT_DEMOTE_CANDIDATE
```

The corresponding PNLF RADICAL verb candidate is recorded as

```text
INTRABAND_PHASE_TRANSPORT -> null
ORBIT_PROMOTE_CANDIDATE   -> PNLF.ORBIT_PROMOTE
ORBIT_DEMOTE_CANDIDATE    -> PNLF.ORBIT_DEMOTE
```

This is a receipt classification only.

## 4. Wave-coordinate provenance

Each sample retains the exact source coordinates

```text
B(t)
omega(t)
N(t)
A_R
```

alongside the semantic, phase and orbital coordinates. v0.3 does not replace these source coordinates with an inferred waveform parameterization.

## 5. Winding transport

The lossless v0.2 relation

\[
\phi_{lift}=\phi_{wrap}+2\pi w
\]

is preserved at every sample. Therefore an intraband transition may still carry nonzero

\[
\Delta\phi_{lift},\qquad \Delta w.
\]

A band hold is not treated as a zero phase transition.

## 6. Deterministic trajectory commitment

The trajectory receipt contains

- one KAKU/content identity;
- one quantizer profile and commitment;
- ordered encoded samples;
- ordered adjacent transition receipts;
- candidate PNLF verbs;
- GREMLIN candidate authority fields;
- SHA-256 over canonical JSON.

Changing sample order, a source coordinate, a winding, or quantizer provenance changes the trajectory commitment.

## 7. Admission boundary

The trajectory is candidate data for later PNLF liminal admission. It carries

```text
epistemic_state = CHYBA
promotion_state = CANDIDATE_ONLY
runtime_execution_authority = false
canon_write_authority = false
state_memory_write_authority = false
```

A PNLF verb candidate is not executed by this layer.

## 8. Validation gates

Reference tests verify:

1. strict time ordering;
2. same KAKU/content identity across all samples;
3. same quantizer provenance across all samples;
4. exact adjacent semantic/phase/winding differences;
5. intraband, promote and demote classification;
6. lower `O` index maps to promotion candidate;
7. band hold preserves phase/winding transport;
8. deterministic trajectory hashing and order sensitivity;
9. fail-closed duplicate/nonmonotonic time and mixed identities;
10. no runtime/canon/state-memory authority.

Reference implementation: `src/phasenav_natural_code/semantic_orbital_trajectory_v03.py`.
Reference tests: `tests/test_semantic_orbital_trajectory_v03.py`.
Validation receipt: `provenance/receipts/PNCS_SEMANTIC_ORBITAL_TRAJECTORY_V0_3.json`.
