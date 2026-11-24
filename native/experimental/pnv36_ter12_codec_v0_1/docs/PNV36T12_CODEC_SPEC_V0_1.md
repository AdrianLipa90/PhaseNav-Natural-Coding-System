# PNCS PNV36T12 — native snapshot codec v0.1 (research)

**Original mathematical framework:** Adrian Lipa (RDSS / PNCS / PhaseNav / NOEMA).

**Scope:** local native x86-64 AVX2 codec for a bounded *state snapshot*, not a new canonical PNV program serialization and not a full PNAML/PhaseNav runtime.

## 1. Types

`Phase36 = (theta_0, ..., theta_35)` contains exactly 36 finite little-endian IEEE-754 binary64 values. Phase coordinates are preserved **unwrapped**, bit-for-bit. Neither a 2π modulo nor a ternary projection is applied to the stored carrier.

`TER12 = (t_0, ..., t_11)` contains exactly 12 signed 8-bit trits from `{-1,0,+1}`. The operator interpretation is:

- `-1` : `SEPARATE`
- `0` : `HOLD( +i, -i )` with both conjugate potential branches preserved by the typed decoder rule
- `+1` : `CONNECT`

No Boolean compression, no mapping `HOLD -> false`, and no inference of a memory/semantic identity from the trit word. The default HOLD pair is the canonical typed potential; this format does **not** serialize arbitrary complex spinor amplitudes, lift history, AUX provenance, or noncanonical pair weights. Those are separate, versioned states.

## 2. Binary frame (320 bytes)

All scalar integer fields are little-endian. Byte offsets are absolute.

| Offset | Size | Type | Meaning |
|---:|---:|---|---|
| 0 | 8 | ASCII | `PNV36T12` magic |
| 8 | 4 | `uint32_le` | version `1` |
| 12 | 4 | `uint32_le` | record size `320` |
| 16 | 288 | `binary64_le[36]` | exact independent unwrapped phase lanes |
| 304 | 12 | `int8[12]` | signed TER; `0` means dual-pole HOLD |
| 316 | 4 | `uint32_le` | FNV-1a32 over bytes `[0..315]` |

FNV-1a is only an **accidental-corruption checksum**. It is not cryptographic, not an authorization witness, and not a substitute for semantic lineage or provenance. Only immutable explicit snapshots are processed; the codec never reads live `/dev/shm/ciel_noema`, watches AUX, or computes dynamic-file SHA.

## 3. Native codec operations

`pnv-codec encode phase36.txt trits12.txt output.pnvc`

- Read **exactly** 36 finite decimal phase values and **exactly** 12 decimal trits.
- Reject malformed input, extra tokens, nonfinite values, invalid ternary domain, and integer-overflow attacks.
- Use AVX2 256-bit moves for 9 groups of 4 binary64 lanes; preserve each lane's bytes.
- Serialize a frame with explicit version, exact length and checksum. It writes **only** the explicitly named output snapshot. Input validation precedes output open. This is a user-invoked CLI operation and **does not implement a PNCS v0.26 effect grant**.

`pnv-codec decode input.pnvc`

- Read exactly 320 bytes and reject truncated/extended frames; verify header, finite phases, trit domain and checksum before output.
- Print `PHASE36 ...` (17 decimal significant digits per binary64 for roundtrip) and `TER12 ...` to standard output. No destination file is created.
- `decode -> encode` must reproduce the same 320 bytes for supported frames (including negative zero and noncanonical decimal input representation).

**Exit codes:** `0` accepted, `23` blocked. The parser/executor remains a separate module `pnv-avx2` for the constrained PNV/1 graph. This codec does not import arbitrary PNV programs.

## 4. PNV linkage and limits

`codec/PNV36T12_CODEC_BINDING_V0_1.pnv` is a SOURCE/ORDER/COMPOSITION witness with canonical PNCS opcode spellings. The named external SOURCE bindings are **not** yet registered in the production PNCS registry. It is deliberately `EPISTEMIC CHYBA`, `MODE READ_ONLY` and must fail closed in a registry that lacks these names.

The companion `pnv/A0_TO_HILBERT_NATIVE.pnv` is executed only by the bounded, locally pinned x86-64 assembly subset. `A0` and `Ja Jestem` remain explicit formal postulates/source labels, not proofs of ontological necessity or physical self-awareness. Euler root branching, TER arithmetic, inverse-square depth scaling, Bombelli `(2+i)^2`, Collatz and Hilbert-room addressing are numeric local kernels; semantic identity, source event identity and external effects are distinct types.

### Existing PNCS boundaries respected

- v0.18: exact `T^36` binding with semantic source/phase identity separation.
- v0.20: only registered KAKU operators on a verified live operator registry can execute as **canonical PNCS**.
- v0.22: exact inverse lineage, not inferred from geometric coincidence.
- v0.24/v0.25: native program-unit / resident activation requires authoritative admission and a pinned generation.
- v0.26: external effects require separate grant. This codec's explicit user CLI file write is not represented as canonical PNCS execution.
- v0.31: full-state preservation until explicit observation. A 12-trit control word is not the full 36D state.

## 5. Reproducibility and release status

Local: `make clean && make check`, using GCC or Clang GNU-compatible assembler, Linux x86-64 AVX2 and standard libc/libm.

The tests cover positive execution, negative PNV parser admission, roundtrip state encoding, corruption, malformed lengths/headers, invalid trits, nonfinite values, and 64-bit overflow.

**Status: post-v1 research candidate; zero automatic release-gate authority.** No claims of CielPC tether, native PNCore/PNROM resident admission, QHTRI physical execution, CPU ternary transistors or user-library deployment.
