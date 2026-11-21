/* audio.h: guided's audio thread (spec §5.1 "Audio and piezo").
 *
 * The 16 ms thread never blocks on audio. It hands commands over two
 * non-blocking paths:
 *   - speech: a 32-slot single-producer/single-consumer ring. If it is full
 *     the new clip is dropped (speech is the first thing to drop).
 *   - ticks / tone: a newest-wins slot. A tick is never queued behind speech.
 * The audio thread runs at a lower priority (BEACON_PRIO_AUDIO) and does the
 * blocking writes. On a laptop it prints what the wearer would hear.
 */
#ifndef GUIDED_AUDIO_H
#define GUIDED_AUDIO_H

#include "law.h"

typedef struct {
    int         verbose;     /* print every tick, not a summary */
    const char *sounds_dir;  /* WAV folder (QNX playback, later) */
    uint64_t    t0_ns;       /* for printed timestamps */
} audio_cfg_t;

int  audio_start(const audio_cfg_t *cfg);
void audio_stop(void);

/* Called from the 16 ms thread only. Never blocks. */
void audio_submit(const guided_cmd_t *cmd);

/* Stats for the printer (copied by the 16 ms thread, read by the audio thread). */
void audio_publish_stats(const beacon_guided_stats_t *stats, int law, int mode, float d_m);

uint64_t audio_dropped_speech(void);

#endif /* GUIDED_AUDIO_H */
