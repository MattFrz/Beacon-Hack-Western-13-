/* law.c: guided's decision logic. See law.h and spec §6, §7, §9, §10. */
#include "law.h"

#include <math.h>
#include <string.h>

#define REACH_ENTER_M      0.50f  /* §10: enter when |d| <= 0.50 m ...   */
#define REACH_ENTER_FRAMES 3      /*      ... for 3 synthesizer frames   */
#define REACH_EXIT_M       0.70f  /* §10: exit when |d| >= 0.70 m        */
#define TONE_BELOW_M       0.15f  /* §10: continuous tone below 0.15 m   */
#define TICK_FAR_M         0.60f
#define TICK_FAR_MS        800.0f
#define TICK_NEAR_MS       80.0f
#define D_EMA_TAU_S        0.200f /* §10: 200 ms EMA of d                */
#define PAN_FULL_M         0.25f  /* lateral offset that pans fully      */
#define WALK_STABLE_NS     600000000ull  /* a change must hold this long before we say it */
#define WALK_MIN_GAP_NS    2500000000ull /* never two cues closer than this */
#define WALK_REMIND_NS     8000000000ull /* full reminder when nothing changed */
#define WALK_REMIND_NEAR_NS 4000000000ull /* "within reach" and no hand yet: remind sooner */
#define RETURN_REPEAT_NS   4000000000ull
#define TURN_STABLE_NS     400000000ull
#define TURN_MIN_GAP_NS    2000000000ull
#define TURN_REMIND_NS     5000000000ull
#define TURN_AFTER_NS      700000000ull  /* out of view this long (not a one-frame blink) before "turn ..." */
#define LOST_REPLAY_NS     8000000000ull  /* "I lost the target" again at most this often (§10) */
#define LANDMARK_GAP_NS    8000000000ull /* "It's next to the mug." at most this often */
#define CHIME_GAP_NS       3000000000ull /* one "facing it" chime, not a burst */
#define DIR_AHEAD_DEG      8.0f   /* within this: "straight ahead" */
#define DIR_SLIGHT_DEG     22.0f  /* within this: "slightly to your left/right" */
#define WITHIN_REACH_M     0.60f
#define RETURN_POP_M       0.60f  /* §10: pop crumb within ~0.6 m        */
#define RETURN_LIVE_M      3.0f   /* §10: named object within ~3 m ends RETURN */
#define HOLD_TICK_SLOWDOWN 1.6f
#define TURN_DEG           25.0f  /* target this far off-axis and out of view: "turn left/right" */
#define POSE_FRESH_NS      1000000000ull /* the map is only trusted with a fresh pose */
#define FOUND_HOLD_NS      600000000ull  /* tone this long before "found it" */
#define FOUND_REARM_M      0.30f  /* hand moved this far away: allow another "found it" */
#define STEP_M             0.70f  /* one walking step */
#define LANDMARK_M         0.30f  /* another object this close to the target: "It's next to ..." */
#define ORIENT_ON_DEG      15.0f  /* pips start when the target is this far to one side */
#define FACING_DEG         10.0f  /* within this you are facing it: chime, pips stop */
#define PIP_SLOW_MS        700.0f /* pip gap with the target at 90 deg or more ... */
#define PIP_FAST_MS        150.0f /* ... down to this as it comes in front */
#define PIP_BURST_NS       6000000000ull /* pips run this long after each spoken cue, then rest */

/* ------------------------------------------------------------------ small math */
static float v3_norm(const float v[3]) { return sqrtf(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]); }

static float clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }

/* T is row-major 4x4 T_world_from_cam (rigid). p_cam = R^T (p_world - t). */
static void cam_from_world(const float T[16], const float pw[3], float pc[3])
{
    float d[3] = { pw[0] - T[3], pw[1] - T[7], pw[2] - T[11] };
    pc[0] = T[0] * d[0] + T[4] * d[1] + T[8] * d[2];
    pc[1] = T[1] * d[0] + T[5] * d[1] + T[9] * d[2];
    pc[2] = T[2] * d[0] + T[6] * d[1] + T[10] * d[2];
}

static void translation(const float T[16], float t[3]) { t[0] = T[3]; t[1] = T[7]; t[2] = T[11]; }

/* ------------------------------------------------------------------ output helpers */
static guided_cmd_t *push_cmd(guided_out_t *out, int kind)
{
    if (out->n_cmds >= GUIDED_MAX_CMDS)
        return NULL;
    guided_cmd_t *c = &out->cmds[out->n_cmds++];
    memset(c, 0, sizeof(*c));
    c->kind = (uint8_t)kind;
    return c;
}

