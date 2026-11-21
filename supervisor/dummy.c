#include "beacon.h"
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>

/* Standalone laptop fixture. Publish the same heartbeat field as guided. */
int main(void)
{
    const char *name = getenv("BEACON_SUPERVISOR_WORLD");
    if (!name)
        name = BEACON_SHM_WORLD;
    int fd = shm_open(name, O_CREAT | O_RDWR, 0600);
    if (fd < 0 || ftruncate(fd, sizeof(beacon_world_t)) < 0) {
        perror("prepare dummy world");
        return 1;
    }
    beacon_world_t *world = mmap(NULL, sizeof(*world), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (world == MAP_FAILED) { perror("map dummy world"); return 1; }
    if (world->abi != 0 && world->abi != BEACON_ABI_VERSION)
        return 1;
    world->abi = BEACON_ABI_VERSION;
    const struct timespec interval = {.tv_nsec = BEACON_SUP_TICK_NS / 2};
    for (;;) {
        beacon_seq_write_begin(&world->seq_guided);
        world->guided.hb_guided_ns = beacon_now_ns();
        beacon_seq_write_end(&world->seq_guided);
        nanosleep(&interval, NULL);
    }
}
