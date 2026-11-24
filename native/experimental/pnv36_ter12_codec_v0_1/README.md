# PhaseNav PNV/1 native AVX2 state codec and bounded executor (research v0.1)

**RDSS / PNCS / NOEMA original author: Adrian Lipa.**

This is an *isolated research module* for the PhaseNav Natural Coding System, **not a modification** of the canonical v0.20–v0.32 execution chain or a v1 release gate.

## What's implemented

- `src/pnv_native.S` — Linux x86-64 assembly executor for **one pinned PNV/1 operator graph** `pnv/A0_TO_HILBERT_NATIVE.pnv`. Executes phase36 SIMD, signed TER12, Euler/Berry, inverse-square contraction, Bombelli/Collatz and Hilbert room address mathematics on supplied fixtures. Preflight parses/validates the entire graph before invoking a transform; unknown source/operator/edge/arity fails closed.
- `codec/pnv_codec.S` — **actual binary snapshot encoder and decoder** for 36 finite, unwrapped `float64` lanes + 12 signed trits. It preserves 0/HOLD as the typed potential `0(+i,-i)`. Fixed 320-byte portable little-endian record, checksum, exact roundtrip.
- `codec/PNV36T12_CODEC_BINDING_V0_1.pnv` — PNCS source-level integration witness; not production registry-admitted or self-executing.
- `tests/` — shell-only positive/negative native conformance tests; no Python/C++ source or runtime and no GitHub Actions required.

## Build and run

```sh
make clean all
make check
./bin/pnv-avx2 pnv/A0_TO_HILBERT_NATIVE.pnv input/phase36_fixture.txt input/ter12_fixture.txt 6 7
./bin/pnv-codec encode input/phase36_fixture.txt input/ter12_fixture.txt /tmp/snapshot.pnvc
./bin/pnv-codec decode /tmp/snapshot.pnvc
```

Only Linux x86-64 with AVX2 is currently implemented. GCC/Clang plus GNU-compatible assembler are **build tools**; ELF runtime uses libc/libm for I/O/math. Underlying CPUs remain binary; signed ternary semantics are software-native and phase36 is not quantized to TER12.

**Detailed binary format and authority boundaries:** [`docs/PNV36T12_CODEC_SPEC_V0_1.md`](docs/PNV36T12_CODEC_SPEC_V0_1.md).

### Runtime status

- Local native fixture executor and codec: **verified by local tests**.
- PNCS program-unit canonical authority, live NOEMA tether, PNCore/QHTRI backend, streaming AUX and external effects: **not admitted or verified**.
- The codec stores phase36+TER12 only; it does **not** encode full 36D amplitudes, semantic graphs, winding history or phase-lift provenance.
- Does not compute SHA over live mutable AUX; cannot promote a local test into verified live CielPC execution.

Original PNCS repository training-rights policy remains applicable. This research contribution carries no assertion of a new blanket license.
