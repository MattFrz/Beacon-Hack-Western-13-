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

int main(void)
{
    int fd = shm_open(BEACON_SHM_FRAMES, O_RDONLY, 0);
    if (fd == -1) {
        perror("read-frames: shm_open");
        return 1;
    }

    size_t size = sizeof(beacon_frames_t);
    void *mem = mmap(NULL, size, PROT_READ, MAP_SHARED, fd, 0);
    close(fd);
    if (mem == MAP_FAILED) {
        perror("read-frames: mmap");
        return 1;
    }

    beacon_frames_t *frames = (beacon_frames_t *)mem;
    if (frames->abi != BEACON_ABI_VERSION) {
        fprintf(stderr, "read-frames: ABI mismatch (have %u, want %u)\n",
                frames->abi, BEACON_ABI_VERSION);
        munmap(mem, size);
        return 1;
    }

    beacon_frame_slot_t *best = malloc(sizeof(*best));
    beacon_frame_slot_t *candidate = malloc(sizeof(*candidate));
    if (best == NULL || candidate == NULL) {
        perror("read-frames: malloc");
        free(best);
        free(candidate);
        munmap(mem, size);
        return 1;
    }

    uint32_t start = frames->newest_slot % BEACON_FRAME_SLOTS;
    uint32_t best_idx = 0;
    beacon_seq_t best_seq = 0;
    uint64_t best_id = 0;
    int found = 0;

    for (uint32_t offset = 0; offset < BEACON_FRAME_SLOTS; ++offset) {
        uint32_t idx = (start + BEACON_FRAME_SLOTS - offset) % BEACON_FRAME_SLOTS;
        beacon_seq_t seq = 0;
        if (!beacon_seq_read(&frames->slot[idx].seq, candidate, &frames->slot[idx],
                             sizeof(*candidate), 8, &seq))
            continue;
        if (!found || candidate->frame_id > best_id) {
            memcpy(best, candidate, sizeof(*best));
            best_idx = idx;
            best_seq = seq;
            best_id = candidate->frame_id;
            found = 1;
        }
    }

    if (!found) {
        fprintf(stderr, "read-frames: no stable slot found\n");
        free(best);
        free(candidate);
        munmap(mem, size);
        return 1;
    }

    printf("slot=%u seq=%u frame_id=%" PRIu64 " t_ns=%" PRIu64
           " width=%u height=%u stride=%u frametype=%u bytes_used=%u\n",
           best_idx, best_seq, best->frame_id, best->t_ns, best->width,
           best->height, best->stride, best->frametype, best->bytes_used);

    free(best);
    free(candidate);
    munmap(mem, size);
    return 0;
}
