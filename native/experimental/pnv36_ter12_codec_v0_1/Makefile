# Isolated post-v1 research witness; does not alter canonical PNCS runtime.
CC ?= gcc
CFLAGS = -O2 -no-pie -Wl,-z,relro,-z,now
.PHONY: all check run clean
all: bin/pnv-avx2 bin/pnv-codec
bin/pnv-avx2: src/pnv_native.S
	@mkdir -p bin
	$(CC) $(CFLAGS) -x assembler -o $@ $< -lm
bin/pnv-codec: codec/pnv_codec.S
	@mkdir -p bin
	$(CC) $(CFLAGS) -x assembler -o $@ $<
run: all
	./bin/pnv-avx2 pnv/A0_TO_HILBERT_NATIVE.pnv input/phase36_fixture.txt input/ter12_fixture.txt 6 7
check: all
	bash tests/test_native.sh
	bash tests/test_codec.sh
clean:
	rm -f bin/pnv-avx2 bin/pnv-codec
