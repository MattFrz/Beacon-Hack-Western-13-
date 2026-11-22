/*
 * beacon_grab.c: pull live JPEG frames off the QNX sensor framework.
 *
 * Why this exists: the QNX image ships the sensor service and the Logitech C270
 * is enumerated on USB, but /usr/include/camera is empty and the camera_example*
 * binaries are interactive. The documented sensor API is enough.
 *
 * How frames actually come out (learned the hard way):
 *   - The unit must be configured "jpeg" with create_window = false and
 *     memory_allocator_type = from_sensor, or the service renders into a Screen
 *     window that does not exist and every buffer is a blank 10 80 YCbCr stub.
 *   - sensor_register_data_callback(SENSOR_EVENT_BUFFER) is unsupported (err 103)
 *     for usb_camera; SENSOR_EVENT_STREAM_DATA works and fires once per frame.
 *   - The buffer it hands you has a small `size` (first UVC packet, ~76 bytes)
 *     but buf->data points at the START of one of the buffers returned by
 *     sensor_premap_buffers(). The full JPEG is contiguous from there, so the
 *     real frame is [data, EOI].
 *
 * Declarations are local and partial on purpose: sensor_api.h pulls in
 * <screen/screen.h>, which is not installed here. Only the leading fields of
 * sensor_buffer_t are read and their offsets are fixed by the ABI.
 *
 * Build on the Pi:  cc -O2 -o beacon_grab beacon_grab.c /usr/lib/libsensor.so.1
 * Run:              ./beacon_grab -u 5 -n 1 -o /tmp/live/frame.jpg
 * Continuous:       ./beacon_grab -u 5 -w -r 5 -o /tmp/live/latest.jpg
 */
#include <errno.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

typedef void *sensor_handle_t;
typedef int sensor_error_t;
typedef int sensor_unit_t;
typedef int sensor_event_t;
typedef int sensor_eventmode_t;

#define SENSOR_EVENT_STREAM_DATA  5
#define SENSOR_EVENTMODE_READONLY 1

typedef struct {
    int32_t format;
    uint64_t size;
    uint8_t *data;
    uint64_t metadata_size;
    void *metadata;
    int64_t timestamp;
    int32_t flags;
    uint32_t reserved[4];
    uint8_t info[1024];   /* partial: the real tail is a format union */
} sensor_buffer_t;

extern sensor_error_t sensor_open(sensor_unit_t unit, int mode, sensor_handle_t *h);
extern sensor_error_t sensor_close(sensor_handle_t h);
extern sensor_error_t sensor_start(sensor_handle_t h, void *start_time);
extern sensor_error_t sensor_stop(sensor_handle_t h, void *stop_time);
extern sensor_error_t sensor_register_data_callback(sensor_handle_t h, sensor_event_t ev,
                                                    sensor_eventmode_t mode,
                                                    bool (*cb)(sensor_handle_t, sensor_buffer_t *, void *),
                                                    void *arg);
extern sensor_error_t sensor_get_eventkey_for_callback(sensor_handle_t h,
                                                       bool (*cb)(sensor_handle_t, sensor_buffer_t *, void *),
                                                       uint64_t *key);
extern sensor_error_t sensor_premap_buffers(sensor_handle_t h, uint64_t key,
                                            void **buffers, int64_t *offsets,
                                            uint64_t *size, uint32_t numasked,
                                            uint32_t *numsupported);

#define MAX_MAP 32

static void *g_map[MAX_MAP];
static uint32_t g_map_n;
static uint64_t g_map_size;

static const char *g_out = "/tmp/live/frame.jpg";
static int g_want = 1;        /* frames to keep before exiting; 0 = run forever */
static int g_skip = 0;        /* frames to drop first (exposure warm-up) */
static int g_continuous = 0;
static double g_min_period_s = 0.0;   /* 1/max_fps; 0 = take everything */
static int g_got = 0;
static int g_kept = 0;
static int g_verbose = 1;

static uint64_t now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

/* Find the JPEG end marker in the frame buffer, bounded by the buffer size. */
static long find_eoi(const uint8_t *p, uint64_t limit)
{
    if (limit > 1024 * 1024)
        limit = 1024 * 1024;   /* no sane 720p MJPEG frame is bigger */
    for (uint64_t i = 2; i + 1 < limit; i++)
        if (p[i] == 0xFF && p[i + 1] == 0xD9)
            return (long)(i + 2);
    return -1;
}

static bool write_atomic(const char *path, const uint8_t *buf, size_t len)
{
    char tmp[512];
    snprintf(tmp, sizeof(tmp), "%s.tmp", path);
    int fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        fprintf(stderr, "open %s: %s\n", tmp, strerror(errno));
        return false;
    }
    ssize_t n = write(fd, buf, len);
    close(fd);
    if (n != (ssize_t)len) {
        fprintf(stderr, "short write %s: %s\n", tmp, strerror(errno));
        return false;
    }
    if (rename(tmp, path) != 0) {
        fprintf(stderr, "rename %s: %s\n", path, strerror(errno));
        return false;
    }
    return true;
}

