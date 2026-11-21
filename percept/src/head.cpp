#define _POSIX_C_SOURCE 200809L

#include "beacon.h"

#include <cerrno>
#include <cinttypes>
#include <cstddef>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

namespace {

volatile sig_atomic_t g_stop = 0;

void on_signal(int)
{
    g_stop = 1;
}

struct Affine {
    uint32_t full_w;
    uint32_t full_h;
    uint32_t net_w;
    uint32_t net_h;
    double scale;
    double pad_x;
    double pad_y;
};

Affine make_affine(uint32_t full_w, uint32_t full_h, uint32_t net_w, uint32_t net_h)
{
    const double scale = net_w / static_cast<double>(full_w) <
                                 net_h / static_cast<double>(full_h)
                             ? net_w / static_cast<double>(full_w)
                             : net_h / static_cast<double>(full_h);
    return Affine{full_w, full_h, net_w, net_h,
                  scale, (net_w - full_w * scale) / 2.0,
                  (net_h - full_h * scale) / 2.0};
}

void print_affine(const char *name, const Affine &a)
{
    std::printf(",\"%s\":{\"full_w\":%u,\"full_h\":%u,\"net_w\":%u,\"net_h\":%u,"
                "\"scale\":%.9f,\"pad_x\":%.9f,\"pad_y\":%.9f}",
                name, a.full_w, a.full_h, a.net_w, a.net_h,
                a.scale, a.pad_x, a.pad_y);
}

struct FrameView {
    uint32_t slot;
    beacon_seq_t seq;
    uint64_t frame_id;
    uint64_t t_ns;
    uint32_t width;
    uint32_t height;
    uint32_t stride;
    uint32_t frametype;
    uint32_t bytes_used;
};

beacon_frames_t *open_frames_ro()
{
    int fd = shm_open(BEACON_SHM_FRAMES, O_RDONLY, 0);
    if (fd == -1) {
        std::perror("percept-head: shm_open frames");
        return nullptr;
    }
    void *mem = mmap(nullptr, sizeof(beacon_frames_t), PROT_READ, MAP_SHARED, fd, 0);
    close(fd);
    if (mem == MAP_FAILED) {
        std::perror("percept-head: mmap frames");
        return nullptr;
    }
    beacon_frames_t *frames = static_cast<beacon_frames_t *>(mem);
    if (frames->abi != BEACON_ABI_VERSION) {
        std::fprintf(stderr, "percept-head: frame ABI mismatch %u vs %u\n",
                     frames->abi, BEACON_ABI_VERSION);
        munmap(mem, sizeof(beacon_frames_t));
        return nullptr;
    }
    return frames;
}

void *init_abi_slot(const char *name, size_t size, size_t abi_offset)
{
    int fd = shm_open(name, O_CREAT | O_RDWR, 0666);
    if (fd == -1) {
        std::perror("percept-head: shm_open");
        return nullptr;
    }
    if (ftruncate(fd, static_cast<off_t>(size)) == -1) {
        std::perror("percept-head: ftruncate");
        close(fd);
        return nullptr;
    }
    void *mem = mmap(nullptr, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (mem == MAP_FAILED) {
        std::perror("percept-head: mmap");
        return nullptr;
    }
    uint32_t *abi = reinterpret_cast<uint32_t *>(static_cast<char *>(mem) + abi_offset);
    if (*abi != BEACON_ABI_VERSION) {
        std::memset(mem, 0, size);
        *abi = BEACON_ABI_VERSION;
    }
    return mem;
}

bool read_newest(beacon_frames_t *frames, FrameView &out)
{
    beacon_frame_slot_t *candidate =
        static_cast<beacon_frame_slot_t *>(std::malloc(sizeof(beacon_frame_slot_t)));
    if (candidate == nullptr) {
        std::perror("percept-head: malloc");
        return false;
    }

    const uint32_t start = frames->newest_slot % BEACON_FRAME_SLOTS;
    bool found = false;
    for (uint32_t offset = 0; offset < BEACON_FRAME_SLOTS; ++offset) {
        uint32_t idx = (start + BEACON_FRAME_SLOTS - offset) % BEACON_FRAME_SLOTS;
        beacon_seq_t seq = 0;
        if (!beacon_seq_read(&frames->slot[idx].seq, candidate, &frames->slot[idx],
                             sizeof(*candidate), 8, &seq))
            continue;
        if (!found || candidate->frame_id > out.frame_id) {
            out.slot = idx;
            out.seq = seq;
            out.frame_id = candidate->frame_id;
            out.t_ns = candidate->t_ns;
            out.width = candidate->width;
            out.height = candidate->height;
            out.stride = candidate->stride;
            out.frametype = candidate->frametype;
            out.bytes_used = candidate->bytes_used;
            found = true;
        }
    }

    std::free(candidate);
    return found;
}

int sleep_until_ns(uint64_t target_ns)
{
    timespec ts;
    ts.tv_sec = static_cast<time_t>(target_ns / 1000000000ull);
    ts.tv_nsec = static_cast<long>(target_ns % 1000000000ull);
    for (;;) {
        int rc = clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, nullptr);
        if (rc == 0)
            return 0;
        if (rc == EINTR)
            continue;
        return -1;
    }
}

void usage(const char *prog)
{
    std::fprintf(stderr,
                 "usage: %s [--once] [--frames N] [--hz N] [--yolo-size N] "
                 "[--depth-size N]\n",
                 prog);
}

} // namespace

