/* beacon.h: the shared contract every process compiles against.
 *
 * Owners: Matt + Munadir. Source: docs/nathans-revision.md §5.1 and §6
 * (current revision: intent.kind includes REPEAT and REJECT).
 * CAM_W / CAM_H / frametype only after the Camera Module 3 probe; do not
 * write C270 sizes here.
 *
 * Field names follow the spec. Shared layout extensions are
 * marked "ADDITION" so they are easy to review.
 *
 * Rules (spec §6):
 *   - Each writer owns its own seq. Odd while writing, even when stable.
 *   - Readers never block: copy, re-check seq, skip on a torn read and keep
 *     the last good copy.
 *   - No mutexes in shared memory (a dying writer must never hold one).
 *   - All times are CLOCK_MONOTONIC nanoseconds as uint64_t.
 *   - mode (LIVE / HOLD / LOST) is never stored in shm. guided computes it;
 *     telemd recomputes it for display with beacon_mode() below.
 */
#ifndef BEACON_H
#define BEACON_H

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define BEACON_ABI_VERSION 1u

/* ---------------------------------------------------------------- names */
#define BEACON_SHM_FRAMES "/beacon_frames"
#define BEACON_SHM_DEPTH  "/beacon_depth"
#define BEACON_SHM_WORLD  "/beacon_world"

/* ---------------------------------------------------------------- sizes */
#define BEACON_NAME_LEN        32
#define BEACON_MAX_OBJECTS     32
#define BEACON_MAX_CRUMBS      512
#define BEACON_MAX_CANDIDATES  8

/* Camera: frozen after the Phase 0 probe (spec §4, §21). 0 = not probed yet.
 * Until then, consumers read width / height from each frame slot. */
#ifndef CAM_W
#define CAM_W 0
#endif
#ifndef CAM_H
#define CAM_H 0
#endif
#define BEACON_FRAME_SLOTS     3
#define BEACON_FRAME_MAX_BYTES (1920u * 1080u * 4u) /* generous max; real size is in the slot */
#define BEACON_DEPTH_MAX_W     256
#define BEACON_DEPTH_MAX_H     256

/* ---------------------------------------------------------------- timing (spec §5.1, §6, §10) */
#define BEACON_GUIDED_PERIOD_NS     16666667ull   /* 60 Hz */
#define BEACON_LIVE_MAX_NS_DEFAULT  1000000000ull /* until p95_vision_ns is measured */
#define BEACON_HOLD_MAX_NS          1500000000ull
#define BEACON_SUP_TICK_NS          50000000ull   /* supervisor pulse timer */

/* ---------------------------------------------------------------- scheduling (spec §5.1) */
#define BEACON_RUNMASK_CORE0   0x1u
#define BEACON_RUNMASK_CORES13 0xeu
#define BEACON_PRIO_SUPERVISOR 63
#define BEACON_PRIO_GUIDED     58
#define BEACON_PRIO_CAMD       50
#define BEACON_PRIO_AUDIO      40   /* guided's audio thread */
#define BEACON_PRIO_PERCEPT    22
#define BEACON_PRIO_VOICED     18

/* Pulse codes, as offsets from _PULSE_CODE_MINAVAIL (spec §5.1 table). */
enum beacon_pulse {
    BEACON_PULSE_SUP_TICK     = 0, /* timer -> supervisor, every 50 ms */
    BEACON_PULSE_HB_GUIDED    = 1,
    BEACON_PULSE_HB_CAMD      = 2,
    BEACON_PULSE_HB_PERCEPT   = 3,
    BEACON_PULSE_HB_VOICED    = 4,
    BEACON_PULSE_INTENT_EDGE  = 5, /* voiced -> guided: new intent */
    BEACON_PULSE_AUDIO_UNDERRUN = 6
};

/* ---------------------------------------------------------------- time */
static inline uint64_t beacon_now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

/* ---------------------------------------------------------------- seqlock (spec §5.1)
 * writer: mark odd, barrier, write fields, barrier, advance to even
 * reader: copy while seq is even and unchanged; give up after `tries`. */
typedef uint32_t beacon_seq_t;

static inline void beacon_seq_write_begin(volatile beacon_seq_t *seq)
{
    *seq |= 1u;                 /* stay odd if the previous writer died mid-update */
    __sync_synchronize();
}

static inline void beacon_seq_write_end(volatile beacon_seq_t *seq)
{
    __sync_synchronize();
    *seq = *seq + 1u;           /* even */
}

