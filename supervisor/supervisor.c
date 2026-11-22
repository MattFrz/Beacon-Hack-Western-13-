/* supervisor.c: Beacon's process parent (spec §5.1).
 *
 * Two modes:
 *
 *   supervisor CHILD [ARG ...]
 *       Legacy single child. This is the laptop test shape: no scheduler
 *       attributes are requested, so `make -C supervisor test` runs as an
 *       ordinary user. Heartbeat is the seqlocked hb_guided_ns field.
 *
 *   supervisor --beacon [opts]
 *       The stack from the spec's process table: guided is the deadline
 *       process and the only one whose death is a fault; everything else is
 *       restart-only and must never mute the cue. Spawns with the policy,
 *       priority and runmask from include/beacon.h, on a 50 ms
 *       CLOCK_MONOTONIC pulse timer, and owns the shm regions.
 *
 * Options (both modes):
 *   --create              create the three shm regions before spawning
 *                         (beacon mode always creates them)
 *   --metres              pass --metres to guided (laptop stand-in for the
 *                         tape-checked metre path)
 *   --with "CMD ..."      extra child for --beacon, SCHED_RR 20 on cores 1-3
 *                         (repeatable; used to supervise the percept producer)
 *   --dry-run             print the spawn table and exit
 *
 * Honest limits, 2026-11-21 (no buzzer, no transistor, no LED on hand):
 *   - There is no second output channel. If guided dies the wearer hears
 *     nothing until the respawn lands; this file logs the fault and restarts
 *     fast, and the pitch must not claim a piezo fault tone.
 *   - camd publishes no heartbeat in shm. Liveness only.
 *   - The 50 ms tick is a QNX pulse timer. The children's heartbeat is the
 *     seqlocked shm field they already write; a child pulse (guided --sup)
 *     also refreshes it when one arrives. One authoritative source keeps a
 *     failed pulse attach from kill-looping guided.
 *
 * Design: docs/nathans-revision.md §5.1. Judging notes: docs/qnx-prize-track.md.
 */
#include "beacon.h"

#include <errno.h>
#include <fcntl.h>
#include <sched.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#ifdef __QNX__
#include <sys/neutrino.h>
#include <sys/procmgr.h>
#include <sys/siginfo.h>
#endif

extern char **environ;

#define CHILD_MAX      8
#define ARGV_MAX       24
#define HEARTBEAT_GRACE 2      /* missed 50 ms ticks before a guided fault */

static volatile sig_atomic_t stopping;
static int g_verbose = 1;

static void stop(int signal_number)
{
    (void)signal_number;
    stopping = 1;
}

/* A worker death interrupts the wait so the loop reaps promptly. */
static void child_signal(int signal_number)
{
    (void)signal_number;
}

static void nap_ns(uint64_t ns)
{
    struct timespec ts = { (time_t)(ns / 1000000000ull), (long)(ns % 1000000000ull) };
    while (nanosleep(&ts, &ts) == -1 && errno == EINTR && !stopping) {
    }
}

/* ------------------------------------------------------------------ shm */

/* Creates or grows a region and zeroes it only when it was new or too small,
 * so a supervisor restart does not wipe a live session. */
static int create_region(const char *name, size_t size)
{
    int fd = shm_open(name, O_CREAT | O_RDWR, 0666);
    if (fd < 0) {
        perror(name);
        return -1;
    }
    struct stat st;
    int fresh = 0;
    if (fstat(fd, &st) == -1) {
        close(fd);
        return -1;
    }
    if ((size_t)st.st_size < size) {
        if (ftruncate(fd, (off_t)size) == -1) {
            perror(name);
            close(fd);
            return -1;
        }
        fresh = st.st_size == 0;
    }
    if (fresh) {
        void *map = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        if (map != MAP_FAILED) {
            memset(map, 0, size);
            munmap(map, size);
        }
    }
    close(fd);
    return 0;
}

static const char *world_name(void)
{
    const char *name = getenv("BEACON_SUPERVISOR_WORLD");
    return name ? name : BEACON_SHM_WORLD;
}

static const char *frames_name(void)
{
    const char *name = getenv("BEACON_FRAMES");
    return name ? name : BEACON_SHM_FRAMES;
}

static const char *depth_name(void)
{
    const char *name = getenv("BEACON_DEPTH");
    return name ? name : BEACON_SHM_DEPTH;
}

