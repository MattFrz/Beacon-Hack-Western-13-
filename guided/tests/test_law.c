/* test_law.c: unit tests for guided's decision logic (no shm, no threads). */
#include "law.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

static int g_fail, g_pass;
#define CHECK(cond, msg) do { if (cond) g_pass++; else { g_fail++; printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, msg); } } while (0)

#define MS 1000000ull
#define S  1000000000ull

static beacon_percept_block_t P;

static void identity_pose(uint32_t epoch)
{
    memset(P.pose.T_world_from_cam, 0, sizeof(P.pose.T_world_from_cam));
    P.pose.T_world_from_cam[0] = P.pose.T_world_from_cam[5] = P.pose.T_world_from_cam[10] = P.pose.T_world_from_cam[15] = 1;
    P.pose.valid = 1;
    P.pose.pose_epoch = epoch;
}

static void obj(int slot, uint32_t id, const char *name, float x, float y, float z, uint64_t seen, int live, uint64_t frame)
{
    beacon_object_t *o = &P.objects[slot];
    memset(o, 0, sizeof(*o));
    o->used = 1; o->id = id; strcpy(o->name, name);
    o->xyz_cam[0] = o->xyz_world[0] = x; o->xyz_cam[1] = o->xyz_world[1] = y; o->xyz_cam[2] = o->xyz_world[2] = z;
    o->conf = 0.8f; o->last_seen_ns = seen; o->in_latest_boxes = (uint8_t)live; o->frame_id = frame; o->pose_epoch = 1;
}

static void hand(float x, float y, float z, uint64_t t, uint64_t frame)
{
    memset(&P.hand, 0, sizeof(P.hand));
    P.hand.valid = 1; P.hand.conf = 0.9f; P.hand.t_ns = t; P.hand.frame_id = frame; P.hand.pose_epoch = 1;
    P.hand.xyz_cam[0] = x; P.hand.xyz_cam[1] = y; P.hand.xyz_cam[2] = z;
}

static beacon_intent_t intent(uint32_t kind, const char *a, const char *b, uint32_t utt, uint64_t t)
{
    beacon_intent_t in;
    memset(&in, 0, sizeof(in));
    in.kind = kind; in.utterance_id = utt; in.t_ns = t;
    if (a) strcpy(in.candidates[in.n_candidates++], a);
    if (b) strcpy(in.candidates[in.n_candidates++], b);
    return in;
}

static int said(const guided_out_t *o, uint16_t clip)
{
    for (int i = 0; i < o->n_cmds; ++i)
        if (o->cmds[i].kind == GUIDED_CMD_SAY)
            for (int k = 0; k < o->cmds[i].n_clips; ++k)
                if (o->cmds[i].clips[k] == clip)
                    return 1;
    return 0;
}

static int has_cmd(const guided_out_t *o, int kind)
{
    for (int i = 0; i < o->n_cmds; ++i)
        if (o->cmds[i].kind == kind)
            return 1;
    return 0;
}

static void reset(guided_state_t *st, int metres)
{
    memset(&P, 0, sizeof(P));
    identity_pose(1);
    guided_cfg_t cfg;
    guided_default_cfg(&cfg);
    cfg.metres_enabled = metres;
    guided_init(st, &cfg);
}

static void test_mode(void)
{
    uint64_t live = BEACON_LIVE_MAX_NS_DEFAULT;
    CHECK(beacon_mode(0, 1, 10 * S, 10 * S, live) == BEACON_MODE_NONE, "unbound is NONE");
    CHECK(beacon_mode(1, 1, 10 * S, 10 * S + 500 * MS, live) == BEACON_MODE_LIVE, "fresh box is LIVE");
    CHECK(beacon_mode(1, 1, 10 * S, 10 * S + 1200 * MS, live) == BEACON_MODE_HOLD, "box older than 1 s is HOLD");
    CHECK(beacon_mode(1, 0, 10 * S, 10 * S + 200 * MS, live) == BEACON_MODE_HOLD, "not in latest boxes is HOLD");
    CHECK(beacon_mode(1, 1, 10 * S, 10 * S + 1600 * MS, live) == BEACON_MODE_LOST, "older than 1.5 s is LOST");
    CHECK(beacon_live_max_ns(800 * MS) == 1600 * MS, "LIVE window is 2 x p95 when larger than 1 s");
}

