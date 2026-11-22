/* world_shm.h: open /beacon_world for writing (shared by beacon_cmd and world_in). */
#ifndef VOICED_WORLD_SHM_H
#define VOICED_WORLD_SHM_H

#include "beacon.h"

#include <fcntl.h>
#include <stdio.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

/* Creates the object if nothing else has yet (same as guided --create). */
static beacon_world_t *world_open(const char *who)
{
    int fd = shm_open(BEACON_SHM_WORLD, O_RDWR | O_CREAT, 0666);
    if (fd == -1 || ftruncate(fd, (off_t)sizeof(beacon_world_t)) == -1) {
        fprintf(stderr, "%s: cannot open %s\n", who, BEACON_SHM_WORLD);
        return NULL;
    }
    beacon_world_t *w = mmap(NULL, sizeof(beacon_world_t), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (w == MAP_FAILED) {
        perror("mmap");
        return NULL;
    }
    if (w->abi == 0)
        w->abi = BEACON_ABI_VERSION;
    return w;
}

#endif