/* Creates the regions the spec gives the supervisor: frames, depth, world.
 * The world is stamped with the ABI because the creator owns that decision;
 * its seqs stay even and zero so every reader sees "stable, empty". */
static int ensure_regions(void)
{
    if (create_region(frames_name(), sizeof(beacon_frames_t)) == -1)
        return -1;
    if (create_region(depth_name(), sizeof(beacon_depth_t)) == -1)
        return -1;
    if (create_region(world_name(), sizeof(beacon_world_t)) == -1)
        return -1;

    int fd = shm_open(world_name(), O_RDWR, 0666);
    if (fd < 0) {
        perror("world");
        return -1;
    }
    beacon_world_t *w = mmap(NULL, sizeof(beacon_world_t), PROT_READ | PROT_WRITE,
                             MAP_SHARED, fd, 0);
    close(fd);
    if (w == MAP_FAILED) {
        perror("mmap world");
        return -1;
    }
    if (w->abi == 0)
        w->abi = BEACON_ABI_VERSION;
    int bad = w->abi != BEACON_ABI_VERSION;
    munmap(w, sizeof(*w));
    if (bad) {
        fprintf(stderr, "supervisor: world abi %u != %u\n", w->abi, BEACON_ABI_VERSION);
        return -1;
    }
    return 0;
}

static const beacon_world_t *open_world(void)
{
    /* A child (guided --create) may still be creating the region at startup. */
    int fd = shm_open(world_name(), O_RDONLY, 0);
    if (fd < 0)
        return MAP_FAILED;
    struct stat st;
    void *map = MAP_FAILED;
    if (fstat(fd, &st) == 0 && st.st_size >= (off_t)sizeof(beacon_world_t))
        map = mmap(NULL, sizeof(beacon_world_t), PROT_READ, MAP_SHARED, fd, 0);
    close(fd);
    return map;
}

/* ------------------------------------------------------------------ children */

enum heartbeat { HB_NONE = 0, HB_SHM_GUIDED, HB_PULSE_GUIDED };

typedef struct {
    const char *name;
    char *argv[ARGV_MAX + 1];   /* NULL-terminated */
    int argc;
    int policy;                 /* SCHED_FIFO or SCHED_RR */
    int prio;
    unsigned runmask;
    int hb;
    pid_t pid;
    uint64_t last_beat_ns;      /* last proof of life */
    uint64_t spawn_ns;
    uint64_t healthy_since_ns;
    uint64_t restart_at_ns;
    size_t attempt;
} child_t;

static const int backoff_ms[] = { 100, 500, 2000, 5000 };

#ifdef __QNX__
static int g_chid = -1;
static int g_coid = -1;

/* Spec §5.1: privileged priorities need AID_PRIORITY. Non-fatal: if this
 * fails we simply stay at the unprivileged ceiling (63). */
static void allow_priorities(void)
{
    if (procmgr_ability(0,
                        PROCMGR_ADN_ROOT | PROCMGR_AOP_ALLOW | PROCMGR_AID_PRIORITY,
                        PROCMGR_ADN_NONROOT | PROCMGR_AOP_ALLOW | PROCMGR_AID_PRIORITY,
                        PROCMGR_AID_EOL) == -1)
        fprintf(stderr, "supervisor: procmgr_ability(AID_PRIORITY): %s\n", strerror(errno));
}

static int pulse_channel(void)
{
    g_chid = ChannelCreate(0);
    if (g_chid == -1) {
        perror("ChannelCreate");
        return -1;
    }
    g_coid = ConnectAttach(0, 0, g_chid, _NTO_SIDE_CHANNEL, 0);
    if (g_coid == -1) {
        perror("ConnectAttach");
        return -1;
    }
    struct sigevent ev;
    struct itimerspec its;
    SIGEV_PULSE_INIT(&ev, g_coid, BEACON_PRIO_SUPERVISOR,
                     _PULSE_CODE_MINAVAIL + BEACON_PULSE_SUP_TICK, 0);
    timer_t timer;
    if (timer_create(CLOCK_MONOTONIC, &ev, &timer) == -1) {
        perror("timer_create");
        return -1;
    }
    its.it_value.tv_sec = 0;
    its.it_value.tv_nsec = (long)BEACON_SUP_TICK_NS;
    its.it_interval = its.it_value;
    if (timer_settime(timer, 0, &its, NULL) == -1) {
        perror("timer_settime");
        return -1;
    }
    return 0;
}
#endif