static void test_bind_order_and_stale(void)
{
    guided_state_t st;
    guided_out_t out;
    uint64_t now = 20 * S;

    reset(&st, 0);
    obj(0, 7, "keychain", 0.0f, 0.2f, 0.8f, now, 1, 5);
    obj(1, 8, "keys", 0.1f, 0.2f, 0.9f, now, 1, 5);
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", "keychain", 1, now);
    guided_step(&st, &P, &in, now, &out);
    CHECK(st.target.bound && st.target.id == 8, "binds the first candidate in order (keys)");

    reset(&st, 0);
    obj(0, 7, "keychain", 0.0f, 0.2f, 0.8f, now, 1, 5);
    obj(1, 8, "keys", 0.1f, 0.2f, 0.9f, now - 2 * S, 0, 1);
    in = intent(BEACON_INTENT_FIND, "keys", "keychain", 1, now);
    guided_step(&st, &P, &in, now, &out);
    CHECK(st.target.bound && st.target.id == 7, "skips a row older than 1.5 s for a new bind");

    reset(&st, 0);
    obj(0, 2, "bottle", -0.6f, 0.1f, 2.2f, now, 1, 5);
    in = intent(BEACON_INTENT_FIND, "phone", NULL, 1, now);
    guided_step(&st, &P, &in, now, &out);
    CHECK(!st.target.bound, "unseen object is not bound");
    CHECK(said(&out, BEACON_CLIP_NOT_SEEN), "unseen says 'I have not seen that'");
}

static int said_range(const guided_out_t *o, uint16_t lo, uint16_t hi)
{
    for (int i = 0; i < o->n_cmds; ++i)
        if (o->cmds[i].kind == GUIDED_CMD_SAY)
            for (int k = 0; k < o->cmds[i].n_clips; ++k)
                if (o->cmds[i].clips[k] >= lo && o->cmds[i].clips[k] <= hi)
                    return 1;
    return 0;
}
#define SAID_INTRO(o) said_range((o), BEACON_CLIP_INTRO_CONT_AHEAD, BEACON_CLIP_INTRO_RIGHT)
#define SAID_DIST(o)  said_range((o), BEACON_CLIP_STEPS_1, BEACON_CLIP_STEPS_FAR)

static void test_walk_sentences(void)
{
    CHECK(guided_dir_cat(0.0f) == DIR_AHEAD, "0 deg is straight ahead");
    CHECK(guided_dir_cat(-15.0f) == DIR_SLEFT, "-15 deg is slightly to your left");
    CHECK(guided_dir_cat(40.0f) == DIR_RIGHT, "40 deg is to your right");
    CHECK(guided_dist_clip(0.5f) == BEACON_CLIP_WITHIN_REACH, "0.5 m is within reach");
    CHECK(guided_dist_clip(2.2f) == BEACON_CLIP_STEPS_3, "2.2 m is about three steps");
    CHECK(guided_dist_clip(0.83f) == BEACON_CLIP_STEPS_1, "0.83 m is about one step");
    CHECK(guided_dist_clip(1.4f) == BEACON_CLIP_STEPS_2, "1.4 m is about two steps");
    CHECK(guided_dist_clip(9.0f) == BEACON_CLIP_STEPS_FAR, "9 m is more than five steps");

    uint16_t c[GUIDED_MAX_CLIPS];
    int n = guided_walk_cue(DIR_SLEFT, BEACON_CLIP_STEPS_3, 1, 1, 1, c, GUIDED_MAX_CLIPS);
    CHECK(n == 2 && c[0] == BEACON_CLIP_INTRO_CONT_SLEFT && c[1] == BEACON_CLIP_STEPS_3,
          "full: 'Your keys are slightly to your left,' + 'about three steps ahead.'");
    n = guided_walk_cue(DIR_SLEFT, 0, 1, 1, 1, c, GUIDED_MAX_CLIPS);
    CHECK(n == 1 && c[0] == BEACON_CLIP_INTRO_SLEFT, "no metres: 'Your keys are slightly to your left.'");
    n = guided_walk_cue(DIR_LEFT, BEACON_CLIP_STEPS_1, 0, 1, 0, c, GUIDED_MAX_CLIPS);
    CHECK(n == 1 && c[0] == BEACON_CLIP_DIR_LEFT, "short direction update: 'To your left.'");
    n = guided_walk_cue(DIR_LEFT, BEACON_CLIP_STEPS_1, 0, 0, 1, c, GUIDED_MAX_CLIPS);
    CHECK(n == 1 && c[0] == BEACON_CLIP_STEPS_1, "short distance update: 'About one step ahead.'");
}

