#include "beacon.h"
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;
static volatile sig_atomic_t stopping;

static void stop(int signal_number)
{
    (void)signal_number;
    stopping = 1;
}

/* A standalone guided --create can still be creating the region at startup. */
static const beacon_world_t *open_world(const char *name)
{
    int fd = shm_open(name, O_RDONLY, 0);
    if (fd < 0)
        return MAP_FAILED;
    struct stat st;
    void *map = MAP_FAILED;
    if (fstat(fd, &st) == 0 && st.st_size >= (off_t)sizeof(beacon_world_t))
        map = mmap(NULL, sizeof(beacon_world_t), PROT_READ, MAP_SHARED, fd, 0);
    close(fd);
    return map;
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "Usage: supervisor CHILD [ARG ...]\n");
        return 2;
    }
    struct sigaction handler = {.sa_handler = stop};
    sigemptyset(&handler.sa_mask);
    if (sigaction(SIGTERM, &handler, NULL) || sigaction(SIGINT, &handler, NULL))
        return 1;

    const char *name = getenv("BEACON_SUPERVISOR_WORLD");
    if (!name)
        name = BEACON_SHM_WORLD;
    const int backoff_ms[] = {100, 500, 2000, 5000};
    size_t attempt = 0;
    while (!stopping) {
        pid_t pid;
        uint64_t started = beacon_now_ns();
        int error = posix_spawnp(&pid, argv[1], NULL, NULL, argv + 1, environ);
        if (error) {
            errno = error;
            perror("spawn worker");
            return 1;
        }
        fprintf(stderr, "started %ld\n", (long)pid);
        const beacon_world_t *world = MAP_FAILED;
        uint64_t last = started, first = 0;
        int reaped = 0;
        while (!stopping) {
            pid_t result = waitpid(pid, NULL, WNOHANG);
            if (result == pid) {
                reaped = 1;
                break;
            }
            if (world == MAP_FAILED)
                world = open_world(name);
            uint64_t beat = 0;
            if (world != MAP_FAILED && world->abi == BEACON_ABI_VERSION)
                if (!beacon_seq_read(&world->seq_guided, &beat, &world->guided.hb_guided_ns,
                                     sizeof(beat), 3, NULL))
                    beat = 0;
            uint64_t now = beacon_now_ns();
            if (beat > last && beat <= now) {
                last = beat;
                if (!first && now - beat < 2 * BEACON_SUP_TICK_NS) {
                    first = beat;
                    fprintf(stderr, "heartbeat %ld (piezo stub clear)\n", (long)pid);
                }
            }
            if (now - last >= 2 * BEACON_SUP_TICK_NS)
                break;
            if (first && last - first >= 10000000000ULL)
                attempt = 0;
            poll(NULL, 0, (int)(BEACON_SUP_TICK_NS / 1000000));
        }
        if (world != MAP_FAILED)
            munmap((void *)world, sizeof(*world));
        if (!reaped) {
            kill(pid, SIGKILL);
            while (waitpid(pid, NULL, 0) < 0 && errno == EINTR) {}
        }
        if (!stopping) {
            fprintf(stderr, "worker fault (piezo stub on), restart in %d ms\n", backoff_ms[attempt]);
            poll(NULL, 0, backoff_ms[attempt]);
            if (attempt + 1 < sizeof(backoff_ms) / sizeof(backoff_ms[0]))
                ++attempt;
        }
    }
    return 0;
}
