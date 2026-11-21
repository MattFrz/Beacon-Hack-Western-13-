CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -std=c11 -I../include
LDLIBS ?= -lpthread

.PHONY: all run-stub one read-frames dump-frame deadline-test test-frame-id-seed clean

all: camd read-frames dump-frame deadline-test

camd: src/main.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ src/main.c $(LDLIBS)

read-frames: tools/read_frames.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ tools/read_frames.c $(LDLIBS)

dump-frame: tools/dump_frame.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ tools/dump_frame.c $(LDLIBS)

deadline-test: tools/deadline_test.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ tools/deadline_test.c $(LDLIBS)

layout-probe: tools/layout_probe.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ tools/layout_probe.c

test-frame-id-seed: camd read-frames layout-probe
	python3 tools/test_frame_id_seed.py

run-stub: camd
	./camd --stub --hz 30

one: camd read-frames
	./camd --stub --once
	./read-frames

clean:
	rm -f camd read-frames dump-frame deadline-test layout-probe
