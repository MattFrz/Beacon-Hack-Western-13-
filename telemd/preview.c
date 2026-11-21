#include "beacon.h"
#include "preview.h"
#include <fcntl.h>
#include <setjmp.h>
#include <stdio.h>
#include <jpeglib.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <unistd.h>

enum { MAX_SIDE = 320, JPEG_LIMIT = 60000 };

static unsigned char rgb[MAX_SIDE * MAX_SIDE * 3];

/* Copy only the preview pixels. All indexing uses validated local dimensions
 * even if camd starts overwriting this slot during sampling. */
static int sample_frame(const volatile beacon_frames_t *ring, uint64_t now,
                        uint64_t *last_capture, unsigned *width, unsigned *height)
{
    unsigned index = ring->newest_slot;
    if (ring->abi != BEACON_ABI_VERSION || index >= BEACON_FRAME_SLOTS)
        return 0;
    const volatile beacon_frame_slot_t *s = &ring->slot[index];
    beacon_seq_t seq = s->seq;
    __sync_synchronize();
    if (seq & 1u)
        return 0;
    uint64_t capture = s->t_ns;
    unsigned w = s->width, h = s->height, stride = s->stride, bytes = s->bytes_used;
    /* Type 0 is Nathan's synthetic BGRX layout. Hardware types await the Pi probe. */
    if (!capture || capture <= *last_capture || capture > now || now - capture >= UINT64_C(1000000000) ||
        s->frametype != 0 || !w || !h || (uint64_t)w * 4 > stride ||
        (uint64_t)stride * h > bytes || bytes > BEACON_FRAME_MAX_BYTES)
        return 0;

    unsigned side = w > h ? w : h;
    *width = side > MAX_SIDE ? (uint64_t)w * MAX_SIDE / side : w;
    *height = side > MAX_SIDE ? (uint64_t)h * MAX_SIDE / side : h;
    if (!*width || !*height)
        return 0;
    unsigned char *out = rgb;
    for (unsigned y = 0; y < *height; ++y) {
        const volatile unsigned char *row = s->pixels + (size_t)(y * h / *height) * stride;
        for (unsigned x = 0; x < *width; ++x) {
            const volatile unsigned char *pixel = row + (x * w / *width) * 4;
            *out++ = pixel[2];
            *out++ = pixel[1];
            *out++ = pixel[0];
        }
    }
    __sync_synchronize();
    if (s->seq != seq)
        return 0;
    *last_capture = capture;
    return 1;
}

struct jpeg_error {
    struct jpeg_error_mgr base;
    jmp_buf recovery;
};

static void skip_jpeg(j_common_ptr jpeg)
{
    struct jpeg_error *error = (struct jpeg_error *)jpeg->err;
    longjmp(error->recovery, 1);
}

static void destination_ready(j_compress_ptr jpeg)
{
    (void)jpeg;
}

static boolean destination_full(j_compress_ptr jpeg)
{
    skip_jpeg((j_common_ptr)jpeg);
    return FALSE;
}

static void send_jpeg(int sock, const struct sockaddr_in *dest, unsigned w, unsigned h)
{
    /* Static storage keeps encoder cleanup valid across libjpeg's error jump. */
    static struct jpeg_compress_struct jpeg;
    static JOCTET data[JPEG_LIMIT];
    struct jpeg_destination_mgr output = {
        .next_output_byte = data, .free_in_buffer = sizeof(data),
        .init_destination = destination_ready, .term_destination = destination_ready,
        .empty_output_buffer = destination_full
    };
    struct jpeg_error error;
    jpeg.err = jpeg_std_error(&error.base);
    error.base.error_exit = skip_jpeg;
    if (setjmp(error.recovery) == 0) {
        jpeg_create_compress(&jpeg);
        jpeg.dest = &output;
        jpeg.image_width = w;
        jpeg.image_height = h;
        jpeg.input_components = 3;
        jpeg.in_color_space = JCS_RGB;
        jpeg_set_defaults(&jpeg);
        jpeg_set_quality(&jpeg, 65, TRUE);
        jpeg_start_compress(&jpeg, TRUE);
        while (jpeg.next_scanline < h) {
            JSAMPROW row = rgb + jpeg.next_scanline * w * 3;
            jpeg_write_scanlines(&jpeg, &row, 1);
        }
        jpeg_finish_compress(&jpeg);
        size_t size = sizeof(data) - output.free_in_buffer;
        if (size < JPEG_LIMIT && sendto(sock, data, size, 0,
                (const struct sockaddr *)dest, sizeof(*dest)) < 0)
            perror("send preview");
    }
    jpeg_destroy_compress(&jpeg);
}

void preview_tick(int sock, const struct sockaddr_in *dest)
{
    static uint64_t next_attempt, last_capture;
    uint64_t now = beacon_now_ns();
    if (now < next_attempt)
        return;
    next_attempt = now + UINT64_C(200000000);

    /* Reopen by name so a late or restarted camera can replace the ring. */
    int fd = shm_open(BEACON_SHM_FRAMES, O_RDONLY, 0);
    if (fd < 0)
        return;
    struct stat st;
    const beacon_frames_t *ring = MAP_FAILED;
    if (fstat(fd, &st) == 0 && st.st_size >= (off_t)sizeof(*ring))
        ring = mmap(NULL, sizeof(*ring), PROT_READ, MAP_SHARED, fd, 0);
    close(fd);
    if (ring == MAP_FAILED)
        return;
    unsigned width, height;
    int ready = sample_frame(ring, now, &last_capture, &width, &height);
    munmap((void *)ring, sizeof(*ring));
    if (ready)
        send_jpeg(sock, dest, width, height);
}