static bool on_data(sensor_handle_t h, sensor_buffer_t *buf, void *arg)
{
    (void)h; (void)arg;
    static uint64_t last_kept_ns;

    if (!buf || !buf->data || buf->size == 0)
        return true;

    ++g_got;
    if (g_got <= g_skip)
        return true;

    if (g_min_period_s > 0.0) {
        uint64_t t = now_ns();
        if (last_kept_ns && (double)(t - last_kept_ns) < g_min_period_s * 1e9)
            return true;
        last_kept_ns = t;
    }

    /* Locate the mapped buffer this frame lives in, then the real JPEG extent. */
    const uint8_t *frame = buf->data;
    uint64_t room = g_map_size;
    for (uint32_t i = 0; i < g_map_n; i++) {
        uint8_t *base = (uint8_t *)g_map[i];
        if (buf->data >= base && buf->data < base + g_map_size) {
            room = g_map_size - (uint64_t)(buf->data - base);
            break;
        }
    }

    int is_jpeg = buf->size > 3 && frame[0] == 0xFF && frame[1] == 0xD8;
    long len = is_jpeg ? find_eoi(frame, room) : -1;

    if (len > 0) {
        if (!write_atomic(g_out, frame, (size_t)len)) {
            fprintf(stderr, "failed to write %s\n", g_out);
        } else if (g_verbose) {
            fprintf(stderr, "frame %d: wrote %ld bytes%s\n", g_got, len,
                    g_continuous ? " (latest)" : "");
        }
        ++g_kept;
    } else if (g_verbose) {
        fprintf(stderr, "frame %d: fmt %d size %llu no JPEG end marker in %llu bytes\n",
                g_got, buf->format, (unsigned long long)buf->size,
                (unsigned long long)room);
    }

    if (!g_continuous && g_kept >= g_want)
        return false;   /* ask the library to hold the buffer; we're done */
    return true;
}

int main(int argc, char **argv)
{
    int unit = 5;
    int c;
    double max_fps = 0.0;

    while ((c = getopt(argc, argv, "u:n:o:s:r:wq")) != -1) {
        switch (c) {
        case 'u': unit = atoi(optarg); break;
        case 'n': g_want = atoi(optarg); break;
        case 'o': g_out = optarg; break;
        case 's': g_skip = atoi(optarg); break;
        case 'r': max_fps = atof(optarg); break;
        case 'w': g_continuous = 1; break;
        case 'q': g_verbose = 0; break;
        default:
            fprintf(stderr,
                    "usage: %s [-u unit] [-n frames] [-o path] [-s skip] [-r maxfps] [-w] [-q]\n"
                    "  -n 0 with -w keeps running; -w rewrites -o as a latest-frame file\n",
                    argv[0]);
            return 2;
        }
    }
    if (max_fps > 0.0)
        g_min_period_s = 1.0 / max_fps;

    sensor_handle_t h = NULL;
    sensor_error_t err = sensor_open((sensor_unit_t)unit, 0 /* ACCESSMODE_DATA */, &h);
    if (err != 0) {
        fprintf(stderr, "sensor_open(%d): err %d (%s)\n", unit, err, strerror(err));
        return 1;
    }

    err = sensor_register_data_callback(h, SENSOR_EVENT_STREAM_DATA,
                                        SENSOR_EVENTMODE_READONLY, on_data, NULL);
    if (err != 0) {
        fprintf(stderr, "register_data_callback: err %d (%s)\n", err, strerror(err));
        sensor_close(h);
        return 1;
    }

    /* Map the service's frame pool so buf->data is readable in our process. */
    uint64_t key = 0;
    err = sensor_get_eventkey_for_callback(h, on_data, &key);
    if (err == 0) {
        void *mapped[MAX_MAP];
        int64_t offs[MAX_MAP];
        uint64_t bsize = 0;
        uint32_t nsup = 0;
        err = sensor_premap_buffers(h, key, mapped, offs, &bsize, MAX_MAP, &nsup);
        if (err == 0) {
            g_map_n = nsup < MAX_MAP ? nsup : MAX_MAP;
            g_map_size = bsize;
            for (uint32_t i = 0; i < g_map_n; i++)
                g_map[i] = mapped[i];
            if (g_verbose)
                fprintf(stderr, "mapped %u buffer(s) of %llu bytes\n",
                        g_map_n, (unsigned long long)g_map_size);
        }
    }
    if (g_map_n == 0)
        fprintf(stderr, "warning: no buffers mapped; frames may be unreadable\n");

    err = sensor_start(h, NULL);
    if (err != 0) {
        fprintf(stderr, "sensor_start: err %d (%s)\n", err, strerror(err));
        sensor_close(h);
        return 1;
    }

    /* Callbacks arrive on the sensor thread; just wait for the frame count. */
    time_t deadline = g_continuous ? 0 : time(NULL) + 20;
    while (g_kept < g_want || g_continuous) {
        usleep(20 * 1000);
        if (deadline != 0 && time(NULL) > deadline) {
            fprintf(stderr, "timed out waiting for frames (%d seen, %d kept)\n",
                    g_got, g_kept);
            break;
        }
    }

    sensor_stop(h, NULL);
    sensor_close(h);
    if (g_verbose)
        fprintf(stderr, "done: %d frame(s) seen, %d kept\n", g_got, g_kept);
    return g_kept > 0 ? 0 : 1;
}
