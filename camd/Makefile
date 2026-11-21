CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -std=c11 -I../include
LDLIBS ?= -lpthread

.PHONY: all run-stub one read-frames deadline-test test-frame-id-seed clean

all: camd read-frames deadline-test

camd: src/main.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ src/main.c $(LDLIBS)

read-frames: tools/read_frames.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ tools/read_frames.c $(LDLIBS)

deadline-test: tools/deadline_test.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ tools/deadline_test.c $(LDLIBS)

test-frame-id-seed: camd read-frames
	python3 tools/test_frame_id_seed.py

run-stub: camd
	./camd --stub --hz 30

one: camd read-frames
	./camd --stub --once
	./read-frames

clean:
	rm -f camd read-frames deadline-test
