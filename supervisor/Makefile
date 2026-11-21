CC ?= cc
CPPFLAGS += -I../include -D_POSIX_C_SOURCE=200809L
CFLAGS += -std=c11 -Wall -Wextra

.PHONY: all test
all: build/supervisor build/dummy

build:
	mkdir -p $@

build/supervisor: supervisor.c ../include/beacon.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $< -o $@

build/dummy: dummy.c ../include/beacon.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $< -o $@

test: all
	python3 test_restart.py
