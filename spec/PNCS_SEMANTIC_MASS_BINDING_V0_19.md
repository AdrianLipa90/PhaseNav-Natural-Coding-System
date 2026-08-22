# PNCS v0.19 — Semantic Mass Binding

## Scope

v0.19 binds the existing `Kaku.semantic_mass` field to the validated PhaseNav runtime scalar:

```text
m_k = κ * (1 + α_M * k) + (L4/L3) * R_k
```

where `R_k` is the 36D Kuramoto-style order parameter of an already bound exact `T^36` realization.

## Source contract

The validated source is the Library `pnv_runtime.py` object with SHA-256:

```text
0b4df86cd01db313ea46ebac0eceee9cf6df0673391edd1a3fb2667c30464a32
```

The source fixes:

```text
κ       = ln(2)/(24π)
L3      = 7
L4      = 2
L5      = 5
α_M     = 1 / ((L3*L4)^2 - L3^2 - L4*L5 + L4^2*κ)
L_RATIO = L4/L3
```

and computes:

```text
R_k = sqrt((Σ sin(phi_i))^2 + (Σ cos(phi_i))^2) / 36
m_k = round(κ*(1 + α_M*k) + L_RATIO*R_k, 10)
```

The v0.19 reference implementation preserves the runtime trigonometric evaluator so reference parity is exact for the validated source contract.

## Explicit phase index

PNCS semantic content IDs are not numeric PhaseNav state IDs. v0.19 therefore does not hash, truncate, parse, or otherwise infer `k` from a content ID.

`phase_index` is an explicit positive integer provenance input:

```text
phase_index ∈ Z, phase_index >= 1
```

Invalid or missing indices fail closed.

## Identity separation

v0.19 maintains separate identities for:

```text
semantic content ID
exact 36D realization ID
semantic-mass realization ID
semantic-mass provenance binding ID
```

Mass equality is not semantic equivalence authority. Two distinct content IDs may have the same exact mass value and remain distinct semantic objects.

## KAKU materialization

A KAKU may be materialized with the computed mass only when:

- the exact v0.18 realization is valid;
- the phase index is explicit and positive;
- the KAKU vector basis matches the realization basis;
- the full 36D phase is retained;
- the semantic mass recomputes exactly under the frozen mass contract.

`verify_kaku_mass` rejects mass, phase, or basis drift.

## Epistemic and execution scope

The binding remains under `CHYBA` with `canon_allowed=false`. It does not enable generic natural-language execution and adds no PNV opcode.

The scalar is the current PhaseNav project semantic-mass implementation quantity. v0.19 does not identify it with physical mass.