static guided_cmd_t *say(guided_out_t *out, int priority, const uint16_t *clips, int n, const char *name)
{
    guided_cmd_t *c = push_cmd(out, GUIDED_CMD_SAY);
    if (!c)
        return NULL;
    c->priority = (uint8_t)priority;
    if (n > GUIDED_MAX_CLIPS)
        n = GUIDED_MAX_CLIPS;
    for (int i = 0; i < n; ++i)
        c->clips[i] = clips[i];
    c->n_clips = (uint8_t)n;
    if (name)
        strncpy(c->name, name, BEACON_NAME_LEN - 1);
    return c;
}

static void say1(guided_out_t *out, int priority, uint16_t clip)
{
    say(out, priority, &clip, 1, NULL);
}

/* WALK templates and NACK clips are kept for REPEAT (§10). */
static void say_remember(guided_state_t *st, guided_out_t *out, int priority,
                         const uint16_t *clips, int n, const char *name)
{
    guided_cmd_t *c = say(out, priority, clips, n, name);
    if (c) {
        st->last_say = *c;
        st->have_last_say = 1;
    }
}

static void nack(guided_state_t *st, guided_out_t *out, int priority, uint16_t clip)
{
    say_remember(st, out, priority, &clip, 1, NULL);
}

static void tone_off(guided_state_t *st, guided_out_t *out)
{
    if (st->tone_on) {
        push_cmd(out, GUIDED_CMD_TONE_OFF);
        st->tone_on = 0;
    }
}

static void leave_reach(guided_state_t *st, guided_out_t *out)
{
    st->in_reach = 0;
    st->reach_enter_n = 0;
    st->found = 0;
    st->walk_started = 0;  /* back to walking: start with a full sentence */
    tone_off(st, out);
}

/* Where the bound target is right now, from the session map (spec §7 Range 3).
 * Only with a valid, fresh pose in the same epoch: a dead percept stops the
 * pose, so this goes false and the wearer hears LOST, never a guessed turn. */
static int memory_bearing(const guided_state_t *st, const beacon_percept_block_t *p,
                          uint64_t now, float pc[3])
{
    if (!p->pose.valid || p->pose.pose_epoch != st->target.pose_epoch)
        return 0;
    if (now > p->pose.t_ns && now - p->pose.t_ns > POSE_FRESH_NS)
        return 0;
    cam_from_world(p->pose.T_world_from_cam, st->target.xyz_world, pc);
    return 1;
}

/* ------------------------------------------------------------------ public helpers */
void guided_default_cfg(guided_cfg_t *cfg)
{
    cfg->metres_enabled = 0;           /* off until the tape check passes (§11) */
    cfg->hand_conf_min = 0.5f;
    cfg->hand_stale_ns = 500000000ull; /* 0.5 s */
    cfg->orient_pips = 1;
}

void guided_init(guided_state_t *st, const guided_cfg_t *cfg)
{
    memset(st, 0, sizeof(*st));
    st->cfg = *cfg;
    st->prev_mode = BEACON_MODE_NONE;
}

float guided_tick_interval_ms(float d)
{
    if (d <= TONE_BELOW_M)
        return 0.0f;
    if (d >= TICK_FAR_M)
        return TICK_FAR_MS;
    float f = (d - TONE_BELOW_M) / (TICK_FAR_M - TONE_BELOW_M);
    return TICK_NEAR_MS + f * (TICK_FAR_MS - TICK_NEAR_MS);
}

/* ------------------------------------------------------------------ walk sentences
 * Google Maps style: one full sentence, then short updates only when the
 * direction or distance actually changes, and a full reminder now and then.
 *   full:  "Your keys are slightly to your left," + "about two metres away."
 *          (no metres before the tape check: "Your keys are slightly to your left.")
 *   short: "To your left." and/or "About one metre away."
 * No up/down: the chest camera looks down at the table, so it would be noise. */
int guided_dir_cat(float az_deg)
{
    float a = fabsf(az_deg);
    if (a < DIR_AHEAD_DEG)
        return DIR_AHEAD;
    if (a < DIR_SLIGHT_DEG)
        return az_deg < 0 ? DIR_SLEFT : DIR_SRIGHT;
    return az_deg < 0 ? DIR_LEFT : DIR_RIGHT;
}

