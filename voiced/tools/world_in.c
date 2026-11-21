/* world_in: laptop-camera bridge. Receives Nathan's percept probe output over UDP
 * and writes it into /beacon_world, so guided on the Pi guides from a laptop camera.
 *
 *   world_in [--port 5006] [--verbose]
 *   laptop:  python3 percept/tools/probe_to_world.py ... --udp <pi-ip>:5006
 *
 * Fallback only: when percept on the Pi writes /beacon_world itself, don't run this.
 * Each datagram is one world JSON (laptop/samples/world.sample.json). Only
 * objects[] (name, id, xyz_cam, conf, in_latest_boxes) and hand (xyz_cam, conf)
 * are used. Times and frame ids are replaced with the Pi's own (the laptop clock
 * differs); hand and objects from one datagram share a frame id. Rows are never
 * deleted, so guided can still turn the wearer toward things out of view.
 * Pose is identity (no visual odometry from the laptop).
 */
#include "world_shm.h"

#include <arpa/inet.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>

static volatile sig_atomic_t g_stop;
static void on_signal(int s) { (void)s; g_stop = 1; }

static beacon_world_t *g_w;
static beacon_percept_block_t g_p;  /* our copy; published whole under seq_percept */
static uint64_t g_frame;

/* ---- tiny JSON helpers: enough for the probe's flat objects ---- */

/* End of the value that starts at s ({...} or [...] or "..." or a scalar). */
static const char *skip_value(const char *s)
{
    int depth = 0, in_str = 0;
    for (const char *p = s; *p; ++p) {
        if (in_str) {
            if (*p == '\\' && p[1]) ++p;
            else if (*p == '"') { in_str = 0; if (!depth) return p + 1; }
            continue;
        }
        if (*p == '"') in_str = 1;
        else if (*p == '{' || *p == '[') ++depth;
        else if (*p == '}' || *p == ']') { if (--depth <= 0) return p + 1; }
        else if (!depth && (*p == ',')) return p;
    }
    return s + strlen(s);
}

/* Value of "key" inside [s, e), or NULL. */
static const char *find_key(const char *s, const char *e, const char *key)
{
    char pat[48];
    snprintf(pat, sizeof(pat), "\"%s\"", key);
    size_t n = strlen(pat);
    for (const char *p = s; p + n < e; ++p)
        if (!strncmp(p, pat, n)) {
            const char *q = p + n;
            while (q < e && (*q == ' ' || *q == ':' || *q == '\t' || *q == '\n' || *q == '\r'))
                ++q;
            return q < e ? q : NULL;
        }
    return NULL;
}

static int get_vec3(const char *s, const char *e, const char *key, float v[3])
{
    const char *p = find_key(s, e, key);
    if (!p || *p != '[')
        return 0;
    char *end;
    ++p;
    for (int i = 0; i < 3; ++i) {
        v[i] = strtof(p, &end);
        if (end == p)
            return 0;
        p = end;
        while (*p == ',' || *p == ' ')
            ++p;
    }
    return 1;
}

static float get_num(const char *s, const char *e, const char *key, float dflt)
{
    const char *p = find_key(s, e, key);
    return (p && (*p == '-' || (*p >= '0' && *p <= '9'))) ? strtof(p, NULL) : dflt;
}

static int get_str(const char *s, const char *e, const char *key, char *out, size_t cap)
{
    const char *p = find_key(s, e, key);
    if (!p || *p != '"')
        return 0;
    size_t i = 0;
    for (++p; p < e && *p != '"' && i + 1 < cap; ++p)
        out[i++] = *p;
    out[i] = '\0';
    return i > 0;
}

/* ---- world update ---- */

static int row_for(const char *name, uint32_t id)
{
    int free_row = -1;
    for (int i = 0; i < BEACON_MAX_OBJECTS; ++i) {
        beacon_object_t *o = &g_p.objects[i];
        if (o->used && o->id == id && !strncmp(o->name, name, BEACON_NAME_LEN))
            return i;
        if (!o->used && free_row < 0)
            free_row = i;
    }
    if (free_row < 0) { /* full: reuse the stalest row */
        free_row = 0;
        for (int i = 1; i < BEACON_MAX_OBJECTS; ++i)
            if (g_p.objects[i].last_seen_ns < g_p.objects[free_row].last_seen_ns)
                free_row = i;
    }
    return free_row;
}