/* Google Maps pacing: no back-to-back repeats. A still target gets one full
 * sentence, then only a reminder every ~8 s; a change gets one short update. */
static void test_walk_pacing(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 1);
    uint64_t now = 120 * S;
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    int says = 0, full = 0;
    for (int i = 0; i < 1250; ++i) {           /* 20 s, keys 2 m ahead-left */
        obj(0, 1, "keys", -0.6f, 0.1f, 2.2f, now, 1, 40);
        guided_step(&st, &P, &in, now, &out);
        for (int k = 0; k < out.n_cmds; ++k)
            if (out.cmds[k].kind == GUIDED_CMD_SAY) says++;
        full += SAID_INTRO(&out);
        now += 16 * MS;
    }
    CHECK(says == 3 && full == 3, "still target, 20 s: one sentence then reminders at ~8 s and ~16 s");

    /* the keys move to the right: one short update, not a full sentence */
    int dir_updates = 0, fulls = 0;
    for (int i = 0; i < 160; ++i) {           /* 2.5 s */
        obj(0, 1, "keys", 0.9f, 0.1f, 2.2f, now, 1, 40);
        guided_step(&st, &P, &in, now, &out);
        dir_updates += said(&out, BEACON_CLIP_DIR_RIGHT);
        fulls += SAID_INTRO(&out);
        now += 16 * MS;
    }
    CHECK(dir_updates == 1 && fulls == 0, "direction change: one short 'To your right.'");
}

static void test_reach_enter_exit(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 0);
    uint64_t now = 30 * S;
    uint64_t frame = 100;
    obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, frame);
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    guided_step(&st, &P, &in, now, &out);
    CHECK(out.law == BEACON_LAW_WALK, "bound, no hand: WALK");
    CHECK(SAID_INTRO(&out), "WALK starts with a full sentence");

    /* hand 0.30 m away in the same frame: enter only on the 3rd frame */
    int entered_at = -1;
    for (int i = 1; i <= 4; ++i) {
        now += 16 * MS;
        obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, frame);
        hand(0.10f, 0.30f, 0.30f, now, frame);
        guided_step(&st, &P, &in, now, &out);
        if (out.law == BEACON_LAW_REACH && entered_at < 0)
            entered_at = i;
        if (i == 3) CHECK(has_cmd(&out, GUIDED_CMD_FLUSH_SPEECH), "entering REACH ducks speech");
    }
    CHECK(entered_at == 3, "REACH starts after 3 frames inside 0.50 m");

    /* hand at 0.60 m: still REACH (hysteresis, exit at 0.70) */
    for (int i = 0; i < 60; ++i) {
        now += 16 * MS;
        obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, frame);
        hand(0.10f, 0.30f, 0.00f, now, frame);
        guided_step(&st, &P, &in, now, &out);
    }
    CHECK(out.law == BEACON_LAW_REACH, "0.60 m stays in REACH (exit is 0.70 m)");

    for (int i = 0; i < 60; ++i) {
        now += 16 * MS;
        obj(0, 1, "keys", 0.10f, 0.30f, 0.90f, now, 1, frame);
        hand(0.10f, 0.30f, 0.00f, now, frame);
        guided_step(&st, &P, &in, now, &out);
    }
    CHECK(out.law == BEACON_LAW_WALK, "0.90 m leaves REACH");

    /* close in under 0.15 m: continuous tone, then "found it" once */
    int tone_seen = 0, found_says = 0, tone_off_after_found = 0;
    for (int i = 0; i < 150; ++i) {
        now += 16 * MS;
        obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, frame);
        hand(0.10f, 0.30f, 0.55f, now, frame);
        guided_step(&st, &P, &in, now, &out);
        if (out.law == BEACON_LAW_REACH && out.continuous)
            tone_seen = 1;
        if (said(&out, BEACON_CLIP_FOUND_IT)) {
            found_says++;
            tone_off_after_found = has_cmd(&out, GUIDED_CMD_TONE_OFF);
        }
    }
    CHECK(tone_seen, "under 0.15 m is a continuous tone");
    CHECK(found_says == 1, "'found it' is said once when the hand stays on the target");
    CHECK(tone_off_after_found, "the tone stops when 'found it' is said");

    /* hand pulls back and comes again: a second confirmation */
    for (int i = 0; i < 60; ++i) {
        now += 16 * MS;
        obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, frame);
        hand(0.10f, 0.30f, 0.20f, now, frame);
        guided_step(&st, &P, &in, now, &out);
    }
    found_says = 0;
    for (int i = 0; i < 150; ++i) {
        now += 16 * MS;
        obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, frame);
        hand(0.10f, 0.30f, 0.55f, now, frame);
        guided_step(&st, &P, &in, now, &out);
        if (said(&out, BEACON_CLIP_FOUND_IT)) found_says++;
    }
    CHECK(found_says == 1, "a new approach gets a new 'found it'");
}

