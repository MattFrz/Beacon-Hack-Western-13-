/* audio.c: guided's audio thread. See audio.h.
 *
 * Mixes the voice clips (clips.c), REACH ticks and the continuous tone into
 * 10 ms stereo blocks and hands them to audio_out.c: a WAV file or nothing on
 * a laptop, the QNX sound device or the Bluetooth PCM pipe on the Pi.
 * Also prints what the wearer hears.
 */
#include "audio.h"
#include "audio_out.h"
#include "clips.h"
#include "platform.h"

#include <math.h>
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
    [BEACON_CLIP_TURN_LEFT] = "turn left.",
    [BEACON_CLIP_TURN_RIGHT] = "turn right.",
    [BEACON_CLIP_FOUND_IT] = "found it.",
    [BEACON_CLIP_INTRO_CONT_AHEAD] = "straight ahead,", [BEACON_CLIP_INTRO_CONT_SLEFT] = "slightly to your left,",
    [BEACON_CLIP_INTRO_CONT_LEFT] = "to your left,", [BEACON_CLIP_INTRO_CONT_SRIGHT] = "slightly to your right,",
    [BEACON_CLIP_INTRO_CONT_RIGHT] = "to your right,",
    [BEACON_CLIP_INTRO_AHEAD] = "straight ahead.", [BEACON_CLIP_INTRO_SLEFT] = "slightly to your left.",
    [BEACON_CLIP_INTRO_LEFT] = "to your left.", [BEACON_CLIP_INTRO_SRIGHT] = "slightly to your right.",
    [BEACON_CLIP_INTRO_RIGHT] = "to your right.",
    [BEACON_CLIP_DIR_AHEAD] = "straight ahead.", [BEACON_CLIP_DIR_SLEFT] = "slightly to your left.",
    [BEACON_CLIP_DIR_LEFT] = "to your left.", [BEACON_CLIP_DIR_SRIGHT] = "slightly to your right.",
    [BEACON_CLIP_DIR_RIGHT] = "to your right.",
    [BEACON_CLIP_WITHIN_REACH] = "within arm's reach.",
    [BEACON_CLIP_STEPS_1] = "about one step ahead.", [BEACON_CLIP_STEPS_2] = "about two steps ahead.",
    [BEACON_CLIP_STEPS_3] = "about three steps ahead.", [BEACON_CLIP_STEPS_4] = "about four steps ahead.",
    [BEACON_CLIP_STEPS_5] = "about five steps ahead.", [BEACON_CLIP_STEPS_FAR] = "more than five steps away.",
    [BEACON_CLIP_TURN_SLIGHT_LEFT] = "turn a little to your left.",
    [BEACON_CLIP_TURN_SLIGHT_RIGHT] = "turn a little to your right.",
    [BEACON_CLIP_TURN_AROUND] = "turn around.",
    [BEACON_CLIP_NEXT_TO] = "it's next to the",
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
    case GUIDED_CMD_PIP:
    case GUIDED_CMD_CHIME:
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
        uint16_t id = c->clips[i];
        const char *w = (id == BEACON_CLIP_OBJECT_NAME) ? c->name
                      : (id < BEACON_CLIP_COUNT && k_clip_words[id] ? k_clip_words[id] : "?");
        if (id >= BEACON_CLIP_INTRO_CONT_AHEAD && id <= BEACON_CLIP_INTRO_RIGHT)
            n += (size_t)snprintf(line + n, sizeof(line) - n, "%s%s: %s", i ? " " : "", c->name, w);
        else if (id == BEACON_CLIP_NEXT_TO)
            n += (size_t)snprintf(line + n, sizeof(line) - n, "%s%s %s.", i ? " " : "", w, c->name);
        else
            n += (size_t)snprintf(line + n, sizeof(line) - n, "%s%s", i ? " " : "", w);
    }
    printf("[%7.3f] SAY%s  \"%s\"\n", secs(), c->priority ? "!" : " ", line);
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

/* ------------------------------------------------------------------ synth */
#define SPEECH_GAIN 0.90f
#define TICK_GAIN   0.40f
#define TONE_GAIN   0.22f
#define TICK_LEN    (AUDIO_RATE / 50)   /* 20 ms click */
#define PIP_GAIN    0.32f               /* turn-toward pips: soft, under the voice level */
#define PIP_HZ      600.0f              /* lower and rounder than the 880 Hz reach tick */
#define PIP_LEN     (AUDIO_RATE / 33)   /* 30 ms */
#define CHIME_LEN   (AUDIO_RATE / 5)    /* 200 ms: two notes, "you are facing it" */
#define RAMP        (AUDIO_RATE / 333)  /* 3 ms fade in and out, no pops */
#define MAX_QUEUED  8

typedef struct { const clip_t *list[CLIPS_MAX_PLAYLIST]; int n; } playlist_t;