/* Spawns one child. Returns the pid, or -1. Scheduler attributes are
 * requested when the host supports them; if the kernel refuses (no root, no
 * ability, or a laptop without RT scheduling) it retries without them so the
 * stack still comes up, and says so. */
static pid_t spawn_child(child_t *c)
{
    posix_spawnattr_t attr;
    short flags = 0;
    int have_attr = posix_spawnattr_init(&attr) == 0;

    if (have_attr) {
#ifdef POSIX_SPAWN_SETSCHEDULER
        flags |= POSIX_SPAWN_SETSCHEDULER;
#endif
#ifdef POSIX_SPAWN_SETSCHEDPARAM
        flags |= POSIX_SPAWN_SETSCHEDPARAM;
#endif
#if defined(__QNX__) && defined(POSIX_SPAWN_EXPLICIT_SCHED)
        flags |= POSIX_SPAWN_EXPLICIT_SCHED;
#endif
#if defined(__QNX__) && defined(POSIX_SPAWN_SETRUNMASK)
        flags |= POSIX_SPAWN_SETRUNMASK;
        posix_spawnattr_setrunmask(&attr, c->runmask);
#endif
        if (flags) {
            struct sched_param sp;
            memset(&sp, 0, sizeof(sp));
            sp.sched_priority = c->prio;
            posix_spawnattr_setschedparam(&attr, &sp);
            posix_spawnattr_setschedpolicy(&attr, c->policy);
            posix_spawnattr_setflags(&attr, flags);
        } else {
            have_attr = 0;   /* nothing to ask for on this host */
        }
    }

    pid_t pid = 0;
    int error = posix_spawnp(&pid, c->argv[0], NULL, have_attr ? &attr : NULL,
                             c->argv, environ);
    if (error && have_attr) {
        /* EPERM / ENOTSUP: run without scheduler attributes rather than
         * leaving the product half-started. Never silent. */
        fprintf(stderr, "supervisor: %s: spawn with sched attrs failed (%s), retrying plain\n",
                c->name, strerror(error));
        error = posix_spawnp(&pid, c->argv[0], NULL, NULL, c->argv, environ);
    }
    if (have_attr)
        posix_spawnattr_destroy(&attr);
    if (error) {
        errno = error;
        fprintf(stderr, "supervisor: spawn %s: %s\n", c->name, strerror(error));
        return -1;
    }
    return pid;
}

static void describe(const child_t *c)
{
    printf("  %-9s prio %-2d %-9s runmask 0x%x  %s\n", c->name, c->prio,
           c->policy == SCHED_FIFO ? "SCHED_FIFO" : "SCHED_RR", c->runmask,
           c->argv[0]);
}

/* ------------------------------------------------------------------ argv */

static int add_argv(child_t *c, const char *arg)
{
    if (c->argc >= ARGV_MAX) {
        fprintf(stderr, "supervisor: %s: too many arguments\n", c->name);
        return -1;
    }
    c->argv[c->argc++] = (char *)arg;
    c->argv[c->argc] = NULL;
    return 0;
}

/* Splits "a b c" on single spaces into owned strings. Only used for extra
 * argv from --with and --guided-args; quoting stays the shell's job. */
static int add_argv_line(child_t *c, const char *line)
{
    char *copy = strdup(line);
    if (!copy)
        return -1;
    int rc = 0;
    for (char *tok = strtok(copy, " "); tok && rc == 0; tok = strtok(NULL, " ")) {
        char *arg = strdup(tok);
        rc = (arg && add_argv(c, arg) == 0) ? 0 : -1;
    }
    free(copy);
    return rc;
}

/* ------------------------------------------------------------------ beacon table */