/* Target left the view but the session map knows where it is (spec §7
 * Range 3): say which way to turn. With a stale pose (dead percept): LOST. */
static void test_turn_from_map(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 0);
    uint64_t now = 110 * S;
    obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, 30);
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    P.pose.t_ns = now;
    guided_step(&st, &P, &in, now, &out);
    CHECK(out.law == BEACON_LAW_WALK && SAID_INTRO(&out), "in view: normal walk cue");

    /* wearer turns 90 degrees right: keys now on their left, out of view */
    float yaw = 90.0f * 0.01745329f;
    float T[16] = { cosf(yaw), 0, sinf(yaw), 0,  0, 1, 0, 0,  -sinf(yaw), 0, cosf(yaw), 0,  0, 0, 0, 1 };
    memcpy(P.pose.T_world_from_cam, T, sizeof(T));
    P.objects[0].in_latest_boxes = 0;
    int left = 0, right = 0, lost = 0;
    for (int i = 0; i < 200; ++i) {          /* 3.2 s: past the 1.5 s LOST line */
        now += 16 * MS;
        P.pose.t_ns = now;
        guided_step(&st, &P, &in, now, &out);
        left += said(&out, BEACON_CLIP_TURN_LEFT);
        right += said(&out, BEACON_CLIP_TURN_RIGHT);
        lost += said(&out, BEACON_CLIP_LOST_TARGET);
    }
    CHECK(left >= 1 && right == 0, "out of view on the left: 'turn left'");
    CHECK(left <= 2, "the turn cue repeats about every 3 s, not every frame");
    CHECK(lost == 0, "with a fresh map it says which way to turn, not 'lost'");

    /* percept dies: pose goes stale, the map is not trusted, so LOST */
    lost = 0;
    left = 0;
    for (int i = 0; i < 120; ++i) {
        now += 16 * MS;
        guided_step(&st, &P, &in, now, &out);
        lost += said(&out, BEACON_CLIP_LOST_TARGET);
        left += said(&out, BEACON_CLIP_TURN_LEFT);
    }
    CHECK(lost == 1 && left == 0, "stale pose: 'I lost the target', never a guessed turn");
}

