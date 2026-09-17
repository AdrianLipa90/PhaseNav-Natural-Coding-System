# PNCS Round28 relation lowering v0.4

Status: `CLOSURE_REQUIRED_CANDIDATE / READ_ONLY / CHYBA / RUNTIME_AUTHORITY_FALSE / CANON_WRITE_FALSE`.

v0.4 is the clean replacement candidate after v0.3 correctly failed CI because its workflow incorrectly required the entire historical v0.1 test file to pass even though that file contains the known missing-opcode release blocker.

This version separates three different obligations:

1. preserve the exact mathematical Round28 surface and its negative-domain gates;
2. prove the generic v0.1 compiler still rejects the three rich Round28 relations without explicit local bindings;
3. test the v0.4 local execution lowering and aggregate-integrity path independently.

The three Round28 relations remain semantically typed as `DOUBLE_COVER_LIFT_OF`, `EXACT_KERNEL_ISOMORPHISM`, and `COORDINATE_ISOMORPHIC_TO`. For execution only, all three are locally lowered to existing `COMPOSITION`. No default compiler vocabulary is widened.

`IDENTITY` is forbidden for `EXACT_KERNEL_ISOMORPHISM` because native PNV `IDENTITY(a,b)` computes payload equality. Isomorphic/kernel-equivalent representations are not required to be identical runtime payloads. `COMPOSITION` preserves the ordered relation endpoints without asserting equality.

The v0.4 gauntlet re-runs exact CP1/spin-lift, antipodal rejection, balanced half-interface, invalid-weight rejection, half-rapidity round-trip/orientation/boundary mathematics; checks expected generic-compiler failure; rejects wrong/missing/extra/IDENTITY bindings; requires preservation of semantic `relation_type`; checks native ordered-composition output and authority boundaries; and adversarially rejects aggregate-manifest tampering and missing leaf compilations.

600-cell/S3 research from historical PR #63 is outside this candidate and receives no release or canon promotion from v0.4.
