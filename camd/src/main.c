#define _GNU_SOURCE

#include "beacon.h"

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <pthread.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#ifdef __QNX__
#include <sys/neutrino.h>
#endif

#define CAMD_STUB_W 640u
#define CAMD_STUB_H 480u
#define CAMD_STUB_FRAMETYPE 0u /* stub marker; never freeze this as a camera frametype */

static volatile sig_atomic_t g_stop = 0;
static uint64_t g_next_frame_id = 1;

static void on_signal(int signo)
{
    (void)signo;
    g_stop = 1;
}

static int pin_core0(void)
{
#ifdef __QNX__
    int runmask = (int)BEACON_RUNMASK_CORE0;
    if (ThreadCtl(_NTO_TCTL_RUNMASK, (void *)(intptr_t)runmask) == -1) {
        perror("camd: ThreadCtl RUNMASK");
        return -1;
    }
#else
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(0, &set);
    if (sched_setaffinity(0, sizeof(set), &set) == -1) {
        perror("camd: sched_setaffinity core 0");
        return -1;
    }
#endif
    return 0;
}

static void set_fifo(void)
{
    struct sched_param param;
    memset(&param, 0, sizeof(param));
    param.sched_priority = (int)BEACON_PRIO_CAMD;
    if (pthread_setschedparam(pthread_self(), SCHED_FIFO, &param) != 0) {
        fprintf(stderr, "camd: SCHED_FIFO %d not set; laptop run may need privileges\n",
                (int)BEACON_PRIO_CAMD);
    }
}

static beacon_frames_t *open_frames(void)
{
    int fd = shm_open(BEACON_SHM_FRAMES, O_CREAT | O_RDWR, 0666);
    if (fd == -1) {
        perror("camd: shm_open");
        return NULL;
    }

    size_t size = sizeof(beacon_frames_t);
    if (ftruncate(fd, (off_t)size) == -1) {
        perror("camd: ftruncate");
        close(fd);
        return NULL;
    }

    void *mem = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (mem == MAP_FAILED) {
        perror("camd: mmap");
        return NULL;
    }

    beacon_frames_t *frames = (beacon_frames_t *)mem;
    if (frames->abi != BEACON_ABI_VERSION) {
        memset(frames, 0, size);
        frames->abi = BEACON_ABI_VERSION;
    }
    return frames;
}

static void publish_frame(beacon_frames_t *frames,
                          uint32_t width, uint32_t height, uint32_t stride,
                          uint32_t frametype, const uint8_t *pixels, size_t bytes_used)
{
    if (bytes_used > BEACON_FRAME_MAX_BYTES) {
        fprintf(stderr, "camd: frame too large (%" PRIu64 " bytes)\n",
                (uint64_t)bytes_used);
        return;
    }

    uint32_t next = (frames->newest_slot + 1u) % BEACON_FRAME_SLOTS;
    beacon_frame_slot_t *slot = &frames->slot[next];

    beacon_seq_write_begin(&slot->seq);
    slot->frame_id = g_next_frame_id++;
    slot->t_ns = beacon_now_ns();
    slot->width = width;
    slot->height = height;
    slot->stride = stride;
    slot->frametype = frametype;
    slot->bytes_used = (uint32_t)bytes_used;
    memcpy(slot->pixels, pixels, bytes_used);
    beacon_seq_write_end(&slot->seq);

    __sync_synchronize();
    frames->newest_slot = next;
}

