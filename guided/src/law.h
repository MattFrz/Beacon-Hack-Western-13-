/* law.h: guided's decision logic (spec §6 mode, §9 bind, §10 laws).
 *
 * Pure: no I/O, no clocks, no shm. guided_step() takes the latest percept
 * and voiced copies plus "now" and returns what to say or tick this frame.
 * That keeps it unit-testable on a laptop and safe on the 16 ms thread.
 */
#ifndef GUIDED_LAW_H
#define GUIDED_LAW_H

#include "beacon.h"

#define GUIDED_MAX_CLIPS 12
#define GUIDED_MAX_CMDS  4

enum guided_cmd_kind {
    GUIDED_CMD_NONE = 0,
    GUIDED_CMD_SAY,          /* play clips[] in order */
    GUIDED_CMD_TICK,         /* one REACH tick */
    GUIDED_CMD_TONE_ON,      /* continuous REACH tone */
    GUIDED_CMD_TONE_OFF,
    GUIDED_CMD_FLUSH_SPEECH, /* drop queued speech (REACH entered, STOP, LOST) */
    GUIDED_CMD_PIP,          /* ADDITION: soft turn-toward pip, panned to the target */
    GUIDED_CMD_CHIME         /* ADDITION: "now facing it" after turning */
};

typedef struct {
    uint8_t  kind;           /* enum guided_cmd_kind */
    uint8_t  priority;       /* 1 = cut off whatever is playing */
    uint8_t  dark;           /* HOLD tick: darker, slower */
    uint8_t  n_clips;
    float    pan;            /* -1 left .. +1 right */
    float    amp;            /* 0..1 */
    uint16_t clips[GUIDED_MAX_CLIPS];      /* enum beacon_clip */
    char     name[BEACON_NAME_LEN];        /* label for BEACON_CLIP_OBJECT_NAME */
} guided_cmd_t;

typedef struct {
    int          law;        /* enum beacon_law */
    int          mode;       /* enum beacon_mode */
    float        d_m;        /* hand-to-target after EMA, < 0 = none */
    float        pan;
    float        tick_hz;    /* 0 = no ticks */
    int          continuous;
    int          n_cmds;
    guided_cmd_t cmds[GUIDED_MAX_CMDS];
} guided_out_t;

typedef struct {
    int      metres_enabled; /* spec §11: only after the tape-measure check passes */
    float    hand_conf_min;
    uint64_t hand_stale_ns;  /* hand older than the target's newest box by this = "hand lost" */
    int      orient_pips;    /* ADDITION: pips while turning toward the target (--no-orient-pips) */
} guided_cfg_t;

typedef struct {
    guided_cfg_t    cfg;
    beacon_target_t target;

    /* intents */
    int      seen_intent;
    uint32_t last_utterance_id;
    uint64_t last_intent_t_ns;
    int      stopped;

    /* REJECT: the FIND/GO request we bound from, and which candidates were tried */
    int             have_bind_intent;
    beacon_intent_t bind_intent;
    uint32_t        tried_mask;

    /* REPEAT: last WALK template or NACK clip, replayed as is (§10) */
    int          have_last_say;
    guided_cmd_t last_say;

    /* RETURN */
    int      returning;
    uint32_t ret_start_i, ret_total, ret_k;
    int      ret_refused_said;

    /* REACH */
    int      in_reach;
    int      reach_enter_n;
    int      d_valid;
    float    d_ema;
    float    lat_ema;
    float    amp;
    uint64_t d_t_ns;
    uint64_t next_tick_ns;
    int      tone_on;
    uint64_t tone_since_ns;  /* when the continuous tone started */
    int      found;          /* "found it" said; quiet until the hand moves away */
    int      turning;        /* giving "turn left/right" from the session map */
    uint16_t turn_clip;      /* last turn instruction spoken */
    uint64_t turn_change_ns; /* when a different turn instruction first applied */

    /* WALK speaking rules */
    int      walk_started;   /* full sentence said for this target */
    int      cue_dir;        /* direction last spoken */
    uint16_t cue_dist;       /* distance clip last spoken (0 = none) */
    uint64_t change_ns;      /* when the direction/distance first differed */

    /* turn-toward pips (ADDITION) */
    int      orienting;      /* target off to one side: pips until we face it */
    uint64_t next_pip_ns;
    uint64_t pips_until_ns;  /* pips stop after a few seconds; the next spoken cue restarts them */

    /* WALK and mode bookkeeping */
    uint64_t last_walk_ns;
    int      prev_mode;
    int      lost_said;
} guided_state_t;

void guided_default_cfg(guided_cfg_t *cfg);
void guided_init(guided_state_t *st, const guided_cfg_t *cfg);

/* p: newest clean copy of the percept block (never NULL; zeroed if none yet).
 * in: newest clean copy of the intent, or NULL if voiced never wrote one.
 * The LIVE window is beacon_live_max_ns(p->health.p95_vision_ns) (spec §6). */
void guided_step(guided_state_t *st, const beacon_percept_block_t *p,
                 const beacon_intent_t *in, uint64_t now_ns, guided_out_t *out);

/* Exposed for tests. */
enum { DIR_AHEAD = 0, DIR_SLEFT, DIR_LEFT, DIR_SRIGHT, DIR_RIGHT };
float    guided_tick_interval_ms(float d_m);  /* 0 = continuous tone */
int      guided_dir_cat(float az_deg);        /* + is right */
uint16_t guided_dist_clip(float range_m);     /* BEACON_CLIP_WITHIN_REACH / STEPS_* */
float    guided_pip_interval_ms(float az_deg); /* faster as the target comes in front */
int      guided_walk_cue(int dir, uint16_t dist, int full, int say_dir, int say_dist,
                         uint16_t *clips, int max);

#endif /* GUIDED_LAW_H */
