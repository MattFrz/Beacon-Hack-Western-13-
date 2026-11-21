#include "beacon.h"
#ifdef BEACON_PREVIEW
#include "preview.h"
#endif
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <math.h>
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

static int snapshot(const beacon_world_t *world, char *packet, size_t cap)
{
    static const char *const modes[] = {"NONE", "LIVE", "HOLD", "LOST"};
    static const char *const laws[] = {"NONE", "STOP", "LOST", "REACH", "WALK", "RETURN"};
    beacon_guided_block_t guided;
    beacon_percept_health_t health;
    beacon_hand_t hand;
    beacon_seq_t gs, ps, hand_seq;
    if (!beacon_seq_read(&world->seq_guided, &guided, &world->guided, sizeof(guided), 3, &gs) ||
        !beacon_seq_read(&world->seq_percept, &health, &world->percept.health, sizeof(health), 3, &ps) ||
        !beacon_seq_read(&world->seq_percept, &hand, &world->percept.hand, sizeof(hand), 3, &hand_seq) ||
        ps != hand_seq)
        return 0;

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
    const char *law = guided.display.law < sizeof(laws)/sizeof(laws[0]) ? laws[guided.display.law] : "NONE";
    return snprintf(packet, cap, "{\"v\":1,\"t_ns\":%" PRIu64 ",\"seq\":{\"guided\":%u,\"percept\":%u},"
                    "\"mode\":\"%s\",\"law\":\"%s\",\"target\":%s,\"hand\":%s,\"d_m\":%s}",
                    now, gs, ps, modes[mode], law, target, hand_json, distance);
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
    const beacon_world_t *world = MAP_FAILED;
    while (world == MAP_FAILED) {
        int fd = shm_open(BEACON_SHM_WORLD, O_RDONLY, 0);
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
            char packet[1400];
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
