/* fakeworld: stands in for percept and voiced so guided runs on a laptop.
 *
 * Creates /beacon_world, then writes scripted percept bundles (5 Hz by
 * default, like a real vision cycle) and intents. Run guided next to it.
 *
 *   fakeworld <scenario> [--rate HZ] [--duration S]
 *
 * Scenarios:
 *   reach   "where are my keys": walk cue, then the hand closes in (ticks, tone)
 *   lost    reach, percept dies mid-reach (HOLD then LOST), comes back with
 *           the keys moved and a new pose_epoch (the Sunday slay test)
 *   walk    "where can I refill water": binds the bottle 2 m away, walk cues
 *   unseen  "where is my phone" with no phone in view
 *   stop    reach, then "stop"
 *   return  walk an L, then "take me back" along the breadcrumbs
 *   turn    the wearer turns away (map says "turn left"), turns back, reaches
 *           and holds the keys ("found it")
 *   reject  keys and keychain in view: "not that one" moves to the keychain,
 *           "say that again" repeats, a second "not that one" runs out
 */
#include "beacon.h"

#include <fcntl.h>
#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t g_stop;
static void on_signal(int s) { (void)s; g_stop = 1; }

static beacon_world_t *g_w;
static beacon_percept_block_t g_p;
static uint64_t g_frame;
static uint32_t g_utt;

static float lerp(float a, float b, float t) { return a + (b - a) * (t < 0 ? 0 : (t > 1 ? 1 : t)); }

static void set_pose_yaw(float yaw_deg, float x, float z, uint32_t epoch)
{
    float c = cosf(yaw_deg * 0.01745329f), s = sinf(yaw_deg * 0.01745329f);
    float T[16] = { c, 0, s, x,
                    0, 1, 0, 0,
                    -s, 0, c, z,
                    0, 0, 0, 1 };
    memcpy(g_p.pose.T_world_from_cam, T, sizeof(T));
    g_p.pose.valid = 1;
    g_p.pose.pose_epoch = epoch;
}

static void world_from_cam(const float pc[3], float pw[3])
{
    const float *T = g_p.pose.T_world_from_cam;
    for (int r = 0; r < 3; ++r)
        pw[r] = T[r * 4 + 0] * pc[0] + T[r * 4 + 1] * pc[1] + T[r * 4 + 2] * pc[2] + T[r * 4 + 3];
}

static void put_object(int slot, uint32_t id, const char *name, float x, float y, float z,
                       int seen, uint64_t now)
{
    beacon_object_t *o = &g_p.objects[slot];
    o->used = 1;
    o->id = id;
    strncpy(o->name, name, BEACON_NAME_LEN - 1);
    o->in_latest_boxes = (uint8_t)seen;
    if (seen) {
        o->xyz_cam[0] = x; o->xyz_cam[1] = y; o->xyz_cam[2] = z;
        world_from_cam(o->xyz_cam, o->xyz_world);
        o->conf = 0.8f;
        o->last_seen_ns = now;
        o->frame_id = g_frame;
        o->pose_epoch = g_p.pose.pose_epoch;
    }
}

static void put_hand(int valid, float x, float y, float z, uint64_t now)
{
    beacon_hand_t *h = &g_p.hand;
    h->valid = (uint8_t)valid;
    if (!valid)
        return;
    h->xyz_cam[0] = x; h->xyz_cam[1] = y; h->xyz_cam[2] = z;
    world_from_cam(h->xyz_cam, h->xyz_world);
    h->conf = 0.9f;
    h->t_ns = now;
    h->frame_id = g_frame;
    h->pose_epoch = g_p.pose.pose_epoch;
}

static void drop_crumb(uint64_t now)
{
    g_p.crumbs[g_p.crumb_i].t_ns = now;
    memcpy(g_p.crumbs[g_p.crumb_i].T_world_from_cam, g_p.pose.T_world_from_cam, sizeof(float) * 16);
    g_p.crumb_i = (g_p.crumb_i + 1) % BEACON_MAX_CRUMBS;
    if (g_p.crumb_n < BEACON_MAX_CRUMBS)
        g_p.crumb_n++;
}

static void publish_percept(uint64_t now)
{
    g_p.health.hb_percept_ns = now;
    g_p.pose.t_ns = now;
    beacon_seq_write_begin(&g_w->seq_percept);
    g_w->percept = g_p;
    beacon_seq_write_end(&g_w->seq_percept);
}

static void say_intent(uint32_t kind, const char *c0, const char *c1, const char *c2, const char *c3, uint64_t now)
{
    beacon_intent_t in;
    memset(&in, 0, sizeof(in));
    in.kind = kind;
    const char *c[4] = { c0, c1, c2, c3 };
    for (int i = 0; i < 4; ++i)
        if (c[i])
            strncpy(in.candidates[in.n_candidates++], c[i], BEACON_NAME_LEN - 1);
    in.t_ns = now;
    in.utterance_id = ++g_utt;
    beacon_seq_write_begin(&g_w->seq_voiced);
    g_w->intent = in;
    beacon_seq_write_end(&g_w->seq_voiced);
    static const char *kn[] = { "NONE", "FIND", "GO", "RETURN", "STOP", "REPEAT", "REJECT",
                                "NACK_UNHEARD", "NACK_UNSEEN", "NACK_CANT" };
    fprintf(stderr, "fakeworld: intent %s %s\n", kn[kind], c0 ? c0 : "");
}