static void test_lost_once_and_no_numbers(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 1);
    uint64_t now = 40 * S;
    obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, 9);
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    guided_step(&st, &P, &in, now, &out);

    /* percept stops: the row never updates again */
    int lost_says = 0, numbers_in_hold = 0, hold_seen = 0;
    for (int i = 0; i < 200; ++i) {
        now += 16 * MS;
        guided_step(&st, &P, &in, now, &out);
        if (out.mode == BEACON_MODE_HOLD) {
            hold_seen = 1;
            if (SAID_DIST(&out)) numbers_in_hold = 1;
        }
        if (said(&out, BEACON_CLIP_LOST_TARGET))
            lost_says++;
    }
    CHECK(hold_seen, "a stale target passes through HOLD");
    CHECK(!numbers_in_hold, "no metres are spoken in HOLD");
    CHECK(out.mode == BEACON_MODE_LOST && out.law == BEACON_LAW_LOST, "then LOST");
    CHECK(lost_says == 1, "'I lost the target' is said exactly once");
}

static void test_frame_mismatch_holds_d(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 0);
    uint64_t now = 50 * S;
    obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, 10);
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    for (int i = 0; i < 10; ++i) {
        now += 16 * MS;
        obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, 10);
        hand(0.10f, 0.30f, 0.30f, now, 10);
        guided_step(&st, &P, &in, now, &out);
    }
    float d_before = out.d_m;
    P.pose.valid = 0; /* no shared world, and the hand is from another frame */
    for (int i = 0; i < 10; ++i) {
        now += 16 * MS;
        obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, 10);
        hand(0.10f, 0.30f, 0.58f, now, 11);
        guided_step(&st, &P, &in, now, &out);
    }
    CHECK(fabsf(out.d_m - d_before) < 1e-6f, "different frame and no pose: d is held, not recomputed");
}

/* `slay percept` mid-reach: the bundle freezes. REACH must keep ticking on the
 * last d (darker in HOLD), never fall back to a spoken WALK cue, then go LOST. */
static void test_percept_dies_mid_reach(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 1);
    uint64_t now = 80 * S;
    obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, 20);
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    for (int i = 0; i < 10; ++i) {
        now += 16 * MS;
        obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, 20);
        hand(0.10f, 0.30f, 0.35f, now, 20);
        guided_step(&st, &P, &in, now, &out);
    }
    CHECK(out.law == BEACON_LAW_REACH, "in REACH before the kill");

    int walk_after_kill = 0, dark_tick = 0, lost = 0;
    for (int i = 0; i < 150; ++i) {       /* 2.4 s with no new bundle */
        now += 16 * MS;
        guided_step(&st, &P, &in, now, &out);
        if (out.law == BEACON_LAW_WALK) walk_after_kill = 1;
        for (int k = 0; k < out.n_cmds; ++k)
            if (out.cmds[k].kind == GUIDED_CMD_TICK && out.cmds[k].dark) dark_tick = 1;
        if (out.law == BEACON_LAW_LOST) lost = 1;
    }
    CHECK(!walk_after_kill, "no WALK cue from a frozen bundle");
    CHECK(dark_tick, "HOLD keeps darker ticks on the last d");
    CHECK(lost, "then LOST");
}

static int said_name(const guided_out_t *o, const char *name)
{
    for (int i = 0; i < o->n_cmds; ++i)
        if (o->cmds[i].kind == GUIDED_CMD_SAY && !strcmp(o->cmds[i].name, name))
            return 1;
    return 0;
}

static void test_reject_and_repeat(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 0);
    uint64_t now = 90 * S;
