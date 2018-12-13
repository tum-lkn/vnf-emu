CC      = g++
CFLAGS  = -std=c++11 -O3
#LDFLAGS = -lfltk

all: mem_access clean

mem_access: mem_access.o
	$(CC) -o $@ $^ $(LDFLAGS)

mem_access.o: mem_access.cpp 
	$(CC) -c $(CFLAGS) $<

.PHONY: clean cleanest

clean:
	rm *.o

cleanest: clean
	rm mem_access
