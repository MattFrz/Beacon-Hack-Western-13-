#include "beacon.h"
#ifdef BEACON_PREVIEW
#include "preview.h"
#endif
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <unistd.h>

/* The wire name is a bounded fixed-width ABI field, possibly without a NUL. */
static void escape_name(const char *name, char out[6 * BEACON_NAME_LEN + 1])
{
    for (size_t i = 0; i < BEACON_NAME_LEN && name[i]; ++i) {
        unsigned char c = (unsigned char)name[i];
        if (c == '"' || c == '\\') {
            *out++ = '\\';
            *out++ = (char)c;
        } else if (c < 32) {
            out += sprintf(out, "\\u%04x", (unsigned)c);
        } else {
            *out++ = (char)c;
        }
    }
    *out = 0;
}

static void vector_json(char out[96], const float xyz[3])
{
    if (isfinite(xyz[0]) && isfinite(xyz[1]) && isfinite(xyz[2]))
        snprintf(out, 96, "[%.9g,%.9g,%.9g]", xyz[0], xyz[1], xyz[2]);
    else
        strcpy(out, "null");
}

static const char *heartbeat_alive(uint64_t heartbeat, uint64_t now)
{
    return heartbeat && heartbeat <= now && now - heartbeat < UINT64_C(1000000000)
        ? "true" : "false";
}

static int append(char *packet, size_t cap, size_t *used, const char *fmt, ...)
{
    va_list args;
    va_start(args, fmt);
    int n = vsnprintf(packet + *used, cap - *used, fmt, args);
    va_end(args);
    if (n < 0 || (size_t)n >= cap - *used) return 0;
    *used += (size_t)n;
    return 1;
}

static int append_scene(char *packet, size_t cap, size_t used, const beacon_percept_block_t *percept)
{
    const beacon_pose_t *p = &percept->pose;
    int valid = p->valid;
    for (int i = 0; i < 16; ++i) valid = valid && isfinite(p->T_world_from_cam[i]);
    if (!append(packet, cap, &used, ",\"pose\":{\"valid\":%s,\"age_ns\":%" PRIu64
                ",\"pose_epoch\":%u", valid ? "true" : "false", p->age_ns, p->pose_epoch)) return 0;
    if (valid) {
        if (!append(packet, cap, &used, ",\"T_world_from_cam\":[")) return 0;
        for (int i = 0; i < 16; ++i)
            if (!append(packet, cap, &used, "%s%.9g", i ? "," : "", p->T_world_from_cam[i])) return 0;
        if (!append(packet, cap, &used, "]")) return 0;
    }
    if (!append(packet, cap, &used, "},\"objects\":[")) return 0;
    int count = 0;
    for (unsigned i = 0; i < BEACON_MAX_OBJECTS; ++i) {
        const beacon_object_t *o = &percept->objects[i];
        if (!o->used || (valid && o->pose_epoch != p->pose_epoch)) continue;
        char name[6 * BEACON_NAME_LEN + 1], cam[96], position[96], id[32];
        escape_name(o->name, name);
        vector_json(cam, o->xyz_cam);
        vector_json(position, o->xyz_world);
        /* ingest can receive string IDs that do not fit the numeric ABI. */
        if (o->id) snprintf(id, sizeof(id), "%u", o->id);
        else snprintf(id, sizeof(id), "\"slot-%u\"", i);
        /* full-frame pixel box from the detector, for boxes drawn on the dashboard's live camera */
        char bbox[128] = "";
        if ((o->bbox_px[2] > o->bbox_px[0] || o->bbox_px[3] > o->bbox_px[1]) &&
            isfinite(o->bbox_px[0]) && isfinite(o->bbox_px[1]) && isfinite(o->bbox_px[2]) && isfinite(o->bbox_px[3]))
            snprintf(bbox, sizeof(bbox), ",\"bbox_px\":[%.1f,%.1f,%.1f,%.1f]",
                     o->bbox_px[0], o->bbox_px[1], o->bbox_px[2], o->bbox_px[3]);
        if (!append(packet, cap, &used, "%s{\"id\":%s,\"name\":\"%s\",\"xyz_cam\":%s,\"xyz_world\":%s,"
                    "\"last_seen_ns\":%" PRIu64 ",\"in_latest_boxes\":%s%s}", count++ ? "," : "",
                    id, name, cam, position, o->last_seen_ns, o->in_latest_boxes ? "true" : "false", bbox)) return 0;
    }
    return append(packet, cap, &used, "]}") ? (int)used : 0;
}