static int beacon_children(child_t *kids, int cap, int metres, const char *guided_args,
                          const char *ingest_args)
{
    int n = 0;
    if (n >= cap)
        return -1;

    child_t *g = &kids[n++];
    memset(g, 0, sizeof(*g));
    g->name = "guided";
    g->policy = SCHED_FIFO;
    g->prio = BEACON_PRIO_GUIDED;
    g->runmask = BEACON_RUNMASK_CORE0;
    g->hb = HB_SHM_GUIDED;
    const char *guided = getenv("BEACON_GUIDED");
    add_argv(g, guided ? guided : "guided/build/guided");
    if (metres)
        add_argv(g, "--metres");
#ifdef __QNX__
    if (g_chid != -1) {
        static char sup[32];
        snprintf(sup, sizeof(sup), "%ld:%d", (long)getpid(), g_chid);
        add_argv(g, "--sup");
        add_argv(g, sup);
    }
#endif
    if (guided_args && *guided_args && add_argv_line(g, guided_args) == -1)
        return -1;

    child_t *i = &kids[n++];
    memset(i, 0, sizeof(*i));
    i->name = "ingest";
    i->policy = SCHED_RR;
    i->prio = BEACON_PRIO_INGEST;
    i->runmask = BEACON_RUNMASK_CPU1;   /* 0xe is EINVAL on this image (beacon.h) */
    i->hb = HB_NONE;
    const char *ingest = getenv("BEACON_INGEST");
    add_argv(i, ingest ? ingest : "ingest/build/ingest");
    if (ingest_args && *ingest_args && add_argv_line(i, ingest_args) == -1)
        return -1;

    return n;
}

/* ------------------------------------------------------------------ main */