/* Qualitative distance: "within arm's reach", "about N steps ahead" (a step is
 * ~0.7 m), "more than five steps away". No metres or centimetres spoken. */
uint16_t guided_dist_clip(float range_m)
{
    if (range_m <= WITHIN_REACH_M)
        return BEACON_CLIP_WITHIN_REACH;
    int steps = (int)(range_m / STEP_M + 0.5f);
    if (steps < 1)
        steps = 1;
    if (steps > 5)
        return BEACON_CLIP_STEPS_FAR;
    return (uint16_t)(BEACON_CLIP_STEPS_1 + steps - 1);
}

float guided_pip_interval_ms(float az_deg)
{
    float a = clampf(fabsf(az_deg), FACING_DEG, 90.0f);
    return PIP_FAST_MS + (a - FACING_DEG) / (90.0f - FACING_DEG) * (PIP_SLOW_MS - PIP_FAST_MS);
}

/* dist == 0: say no distance (metres not allowed yet). */
int guided_walk_cue(int dir, uint16_t dist, int full, int say_dir, int say_dist,
                    uint16_t *clips, int max)
{
    int n = 0;
    if (max < 2)
        return 0;
    if (full) {
        if (dist) {
            clips[n++] = (uint16_t)(BEACON_CLIP_INTRO_CONT_AHEAD + dir);
            clips[n++] = dist;
        } else {
            clips[n++] = (uint16_t)(BEACON_CLIP_INTRO_AHEAD + dir);
        }
        return n;
    }
    if (say_dir)
        clips[n++] = (uint16_t)(BEACON_CLIP_DIR_AHEAD + dir);
    if (say_dist && dist)
        clips[n++] = dist;
    return n;
}

/* ------------------------------------------------------------------ bind (§9) */
static void copy_target_from(beacon_target_t *t, const beacon_object_t *o)
{
    t->id = o->id;
    memcpy(t->name, o->name, BEACON_NAME_LEN);
    t->name[BEACON_NAME_LEN - 1] = '\0';
    memcpy(t->xyz_cam, o->xyz_cam, sizeof(t->xyz_cam));
    memcpy(t->xyz_world, o->xyz_world, sizeof(t->xyz_world));
    t->conf = o->conf;
    t->last_seen_ns = o->last_seen_ns;
    t->frame_id = o->frame_id;
    t->pose_epoch = o->pose_epoch;
    t->in_latest_boxes = o->in_latest_boxes;
    t->bound = 1;
}

/* First candidate (in order, skipping those in skip_mask) with a stored row
 * seen within 1.5 s. Ties on a name: nearest in cam if live, else nearest in
 * world if pose is valid. Returns the candidate index bound, or -1. */
static int bind_target(guided_state_t *st, const beacon_percept_block_t *p,
                       const beacon_intent_t *in, uint64_t now, uint32_t skip_mask)
{
    float me_w[3];
    translation(p->pose.T_world_from_cam, me_w);

    for (uint32_t c = 0; c < in->n_candidates && c < BEACON_MAX_CANDIDATES; ++c) {
        if (skip_mask & (1u << c))
            continue;
        const char *want = in->candidates[c];
        int best = -1;
        float best_d = 1e30f;
        for (int i = 0; i < BEACON_MAX_OBJECTS; ++i) {
            const beacon_object_t *o = &p->objects[i];
            if (!o->used || strncmp(o->name, want, BEACON_NAME_LEN) != 0)
                continue;
            uint64_t age = now > o->last_seen_ns ? now - o->last_seen_ns : 0;
            if (age >= BEACON_MEMORY_BIND_MAX_NS)
                continue; /* too old for a NEW bind (§9: 20 s memory window) */
            float d;
            if (o->in_latest_boxes) {
                d = v3_norm(o->xyz_cam);
            } else if (p->pose.valid && o->pose_epoch == p->pose.pose_epoch) {
                float v[3] = { o->xyz_world[0] - me_w[0], o->xyz_world[1] - me_w[1], o->xyz_world[2] - me_w[2] };
                d = 1000.0f + v3_norm(v); /* live rows win over remembered rows */
            } else {
                d = 1e20f;
            }
            if (d < best_d) {
                best_d = d;
                best = i;
            }
        }
        if (best >= 0) {
            copy_target_from(&st->target, &p->objects[best]);
            return (int)c;
        }
    }
    return -1;
}