/* Copies n bytes from src to dst under seq. Returns 1 on a clean copy and
 * stores the even seq in *seq_out (if not NULL), 0 if every try was torn.
 * Never blocks. On 0, dst may be garbage: keep your last good copy. */
static inline int beacon_seq_read(const volatile beacon_seq_t *seq,
                                  void *dst, const volatile void *src, size_t n,
                                  int tries, beacon_seq_t *seq_out)
{
    for (int i = 0; i < tries; ++i) {
        beacon_seq_t s1 = *seq;
        __sync_synchronize();
        if (s1 & 1u)
            continue;
        memcpy(dst, (const void *)src, n);
        __sync_synchronize();
        beacon_seq_t s2 = *seq;
        if (s1 == s2) {
            if (seq_out)
                *seq_out = s1;
            return 1;
        }
    }
    return 0;
}

/* ---------------------------------------------------------------- frame ring (/beacon_frames), writer: camd */
typedef struct {
    float    scale, pad_x, pad_y;  /* letterbox of full W x H onto net w x h (spec §7) */
    uint32_t net_w, net_h;
} beacon_letterbox_t;

typedef struct {
    beacon_seq_t seq;
    uint32_t     _pad0;
    uint64_t     frame_id;     /* monotonic */
    uint64_t     t_ns;         /* CLOCK_MONOTONIC at dequeue */
    uint32_t     width, height, stride, frametype;
    uint32_t     bytes_used;
    uint32_t     _pad1;
    uint8_t      pixels[BEACON_FRAME_MAX_BYTES];
} beacon_frame_slot_t;

typedef struct {
    uint32_t            abi;
    uint32_t            newest_slot; /* hint; readers still check each slot's seq */
    beacon_frame_slot_t slot[BEACON_FRAME_SLOTS];
} beacon_frames_t;

/* ---------------------------------------------------------------- depth slot (/beacon_depth), writer: percept */
typedef struct {
    beacon_seq_t       seq;
    uint32_t           abi;
    uint64_t           frame_id, t_ns;
    uint32_t           w_d, h_d;          /* depth net output, ~210 */
    beacon_letterbox_t depth_affine;      /* CAM_W x CAM_H -> w_d x h_d */
    beacon_letterbox_t yolo_affine;       /* CAM_W x CAM_H -> 320 x 320 */
    float              hand_crop_origin_x, hand_crop_origin_y, hand_crop_scale;
    float              metres[BEACON_DEPTH_MAX_W * BEACON_DEPTH_MAX_H]; /* <= 0 or NaN = invalid */
} beacon_depth_t;

/* ---------------------------------------------------------------- world state (/beacon_world) */
typedef struct {
    float    T_world_from_cam[16]; /* row-major 4x4 */
    uint64_t t_ns;
    uint64_t age_ns;
    uint32_t pose_epoch;           /* bumped on every percept restart */
    uint8_t  valid;
    uint8_t  _pad[3];
} beacon_pose_t;

typedef struct {
    uint32_t id;
    char     name[BEACON_NAME_LEN];
    float    xyz_cam[3];           /* OpenCV camera frame: +X right, +Y down, +Z forward, metres */
    float    xyz_world[3];
    float    bbox_px[4];           /* full-frame pixels: x0, y0, x1, y1 */
    float    conf;
    uint64_t last_seen_ns;         /* capture time of the last box */
    uint64_t frame_id;
    uint32_t pose_epoch;
    uint8_t  in_latest_boxes;      /* 1 iff this name had a box in the cycle that wrote this seq */
    uint8_t  used;                 /* ADDITION: row in use (rows are never deleted when out of view) */
    uint8_t  _pad[2];
} beacon_object_t;

typedef struct {
    float    T_world_from_cam[16];
    uint64_t t_ns;
} beacon_crumb_t;

typedef struct {
    float    xyz_cam[3];
    float    xyz_world[3];
    float    conf;
    uint64_t t_ns;                 /* capture time of its frame */
    uint64_t frame_id;
    uint32_t pose_epoch;           /* ADDITION: spec §7 Range 1 compares hand.pose_epoch */
    uint8_t  valid;                /* ADDITION: 0 = no hand in that frame */
    uint8_t  _pad[3];
} beacon_hand_t;

typedef struct {
    uint64_t hb_percept_ns;
    uint32_t last_yolo_ms, last_depth_ms;
    uint64_t p95_vision_ns;        /* 0 until measured */
} beacon_percept_health_t;