static void fill_stub_frame(uint8_t *pixels, uint32_t width, uint32_t height,
                            uint32_t stride, uint64_t frame_id)
{
    for (uint32_t y = 0; y < height; ++y) {
        for (uint32_t x = 0; x < width; ++x) {
            size_t off = (size_t)y * stride + (size_t)x * 4u;
            pixels[off + 0] = (uint8_t)((x * 4u + frame_id * 3u) & 0xffu);
            pixels[off + 1] = (uint8_t)((y * 4u + frame_id * 2u) & 0xffu);
            pixels[off + 2] = (uint8_t)((x + y + frame_id) & 0xffu);
            pixels[off + 3] = 255u;
        }
    }

    if (width > 40u && height > 30u) {
        uint32_t x0 = (uint32_t)((frame_id * 7u) % (width - 40u));
        uint32_t y0 = (uint32_t)((frame_id * 3u) % (height - 30u));
        for (uint32_t y = y0; y < y0 + 30u; ++y) {
            for (uint32_t x = x0; x < x0 + 40u; ++x) {
                size_t off = (size_t)y * stride + (size_t)x * 4u;
                pixels[off + 0] = 255u;
                pixels[off + 1] = 255u;
                pixels[off + 2] = 255u;
                pixels[off + 3] = 255u;
            }
        }
    }
}

static int sleep_until_ns(uint64_t target_ns)
{
    struct timespec ts;
    ts.tv_sec = (time_t)(target_ns / 1000000000ull);
    ts.tv_nsec = (long)(target_ns % 1000000000ull);

    for (;;) {
        int rc = clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, NULL);
        if (rc == 0)
            return 0;
        if (rc == EINTR)
            continue;
        return -1;
    }
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "usage: %s [--stub] [--once] [--hz N] [--frames N]\n"
            "  --stub   publish a synthetic frame (required on QNX until CamAPI is wired)\n"
            "  --once   publish one frame and exit\n"
            "  --hz N   publish rate for the stub, default 30\n"
            "  --frames N  stop after N frames, 0 means unlimited\n",
            prog);
}

int main(int argc, char **argv)
{
    int use_stub = 0;
    int once = 0;
    uint32_t hz = 30u;
    long max_frames = 0;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--stub") == 0) {
            use_stub = 1;
        } else if (strcmp(argv[i], "--once") == 0) {
            once = 1;
        } else if (strcmp(argv[i], "--hz") == 0 && i + 1 < argc) {
            hz = (uint32_t)strtoul(argv[++i], NULL, 10);
        } else if (strcmp(argv[i], "--frames") == 0 && i + 1 < argc) {
            max_frames = strtol(argv[++i], NULL, 10);
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    if (hz == 0u) {
        fprintf(stderr, "camd: --hz must be positive\n");
        return 2;
    }

#ifdef __QNX__
    if (!use_stub) {
        fprintf(stderr,
                "camd: QNX CamAPI adapter is not wired yet. Use --stub for the "
                "scheduler and shm skeleton.\n");
        return 2;
    }
#else
    use_stub = 1;
    (void)use_stub;
#endif

    if (pin_core0() == -1)
        return 1;
    set_fifo();

    beacon_frames_t *frames = open_frames();
    if (frames == NULL)
        return 1;

    uint32_t width = CAMD_STUB_W;
    uint32_t height = CAMD_STUB_H;
    uint32_t stride = width * 4u;
    size_t bytes = (size_t)stride * height;
    uint8_t *buffer = (uint8_t *)malloc(bytes);
    if (buffer == NULL) {
        perror("camd: malloc");
        munmap(frames, sizeof(*frames));
        return 1;
    }

    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);

    uint64_t period_ns = 1000000000ull / hz;
    uint64_t next_ns = beacon_now_ns() + period_ns;
    long published = 0;

    while (!g_stop) {
        fill_stub_frame(buffer, width, height, stride, g_next_frame_id);
        publish_frame(frames, width, height, stride, CAMD_STUB_FRAMETYPE,
                      buffer, bytes);
        ++published;

        if (once || (max_frames > 0 && published >= max_frames))
            break;

        next_ns += period_ns;
        uint64_t now_ns = beacon_now_ns();
        if (next_ns < now_ns)
            next_ns = now_ns + period_ns;
        if (sleep_until_ns(next_ns) == -1) {
            perror("camd: clock_nanosleep");
            break;
        }
    }

    fprintf(stderr, "camd: published %ld stub frame(s) to %s\n",
            published, BEACON_SHM_FRAMES);

    free(buffer);
    munmap(frames, sizeof(*frames));
    return 0;
}
