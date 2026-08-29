# libpnv36 v0.1

`libpnv36` is the native CPU execution layer for exact 36D PhaseNav states.
PhaseNav remains the semantic authority; this crate lowers selected numerical
primitives into a compact Rust representation suitable for SIMD execution.

## v0.1 scope

- `Phi36`: `#[repr(C, align(32))]`, exactly 36 finite `f64` coordinates.
- Exact object size: 288 bytes = 9 AVX2-width blocks of four `f64` values.
- Strict wrapped radial delta and signed torus-turn delta.
- Strict L2 and angular-distance primitives.
- Runtime AVX2 dispatch on x86_64 for lane-local squaring.
- Canonical scalar-order reduction after SIMD multiplication.
- Stable nearest-k reference implementation with index tie-breaking.
- Fail-loud rejection of non-finite coordinates and invalid `k`.

## Numerical modes

The first implementation exposes only the strict path. Algebraic/reassociated
floating-point kernels are reserved for a later `Fast36` layer and require a
separate equivalence/fitness gate before use in any authoritative runtime path.

## Live runtime contract

Integration with NOEMA is through the live `/dev/shm/ciel_noema` surface. The
Rust layer consumes or produces exact 36D state blocks only after the existing
NOEMA admission/tether contract has established an active runtime.

## Validation status

Source and unit tests are present. The current ChatGPT execution environment
used to create v0.1 had no `rustc`/`cargo` binary, therefore local compilation
status is **PENDING** rather than inferred. Promotion requires compilation plus
cross-language equivalence tests against the canonical PhaseNav batch kernels.

## Next gate

1. Compile with Rust 1.98+.
2. Compare `Phi36` distance/delta outputs against the canonical Python/NumPy
   kernels over deterministic and randomized corpora.
3. Require exact/declared-tolerance equivalence per primitive.
4. Benchmark scalar vs AVX2 paths.
5. Only then expose the crate through the NOEMA runtime adapter.