static int snapshot(const beacon_world_t *world, char *packet, size_t cap)
{
    static const char *const modes[] = {"NONE", "LIVE", "HOLD", "LOST"};
    static const char *const laws[] = {"NONE", "STOP", "LOST", "REACH", "WALK", "RETURN"};
    beacon_guided_block_t guided;
    static beacon_percept_block_t percept;
    beacon_seq_t gs, ps;
    if (!beacon_seq_read(&world->seq_guided, &guided, &world->guided, sizeof(guided), 3, &gs) ||
        !beacon_seq_read(&world->seq_percept, &percept, &world->percept, sizeof(percept), 3, &ps))
        return 0;
    beacon_percept_health_t health = percept.health;
    beacon_hand_t hand = percept.hand;

    uint64_t now = beacon_now_ns();
    const beacon_target_t *t = &guided.target;
    uint64_t live_ns = beacon_live_max_ns(health.p95_vision_ns);
    int mode = beacon_mode(t->bound, t->in_latest_boxes, t->last_seen_ns, now, live_ns);
    char target[768] = "null";
    if (t->bound) {
        char name[6 * BEACON_NAME_LEN + 1], camera[96], position[96], confidence[32] = "null";
        escape_name(t->name, name);
        vector_json(camera, t->xyz_cam);
        vector_json(position, t->xyz_world);
        if (isfinite(t->conf))
            snprintf(confidence, sizeof(confidence), "%.9g", t->conf);
        snprintf(target, sizeof(target),
                 "{\"id\":%u,\"name\":\"%s\",\"xyz_cam\":%s,\"xyz_world\":%s,"
                 "\"conf\":%s,\"last_seen_ns\":%" PRIu64 ",\"frame_id\":%" PRIu64 ",\"pose_epoch\":%u}",
                 t->id, name, camera, position, confidence, t->last_seen_ns, t->frame_id, t->pose_epoch);
    }
    char hand_json[384] = "null", distance[32] = "null";
    if (hand.valid && hand.t_ns && hand.t_ns <= now && now - hand.t_ns < live_ns &&
        isfinite(hand.conf) && isfinite(hand.xyz_cam[0]) &&
        isfinite(hand.xyz_cam[1]) && isfinite(hand.xyz_cam[2])) {
        char camera[96], position[96];
        vector_json(camera, hand.xyz_cam);
        vector_json(position, hand.xyz_world);
        snprintf(hand_json, sizeof(hand_json),
                 "{\"xyz_cam\":%s,\"xyz_world\":%s,\"conf\":%.9g,"
                 "\"t_ns\":%" PRIu64 ",\"frame_id\":%" PRIu64 "}",
                 camera, position, hand.conf, hand.t_ns, hand.frame_id);
        if (mode == BEACON_MODE_LIVE && hand.frame_id == t->frame_id &&
            hand.pose_epoch == t->pose_epoch && guided.display.d_m >= 0 && isfinite(guided.display.d_m))
            snprintf(distance, sizeof(distance), "%.9g", guided.display.d_m);
    }
    const beacon_guided_display_t *display = &guided.display;
    char ticks[32] = "null", pan[32] = "null";
    if (isfinite(display->tick_hz) && display->tick_hz > 0)
        snprintf(ticks, sizeof(ticks), "%.9g", display->tick_hz);
    if (isfinite(display->pan))
        snprintf(pan, sizeof(pan), "%.9g", display->pan);

    /* Each uint16_t clip ID needs at most five digits and a comma. */
    enum { CLIP_CAPACITY = sizeof(display->last_clips) / sizeof(display->last_clips[0]) };
    char clips[6 * CLIP_CAPACITY + 1] = "";
    size_t used = 0;
    for (size_t i = 0; i < display->n_last_clips && i < CLIP_CAPACITY; ++i)
        used += (size_t)snprintf(clips + used, sizeof(clips) - used, "%s%u",
                                 i ? "," : "", (unsigned)display->last_clips[i]);

    const char *law = guided.display.law < sizeof(laws)/sizeof(laws[0]) ? laws[guided.display.law] : "NONE";
    int n = snprintf(packet, cap, "{\"v\":1,\"t_ns\":%" PRIu64 ",\"seq\":{\"guided\":%u,\"percept\":%u},"
                    "\"health\":{\"last_yolo_ms\":%" PRIu32 ",\"last_depth_ms\":%" PRIu32
                    ",\"p95_vision_ns\":%" PRIu64 ",\"timing\":{\"misses_16ms\":%" PRIu64
                    ",\"worst_late_us\":%" PRIu64 "},\"procs\":{"
                    "\"guided\":{\"alive\":%s,\"hb_ns\":%" PRIu64 "},"
                    "\"percept\":{\"alive\":%s,\"hb_ns\":%" PRIu64 "}}},"
                    "\"mode\":\"%s\",\"law\":\"%s\",\"target\":%s,\"hand\":%s,\"d_m\":%s,"
                    "\"cue\":{\"tick_hz\":%s,\"pan\":%s,\"continuous\":%s,\"clip_ids\":[%s]}",
                    now, gs, ps, health.last_yolo_ms, health.last_depth_ms, health.p95_vision_ns,
                    guided.stats.misses, guided.stats.worst_late_ns / UINT64_C(1000),
                    heartbeat_alive(guided.hb_guided_ns, now), guided.hb_guided_ns,
                    heartbeat_alive(health.hb_percept_ns, now), health.hb_percept_ns,
                    modes[mode], law, target, hand_json, distance,
                    ticks, pan, display->continuous ? "true" : "false", clips);
    if (n <= 0 || (size_t)n >= cap) return 0;
    size_t len = (size_t)n;
    /* The spoken request (voiced/beacon_cmd -> intent), for the dashboard's Intent card. */
    static const char *const kinds[] = {"NONE", "FIND", "GO", "RETURN", "STOP", "REPEAT", "REJECT",
                                        "NACK_UNHEARD", "NACK_UNSEEN", "NACK_CANT"};
    beacon_intent_t intent;
    beacon_seq_t vs;
    if (beacon_seq_read(&world->seq_voiced, &intent, &world->intent, sizeof(intent), 3, &vs) &&
        intent.kind != BEACON_INTENT_NONE && intent.kind < sizeof(kinds) / sizeof(kinds[0])) {
        if (!append(packet, cap, &len, ",\"intent\":{\"kind\":\"%s\",\"utterance_id\":%u,\"candidates\":[",
                    kinds[intent.kind], intent.utterance_id)) return 0;
        for (uint32_t i = 0; i < intent.n_candidates && i < BEACON_MAX_CANDIDATES; ++i) {
            char name[6 * BEACON_NAME_LEN + 1];
            escape_name(intent.candidates[i], name);
            if (!append(packet, cap, &len, "%s\"%s\"", i ? "," : "", name)) return 0;
        }
        if (!append(packet, cap, &len, "]}")) return 0;
    }
    return append_scene(packet, cap, len, &percept);
}

