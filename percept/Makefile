PYTHON ?= python3
CXX ?= g++
CXXFLAGS ?= -O2 -Wall -Wextra -std=c++17 -I../include
LDLIBS ?= -lpthread

.PHONY: all one clean test-python

all: percept-head

percept-head: src/head.cpp ../include/beacon.h
	$(CXX) $(CXXFLAGS) -o $@ src/head.cpp $(LDLIBS)

one: percept-head
	./percept-head --once

clean:
	rm -f percept-head

test-python:
	cd .. && $(PYTHON) -m unittest percept.tools.probe_frame_test percept.tools.probe_to_world_test percept.tools.tape_check_test percept.tools.calibrate_camera_test percept.tools.vo_core_test percept.tools.vo_probe_test percept.tools.merge_vo_world_test percept.tools.live_probe_test