static struct {
    playlist_t queue[MAX_QUEUED];   /* cues waiting to be spoken */
    int        q_head, q_len;
    playlist_t cur;                 /* cue being spoken */
    int        cur_i;
    size_t     cur_pos;
    int        tick_left, tick_len;  /* samples left / total in the current click */
    float      tick_freq, tick_freq2, tick_amp, tick_pan, tick_phase; /* freq2: 2nd half */
    int        tone_on;
    float      tone_pan, tone_phase, tone_level;
    int        chime_pending;       /* waits for the voice to finish */
} S;

static void speech_clear(void)
{
    S.q_len = 0;
    S.cur.n = 0;
    S.cur_i = 0;
    S.cur_pos = 0;
}

static void speech_push(const guided_cmd_t *c)
{
    playlist_t pl;
    pl.n = clips_playlist(c->clips, c->n_clips, c->name, pl.list, CLIPS_MAX_PLAYLIST);
    if (pl.n == 0)
        return;
    if (c->priority)           /* LOST, STOP, NACKs cut whatever is playing */
        speech_clear();
    if (S.q_len == MAX_QUEUED) { /* full: drop the oldest waiting cue */
        S.q_head = (S.q_head + 1) % MAX_QUEUED;
        S.q_len--;
    }
    S.queue[(S.q_head + S.q_len) % MAX_QUEUED] = pl;
    S.q_len++;
}

static float speech_next(void)
{
    for (;;) {
        if (S.cur_i < S.cur.n) {
            const clip_t *c = S.cur.list[S.cur_i];
            if (S.cur_pos < c->n)
                return c->samples[S.cur_pos++] / 32768.0f;
            S.cur_i++;
            S.cur_pos = 0;
            continue;
        }
        if (S.q_len == 0)
            return 0.0f;
        S.cur = S.queue[S.q_head];
        S.q_head = (S.q_head + 1) % MAX_QUEUED;
        S.q_len--;
        S.cur_i = 0;
        S.cur_pos = 0;
    }
}

static void pan_gains(float pan, float *l, float *r)
{
    float a = (pan + 1.0f) * 0.78539816f; /* equal-power pan, pi/4 at centre */
    *l = cosf(a);
    *r = sinf(a);
}

static void render_block(int16_t *out, int frames)
{
    const float two_pi = 6.2831853f;
    for (int i = 0; i < frames; ++i) {
        float sp = speech_next() * SPEECH_GAIN;
        float l = sp, r = sp;
        if (S.tick_left > 0) {
            int k = S.tick_len - S.tick_left;
            float env = 1.0f;
            if (k < RAMP)
                env = (float)k / RAMP;
            else if (S.tick_left < RAMP)
                env = (float)S.tick_left / RAMP;
            float v = sinf(S.tick_phase) * env * S.tick_amp * TICK_GAIN, gl, gr;
            pan_gains(S.tick_pan, &gl, &gr);
            l += v * gl;
            r += v * gr;
            S.tick_phase += two_pi * (k < S.tick_len / 2 ? S.tick_freq : S.tick_freq2) / AUDIO_RATE;
            S.tick_left--;
        }
        float target = S.tone_on ? 1.0f : 0.0f; /* fade the tone in and out */
        S.tone_level += (target - S.tone_level) * 0.01f;
        if (S.tone_level > 0.001f) {
            float v = sinf(S.tone_phase) * S.tone_level * TONE_GAIN, gl, gr;
            pan_gains(S.tone_pan, &gl, &gr);
            l += v * gl;
            r += v * gr;
            S.tone_phase += two_pi * 1320.0f / AUDIO_RATE;
        }
        if (S.tick_phase > two_pi)
            S.tick_phase -= two_pi;
        if (S.tone_phase > two_pi)
            S.tone_phase -= two_pi;
        l = l > 1.0f ? 1.0f : (l < -1.0f ? -1.0f : l);
        r = r > 1.0f ? 1.0f : (r < -1.0f ? -1.0f : r);
        out[2 * i] = (int16_t)(l * 32767.0f);
        out[2 * i + 1] = (int16_t)(r * 32767.0f);
    }
}