int main(int argc, char **argv)
{
    int beacon = 0, create = 0, metres = 0, dry = 0;
    char *with_lines[CHILD_MAX] = { 0 };
    int n_with = 0;
    const char *guided_args = NULL;
    const char *ingest_args = NULL;

    /* Line-buffered so a redirected log reads in order next to stderr. */
    setvbuf(stdout, NULL, _IOLBF, 0);

    if (argc < 2) {
        fprintf(stderr,
                "Usage: supervisor CHILD [ARG ...]\n"
                "       supervisor --beacon [--metres] [--with \"CMD ...\"] [--dry-run]\n");
        return 2;
    }

    struct sigaction handler;
    memset(&handler, 0, sizeof(handler));
    handler.sa_handler = stop;
    sigemptyset(&handler.sa_mask);
    sigaction(SIGTERM, &handler, NULL);
    sigaction(SIGINT, &handler, NULL);
    signal(SIGCHLD, child_signal);

    int first = 0;   /* index of the child argv, 0 = none */
    for (int a = 1; a < argc; ++a) {
        if (!strcmp(argv[a], "--beacon")) {
            beacon = 1;
            create = 1;
        } else if (!strcmp(argv[a], "--create")) {
            create = 1;
        } else if (!strcmp(argv[a], "--metres")) {
            metres = 1;
        } else if (!strcmp(argv[a], "--dry-run")) {
            dry = 1;
        } else if (!strcmp(argv[a], "--with") && a + 1 < argc) {
            if (n_with >= CHILD_MAX) {
                fprintf(stderr, "supervisor: too many --with children\n");
                return 2;
            }
            with_lines[n_with++] = argv[++a];
        } else if (!strcmp(argv[a], "--guided-args") && a + 1 < argc) {
            guided_args = argv[++a];
        } else if (!strcmp(argv[a], "--ingest-args") && a + 1 < argc) {
            ingest_args = argv[++a];
        } else if (!strncmp(argv[a], "--", 2)) {
            fprintf(stderr, "supervisor: unknown option %s\n", argv[a]);
            return 2;
        } else {
            first = a;
            break;
        }
    }

    if (!beacon && first == 0) {
        fprintf(stderr, "supervisor: missing CHILD, or pass --beacon\n");
        return 2;
    }

    const char *world = world_name();
    if (create && ensure_regions() == -1)
        return 1;

#ifdef __QNX__
    if (beacon) {
        allow_priorities();
        if (pulse_channel() == -1)
            fprintf(stderr, "supervisor: no pulse channel; falling back to nanosleep ticks\n");
    }
#endif

    /* -------------------------------------------------- legacy single child */
    if (!beacon) {
        const int backoff[] = { 100, 500, 2000, 5000 };
        size_t attempt = 0;
        if (dry)
            return 0;
        while (!stopping) {
            pid_t pid;
            uint64_t started = beacon_now_ns();
            int error = posix_spawnp(&pid, argv[first], NULL, NULL, argv + first, environ);
            if (error) {
                errno = error;
                perror("spawn worker");
                return 1;
            }
            fprintf(stderr, "started %ld\n", (long)pid);
            const beacon_world_t *w = MAP_FAILED;
            uint64_t last = started, first_beat = 0;
            int reaped = 0;
            while (!stopping) {
                pid_t result = waitpid(pid, NULL, WNOHANG);
                if (result == pid) {
                    reaped = 1;
                    break;
                }
                if (w == MAP_FAILED)
                    w = open_world();
                uint64_t beat = 0;
                if (w != MAP_FAILED && w->abi == BEACON_ABI_VERSION)
                    if (!beacon_seq_read(&w->seq_guided, &beat, &w->guided.hb_guided_ns,
                                         sizeof(beat), 3, NULL))
                        beat = 0;
                uint64_t now = beacon_now_ns();
                if (beat > last && beat <= now) {
                    last = beat;
                    if (!first_beat && now - beat < 2 * BEACON_SUP_TICK_NS) {
                        first_beat = beat;
                        fprintf(stderr, "heartbeat %ld (deadline thread alive)\n", (long)pid);
                    }
                }
                if (now - last >= 2 * BEACON_SUP_TICK_NS)
                    break;
                if (first_beat && last - first_beat >= 10000000000ULL)
                    attempt = 0;
                nap_ns(BEACON_SUP_TICK_NS);
            }
            if (w != MAP_FAILED)
                munmap((void *)w, sizeof(*w));
            if (!reaped) {
                kill(pid, SIGKILL);
                while (waitpid(pid, NULL, 0) < 0 && errno == EINTR) {
                }
            }
            if (!stopping) {
                fprintf(stderr, "worker fault (no output channel), restart in %d ms\n",
                        backoff[attempt]);
                nap_ns((uint64_t)backoff[attempt] * 1000000ull);
                if (attempt + 1 < sizeof(backoff) / sizeof(backoff[0]))
                    ++attempt;
            }
        }
        return 0;
    }

    /* -------------------------------------------------- beacon stack */
    child_t kids[CHILD_MAX];
    memset(kids, 0, sizeof(kids));
    int n = beacon_children(kids, CHILD_MAX, metres, guided_args, ingest_args);
    if (n < 0) {
        fprintf(stderr, "supervisor: child table overflow\n");
        return 2;
    }
    for (int k = 0; k < n_with; ++k) {
        if (n >= CHILD_MAX)
            break;
        child_t *c = &kids[n];
        memset(c, 0, sizeof(*c));
        c->name = "extra";
        c->policy = SCHED_RR;
        c->prio = BEACON_PRIO_INGEST;
        c->runmask = BEACON_RUNMASK_CPU1;   /* tuned for the loaner image */
        c->hb = HB_NONE;
        if (add_argv_line(c, with_lines[k]) == -1)
            return 2;
        ++n;
    }

    printf("supervisor: %d children, shm world %s\n", n, world);
    for (int k = 0; k < n; ++k)
        describe(&kids[k]);
    if (dry)
        return 0;

    uint64_t now = beacon_now_ns();
    for (int k = 0; k < n; ++k) {
        kids[k].pid = spawn_child(&kids[k]);
        if (kids[k].pid > 0) {
            kids[k].last_beat_ns = kids[k].spawn_ns = now;
            kids[k].healthy_since_ns = now;
            if (g_verbose)
                fprintf(stderr, "started %s %ld\n", kids[k].name, (long)kids[k].pid);
        } else {
            kids[k].restart_at_ns = now + 1000000000ull;   /* retry in 1 s */
        }
    }

    const beacon_world_t *w = MAP_FAILED;
    while (!stopping) {
        /* 1. sleep until the next 50 ms tick, waking early for a child death
         *    or (on QNX) a child pulse. */
#ifdef __QNX__
        if (g_chid != -1) {
            struct _pulse p;
            int rc = MsgReceivePulse(g_chid, &p, sizeof(p), NULL);
            if (rc == 0 && p.code == (_PULSE_CODE_MINAVAIL + BEACON_PULSE_HB_GUIDED)) {
                for (int k = 0; k < n; ++k)
                    if (kids[k].hb == HB_PULSE_GUIDED || kids[k].hb == HB_SHM_GUIDED)
                        kids[k].last_beat_ns = beacon_now_ns();
            }
        } else {
            nap_ns(BEACON_SUP_TICK_NS);
        }
#else
        nap_ns(BEACON_SUP_TICK_NS);
#endif
        if (stopping)
            break;
        now = beacon_now_ns();

        /* 2. reap, then decide who restarts and who faulted. */
        for (int k = 0; k < n; ++k) {
            child_t *c = &kids[k];
            if (c->pid > 0) {
                int status = 0;
                pid_t r = waitpid(c->pid, &status, WNOHANG);
                if (r == c->pid) {
                    if (g_verbose)
                        fprintf(stderr, "%s exited pid %ld\n", c->name, (long)c->pid);
                    c->pid = 0;
                    c->restart_at_ns = now + (uint64_t)backoff_ms[c->attempt] * 1000000ull;
                    if (c->attempt + 1 < sizeof(backoff_ms) / sizeof(backoff_ms[0]))
                        ++c->attempt;
                    if (c->hb == HB_SHM_GUIDED || c->hb == HB_PULSE_GUIDED)
                        fprintf(stderr, "guided fault (no output channel)\n");
                }
            }
        }

        /* 3. heartbeat: the seqlocked shm field children already publish. */
        if (w == MAP_FAILED)
            w = open_world();
        if (w != MAP_FAILED && w->abi == BEACON_ABI_VERSION) {
            uint64_t beat = 0;
            if (beacon_seq_read(&w->seq_guided, &beat, &w->guided.hb_guided_ns,
                                sizeof(beat), 3, NULL) && beat) {
                for (int k = 0; k < n; ++k) {
                    child_t *c = &kids[k];
                    if (c->hb != HB_SHM_GUIDED)
                        continue;
                    if (beat > c->last_beat_ns && beat <= now)
                        c->last_beat_ns = beat;
                }
            }
        }

        for (int k = 0; k < n; ++k) {
            child_t *c = &kids[k];
            const int critical = c->hb != HB_NONE;

            /* A live critical child that stops beating is dead even if the pid
             * survives: SIGSTOP, a wedged loop, a binding that never returns.
             * Startup gets a two second grace because guided loads its clips
             * before the first heartbeat. */
            uint64_t grace = HEARTBEAT_GRACE * BEACON_SUP_TICK_NS;
            if (now - c->spawn_ns < 2000000000ull)
                grace = 2000000000ull;
            if (c->pid > 0 && critical && now - c->last_beat_ns >= grace) {
                fprintf(stderr, "%s fault: heartbeat stale, killing pid %ld\n",
                        c->name, (long)c->pid);
                kill(c->pid, SIGKILL);
                while (waitpid(c->pid, NULL, 0) < 0 && errno == EINTR) {
                }
                c->pid = 0;
                c->restart_at_ns = now + (uint64_t)backoff_ms[c->attempt] * 1000000ull;
                if (c->attempt + 1 < sizeof(backoff_ms) / sizeof(backoff_ms[0]))
                    ++c->attempt;
                continue;
            }

            /* Backoff resets after ten healthy seconds, so a crash loop does
             * not park the cue on a five second delay forever. */
            if (c->pid > 0 && c->attempt &&
                now - c->healthy_since_ns >= 10000000000ull)
                c->attempt = 0;

            if (c->pid == 0 && now >= c->restart_at_ns) {
                pid_t pid = spawn_child(c);
                if (pid > 0) {
                    c->pid = pid;
                    c->spawn_ns = c->healthy_since_ns = c->last_beat_ns = now;
                    if (g_verbose)
                        fprintf(stderr, "restarted %s %ld\n", c->name, (long)pid);
                } else {
                    c->restart_at_ns = now + (uint64_t)backoff_ms[c->attempt] * 1000000ull;
                }
            }
        }
    }

    /* Shutdown: TERM the children in reverse so guided outlives its writers,
     * then give them two seconds before SIGKILL. A child that ignores SIGTERM
     * must not hang the supervisor at the end of a demo. */
    for (int k = n - 1; k >= 0; --k) {
        if (kids[k].pid > 0)
            kill(kids[k].pid, SIGTERM);
    }
    uint64_t give_up = beacon_now_ns() + 2000000000ull;
    for (int k = 0; k < n; ++k) {
        if (kids[k].pid <= 0)
            continue;
        for (;;) {
            pid_t r = waitpid(kids[k].pid, NULL, WNOHANG);
            if (r == kids[k].pid)
                break;
            if (beacon_now_ns() >= give_up) {
                kill(kids[k].pid, SIGKILL);
                while (waitpid(kids[k].pid, NULL, 0) < 0 && errno == EINTR) {
                }
                break;
            }
            nap_ns(10000000ull);
        }
    }
    if (w != MAP_FAILED)
        munmap((void *)w, sizeof(*w));
    return 0;
}
