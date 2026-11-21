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

.PHONY: preview
preview: build/telemd-preview

build/telemd-preview: telemd.c preview.c preview.h ../include/beacon.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) -DBEACON_PREVIEW telemd.c preview.c -o $@ $(LDLIBS) -ljpeg

build/telemd: telemd.c ../include/beacon.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) telemd.c -o $@ $(LDLIBS)
