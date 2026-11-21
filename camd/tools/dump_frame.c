#define _POSIX_C_SOURCE 200809L

#include "beacon.h"

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#define DUMP_HEADER_BYTES (14u + 108u)

static void put_u16(uint8_t *p, uint16_t v)
{
    p[0] = (uint8_t)(v & 0xffu);
    p[1] = (uint8_t)(v >> 8);
}

static void put_u32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)(v & 0xffu);
    p[1] = (uint8_t)((v >> 8) & 0xffu);
    p[2] = (uint8_t)((v >> 16) & 0xffu);
    p[3] = (uint8_t)((v >> 24) & 0xffu);
}

static int write_bmp(const char *path, const beacon_frame_slot_t *slot)
{
    uint64_t needed = (uint64_t)slot->stride * slot->height;
    if (slot->width == 0u || slot->height == 0u || slot->stride < slot->width * 4u ||
        needed == 0u || needed > slot->bytes_used ||
        needed > UINT32_MAX - DUMP_HEADER_BYTES ||
        slot->height > (uint32_t)INT32_MAX) {
        fprintf(stderr, "dump-frame: frame metadata does not fit a BMP\n");
        return -1;
    }

    FILE *fp = fopen(path, "wb");
    if (fp == NULL) {
        fprintf(stderr, "dump-frame: open %s: %s\n", path, strerror(errno));
        return -1;
    }

    uint8_t header[DUMP_HEADER_BYTES];
    memset(header, 0, sizeof(header));
    header[0] = 'B';
    header[1] = 'M';
    put_u32(header + 2, (uint32_t)(DUMP_HEADER_BYTES + needed));
    put_u32(header + 10, DUMP_HEADER_BYTES);

    uint8_t *dib = header + 14;
    put_u32(dib, 108);                    /* BITMAPV4HEADER */
    put_u32(dib + 4, slot->width);
    put_u32(dib + 8, (uint32_t)(-(int32_t)slot->height)); /* top-down */
    put_u16(dib + 12, 1);                 /* planes */
    put_u16(dib + 14, 32);                /* bpp */
    put_u32(dib + 16, 3);                 /* BI_BITFIELDS */
    put_u32(dib + 20, (uint32_t)needed);
    put_u32(dib + 40, 0x00ff0000u);       /* red mask */
    put_u32(dib + 44, 0x0000ff00u);       /* green mask */
    put_u32(dib + 48, 0x000000ffu);       /* blue mask */
    put_u32(dib + 52, 0xff000000u);       /* alpha mask */

    if (fwrite(header, 1, sizeof(header), fp) != sizeof(header))
        goto write_failed;

    for (uint32_t y = 0; y < slot->height; ++y) {
        const uint8_t *row = slot->pixels + (size_t)y * slot->stride;
        if (fwrite(row, 1, slot->stride, fp) != slot->stride)
            goto write_failed;
    }

    if (fclose(fp) != 0) {
        fprintf(stderr, "dump-frame: close %s: %s\n", path, strerror(errno));
        return -1;
    }
    return 0;

write_failed:
    fprintf(stderr, "dump-frame: write %s: %s\n", path, strerror(errno));
    fclose(fp);
    return -1;
}

int main(int argc, char **argv)
{
    const char *path = (argc == 2) ? argv[1] : "/tmp/beacon_frame.bmp";
    if (argc > 2) {
        fprintf(stderr, "usage: %s [output.bmp]\n", argv[0]);
        return 2;
    }

    int fd = shm_open(BEACON_SHM_FRAMES, O_RDONLY, 0);
    if (fd == -1) {
        perror("dump-frame: shm_open");
        return 1;
    }
    size_t size = sizeof(beacon_frames_t);
    void *mem = mmap(NULL, size, PROT_READ, MAP_SHARED, fd, 0);
    close(fd);
    if (mem == MAP_FAILED) {
        perror("dump-frame: mmap");
        return 1;
    }

    beacon_frames_t *frames = (beacon_frames_t *)mem;
    if (frames->abi != BEACON_ABI_VERSION) {
        fprintf(stderr, "dump-frame: ABI mismatch (have %u, want %u)\n",
                frames->abi, BEACON_ABI_VERSION);
        munmap(mem, size);
        return 1;
    }

    beacon_frame_slot_t *candidate = (beacon_frame_slot_t *)malloc(sizeof(*candidate));
    beacon_frame_slot_t *best = (beacon_frame_slot_t *)malloc(sizeof(*best));
    if (candidate == NULL || best == NULL) {
        perror("dump-frame: malloc");
        free(candidate);
        free(best);
        munmap(mem, size);
        return 1;
    }

    uint32_t start = frames->newest_slot % BEACON_FRAME_SLOTS;
    uint64_t best_id = 0;
    int found = 0;
    for (uint32_t offset = 0; offset < BEACON_FRAME_SLOTS; ++offset) {
        uint32_t idx = (start + BEACON_FRAME_SLOTS - offset) % BEACON_FRAME_SLOTS;
        if (!beacon_seq_read(&frames->slot[idx].seq, candidate, &frames->slot[idx],
                             sizeof(*candidate), 8, NULL))
            continue;
        if (!found || candidate->frame_id > best_id) {
            memcpy(best, candidate, sizeof(*best));
            best_id = candidate->frame_id;
            found = 1;
        }
    }

    if (!found) {
        fprintf(stderr, "dump-frame: no stable slot found\n");
        free(candidate);
        free(best);
        munmap(mem, size);
        return 1;
    }

    int rc = write_bmp(path, best);
    if (rc == 0) {
        printf("wrote %s from frame_id=%" PRIu64 " (%ux%u, frametype=%u)\n",
               path, best->frame_id, best->width, best->height, best->frametype);
    }

    free(candidate);
    free(best);
    munmap(mem, size);
    return rc == 0 ? 0 : 1;
}
