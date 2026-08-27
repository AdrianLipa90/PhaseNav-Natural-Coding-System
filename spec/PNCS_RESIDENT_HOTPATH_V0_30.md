# PNCS Resident Hot Path v0.30

Status: IMPLEMENTED CANDIDATE / CHYBA / canon_allowed=false

## Purpose

v0.30 preserves the v0.25 full resident admission as the authority-producing cold path and adds a bounded hot-dispatch token for repeated in-process control transitions.

The optimization target comes from the BioOS/Linux same-host benchmark: the direct resident primitive was measured at approximately 1.17 us for the 288-byte reference payload while a full Terminal36D semantic/evidence dispatch was approximately 38.88 us. The design goal is therefore to preserve the evidence spine while removing repeated reconstruction and hashing of authority artifacts from every resident dispatch.

## Flow

```text
v0.25 LOAD
  -> v0.25 FULL ADMIT
  -> v0.30 ISSUE HOT TOKEN
  -> HOT GUARD
  -> v0.20/v0.22 kernel
  -> HOT GUARD
  -> exact ResidentDispatchReceipt
```

A hot token can only be issued from a successful v0.25 `ResidentAdmission`.

## Token binding

The token binds resident handle/program/control-definition identity, the full v0.25 admission and generation payload, plus file identity for resident program, handle, active pointer, session startpoint, current memory, fast-admission seal and live operator registry.

File identity is:

```text
(st_dev, st_ino, st_size, st_mtime_ns, st_ctime_ns)
```

The exact operator-registry SHA remains part of the generation fully admitted before token issuance. Hot dispatch does not re-hash the full registry every call; any observed authority-file identity change invalidates the token and requires a new full admission.

## Per-dispatch guard

Every hot dispatch guards both before and after kernel execution. It requires ACTIVE binding, unchanged authority-file identities, the same handle/generation active pointer, ACTIVE/no-fallback fast seal, exact CURRENT/startpoint/AC/ethics generation fields, matching live producer PIDs, fresh heartbeats, active AC ethics hardpath, and the required Unix socket when enabled.

Any mismatch is an immediate failure. There is no silent token refresh and no static fallback.

## Evidence compatibility

Kernel output still passes the exact v0.20 execution-receipt validator and exact v0.22 inverse-lineage validator used by v0.25. Successful dispatch emits the existing content-addressed `ResidentDispatchReceipt` structure while keeping external effects, continuation execution, return execution and static fallback closed.

## Evidence boundary

This implementation opens an optimization candidate. It does not establish a performance gain until the v0.30 path is benchmarked against v0.25 on the same live generation and negative invalidation tests pass.

Promotion gate:

```text
functional equivalence PASS
AND generation-change invalidation PASS
AND program/handle/operator tamper invalidation PASS
AND same-host latency benchmark PASS
```
