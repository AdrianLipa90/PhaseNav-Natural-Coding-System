# PNCS Actions Quota Dedup v0.1

Status: `CANDIDATE / STATIC WORKFLOW AUDIT COMPLETE / PRIVATE ACTIONS RUNNER QUOTA GATE`

Branch: `fix/pncs-actions-quota-dedupe-v0.1`

## Goal

Reduce repeated GitHub-hosted runner setup, remove redundant hosted conformance replays, and minimize temporary artifact storage while preserving the existing pure, self-hosted and live validation surfaces.

## v0.28 adversarial conformance

### Before

Normal hosted execution used five independent `ubuntu-latest` jobs:

1. structural authority;
2. semantic equivalence;
3. dynamics pure;
4. concurrency pure;
5. repository integrity.

Each job repeated checkout, Python setup and pytest installation.

The special post-merge conformance PR additionally ran a complete hosted `macos-latest` test mirror, a separate self-hosted full mirror, a separate self-hosted manifest candidate job, and the live `/dev/shm` gate.

### Candidate after v0.1

The same normal pure test corpus is executed in one `ubuntu-latest` job:

```text
pure-conformance
  checkout x1
  setup-python x1
  pip install pytest x1
  one complete v0.28 pytest corpus
```

The special PR path becomes:

```text
pure-conformance                ubuntu hosted
hosted-manifest-candidate       ubuntu hosted, after pure-conformance
pure-self-hosted-mirror         self-hosted
live-dev-shm                    self-hosted
```

The self-hosted pure mirror also checks deterministic manifest generation, removing the separate self-hosted manifest job.

The hosted manifest artifact contains only:

```text
MANIFEST.sha256.json
MANIFEST.sha256.json.sha256
MANIFEST.source_commit.txt
MANIFEST.source_tree.txt
```

with `retention-days: 1`.

## v1 release closure

### Before

The release closure used:

```text
release-train-pure             ubuntu-latest
manifest-and-exact-source      macos-latest
```

and uploaded the complete tracked source ZIP together with the manifest provenance for seven days.

### Candidate after v0.1

The release tests and exact-source manifest run in one `ubuntu-latest` job with one checkout and Python setup.

The candidate artifact is reduced to the four manifest/source identity files and retained for one day. The full source ZIP is omitted because the exact commit SHA, tree SHA and tracked-tree manifest already bind the source identity.

## Coverage invariant

The v0.28 pure test file set is unchanged by this branch. The v1 release-train test file set is unchanged.

Self-hosted pure validation and live `/dev/shm/ciel_noema` validation remain independent gates.

## Expected resource effect

For an ordinary v0.28 hosted run:

```text
hosted jobs:       5 -> 1
checkout/setup:    5 -> 1
pytest install:    5 -> 1
pure test files:   unchanged
```

For a v1 release closure:

```text
hosted jobs:       2 -> 1
macOS jobs:        1 -> 0
full source ZIP:   removed from artifact
artifact retention 7 days -> 1 day
```

The exact minute saving depends on runner startup, dependency installation and test duration, so this document does not assign an unmeasured percentage.

## Current validation boundary

The repository's current private GitHub-hosted runner allocation is account-quota blocked before checkout. Therefore workflow execution on the exact branch head remains an infrastructure gate.

Promotion requires a real GitHub Actions execution after runner allocation is restored, followed by confirmation that the same test corpus passes and the compact manifest artifact is produced.

## Merge policy

This branch is a workflow optimization candidate. Merge to `main` requires explicit project approval after the infrastructure gate is runnable.
