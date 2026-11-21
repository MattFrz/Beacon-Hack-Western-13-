CC ?= cc
CPPFLAGS += -I../include -D_POSIX_C_SOURCE=200809L
CFLAGS += -std=c11 -Wall -Wextra
ifeq ($(shell uname -s),Linux)
LDLIBS += -lrt
endif
ifneq (,$(filter QNX,$(shell uname -s))$(findstring qcc,$(CC)))
LDLIBS += -lsocket
endif

all: build/telemd

build/telemd: telemd.c ../include/beacon.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) telemd.c -o $@ $(LDLIBS)
