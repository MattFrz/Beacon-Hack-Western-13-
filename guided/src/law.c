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
#define WALK_REPEAT_NS     3000000000ull /* §10: repeat ~every 3 s       */
#define WALK_REPEAT_NEAR_NS 1500000000ull /* faster repeats when close   */
#define WALK_NEAR_M        0.60f
#define RETURN_POP_M       0.60f  /* §10: pop crumb within ~0.6 m        */
#define RETURN_LIVE_M      3.0f   /* §10: named object within ~3 m ends RETURN */
#define HOLD_TICK_SLOWDOWN 1.6f

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

static void say(guided_out_t *out, int priority, const uint16_t *clips, int n, const char *name)
{
    guided_cmd_t *c = push_cmd(out, GUIDED_CMD_SAY);
    if (!c)
        return;
    c->priority = (uint8_t)priority;
    if (n > GUIDED_MAX_CLIPS)
        n = GUIDED_MAX_CLIPS;
    for (int i = 0; i < n; ++i)
        c->clips[i] = clips[i];
    c->n_clips = (uint8_t)n;
    if (name)
        strncpy(c->name, name, BEACON_NAME_LEN - 1);
}

static void say1(guided_out_t *out, int priority, uint16_t clip)
{
    say(out, priority, &clip, 1, NULL);
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
    tone_off(st, out);
}

