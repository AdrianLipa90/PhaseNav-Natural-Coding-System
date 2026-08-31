# PNCS GREMLIN Strict Admission Kernel v0.1

Status: IMPLEMENTED ON DEBUG BRANCH / CONFORMANCE PENDING

Schema: `PNCS_GREMLIN_STRICT_ADMISSION_V0_1`

## Purpose

The strict-admission kernel provides one shared fail-closed boundary for exact Python type admission and finite numeric-domain admission used by GREMLIN mathematical candidate layers.

Its responsibility is limited to input shape, input type, finiteness, and declared scalar-domain bounds. Semantic identity, candidate authority, runtime authority, and canon status remain assigned by their existing dedicated layers.

## Admission primitives

### Explicit sequence

`exact_sequence(...)` requires an explicit iterable container. `str`, `bytes`, and `bytearray` are rejected as sequence containers. Optional exact-length and minimum-length gates are evaluated before numeric admission.

### Finite real

`finite_real(...)` admits `numbers.Real` values, excludes `bool`, converts the admitted real object to Python `float`, and requires a finite result.

This closes implicit admissions such as:

```text
"1.0" -> 1.0
True -> 1.0
```

### Finite complex

`finite_complex(...)` admits `numbers.Complex` values, excludes `bool`, and requires finite real and imaginary components.

This closes implicit admissions such as:

```text
"1+2j" -> (1+2j)
```

### Numeric domains

The kernel exposes bounded scalar gates built on `finite_real(...)`:

```text
positive_real(x)       -> x > 0
nonnegative_real(x)    -> x >= 0
closed_unit_interval(x)-> 0 <= x <= 1
```

### Numeric sequences

`finite_real_sequence(...)` and `finite_complex_sequence(...)` combine explicit-container admission, optional shape constraints, and exact member admission. Every member is reported with an indexed field label on failure.

## Error contract

Every primitive accepts an `error_type` argument. GREMLIN consumers therefore retain their established public error class while sharing one admission implementation.

Current bindings:

```text
gremlin_cross_formalism_bank_v02.py
  -> CrossFormalismBankError

gremlin_cross_formalism_round28_v01.py
  -> Round28Error
```

## Cross-formalism integration

The v0.2 cross-formalism falsification helpers now route the following inputs through the kernel:

- coboundary cycle potentials,
- complex states used by Bargmann products,
- rephasing phase,
- spinor rotation angle,
- normalized-shape coordinates,
- positive scale coordinates,
- normalization tolerance.

The mathematical formulas and source-pinned candidate bank remain unchanged.

## ROUND28 integration

ROUND28 falsification helpers now route the following inputs through the kernel:

- CP1 three-vectors,
- CP1 ambiguity tolerance,
- Rodrigues and spin-lift angles,
- quaternion coordinates,
- half-interface weight and phase,
- half-interface tolerance,
- rapidity and centered-coordinate inputs.

Internal dot/cross operations consume already admitted finite vectors and therefore avoid a second coercion layer.

## Regression surface

Direct kernel corpus:

`tests/test_gremlin_strict_admission_v01.py`

Consumer-boundary corpus:

`tests/test_gremlin_strict_admission_consumers_v01.py`

The adversarial cases include boolean-as-number, numeric strings, complex strings, string-as-sequence containers, non-finite values, malformed vector dimensions, and invalid tolerance/scale domains.

Both corpora are part of the GREMLIN authoring workflow and v1 release closure. Hosted conformance remains pending until a GitHub Actions runner executes the test steps.