typedef struct {                   /* written by percept under seq_percept */
    beacon_pose_t           pose;
    beacon_object_t         objects[BEACON_MAX_OBJECTS];
    beacon_crumb_t          crumbs[BEACON_MAX_CRUMBS];
    uint32_t                crumb_i, crumb_n; /* next write index, count */
    beacon_hand_t           hand;
    beacon_percept_health_t health;
} beacon_percept_block_t;

enum beacon_intent_kind {
    BEACON_INTENT_NONE = 0,
    BEACON_INTENT_FIND,
    BEACON_INTENT_GO,
    BEACON_INTENT_RETURN,
    BEACON_INTENT_STOP,
    BEACON_INTENT_REPEAT,          /* replay the last WALK template or NACK clip */
    BEACON_INTENT_REJECT,          /* drop the bind, try the next candidate name */
    BEACON_INTENT_NACK_UNHEARD,
    BEACON_INTENT_NACK_UNSEEN,
    BEACON_INTENT_NACK_CANT
};

typedef struct {                   /* written by voiced under seq_voiced */
    uint32_t kind;                 /* enum beacon_intent_kind */
    uint32_t n_candidates;
    char     candidates[BEACON_MAX_CANDIDATES][BEACON_NAME_LEN];
    uint64_t t_ns;
    uint32_t utterance_id;         /* ADDITION: +1 per request so guided sees repeats of the same words */
    uint32_t _pad;
} beacon_intent_t;

typedef struct {
    uint32_t id;
    char     name[BEACON_NAME_LEN];
    float    xyz_cam[3];
    float    xyz_world[3];
    float    conf;
    uint64_t last_seen_ns;
    uint64_t frame_id;
    uint32_t pose_epoch;
    uint8_t  bound;                /* ADDITION: 0 = no target */
    uint8_t  in_latest_boxes;      /* ADDITION: copied at refresh, drives LIVE */
    uint8_t  _pad[2];
} beacon_target_t;

/* ADDITION (team plan, timing panel): what guided is doing, for telemd only.
 * guided never reads this back. */
enum beacon_law {
    BEACON_LAW_NONE = 0,
    BEACON_LAW_STOP,
    BEACON_LAW_LOST,
    BEACON_LAW_REACH,
    BEACON_LAW_WALK,
    BEACON_LAW_RETURN
};

typedef struct {
    uint32_t law;                  /* enum beacon_law */
    float    d_m;                  /* hand-to-target, < 0 = none */
    float    pan;                  /* -1 left .. +1 right */
    float    tick_hz;              /* 0 = no ticks */
    uint8_t  continuous;           /* continuous tone */
    uint8_t  n_last_clips;
    uint16_t last_clips[12];       /* last spoken clip sequence (enum beacon_clip) */
    uint8_t  _pad[2];
} beacon_guided_display_t;

typedef struct {
    uint64_t loops;
    uint64_t misses;               /* 16 ms deadlines missed */
    uint64_t worst_late_ns;
    uint64_t p95_late_ns;
} beacon_guided_stats_t;

typedef struct {                   /* written by guided under seq_guided */
    uint64_t                hb_guided_ns;
    beacon_target_t         target;
    beacon_guided_display_t display; /* ADDITION */
    beacon_guided_stats_t   stats;   /* ADDITION */
} beacon_guided_block_t;

typedef struct {
    uint32_t               abi;
    uint32_t               _pad;
    beacon_seq_t           seq_percept;
    uint32_t               _pad_p;
    beacon_percept_block_t percept;
    beacon_seq_t           seq_voiced;
    uint32_t               _pad_v;
    beacon_intent_t        intent;
    beacon_seq_t           seq_guided;
    uint32_t               _pad_g;
    beacon_guided_block_t  guided;
} beacon_world_t;

/* ---------------------------------------------------------------- mode (spec §6)
 * Shared so telemd shows exactly what guided decides. Pure function. */
enum beacon_mode {
    BEACON_MODE_NONE = 0, /* no bound target */
    BEACON_MODE_LIVE,
    BEACON_MODE_HOLD,
    BEACON_MODE_LOST
};

static inline uint64_t beacon_live_max_ns(uint64_t p95_vision_ns)
{
    uint64_t twice = 2ull * p95_vision_ns;
    return twice > BEACON_LIVE_MAX_NS_DEFAULT ? twice : BEACON_LIVE_MAX_NS_DEFAULT;
}

static inline int beacon_mode(int bound, int in_latest_boxes, uint64_t last_seen_ns,
                              uint64_t now_ns, uint64_t live_max_ns)
{
    if (!bound)
        return BEACON_MODE_NONE;
    uint64_t age = now_ns > last_seen_ns ? now_ns - last_seen_ns : 0;
    if (in_latest_boxes && age < live_max_ns)
        return BEACON_MODE_LIVE;
    if (age < BEACON_HOLD_MAX_NS)
        return BEACON_MODE_HOLD;
    return BEACON_MODE_LOST;
}

