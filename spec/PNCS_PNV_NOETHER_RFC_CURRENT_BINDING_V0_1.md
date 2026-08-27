# PNCS PNV Noether ↔ RFC Conserved-Current Binding v0.1

Status: `IMPLEMENTED_CANDIDATE_CURRENT_BINDING / EXACT_DEFECT_BOUND / COMMON_SLICE_MEASURE_ORIENTATION_EXPLICIT / RFC_PHYSICAL_PROMOTION_GATED`

## Purpose

This contract follows `PNCS_PNV_NOETHER_COLLECTIVE_CARRIER_V0_1` and addresses

\[
\boxed{
Q_\Sigma
\stackrel{?}{\longleftrightarrow}
Q_\vartheta
=\int_\Sigma n_\mu J_\vartheta^\mu\,dV_h.
}
\]

The executable loop is

```text
SOURCE.PHASE_NOETHER.RFC_CONSERVED_CURRENT.ROUNDTRIP
```

The loop rejects promotion from integrated-charge equality alone. It requires a common slice, normal orientation, measure identity, ordered cell partition, local-current control and side-flux convention.

## 1. Paired finite-cell representation

On one ordered cell partition \(C_a\), the Noether representation carries

\[
j_{\vartheta,a},\qquad V_a^{(\vartheta)}>0,
\]

and the RFC representation carries

\[
j_{Q,a},\qquad V_a^{(Q)}>0.
\]

The normal-current samples are taken on the same declared slice and normal orientation. The positive-source sector uses finite non-negative cell currents and

\[
\boxed{
Q_\vartheta=\sum_a V_a^{(\vartheta)}j_{\vartheta,a}>0,
\qquad
Q_\Sigma=\sum_a V_a^{(Q)}j_{Q,a}>0.
}
\]

## 2. Semantic common-slice gates

The paired state records

```text
slice_id
noether_measure_id
rfc_measure_id
noether_normal_id
rfc_normal_id
noether_cell_ids
rfc_cell_ids
```

and fails closed unless

```text
same measure_id
same normal orientation id
same ordered cell_ids
```

before local-current promotion.

## 3. Exact local current and measure defects

The current mismatch is normalized by the finite Noether charge:

\[
\boxed{
\Delta_J
:=
\frac{\sum_aV_a^{(Q)}|j_{Q,a}-j_{\vartheta,a}|}{Q_\vartheta}.
}
\]

The measure mismatch is weighted by the actual Noether current support:

\[
\boxed{
\Delta_V
:=
\frac{\sum_a|V_a^{(Q)}-V_a^{(\vartheta)}|\,|j_{\vartheta,a}|}{Q_\vartheta}.
}
\]

The integrated extensive-charge mismatch is

\[
\boxed{
\Delta_\Sigma
:=
\frac{|Q_\Sigma-Q_\vartheta|}{Q_\vartheta}.
}
\]

The executable field names are

```text
Delta_local_current = Delta_J
Delta_measure       = Delta_V
Delta_total_charge  = Delta_Sigma
```

## 4. Exact defect theorem

For every cell,

\[
V_a^{(Q)}j_{Q,a}-V_a^{(\vartheta)}j_{\vartheta,a}
=
V_a^{(Q)}(j_{Q,a}-j_{\vartheta,a})
+(V_a^{(Q)}-V_a^{(\vartheta)})j_{\vartheta,a}.
\]

Therefore

\[
\boxed{
\Delta_\Sigma\le\Delta_J+\Delta_V.
}
\]

The implementation also records

\[
\boxed{
\Delta_{\rm bound}
:=\max\{0,\Delta_\Sigma-(\Delta_J+\Delta_V)\}
}
\]

as `Delta_bound_margin`. For the exact theorem it is zero up to the declared numerical floor.

Consequently,

\[
\Delta_J=0,
\qquad
\Delta_V=0
\]

implies

\[
\boxed{Q_\Sigma=Q_\vartheta.}
\]

## 5. Equality of totals remains insufficient

