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
#define CAMD_FRAMETYPE_BMP_BGRA 0xffffu /* bring-up marker, not a camera format */

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

static void seed_next_frame_id(beacon_frames_t *frames)
{
    _Static_assert(
        offsetof(beacon_frame_slot_t, t_ns) >=
            offsetof(beacon_frame_slot_t, frame_id) + sizeof(uint64_t),
        "frame header layout changed; update the frame-id seed read");

    uint8_t head[offsetof(beacon_frame_slot_t, t_ns)];
    uint64_t max_id = 0;
    for (uint32_t i = 0; i < BEACON_FRAME_SLOTS; ++i) {
        if (!beacon_seq_read(&frames->slot[i].seq, head, &frames->slot[i],
                             sizeof(head), 8, NULL))
            continue;

        uint64_t id = 0;
        memcpy(&id, head + offsetof(beacon_frame_slot_t, frame_id), sizeof(id));
        if (id > max_id)
            max_id = id;
    }

    g_next_frame_id = max_id + 1u;
    if (g_next_frame_id == 0u)
        g_next_frame_id = 1u;
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

typedef struct {
    uint8_t *pixels;
    uint32_t width;
    uint32_t height;
    uint32_t stride;
    uint32_t frametype;
    size_t bytes;
} bmp_image_t;

static uint32_t read_le32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static int load_bmp(const char *path, bmp_image_t *out)
{
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) {
        fprintf(stderr, "camd: open BMP %s: %s\n", path, strerror(errno));
        return -1;
    }

    uint8_t file_header[14];
    uint8_t dib_header[124];
    if (fread(file_header, 1, sizeof(file_header), fp) != sizeof(file_header)) {
        fprintf(stderr, "camd: BMP %s has no file header\n", path);
        fclose(fp);
        return -1;
    }
    if (file_header[0] != 'B' || file_header[1] != 'M') {
        fprintf(stderr, "camd: BMP %s has a bad signature\n", path);
        fclose(fp);
        return -1;
    }

    uint32_t off_bits = read_le32(file_header + 10);
    if (fread(dib_header, 1, 4, fp) != 4) {
        fprintf(stderr, "camd: BMP %s has no DIB size\n", path);
        fclose(fp);
        return -1;
    }
    uint32_t header_size = read_le32(dib_header);
    if (header_size < 40u || header_size > sizeof(dib_header)) {
        fprintf(stderr, "camd: unsupported BMP DIB size %u\n", header_size);
        fclose(fp);
        return -1;
    }
    if (fread(dib_header + 4, 1, header_size - 4u, fp) != header_size - 4u) {
        fprintf(stderr, "camd: BMP %s has a truncated DIB header\n", path);
        fclose(fp);
        return -1;
    }

    int32_t raw_width = (int32_t)read_le32(dib_header + 4);
    int32_t raw_height = (int32_t)read_le32(dib_header + 8);
    uint16_t planes = (uint16_t)(dib_header[12] | ((uint16_t)dib_header[13] << 8));
    uint16_t bpp = (uint16_t)(dib_header[14] | ((uint16_t)dib_header[15] << 8));
    uint32_t compression = read_le32(dib_header + 16);
    if (raw_width <= 0 || raw_height == 0 || planes != 1u || bpp != 32u) {
        fprintf(stderr,
                "camd: only 32-bit BMP is supported (%d x %d, planes %u, bpp %u)\n",
                raw_width, raw_height, planes, bpp);
        fclose(fp);
        return -1;
    }
    if (compression != 0u && compression != 3u) {
        fprintf(stderr, "camd: unsupported BMP compression %u\n", compression);
        fclose(fp);
        return -1;
    }
    if (compression == 3u) {
        if (header_size < 52u) {
            fprintf(stderr, "camd: BI_BITFIELDS BMP has no masks\n");
            fclose(fp);
            return -1;
        }
        uint32_t red = read_le32(dib_header + 40);
        uint32_t green = read_le32(dib_header + 44);
        uint32_t blue = read_le32(dib_header + 48);
        if (red != 0x00ff0000u || green != 0x0000ff00u || blue != 0x000000ffu) {
            fprintf(stderr, "camd: expected BGRA byte order in BMP masks\n");
            fclose(fp);
            return -1;
        }
    }

    int top_down = raw_height < 0;
    uint64_t height64 = top_down ? (uint64_t)(-(int64_t)raw_height) : (uint64_t)raw_height;
    uint64_t stride64 = (((uint64_t)raw_width * 32u + 31u) / 32u) * 4u;
    uint64_t bytes64 = stride64 * height64;
    if (height64 == 0u || height64 > UINT32_MAX || stride64 > UINT32_MAX ||
        bytes64 == 0u || bytes64 > BEACON_FRAME_MAX_BYTES) {
        fprintf(stderr, "camd: BMP dimensions do not fit the frame ring\n");
        fclose(fp);
        return -1;
    }

    if (fseek(fp, 0, SEEK_END) != 0) {
        fprintf(stderr, "camd: BMP seek failed\n");
        fclose(fp);
        return -1;
    }
    long file_size = ftell(fp);
    if (file_size < 0 || (uint64_t)off_bits + bytes64 > (uint64_t)file_size) {
        fprintf(stderr, "camd: BMP %s is truncated\n", path);
        fclose(fp);
        return -1;
    }

    uint8_t *pixels = (uint8_t *)malloc((size_t)bytes64);
    if (pixels == NULL) {
        fprintf(stderr, "camd: BMP malloc failed\n");
        fclose(fp);
        return -1;
    }
    for (uint32_t y = 0; y < (uint32_t)height64; ++y) {
        uint64_t src_row = top_down ? y : (height64 - 1u - y);
        long row_off = (long)((uint64_t)off_bits + src_row * stride64);
        if (fseek(fp, row_off, SEEK_SET) != 0 ||
            fread(pixels + (size_t)y * (size_t)stride64, 1, (size_t)stride64, fp) != stride64) {
            fprintf(stderr, "camd: BMP row read failed\n");
            free(pixels);
            fclose(fp);
            return -1;
        }
    }
    fclose(fp);

    out->pixels = pixels;
    out->width = (uint32_t)raw_width;
    out->height = (uint32_t)height64;
    out->stride = (uint32_t)stride64;
    out->frametype = CAMD_FRAMETYPE_BMP_BGRA;
    out->bytes = (size_t)bytes64;
    return 0;
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
            "usage: %s (--stub | --bmp PATH) [--once] [--hz N] [--frames N]\n"
            "  --stub      publish a synthetic frame\n"
            "  --bmp PATH  publish an uncompressed 32-bit BMP (bring-up only)\n"
            "  --once      publish one frame and exit\n"
            "  --hz N      publish rate, default 30\n"
            "  --frames N  stop after N frames, 0 means unlimited\n",
            prog);
}

