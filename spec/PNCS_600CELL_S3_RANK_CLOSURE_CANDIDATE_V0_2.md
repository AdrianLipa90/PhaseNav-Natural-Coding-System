# PNCS 600-cell / S3 Rank Closure Candidate v0.2

Status: `CANDIDATE / ACTIVE_WORKING_RESULT / DEFAULT_OFF`

Date: 2026-09-11

This surface imports the TIR candidate rank result into the PhaseNav working layer without promoting a physical orbital interpretation.

Validated sampled harmonic ranks on the 120 600-cell vertices:

```text
ell : continuum dimension -> sampled rank
0   : 1  -> 1
1   : 4  -> 4
2   : 9  -> 9
3   : 16 -> 16
4   : 25 -> 25
5   : 36 -> 36
6   : 49 -> 25
7   : 64 -> 40
```

Cumulative sampled ranks:

```text
1, 5, 14, 30, 55, 91, 116, 120
```

Working interpretation admitted by this candidate:

```text
ell <= 5 : full-dimensional S3 sampling
ell = 6  : first rank-collapse / quadrature-boundary sector
ell = 7  : completes the finite 120-dimensional sample space when accumulated with ell<=6
```

The words `event horizon`, `fractal level`, `atomic orbital identity` and `physical compactification` are not canonical consequences of this rank statement. They remain research interpretations.

This candidate may be used by executable angular-basis experiments and soliton/DNLS experiments so long as all receipts retain `status=CANDIDATE`.
