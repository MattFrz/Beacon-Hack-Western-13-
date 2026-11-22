/* audio_out.c: see audio_out.h. */
#include "audio_out.h"
#include "beacon.h"

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#if defined(__QNX__) && !defined(BEACON_NO_IOAUDIO)
#include <sys/asoundlib.h>
#endif

enum { OUT_NONE, OUT_WAV, OUT_QNX, OUT_FIFO };
static int g_kind = OUT_NONE;

/* ------------------------------------------------------------------ Bluetooth PCM pipe
 * Combadge-HTN/qnx-bluetooth reads raw PCM from a named pipe (audio.pcm):
 * 44.1 kHz, stereo, signed 16-bit little-endian, and sends it to the A2DP
 * speaker. We upsample our 16 kHz blocks with linear interpolation. If the
 * Bluetooth program is not running yet, we keep retrying once a second and
 * stay silent meanwhile; guided never waits on it. */
#define FIFO_RATE 44100
static char     g_fifo_path[512];
static int      g_fifo_fd = -1;
static uint64_t g_fifo_retry_ns;
static double   g_rs_pos;
static int16_t  g_rs_prev[2];

static void fifo_try_open(void)
{
    uint64_t now = beacon_now_ns();
    if (now < g_fifo_retry_ns)
        return;
    g_fifo_retry_ns = now + 1000000000ull;
    int fd = open(g_fifo_path, O_WRONLY | O_NONBLOCK); /* ENXIO until a reader exists */
    if (fd < 0)
        return;
    int fl = fcntl(fd, F_GETFL);
    fcntl(fd, F_SETFL, fl & ~O_NONBLOCK);  /* blocking writes: never drop samples mid-word */
    g_fifo_fd = fd;
    g_rs_pos = 0.0;
    fprintf(stderr, "guided: streaming to Bluetooth PCM pipe %s\n", g_fifo_path);
}

static void fifo_write(const int16_t *in, size_t frames)
{
    if (g_fifo_fd < 0) {
        fifo_try_open();
        if (g_fifo_fd < 0)
            return;
    }
    int16_t out[2 * (AUDIO_FRAME * FIFO_RATE / AUDIO_RATE + 4)];
    const double step = (double)AUDIO_RATE / FIFO_RATE;
    size_t n = 0;
    while (g_rs_pos <= (double)frames - 1.0 && n < sizeof(out) / sizeof(out[0]) / 2) {
        int i0 = (int)(g_rs_pos < 0 ? -1 : g_rs_pos);
        double frac = g_rs_pos - i0;
        for (int c = 0; c < 2; ++c) {
            double a = i0 < 0 ? g_rs_prev[c] : in[2 * i0 + c];
            double b = in[2 * (i0 + 1) + c];
            out[2 * n + c] = (int16_t)(a + (b - a) * frac);
        }
        n++;
        g_rs_pos += step;
    }
    g_rs_pos -= (double)frames;
    g_rs_prev[0] = in[2 * (frames - 1)];
    g_rs_prev[1] = in[2 * (frames - 1) + 1];

    const char *p = (const char *)out;
    size_t left = n * 4;
    while (left > 0) {
        ssize_t w = write(g_fifo_fd, p, left);
        if (w < 0 && errno == EINTR)
            continue;
        if (w <= 0) { /* reader went away (EPIPE): drop and retry later */
            close(g_fifo_fd);
            g_fifo_fd = -1;
            fprintf(stderr, "guided: Bluetooth PCM pipe closed, will retry\n");
            return;
        }
        p += w;
        left -= (size_t)w;
    }
}

/* ------------------------------------------------------------------ WAV file */
static FILE *g_wav;
static uint32_t g_wav_bytes;

static void put32(unsigned char *p, uint32_t v) { p[0] = v; p[1] = v >> 8; p[2] = v >> 16; p[3] = v >> 24; }
static void put16(unsigned char *p, uint16_t v) { p[0] = v; p[1] = v >> 8; }

static void wav_header(uint32_t data_bytes)
{
    unsigned char h[44];
    memcpy(h, "RIFF", 4);
    put32(h + 4, 36 + data_bytes);
    memcpy(h + 8, "WAVEfmt ", 8);
    put32(h + 16, 16);
    put16(h + 20, 1);
    put16(h + 22, AUDIO_CHANNELS);
    put32(h + 24, AUDIO_RATE);
    put32(h + 28, AUDIO_RATE * AUDIO_CHANNELS * 2);
    put16(h + 32, AUDIO_CHANNELS * 2);
    put16(h + 34, 16);
    memcpy(h + 36, "data", 4);
    put32(h + 40, data_bytes);
    fseek(g_wav, 0, SEEK_SET);
    fwrite(h, 1, sizeof(h), g_wav);
}

/* ------------------------------------------------------------------ QNX io-audio */
#if defined(__QNX__) && !defined(BEACON_NO_IOAUDIO)
/* Classic io-audio plugin API (as in QNX's `wave` sample). Untested on the
 * loaner Pi: verify with a USB headset or speaker during bring-up. */
static snd_pcm_t *g_pcm;

