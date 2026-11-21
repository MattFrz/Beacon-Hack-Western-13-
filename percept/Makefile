CXX ?= g++
CXXFLAGS ?= -O2 -Wall -Wextra -std=c++17 -I../include
LDLIBS ?= -lpthread

.PHONY: all one clean

all: percept-head

percept-head: src/head.cpp ../include/beacon.h
	$(CXX) $(CXXFLAGS) -o $@ src/head.cpp $(LDLIBS)

one: percept-head
	./percept-head --once

clean:
	rm -f percept-head
