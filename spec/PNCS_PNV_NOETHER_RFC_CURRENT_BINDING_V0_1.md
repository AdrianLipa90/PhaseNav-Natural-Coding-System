# PNCS PNV Noether ↔ RFC Conserved-Current Binding v0.1

Status: `IMPLEMENTED_CANDIDATE_CURRENT_BINDING / COMMON_MEASURE_EXPLICIT / RFC_PHYSICAL_PROMOTION_GATED`

## Purpose

This contract follows `PNCS_PNV_NOETHER_COLLECTIVE_CARRIER_V0_1` and addresses the next source frontier directly:

\[
\boxed{
Q_\Sigma
\stackrel{?}{\longleftrightarrow}
Q_\vartheta
=\int_\Sigma n_\mu J_\vartheta^\mu\,dV_h.
}
\]

The executable semantic loop is

```text
SOURCE.PHASE_NOETHER.RFC_CONSERVED_CURRENT.ROUNDTRIP
```

The loop does not infer current identity from equality of total charges alone. It requires an explicit common slice/measure/cell partition and audits both local and total defects.

## 1. Finite-cell representation

For ordered cells \(C_a\) on one slice \(\Sigma\), let

\[
V_a>0
\]

be the cell volume in the pinned common measure.

The Noether normal current samples are

\[
j_{\vartheta,a},
\]

and the RFC carrier-current samples are

\[
j_{Q,a}.
\]

The finite charges are

\[
\boxed{
Q_\vartheta=\sum_a V_a j_{\vartheta,a},
\qquad
Q_\Sigma=\sum_a V_a j_{Q,a}.
}
\]

The positive candidate sector requires both totals to be positive.

## 2. Common-measure gate

The two representations carry explicit measure identifiers, ordered cell identifiers and cell volumes.

The exact semantic partition gate requires

```text
same measure_id
same ordered cell_ids
```

and the numerical volume defect is

\[
\boxed{
\Delta_V
=\frac{\sum_a|V_a^{(\vartheta)}-V_a^{(Q)}|}
{\sum_a V_a^{(\vartheta)}}.
}
\]

A declared `measure_tolerance` controls candidate numerical admission. Semantic measure-ID or cell-ID mismatch fails closed before current comparison.

## 3. Local current defect

On the common support define the volume-weighted local defect

\[
\boxed{
\Delta_{\rm local}
=\frac{\sum_a V_a|j_{Q,a}-j_{\vartheta,a}|}
{Q_\vartheta}.
}
\]

This gate is intentionally stronger than equality of total charges.

For example, with equal unit cell volumes,

\[
j_\vartheta=(1,3),
\qquad
j_Q=(2,2),
\]

we have

\[
Q_\vartheta=Q_\Sigma=4
\]

but

\[
\Delta_{\rm local}=\frac{|2-1|+|2-3|}{4}=\frac12.
\]

Thus total-charge agreement cannot by itself promote a local conserved-current identity.

## 4. Total-charge defect

The integrated mismatch is

\[
\boxed{
\Delta_Q
=\frac{|Q_\Sigma-Q_\vartheta|}{Q_\vartheta}.
}
\]

Exact current binding implies both

\[
\Delta_{\rm local}=0,
\qquad
\Delta_Q=0.
\]

The converse from \(\Delta_Q=0\) alone is not admitted.

## 5. Side-flux conservation gate

RF-N1B2 conservation uses the zero-side-flux sector. The executable state therefore carries an explicit side-flux coordinate

\[
F_{\rm side}.
\]

The audit coordinate is

\[
\boxed{
\Delta_F=|F_{\rm side}|.
}
\]

A declared `side_flux_tolerance` controls the candidate conservation gate; exact closure uses zero.

## 6. Executable state

Schema:

```text
PNCS_NOETHER_RFC_CURRENT_STATE_V0_1
```

Raw paired fields:

```text
slice_id
noether_measure_id
rfc_measure_id
noether_cell_ids
rfc_cell_ids
noether_volumes
rfc_volumes
j_theta_cells
j_q_cells
side_flux
```

Derived fields:

```text
Q_theta
Q_Sigma
Delta_measure
Delta_local_current
Delta_total_charge
side_flux_abs
```

Bound fields:

```text
Q_NOETHER=Q_theta
Q_RFC=Q_Sigma
```

## 7. Transport chain

```text
noether_rfc.resolve_common_measure
  -> verify measure IDs and ordered cell IDs
  -> derive Delta_measure, Q_theta, Q_Sigma,
     Delta_local_current, Delta_total_charge, side_flux_abs

noether_rfc.bind_conserved_current
  -> require all declared defects within tolerance
  -> expose Q_NOETHER and Q_RFC

noether_rfc.reconstruct_pair
  -> reverse-audit the bound totals
  -> reconstruct the exact paired local-current state
```

## 8. Law frame

Law nodes:

```text
LAW.NOETHER.LOCAL_NORMAL_CURRENT
LAW.SOURCE.COMMON_SLICE_MEASURE
LAW.RFC.CONSERVED_LOCAL_CURRENT
```

Domains:

```text
IDT_NOETHER_FIELD
IDT_RFC_INTERFACE
RFC_SOURCE_CARRIER
```

## 9. Invariants

```text
SOURCE.NOETHER_TOTAL_CHARGE
SOURCE.RFC_TOTAL_CHARGE
SOURCE.COMMON_MEASURE_DEFECT
SOURCE.LOCAL_CURRENT_BINDING_DEFECT
SOURCE.TOTAL_CHARGE_BINDING_DEFECT
SOURCE.SIDE_FLUX_DEFECT
```

## 10. Fail-closed conditions

```text
non-empty slice and measure IDs
unique non-empty ordered cell IDs
positive cell volumes
finite non-negative positive-sector local currents
Q_theta > 0
Q_Sigma > 0
exact semantic measure-ID agreement
exact ordered cell-ID agreement
Delta_measure <= measure_tolerance
Delta_local_current <= local_current_tolerance
Delta_total_charge <= total_charge_tolerance
side_flux_abs <= side_flux_tolerance
reverse bound totals must match recomputed totals
```

## 11. Authority boundary

This loop provides an executable candidate falsification surface for the RFC physical carrier identity. All generated KAKU/RADICAL/OPERATOR material remains

```text
EPISTEMIC CHYBA
CANDIDATE_ONLY
runtime_execution_authority=false
canon_write_authority=false
```

Promotion of `Q_Sigma <-> Q_theta` remains external to candidate authoring and requires physical cross-binding evidence.
