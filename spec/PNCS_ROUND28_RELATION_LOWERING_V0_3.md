# PNCS Round28 relation lowering v0.3

Status: `CLOSURE_REQUIRED_CANDIDATE / READ_ONLY / CHYBA / RUNTIME_AUTHORITY_FALSE / CANON_WRITE_FALSE`.

This candidate isolates the actual v0.28 release blocker from the unrelated 600-cell research carried by historical PR #63.

The Round28 bank uses three rich semantic relation types that are intentionally absent from the generic native-PNV opcode table: `DOUBLE_COVER_LIFT_OF`, `EXACT_KERNEL_ISOMORPHISM`, and `COORDINATE_ISOMORPHIC_TO`. The generic compiler must continue to reject them without an explicit local binding.

For Round28 only, v0.3 lowers all three relations to the already admitted `COMPOSITION` execution primitive. `COMPOSITION` preserves the ordered pair of source values. It does **not** assert equality, physical identity, or proof of the source-domain isomorphism. The original semantic `relation_type`, invariant, evidence refs, and falsification gate remain authoritative in the Round28 specification.

`IDENTITY` is explicitly rejected for `EXACT_KERNEL_ISOMORPHISM`: native PNV `IDENTITY(a,b)` computes runtime equality `a == b`; two representations related by an exact kernel isomorphism need not be identical payloads.

Admission gates:
1. exact three-relation keyset;
2. all local lowerings equal `COMPOSITION`;
3. no widening of `DEFAULT_RELATION_OPCODE`;
4. generic v0.1 compiler still fails closed for every unbound Round28 relation;
5. compiled relation plan retains the rich semantic relation type;
6. native execution result is an ordered two-value composition, never a boolean identity result;
7. v0.1 aggregate integrity validation passes;
8. READ_ONLY, CHYBA, no external effects, no runtime/canon authority;
9. dedicated CI PASS before any release-route promotion.

This candidate does not promote the 600-cell/S3 research artifacts from PR #63. Those remain independently experimental/candidate work.
