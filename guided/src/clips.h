/* clips.h: the pre-rendered voice clips in sounds/ (16 kHz mono 16-bit WAV).
 *
 * Loaded once at startup, never on the 16 ms thread. A spoken cue from the
 * law (a list of beacon_clip ids) becomes a short playlist of clips, using
 * the whole-phrase clips when they match so it flows like one sentence:
 *   OBJECT_NAME ABOUT NUM_2 METRES A_LITTLE LEFT
 *     -> name_keys.wav, about_2_metres.wav, a_little_left.wav
 */
#ifndef GUIDED_CLIPS_H
#define GUIDED_CLIPS_H

#include <stddef.h>
#include <stdint.h>

#define CLIPS_RATE 16000
#define CLIPS_MAX_PLAYLIST 12

typedef struct {
    char     name[40];
    int16_t *samples;
    size_t   n;
} clip_t;

/* Loads every .wav it knows about from dir. Returns how many loaded;
 * missing files are skipped (the cue just plays without them). */
int clips_load(const char *dir);

/* Finds a loaded clip by file stem ("about_2_metres"), or NULL. */
const clip_t *clips_find(const char *stem);

/* Builds the playlist for one cue. label is the target's name for
 * BEACON_CLIP_OBJECT_NAME. Returns the number of entries written. */
int clips_playlist(const uint16_t *ids, int n_ids, const char *label,
                   const clip_t **out, int max_out);

#endif /* GUIDED_CLIPS_H */
