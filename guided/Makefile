# guided: laptop build by default, QNX cross-build with
#   make CC="qcc -Vgcc_ntoaarch64le"
# (QNX SDP 8.0 sourced), or plain `make` on the Pi itself.

CC      ?= cc
BUILD   := build
CFLAGS  ?= -O2 -g
CFLAGS  += -std=c11 -Wall -Wextra -I../include -Isrc -D_POSIX_C_SOURCE=200809L

ifneq (,$(findstring qcc,$(CC)))
  CFLAGS += -D_QNX_SOURCE
  LDLIBS := -lm
else ifeq ($(shell uname -s),QNX)
  CFLAGS += -D_QNX_SOURCE
  LDLIBS := -lm
else
  LDLIBS := -lpthread -lm -lrt
endif

GUIDED_SRC := src/main.c src/law.c src/audio.c src/platform.c

.PHONY: all test clean
all: $(BUILD)/guided $(BUILD)/fakeworld $(BUILD)/test_law

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/guided: $(GUIDED_SRC) src/*.h ../include/beacon.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ $(GUIDED_SRC) $(LDLIBS)

$(BUILD)/fakeworld: tools/fakeworld.c ../include/beacon.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ tools/fakeworld.c $(LDLIBS)

$(BUILD)/test_law: tests/test_law.c src/law.c src/law.h ../include/beacon.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ tests/test_law.c src/law.c $(LDLIBS)

test: $(BUILD)/test_law
	./$(BUILD)/test_law

clean:
	rm -rf $(BUILD)
