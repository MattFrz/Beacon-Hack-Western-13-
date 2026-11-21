CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -std=c11 -I../include
LDLIBS ?= -lpthread

.PHONY: all run-stub one read-frames clean

all: camd read-frames

camd: src/main.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ src/main.c $(LDLIBS)

read-frames: tools/read_frames.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ tools/read_frames.c $(LDLIBS)

run-stub: camd
	./camd --stub --hz 30

one: camd read-frames
	./camd --stub --once
	./read-frames

clean:
	rm -f camd read-frames