int main(int argc, char **argv)
{
    char *end;
    long port = argc > 2 ? strtol(argv[2], &end, 10) : 5005;
    struct sockaddr_in dest = {.sin_family = AF_INET};
    if (argc > 3 || port < 1 || port > 65535 || (argc > 2 && *end) ||
        inet_pton(AF_INET, argc > 1 ? argv[1] : "127.0.0.1", &dest.sin_addr) != 1) {
        fprintf(stderr, "Usage: telemd [destination-IPv4 [UDP-port]]\n");
        return 2;
    }
    dest.sin_port = htons((uint16_t)port);
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) { perror("UDP socket"); return 1; }
    const struct timespec period = {.tv_nsec = 100000000};
    /* BEACON_WORLD lets tests and replay runs use a private shm, the same
     * escape hatch guided, ingest and supervisor already have. The product
     * path never sets it: telemd attaches to /beacon_world. */
    const char *world_name = getenv("BEACON_WORLD");
    if (!world_name)
        world_name = BEACON_SHM_WORLD;
    const beacon_world_t *world = MAP_FAILED;
    while (world == MAP_FAILED) {
        int fd = shm_open(world_name, O_RDONLY, 0);
        if (fd >= 0) {
            struct stat st;
            if (fstat(fd, &st) < 0) { perror("fstat world"); return 1; }
            if (st.st_size >= (off_t)sizeof(*world)) {
                world = mmap(NULL, sizeof(*world), PROT_READ, MAP_SHARED, fd, 0);
                if (world == MAP_FAILED) { perror("mmap world"); return 1; }
            }
            close(fd);
        } else if (errno != ENOENT) { perror("open world"); return 1; }
        if (world == MAP_FAILED) nanosleep(&period, NULL);
    }
    for (;;) {
        if (world->abi == BEACON_ABI_VERSION) {
            static char packet[24576]; /* full object table with escaped names, below one UDP payload */
            int n = snapshot(world, packet, sizeof(packet));
            if (n > 0 && (size_t)n < sizeof(packet) &&
                sendto(sock, packet, (size_t)n, 0, (struct sockaddr *)&dest, sizeof(dest)) < 0)
                perror("send telemetry");
        } else if (world->abi != 0) {
            fprintf(stderr, "Unsupported world ABI %u\n", world->abi);
            return 1;
        }
#ifdef BEACON_PREVIEW
        preview_tick(sock, &dest);
#endif
        nanosleep(&period, NULL);
    }
}
