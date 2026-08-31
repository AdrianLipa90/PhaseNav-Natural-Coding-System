# PNCS PNLF Orbital Memory Admission v0.1

Status: `IMPLEMENTED_ON_DEBUG_BRANCH / HOSTED_CONFORMANCE_PENDING`

## 1. Scope

This contract binds the public admission surface of `pnlf_orbital_memory_v01.py` while preserving the existing PNLF schemas, checkpoint bodies, liminal revision bodies and deterministic identity construction.

The covered structures are:

```text
OrbitalState
PNLFHeader
StateMemoryCheckpoint
LiminalSegmentRevision
build_state_checkpoint
open_liminal_segment
advance_liminal_segment
admit_liminal_segment
reject_liminal_segment
logical_address
tau_frame
```

The migration is an admission hardening layer. Existing legal canonical values retain their established serialization and content-addressed identities.

## 2. Finite real coordinates

PNLF scalar coordinates admitted through `_finite`, `_non_negative` and `_positive` require an actual `numbers.Real` value with `bool` excluded.

The value must remain finite after representation as Python `float`.

This applies transitively to orbital coordinates and proper-time coordinates including:

```text
r_phase
phase
E_bind
L_phase
semantic_mass
orbit_period
winding
proper_time
memory_affinity
tau
tau_start
tau_cursor
tau_end
```

Numeric strings, bool values and arbitrary objects exposing `__float__` do not enter the PNLF numeric state.

Finite-conversion overflow fails closed at the admission boundary.

## 3. Text, digest and checkpoint identities

Text fields admitted through `_require_text` require string type and non-empty text after the existing whitespace normalization.

SHA-256 commitments admitted through `_digest` require exact string type and the existing lowercase 64-hex format.

Checkpoint identities admitted through `_checkpoint_id` require exact string type and the existing form

```text
pnlf:checkpoint:sha256:<64 lowercase hex digits>
```

`orbital_band` and liminal `resolution_state` additionally require direct string identity before membership/state normalization is evaluated.

## 4. M-layer admission

Active M-layer collections use an explicit `list` or `tuple` container.

Each member is an exact non-empty string and must belong to the established PNLF M-layer set.

The existing deterministic representation remains:

```text
sorted(unique(active_m_layers))
```

Thus legal duplicate/order variants retain one deterministic tuple representation.

## 5. Canonical JSON mapping identity

Canonical PNLF JSON preserves mapping keys as exact strings.

Nested mappings are recursively admitted with string keys before JSON serialization. A non-string key cannot manufacture a provenance key through Python `str(...)` representation.

The existing canonical serialization parameters remain:

```text
sort_keys = true
separators = (",", ":")
ensure_ascii = false
allow_nan = false
```

## 6. Checkpoint identity stability

`build_state_checkpoint` first admits `tau` through the shared proper-time scalar gate and compares `orbital_state.proper_time` against that admitted value.

For a legal canonical checkpoint, this migration preserves the previous checkpoint body and therefore preserves both:

```text
state_commitment
checkpoint_object_id
```

The regression fixture binds this invariant to:

```text
pnlf:checkpoint:sha256:122beb86d43106392551678d761b289014f1daa842738cc30cd9e1d690591d25
```

for the declared test fixture.

## 7. Liminal state admission

`resolution_state` requires string type before the existing uppercase state mapping.

The established state set remains:

```text
OPEN
ADMITTED
REJECTED
```

All existing liminal state-transition, witness, pilot and commitment gates remain unchanged.

## 8. Validation gates

The adversarial regression corpus verifies:

1. bool, numeric-string and arbitrary float-coercible scalar rejection;
2. finite-conversion overflow rejection;
3. exact orbital-band string identity;
4. exact text and SHA-256 identity typing;
5. explicit M-layer container admission and exact member typing;
6. canonical JSON string-key identity;
7. public proper-time address admission;
8. unchanged canonical checkpoint object identity for legal input;
9. unchanged deterministic M-layer ordering/deduplication for legal input.

Reference implementation:
`src/phasenav_natural_code/pnlf_orbital_memory_v01.py`

Reference regressions:
`tests/test_pnlf_orbital_memory_v01.py`
`tests/test_pnlf_orbital_memory_admission_v01.py`

Authority remains governed by the existing PNLF receipt fields and state-transition contracts.