Local current errors may cancel in the integral. Thus

\[
\boxed{
\Delta_\Sigma=0
\not\Rightarrow
\Delta_J=0.
}
\]

The reference adversarial fixture uses equal total charge with redistributed cell current and must fail the local-current gate.

## 6. Normalized profiles

The bound state additionally exposes

\[
p_{\vartheta,a}
=\frac{V_a^{(\vartheta)}j_{\vartheta,a}}{Q_\vartheta},
\qquad
p_{Q,a}
=\frac{V_a^{(Q)}j_{Q,a}}{Q_\Sigma}.
\]

Both profile sums are audited. On exact local current and measure binding,

\[
\boxed{p_{Q,a}=p_{\vartheta,a}.}
\]

This supplies the phase-current profile needed by the later `p_IDT ↔ p_Q` physical state-space gate.

## 7. Side-flux conservation gate

The state carries

\[
F_{\rm side}
\]

with

\[
\boxed{\Delta_F=|F_{\rm side}|.}
\]

Exact cross-slice conservation uses zero side flux. A declared `side_flux_tolerance` can be used for numerical candidate work.

## 8. Executable state

Schema:

```text
PNCS_NOETHER_RFC_CURRENT_STATE_V0_1
```

Raw fields:

```text
slice_id
noether_measure_id
rfc_measure_id
noether_normal_id
rfc_normal_id
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
Delta_bound_margin
side_flux_abs
p_theta
p_Q
```

Bound fields:

```text
Q_NOETHER = Q_theta
Q_RFC     = Q_Sigma
```

## 9. Transport chain

```text
noether_rfc.resolve_common_measure
  -> verify measure, normal and ordered-cell identity
  -> compute Q_theta, Q_Sigma, Delta_J, Delta_V, Delta_Sigma
  -> verify Delta_Sigma <= Delta_J + Delta_V
  -> expose normalized profiles

noether_rfc.bind_conserved_current
  -> require declared local, measure, total-charge and side-flux tolerances
  -> expose Q_NOETHER and Q_RFC

noether_rfc.reconstruct_pair
  -> reverse-audit totals and profiles
  -> reconstruct exact paired local-current state
```

## 10. Law frame and invariants

Law nodes:

```text
LAW.NOETHER.LOCAL_NORMAL_CURRENT
LAW.SOURCE.COMMON_SLICE_MEASURE
LAW.RFC.CONSERVED_LOCAL_CURRENT
```

Invariants:

```text
SOURCE.NOETHER_TOTAL_CHARGE
SOURCE.RFC_TOTAL_CHARGE
SOURCE.COMMON_MEASURE_DEFECT
SOURCE.LOCAL_CURRENT_BINDING_DEFECT
SOURCE.TOTAL_CHARGE_BINDING_DEFECT
SOURCE.CURRENT_MEASURE_BOUND_MARGIN
SOURCE.NOETHER_PROFILE_NORM
SOURCE.RFC_PROFILE_NORM
SOURCE.SIDE_FLUX_DEFECT
```

## 11. Fail-closed conditions

```text
non-empty slice / measure / normal IDs
unique ordered cell IDs
positive cell volumes
finite non-negative positive-sector currents
Q_theta > 0
Q_Sigma > 0
measure-ID agreement
normal-orientation agreement
ordered-cell agreement
exact defect inequality
Delta_measure <= measure_tolerance
Delta_local_current <= local_current_tolerance
Delta_total_charge <= total_charge_tolerance
side_flux_abs <= side_flux_tolerance
reverse bound totals and profiles must match recomputation
```

## 12. Authority boundary

All KAKU/RADICAL/OPERATOR output remains

```text
EPISTEMIC CHYBA
CANDIDATE_ONLY
runtime_execution_authority=false
canon_write_authority=false
```

The contract supplies an executable falsification surface. Physical promotion of `Q_Sigma ↔ Q_theta` remains external and requires the measured current/measure defects to satisfy the admitted evidence gate.