/* Keep the bound target's geometry in step with its objects[] row. */
static void refresh_target(guided_state_t *st, const beacon_percept_block_t *p)
{
    if (!st->target.bound)
        return;
    for (int i = 0; i < BEACON_MAX_OBJECTS; ++i) {
        const beacon_object_t *o = &p->objects[i];
        if (o->used && o->id == st->target.id &&
            strncmp(o->name, st->target.name, BEACON_NAME_LEN) == 0) {
            copy_target_from(&st->target, o);
            return;
        }
    }
    /* Row evicted: keep the last copy; it ages into HOLD then LOST. */
    st->target.in_latest_boxes = 0;
}

static void reset_guidance(guided_state_t *st)
{
    st->in_reach = 0;
    st->reach_enter_n = 0;
    st->found = 0;
    st->turning = 0;
    st->walk_started = 0;
    st->change_ns = 0;
    st->d_valid = 0;
    st->last_walk_ns = 0;
    st->last_landmark_ns = 0;
    st->lost_said = 0;
    st->last_lost_say_ns = 0;
    st->prev_mode = BEACON_MODE_NONE;
}

/* ------------------------------------------------------------------ intents */
static void handle_intent(guided_state_t *st, const beacon_percept_block_t *p,
                          const beacon_intent_t *in, uint64_t now, guided_out_t *out)
{
    switch (in->kind) {
    case BEACON_INTENT_FIND:
    case BEACON_INTENT_GO: {
        st->stopped = 0;
        st->returning = 0;
        leave_reach(st, out);
        reset_guidance(st);
        st->bind_intent = *in;
        st->have_bind_intent = 1;
        st->tried_mask = 0;
        int c = bind_target(st, p, in, now, 0);
        if (c < 0) {
            st->target.bound = 0;
            nack(st, out, 1, BEACON_CLIP_NOT_SEEN);
        } else {
            st->tried_mask |= 1u << c;
        }
        break;
    }
    case BEACON_INTENT_REJECT: {
        /* "Not that one": drop this bind, try the next unused candidate name
         * still in objects[] and younger than 1.5 s. Never leave the set. */
        push_cmd(out, GUIDED_CMD_FLUSH_SPEECH);
        leave_reach(st, out);
        reset_guidance(st);
        st->returning = 0;
        int c = -1;
        if (st->have_bind_intent && st->target.bound)
            c = bind_target(st, p, &st->bind_intent, now, st->tried_mask);
        if (c < 0) {
            st->target.bound = 0;
            nack(st, out, 1, BEACON_CLIP_NOT_SEEN);
        } else {
            st->tried_mask |= 1u << c;
        }
        break;
    }
    case BEACON_INTENT_REPEAT:
        /* Replay the last WALK template or NACK clip; no new inference (§10). */
        if (st->have_last_say) {
            guided_cmd_t *c = push_cmd(out, GUIDED_CMD_SAY);
            if (c)
                *c = st->last_say;
        } else {
            say1(out, 0, BEACON_CLIP_NOT_SEEN);
        }
        break;
    case BEACON_INTENT_RETURN:
        st->stopped = 0;
        leave_reach(st, out);
        if (!p->pose.valid || p->crumb_n == 0) {
            nack(st, out, 1, BEACON_CLIP_CANNOT_RETRACE);
            st->returning = 0;
        } else {
            st->returning = 1;
            st->ret_start_i = p->crumb_i;
            st->ret_total = p->crumb_n;
            st->ret_k = 0;
            st->ret_refused_said = 0;
            st->last_walk_ns = 0;
        }
        break;
    case BEACON_INTENT_STOP:
        push_cmd(out, GUIDED_CMD_FLUSH_SPEECH);
        leave_reach(st, out);
        st->target.bound = 0;
        st->returning = 0;
        st->stopped = 1;
        reset_guidance(st);
        say1(out, 1, BEACON_CLIP_STOPPING);
        break;
    case BEACON_INTENT_NACK_UNHEARD:
        nack(st, out, 0, BEACON_CLIP_DID_NOT_CATCH);
        break;
    case BEACON_INTENT_NACK_UNSEEN:
        nack(st, out, 0, BEACON_CLIP_NOT_SEEN);
        break;
    case BEACON_INTENT_NACK_CANT:
        nack(st, out, 0, BEACON_CLIP_CANNOT_HELP);
        break;
    default:
        break;
    }
}