int main(int argc, char **argv)
{
    const char *sc = argc > 1 ? argv[1] : "reach";
    double rate = 5.0, duration = 0;
    for (int i = 2; i < argc; ++i) {
        if (!strcmp(argv[i], "--rate") && i + 1 < argc) rate = atof(argv[++i]);
        else if (!strcmp(argv[i], "--duration") && i + 1 < argc) duration = atof(argv[++i]);
    }
    if (duration <= 0)
        duration = !strcmp(sc, "lost") ? 16 : (!strcmp(sc, "return") ? 22 : (!strcmp(sc, "turn") ? 15 : 12));

    int fd = shm_open(BEACON_SHM_WORLD, O_RDWR | O_CREAT, 0666);
    if (fd == -1 || ftruncate(fd, (off_t)sizeof(beacon_world_t)) == -1) {
        perror("fakeworld: shm");
        return 1;
    }
    g_w = mmap(NULL, sizeof(beacon_world_t), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (g_w == MAP_FAILED) {
        perror("fakeworld: mmap");
        return 1;
    }
    memset(g_w, 0, sizeof(*g_w));
    g_w->abi = BEACON_ABI_VERSION;
    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);

    memset(&g_p, 0, sizeof(g_p));
    set_pose_yaw(0, 0, 0, 1);

    uint64_t t0 = beacon_now_ns();
    uint64_t period = (uint64_t)(1e9 / rate);
    int said_find = 0, said_two = 0;
    double last_crumb = -1;
    fprintf(stderr, "fakeworld: scenario %s, percept %.1f Hz, %.0f s\n", sc, rate, duration);

    while (!g_stop) {
        uint64_t now = beacon_now_ns();
        double t = (double)(now - t0) * 1e-9;
        if (t >= duration)
            break;
        g_frame++;
        int publish = 1;

        if (!strcmp(sc, "reach") || !strcmp(sc, "lost") || !strcmp(sc, "stop")) {
            /* keys on the table 60 cm ahead, a bit right; a bottle further left */
            float kx = 0.10f, ky = 0.30f, kz = 0.60f;
            if (!strcmp(sc, "lost") && t >= 6.0 && t < 10.0)
                publish = 0;                                  /* `slay percept` */
            if (!strcmp(sc, "lost") && t >= 10.0) {
                kx = -0.15f;                                  /* judge moved the keys */
                if (g_p.pose.pose_epoch == 1) {
                    set_pose_yaw(0, 0, 0, 2);                 /* restart bumps pose_epoch */
                    fprintf(stderr, "fakeworld: percept back, keys moved left, pose_epoch 2\n");
                }
            }
            put_object(0, 1, "keys", kx, ky, kz, 1, now);
            put_object(1, 2, "bottle", -0.45f, 0.05f, 1.6f, 1, now);
            double ht = !strcmp(sc, "lost") && t >= 10.0 ? t - 10.0 : t - 3.0;
            if (ht >= 0) {
                float f = (float)(ht / 5.0);
                put_hand(1, lerp(0.35f, kx + 0.01f, f), lerp(0.55f, ky + 0.01f, f),
                         lerp(0.20f, kz - 0.02f, f), now);
            } else {
                put_hand(0, 0, 0, 0, now);
            }
            if (!said_find && t >= 0.5) {
                say_intent(BEACON_INTENT_FIND, "keys", "keychain", NULL, NULL, now);
                said_find = 1;
            }
            if (!strcmp(sc, "stop") && !said_two && t >= 5.0) {
                say_intent(BEACON_INTENT_STOP, NULL, NULL, NULL, NULL, now);
                said_two = 1;
            }
        } else if (!strcmp(sc, "walk")) {
            /* bottle ahead-left with a mug beside it; from 6 s the wearer turns to face it */
            float bx = lerp(-0.60f, 0.0f, (float)(t - 6.0) / 3.0f);
            put_object(0, 2, "bottle", bx, 0.10f, 2.20f, 1, now);
            put_object(1, 4, "mug", bx + 0.18f, 0.10f, 2.25f, 1, now);
            put_hand(0, 0, 0, 0, now);
            if (!said_find && t >= 0.5) {
                say_intent(BEACON_INTENT_GO, "fountain", "dispenser", "sink", "bottle", now);
                said_find = 1;
            }
        } else if (!strcmp(sc, "turn")) {
            /* keys on the table; the wearer turns 90 deg right (keys leave the
             * view, the map says "turn left"), turns back, then reaches. */
            float yaw = 0;
            if (t >= 3 && t < 4) yaw = (float)((t - 3) * 90);
            else if (t >= 4 && t < 7) yaw = 90;
            else if (t >= 7 && t < 8) yaw = (float)(90 - (t - 7) * 90);
            set_pose_yaw(yaw, 0, 0, 1);
            const float kw[3] = { 0.10f, 0.30f, 0.60f };    /* keys in the world */
            const float *T = g_p.pose.T_world_from_cam;
            float d[3] = { kw[0] - T[3], kw[1] - T[7], kw[2] - T[11] };
            float kc[3] = { T[0] * d[0] + T[4] * d[1] + T[8] * d[2],
                            T[1] * d[0] + T[5] * d[1] + T[9] * d[2],
                            T[2] * d[0] + T[6] * d[1] + T[10] * d[2] };
            int seen = kc[2] > 0.05f && fabsf(atan2f(kc[0], kc[2])) < 0.47f; /* ~27 deg half FOV */
            put_object(0, 1, "keys", kc[0], kc[1], kc[2], seen, now);
            double ht = t - 8.5;
            if (ht >= 0) {
                float f = (float)(ht / 3.0);
                put_hand(1, lerp(0.35f, kw[0] + 0.01f, f), lerp(0.55f, kw[1] + 0.01f, f),
                         lerp(0.20f, kw[2] - 0.02f, f), now);
            } else {
                put_hand(0, 0, 0, 0, now);
            }
            if (!said_find && t >= 0.5) {
                say_intent(BEACON_INTENT_FIND, "keys", "keychain", NULL, NULL, now);
                said_find = 1;
            }
        } else if (!strcmp(sc, "reject")) {
            /* keys and a keychain both on the table: "not that one", then "say that again" */
            put_object(0, 1, "keys", 0.10f, 0.30f, 0.60f, 1, now);
            put_object(1, 3, "keychain", -0.35f, 0.25f, 0.90f, 1, now);
            put_hand(0, 0, 0, 0, now);
            if (!said_find && t >= 0.5) {
                say_intent(BEACON_INTENT_FIND, "keys", "keychain", NULL, NULL, now);
                said_find = 1;
            }
            if (said_find == 1 && t >= 4.0) {
                say_intent(BEACON_INTENT_REJECT, NULL, NULL, NULL, NULL, now);
                said_find = 2;
            }
            if (said_find == 2 && t >= 5.5) {
                say_intent(BEACON_INTENT_REPEAT, NULL, NULL, NULL, NULL, now);
                said_find = 3;
            }
            if (said_find == 3 && t >= 7.0) {
                say_intent(BEACON_INTENT_REJECT, NULL, NULL, NULL, NULL, now);
                said_find = 4;
            }
        } else if (!strcmp(sc, "unseen")) {
            put_object(0, 2, "bottle", -0.60f, 0.10f, 2.20f, 1, now);
            if (!said_find && t >= 0.5) {
                say_intent(BEACON_INTENT_FIND, "phone", NULL, NULL, NULL, now);
                said_find = 1;
            }
        } else if (!strcmp(sc, "return")) {
            /* 0-4 s: 2 m forward. 4-5 s: turn right. 5-8 s: 1.5 m right.
             * 8.5 s: "take me back". 9-19 s: walk the route backwards. */
            float x = 0, z = 0, yaw = 0;
            if (t < 4) { z = (float)(t / 4 * 2.0); }
            else if (t < 5) { z = 2.0f; yaw = (float)((t - 4) * 90); }
            else if (t < 8) { z = 2.0f; yaw = 90; x = (float)((t - 5) / 3 * 1.5); }
            else if (t < 9) { z = 2.0f; x = 1.5f; yaw = 90 + (float)((t - 8) * 180); }
            else if (t < 13) { z = 2.0f; yaw = 270; x = 1.5f - (float)((t - 9) / 4 * 1.5); }
            else if (t < 14) { z = 2.0f; x = 0; yaw = 270 - (float)((t - 13) * 90); }
            else { yaw = 180; z = 2.0f - (float)((t - 14) / 5 * 2.0); if (z < 0) z = 0; }
            set_pose_yaw(yaw, x, z, 1);
            put_hand(0, 0, 0, 0, now);
            if (t < 8.5 && t - last_crumb >= 0.4) {
                drop_crumb(now);
                last_crumb = t;
            }
            if (!said_find && t >= 8.5) {
                say_intent(BEACON_INTENT_RETURN, NULL, NULL, NULL, NULL, now);
                said_find = 1;
            }
        } else {
            fprintf(stderr, "fakeworld: unknown scenario %s\n", sc);
            return 2;
        }

        if (publish)
            publish_percept(now);
        struct timespec nap = { (time_t)(period / 1000000000ull), (long)(period % 1000000000ull) };
        nanosleep(&nap, NULL);
    }
    return 0;
}
