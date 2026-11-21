#define _GNU_SOURCE

#include "beacon.h"

#include <errno.h>
#include <inttypes.h>
#include <pthread.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef __QNX__
#include <sys/neutrino.h>
#endif

#define MAX_SAMPLES 3600u
#define DEFAULT_SAMPLES 600u
#define PERIOD_NS BEACON_GUIDED_PERIOD_NS
#define MISS_NS 1000000ull

static const uint64_t kThresholds[] = {1000000ull, 2000000ull, 8000000ull,
                                       (uint64_t)BEACON_GUIDED_PERIOD_NS};

static volatile int g_stop = 0;
static uint64_t g_late[MAX_SAMPLES];

static int pin_cpu(unsigned cpu)
{
#ifdef __QNX__
    int runmask = 1 << cpu;
    if (ThreadCtl(_NTO_TCTL_RUNMASK, (void *)(intptr_t)runmask) == -1) {
        perror("deadline-test: ThreadCtl RUNMASK");
        return -1;
    }
#else
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET((int)cpu, &set);
    if (sched_setaffinity(0, sizeof(set), &set) == -1) {
        perror("deadline-test: sched_setaffinity");
        return -1;
    }
#endif
    return 0;
}

static void set_fifo(int priority)
{
    struct sched_param param;
    memset(&param, 0, sizeof(param));
    param.sched_priority = priority;
    if (pthread_setschedparam(pthread_self(), SCHED_FIFO, &param) != 0)
        fprintf(stderr, "deadline-test: could not set FIFO %d\n", priority);
}

static void *hog(void *arg)
{
    unsigned cpu = (unsigned)(uintptr_t)arg;
    if (pin_cpu(cpu) == -1)
        return NULL;
    set_fifo(10);

    volatile double x = 1.0;
    while (!g_stop) {
        for (int i = 0; i < 20000; ++i)
            x = x * 1.000001 + 0.000001;
    }
    return (void *)(uintptr_t)(x > 0.0);
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

static int cmp_u64(const void *a, const void *b)
{
    uint64_t x = *(const uint64_t *)a;
    uint64_t y = *(const uint64_t *)b;
    return x < y ? -1 : x > y ? 1 : 0;
}

int main(int argc, char **argv)
{
    unsigned hog_count = 3;
    uint32_t samples = DEFAULT_SAMPLES;
    for (int i = 1; i < argc; i += 2) {
        if (i + 1 >= argc)
            break;
        if (strcmp(argv[i], "--hogs") == 0) {
            hog_count = (unsigned)strtoul(argv[i + 1], NULL, 10);
            if (hog_count > 3) {
                fprintf(stderr, "deadline-test: --hogs must be 0..3\n");
                return 2;
            }
        } else if (strcmp(argv[i], "--samples") == 0) {
            unsigned long n = strtoul(argv[i + 1], NULL, 10);
            if (n == 0 || n > MAX_SAMPLES) {
                fprintf(stderr, "deadline-test: --samples must be 1..%u\n",
                        MAX_SAMPLES);
                return 2;
            }
            samples = (uint32_t)n;
        } else {
            break;
        }
    }
    if (argc % 2 == 0) {
        fprintf(stderr, "usage: %s [--hogs 0..3] [--samples 1..%u]\n",
                argv[0], MAX_SAMPLES);
        return 2;
    }

    if (pin_cpu(0) == -1)
        return 1;
    set_fifo((int)BEACON_PRIO_GUIDED);

    pthread_t hogs[3];
    for (unsigned i = 0; i < hog_count; ++i) {
        if (pthread_create(&hogs[i], NULL, hog, (void *)(uintptr_t)(i + 1)) != 0) {
            fprintf(stderr, "deadline-test: pthread_create hog %u failed\n", i + 1);
            return 1;
        }
    }

    uint64_t target = beacon_now_ns() + PERIOD_NS;
    uint64_t misses = 0;
    uint64_t worst = 0;
    uint64_t threshold_misses[4] = {0, 0, 0, 0};

    for (uint32_t i = 0; i < samples; ++i) {
        if (sleep_until_ns(target) == -1) {
            perror("deadline-test: clock_nanosleep");
            break;
        }
        uint64_t now = beacon_now_ns();
        uint64_t late = now > target ? now - target : 0;
        g_late[i] = late;
        if (late > worst)
            worst = late;
        if (late > MISS_NS)
            ++misses;
        for (size_t t = 0; t < 4; ++t) {
            if (late > kThresholds[t])
                ++threshold_misses[t];
        }
        target += PERIOD_NS;
        uint64_t now2 = beacon_now_ns();
        if (target < now2)
            target = now2 + PERIOD_NS;
    }

    g_stop = 1;
    for (unsigned i = 0; i < hog_count; ++i)
        pthread_join(hogs[i], NULL);

    qsort(g_late, samples, sizeof(g_late[0]), cmp_u64);
    uint64_t p95 = g_late[(samples * 95u) / 100u];

    printf("{\"samples\":%u,\"period_ns\":%" PRIu64 ",\"miss_threshold_ns\":%" PRIu64
           ",\"misses\":%" PRIu64 ",\"worst_late_ns\":%" PRIu64
           ",\"p95_late_ns\":%" PRIu64 ",\"prio\":%d,\"core\":0,\"hogs\":%u"
           ",\"over_1ms\":%" PRIu64 ",\"over_2ms\":%" PRIu64
           ",\"over_8ms\":%" PRIu64 ",\"over_period\":%" PRIu64 "}\n",
           samples, (uint64_t)PERIOD_NS, (uint64_t)MISS_NS, misses, worst, p95,
           (int)BEACON_PRIO_GUIDED, hog_count, threshold_misses[0],
           threshold_misses[1], threshold_misses[2], threshold_misses[3]);
    return 0;
}
