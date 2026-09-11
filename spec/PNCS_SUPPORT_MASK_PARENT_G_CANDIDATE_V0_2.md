# PNCS Support-Mask Parent-g Candidate v0.2

Status: `CANDIDATE / ACTIVE_WORKING_IMPLEMENTATION / DEFAULT_OFF`

Date: 2026-09-11

This version addresses the previously open `support_mask_parent_g_activation` gate without reviving the rejected additive `C_PR` v0.1 runtime term.

## Working rule

`CANDIDATE` means executable working implementation. It may run when explicitly admitted and may feed candidate-labelled downstream work. It is not treated as unused or archived.

The runtime wrapper:

1. takes an immutable parent v0.32 `DriveSnapshot`;
2. masks a copy of `g` with the canonical `I_12 square K_3` support;
3. executes the existing v0.32 `controlled_step` unchanged;
4. re-applies the support mask after the parent's adaptive update;
5. rebuilds the QHTRI Hamiltonian from the masked `g_next`;
6. returns the normal controlled-step outputs with an explicit `CANDIDATE` receipt.

The canonical parent implementation is not edited and the default route remains unchanged.

## Invariants under test

```text
status = CANDIDATE
candidate_executable = true
default_enabled = false
support degree = 7
outside-mask nonzeros in g_next = 0
parent snapshot mutation = forbidden
one-step target residual = must remain floating-point scale
Hamiltonian Hermiticity = must remain floating-point scale
additive C_PR v0.1 = NOT_USED / REJECTED_V0_1 preserved
```

Implementation:

`src/phasenav_natural_code/platonic_ramanujan_masked_runtime_v02.py`

Tests:

`tests/test_platonic_ramanujan_masked_runtime_v02.py`

This is a working candidate for the support-mask gate. It is not yet a canonical runtime activation and makes no physical orbital claim.
