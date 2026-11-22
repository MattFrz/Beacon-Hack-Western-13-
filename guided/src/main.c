/* guided: the 60 Hz synthesizer (spec §5.1 "guided", §6, §9, §10).
 *
 * Every 16.67 ms on core 0 at SCHED_FIFO 58:
 *   1. copy the newest percept and voiced blocks (seqlock, never block)
 *   2. bind, compute mode, pick the law (law.c)
 *   3. hand speech / ticks to the audio thread (never block), drive the piezo
 *   4. publish target, heartbeat and stats under seq_guided, pulse supervisor
 *   5. sleep to the next absolute deadline; count misses, never catch up
 *
 * Usage: guided [--create] [--metres] [--no-orient-pips] [--hand-conf C] [--duration S] [--verbose] [--sup PID:CHID]
 *               [--audio none|qnx|fifo:PATH|FILE.wav] [--sounds DIR]
 *   --create    create /beacon_world if missing (laptop / standalone; the
 *               supervisor creates it on the Pi)
 *   --metres    speak distance in steps (only after the tape-measure check, spec §11)
 *   --no-orient-pips  no soft pips while turning toward the target
 *   --hand-conf C     ADDITION: lowest hand confidence REACH trusts (default 0.5). The
 *               on-device YOLO hand class scores 0.05-0.25, so the live demo passes 0.05.
 *   --audio     where sound goes (audio_out.h); default none
 *   --sounds    folder with the voice clips; default sounds/ or ../sounds/
 */
#include "audio.h"
#include "law.h"
#include "platform.h"

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t g_stop;
static void on_signal(int sig) { (void)sig; g_stop = 1; }

#define LATE_BUCKET_NS 50000ull   /* 50 us buckets */
#define LATE_BUCKETS   400        /* up to 20 ms; last bucket = overflow */

static beacon_world_t *open_world(int create)
{
    /* BEACON_WORLD lets tests / parallel instances use their own shm name
     * (supervisor has the same escape hatch via BEACON_SUPERVISOR_WORLD).
     * The product path never sets it: guided attaches to /beacon_world. */
    const char *shm_name = getenv("BEACON_WORLD");
    if (!shm_name)
        shm_name = BEACON_SHM_WORLD;
    int flags = O_RDWR | (create ? O_CREAT : 0);
    int fd = shm_open(shm_name, flags, 0666);
    if (fd == -1) {
        fprintf(stderr, "guided: shm_open %s: %s%s\n", shm_name, strerror(errno),
                create ? "" : " (start the supervisor or fakeworld first, or pass --create)");
        return NULL;
    }
    struct stat sb;
    if (fstat(fd, &sb) == -1) {
        close(fd);
        return NULL;
    }
    if ((size_t)sb.st_size < sizeof(beacon_world_t)) {
        if (!create || ftruncate(fd, (off_t)sizeof(beacon_world_t)) == -1) {
            fprintf(stderr, "guided: %s is %lld bytes, need %zu\n", shm_name,
                    (long long)sb.st_size, sizeof(beacon_world_t));
            close(fd);
            return NULL;
        }
    }
    void *m = mmap(NULL, sizeof(beacon_world_t), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (m == MAP_FAILED) {
        perror("guided: mmap");
        return NULL;
    }
    beacon_world_t *w = m;
    if (create && w->abi == 0)
        w->abi = BEACON_ABI_VERSION;
    if (w->abi != BEACON_ABI_VERSION)
        fprintf(stderr, "guided: warning: world abi %u, built for %u\n", w->abi, BEACON_ABI_VERSION);
    return w;
}

static void sleep_until(uint64_t t_ns)
{
    struct timespec ts = { (time_t)(t_ns / 1000000000ull), (long)(t_ns % 1000000000ull) };
    while (clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, NULL) == EINTR && !g_stop) {
    }
}