int main(int argc, char **argv)
{
    bool once = false;
    long max_frames = 0;
    uint32_t hz = 10;
    uint32_t yolo_size = 320;
    uint32_t depth_size = 210;

    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--once") == 0) {
            once = true;
        } else if (std::strcmp(argv[i], "--frames") == 0 && i + 1 < argc) {
            max_frames = std::strtol(argv[++i], nullptr, 10);
        } else if (std::strcmp(argv[i], "--hz") == 0 && i + 1 < argc) {
            hz = static_cast<uint32_t>(std::strtoul(argv[++i], nullptr, 10));
        } else if (std::strcmp(argv[i], "--yolo-size") == 0 && i + 1 < argc) {
            yolo_size = static_cast<uint32_t>(std::strtoul(argv[++i], nullptr, 10));
        } else if (std::strcmp(argv[i], "--depth-size") == 0 && i + 1 < argc) {
            depth_size = static_cast<uint32_t>(std::strtoul(argv[++i], nullptr, 10));
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    if (hz == 0 || yolo_size == 0 || depth_size == 0) {
        std::fprintf(stderr, "percept-head: sizes and --hz must be positive\n");
        return 2;
    }

    beacon_frames_t *frames = open_frames_ro();
    if (frames == nullptr)
        return 1;

    void *depth_mem = init_abi_slot(BEACON_SHM_DEPTH, sizeof(beacon_depth_t),
                                    offsetof(beacon_depth_t, abi));
    void *world_mem = init_abi_slot(BEACON_SHM_WORLD, sizeof(beacon_world_t),
                                    offsetof(beacon_world_t, abi));
    (void)depth_mem;
    (void)world_mem;

    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);

    uint64_t period_ns = 1000000000ull / hz;
    uint64_t next_ns = beacon_now_ns() + period_ns;
    long seen = 0;

    while (!g_stop) {
        FrameView view{};
        if (read_newest(frames, view)) {
            Affine yolo = make_affine(view.width, view.height, yolo_size, yolo_size);
            Affine depth_a = make_affine(view.width, view.height, depth_size, depth_size);
            std::printf("{\"kind\":\"frame\",\"slot\":%u,\"seq\":%u,"
                        "\"frame_id\":%" PRIu64 ",\"t_ns\":%" PRIu64 ","
                        "\"W\":%u,\"H\":%u,\"stride\":%u,\"frametype\":%u,"
                        "\"bytes_used\":%u",
                        view.slot, view.seq, view.frame_id, view.t_ns,
                        view.width, view.height, view.stride, view.frametype,
                        view.bytes_used);
            print_affine("yolo_affine", yolo);
            print_affine("depth_affine", depth_a);
            std::printf(",\"model_outputs\":0,\"shm_writes\":\"abi-only\"}\n");
        } else {
            std::fprintf(stderr, "percept-head: no stable frame slot\n");
        }

        ++seen;
        if (once || (max_frames > 0 && seen >= max_frames))
            break;

        next_ns += period_ns;
        uint64_t now_ns = beacon_now_ns();
        if (next_ns < now_ns)
            next_ns = now_ns + period_ns;
        if (sleep_until_ns(next_ns) == -1) {
            std::perror("percept-head: clock_nanosleep");
            break;
        }
    }

    munmap(frames, sizeof(*frames));
    return 0;
}
