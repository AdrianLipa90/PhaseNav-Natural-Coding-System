# PNCS Tau Liminal File Codec v0.1

Status: ARCHITECTURE CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false

## Core contract

The PNCS file carrier uses exact scalar tau modulation as the content channel:

```text
Delta_tau(b) = 1 + b/257,  b in {0..255}
```

A local reference interval gives the affine-invariant ratio:

```text
r_b = Delta_tau_data / Delta_tau_reference = 1 + b/257
```

Under `tau' = a*tau + c`, with `a > 0`, the ratio is invariant. Laboratory wall-clock is realization evidence and is excluded from semantic content identity.

## TAU FRAME

```text
PILOT_L
  -> exact scalar tau content symbols
  -> PILOT_R
  -> whole-lane T36 witness
```

The reference implementation uses one T36 witness per block. The 36 phase coordinates carry a 32-byte BLAKE2b-256 block commitment plus a 4-byte block index as one whole lane.

## Identity separation

```text
FILE_ID != CONTENT_COMMITMENT != CHECKPOINT_OBJECT_ID
```

`FILE_ID` is genesis-anchored logical identity. `CONTENT_COMMITMENT` identifies current content. `CHECKPOINT_OBJECT_ID` identifies one State Memory generation and its lineage.

## Liminal/State composition

```text
State checkpoint S_n
  -> Liminal segment Lambda_n(tau)
  -> consolidation
  -> State checkpoint S_(n+1)
```

An uncommitted liminal tail is excluded from recovery. M8 identity continuity remains protected and requires explicit identity authority for mutation.

## GREMLIN isomorphic codec compilation

GREMLIN consumes the shared invariant across these domains:

```text
PNCS TAU FRAME
  <-> PNCS T36 WITNESS
  <-> PNV-State-Memory LIMINAL SEGMENT
  <-> BioOS PNLF FILE
  <-> PNH5 compatibility view
```

The existing relational-isomorphism compiler materializes content-addressed KAKU candidates, one RADICAL dependency graph, deterministic OPERATORS and a PNV conformance program. `ISOMORPHIC_TO`, `BINDS` and `MAPS_TO` lower to the deterministic `COMPOSITION` subset.

GREMLIN output remains `CANDIDATE_ONLY`; runtime execution authority and canon write authority remain false. Candidate conformance execution is READ_ONLY.

## Tested candidate gates

The development receipts preceding repository integration record:

```text
PNLF_LIMINAL_STATE_TEST_RECEIPT_V0_1       10/10 PASS
PNLF_ANALOG_ROBUSTNESS_RECEIPT_V0_2         9/9 PASS
PNLF_TAU_SELF_CALIBRATION_RECEIPT_V0_3      5/5 PASS
PNLF_BLOCK_FILE_E2E_RECEIPT_V0_4            6/6 PASS
TOTAL                                      30/30 PASS
```

Evidence status: local executable candidate. Physical carrier validation is a separate gate.
