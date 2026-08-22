# PNCS 36D Basis v0.1

Status: STRUCTURE_DEFINED / SEMANTIC_AXES_PENDING_CANON

The semantic names and exact physical/relational interpretation of the 36 axes are intentionally not invented in this document.

Canonical vector:

    v = (v_0, v_1, ..., v_35) in R^36

Phase representation MAY be bound to T^36 once the canonical PhaseNav representation contract is attached.

For v0.1 every vector MUST:
- have exactly 36 components,
- contain finite float64-compatible values,
- preserve coordinate order,
- carry an explicit basis_id,
- never be truncated to 11D or any other size.

Next canonization gate:
- define axis identities,
- define normalization/domain per axis,
- define which axes are semantic, phase, relational, metric, or derived,
- define transformation from semantic vector to PhaseNav phase representation,
- define invariants under composition.
