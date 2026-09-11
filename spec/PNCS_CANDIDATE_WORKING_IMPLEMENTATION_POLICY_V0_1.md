# PNCS Candidate Working Implementation Policy v0.1

Status: `CANONICAL_PROCESS_POLICY`

Date: 2026-09-11

A component marked `CANDIDATE` is an active working implementation. It is not dead code, not archival code and not equivalent to `FAILED`.

Required interpretation:

```text
CANONICAL   = validated contract admitted to the canonical/default surface.
CANDIDATE   = executable, testable and routable working implementation whose outputs remain candidate-labelled.
QUARANTINED = isolated from normal candidate/canonical routing except explicit diagnostics.
FAILED      = known failing implementation; it may be inspected but must not be treated as a working route.
```

A `CANDIDATE` implementation MAY:

- execute when explicitly selected;
- participate in research runs, benchmarks, comparisons and candidate integration tests;
- produce receipts and derived artifacts;
- depend on canonical components;
- be consumed by another explicitly candidate-labelled component.

A `CANDIDATE` implementation MUST:

- preserve `status=CANDIDATE` in its execution/provenance receipt;
- identify its candidate ID/version;
- declare its validated domain and known unresolved domain;
- fail closed when an input leaves the validated domain unless the unresolved operation itself is the explicit experiment;
- keep promotion gates explicit;
- never silently satisfy a canonical gate merely because it executed successfully.

`CANDIDATE` therefore means `WORKING / ACTIVE / NOT_YET_PROMOTED`.

This policy does not erase historical negative results. In particular the v0.1 additive Platonic–Ramanujan `C_PR` default-runtime proposal remains `REJECTED_V0_1`; later working versions use new candidate IDs and are tested independently.

## First admitted working candidate

`600CELL_S3_ANGULAR_L0_L5_V0_1`

Implementation:

`src/phasenav_natural_code/candidate_600cell_s3_v01.py`

Properties currently validated in isolation:

```text
vertices = 120
embedding = S^3 subset R^4
graph_degree = 12
edges = 720
validated angular sectors = ell=0..5
degeneracies = 1,4,9,16,25,36
candidate angular eigenvalues = ell(ell+2) = 0,3,8,15,24,35
spherical design degree tested = 11
first tested quadrature break = degree 12
x_1^12 break = 1/4096
physical_binding = false
runtime_default_enabled = false
explicit_candidate_execution = true
```

The implementation is usable immediately through explicit `candidate_enabled=True`. Inputs with support in unresolved mirror sectors fail closed.
