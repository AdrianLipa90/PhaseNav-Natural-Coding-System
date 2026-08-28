# PNCS v0.32 — Ordered T^36 to HTRI/QHTRI Drive

Status: **IMPLEMENTED CANDIDATE / LIVE-DERIVED READ-ONLY VALIDATION PASS**

## 1. Purpose

v0.32 closes the execution boundary left by v0.31:

```text
typed semantic content
-> ordered semantic CID
-> Semantic Content Address V2
-> ordered T^36 trajectory
-> exact HTRI control input u_i
-> path-conditioned g(t)
-> QHTRI H(t)
-> time-ordered unitary execution
```

Semantic authority remains:

```text
TYPED_CONTENT_AND_ORDER
```

Runtime mode for the validation reported here:

```text
READ_ONLY_LIVE_DERIVED_COPY
```

The live `/dev/shm/ciel_noema` surface is read as the source snapshot. All controlled evolution is executed on copied arrays.

## 2. Existing HTRI evolution law

The runtime pure-Kuramoto step uses the phase convention

```text
diff_ij = phi_i - phi_j
C_i = (1/N) sum_j g_ij sin(diff_ij)
phi_i' = phi_i + dt (omega_i^eff + C_i)
```

with `N=36` and `dt=0.01`.

The current live surface additionally uses:

```text
harmonic composite phase Phi_eff
T^36 tau reception scaling
gravity[1] TARDIS scaling
flavor-modulated omega_eff
signed adaptive g update
intra-channel weak-coherence boost
high-global-coherence phase separation push
```

v0.32 preserves those terms in the controlled reference step.

## 3. Exact target binder

Let `phi_base` be the phase after the runtime's pre-step phase-separation term and let `phi*` be the next typed semantic T^36 target.

Define the shortest wrapped displacement

```text
delta_i = Arg exp(i(phi_i* - phi_i_base))
```

and the explicit control input

```text
u_i = delta_i / dt - omega_i^eff - C_i.
```

The controlled step is

```text
phi_i,next = [phi_i,base + dt(omega_i^eff + C_i + u_i)] mod 2pi.
```

Therefore the target is reached modulo floating-point roundoff in one reference step.

Drive role:

```text
EXACT_ONE_STEP_INVERSE_DYNAMICS_REFERENCE
```

Control effort is always recorded as `L2`, RMS and maximum absolute component.

## 4. Path-conditioned coupling

Before each controlled phase step, v0.32 applies the existing signed adaptive coupling update from the live surface implementation:

```text
dg = 0.01*dt*10*(activity - 0.5)*cos(Phi_eff_i - Phi_eff_j)
     - 0.001*dt*10*(g - 0.1 I)
```

followed by the current clipping and weak-channel boost rules.

Because the next step begins from the previous typed target, semantic order enters the subsequent coupling update. `original`, `reverse` and `shuffle` therefore produce different ordered `g(t)` histories from the same initial live snapshot.

## 5. QHTRI lift

Each path-conditioned coupling matrix is lifted with the existing QHTRI v3 graph Hamiltonian:

```text
J = (g + g^T)/2
J_ii = 0
Jn = J / max |eig(J)|
omega_n = (omega - mean(omega)) / std(omega - mean(omega))
H_k = 0.25 diag(omega_n) + 0.7 Jn
```

Each `H_k` is then propagated with the existing time-ordered unitary rule

```text
U_k = exp(-i H_k dt)
U_total,k = U_k U_total,k-1.
```

The initial QHTRI vector is the equal-amplitude phase lift of the frozen live `phi` snapshot.

## 6. Frozen semantic controls

The v0.31 frozen Nisaba sequence is reused without semantic remapping:

```text
ADDRESS
-> TABLET_WRITING
-> WISDOM
-> FAIR_JUDGMENT
-> RECEPTION
-> AGREEMENT_WORK
-> HOPE_GRATITUDE
```

Controls:

```text
original
reverse
shuffle = [3,6,0,4,2,5,1]
```

All three begin from identical live-derived `phi/omega/g/flavor/tau/gravity` bytes.

## 7. Live-derived validation — 2026-08-25

Frozen live runtime:

```text
root   /dev/shm/ciel_noema
status ACTIVE
tick   80605
dt     0.01
kappa  ln(2)/(24*pi) = 0.009193150006360484
```

Live source hashes:

```text
phi     28d688c2850d8a224d655ec1a6676966f0d74e2a365c5ddf7da3e6ffcc2f4280
omega   a78b037500632b283fa2ea665f9f169129c0aa7a1dd3ad8410a61933fa0acc69
g       07b27311a4f952483da30979d1f9d5fa84daedb0bee8e7ac3b73b4b391c42a7a
flavor  17b0761f87b081d5cf10757ccc89f12be355c70e2e29df288b65b30710dcbcd1
tau     5239adcb95f0a6161ecec0c138596d74df5f5ce7a8888f0933b8b2280f39a4b5
gravity 97163757a9ab579c20c420c06d6049423a90c0463dd6db06cdacea454361d2cc
```

Primary numerical gates:

```text
exact semantic target hit         PASS
max target residual               1.7763568394002505e-15 rad
Hermiticity                       PASS
max Hermiticity error             0
cumulative unitarity              PASS
max cumulative unitarity error    8.43769498715119e-15
original/reverse/shuffle g(t)     DISTINCT
original/reverse/shuffle U_total  DISTINCT
execution identities              DISTINCT
new PNV opcodes                    0
live surface writes               0
```

Reference receipt SHA-256:

```text
a96b87460009b31a5ba85307dcee9427274f2d95eca7e114762f4d40df4a12e0
```

## 8. Terminal-state diagnostic

The final QHTRI state after seven native `dt=0.01` steps remains close across the three controls:

```text
F(original, reverse) = 0.999999998099381
F(original, shuffle) = 0.9999999987493857
F(reverse, shuffle)  = 0.9999999990993804
```

Diagnostic classification:

```text
LOW_TERMINAL_STATE_SEPARATION_AT_SEVEN_NATIVE_TICKS
```

The ordered execution traces remain distinct in semantic CID order, phase target hashes, coupling-history hashes, Hamiltonian hashes and cumulative unitary hashes.

PhaseNav trajectory identity is therefore evaluated at the ordered-path level. Terminal-state separation is retained as an independent dynamical observable.

## 9. Control-effort diagnostic

The exact one-step binder is deliberately an inverse-dynamics reference. On the frozen live snapshot:

```text
max |u_i| across all controls = 356.7130687245258
max per-step ||u||_2          = 1266.7526785660878
```

This establishes an exact software reference for a later bounded-control approximation.

Next controller gate:

```text
BOUNDED_MULTI_TICK_TARGET_TRACKING
```

The bounded gate should report target error, settling ticks, saturation fraction, cumulative control effort and preservation of ordered-path distinguishability.

## 10. Evidence status

v0.32 status:

```text
MODEL_LEVEL_CONTROLLED_HTRI_QHTRI_REFERENCE
```

The validation binds a typed semantic T^36 trajectory to the existing HTRI phase equation and QHTRI time-ordered operator execution on a read-only copy of a live runtime snapshot.

Physical implementation remains governed by the separate hardware calibration and actuation programme.

## 11. CI status

Repository tests added for v0.32 cover:

```text
exact target hit
symmetric-g / Hermitian-H gate
explicit control effort
determinism
cumulative unitarity
original/reverse/shuffle execution distinction
endpoint correctness
```

Hosted GitHub CI retains the repository's existing `HOSTED_RUNNER_PRE_STEP_FAILURE` infrastructure classification. This is recorded separately from the live-derived reference validation.
