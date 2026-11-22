/*
 * beacon_grab.c: pull frames off the QNX sensor framework into files.
 *
 * Why this exists: the QNX image ships the sensor service and a Logitech C270
 * is enumerated on USB, but no capture client we can use -- /usr/include/camera
 * is empty, and the camera_example* binaries are interactive/viewfinder-only.
 * The documented sensor API (sensor/sensor_api.h) is enough: open the unit,
 * register a data callback, start streaming, write each buffer out.
 *
 * Declarations are local and partial on purpose: sensor_api.h pulls in
 * <screen/screen.h>, which is not installed here. Only the leading fields of
 * sensor_buffer_t are read, and those offsets are fixed by the ABI, so a
 * partial struct is safe for receiving pointers from the library.
 *
 * Build on the Pi:   cc -O2 -o beacon_grab beacon_grab.c -lsensor
 * Run:               ./beacon_grab -u 5 -n 10 -o /tmp/live/frame
 */
#include <errno.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef void *sensor_handle_t;
typedef int sensor_error_t;
typedef int sensor_unit_t;
typedef int sensor_event_t;
typedef int sensor_eventmode_t;

/* sensor_format_t values we care about (sensor_api.h). */
#define SENSOR_FORMAT_UNSPECIFIED        0
#define SENSOR_FORMAT_VIDEO_COMPRESSED   9
#define SENSOR_FORMAT_METADATA           6

/* sensor_event_t */
#define SENSOR_EVENT_BUFFER       4
#define SENSOR_EVENT_STREAM_DATA  5

/* sensor_eventmode_t */
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

static int g_want = 10;
static int g_got = 0;
static const char *g_prefix = "/tmp/live/frame";
static int g_verbose = 1;

static bool on_data(sensor_handle_t h, sensor_buffer_t *buf, void *arg)
{
    (void)h; (void)arg;
    if (!buf || !buf->data || buf->size == 0)
        return true;

    int is_jpeg = buf->size > 3 && buf->data[0] == 0xFF && buf->data[1] == 0xD8;

    if (g_verbose)
        fprintf(stderr, "frame %d: fmt %d size %llu ts %lld jpeg %d\n",
                g_got, buf->format, (unsigned long long)buf->size,
                (long long)buf->timestamp, is_jpeg);

    if (g_got < g_want) {
        char path[256];
        snprintf(path, sizeof(path), "%s_%03d.%s", g_prefix, g_got,
                 is_jpeg ? "jpg" : "raw");
        int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (fd >= 0) {
            ssize_t n = write(fd, buf->data, buf->size);
            close(fd);
            if (n != (ssize_t)buf->size)
                fprintf(stderr, "short write %s: %s\n", path, strerror(errno));
            else if (g_verbose > 1)
                fprintf(stderr, "  wrote %s\n", path);
        } else {
            fprintf(stderr, "open %s: %s\n", path, strerror(errno));
        }
    }
    ++g_got;
    return true; /* let the library reclaim the buffer */
}

int main(int argc, char **argv)
{
    int unit = 5;
    int c;
    while ((c = getopt(argc, argv, "u:n:o:q")) != -1) {
        switch (c) {
        case 'u': unit = atoi(optarg); break;
        case 'n': g_want = atoi(optarg); break;
        case 'o': g_prefix = optarg; break;
        case 'q': g_verbose = 0; break;
        default:
            fprintf(stderr, "usage: %s [-u unit] [-n frames] [-o prefix] [-q]\n", argv[0]);
            return 2;
        }
    }

    sensor_handle_t h = NULL;
    sensor_error_t err = sensor_open((sensor_unit_t)unit, 0 /* ACCESSMODE_DATA */, &h);
    if (err != 0) {
        fprintf(stderr, "sensor_open(%d): err %d (%s)\n", unit, err, strerror(err));
        return 1;
    }

    err = sensor_register_data_callback(h, SENSOR_EVENT_BUFFER, SENSOR_EVENTMODE_READONLY,
                                        on_data, NULL);
    if (err != 0) {
        fprintf(stderr, "register_data_callback(BUFFER): err %d (%s) -- trying STREAM_DATA\n",
                err, strerror(err));
        err = sensor_register_data_callback(h, SENSOR_EVENT_STREAM_DATA,
                                            SENSOR_EVENTMODE_READONLY, on_data, NULL);
        if (err != 0) {
            fprintf(stderr, "register_data_callback(STREAM_DATA): err %d (%s)\n",
                    err, strerror(err));
            sensor_close(h);
            return 1;
        }
    }

    err = sensor_start(h, NULL);
    if (err != 0) {
        fprintf(stderr, "sensor_start: err %d (%s)\n", err, strerror(err));
        sensor_close(h);
        return 1;
    }
    fprintf(stderr, "streaming unit %d, want %d frame(s)\n", unit, g_want);

    for (int waited = 0; g_got < g_want && waited < 200; ++waited)
        usleep(100 * 1000);   /* callbacks arrive on the sensor thread */

    sensor_stop(h, NULL);
    sensor_close(h);
    fprintf(stderr, "captured %d frame(s)\n", g_got);
    return g_got > 0 ? 0 : 1;
}