#define TABLE(t) do { obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, (t), 1, 4);                       obj(1, 3, "keychain", -0.35f, 0.25f, 0.90f, (t), 1, 4);                       obj(2, 5, "bottle", 0.0f, 0.1f, 1.5f, (t), 1, 4); } while (0)
    TABLE(now);

    beacon_intent_t in = intent(BEACON_INTENT_REPEAT, NULL, NULL, 1, now);
    guided_step(&st, &P, &in, now, &out);
    CHECK(said(&out, BEACON_CLIP_NOT_SEEN), "REPEAT with nothing spoken yet says 'I have not seen that'");

    in = intent(BEACON_INTENT_FIND, "keys", "keychain", 2, now);
    guided_step(&st, &P, &in, now, &out);
    CHECK(st.target.id == 1 && said_name(&out, "keys"), "FIND binds keys and speaks its cue");

    TABLE(now + S);
    in = intent(BEACON_INTENT_REJECT, NULL, NULL, 3, now + S);
    guided_step(&st, &P, &in, now + S, &out);
    CHECK(st.target.bound && st.target.id == 3, "REJECT moves to the next candidate (keychain)");
    CHECK(said_name(&out, "keychain"), "and speaks the new cue right away");

    TABLE(now + 2 * S);
    in = intent(BEACON_INTENT_REPEAT, NULL, NULL, 4, now + 2 * S);
    guided_step(&st, &P, &in, now + 2 * S, &out);
    CHECK(said_name(&out, "keychain") && out.n_cmds == 1, "REPEAT replays the last cue exactly once");

    TABLE(now + 3 * S);
    in = intent(BEACON_INTENT_REJECT, NULL, NULL, 5, now + 3 * S);
    guided_step(&st, &P, &in, now + 3 * S, &out);
    CHECK(!st.target.bound && said(&out, BEACON_CLIP_NOT_SEEN), "REJECT with no candidates left clears the bind");
    CHECK(!said_name(&out, "bottle"), "REJECT never leaves the candidate set");
#undef TABLE
}

static void test_off_axis_amp_floor(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 0);
    uint64_t now = 100 * S;
    obj(0, 1, "keys", 0.30f, 0.30f, 0.60f, now, 1, 8);
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    float min_amp = 1.0f;
    int ticks = 0;
    for (int i = 0; i < 120; ++i) {
        now += 16 * MS;
        obj(0, 1, "keys", 0.30f, 0.30f, 0.60f, now, 1, 8);
        hand(-0.05f, 0.30f, 0.62f, now, 8);   /* 35 cm to the side, same depth */
        guided_step(&st, &P, &in, now, &out);
        for (int k = 0; k < out.n_cmds; ++k)
            if (out.cmds[k].kind == GUIDED_CMD_TICK) {
                ticks++;
                if (out.cmds[k].amp < min_amp) min_amp = out.cmds[k].amp;
            }
    }
    CHECK(ticks > 0, "off-axis hand still gets REACH ticks");
    CHECK(min_amp >= 0.25f - 1e-6f, "tick amplitude never drops below 0.25");
}

static void test_stop(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 0);
    uint64_t now = 60 * S;
    obj(0, 1, "keys", 0.10f, 0.30f, 0.60f, now, 1, 3);
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    guided_step(&st, &P, &in, now, &out);
    in = intent(BEACON_INTENT_STOP, NULL, NULL, 2, now + S);
    guided_step(&st, &P, &in, now + S, &out);
    CHECK(said(&out, BEACON_CLIP_STOPPING) && !st.target.bound, "STOP says 'stopping' and unbinds");
    CHECK(out.law == BEACON_LAW_STOP, "law is STOP afterwards");
}

static void test_return_refused_without_pose(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 0);
    P.pose.valid = 0;
    P.crumb_n = 5;
    beacon_intent_t in = intent(BEACON_INTENT_RETURN, NULL, NULL, 1, 70 * S);
    guided_step(&st, &P, &in, 70 * S, &out);
    CHECK(said(&out, BEACON_CLIP_CANNOT_RETRACE) && !st.returning, "RETURN without pose is refused");
}

static void test_tick_curve(void)
{
    CHECK(fabsf(guided_tick_interval_ms(0.60f) - 800.0f) < 0.01f, "800 ms at 0.6 m");
    CHECK(guided_tick_interval_ms(0.10f) == 0.0f, "continuous under 0.15 m");
    float mid = guided_tick_interval_ms(0.30f);
    CHECK(mid > 80.0f && mid < 800.0f, "interval shrinks as the hand closes in");
}