static int qnx_open(void)
{
    int card = -1, dev = 0;
    if (snd_pcm_open_preferred(&g_pcm, &card, &dev, SND_PCM_OPEN_PLAYBACK) < 0)
        return -1;
    snd_pcm_channel_params_t pp;
    memset(&pp, 0, sizeof(pp));
    pp.mode = SND_PCM_MODE_BLOCK;
    pp.channel = SND_PCM_CHANNEL_PLAYBACK;
    pp.start_mode = SND_PCM_START_FULL;
    pp.stop_mode = SND_PCM_STOP_STOP;
    pp.buf.block.frag_size = AUDIO_FRAME * AUDIO_CHANNELS * 2;
    pp.buf.block.frags_max = 4;   /* ~40 ms queued at most: short delay */
    pp.buf.block.frags_min = 1;
    pp.format.interleave = 1;
    pp.format.rate = AUDIO_RATE;
    pp.format.voices = AUDIO_CHANNELS;
    pp.format.format = SND_PCM_SFMT_S16_LE;
    if (snd_pcm_plugin_params(g_pcm, &pp) < 0 ||
        snd_pcm_plugin_prepare(g_pcm, SND_PCM_CHANNEL_PLAYBACK) < 0) {
        snd_pcm_close(g_pcm);
        g_pcm = NULL;
        return -1;
    }
    return 0;
}

static void qnx_write(const int16_t *buf, size_t frames)
{
    size_t bytes = frames * AUDIO_CHANNELS * 2;
    int n = snd_pcm_plugin_write(g_pcm, buf, bytes);
    if (n < (int)bytes) {
        /* underrun or error: re-prepare and drop this block, never stall */
        snd_pcm_channel_status_t st;
        memset(&st, 0, sizeof(st));
        st.channel = SND_PCM_CHANNEL_PLAYBACK;
        if (snd_pcm_plugin_status(g_pcm, &st) == 0 &&
            (st.status == SND_PCM_STATUS_UNDERRUN || st.status == SND_PCM_STATUS_READY))
            snd_pcm_plugin_prepare(g_pcm, SND_PCM_CHANNEL_PLAYBACK);
    }
}
#endif

/* ------------------------------------------------------------------ interface */
int audio_out_open(const char *spec)
{
    g_kind = OUT_NONE;
    if (!spec || !spec[0] || !strcmp(spec, "none"))
        return 0;
    if (!strncmp(spec, "fifo:", 5)) {
        snprintf(g_fifo_path, sizeof(g_fifo_path), "%s", spec + 5);
        g_fifo_fd = -1;
        g_fifo_retry_ns = 0;
        g_kind = OUT_FIFO;
        fifo_try_open();
        if (g_fifo_fd < 0)
            fprintf(stderr, "guided: waiting for the Bluetooth PCM reader on %s\n", g_fifo_path);
        return 0;
    }
    if (!strcmp(spec, "qnx")) {
#if defined(__QNX__) && !defined(BEACON_NO_IOAUDIO)
        if (qnx_open() == 0) {
            g_kind = OUT_QNX;
            return 0;
        }
        fprintf(stderr, "guided: cannot open the QNX audio device; is a USB headset or speaker plugged in?\n");
#else
        fprintf(stderr, "guided: --audio qnx needs QNX io-audio (not in this build); use fifo:PATH for the JBL\n");
#endif
        return -1;
    }
    g_wav = fopen(spec, "wb");
    if (!g_wav) {
        perror("guided: audio file");
        return -1;
    }
    g_wav_bytes = 0;
    wav_header(0);
    g_kind = OUT_WAV;
    return 0;
}

/* Only the QNX sound device sets the pace. The Bluetooth pipe follows the
 * clock too: a reader that drains faster than real time must never make us
 * race ahead, and a slow one just blocks this (low-priority) thread briefly. */
int audio_out_paced(void) { return g_kind == OUT_QNX; }

void audio_out_write(const int16_t *buf, size_t frames)
{
    if (g_kind == OUT_FIFO) {
        fifo_write(buf, frames);
    } else if (g_kind == OUT_WAV) {
        fwrite(buf, AUDIO_CHANNELS * 2, frames, g_wav);
        g_wav_bytes += (uint32_t)(frames * AUDIO_CHANNELS * 2);
    }
#if defined(__QNX__) && !defined(BEACON_NO_IOAUDIO)
    else if (g_kind == OUT_QNX) {
        qnx_write(buf, frames);
    }
#endif
}

void audio_out_close(void)
{
    if (g_kind == OUT_FIFO && g_fifo_fd >= 0) {
        close(g_fifo_fd);
        g_fifo_fd = -1;
    }
    if (g_kind == OUT_WAV && g_wav) {
        wav_header(g_wav_bytes);
        fclose(g_wav);
        g_wav = NULL;
    }
#if defined(__QNX__) && !defined(BEACON_NO_IOAUDIO)
    if (g_kind == OUT_QNX && g_pcm) {
        snd_pcm_plugin_flush(g_pcm, SND_PCM_CHANNEL_PLAYBACK);
        snd_pcm_close(g_pcm);
        g_pcm = NULL;
    }
#endif
    g_kind = OUT_NONE;
}
