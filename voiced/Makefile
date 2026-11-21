# voiced: laptop build by default; on the Pi just `make` (QNX detected).
#   build/beacon_cmd   typed commands -> intent (stand-in for the mic)
#   build/world_in     laptop camera (percept probe over UDP) -> /beacon_world

CC      ?= cc
BUILD   := build
CFLAGS  ?= -O2 -g
CFLAGS  += -std=c11 -Wall -Wextra -I../include -Itools -D_POSIX_C_SOURCE=200809L

ifneq (,$(findstring qcc,$(CC)))
  CFLAGS += -D_QNX_SOURCE
  LDLIBS := -lsocket
else ifeq ($(shell uname -s),QNX)
  CFLAGS += -D_QNX_SOURCE
  LDLIBS := -lsocket
else
  LDLIBS := -lrt
endif

.PHONY: all clean
all: $(BUILD)/beacon_cmd $(BUILD)/world_in

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/beacon_cmd: tools/beacon_cmd.c tools/world_shm.h ../include/beacon.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ tools/beacon_cmd.c $(LDLIBS)

$(BUILD)/world_in: tools/world_in.c tools/world_shm.h ../include/beacon.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ tools/world_in.c $(LDLIBS)

clean:
	rm -rf $(BUILD)
