#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
BIN=./bin/pnv-avx2
PNV=pnv/A0_TO_HILBERT_NATIVE.pnv
PHASE=input/phase36_fixture.txt
TRITS=input/ter12_fixture.txt
TESTS=0
PASS=0
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
ok() { TESTS=$((TESTS+1)); if "$@" > "$TMP/log" 2>&1; then PASS=$((PASS+1)); else echo "FAIL positive $TESTS"; cat "$TMP/log"; exit 1; fi; }
blocked() { TESTS=$((TESTS+1)); set +e; "$@" > "$TMP/log" 2>&1; st=$?; set -e; if [[ $st -eq 23 ]] && grep -q '^BLOCKED:' "$TMP/log"; then PASS=$((PASS+1)); else echo "FAIL expected blocked ($TESTS): exit=$st"; cat "$TMP/log"; exit 1; fi; }
# Positive, native executable must actually execute the PNV source.
ok "$BIN" "$PNV" "$PHASE" "$TRITS" 6 7
grep -q 'rooms=127 guest_room=84 branch_k=21' "$TMP/log"
grep -q 'states=17 end=1' "$TMP/log"
grep -q 'SEPARATE=4 HOLD=4 CONNECT=4' "$TMP/log"
grep -q 'PHASE36: 36 finite' "$TMP/log"
grep -q 'inverse_sq_factor=4096' "$TMP/log"
ok "$BIN" "$PNV" "$PHASE" "$TRITS" 4 3
grep -q 'rooms=31' "$TMP/log"
grep -q 'seed=3 states=8 end=1' "$TMP/log"
ok "$BIN" "$PNV" "$PHASE" "$TRITS" 8 27
grep -q 'rooms=511' "$TMP/log"
grep -q 'seed=27 states=112 end=1' "$TMP/log"
# Invalid headers, source IDs, transform maps, and wrong provenance edges must fail closed.
sed 's/^PNV 1$/PNV 2/' "$PNV" > "$TMP/invalid_header.pnv"
blocked "$BIN" "$TMP/invalid_header.pnv" "$PHASE" "$TRITS" 6 7
sed 's/RDSS_A0_AXIOM/UNREGISTERED_A0/' "$PNV" > "$TMP/invalid_source.pnv"
blocked "$BIN" "$TMP/invalid_source.pnv" "$PHASE" "$TRITS" 6 7
sed 's/RDSS_EULER_SPIN_BERRY/NOT_A_MAP/' "$PNV" > "$TMP/invalid_map.pnv"
blocked "$BIN" "$TMP/invalid_map.pnv" "$PHASE" "$TRITS" 6 7
sed 's/OP SPIN TRANSFORM A /OP SPIN TRANSFORM TER /' "$PNV" > "$TMP/invalid_edge.pnv"
blocked "$BIN" "$TMP/invalid_edge.pnv" "$PHASE" "$TRITS" 6 7
sed '/^OP HOTEL TRANSFORM/d' "$PNV" > "$TMP/missing_transform.pnv"
blocked "$BIN" "$TMP/missing_transform.pnv" "$PHASE" "$TRITS" 6 7
sed '/^ASSERT SYSTEM/d' "$PNV" > "$TMP/no_assert.pnv"
blocked "$BIN" "$TMP/no_assert.pnv" "$PHASE" "$TRITS" 6 7
sed 's/^EMIT SYSTEM$/EMIT UNSEEN/' "$PNV" > "$TMP/dangling_emit.pnv"
blocked "$BIN" "$TMP/dangling_emit.pnv" "$PHASE" "$TRITS" 6 7
sed 's/^MODE INTERNAL_EXECUTION$/MODE EFFECTFUL/' "$PNV" > "$TMP/forbidden_effect.pnv"
blocked "$BIN" "$TMP/forbidden_effect.pnv" "$PHASE" "$TRITS" 6 7
# 36 finite phase values required, no 35/37/nonfinite.
awk '{for(i=1;i<=35;i++)printf("%s ",$i); print ""}' "$PHASE" > "$TMP/phase35.txt"
blocked "$BIN" "$PNV" "$TMP/phase35.txt" "$TRITS" 6 7
cat "$PHASE" | sed 's/$/ 1.75/' > "$TMP/phase37.txt"
blocked "$BIN" "$PNV" "$TMP/phase37.txt" "$TRITS" 6 7
sed "s/^[-][0-9.]* /nan /" "$PHASE" > "$TMP/nan36.txt"
blocked "$BIN" "$PNV" "$TMP/nan36.txt" "$TRITS" 6 7
sed "s/^[-][0-9.]* /inf /" "$PHASE" > "$TMP/inf36.txt"
blocked "$BIN" "$PNV" "$TMP/inf36.txt" "$TRITS" 6 7
# 12 signed trits with explicit 0/HOLD; forbid bool, extra/missing and invalid values.
awk '{for(i=1;i<=11;i++)printf("%s ",$i); print ""}' "$TRITS" > "$TMP/trits11.txt"
blocked "$BIN" "$PNV" "$PHASE" "$TMP/trits11.txt" 6 7
sed 's/$/ 1/' "$TRITS" > "$TMP/trits13.txt"
blocked "$BIN" "$PNV" "$PHASE" "$TMP/trits13.txt" 6 7
sed 's/^\-1/2/' "$TRITS" > "$TMP/trits2.txt"
blocked "$BIN" "$PNV" "$PHASE" "$TMP/trits2.txt" 6 7
sed 's/^\-1/true/' "$TRITS" > "$TMP/trits_bool.txt"
blocked "$BIN" "$PNV" "$PHASE" "$TMP/trits_bool.txt" 6 7
# bounds, no implicit defaults, no numeric strings silently truncated.
blocked "$BIN" "$PNV" "$PHASE" "$TRITS" 9 7
blocked "$BIN" "$PNV" "$PHASE" "$TRITS" 0 7
blocked "$BIN" "$PNV" "$PHASE" "$TRITS" 6 0
blocked "$BIN" "$PNV" "$PHASE" "$TRITS" 6oops 7
blocked "$BIN" "$PNV" "$PHASE" "$TRITS" 6 7oops
# Strict parser: no trailing header suffix, no seventh ignored token, exact arities.
sed 's/^PNV 1$/PNV 1_NOT_EXACT/' "$PNV" > "$TMP/header_suffix.pnv"
blocked "$BIN" "$TMP/header_suffix.pnv" "$PHASE" "$TRITS" 6 7
sed 's/^EPISTEMIC CHYBA$/EPISTEMIC CHYBA_GARBAGE/' "$PNV" > "$TMP/epistemic_suffix.pnv"
blocked "$BIN" "$TMP/epistemic_suffix.pnv" "$PHASE" "$TRITS" 6 7
sed 's/^MODE INTERNAL_EXECUTION$/MODE INTERNAL_EXECUTION EXTRA/' "$PNV" > "$TMP/mode_suffix.pnv"
blocked "$BIN" "$TMP/mode_suffix.pnv" "$PHASE" "$TRITS" 6 7
sed 's/^OP A0 SOURCE RDSS_A0_AXIOM$/OP A0 SOURCE RDSS_A0_AXIOM EXTRA/' "$PNV" > "$TMP/source_extra.pnv"
blocked "$BIN" "$TMP/source_extra.pnv" "$PHASE" "$TRITS" 6 7
sed 's/^OP A0 SOURCE RDSS_A0_AXIOM$/OP A0 SOURCE RDSS_A0_AXIOM T1 T2 T3/' "$PNV" > "$TMP/source_extra7.pnv"
blocked "$BIN" "$TMP/source_extra7.pnv" "$PHASE" "$TRITS" 6 7
sed 's/^ASSERT SYSTEM$/ASSERT SYSTEM EXTRA/' "$PNV" > "$TMP/assert_extra.pnv"
blocked "$BIN" "$TMP/assert_extra.pnv" "$PHASE" "$TRITS" 6 7
sed 's/^-1/4294967296/' "$TRITS" > "$TMP/trit_overflow.txt"
blocked "$BIN" "$PNV" "$PHASE" "$TMP/trit_overflow.txt" 6 7
sed 's/^-1/1.0/' "$TRITS" > "$TMP/trit_decimal.txt"
blocked "$BIN" "$PNV" "$PHASE" "$TMP/trit_decimal.txt" 6 7
printf 'LOCAL_NATIVE_TESTS=%d/%d PASS\n' "$PASS" "$TESTS"

