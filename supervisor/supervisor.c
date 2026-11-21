#include "beacon.h"
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;
static volatile sig_atomic_t stopping;

static void stop(int signal_number)
{
    (void)signal_number;
    stopping = 1;
}

static int spawn_worker(char **args, pid_t *pid, int *reader)
{
    int channel[2];
    if (pipe(channel) < 0)
        return errno;
    posix_spawn_file_actions_t actions;
    int error = posix_spawn_file_actions_init(&actions);
    if (!error) {
        error = posix_spawn_file_actions_addclose(&actions, channel[0]);
        if (!error)
            error = posix_spawn_file_actions_adddup2(&actions, channel[1], STDOUT_FILENO);
        if (!error && channel[1] != STDOUT_FILENO)
            error = posix_spawn_file_actions_addclose(&actions, channel[1]);
        if (!error)
            error = posix_spawnp(pid, args[0], &actions, NULL, args, environ);
        posix_spawn_file_actions_destroy(&actions);
    }
    close(channel[1]);
    if (error)
        close(channel[0]);
    else
        *reader = channel[0];
    return error;
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
    const int backoff_ms[] = {100, 500, 2000, 5000};
    size_t attempt = 0;
    while (!stopping) {
        int reader;
        pid_t pid;
        int error = spawn_worker(argv + 1, &pid, &reader);
        if (error) {
            errno = error;
            perror("spawn worker");
            return 1;
        }
        fprintf(stderr, "started %ld\n", (long)pid);
        struct pollfd input = {.fd = reader, .events = POLLIN};
        uint64_t last_heartbeat = beacon_now_ns();
        int first = 1;
        while (!stopping && beacon_now_ns() - last_heartbeat < 2 * BEACON_SUP_TICK_NS) {
            int ready = poll(&input, 1, (int)(BEACON_SUP_TICK_NS / 1000000));
            if (ready < 0 && errno == EINTR)
                continue;
            if (ready < 0)
                break;
            if (ready == 0)
                continue;
            char bytes[64];
            ssize_t n = read(reader, bytes, sizeof(bytes));
            if (n <= 0)
                break;
            if (memchr(bytes, 'H', (size_t)n)) {
                last_heartbeat = beacon_now_ns();
                if (first)
                    fprintf(stderr, "heartbeat %ld (piezo stub clear)\n", (long)pid);
                first = 0;
            }
        }
        if (!stopping)
            fprintf(stderr, "worker fault (piezo stub on)\n");
        kill(pid, SIGKILL);
        while (waitpid(pid, NULL, 0) < 0 && errno == EINTR) {}
        close(reader);
        if (!stopping) {
            poll(NULL, 0, backoff_ms[attempt]);
            if (attempt + 1 < sizeof(backoff_ms) / sizeof(backoff_ms[0]))
                ++attempt;
        }
    }
    return 0;
}
