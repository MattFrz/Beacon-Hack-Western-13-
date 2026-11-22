/* ingest: the missing wire between the probe and guided
 * (docs/qnx-integration-plan.md step 4).
 *
 * The percept probe (percept/tools/probe_to_world.py) emits one world-record
 * JSON object per UDP datagram. guided reads /beacon_world. Nothing connected
 * the two; this process does, on the device itself:
 *
 *   probe --udp 127.0.0.1:5006  ->  ingest  ->  /beacon_world (seq_percept)
 *
 * Contract (spec §5/§6, unchanged here):
 *   - ingest is the ONLY writer of seq_percept: pose, objects[], hand, health.
 *     It never writes seq_guided (guided owns the target bind) or crumbs
 *     (preserved from the block already in shm, per the restart-attach rule).
 *   - Timestamps are passed through as capture times; hb_percept_ns is
 *     refresh-time (it is a liveness field, not a measurement).
 *   - Malformed datagrams (e.g. a JPEG preview aimed here by mistake) are
 *     counted and dropped. Never blocks, never queues: newest record wins.
 *   - --intent KIND[:name,...] is a bring-up stand-in for `voiced`: it writes
 *     one seq_voiced intent AFTER the first record lands (guided binds from
 *     objects[], which must exist; an earlier intent would bind nothing).
 *
 * Usage:
 *   ingest [--create] [--udp [PORT]] [--stdin] [--intent SPEC] [--verbose]
 *     default: listen on UDP 5006 (the bridge owns 5005 on the laptop)
 *   BEACON_WORLD=/beacon_x overrides the shm name (tests; default
 *     /beacon_world), matching supervisor's BEACON_SUPERVISOR_WORLD pattern.
 *
 * On QNX: SCHED_RR 22 with runmask 0xe (cores 1-3; never core 0).
 */
#include "json.h"

#include "beacon.h"

#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <poll.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <unistd.h>

#ifdef __QNX__
#include <sys/neutrino.h>
#endif

#define INGEST_DEFAULT_PORT 5006
#define INGEST_MAX_DGRAM    65536
#define INGEST_ARENA_BYTES (256u * 1024u)

static volatile sig_atomic_t g_stop;
static void on_signal(int sig) { (void)sig; g_stop = 1; }

/* ------------------------------------------------------------------ world shm */