/* ---------------------------------------------------------------- clips (spec §10)
 * One WAV per id in sounds/, named sounds/<id-name>.wav (Matt). Object names
 * are spoken from sounds/name_<label>.wav using the label string. */
enum beacon_clip {
    BEACON_CLIP_NONE = 0,
    BEACON_CLIP_NUM_0, BEACON_CLIP_NUM_1, BEACON_CLIP_NUM_2, BEACON_CLIP_NUM_3,
    BEACON_CLIP_NUM_4, BEACON_CLIP_NUM_5, BEACON_CLIP_NUM_6, BEACON_CLIP_NUM_7,
    BEACON_CLIP_NUM_8, BEACON_CLIP_NUM_9,
    BEACON_CLIP_METRE,
    BEACON_CLIP_METRES,
    BEACON_CLIP_AHEAD,
    BEACON_CLIP_LEFT,
    BEACON_CLIP_RIGHT,
    BEACON_CLIP_UP,
    BEACON_CLIP_DOWN,
    BEACON_CLIP_LOST_TARGET,      /* "I lost the target" */
    BEACON_CLIP_STOPPING,         /* "stopping" */
    BEACON_CLIP_NOT_SEEN,         /* "I have not seen that" */
    BEACON_CLIP_CANNOT_RETRACE,   /* "I cannot retrace without a path" */
    BEACON_CLIP_DID_NOT_CATCH,    /* "I did not catch that" */
    BEACON_CLIP_CANNOT_HELP,      /* "I cannot help with that" */
    /* ADDITIONS used by the WALK template; not in the spec's clip list */
    BEACON_CLIP_ABOUT,            /* "about" */
    BEACON_CLIP_A_LITTLE,         /* "a little" */
    BEACON_CLIP_YOU_ARE_BACK,     /* "you are back" */
    BEACON_CLIP_PROMPT_BEEP,      /* short beep before listening */
    BEACON_CLIP_OBJECT_NAME,      /* placeholder: speak the target's label */
    BEACON_CLIP_TURN_LEFT,        /* ADDITION: target out of view, from the session map */
    BEACON_CLIP_TURN_RIGHT,       /* ADDITION */
    BEACON_CLIP_FOUND_IT,         /* ADDITION: hand has stayed on the target */
    /* ADDITION: natural walk sentences. Directions are in the order
     * ahead, slightly left, left, slightly right, right. */
    BEACON_CLIP_INTRO_CONT_AHEAD,  /* "Your <label> is/are straight ahead," */
    BEACON_CLIP_INTRO_CONT_SLEFT,
    BEACON_CLIP_INTRO_CONT_LEFT,
    BEACON_CLIP_INTRO_CONT_SRIGHT,
    BEACON_CLIP_INTRO_CONT_RIGHT,
    BEACON_CLIP_INTRO_AHEAD,       /* same, ending the sentence: "...straight ahead." */
    BEACON_CLIP_INTRO_SLEFT,
    BEACON_CLIP_INTRO_LEFT,
    BEACON_CLIP_INTRO_SRIGHT,
    BEACON_CLIP_INTRO_RIGHT,
    BEACON_CLIP_DIR_AHEAD,         /* short update: "Straight ahead." */
    BEACON_CLIP_DIR_SLEFT,
    BEACON_CLIP_DIR_LEFT,
    BEACON_CLIP_DIR_SRIGHT,
    BEACON_CLIP_DIR_RIGHT,
    BEACON_CLIP_WITHIN_REACH,      /* "within arm's reach." */
    BEACON_CLIP_STEPS_1,           /* "about one step ahead." ... (a step is ~0.7 m) */
    BEACON_CLIP_STEPS_2,
    BEACON_CLIP_STEPS_3,
    BEACON_CLIP_STEPS_4,
    BEACON_CLIP_STEPS_5,
    BEACON_CLIP_STEPS_FAR,         /* "more than five steps away." */
    BEACON_CLIP_TURN_SLIGHT_LEFT,  /* "Turn a little to your left." */
    BEACON_CLIP_TURN_SLIGHT_RIGHT,
    BEACON_CLIP_TURN_AROUND,
    BEACON_CLIP_NEXT_TO,           /* "It's next to the mug." (cmd name = the landmark) */
    BEACON_CLIP_COUNT
};

#endif /* BEACON_H */
