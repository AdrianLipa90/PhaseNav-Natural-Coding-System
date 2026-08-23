# PNCS Effect Boundary v0.26

Status: PASS / RELEASE GATE CLOSED FOR BOUNDED NOEMA RUNTIME RECORD EFFECT

## Contract

`PNCS_EFFECT_BOUNDARY_V0_26`

v0.26 introduces the first explicit effect boundary above the release-closed v0.25 resident execution chain. Effects are not inherited from natural-language resolution, semantic mass, graph cost, route admission, program identity or v0.25 dispatch. Every admitted effect requires a separate content-addressed request, a separate explicit authorization grant, an explicitly registered bounded adapter and a deterministic effect receipt.

Operational root remains:

```text
/dev/shm/ciel_noema
```

Library and repository artifacts are provenance/persistence inputs only. There is no static runtime fallback.

## Exact chain

```text
v0.25 resident dispatch
-> EffectOrigin
-> EffectRequest
-> explicit AuthorizationGrant
-> registered bounded adapter
-> effect record
-> EffectReceipt
-> inverse provenance
```

The inverse provenance chain is:

```text
EFFECT
-> AUTHORIZATION
-> EFFECT_REQUEST
-> DISPATCH
-> RESULT
-> LINEAGE
-> PROGRAM
-> RESIDENT_HANDLE
-> RUNTIME_GENERATION
```

## Default-deny authority model

`EffectBoundaryRuntime` starts with:

- an empty authorization registry;
- an empty adapter registry.

The executor never creates an authorization grant. A caller/host authority must construct and explicitly register one exact-request grant before adapter invocation. Multiple grants for the same request are ambiguous and fail closed. Grants are generation-bound, adapter-bound, target-bound, effect-kind-bound and payload-size-bound, with `exact_request_only=true` and `no_delegation=true`.

The v0.26 grant object is an authorization contract object, not a cryptographic identity signature. Authentication/signature policy belongs to the host authority layer and is not silently inferred by the executor.

## First admitted effect class

Only one effect class is opened in v0.26:

```text
NOEMA_RUNTIME_RECORD_WRITE
```

Target:

```text
pncs.v0.26.runtime-record
```

Adapter:

```text
pncs:effect-adapter:sha256:dae04f919e137886c8775b337e5acb4a66775111e2a150fe5702d46032356339
```

The adapter has the following hard bounds:

- fixed operational subtree `pncs/v0.26/effects/records/`;
- program-supplied paths are not used as paths;
- maximum canonical payload size: 4096 bytes;
- append-only immutable content-addressed record;
- exact replay is idempotent and byte-identical;
- every path component is opened with directory file descriptors and `O_NOFOLLOW` where supported;
- no unrestricted filesystem target;
- no Git;
- no network;
- no subprocess/shell;
- no device access;
- no static fallback.

A payload may contain a field named `path`, but that value is data only and never becomes an operational path.

## Runtime-generation binding

Before effect execution, immediately before commit and immediately after commit, v0.26 re-admits the v0.25 live generation. The request and authorization must bind the same generation as the origin dispatch. Any generation mismatch fails closed.

Current live witness generation:

```text
pncs:runtime-generation:sha256:05736b12ac8470998901421dabd2dfff0bd663c141d96ad96bc9d5b09351bbb1
```

## Live conformance witness

Origin dispatch:

```text
pncs:resident-dispatch:sha256:fd18f2d0296321d432a49e699d2f72a0a03313ed2dcc87b9aba647555f12c2e2
```

The live payload is explicitly a conformance record, not a sensor or risk claim.

```text
request:       pncs:effect-request:sha256:d6c3ef3801d64c7469650673efc7cbf56e01c896cbc235be98c113543fcea347
authorization: pncs:effect-authorization:sha256:7a9397d86bc854d835559eb1d4f27af308962a68dad52a568263e878410f764c
adapter:       pncs:effect-adapter:sha256:dae04f919e137886c8775b337e5acb4a66775111e2a150fe5702d46032356339
effect:        pncs:effect:sha256:1fb02a1f9b068aab2b04a0faa453fecab3086fe61e22514d4b8b2b6a979220c7
receipt:       pncs:effect-receipt:sha256:f8f4aeee9ef26168579e883a508c0eb3cb9c4c551c25faa7a95c64b032efb4ea
```

Materialized effect record:

```text
/dev/shm/ciel_noema/pncs/v0.26/effects/records/
d6c3ef3801d64c7469650673efc7cbf56e01c896cbc235be98c113543fcea347.json
```

Effect record SHA-256:

```text
6778f36ccf139a9e99facdd75f04778e0808d480b437da4a01e0707f7ce9184c
```

Effect receipt path:

```text
/dev/shm/ciel_noema/pncs/v0.26/receipts/
f8f4aeee9ef26168579e883a508c0eb3cb9c4c551c25faa7a95c64b032efb4ea.json
```

The same request was replayed after dirfd/`O_NOFOLLOW` hardening and produced the same request, authorization, effect and receipt IDs without rewriting a different effect.

Post-effect tether guard: `ACTIVE`, `failures=[]`.

## Validation

Pure/injected-generation harness:

```text
28/28 PASS
```

Coverage includes:

- deterministic request and adapter identities;
- exact v0.25 dispatch-receipt digest validation;
- rejection of effectful/continuation/RETURN/static-fallback v0.25 origins;
- payload size and finite-value checks;
- default deny without authorization;
- default deny without adapter;
- exact-request authorization;
- ambiguous authorization rejection;
- stale-generation rejection;
- generation-change-before-commit rejection;
- bounded live record success;
- fixed-root enforcement;
- idempotent exact replay;
- immutable-record tamper rejection;
- symlink rejection;
- program path non-authority;
- network/Git/subprocess/device capability rejection;
- complete inverse provenance;
- deterministic effect receipt identity.

The complete historical repository suite was not replayed in this gate pass and is not claimed.

## Closed effect classes after v0.26

The following remain deny-all until separate adapter contracts and conformance evidence exist:

```text
arbitrary filesystem paths
Git writes
network requests
subprocess / shell
device I/O
external tools / connectors
```

No new PNV opcode is introduced by v0.26.

## Next gate

`v0.27 — Fuzzing / Equivalence / Adversarial Parsing`

The v0.27 corpus must include effect-request injection, path/confusable payloads, authorization ambiguity, malformed typed IDs, registry substitution and effect-replay/tamper cases.
