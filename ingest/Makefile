# ingest: probe UDP -> /beacon_world relay.
# Laptop build by default, QNX cross-build with
#   make CC="qcc -Vgcc_ntoaarch64le"
# (QNX SDP 8.0 sourced), or plain `make` on the Pi itself.

CC      ?= cc
BUILD   := build
CFLAGS  ?= -O2 -g
CFLAGS  += -std=c11 -Wall -Wextra -I../include -Isrc -D_POSIX_C_SOURCE=200809L
PYTHON  ?= python3

ifneq (,$(findstring qcc,$(CC)))
  CFLAGS += -D_QNX_SOURCE
  LDLIBS := -lsocket
else ifeq ($(shell uname -s),QNX)
  CFLAGS += -D_QNX_SOURCE
  LDLIBS := -lsocket
else
  LDLIBS := -lrt
endif

INGEST_SRC := src/main.c src/json.c

.PHONY: all test clean
all: $(BUILD)/ingest

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/ingest: $(INGEST_SRC) src/*.h ../include/beacon.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ $(INGEST_SRC) $(LDLIBS)

test: $(BUILD)/ingest
	$(PYTHON) tests/test_ingest.py

clean:
	rm -rf $(BUILD)