int main(int argc, char **argv)
{
    int use_stub = 0;
    const char *bmp_path = NULL;
    int once = 0;
    uint32_t hz = 30u;
    long max_frames = 0;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--stub") == 0) {
            use_stub = 1;
        } else if (strcmp(argv[i], "--bmp") == 0 && i + 1 < argc) {
            bmp_path = argv[++i];
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
    if (use_stub == (bmp_path != NULL)) {
        fprintf(stderr, "camd: choose exactly one of --stub or --bmp\n");
        return 2;
    }

    if (pin_core0() == -1)
        return 1;
    set_fifo();

    beacon_frames_t *frames = open_frames();
    if (frames == NULL)
        return 1;
    seed_next_frame_id(frames);

    uint8_t *buffer = NULL;
    uint32_t width = 0u;
    uint32_t height = 0u;
    uint32_t stride = 0u;
    uint32_t frametype = CAMD_STUB_FRAMETYPE;
    size_t bytes = 0u;
    const char *source = "stub";

    if (bmp_path != NULL) {
        bmp_image_t image;
        if (load_bmp(bmp_path, &image) == -1) {
            munmap(frames, sizeof(*frames));
            return 1;
        }
        buffer = image.pixels;
        width = image.width;
        height = image.height;
        stride = image.stride;
        frametype = image.frametype;
        bytes = image.bytes;
        source = "BMP";
    } else {
        width = CAMD_STUB_W;
        height = CAMD_STUB_H;
        stride = width * 4u;
        bytes = (size_t)stride * height;
        buffer = (uint8_t *)malloc(bytes);
        if (buffer == NULL) {
            perror("camd: malloc");
            munmap(frames, sizeof(*frames));
            return 1;
        }
    }

    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);

    uint64_t period_ns = 1000000000ull / hz;
    uint64_t next_ns = beacon_now_ns() + period_ns;
    long published = 0;

    while (!g_stop) {
        if (bmp_path == NULL)
            fill_stub_frame(buffer, width, height, stride, g_next_frame_id);
        publish_frame(frames, width, height, stride, frametype, buffer, bytes);
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

    fprintf(stderr, "camd: published %ld %s frame(s) to %s\n",
            published, source, BEACON_SHM_FRAMES);

    free(buffer);
    munmap(frames, sizeof(*frames));
    return 0;
}