static beacon_world_t *open_world(const char *name, int create)
{
    int flags = O_RDWR | (create ? O_CREAT : 0);
    int fd = shm_open(name, flags, 0666);
    if (fd == -1) {
        fprintf(stderr, "ingest: shm_open %s: %s%s\n", name, strerror(errno),
                create ? "" : " (start with --create, or start the supervisor)");
        return NULL;
    }
    struct stat sb;
    if (fstat(fd, &sb) == -1) {
        close(fd);
        return NULL;
    }
    if ((size_t)sb.st_size < sizeof(beacon_world_t)) {
        if (!create || ftruncate(fd, (off_t)sizeof(beacon_world_t)) == -1) {
            fprintf(stderr, "ingest: %s is %lld bytes, need %zu\n", name,
                    (long long)sb.st_size, sizeof(beacon_world_t));
            close(fd);
            return NULL;
        }
    }
    void *m = mmap(NULL, sizeof(beacon_world_t), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (m == MAP_FAILED) {
        perror("ingest: mmap");
        return NULL;
    }
    beacon_world_t *w = m;
    if (create && w->abi == 0)
        w->abi = BEACON_ABI_VERSION;
    if (w->abi != BEACON_ABI_VERSION)
        fprintf(stderr, "ingest: warning: world abi %u, built for %u\n",
                w->abi, BEACON_ABI_VERSION);
    return w;
}

/* Attach to an existing percept block without zeroing it (spec §5 restart
 * rule). A torn blob (odd seq from a writer that died mid-write) is skipped
 * and replaced by our own zeroes; we own the block from here on. */
static void attach_block(beacon_world_t *w, beacon_percept_block_t *cur)
{
    beacon_seq_t seq;
    if (w->seq_percept != 0 &&
        beacon_seq_read(&w->seq_percept, cur, &w->percept, sizeof(*cur), 3, &seq))
        return; /* keep pose_epoch/hand health as they were */
    memset(cur, 0, sizeof(*cur));
}

/* ------------------------------------------------------------------ record mapping */

static void map_vec3(float out[3], const jval *v)
{
    out[0] = out[1] = out[2] = 0.0f;
    if (!jis(v, J_ARR))
        return;
    for (int i = 0; i < 3 && i < v->n; ++i)
        out[i] = (float)jnum(jarr_at(v, i), 0.0);
}

/* objects[] is authoritative per record: rows not in the record are gone
 * (the probe replays held rows itself with in_latest_boxes=false). */
static int map_objects(beacon_percept_block_t *blk, const jval *arr, uint32_t pose_epoch)
{
    memset(blk->objects, 0, sizeof(blk->objects));
    if (!jis(arr, J_ARR))
        return -1;
    int n = 0;
    for (int i = 0; i < arr->n && n < BEACON_MAX_OBJECTS; ++i) {
        const jval *o = jarr_at(arr, i);
        if (!jis(o, J_OBJ))
            continue;
        const char *name = jstr(jobj_get(o, "name"));
        if (!name || !*name)
            continue; /* a row without a name can never be bound or spoken */
        beacon_object_t *dst = &blk->objects[n];
        strncpy(dst->name, name, BEACON_NAME_LEN - 1);
        dst->id = (uint32_t)juint(jobj_get(o, "id"), 0);
        map_vec3(dst->xyz_cam, jobj_get(o, "xyz_cam"));
        map_vec3(dst->xyz_world, jobj_get(o, "xyz_world"));
        const jval *bbox = jobj_get(o, "bbox_px");
        for (int k = 0; k < 4 && k < (jis(bbox, J_ARR) ? bbox->n : 0); ++k)
            dst->bbox_px[k] = (float)jnum(jarr_at(bbox, k), 0.0);
        dst->conf = (float)jnum(jobj_get(o, "conf"), 0.0);
        dst->last_seen_ns = juint(jobj_get(o, "last_seen_ns"), 0);
        dst->frame_id = juint(jobj_get(o, "frame_id"), 0);
        dst->pose_epoch = (uint32_t)juint(jobj_get(o, "pose_epoch"), pose_epoch);
        dst->in_latest_boxes = (uint8_t)juint(jobj_get(o, "in_latest_boxes"), 0);
        dst->used = 1;
        ++n;
    }
    return n;
}

static void map_pose(beacon_percept_block_t *blk, const jval *root)
{
    const jval *p = jobj_get(root, "pose");
    memset(&blk->pose, 0, sizeof(blk->pose));
    if (!jis(p, J_OBJ))
        return;
    blk->pose.valid = (uint8_t)juint(jobj_get(p, "valid"), 0);
    blk->pose.pose_epoch = (uint32_t)juint(jobj_get(p, "pose_epoch"), 0);
    blk->pose.t_ns = juint(jobj_get(p, "t_ns"), 0);
    blk->pose.age_ns = juint(jobj_get(p, "age_ns"), 0);
    const jval *t = jobj_get(p, "T_world_from_cam");
    /* The live VO probe emits four rows. Recorded probes also use a flat matrix. */
    int nested = jis(t, J_ARR) && t->n == 4;
    for (int i = 0; i < 16; ++i) {
        const jval *row = nested ? jarr_at(t, i / 4) : t;
        const jval *v = jarr_at(row, nested ? i % 4 : i);
        if (!jis(row, J_ARR) || row->n != (nested ? 4 : 16) ||
            (!jis(v, J_INT) && !jis(v, J_NUM))) {
            blk->pose.valid = 0;
            return;
        }
        blk->pose.T_world_from_cam[i] = (float)jnum(v, 0.0);
    }
}

/* hand: absent or without xyz_cam -> no hand this record (valid = 0). */
static void map_hand(beacon_percept_block_t *blk, const jval *root)
{
    memset(&blk->hand, 0, sizeof(blk->hand));
    const jval *h = jobj_get(root, "hand");
    if (!jis(h, J_OBJ))
        return;
    const jval *xyz = jobj_get(h, "xyz_cam");
    if (!jis(xyz, J_ARR))
        return;
    map_vec3(blk->hand.xyz_cam, xyz);
    map_vec3(blk->hand.xyz_world, jobj_get(h, "xyz_world"));
    blk->hand.conf = (float)jnum(jobj_get(h, "conf"), 0.0);
    blk->hand.t_ns = juint(jobj_get(h, "t_ns"), 0);
    blk->hand.frame_id = juint(jobj_get(h, "frame_id"), 0);
    blk->hand.pose_epoch = blk->pose.pose_epoch; /* same record, same epoch */
    blk->hand.valid = 1;
}

/* health: p95_vision_ns is preserved across records (it is a measurement,
 * not per-record state). hb is refresh time. */
static void map_health(beacon_percept_block_t *blk, const jval *root, uint64_t now)
{
    const jval *h = jobj_get(root, "health");
    blk->health.last_yolo_ms = (uint32_t)juint(jobj_get(h, "last_yolo_ms"), 0);
    blk->health.last_depth_ms = (uint32_t)juint(jobj_get(h, "last_depth_ms"), 0);
    /* ADDITION: percept's measured p95 capture->publish latency sets guided's
     * LIVE window (spec: max(1 s, 2 x p95)); a record without it keeps the last. */
    uint64_t p95 = juint(jobj_get(h, "p95_vision_ns"), 0);
    if (p95)
        blk->health.p95_vision_ns = p95;
    blk->health.hb_percept_ns = now;
}

/* Returns 0 on success (blk updated), -1 on a dropped record. */
static int map_record(beacon_percept_block_t *blk, const jval *root, uint64_t now)
{
    if (!jis(root, J_OBJ)) {
        return -1;
    }
    const jval *objects = jobj_get(root, "objects");
    if (!jis(objects, J_ARR)) {
        return -1; /* not a world record; probably a stray datagram */
    }
    map_pose(blk, root);
    if (map_objects(blk, objects, blk->pose.pose_epoch) < 0)
        return -1;
    map_hand(blk, root);
    map_health(blk, root, now);
    return 0;
}

/* ------------------------------------------------------------------ intent (bring-up stand-in for voiced) */

static const struct { const char *name; uint32_t kind; } k_kinds[] = {
    { "NONE", BEACON_INTENT_NONE },       { "FIND", BEACON_INTENT_FIND },
    { "GO", BEACON_INTENT_GO },            { "RETURN", BEACON_INTENT_RETURN },
    { "STOP", BEACON_INTENT_STOP },        { "REPEAT", BEACON_INTENT_REPEAT },
    { "REJECT", BEACON_INTENT_REJECT },    { "NACK_UNHEARD", BEACON_INTENT_NACK_UNHEARD },
    { "NACK_UNSEEN", BEACON_INTENT_NACK_UNSEEN },
    { "NACK_CANT", BEACON_INTENT_NACK_CANT },
};

static int parse_intent(char *spec, beacon_intent_t *out)
{
    memset(out, 0, sizeof(*out));
    char *colon = strchr(spec, ':');
    char *names = NULL;
    if (colon) {
        *colon = '\0';
        names = colon + 1;
    }
    uint32_t kind = BEACON_INTENT_NONE;
    int found = 0;
    for (size_t i = 0; i < sizeof(k_kinds) / sizeof(k_kinds[0]); ++i)
        if (strcmp(spec, k_kinds[i].name) == 0) {
            kind = k_kinds[i].kind;
            found = 1;
            break;
        }
    if (!found) {
        fprintf(stderr, "ingest: unknown intent kind '%s'\n", spec);
        return -1;
    }
    out->kind = kind;
    if (names && *names) {
        char *save = NULL;
        for (char *tok = strtok_r(names, ",", &save); tok;
             tok = strtok_r(NULL, ",", &save)) {
            if (out->n_candidates >= BEACON_MAX_CANDIDATES)
                break;
            strncpy(out->candidates[out->n_candidates], tok, BEACON_NAME_LEN - 1);
            ++out->n_candidates;
        }
    }
    return 0;
}

static void write_intent(beacon_world_t *w, const beacon_intent_t *intent, uint64_t now)
{
    beacon_seq_write_begin(&w->seq_voiced);
    w->intent = *intent;
    w->intent.t_ns = now;
    w->intent.utterance_id = 1;
    beacon_seq_write_end(&w->seq_voiced);
}

/* ------------------------------------------------------------------ scheduling */

static void apply_sched(void)
{
#ifdef __QNX__
    /* This image rejects multi-bit runmasks (0xe returns EINVAL) and accepts a
     * single CPU or every CPU. Prefer cores 1-3, then settle for one core off
     * core 0 rather than running anywhere. The kernel readback is the evidence
     * for the placement claim, because `pidin -F %i` renders empty here. */
    static const unsigned candidates[] = { BEACON_RUNMASK_CORES13, 0x2u, 0x4u, 0x8u };
    for (size_t i = 0; i < sizeof(candidates) / sizeof(*candidates); ++i) {
        /* In: the mask we want. Out: the mask the kernel had before.
         * _NTO_TCTL_RUNMASK takes the value; GET_AND_SET takes a pointer. */
        unsigned prev = candidates[i];
        if (ThreadCtl(_NTO_TCTL_RUNMASK_GET_AND_SET, &prev) == -1) {
            fprintf(stderr, "ingest: runmask 0x%x rejected: %s\n",
                    candidates[i], strerror(errno));
            continue;
        }
        fprintf(stderr, "ingest: runmask 0x%x applied (kernel said it was 0x%x)\n",
                candidates[i], prev);
        break;
    }
#endif
    struct sched_param sp;
    memset(&sp, 0, sizeof(sp));
    sp.sched_priority = BEACON_PRIO_PERCEPT;
    if (sched_setscheduler(0, SCHED_RR, &sp) == -1)
        fprintf(stderr, "ingest: SCHED_RR %d not applied (normal on a laptop)\n",
                BEACON_PRIO_PERCEPT);
}

/* ------------------------------------------------------------------ main */

static void usage(const char *argv0)
{
    fprintf(stderr,
            "usage: %s [--create] [--udp [PORT]] [--stdin] [--intent KIND[:name,...]] [--verbose]\n"
            "  probe world records in (UDP or stdin), /beacon_world out\n"
            "  --udp        listen on PORT (default %d); the bridge owns 5005\n"
            "  --stdin      read one JSON record per line instead of UDP\n"
            "  --intent     one-shot voiced stand-in, e.g. FIND:keys,keychain (written\n"
            "               after the first record lands so guided can bind)\n"
            "  BEACON_WORLD overrides the shm name (default %s)\n",
            argv0, INGEST_DEFAULT_PORT, BEACON_SHM_WORLD);
}

int main(int argc, char **argv)
{
    int create = 0, verbose = 0, use_stdin = 0;
    long port = INGEST_DEFAULT_PORT;
    char *intent_spec = NULL; /* argv is mutable; parse_intent strtok_r's it */

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--create")) {
            create = 1;
        } else if (!strcmp(argv[i], "--stdin")) {
            use_stdin = 1;
        } else if (!strcmp(argv[i], "--verbose")) {
            verbose = 1;
        } else if (!strcmp(argv[i], "--udp")) {
            if (i + 1 < argc && argv[i + 1][0] >= '0' && argv[i + 1][0] <= '9')
                port = strtol(argv[++i], NULL, 10);
            else
                port = INGEST_DEFAULT_PORT;
        } else if (!strcmp(argv[i], "--intent") && i + 1 < argc) {
            intent_spec = argv[++i];
        } else {
            usage(argv[0]);
            return 2;
        }
    }
    if (port < 1 || port > 65535) {
        fprintf(stderr, "ingest: bad port %ld\n", port);
        return 2;
    }

    beacon_intent_t intent;
    int pending_intent = 0;
    if (intent_spec) {
        if (parse_intent(intent_spec, &intent) != 0)
            return 2;
        pending_intent = 1;
    }

    const char *world_name = getenv("BEACON_WORLD");
    if (!world_name)
        world_name = BEACON_SHM_WORLD;
    beacon_world_t *w = open_world(world_name, create);
    if (!w)
        return 1;

    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = on_signal;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    apply_sched();

    beacon_percept_block_t cur;
    attach_block(w, &cur);

    int fd;
    if (use_stdin) {
        fd = STDIN_FILENO;
    } else {
        fd = socket(AF_INET, SOCK_DGRAM, 0);
        if (fd == -1) {
            perror("ingest: socket");
            return 1;
        }
        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = htonl(INADDR_ANY);
        addr.sin_port = htons((unsigned short)port);
        if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
            fprintf(stderr, "ingest: bind udp %ld: %s\n", port, strerror(errno));
            return 1;
        }
    }

    static char dgram[INGEST_MAX_DGRAM];
    static char arena[INGEST_ARENA_BYTES];
    uint64_t records = 0, dropped = 0;

    fprintf(stderr, "ingest: world %s, %s, prio RR %d\n",
            world_name, use_stdin ? "stdin" : "udp", BEACON_PRIO_PERCEPT);

    while (!g_stop) {
        struct pollfd pfd = { .fd = fd, .events = POLLIN };
        int rc = poll(&pfd, 1, 250);
        if (rc == 0)
            continue;
        if (rc == -1) {
            if (errno == EINTR)
                continue;
            perror("ingest: poll");
            break;
        }

        ssize_t len;
        if (use_stdin) {
            if (!fgets(dgram, sizeof(dgram), stdin))
                break; /* EOF: stream done (replay mode) */
            len = (ssize_t)strlen(dgram);
            while (len > 0 && (dgram[len - 1] == '\n' || dgram[len - 1] == '\r'))
                dgram[--len] = '\0';
            if (len == 0)
                continue;
        } else {
            len = recvfrom(fd, dgram, sizeof(dgram) - 1, 0, NULL, NULL);
            if (len == -1) {
                if (errno == EINTR)
                    continue;
                perror("ingest: recvfrom");
                break;
            }
        }
        dgram[len] = '\0';

        jval *root = NULL;
        const char *err = "";
        if (json_parse(dgram, (size_t)len, arena, sizeof(arena), &root, &err) != 0) {
            ++dropped;
            if (dropped == 1 || verbose)
                fprintf(stderr, "ingest: drop (%s)\n", err);
            continue;
        }
        uint64_t now = beacon_now_ns();
        if (map_record(&cur, root, now) != 0) {
            ++dropped;
            if (verbose)
                fprintf(stderr, "ingest: drop (not a world record)\n");
            continue;
        }

        beacon_seq_write_begin(&w->seq_percept);
        w->percept = cur;
        beacon_seq_write_end(&w->seq_percept);
        ++records;

        if (verbose) {
            int nobj = 0;
            for (int i = 0; i < BEACON_MAX_OBJECTS; ++i)
                nobj += cur.objects[i].used ? 1 : 0;
            fprintf(stderr, "ingest: rec %llu objects %d hand %d t_ns %llu\n",
                    (unsigned long long)records, nobj, (int)cur.hand.valid,
                    (unsigned long long)cur.pose.t_ns);
        }

        if (pending_intent) {
            /* Wait for a record that carries the object the intent names. A FIND
             * bound off an empty objects[] -- or off an unrelated detection --
             * gives guided nothing to bind and earns one NACK ("I have not seen
             * that"), which is never retried (§9). Perception flickers between
             * LIVE and LOST and low-confidence junk is normal, so the honest
             * trigger is "a record that contains one of the candidates".
             * With no candidates listed, any object is enough. */
            int nobj = 0, nmatch = 0;
            for (int i = 0; i < BEACON_MAX_OBJECTS; ++i) {
                if (!cur.objects[i].used)
                    continue;
                ++nobj;
                if (intent.n_candidates == 0) {
                    ++nmatch;
                    continue;
                }
                for (uint32_t c = 0; c < intent.n_candidates; ++c)
                    if (!strcmp(cur.objects[i].name, intent.candidates[c])) {
                        ++nmatch;
                        break;
                    }
            }
            if (nmatch > 0) {
                write_intent(w, &intent, now);
                pending_intent = 0;
                fprintf(stderr, "ingest: intent %u with %u candidate(s) written "
                                "after %llu record(s), %d object(s), %d match(es)\n",
                        intent.kind, intent.n_candidates,
                        (unsigned long long)records, nobj, nmatch);
            }
        }
    }

    fprintf(stderr, "ingest: %llu records, %llu dropped\n",
            (unsigned long long)records, (unsigned long long)dropped);
    if (fd != STDIN_FILENO)
        close(fd);
    munmap(w, sizeof(*w));
    return 0;
}
