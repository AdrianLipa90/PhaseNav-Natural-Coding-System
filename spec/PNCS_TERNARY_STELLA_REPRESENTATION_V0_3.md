# PNCS Ternary Stella Representation v0.3

Status: `CANDIDATE_ONLY / CLASSICAL / MEMORY-ONTOLOGY-TODO-DERIVED`

Source intuition: `AdrianLipa90/Memory-Ontology/todo/ternary-stella-intuition-v0.1.md`.

## Representation

A standard balanced trit is

```text
{-1, 0, +1}
```

and has exactly three states.

PNCS Stella-3 uses three balanced trits:

```text
(d0,d1,d2),  di in {-1,0,+1}
```

therefore its logical state space is exactly

```text
3^3 = 27.
```

The geometric shell decomposition is checked exhaustively:

```text
27 = 1 center + 6 axis + 12 edge + 8 corner.
```

The eight sign corners are only the all-nonzero subset. They are not treated as
eight states of one standard trit.

For coarse scalar routing, Stella-3 encodes

```text
level = d0 + 3*d1 + 9*d2 in {-13,...,+13}.
```

This supplies 27 uniformly spaced reconstruction levels.

## Measured routing benchmark

Seed: `20260925`. 30,000 random route-weight sets for each width.

| routes | sign-trit exact parity | Stella-3 exact parity | Stella-3 mean regret |
|---:|---:|---:|---:|
| 2 | 0.7504 | 0.9908 | 0.000123 |
| 4 | 0.5490 | 0.9732 | 0.000487 |
| 8 | 0.2953 | 0.9374 | 0.001237 |
| 16 | 0.1314 | 0.8702 | 0.002681 |
| 32 | 0.0644 | 0.7695 | 0.004669 |
| 64 | 0.0303 | 0.6167 | 0.007471 |

The sign-only representation is therefore rejected as a general route-ranking
replacement. Stella-3 is substantially better but is still a lossy coarse
representation: exact decision parity falls as route count grows.

No exact-equivalence claim is made.

## Serialization

A 27-symbol alphabet requires at least `ceil(log2(27)) = 5` binary bits per
symbol in fixed-width lossless binary serialization.

The implementation packs exactly five bits per Stella state. A 100,000-state
round-trip was exact:

```text
100000 states -> 62500 bytes -> 100000 identical states
```

For the weight field alone this is a theoretical fixed-width ratio of

```text
64 / 5 = 12.8x
```

against float64 weights. This is not a claim about whole Python-object memory,
whole graph memory, or native ternary hardware.

## Planner integration

`TERNARY_BALANCED` and `TERNARY_STELLA` are admitted as representation
families by PNCS Hybrid Memory Grammar and the canonical Representation
Planner. They receive no preference from their name.

The normal rule remains:

```text
behavioral equivalence contract first -> cost/Pareto selection second
```

A ternary candidate that violates the requested observable/error/horizon
contract must be rejected even if it is cheaper.

## Non-claims

- no physical quantum claim;
- no quantum advantage claim;
- no universal memory-law claim;
- no exact routing equivalence claim;
- no claim that one trit has eight states;
- no claim that a 5-bit binary serialization is native ternary hardware.