/* ------------------------------------------------------------------ public helpers */
void guided_default_cfg(guided_cfg_t *cfg)
{
    cfg->metres_enabled = 0;           /* off until the tape check passes (§11) */
    cfg->hand_conf_min = 0.5f;
    cfg->hand_stale_ns = 500000000ull; /* 0.5 s */
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

/* "<name>. About two metres, a little left." built from clips (§10 WALK). */
int guided_walk_clips(const float pc[3], int metres_ok, int with_name, uint16_t *clips, int max)
{
    int n = 0;
#define ADD(c) do { if (n < max) clips[n++] = (uint16_t)(c); } while (0)
    if (with_name)
        ADD(BEACON_CLIP_OBJECT_NAME);

    float range = v3_norm(pc);
    if (metres_ok && range >= 0.5f) {
        int m = (int)lroundf(range);
        if (m < 1) m = 1;
        if (m > 9) m = 9;
        ADD(BEACON_CLIP_ABOUT);
        ADD(BEACON_CLIP_NUM_0 + m);
        ADD(m == 1 ? BEACON_CLIP_METRE : BEACON_CLIP_METRES);
    }

    const float rad2deg = 57.2957795f;
    float az = atan2f(pc[0], pc[2]) * rad2deg;                              /* + right */
    float el = atan2f(-pc[1], hypotf(pc[0], pc[2])) * rad2deg;              /* + up (Y is down) */
    if (fabsf(az) < 10.0f) {
        ADD(BEACON_CLIP_AHEAD);
    } else if (fabsf(az) < 25.0f) {
        ADD(BEACON_CLIP_A_LITTLE);
        ADD(az < 0 ? BEACON_CLIP_LEFT : BEACON_CLIP_RIGHT);
    } else {
        ADD(az < 0 ? BEACON_CLIP_LEFT : BEACON_CLIP_RIGHT);
    }
    if (el > 20.0f)
        ADD(BEACON_CLIP_UP);
    else if (el < -20.0f)
        ADD(BEACON_CLIP_DOWN);
#undef ADD
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

/* First candidate (in order) with a stored row seen within 1.5 s. Ties on a
 * name: nearest in cam if live, else nearest in world if pose is valid. */
static int bind_target(guided_state_t *st, const beacon_percept_block_t *p,
                       const beacon_intent_t *in, uint64_t now)
{
    float me_w[3];
    translation(p->pose.T_world_from_cam, me_w);

    for (uint32_t c = 0; c < in->n_candidates && c < BEACON_MAX_CANDIDATES; ++c) {
        const char *want = in->candidates[c];
        int best = -1;
        float best_d = 1e30f;
        for (int i = 0; i < BEACON_MAX_OBJECTS; ++i) {
            const beacon_object_t *o = &p->objects[i];
            if (!o->used || strncmp(o->name, want, BEACON_NAME_LEN) != 0)
                continue;
            uint64_t age = now > o->last_seen_ns ? now - o->last_seen_ns : 0;
            if (age >= BEACON_HOLD_MAX_NS)
                continue; /* too old for a NEW bind (§9) */
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
            return 1;
        }
    }
    return 0;
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
    st->d_valid = 0;
    st->last_walk_ns = 0;
    st->lost_said = 0;
    st->prev_mode = BEACON_MODE_NONE;
}

/* ------------------------------------------------------------------ intents */
static void handle_intent(guided_state_t *st, const beacon_percept_block_t *p,
                          const beacon_intent_t *in, uint64_t now, guided_out_t *out)
{
    switch (in->kind) {
    case BEACON_INTENT_FIND:
    case BEACON_INTENT_GO:
        st->stopped = 0;
        st->returning = 0;
        leave_reach(st, out);
        reset_guidance(st);
        if (!bind_target(st, p, in, now)) {
            st->target.bound = 0;
            say1(out, 1, BEACON_CLIP_NOT_SEEN);
        }
        break;
    case BEACON_INTENT_RETURN:
        st->stopped = 0;
        leave_reach(st, out);
        if (!p->pose.valid || p->crumb_n == 0) {
            say1(out, 1, BEACON_CLIP_CANNOT_RETRACE);
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
        say1(out, 0, BEACON_CLIP_DID_NOT_CATCH);
        break;
    case BEACON_INTENT_NACK_UNSEEN:
        say1(out, 0, BEACON_CLIP_NOT_SEEN);
        break;
    case BEACON_INTENT_NACK_CANT:
        say1(out, 0, BEACON_CLIP_CANNOT_HELP);
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
    *amp = n > 1e-4f ? clampf(v[2] / n, 0.0f, 1.0f) : 1.0f; /* §10: cos(theta), clamped at 0 */
    return 1;
}

/* ------------------------------------------------------------------ the step */
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
                if (st->last_walk_ns == 0 || now - st->last_walk_ns >= WALK_REPEAT_NS) {
                    float pc[3];
                    cam_from_world(p->pose.T_world_from_cam, cw, pc);
                    pc[1] = 0.0f; /* walking cue: ignore height */
                    uint16_t clips[GUIDED_MAX_CLIPS];
                    int n = guided_walk_clips(pc, st->cfg.metres_enabled, 0, clips, GUIDED_MAX_CLIPS);
                    say(out, 0, clips, n, NULL);
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

    /* ---------------- LOST (§6, §10): unique cue, never a number */
    if (mode == BEACON_MODE_LOST) {
        out->law = BEACON_LAW_LOST;
        if (st->in_reach)
            leave_reach(st, out);
        if (!st->lost_said) {
            push_cmd(out, GUIDED_CMD_FLUSH_SPEECH);
            say1(out, 1, BEACON_CLIP_LOST_TARGET);
            st->lost_said = 1;
        }
        st->d_valid = 0;
        st->prev_mode = mode;
        return;
    }
    if (st->prev_mode == BEACON_MODE_LOST) {
        st->lost_said = 0;
        st->last_walk_ns = 0; /* target is back: speak right away */
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
        float ms = guided_tick_interval_ms(st->d_ema);
        if (ms <= 0.0f && !hold) {
            out->continuous = 1;
            if (!st->tone_on) {
                guided_cmd_t *c = push_cmd(out, GUIDED_CMD_TONE_ON);
                if (c) { c->pan = out->pan; c->amp = 1.0f; }
                st->tone_on = 1;
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
        float range = v3_norm(st->target.xyz_cam);
        uint64_t every = (!hand_ok && range <= WALK_NEAR_M) ? WALK_REPEAT_NEAR_NS : WALK_REPEAT_NS;
        if (st->last_walk_ns == 0 || now - st->last_walk_ns >= every) {
            uint16_t clips[GUIDED_MAX_CLIPS];
            int n = guided_walk_clips(st->target.xyz_cam, st->cfg.metres_enabled, 1, clips, GUIDED_MAX_CLIPS);
            say(out, 0, clips, n, st->target.name);
            st->last_walk_ns = now;
        }
    }
    /* HOLD in WALK: say nothing new; no stale metres. */
    st->prev_mode = mode;
}
