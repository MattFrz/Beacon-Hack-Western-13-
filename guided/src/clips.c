/* clips.c: load the WAV clips in sounds/ and map cues to playlists. See clips.h. */
#include "clips.h"
#include "beacon.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_CLIPS 160

static clip_t g_clips[MAX_CLIPS];
static int g_n;

/* One file stem per beacon_clip id (matches sounds/make_clips.py). */
static const char *const k_stem[BEACON_CLIP_COUNT] = {
    [BEACON_CLIP_NUM_0] = "num_0", [BEACON_CLIP_NUM_1] = "num_1", [BEACON_CLIP_NUM_2] = "num_2",
    [BEACON_CLIP_NUM_3] = "num_3", [BEACON_CLIP_NUM_4] = "num_4", [BEACON_CLIP_NUM_5] = "num_5",
    [BEACON_CLIP_NUM_6] = "num_6", [BEACON_CLIP_NUM_7] = "num_7", [BEACON_CLIP_NUM_8] = "num_8",
    [BEACON_CLIP_NUM_9] = "num_9",
    [BEACON_CLIP_METRE] = "metre", [BEACON_CLIP_METRES] = "metres",
    [BEACON_CLIP_AHEAD] = "ahead", [BEACON_CLIP_LEFT] = "left", [BEACON_CLIP_RIGHT] = "right",
    [BEACON_CLIP_UP] = "up", [BEACON_CLIP_DOWN] = "down",
    [BEACON_CLIP_LOST_TARGET] = "lost_target",
    [BEACON_CLIP_STOPPING] = "stopping",
    [BEACON_CLIP_NOT_SEEN] = "not_seen",
    [BEACON_CLIP_CANNOT_RETRACE] = "cannot_retrace",
    [BEACON_CLIP_DID_NOT_CATCH] = "did_not_catch",
    [BEACON_CLIP_CANNOT_HELP] = "cannot_help",
    [BEACON_CLIP_ABOUT] = "about",
    [BEACON_CLIP_A_LITTLE] = "a_little",
    [BEACON_CLIP_YOU_ARE_BACK] = "you_are_back",
    [BEACON_CLIP_TURN_LEFT] = "turn_left",
    [BEACON_CLIP_TURN_RIGHT] = "turn_right",
    [BEACON_CLIP_FOUND_IT] = "found_it",
    [BEACON_CLIP_DIR_AHEAD] = "dir_ahead", [BEACON_CLIP_DIR_SLEFT] = "dir_sleft",
    [BEACON_CLIP_DIR_LEFT] = "dir_left", [BEACON_CLIP_DIR_SRIGHT] = "dir_sright",
    [BEACON_CLIP_DIR_RIGHT] = "dir_right",
    [BEACON_CLIP_WITHIN_REACH] = "within_reach",
    [BEACON_CLIP_STEPS_1] = "steps_1", [BEACON_CLIP_STEPS_2] = "steps_2",
    [BEACON_CLIP_STEPS_3] = "steps_3", [BEACON_CLIP_STEPS_4] = "steps_4",
    [BEACON_CLIP_STEPS_5] = "steps_5", [BEACON_CLIP_STEPS_FAR] = "steps_far",
    [BEACON_CLIP_TURN_SLIGHT_LEFT] = "turn_slight_left",
    [BEACON_CLIP_TURN_SLIGHT_RIGHT] = "turn_slight_right",
    [BEACON_CLIP_TURN_AROUND] = "turn_around",
};

static const char *const k_names[] = { "bottle", "can", "keys", "phone", "box", "mouse" };
static const char *const k_dirs[] = { "ahead", "sleft", "left", "sright", "right" };

static uint32_t rd32(const unsigned char *p) { return p[0] | p[1] << 8 | p[2] << 16 | (uint32_t)p[3] << 24; }
static uint16_t rd16(const unsigned char *p) { return (uint16_t)(p[0] | p[1] << 8); }

/* Minimal reader for 16-bit mono PCM WAV at 16 kHz (what make_clips.py writes). */
static int load_one(const char *dir, const char *stem)
{
    if (g_n >= MAX_CLIPS)
        return 0;
    char path[512];
    snprintf(path, sizeof(path), "%s/%s.wav", dir, stem);
    FILE *f = fopen(path, "rb");
    if (!f)
        return 0;
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char *buf = (size > 44 && size < 4 * 1024 * 1024) ? malloc((size_t)size) : NULL;
    int ok = buf && fread(buf, 1, (size_t)size, f) == (size_t)size;
    fclose(f);
    if (!ok || memcmp(buf, "RIFF", 4) || memcmp(buf + 8, "WAVE", 4)) {
        free(buf);
        return 0;
    }
    uint16_t fmt = 0, ch = 0, bits = 0;
    uint32_t rate = 0;
    long pos = 12;
    while (pos + 8 <= size) {
        uint32_t len = rd32(buf + pos + 4);
        if (!memcmp(buf + pos, "fmt ", 4) && len >= 16) {
            fmt = rd16(buf + pos + 8);
            ch = rd16(buf + pos + 10);
            rate = rd32(buf + pos + 12);
            bits = rd16(buf + pos + 22);
        } else if (!memcmp(buf + pos, "data", 4)) {
            if (fmt != 1 || ch != 1 || bits != 16 || rate != CLIPS_RATE) {
                fprintf(stderr, "guided: %s is not 16 kHz mono 16-bit PCM, skipped\n", path);
                break;
            }
            size_t bytes = len <= (uint32_t)(size - pos - 8) ? len : (size_t)(size - pos - 8);
            clip_t *c = &g_clips[g_n];
            c->n = bytes / 2;
            c->samples = malloc(c->n * sizeof(int16_t));
            if (!c->samples)
                break;
            for (size_t i = 0; i < c->n; ++i)
                c->samples[i] = (int16_t)rd16(buf + pos + 8 + 2 * i);
            snprintf(c->name, sizeof(c->name), "%s", stem);
            g_n++;
            free(buf);
            return 1;
        }
        pos += 8 + len + (len & 1);
    }
    free(buf);
    return 0;
}

