/* audio.c: guided's audio thread. See audio.h.
 *
 * Laptop: prints what the wearer would hear.
 * QNX: same printing for now; USB playback through io-audio is a TODO until a
 * USB headset or speaker is on the Pi (the JBL Go 3 is Bluetooth-only).
 */
#include "audio.h"
#include "platform.h"

#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#define SPEECH_SLOTS 32u

static const char *const k_clip_words[BEACON_CLIP_COUNT] = {
    [BEACON_CLIP_NONE] = "",
    [BEACON_CLIP_NUM_0] = "zero", [BEACON_CLIP_NUM_1] = "one", [BEACON_CLIP_NUM_2] = "two",
    [BEACON_CLIP_NUM_3] = "three", [BEACON_CLIP_NUM_4] = "four", [BEACON_CLIP_NUM_5] = "five",
    [BEACON_CLIP_NUM_6] = "six", [BEACON_CLIP_NUM_7] = "seven", [BEACON_CLIP_NUM_8] = "eight",
    [BEACON_CLIP_NUM_9] = "nine",
    [BEACON_CLIP_METRE] = "metre", [BEACON_CLIP_METRES] = "metres",
    [BEACON_CLIP_AHEAD] = "ahead", [BEACON_CLIP_LEFT] = "left", [BEACON_CLIP_RIGHT] = "right",
    [BEACON_CLIP_UP] = "up", [BEACON_CLIP_DOWN] = "down",
    [BEACON_CLIP_LOST_TARGET] = "I lost the target",
    [BEACON_CLIP_STOPPING] = "stopping",
    [BEACON_CLIP_NOT_SEEN] = "I have not seen that",
    [BEACON_CLIP_CANNOT_RETRACE] = "I cannot retrace without a path",
    [BEACON_CLIP_DID_NOT_CATCH] = "I did not catch that",
    [BEACON_CLIP_CANNOT_HELP] = "I cannot help with that",
    [BEACON_CLIP_ABOUT] = "about", [BEACON_CLIP_A_LITTLE] = "a little",
    [BEACON_CLIP_YOU_ARE_BACK] = "you are back",
    [BEACON_CLIP_PROMPT_BEEP] = "<beep>",
    [BEACON_CLIP_OBJECT_NAME] = "<name>",
};

/* speech ring: single producer (16 ms thread), single consumer (audio thread) */
static guided_cmd_t    g_ring[SPEECH_SLOTS];
static _Atomic uint32_t g_head, g_tail, g_flush_upto;
static _Atomic uint64_t g_dropped;

/* newest-wins tick/tone slot */
typedef struct { uint32_t gen; guided_cmd_t cmd; } tick_payload_t;
static struct { beacon_seq_t seq; tick_payload_t p; } g_tick;

/* stats slot */
typedef struct { beacon_guided_stats_t stats; int law, mode; float d_m; } stats_payload_t;
static struct { beacon_seq_t seq; stats_payload_t p; } g_stats;

static pthread_t   g_thread;
static atomic_int  g_run;
static audio_cfg_t g_cfg;

/* ------------------------------------------------------------------ producer side */
void audio_submit(const guided_cmd_t *cmd)
{
    switch (cmd->kind) {
    case GUIDED_CMD_FLUSH_SPEECH:
        atomic_store_explicit(&g_flush_upto, atomic_load_explicit(&g_head, memory_order_relaxed),
                              memory_order_release);
        break;
    case GUIDED_CMD_SAY: {
        uint32_t h = atomic_load_explicit(&g_head, memory_order_relaxed);
        uint32_t t = atomic_load_explicit(&g_tail, memory_order_acquire);
        if (h - t >= SPEECH_SLOTS) {
            atomic_fetch_add(&g_dropped, 1);
            return;
        }
        g_ring[h % SPEECH_SLOTS] = *cmd;
        atomic_store_explicit(&g_head, h + 1, memory_order_release);
        break;
    }
    case GUIDED_CMD_TICK:
    case GUIDED_CMD_TONE_ON:
    case GUIDED_CMD_TONE_OFF:
        beacon_seq_write_begin(&g_tick.seq);
        g_tick.p.gen++;
        g_tick.p.cmd = *cmd;
        beacon_seq_write_end(&g_tick.seq);
        break;
    default:
        break;
    }
}

void audio_publish_stats(const beacon_guided_stats_t *stats, int law, int mode, float d_m)
{
    beacon_seq_write_begin(&g_stats.seq);
    g_stats.p.stats = *stats;
    g_stats.p.law = law;
    g_stats.p.mode = mode;
    g_stats.p.d_m = d_m;
    beacon_seq_write_end(&g_stats.seq);
}

uint64_t audio_dropped_speech(void) { return atomic_load(&g_dropped); }