static int is_new_intent(guided_state_t *st, const beacon_intent_t *in)
{
    if (!in || in->kind == BEACON_INTENT_NONE)
        return 0;
    if (st->seen_intent && in->utterance_id == st->last_utterance_id &&
        in->t_ns == st->last_intent_t_ns)
        return 0;
    st->seen_intent = 1;
    st->last_utterance_id = in->utterance_id;
    st->last_intent_t_ns = in->t_ns;
    return 1;
}

/* ------------------------------------------------------------------ REACH distance (§7 Range 1) */
/* 1 = fresh d, 2 = cannot measure this frame (hold last d), 0 = no usable hand. */
static int measure_d(const guided_state_t *st, const beacon_percept_block_t *p, uint64_t now,
                     float *d, float *lat, float *amp)
{
    const beacon_hand_t *h = &p->hand;
    (void)now;
    if (!h->valid || h->conf < st->cfg.hand_conf_min)
        return 0;
    /* Stale relative to the newest vision bundle, not the wall clock: if
     * percept dies, the whole bundle ages and mode (LIVE/HOLD/LOST) handles
     * it, so REACH holds its last d instead of dropping to WALK (§10). */
    if (st->target.last_seen_ns > h->t_ns &&
        st->target.last_seen_ns - h->t_ns > st->cfg.hand_stale_ns)
        return 0;

    float tc[3];
    if (h->frame_id == st->target.frame_id) {
        memcpy(tc, st->target.xyz_cam, sizeof(tc));
    } else if (p->pose.valid && h->pose_epoch == st->target.pose_epoch &&
               p->pose.pose_epoch == st->target.pose_epoch) {
        cam_from_world(p->pose.T_world_from_cam, st->target.xyz_world, tc);
    } else {
        return 2; /* not the same camera frame and no shared world: do not subtract */
    }
    float v[3] = { tc[0] - h->xyz_cam[0], tc[1] - h->xyz_cam[1], tc[2] - h->xyz_cam[2] };
    float n = v3_norm(v);
    *d = n;
    *lat = v[0];
    /* §10: max(0.25, cos(theta)): off-axis stays audible, never silent */
    *amp = n > 1e-4f ? clampf(v[2] / n, 0.25f, 1.0f) : 1.0f;
    return 1;
}

/* ------------------------------------------------------------------ the step */
/* "It's next to the mug.": another object in the same frame right beside the
 * target. Said after a full sentence only. */
static void say_landmark(guided_state_t *st, const beacon_percept_block_t *p, guided_out_t *out,
                         uint64_t now)
{
    if (st->last_landmark_ns && now - st->last_landmark_ns < LANDMARK_GAP_NS)
        return;
    const float *t = st->target.xyz_cam;
    for (int i = 0; i < BEACON_MAX_OBJECTS; ++i) {
        const beacon_object_t *o = &p->objects[i];
        if (!o->used || !o->in_latest_boxes || o->id == st->target.id ||
            !strncmp(o->name, st->target.name, BEACON_NAME_LEN))
            continue;
        float dx = o->xyz_cam[0] - t[0], dy = o->xyz_cam[1] - t[1], dz = o->xyz_cam[2] - t[2];
        if (sqrtf(dx * dx + dy * dy + dz * dz) <= LANDMARK_M) {
            uint16_t c = BEACON_CLIP_NEXT_TO;
            say(out, 0, &c, 1, o->name);
            st->last_landmark_ns = now;
            return;
        }
    }
}

/* Turn-toward pips (ADDITION): soft, panned to the target, faster as it comes in
 * front; one chime once you face it, then quiet. Never in the frame we speak
 * (and the audio thread drops a pip while the voice plays). */
static void orient(guided_state_t *st, guided_out_t *out, float az, uint64_t now, int spoke)
{
    if (!st->cfg.orient_pips)
        return;
    float a = fabsf(az);
    for (int i = 0; i < out->n_cmds; ++i) /* any speech this frame (cue, REPEAT, landmark) */
        spoke |= out->cmds[i].kind == GUIDED_CMD_SAY;
    if (!st->orienting) {
        if (a < ORIENT_ON_DEG)
            return;
        st->orienting = 1;
        st->next_pip_ns = now + 700000000ull; /* let the spoken cue go first */
        st->pips_until_ns = now + PIP_BURST_NS;
    }
    if (a < FACING_DEG) {
        st->orienting = 0;
        if (!st->last_chime_ns || now - st->last_chime_ns >= CHIME_GAP_NS) {
            push_cmd(out, GUIDED_CMD_CHIME);
            st->last_chime_ns = now;
        }
        return;
    }
    if (spoke) {
        st->next_pip_ns = now + 700000000ull;
        st->pips_until_ns = now + PIP_BURST_NS;
        return;
    }
    if (now >= st->next_pip_ns && now < st->pips_until_ns) {
        guided_cmd_t *c = push_cmd(out, GUIDED_CMD_PIP);
        if (c) {
            c->pan = clampf(az / 45.0f, -1.0f, 1.0f);
            c->amp = 1.0f;
        }
        st->next_pip_ns = now + (uint64_t)(guided_pip_interval_ms(az) * 1e6f);
    }
}

