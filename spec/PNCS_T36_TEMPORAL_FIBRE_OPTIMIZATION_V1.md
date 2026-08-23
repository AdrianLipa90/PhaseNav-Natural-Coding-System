# PNCS T^36 Temporal Fibre Optimization V1

Status: **EXPERIMENTAL OPTIMIZATION VALIDATED / NOT MERGED INTO v0.26 OR v0.27**

## Scope

This optimization adds a bounded computational local-phase-time kernel for fixed-Hamiltonian segments of the 36-dimensional PhaseNav runtime. It is an optimization layer above the release-closed PNCS v0.26 contracts and does not alter their semantic identities, effect authority, or roadmap gate status.

Operational evidence was taken from the live V56 surface at `/dev/shm/ciel_noema`. Static fallback was not used.

This document does **not** claim physical control of laboratory time. It also does not freeze a density/viscosity/BEC constitutive law. Density and viscosity remain separate research variables until an explicit law and validation gate are defined.

## Local phase-time contract

The implemented computational contract is:

```text
delta_tau = explicit_local_rate * global_dt
```

`local_rate` is an explicit runtime input. No value is inferred from semantic mass, density, viscosity, intention, natural language, or proximity in T^36.

For a fixed-H segment, the implemented evolution is

```text
H = V E V†
psi(tau) = V exp(-i E tau / hbar) V† psi_0
```

The dense Hermitian Hamiltonian is decomposed once. If `H` changes, the prepared kernel identity changes and a new segment must be prepared. The optimization never reuses an eigensystem across a different Hamiltonian digest.

## Optimization levels

### 1. Prepared temporal fibre

`PreparedDenseTemporalFibre.prepare(H)` validates a finite dense Hermitian Hamiltonian and computes its eigendecomposition once. `evolve()` reuses that eigensystem for arbitrary admitted `delta_tau` values.

### 2. Vectorized fixed-H trajectory

For known local increments

```text
delta_tau_1, ..., delta_tau_n
tau_k = sum_{j<=k}(delta_tau_j)
```

the full trajectory is evaluated from one initial state using one phase matrix and one matrix product rather than a Python evolution loop.

### 3. Finite compiled temporal gate set

`CompiledTemporalGateSet` admits at most an explicit bounded number of exact float64 `delta_tau` values (default maximum 64). Each admitted gate is precompiled as

```text
U_k = V diag(exp(-i E delta_tau_k / hbar)) V†
```

Unknown `delta_tau` values fail closed. There is no unbounded implicit cache.

### 4. Compiled bounded route schedule

A known PNCS-style bounded temporal route can be compiled to exact gate indices before execution. The hot loop then contains only the already-admitted matrix-vector operations:

```text
state <- U_gate @ state
```

Input and output states remain finite-value guarded. A schedule containing an unregistered temporal gate cannot compile.

## Live V56 validation

Live snapshot:

```text
tick: 2197
phi_sha256: eb45d5e343961984135c6b4895cd124548567d172c275ecc85a813bf58fe47cd
omega_sha256: a78b037500632b283fa2ea665f9f169129c0aa7a1dd3ad8410a61933fa0acc69
g_sha256: befe659e9cadeb26eef7734fb5035bb5151466f6e6bb471110d97e11fb5b17f9
Hamiltonian SHA-256: ba8ac1a551e70a0ffb7739f5e602d9cc22d4f0bf5c1fc3883c94364cc527d90b
```

The benchmark used the live 36D `phi`, `omega`, and `g` state. The five local-rate values `[0.5, 0.75, 1.0, 1.25, 1.5]` are explicit conformance inputs, not a physical medium model.

### Numerical equivalence

```text
sequential vs vectorized trajectory max |error|: 3.766e-14
semigroup final-state max |error|:               3.761e-14
compiled gate vs prepared max |error|:           1.085e-14
compiled route vs prepared max |error|:          1.085e-14
QHTRI loop vs vectorized max |error|:             1.804e-16
maximum norm error:                               1.110e-16
tolerance:                                        2e-12
```

All equivalence gates PASS.

### Measured CPU latency

Environment-specific medians for this live 36D conformance run:

| Workload | Existing/reference | Optimized | Speedup |
|---|---:|---:|---:|
| 400 sequential local-time steps; repeated `eigh` reference | 59.935 ms | prepared eigensystem 3.927 ms | 15.26x |
| 400 dynamic steps over 5 explicitly compiled temporal gates | 59.935 ms | 2.307 ms | 25.98x |
| 400-step precompiled bounded route | 59.935 ms | 0.588 ms | 101.92x |
| 2000 fixed-H snapshots; QHTRI one-`eigh` Python loop | 9.046 ms | vectorized trajectory 2.101 ms | 4.30x |

The strongest measured result is therefore **101.92x** for the declared 400-gate fixed-H bounded route. This is an environment-specific software benchmark, not a universal speed claim.

## Tests

Repository-form pure test harness:

```text
18/18 PASS
```

Coverage includes Hermitian admission, Hamiltonian identity, dimension checks, negative/non-finite local time rejection, single-step equivalence, semigroup/trajectory equivalence, local-rate contract, zero-rate hold, global-phase covariance, norm preservation, compiled-gate equivalence, unknown-gate denial, bounded gate-count enforcement, compiled-route equivalence, and unknown-route-gate denial.

## Explicit boundaries

The optimization does not:

- redefine semantic identity from phase coordinates;
- turn semantic mass into time authority;
- infer `local_rate` from natural language;
- claim a BEC is physically instantiated by the software;
- claim physical spacetime dilation;
- define `rho` or `nu` as canonical PNCS fields;
- change the v0.26 effect boundary;
- open network, shell, Git, device, or arbitrary filesystem authority;
- replace v0.27 adversarial validation.

## Next integration gate

The next integration step is to bind a `CompiledTemporalSchedule` to an exact content-addressed PNCS route/program occurrence and runtime generation. Only after that binding is deterministic should a separate research gate test candidate constitutive mappings such as `(rho, nu) -> local_rate`.