/* ------------------------------------------------------------------ consumer side */
static double secs(void) { return (double)(beacon_now_ns() - g_cfg.t0_ns) * 1e-9; }

static void print_say(const guided_cmd_t *c)
{
    char line[256];
    size_t n = 0;
    line[0] = '\0';
    for (int i = 0; i < c->n_clips && n < sizeof(line) - 40; ++i) {
        const char *w = (c->clips[i] == BEACON_CLIP_OBJECT_NAME) ? c->name
                      : (c->clips[i] < BEACON_CLIP_COUNT ? k_clip_words[c->clips[i]] : "?");
        n += (size_t)snprintf(line + n, sizeof(line) - n, "%s%s", i ? " " : "", w);
    }
    printf("[%7.3f] SAY%s  \"%s\"\n", secs(), c->priority ? "!" : " ", line);
    /* TODO(QNX): play sounds/<clip>.wav (and sounds/name_<label>.wav) through io-audio. */
}

static const char *law_name(int law)
{
    static const char *n[] = { "NONE", "STOP", "LOST", "REACH", "WALK", "RETURN" };
    return (law >= 0 && law <= BEACON_LAW_RETURN) ? n[law] : "?";
}

static const char *mode_name(int mode)
{
    static const char *n[] = { "NONE", "LIVE", "HOLD", "LOST" };
    return (mode >= 0 && mode <= BEACON_MODE_LOST) ? n[mode] : "?";
}

static void *audio_main(void *arg)
{
    (void)arg;
    platform_set_thread_sched(BEACON_PRIO_AUDIO, BEACON_RUNMASK_CORE0);

    uint32_t seen_gen = 0;
    double last_tick_print = -1.0, last_stats_print = 0.0;
    int ticks_since_print = 0;
    struct timespec nap = { 0, 2000000 }; /* 2 ms */

    while (atomic_load(&g_run)) {
        /* flush first, then speech */
        uint32_t t = atomic_load_explicit(&g_tail, memory_order_relaxed);
        uint32_t f = atomic_load_explicit(&g_flush_upto, memory_order_acquire);
        if ((int32_t)(f - t) > 0) {
            atomic_store_explicit(&g_tail, f, memory_order_release);
            t = f;
        }
        uint32_t h = atomic_load_explicit(&g_head, memory_order_acquire);
        while (t != h) {
            guided_cmd_t c = g_ring[t % SPEECH_SLOTS];
            t++;
            atomic_store_explicit(&g_tail, t, memory_order_release);
            print_say(&c);
        }

        /* ticks and tone: newest wins */
        tick_payload_t tk;
        if (beacon_seq_read(&g_tick.seq, &tk, &g_tick.p, sizeof(tk), 4, NULL) && tk.gen != seen_gen) {
            uint32_t missed = tk.gen - seen_gen - 1;
            seen_gen = tk.gen;
            if (tk.cmd.kind == GUIDED_CMD_TONE_ON) {
                printf("[%7.3f] TONE  on   pan %+.2f\n", secs(), tk.cmd.pan);
            } else if (tk.cmd.kind == GUIDED_CMD_TONE_OFF) {
                printf("[%7.3f] TONE  off\n", secs());
            } else {
                ticks_since_print += 1 + (int)missed;
                double now = secs();
                if (g_cfg.verbose || now - last_tick_print >= 0.5) {
                    printf("[%7.3f] TICK  x%-2d pan %+.2f amp %.2f%s\n", now, ticks_since_print,
                           tk.cmd.pan, tk.cmd.amp, tk.cmd.dark ? "  (hold)" : "");
                    last_tick_print = now;
                    ticks_since_print = 0;
                }
            }
        }

        /* stats every 5 s, from the printer thread, never from the 16 ms thread */
        double now = secs();
        if (now - last_stats_print >= 5.0) {
            stats_payload_t st;
            if (beacon_seq_read(&g_stats.seq, &st, &g_stats.p, sizeof(st), 4, NULL)) {
                printf("[%7.3f] STAT  law %-6s mode %-4s d %5.2f m | loops %llu misses %llu worst %.0f us p95 %.0f us\n",
                       now, law_name(st.law), mode_name(st.mode), st.d_m,
                       (unsigned long long)st.stats.loops, (unsigned long long)st.stats.misses,
                       st.stats.worst_late_ns / 1e3, st.stats.p95_late_ns / 1e3);
            }
            last_stats_print = now;
        }
        fflush(stdout);
        nanosleep(&nap, NULL);
    }
    return NULL;
}

int audio_start(const audio_cfg_t *cfg)
{
    g_cfg = *cfg;
    atomic_store(&g_run, 1);
    return pthread_create(&g_thread, NULL, audio_main, NULL);
}

void audio_stop(void)
{
    atomic_store(&g_run, 0);
    pthread_join(g_thread, NULL);
}
