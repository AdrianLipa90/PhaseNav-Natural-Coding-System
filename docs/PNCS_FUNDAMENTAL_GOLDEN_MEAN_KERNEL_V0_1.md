# PNCS Fundamental Golden-Mean Dynamics Kernel v0.1 — post-v1 quarantine

Status: `QUARANTINE_POST_V1 / EXPERIMENTAL_IDEA / RUNTIME_OFF / NOT_IN_V1_RELEASE_GRAPH`.

The mathematical kernel introduced at commit `85f0b3bebb67248f449fa13721481f44ce6840cf` is preserved exactly for research, but it is not part of the frozen PNCS v1.0 release train.

The active v1 release contract already states that new research which is not required to close an existing release gate must be classified `EXPERIMENTAL_IDEA` and routed to `QUARANTINE_POST_V1`. The golden-mean kernel was mathematically validated, but it was not shown to be `RELEASE_BLOCKER_FIX`, `CLOSURE_REQUIRED`, or `HARDENING_REQUIRED` for v0.28. Its earlier `CANONICAL_MATHEMATICAL_KERNEL` label therefore described a valid research object at the wrong release layer.

Exact preserved payload:

- research module: `research/post_v1/fundamental_golden_mean_v01/src/phasenav_natural_code/golden_mean_dynamics_v01.py`
- original Git blob: `766d6ea951c820f5be0513eef2849cbca4d15b26`
- research test: `research/post_v1/fundamental_golden_mean_v01/tests/test_golden_mean_dynamics_v01.py`
- original test blob: `0939ef460906fffeddc8081bb3ff9227de03ddf5`
- historical import receipt remains unchanged at `provenance/receipts/PNCS_FUNDAMENTAL_GOLDEN_MEAN_IMPORT_V0_1.json`.

The active package path `src/phasenav_natural_code/golden_mean_dynamics_v01.py` and its active-suite test are intentionally absent after quarantine. Dedicated research CI still re-runs the exact mathematical test against the preserved research copy.

This reclassification does not invalidate the mathematical claims or their upstream provenance. It only corrects PNCS release authority and package membership.