static void *audio_main(void *arg)
{
    (void)arg;
    platform_set_thread_sched(BEACON_PRIO_AUDIO, BEACON_RUNMASK_CORE0);

    int loaded = clips_load(g_cfg.sounds_dir);
    fprintf(stderr, "guided: %d voice clips loaded from %s\n", loaded, g_cfg.sounds_dir);
    if (audio_out_open(g_cfg.out) != 0)
        audio_out_open("none");

    uint32_t seen_gen = 0;
    double last_tick_print = -1.0, last_stats_print = 0.0;
    int ticks_since_print = 0;
    int16_t block[AUDIO_FRAME * AUDIO_CHANNELS];
    const uint64_t block_ns = 1000000000ull * AUDIO_FRAME / AUDIO_RATE;
    uint64_t next = beacon_now_ns();

    while (atomic_load(&g_run)) {
        /* flush first, then speech */
        uint32_t t = atomic_load_explicit(&g_tail, memory_order_relaxed);
        uint32_t f = atomic_load_explicit(&g_flush_upto, memory_order_acquire);
        if ((int32_t)(f - t) > 0) {
            atomic_store_explicit(&g_tail, f, memory_order_release);
            t = f;
            speech_clear();
        }
        uint32_t h = atomic_load_explicit(&g_head, memory_order_acquire);
        while (t != h) {
            guided_cmd_t c = g_ring[t % SPEECH_SLOTS];
            t++;
            atomic_store_explicit(&g_tail, t, memory_order_release);
            print_say(&c);
            speech_push(&c);
        }

        /* ticks and tone: newest wins */
        tick_payload_t tk;
        if (beacon_seq_read(&g_tick.seq, &tk, &g_tick.p, sizeof(tk), 4, NULL) && tk.gen != seen_gen) {
            uint32_t missed = tk.gen - seen_gen - 1;
            seen_gen = tk.gen;
            if (tk.cmd.kind == GUIDED_CMD_TONE_ON) {
                S.tone_on = 1;
                S.tone_pan = tk.cmd.pan;
                printf("[%7.3f] TONE  on   pan %+.2f\n", secs(), tk.cmd.pan);
            } else if (tk.cmd.kind == GUIDED_CMD_TONE_OFF) {
                S.tone_on = 0;
                printf("[%7.3f] TONE  off\n", secs());
            } else if (tk.cmd.kind == GUIDED_CMD_PIP) {
                /* never over the voice: a pip while Beacon talks is dropped */
                if (S.cur_i >= S.cur.n && S.q_len == 0 && S.tick_left == 0) {
                    S.tick_left = S.tick_len = PIP_LEN;
                    S.tick_phase = 0.0f;
                    S.tick_pan = tk.cmd.pan;
                    S.tick_amp = PIP_GAIN / TICK_GAIN;
                    S.tick_freq = S.tick_freq2 = PIP_HZ;
                    if (g_cfg.verbose)
                        printf("[%7.3f] PIP   pan %+.2f\n", secs(), tk.cmd.pan);
                }
            } else if (tk.cmd.kind == GUIDED_CMD_CHIME) {
                S.chime_pending = 1;
            } else {
                S.tick_left = S.tick_len = TICK_LEN;
                S.tick_phase = 0.0f;
                S.tick_pan = tk.cmd.pan;
                S.tick_amp = tk.cmd.amp * (tk.cmd.dark ? 0.6f : 1.0f);
                S.tick_freq = S.tick_freq2 = tk.cmd.dark ? 523.0f : 880.0f; /* HOLD ticks are lower */
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

        /* the "facing it" chime plays once the voice is quiet */
        if (S.chime_pending && S.cur_i >= S.cur.n && S.q_len == 0) {
            S.chime_pending = 0;
            S.tick_left = S.tick_len = CHIME_LEN;
            S.tick_phase = 0.0f;
            S.tick_pan = 0.0f;
            S.tick_amp = 0.8f;
            S.tick_freq = 880.0f;   /* rising two-note chime */
            S.tick_freq2 = 1320.0f;
            printf("[%7.3f] CHIME facing the target\n", secs());
        }

        /* stats every 5 s, from this thread, never from the 16 ms thread */
        double now_s = secs();
        if (now_s - last_stats_print >= 5.0) {
            stats_payload_t st;
            if (beacon_seq_read(&g_stats.seq, &st, &g_stats.p, sizeof(st), 4, NULL)) {
                printf("[%7.3f] STAT  law %-6s mode %-4s d %5.2f m | loops %llu misses %llu worst %.0f us p95 %.0f us\n",
                       now_s, law_name(st.law), mode_name(st.mode), st.d_m,
                       (unsigned long long)st.stats.loops, (unsigned long long)st.stats.misses,
                       st.stats.worst_late_ns / 1e3, st.stats.p95_late_ns / 1e3);
            }
            last_stats_print = now_s;
        }
        fflush(stdout);

        /* one 10 ms block; a device or pipe paces us, otherwise the clock does */
        render_block(block, AUDIO_FRAME);
        audio_out_write(block, AUDIO_FRAME);
        if (!audio_out_paced()) {
            next += block_ns;
            uint64_t now_ns = beacon_now_ns();
            if (next > now_ns) {
                struct timespec ts = { (time_t)(next / 1000000000ull), (long)(next % 1000000000ull) };
                clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, NULL);
            } else if (now_ns - next > 100000000ull) {
                next = now_ns; /* fell far behind (laptop hiccup): do not burst */
            }
        }
    }
    audio_out_close();
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
