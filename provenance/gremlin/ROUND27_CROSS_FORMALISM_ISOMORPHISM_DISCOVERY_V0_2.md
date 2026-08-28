# GREMLIN ROUND27 — Cross-Formalism Isomorphism Discovery v0.2

Status: `CANDIDATE_ONLY / CHYBA / SOURCE_AUDITED`

## Source bank

```text
TIR  26bd867c10b6f6e21b54f2a4dc7b2f49df62907a
IDT  3ac1f53af5223d16f8818dba99a63a6af2ba9498
RFC  3ebd7761ccfa70858ab8af1933c2208a82260f9d
SOH  4cf36453ee2b6d33a1f9177ca324b9ef491270be
ZPE  7caf8474852ac733d290313d9026f5ffc03f0c9a
```

## Ranked candidates

```text
XFI.01 EXACT              exact coboundary <-> trivial loop holonomy
XFI.04 EXACT              shape/scale defect triangle
XFI.02 EXACT_CONDITIONAL  TIR CP plaquette <-> Bargmann quadrilateral
XFI.03 EXACT_STRUCTURAL   SOH / horizon / Wilson spinor central sign
XFI.07 SUPPORTED_EXTENSION existing action-area-holonomy bank + Bargmann/Wilson
XFI.05 STRONG_STRUCTURAL  positive-ray quotient <-> projective quotient
XFI.06 STRONG_STRUCTURAL  scale x normalized direction fibration
XFI.08 STRONG_STRUCTURAL  mobility/orientation <-> magnitude/phase split
```

## Independent numerical falsification sanity checks

These checks were reproduced in-session from the declared equations. They verify the mathematical gates but are recorded separately from exact-branch package execution.

### XFI.01 exact coboundary closure

640 randomized closed cycles, cycle sizes 2..17:

```text
max |sum_C dV|                         1.0658141036401503e-14
max |product_C exp(i dphi) - 1|       1.0380585280245214e-14
verdict                                PASS_NUMERICAL_SANITY
```

### XFI.02 Bargmann local-rephasing invariance

100 randomized four-state complex loops with independent local phases:

```text
max |B_rephased - B_reference|         1.389512421408389e-16
verdict                                PASS_NUMERICAL_SANITY
```

### XFI.03 spinor central sign

```text
+2pi -> -1 + 1.2246467991473532e-16 i
+4pi -> +1 - 2.4492935982947064e-16 i
-2pi -> -1 - 1.2246467991473532e-16 i
-4pi -> +1 + 2.4492935982947064e-16 i
verdict                                PASS_NUMERICAL_SANITY
```

### XFI.04 shape/scale defect triangle

1400 randomized positive normalized simplex pairs, dimensions 2..15, positive scales spanning four decades:

```text
minimum (D_shape + D_scale - D_ext)    0.002760977838665135
violations                             0
verdict                                PASS_NUMERICAL_SANITY
```

## Existing supported hypothesis reused

IDT already stores `validation/gremlin/ACTION_AREA_HOLONOMY_V0_1.md` with 6/6 pairwise structural matches across Kepler swept area, symplectic action-area, Berry holonomy and memory circulation. ROUND27 treats XFI.07 as an extension of that existing receipt by adding ZPE Bargmann and field-Wilson loop observables.

## Execution boundary

Attempted exact feature-branch checkout:

```text
git clone --depth 1 --branch feat/gremlin-cross-formalism-isomorphism-bank-v0.2 ...
fatal: Could not resolve host: github.com
```

Therefore:

```text
SOURCE_AUDIT                      PASS
BANK_DESIGN                       PASS
REPOSITORY_WRITE                  PASS
NUMERICAL_FALSIFICATION_SANITY    PASS
EXACT_BRANCH_PYTEST               UNEXECUTED_ENVIRONMENT_DNS_BLOCK
GREMLIN_COMPILER_EXECUTION        UNEXECUTED_ENVIRONMENT_DNS_BLOCK
RUNTIME_EXECUTION_AUTHORITY       FALSE
CANON_WRITE_AUTHORITY             FALSE
```
