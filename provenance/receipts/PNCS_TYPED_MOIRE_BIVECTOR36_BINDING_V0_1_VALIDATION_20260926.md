# PNCS Typed Moire Bivector36 Binding Validation Receipt
Date: 2026-09-26
Status: PASS_CONTRACT / NON_CANON

Normative candidate:

    spec/PNCS_TYPED_MOIRE_BIVECTOR36_BINDING_V0_1.md

Cross-repository executable implementation:

    AdrianLipa90/noema-phasenav-core
    branch calibrate/typed-t36-bivector-adapter-v0.1-20260926

Recorded executable result:

    10/10 PASS

Critical contract result:

    PNV_T36_PHASE_ANGLES_RADIANS_V1
      -> physical Bivector36

is NOT admitted merely because both representations have 36 coordinates.

The admitted candidate source basis is separately typed as

    PNV_MOIRE_RELATIVE_PHASE_MATRIX6_ROW_MAJOR_V1.

Live generic phi was explicitly tested and rejected for missing axis semantics.

canon_allowed = false
