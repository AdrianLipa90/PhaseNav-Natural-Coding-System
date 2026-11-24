#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
BIN=./bin/pnv-codec
PHASE=input/phase36_fixture.txt
TRITS=input/ter12_fixture.txt
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
n=0
pass(){ n=$((n+1)); printf 'PASS %02d %s\n' "$n" "$1"; }
expect_blocked(){
  local tag=$1; shift
  local st=0
  "$@" > "$TMP/output" 2>&1 || st=$?
  if [[ "$st" -ne 23 ]]; then echo "FAIL $tag: exit=$st"; cat "$TMP/output"; exit 1; fi
  pass "$tag"
}
"$BIN" encode "$PHASE" "$TRITS" "$TMP/snapshot.pnvc" > "$TMP/log"
grep -q '^PNVC1 ENCODE OK:' "$TMP/log"
[[ $(wc -c < "$TMP/snapshot.pnvc") -eq 320 ]]
pass 'encode exactly 320 bytes'
"$BIN" decode "$TMP/snapshot.pnvc" > "$TMP/decoded"
[[ $(grep -c '^PHASE36 ' "$TMP/decoded") -eq 1 ]]
[[ $(grep -c '^TER12 ' "$TMP/decoded") -eq 1 ]]
pass 'decode known-good frame'
sed -n 's/^PHASE36 //p' "$TMP/decoded" > "$TMP/phases_decoded"
sed -n 's/^TER12 //p' "$TMP/decoded" > "$TMP/trits_decoded"
[[ $(wc -w < "$TMP/phases_decoded") -eq 36 ]]
[[ $(wc -w < "$TMP/trits_decoded") -eq 12 ]]
pass 'exact 36 and 12 lane counts'
"$BIN" encode "$TMP/phases_decoded" "$TMP/trits_decoded" "$TMP/reencoded.pnvc" > /dev/null
cmp "$TMP/snapshot.pnvc" "$TMP/reencoded.pnvc"
pass 'bitwise roundtrip encode->decode->encode'
"$BIN" encode "$PHASE" "$TRITS" "$TMP/snapshot2.pnvc" > /dev/null
cmp "$TMP/snapshot.pnvc" "$TMP/snapshot2.pnvc"
pass 'deterministic encoding'
# Mutation tests: malformed record length, wrong magic/version, checksum, domain.
head -c 319 "$TMP/snapshot.pnvc" > "$TMP/short"
expect_blocked 'truncated frame' "$BIN" decode "$TMP/short"
cp "$TMP/snapshot.pnvc" "$TMP/long"; printf '\000' >> "$TMP/long"
expect_blocked 'trailing data rejected' "$BIN" decode "$TMP/long"
cp "$TMP/snapshot.pnvc" "$TMP/bad_magic"; printf 'X' | dd of="$TMP/bad_magic" bs=1 seek=0 conv=notrunc status=none
expect_blocked 'invalid magic rejected' "$BIN" decode "$TMP/bad_magic"
cp "$TMP/snapshot.pnvc" "$TMP/bad_version"; printf '\002' | dd of="$TMP/bad_version" bs=1 seek=8 conv=notrunc status=none
expect_blocked 'invalid version rejected' "$BIN" decode "$TMP/bad_version"
cp "$TMP/snapshot.pnvc" "$TMP/bad_crc"; printf '\377' | dd of="$TMP/bad_crc" bs=1 seek=35 conv=notrunc status=none
expect_blocked 'checksum corruption rejected' "$BIN" decode "$TMP/bad_crc"
awk '{for(i=1;i<=35;i++)printf "%s ",$i;print ""}' "$PHASE" > "$TMP/35"
expect_blocked '35-phase fixture rejected' "$BIN" encode "$TMP/35" "$TRITS" "$TMP/35.pnvc"
sed 's/$/ 4/' "$PHASE" > "$TMP/37"
expect_blocked '37-phase fixture rejected' "$BIN" encode "$TMP/37" "$TRITS" "$TMP/37.pnvc"
awk '{$1="nan";print}' "$PHASE" > "$TMP/nan"
expect_blocked 'NaN phase rejected' "$BIN" encode "$TMP/nan" "$TRITS" "$TMP/nan.pnvc"
awk '{$1="inf";print}' "$PHASE" > "$TMP/inf"
expect_blocked 'Inf phase rejected' "$BIN" encode "$TMP/inf" "$TRITS" "$TMP/inf.pnvc"
awk '{for(i=1;i<=11;i++)printf "%s ",$i;print ""}' "$TRITS" > "$TMP/11"
expect_blocked '11-trit fixture rejected' "$BIN" encode "$PHASE" "$TMP/11" "$TMP/11.pnvc"
sed 's/$/ 1/' "$TRITS" > "$TMP/13"
expect_blocked '13-trit fixture rejected' "$BIN" encode "$PHASE" "$TMP/13" "$TMP/13.pnvc"
sed 's/^-1/2/' "$TRITS" > "$TMP/2"
expect_blocked 'trit 2 rejected' "$BIN" encode "$PHASE" "$TMP/2" "$TMP/2.pnvc"
sed 's/^-1/false/' "$TRITS" > "$TMP/boolean"
expect_blocked 'Boolean trit rejected' "$BIN" encode "$PHASE" "$TMP/boolean" "$TMP/boolean.pnvc"
sed 's/^-1/4294967296/' "$TRITS" > "$TMP/intover"
expect_blocked 'int32 wrapping attack rejected' "$BIN" encode "$PHASE" "$TMP/intover" "$TMP/intover.pnvc"
sed 's/^-1/1.0/' "$TRITS" > "$TMP/decimal"
expect_blocked 'trit with decimal trailing text rejected' "$BIN" encode "$PHASE" "$TMP/decimal" "$TMP/decimal.pnvc"
expect_blocked 'unknown CLI command rejected' "$BIN" xyz "$TMP/snapshot.pnvc"
# Property test: signed zero and exponents produce reversible *binary64* payload.
printf -- '-0 0 1e-100 1e100 ' > "$TMP/phase_exponents"
for i in $(seq 5 36); do printf '0 ' >> "$TMP/phase_exponents"; done
printf '\n' >> "$TMP/phase_exponents"
"$BIN" encode "$TMP/phase_exponents" "$TRITS" "$TMP/exponent.pnvc" >/dev/null
"$BIN" decode "$TMP/exponent.pnvc" > "$TMP/exponent_decoded"
sed -n 's/^PHASE36 //p' "$TMP/exponent_decoded" > "$TMP/exponent_phase"
"$BIN" encode "$TMP/exponent_phase" "$TRITS" "$TMP/exponent2.pnvc" >/dev/null
cmp "$TMP/exponent.pnvc" "$TMP/exponent2.pnvc"
pass 'signed zero and exponent IEEE-754 roundtrip'
# Encoding errors before output file creation must not synthesize an artifact.
[[ ! -f "$TMP/nan.pnvc" && ! -f "$TMP/2.pnvc" ]]
pass 'invalid semantic state creates no snapshot'
echo "NATIVE_CODEC_LOCAL_TESTS=$n/$n PASS"