void guided_step(guided_state_t *st, const beacon_percept_block_t *p,
                 const beacon_intent_t *in, uint64_t now, guided_out_t *out)
{
    memset(out, 0, sizeof(*out));
    out->d_m = -1.0f;

    if (is_new_intent(st, in))
        handle_intent(st, p, in, now, out);

    refresh_target(st, p);
    uint64_t live_max = beacon_live_max_ns(p->health.p95_vision_ns);
    int mode = beacon_mode(st->target.bound, st->target.in_latest_boxes,
                           st->target.last_seen_ns, now, live_max);
    out->mode = mode;

    /* A live named object within ~3 m ends RETURN and takes over (§10). */
    if (st->returning && mode == BEACON_MODE_LIVE && v3_norm(st->target.xyz_cam) < RETURN_LIVE_M)
        st->returning = 0;

    /* ---------------- RETURN */
    if (st->returning) {
        out->law = BEACON_LAW_RETURN;
        if (!p->pose.valid) {
            if (!st->ret_refused_said) {
                say1(out, 1, BEACON_CLIP_CANNOT_RETRACE);
                st->ret_refused_said = 1;
            }
            return;
        }
        st->ret_refused_said = 0;
        float me[3];
        translation(p->pose.T_world_from_cam, me);
        while (st->ret_k < st->ret_total) {
            uint32_t idx = (st->ret_start_i + 2u * BEACON_MAX_CRUMBS - 1u - st->ret_k) % BEACON_MAX_CRUMBS;
            float cw[3];
            translation(p->crumbs[idx].T_world_from_cam, cw);
            float dx = cw[0] - me[0], dz = cw[2] - me[2];
            if (hypotf(dx, dz) >= RETURN_POP_M) {
                if (st->last_walk_ns == 0 || now - st->last_walk_ns >= RETURN_REPEAT_NS) {
                    float pc[3];
                    cam_from_world(p->pose.T_world_from_cam, cw, pc);
                    int dir = guided_dir_cat(atan2f(pc[0], pc[2]) * 57.2957795f);
                    uint16_t dist = st->cfg.metres_enabled ? guided_dist_clip(hypotf(pc[0], pc[2])) : 0;
                    uint16_t clips[GUIDED_MAX_CLIPS];
                    int n = guided_walk_cue(dir, dist, 0, 1, 1, clips, GUIDED_MAX_CLIPS);
                    say_remember(st, out, 0, clips, n, NULL);
                    st->last_walk_ns = now;
                }
                return;
            }
            st->ret_k++;
        }
        st->returning = 0;
        say1(out, 1, BEACON_CLIP_YOU_ARE_BACK);
        out->law = BEACON_LAW_NONE;
        return;
    }

    /* ---------------- STOP / nothing bound */
    if (!st->target.bound) {
        out->law = st->stopped ? BEACON_LAW_STOP : BEACON_LAW_NONE;
        leave_reach(st, out);
        st->prev_mode = mode;
        return;
    }

    /* ---------------- out of view, but the map knows where it is: turn */
    if (mode == BEACON_MODE_LIVE && st->turning) {
        st->turning = 0;
        st->walk_started = 0; /* back in view: a full sentence right away */
    }
    if (mode != BEACON_MODE_LIVE && !st->in_reach) {
        float pc[3];
        if (memory_bearing(st, p, now, pc)) {
            float az = atan2f(pc[0], pc[2]) * 57.2957795f;
            float a = fabsf(az);
            /* a real camera blinks: one missing frame is not "out of view" */
            int gone = now - st->target.last_seen_ns >= TURN_AFTER_NS;
            if (a > TURN_DEG && (st->turning || gone)) {
                out->law = BEACON_LAW_WALK;
                uint16_t clip = a > 135.0f ? BEACON_CLIP_TURN_AROUND
                              : a > 70.0f ? (az < 0 ? BEACON_CLIP_TURN_LEFT : BEACON_CLIP_TURN_RIGHT)
                              : (az < 0 ? BEACON_CLIP_TURN_SLIGHT_LEFT : BEACON_CLIP_TURN_SLIGHT_RIGHT);
                int speak = 0;
                if (!st->turning) {               /* just left the view: say it now (spaced) */
                    st->turning = 1;
                    st->turn_clip = 0;
                    st->turn_change_ns = now;
                    speak = !st->last_walk_ns || now - st->last_walk_ns >= TURN_MIN_GAP_NS;
                } else if (clip != st->turn_clip) { /* e.g. "turn left" -> "a little to your left" */
                    if (!st->turn_change_ns)
                        st->turn_change_ns = now;
                    speak = now - st->turn_change_ns >= TURN_STABLE_NS &&
                            now - st->last_walk_ns >= TURN_MIN_GAP_NS;
                } else {
                    st->turn_change_ns = 0;
                    speak = now - st->last_walk_ns >= TURN_REMIND_NS;
                }
                if (speak) {
                    say_remember(st, out, 0, &clip, 1, NULL);
                    st->turn_clip = clip;
                    st->turn_change_ns = 0;
                    st->last_walk_ns = now;
                }
                orient(st, out, az, now, speak);
                /* lost_said is NOT cleared here: a pose that flickers stale/fresh would
                 * otherwise say "I lost the target" again and again. Only seeing the
                 * target again (below) re-arms it. */
                st->prev_mode = mode;
                return;
            }
        }
    }

    /* ---------------- LOST (§6, §10): unique cue, never a number.
     * Said once immediately, then at most every LOST_REPLAY_NS: a flickering
     * view (YOLO conf hovering, scene being arranged) flips mode in and out
     * of LOST every record, and re-saying it per entry tells the wearer
     * nothing they can act on. */
    if (mode == BEACON_MODE_LOST) {
        out->law = BEACON_LAW_LOST;
        if (st->in_reach)
            leave_reach(st, out);
        if (!st->lost_said &&
            (now >= st->last_lost_say_ns + LOST_REPLAY_NS || !st->last_lost_say_ns)) {
            push_cmd(out, GUIDED_CMD_FLUSH_SPEECH);
            say1(out, 1, BEACON_CLIP_LOST_TARGET);
            st->lost_said = 1;
            st->last_lost_say_ns = now;
        }
        st->d_valid = 0;
        st->prev_mode = mode;
        return;
    }
    if (st->prev_mode == BEACON_MODE_LOST) {
        st->lost_said = 0;
        st->walk_started = 0; /* target is back: a full sentence right away */
    }

    /* ---------------- REACH distance */
    float d = 0, lat = 0, amp = 1.0f;
    int m = (mode == BEACON_MODE_LIVE) ? measure_d(st, p, now, &d, &lat, &amp) : 2;
    int hand_ok = (m != 0);
    if (m == 1) {
        if (!st->d_valid) {
            st->d_ema = d;
            st->lat_ema = lat;
        } else {
            float dt = (float)(now - st->d_t_ns) * 1e-9f;
            float a = 1.0f - expf(-dt / D_EMA_TAU_S);
            st->d_ema += a * (d - st->d_ema);
            st->lat_ema += a * (lat - st->lat_ema);
        }
        st->amp = amp;
        st->d_valid = 1;
        st->d_t_ns = now;
    }

    /* ---------------- REACH enter / exit with hysteresis (§10) */
    if (!st->in_reach) {
        if (mode == BEACON_MODE_LIVE && m == 1 && st->d_ema <= REACH_ENTER_M) {
            if (++st->reach_enter_n >= REACH_ENTER_FRAMES) {
                st->in_reach = 1;
                st->orienting = 0;
                st->next_tick_ns = now;
                push_cmd(out, GUIDED_CMD_FLUSH_SPEECH); /* duck WALK the moment REACH enters */
            }
        } else {
            st->reach_enter_n = 0; /* never start REACH from HOLD */
        }
    } else {
        int hold = (mode == BEACON_MODE_HOLD);
        if (!hold && (!hand_ok || (st->d_valid && st->d_ema >= REACH_EXIT_M)))
            leave_reach(st, out);
    }

    if (st->in_reach && st->d_valid) {
        int hold = (mode == BEACON_MODE_HOLD);
        out->law = BEACON_LAW_REACH;
        out->d_m = st->d_ema;
        out->pan = clampf(st->lat_ema / PAN_FULL_M, -1.0f, 1.0f);
        if (st->found && st->d_ema > FOUND_REARM_M)
            st->found = 0;               /* hand moved away: guide again */
        if (st->found) {                 /* already confirmed: stay quiet */
            st->prev_mode = mode;
            return;
        }
        float ms = guided_tick_interval_ms(st->d_ema);
        if (ms <= 0.0f && !hold) {
            out->continuous = 1;
            if (!st->tone_on) {
                guided_cmd_t *c = push_cmd(out, GUIDED_CMD_TONE_ON);
                if (c) { c->pan = out->pan; c->amp = 1.0f; }
                st->tone_on = 1;
                st->tone_since_ns = now;
            } else if (now - st->tone_since_ns >= FOUND_HOLD_NS) {
                tone_off(st, out);       /* hand stayed on it: confirm out loud */
                say1(out, 1, BEACON_CLIP_FOUND_IT);
                st->found = 1;
                out->continuous = 0;
            }
        } else {
            tone_off(st, out);
            if (ms <= 0.0f)
                ms = TICK_NEAR_MS;
            if (hold)
                ms *= HOLD_TICK_SLOWDOWN;
            out->tick_hz = 1000.0f / ms;
            if (now >= st->next_tick_ns) {
                guided_cmd_t *c = push_cmd(out, GUIDED_CMD_TICK);
                if (c) {
                    c->pan = out->pan;
                    c->amp = st->amp;
                    c->dark = (uint8_t)hold;
                }
                st->next_tick_ns = now + (uint64_t)(ms * 1e6f);
            }
        }
        st->prev_mode = mode;
        return;
    }

    /* ---------------- WALK (§10): spoken, from LIVE only, no ticks */
    out->law = BEACON_LAW_WALK;
    if (st->d_valid)
        out->d_m = st->d_ema;
    if (mode == BEACON_MODE_LIVE) {
        const float *pc = st->target.xyz_cam;
        int dir = guided_dir_cat(atan2f(pc[0], pc[2]) * 57.2957795f);
        uint16_t dist = guided_dist_clip(v3_norm(pc));
        /* "within reach" is not a number, so it is allowed before the tape check */
        if (!st->cfg.metres_enabled && dist != BEACON_CLIP_WITHIN_REACH)
            dist = 0;
        uint16_t clips[GUIDED_MAX_CLIPS];
        int n = 0, full = 0;
        if (!st->walk_started) {
            /* new target: now; back in view after a turn or LOST: not on top of the last cue */
            if (!st->last_walk_ns || now - st->last_walk_ns >= WALK_MIN_GAP_NS) {
                n = guided_walk_cue(dir, dist, 1, 1, 1, clips, GUIDED_MAX_CLIPS);
                full = 1;
                st->walk_started = 1;
            }
        } else {
            int dir_changed = dir != st->cue_dir, dist_changed = dist != st->cue_dist;
            if (dir_changed || dist_changed) {
                if (!st->change_ns)
                    st->change_ns = now;
            } else {
                st->change_ns = 0;
            }
            uint64_t remind = (dist == BEACON_CLIP_WITHIN_REACH && !hand_ok)
                            ? WALK_REMIND_NEAR_NS : WALK_REMIND_NS;
            if (st->change_ns && now - st->change_ns >= WALK_STABLE_NS &&
                now - st->last_walk_ns >= WALK_MIN_GAP_NS)
                n = guided_walk_cue(dir, dist, 0, dir_changed, dist_changed, clips, GUIDED_MAX_CLIPS);
            else if (now - st->last_walk_ns >= remind) {
                n = guided_walk_cue(dir, dist, 1, 1, 1, clips, GUIDED_MAX_CLIPS);
                full = 1;
            }
        }
        if (n > 0) {
            say_remember(st, out, 0, clips, n, st->target.name);
            if (full)
                say_landmark(st, p, out, now);
            st->cue_dir = dir;
            st->cue_dist = dist;
            st->change_ns = 0;
            st->last_walk_ns = now;
        }
        orient(st, out, atan2f(pc[0], pc[2]) * 57.2957795f, now, n > 0);
    }
    /* HOLD in WALK: say nothing new; no stale metres. */
    st->prev_mode = mode;
}
