# PNCS v1.0 Release Train Freeze v0.1

**Purpose:** reach PNCS v1.0 without allowing new research ideas to continuously extend the release-critical path.

**Rule:** preserve ideas; do not promote them into the active release train unless they are required to fix an existing release gate.

## Active release train

### v0.28 — release closure
No feature additions. Close the already-defined exact, conformance, live, manifest, and foundation gates.

### v0.29 — release hardening
No research additions. Required work only: clean installation, reproducible packaging, deterministic replay, public API freeze, documentation freeze, live soak, no-static-fallback proof, and complete release provenance.

### v0.30 — release candidate
Only release blockers and provenance/document corrections. Produce the release-candidate build, clean-room replay, zero critical regressions, final version/changelog, and exact tag-payload/manifest match.

### v1.0
Terminal state for this release train. No additional feature is required for v1.0 once v0.30 passes.

## Idea valve
Every proposed change is classified as one of:
- `RELEASE_BLOCKER_FIX`
- `CLOSURE_REQUIRED`
- `HARDENING_REQUIRED`
- `DOC_PROVENANCE`
- `EXPERIMENTAL_IDEA`

`EXPERIMENTAL_IDEA` always produces `QUARANTINE_POST_V1`, never silent promotion.

The quarantine preserves the current research programme, including:
- Prime-Temporal Hydro;
- Radical Engine;
- 1024-ion embedding;
- PrimeFlow v0.2;
- Temporal Geometry v0.2;
- non-coboundary prime-interaction search.

These ideas may continue on experimental branches but cannot become dependencies of v1.0.

## PhaseNav invariant

```text
new idea
-> classify
-> if release-required: active gate
-> otherwise: content-addressed quarantine
-> current release gate remains unchanged
```

The invariant is: **new research never changes the identity of the currently active release gate.**

## Advancement
A stage advances only when every preregistered gate for that stage is PASS. Missing evidence is a stage blocker; it is never interpreted as a pass.