int main(int argc, char **argv)
{
    int create = 0, verbose = 0;
    double duration_s = 0.0;
    const char *sup = NULL;
    const char *audio_spec = "none";
    const char *sounds = NULL;
    guided_cfg_t cfg;
    guided_default_cfg(&cfg);

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--create")) create = 1;
        else if (!strcmp(argv[i], "--metres")) cfg.metres_enabled = 1;
        else if (!strcmp(argv[i], "--no-orient-pips")) cfg.orient_pips = 0;
        else if (!strcmp(argv[i], "--verbose")) verbose = 1;
        else if (!strcmp(argv[i], "--hand-conf") && i + 1 < argc) cfg.hand_conf_min = (float)atof(argv[++i]);
        else if (!strcmp(argv[i], "--duration") && i + 1 < argc) duration_s = atof(argv[++i]);
        else if (!strcmp(argv[i], "--sup") && i + 1 < argc) sup = argv[++i];
        else if (!strcmp(argv[i], "--audio") && i + 1 < argc) audio_spec = argv[++i];
        else if (!strcmp(argv[i], "--sounds") && i + 1 < argc) sounds = argv[++i];
        else {
            fprintf(stderr, "usage: %s [--create] [--metres] [--no-orient-pips] [--hand-conf C] [--duration S] [--verbose] [--sup PID:CHID]\n"
                            "       [--audio none|qnx|fifo:PATH|FILE.wav] [--sounds DIR]\n", argv[0]);
            return 2;
        }
    }
    if (!sounds)
        sounds = access("sounds/num_1.wav", R_OK) == 0 ? "sounds" : "../sounds";
    signal(SIGPIPE, SIG_IGN); /* a closed Bluetooth pipe must not kill guided */

    beacon_world_t *w = open_world(create);
    if (!w)
        return 1;

    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = on_signal;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    platform_piezo_init();
    if (sup)
        platform_supervisor_connect(sup);

    uint64_t t0 = beacon_now_ns();
    audio_cfg_t acfg = { .verbose = verbose, .sounds_dir = sounds, .out = audio_spec, .t0_ns = t0 };
    if (audio_start(&acfg) != 0) {
        fprintf(stderr, "guided: cannot start audio thread\n");
        return 1;
    }

    if (platform_set_thread_sched(BEACON_PRIO_GUIDED, BEACON_RUNMASK_CORE0) != 0)
        fprintf(stderr, "guided: running without SCHED_FIFO %d / core 0 pinning (normal on a laptop)\n",
                BEACON_PRIO_GUIDED);
    fprintf(stderr, "guided: 60 Hz, metres %s\n", cfg.metres_enabled ? "ON" : "off (pass --metres after the tape check)");

    static beacon_percept_block_t p;   /* last clean copies (zero = nothing yet) */
    static beacon_intent_t intent;
    int have_intent = 0;
    guided_state_t st;
    guided_init(&st, &cfg);

    static uint64_t late_hist[LATE_BUCKETS];
    beacon_guided_stats_t stats;
    memset(&stats, 0, sizeof(stats));
    beacon_guided_display_t disp;
    memset(&disp, 0, sizeof(disp));
    uint64_t piezo_off_at = 0;
    int tone = 0;

    uint64_t next = beacon_now_ns() + BEACON_GUIDED_PERIOD_NS;
    uint64_t end = duration_s > 0 ? t0 + (uint64_t)(duration_s * 1e9) : 0;

    while (!g_stop) {
        uint64_t now = beacon_now_ns();
        if (end && now >= end)
            break;

        /* 1. newest clean copies; on a torn or empty read keep the last good one */
        beacon_percept_block_t tmp_p;
        beacon_seq_t s;
        if (w->seq_percept != 0 &&
            beacon_seq_read(&w->seq_percept, &tmp_p, &w->percept, sizeof(tmp_p), 3, &s))
            p = tmp_p;
        beacon_intent_t tmp_i;
        if (w->seq_voiced != 0 &&
            beacon_seq_read(&w->seq_voiced, &tmp_i, &w->intent, sizeof(tmp_i), 3, &s)) {
            intent = tmp_i;
            have_intent = 1;
        }

        /* 2. decide */
        guided_out_t out;
        guided_step(&st, &p, have_intent ? &intent : NULL, now, &out);

        /* 3. audio and piezo, never blocking */
        for (int i = 0; i < out.n_cmds; ++i) {
            const guided_cmd_t *c = &out.cmds[i];
            audio_submit(c);
            if (c->kind == GUIDED_CMD_TICK) {
                platform_piezo_set(1);
                piezo_off_at = now + 20000000ull; /* 20 ms click */
            } else if (c->kind == GUIDED_CMD_TONE_ON) {
                tone = 1;
                platform_piezo_set(1);
            } else if (c->kind == GUIDED_CMD_TONE_OFF) {
                tone = 0;
                platform_piezo_set(0);
            } else if (c->kind == GUIDED_CMD_SAY) {
                disp.n_last_clips = c->n_clips;
                memcpy(disp.last_clips, c->clips, sizeof(disp.last_clips));
            }
        }
        if (!tone && piezo_off_at && now >= piezo_off_at) {
            platform_piezo_set(0);
            piezo_off_at = 0;
        }

        /* 4. publish (guided is the only writer of seq_guided) */
        disp.law = (uint32_t)out.law;
        disp.d_m = out.d_m;
        disp.pan = out.pan;
        disp.tick_hz = out.tick_hz;
        disp.continuous = (uint8_t)out.continuous;
        beacon_seq_write_begin(&w->seq_guided);
        w->guided.hb_guided_ns = now;
        w->guided.target = st.target;
        w->guided.display = disp;
        w->guided.stats = stats;
        beacon_seq_write_end(&w->seq_guided);
        audio_publish_stats(&stats, out.law, out.mode, out.d_m);
        platform_heartbeat();

        /* 5. absolute deadline; a late wake counts a miss and jumps forward */
        sleep_until(next);
        uint64_t woke = beacon_now_ns();
        uint64_t late = woke > next ? woke - next : 0;
        stats.loops++;
        if (late > stats.worst_late_ns)
            stats.worst_late_ns = late;
        uint64_t b = late / LATE_BUCKET_NS;
        late_hist[b < LATE_BUCKETS ? b : LATE_BUCKETS - 1]++;
        if (stats.loops % 60 == 0) {
            uint64_t want = (stats.loops * 95 + 99) / 100, acc = 0;
            for (int i = 0; i < LATE_BUCKETS; ++i) {
                acc += late_hist[i];
                if (acc >= want) {
                    stats.p95_late_ns = (uint64_t)(i + 1) * LATE_BUCKET_NS;
                    break;
                }
            }
        }
        next += BEACON_GUIDED_PERIOD_NS;
        if (woke > next) {
            stats.misses++;
            next = woke + BEACON_GUIDED_PERIOD_NS; /* do not catch up */
        }
    }

    platform_piezo_set(0);
    audio_stop();
    fprintf(stderr, "guided: %llu loops, %llu missed deadlines, worst lateness %.0f us, p95 %.0f us, %llu speech drops\n",
            (unsigned long long)stats.loops, (unsigned long long)stats.misses,
            stats.worst_late_ns / 1e3, stats.p95_late_ns / 1e3,
            (unsigned long long)audio_dropped_speech());
    munmap(w, sizeof(*w));
    return 0;
}