static int apply(const char *json, uint64_t now)
{
    const char *end = json + strlen(json);
    ++g_frame;
    for (int i = 0; i < BEACON_MAX_OBJECTS; ++i)
        g_p.objects[i].in_latest_boxes = 0;

    int seen = 0;
    const char *arr = find_key(json, end, "objects");
    if (arr && *arr == '[') {
        const char *p = arr + 1;
        while (*p && *p != ']') {
            while (*p == ' ' || *p == ',' || *p == '\n' || *p == '\r' || *p == '\t')
                ++p;
            if (*p != '{')
                break;
            const char *oe = skip_value(p);
            char name[BEACON_NAME_LEN];
            float xyz[3];
            const char *live = find_key(p, oe, "in_latest_boxes");
            int is_live = !live || *live == 't';   /* HOLD replays arrive as false: skip */
            if (is_live && get_str(p, oe, "name", name, sizeof(name)) && get_vec3(p, oe, "xyz_cam", xyz)) {
                uint32_t id = (uint32_t)get_num(p, oe, "id", 0);
                beacon_object_t *o = &g_p.objects[row_for(name, id)];
                memset(o, 0, sizeof(*o));
                o->used = 1;
                o->id = id;
                strncpy(o->name, name, BEACON_NAME_LEN - 1);
                memcpy(o->xyz_cam, xyz, sizeof(xyz));
                memcpy(o->xyz_world, xyz, sizeof(xyz)); /* identity pose */
                o->conf = get_num(p, oe, "conf", 0.8f);
                o->last_seen_ns = now;
                o->frame_id = g_frame;
                o->pose_epoch = 1;
                o->in_latest_boxes = 1;
                ++seen;
            }
            p = oe;
        }
    }

    g_p.hand.valid = 0;
    const char *h = find_key(json, end, "hand");
    if (h && *h == '{') {
        const char *he = skip_value(h);
        float xyz[3];
        if (get_vec3(h, he, "xyz_cam", xyz)) {
            memcpy(g_p.hand.xyz_cam, xyz, sizeof(xyz));
            memcpy(g_p.hand.xyz_world, xyz, sizeof(xyz));
            g_p.hand.conf = get_num(h, he, "conf", 0.9f);
            g_p.hand.t_ns = now;
            g_p.hand.frame_id = g_frame;
            g_p.hand.pose_epoch = 1;
            g_p.hand.valid = 1;
        }
    }
    return seen;
}

static void publish(uint64_t now, uint64_t p95)
{
    static const float I[16] = { 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1 };
    memcpy(g_p.pose.T_world_from_cam, I, sizeof(I));
    g_p.pose.t_ns = now;
    g_p.pose.pose_epoch = 1;
    g_p.pose.valid = 1;
    g_p.health.hb_percept_ns = now;
    g_p.health.p95_vision_ns = p95;
    beacon_seq_write_begin(&g_w->seq_percept);
    g_w->percept = g_p;
    beacon_seq_write_end(&g_w->seq_percept);
}

int main(int argc, char **argv)
{
    int port = 5006, verbose = 0;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--port") && i + 1 < argc) port = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--verbose")) verbose = 1;
        else { fprintf(stderr, "usage: %s [--port 5006] [--verbose]\n", argv[0]); return 2; }
    }
    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);
    g_w = world_open("world_in");
    if (!g_w)
        return 1;

    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in a;
    memset(&a, 0, sizeof(a));
    a.sin_family = AF_INET;
    a.sin_addr.s_addr = htonl(INADDR_ANY);
    a.sin_port = htons((uint16_t)port);
    if (sock < 0 || bind(sock, (struct sockaddr *)&a, sizeof(a)) < 0) {
        perror("world_in: bind");
        return 1;
    }
    struct timeval tv = { 0, 200000 }; /* wake up to notice Ctrl-C */
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    fprintf(stderr, "world_in: listening on UDP %d, writing %s\n", port, BEACON_SHM_WORLD);

    static char buf[65536];
    uint64_t last_rx = 0, gaps[20] = { 0 }, count = 0;
    double last_print = 0;
    while (!g_stop) {
        ssize_t n = recv(sock, buf, sizeof(buf) - 1, 0);
        if (n <= 0)
            continue;
        if ((unsigned char)buf[0] == 0xFF) /* JPEG preview, not world JSON */
            continue;
        buf[n] = '\0';
        uint64_t now = beacon_now_ns();
        if (last_rx)
            gaps[count % 20] = now - last_rx;
        last_rx = now;
        ++count;
        uint64_t p95 = 0; /* worst of the last 20 gaps: sets guided's LIVE window */
        for (int i = 0; i < 20; ++i)
            if (gaps[i] > p95)
                p95 = gaps[i];
        int seen = apply(buf, now);
        publish(now, p95);
        double t = (double)now * 1e-9;
        if (verbose || t - last_print >= 2.0) {
            fprintf(stderr, "world_in: %llu msgs, %d live objects", (unsigned long long)count, seen);
            for (int i = 0; i < BEACON_MAX_OBJECTS; ++i) {
                const beacon_object_t *o = &g_p.objects[i];
                if (o->used && o->in_latest_boxes)
                    fprintf(stderr, " | %s %.2f,%.2f,%.2f", o->name, o->xyz_cam[0], o->xyz_cam[1], o->xyz_cam[2]);
            }
            fprintf(stderr, "%s, gap p95 %.0f ms\n", g_p.hand.valid ? " | hand" : "", (double)p95 * 1e-6);
            last_print = t;
        }
    }
    close(sock);
    return 0;
}