static void test_seq_writer_restart(void)
{
    beacon_seq_t seq = 0;
    uint32_t value = 1;
    uint32_t snapshot = 0;

    beacon_seq_write_begin(&seq);
    value = 2;
    CHECK(seq == 1, "a new write marks the sequence odd");

    /* The first writer exits before publishing its partial update. */
    beacon_seq_write_begin(&seq);
    CHECK(!beacon_seq_read(&seq, &snapshot, &value, sizeof(snapshot), 1, NULL),
          "a replacement writer keeps its partial update unreadable");
    value = 3;
    beacon_seq_write_end(&seq);
    CHECK(beacon_seq_read(&seq, &snapshot, &value, sizeof(snapshot), 1, NULL) &&
          snapshot == 3, "the completed update is readable after a restart");

    beacon_seq_write_begin(&seq);
    value = 4;
    beacon_seq_write_end(&seq);
    CHECK(seq == 4 && beacon_seq_read(&seq, &snapshot, &value, sizeof(snapshot), 1, NULL) &&
          snapshot == 4, "subsequent writes still publish normally");
}

static int count_kind(const guided_out_t *o, int kind)
{
    int n = 0;
    for (int i = 0; i < o->n_cmds; ++i)
        n += o->cmds[i].kind == kind;
    return n;
}

/* "It's next to the mug." after the full sentence when another object sits beside the target */
static void test_landmark(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 1);
    uint64_t now = 300 * S;
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    obj(0, 1, "keys", 0.0f, 0.1f, 2.0f, now, 1, 40);
    obj(1, 2, "mug", 0.15f, 0.1f, 2.05f, now, 1, 40);
    guided_step(&st, &P, &in, now, &out);
    int next_to = 0;
    for (int i = 0; i < out.n_cmds; ++i)
        if (out.cmds[i].kind == GUIDED_CMD_SAY && out.cmds[i].clips[0] == BEACON_CLIP_NEXT_TO &&
            !strcmp(out.cmds[i].name, "mug"))
            next_to = 1;
    CHECK(SAID_INTRO(&out) && next_to, "full sentence then 'It's next to the mug.'");
    memset(&P.objects[1], 0, sizeof(P.objects[1]));
}

/* Turn-toward pips: soft, panned to the target, faster as it comes in front,
 * one chime once facing it, then quiet. */
static void test_orient_pips(void)
{
    CHECK(guided_pip_interval_ms(90.0f) > guided_pip_interval_ms(20.0f), "pips speed up as you face the target");

    guided_state_t st;
    guided_out_t out;
    reset(&st, 1);
    uint64_t now = 400 * S;
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    int pips = 0, pip_right = 1, chimes = 0, pip_with_say = 0;
    for (int i = 0; i < 190; ++i) {            /* 3 s, keys 40 deg to the right */
        obj(0, 1, "keys", 1.3f, 0.1f, 1.5f, now, 1, 40);
        guided_step(&st, &P, &in, now, &out);
        for (int k = 0; k < out.n_cmds; ++k)
            if (out.cmds[k].kind == GUIDED_CMD_PIP) {
                pips++;
                if (out.cmds[k].pan <= 0.0f) pip_right = 0;
            }
        if (count_kind(&out, GUIDED_CMD_PIP) && count_kind(&out, GUIDED_CMD_SAY)) pip_with_say = 1;
        chimes += count_kind(&out, GUIDED_CMD_CHIME);
        now += 16 * MS;
    }
    CHECK(pips >= 4 && pip_right && !pip_with_say && chimes == 0,
          "target to the right: pips on the right, never with speech, no chime yet");

    int after = 0;
    for (int i = 0; i < 60; ++i) {             /* wearer turned: keys straight ahead */
        obj(0, 1, "keys", 0.0f, 0.1f, 1.5f, now, 1, 40);
        guided_step(&st, &P, &in, now, &out);
        chimes += count_kind(&out, GUIDED_CMD_CHIME);
        if (chimes) after += count_kind(&out, GUIDED_CMD_PIP);
        now += 16 * MS;
    }
    CHECK(chimes == 1 && after == 0, "facing it: one chime, then no pips");

    guided_cfg_t cfg;
    guided_default_cfg(&cfg);
    cfg.orient_pips = 0;
    guided_init(&st, &cfg);
    now += 10 * S;
    in = intent(BEACON_INTENT_FIND, "keys", NULL, 2, now);
    pips = 0;
    for (int i = 0; i < 190; ++i) {
        obj(0, 1, "keys", 1.3f, 0.1f, 1.5f, now, 1, 40);
        guided_step(&st, &P, &in, now, &out);
        pips += count_kind(&out, GUIDED_CMD_PIP) + count_kind(&out, GUIDED_CMD_CHIME);
        now += 16 * MS;
    }
    CHECK(pips == 0, "--no-orient-pips: silent between spoken cues");
}

