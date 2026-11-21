/* Print the beacon_frames layout so Python tests can verify their mirror. */
#define _POSIX_C_SOURCE 200809L

#include "beacon.h"

#include <stddef.h>
#include <stdio.h>

int main(void)
{
    printf("abi=%u\n", (unsigned)BEACON_ABI_VERSION);
    printf("frame_slots=%u\n", (unsigned)BEACON_FRAME_SLOTS);
    printf("frame_max_bytes=%zu\n", (size_t)BEACON_FRAME_MAX_BYTES);
    printf("sizeof_frames=%zu\n", sizeof(beacon_frames_t));
    printf("sizeof_slot=%zu\n", sizeof(beacon_frame_slot_t));
    printf("offsetof_newest_slot=%zu\n", offsetof(beacon_frames_t, newest_slot));
    printf("offsetof_slot=%zu\n", offsetof(beacon_frames_t, slot));
    printf("offsetof_seq=%zu\n", offsetof(beacon_frame_slot_t, seq));
    printf("offsetof_frame_id=%zu\n", offsetof(beacon_frame_slot_t, frame_id));
    return 0;
}
