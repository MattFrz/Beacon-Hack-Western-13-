CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -std=c11 -I../include
LDLIBS ?= -lpthread

.PHONY: all run-stub one clean

all: camd

camd: src/main.c ../include/beacon.h
	$(CC) $(CFLAGS) -o $@ src/main.c $(LDLIBS)

run-stub: camd
	./camd --stub --hz 30

one: camd
	./camd --stub --once

clean:
	rm -f camd