/* Real cameras blink: the target drops out of the boxes for a few frames now
 * and then. That must not trigger "turn ..." or back-to-back full sentences. */
static void test_flicker(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 1);
    uint64_t now = 500 * S, seen = now;
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    int says = 0, turns = 0;
    uint64_t last_say = 0, min_gap = ~0ull;
    for (int i = 0; i < 600; ++i) {             /* ~10 s at 60 Hz, 40 deg right */
        int live = (i % 24) < 16;                 /* in view 16 frames, gone 8 (~0.13 s) */
        if (live)
            seen = now;
        obj(0, 1, "keys", 0.84f, 0.1f, 1.0f, seen, live, 40 + (uint64_t)i);
        P.pose.t_ns = now;
        guided_step(&st, &P, &in, now, &out);
        for (int k = 0; k < out.n_cmds; ++k)
            if (out.cmds[k].kind == GUIDED_CMD_SAY) {
                says++;
                if (last_say && now - last_say < min_gap)
                    min_gap = now - last_say;
                last_say = now;
                for (int c = 0; c < out.cmds[k].n_clips; ++c)
                    if (out.cmds[k].clips[c] >= BEACON_CLIP_TURN_SLIGHT_LEFT &&
                        out.cmds[k].clips[c] <= BEACON_CLIP_TURN_AROUND)
                        turns++;
            }
        now += 16 * MS;
    }
    CHECK(turns == 0, "short blinks out of view never say \"turn ...\"");
    CHECK(says <= 3 && (says < 2 || min_gap >= 2 * S), "blinking target: few cues, at least 2 s apart");
}

/* On the Pi the pose copy can arrive late now and then, so the map flips between
 * trusted and stale while the target is out of view. "I lost the target" must
 * still be said at most once. */
static void test_lost_once_with_flaky_pose(void)
{
    guided_state_t st;
    guided_out_t out;
    reset(&st, 1);
    uint64_t now = 600 * S;
    obj(0, 1, "keys", 0.0f, 0.1f, 1.0f, now, 1, 40);
    P.pose.t_ns = now;
    beacon_intent_t in = intent(BEACON_INTENT_FIND, "keys", NULL, 1, now);
    guided_step(&st, &P, &in, now, &out);
    uint64_t seen = now;
    obj(0, 1, "keys", 1.0f, 0.1f, 0.2f, seen, 0, 40);   /* now far right, out of view */
    int lost = 0;
    for (int i = 0; i < 400; ++i) {              /* ~6.4 s */
        now += 16 * MS;
        if (i % 70 == 0)
            P.pose.t_ns = now;                     /* pose refreshed only every ~1.1 s */
        guided_step(&st, &P, &in, now, &out);
        lost += said(&out, BEACON_CLIP_LOST_TARGET);
    }
    CHECK(lost <= 1, "flaky pose freshness: 'I lost the target' at most once");
}

int main(void)
{
    test_seq_writer_restart();
    test_mode();
    test_bind_order_and_stale();
    test_walk_sentences();
    test_walk_pacing();
    test_landmark();
    test_orient_pips();
    test_flicker();
    test_lost_once_with_flaky_pose();
    test_reach_enter_exit();
    test_turn_from_map();
    test_lost_once_and_no_numbers();
    test_frame_mismatch_holds_d();
    test_percept_dies_mid_reach();
    test_reject_and_repeat();
    test_off_axis_amp_floor();
    test_stop();
    test_return_refused_without_pose();
    test_tick_curve();
    printf("%d passed, %d failed\n", g_pass, g_fail);
    return g_fail ? 1 : 0;
}