int clips_load(const char *dir)
{
    char stem[40];
    for (int i = 0; i < BEACON_CLIP_COUNT; ++i)
        if (k_stem[i])
            load_one(dir, k_stem[i]);
    for (size_t i = 0; i < sizeof(k_names) / sizeof(k_names[0]); ++i) {
        snprintf(stem, sizeof(stem), "name_%s", k_names[i]);
        load_one(dir, stem);
        snprintf(stem, sizeof(stem), "next_to_%s", k_names[i]);
        load_one(dir, stem);
        for (int d = 0; d < 5; ++d) {
            snprintf(stem, sizeof(stem), "intro_%s_%s_c", k_names[i], k_dirs[d]);
            load_one(dir, stem);
            snprintf(stem, sizeof(stem), "intro_%s_%s", k_names[i], k_dirs[d]);
            load_one(dir, stem);
        }
    }
    for (int m = 1; m <= 9; ++m) {
        snprintf(stem, sizeof(stem), "about_%d_metre%s", m, m == 1 ? "" : "s");
        load_one(dir, stem);
    }
    load_one(dir, "a_little_left");
    load_one(dir, "a_little_right");
    return g_n;
}

const clip_t *clips_find(const char *stem)
{
    for (int i = 0; i < g_n; ++i)
        if (!strcmp(g_clips[i].name, stem))
            return &g_clips[i];
    return NULL;
}

int clips_playlist(const uint16_t *ids, int n_ids, const char *label,
                   const clip_t **out, int max_out)
{
    int n = 0;
    char stem[48];
    for (int i = 0; i < n_ids && n < max_out; ++i) {
        uint16_t id = ids[i];
        const clip_t *c = NULL;

        /* "about" + number + metre(s) -> one phrase clip */
        if (id == BEACON_CLIP_ABOUT && i + 2 < n_ids &&
            ids[i + 1] >= BEACON_CLIP_NUM_1 && ids[i + 1] <= BEACON_CLIP_NUM_9 &&
            (ids[i + 2] == BEACON_CLIP_METRE || ids[i + 2] == BEACON_CLIP_METRES)) {
            int m = ids[i + 1] - BEACON_CLIP_NUM_0;
            snprintf(stem, sizeof(stem), "about_%d_metre%s", m, m == 1 ? "" : "s");
            if ((c = clips_find(stem)) != NULL) {
                out[n++] = c;
                i += 2;
                continue;
            }
        }
        /* "a little" + left/right -> one phrase clip */
        if (id == BEACON_CLIP_A_LITTLE && i + 1 < n_ids &&
            (ids[i + 1] == BEACON_CLIP_LEFT || ids[i + 1] == BEACON_CLIP_RIGHT)) {
            c = clips_find(ids[i + 1] == BEACON_CLIP_LEFT ? "a_little_left" : "a_little_right");
            if (c) {
                out[n++] = c;
                i += 1;
                continue;
            }
        }
        /* "Your keys are slightly to your left[,|.]": per object and direction */
        if (id >= BEACON_CLIP_INTRO_CONT_AHEAD && id <= BEACON_CLIP_INTRO_RIGHT) {
            int cont = id <= BEACON_CLIP_INTRO_CONT_RIGHT;
            int d = cont ? id - BEACON_CLIP_INTRO_CONT_AHEAD : id - BEACON_CLIP_INTRO_AHEAD;
            if (label && label[0]) {
                snprintf(stem, sizeof(stem), "intro_%s_%s%s", label, k_dirs[d], cont ? "_c" : "");
                c = clips_find(stem);
            }
            if (!c) /* unknown object: say the direction on its own */
                c = clips_find(k_stem[BEACON_CLIP_DIR_AHEAD + d]);
            if (c)
                out[n++] = c;
            continue;
        }
        if (id == BEACON_CLIP_OBJECT_NAME || id == BEACON_CLIP_NEXT_TO) {
            if (label && label[0]) {
                snprintf(stem, sizeof(stem), "%s_%s",
                         id == BEACON_CLIP_NEXT_TO ? "next_to" : "name", label);
                c = clips_find(stem);
            }
        } else if (id < BEACON_CLIP_COUNT && k_stem[id]) {
            c = clips_find(k_stem[id]);
        }
        if (c)
            out[n++] = c;
    }
    return n;
}
