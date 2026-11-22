/* platform.c: QNX calls for guided, with laptop stand-ins. See platform.h. */
#include "platform.h"
#include "beacon.h"

#include <errno.h>
#include <pthread.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef __QNX__
#include <sys/neutrino.h>
#endif

int platform_set_thread_sched(int prio, unsigned runmask)
{
    int rc = 0;
#ifdef __QNX__
    /* Pin first (spec §5.1: set the runmask on every thread we create). */
    if (ThreadCtl(_NTO_TCTL_RUNMASK, (void *)(uintptr_t)runmask) == -1) {
        rc = -1;
        fprintf(stderr, "guided: runmask 0x%x rejected: %s\n", runmask, strerror(errno));
    } else {
        /* Read it back: `pidin -F %%i` renders empty on this image, so the
         * kernel's own answer is the evidence for the core-0 claim. */
        int now = ThreadCtl(_NTO_TCTL_RUNMASK_GET_AND_SET, (void *)(uintptr_t)runmask);
        fprintf(stderr, "guided: runmask 0x%x applied (kernel readback 0x%x)\n",
                runmask, (unsigned)now);
    }
#else
    (void)runmask; /* laptop: do not pin, the laptop has other work to do */
#endif
    struct sched_param sp;
    memset(&sp, 0, sizeof(sp));
    sp.sched_priority = prio;
    if (pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp) != 0)
        rc = -1;
    return rc;
}

/* ------------------------------------------------------------------ piezo */
static int g_piezo_state;
static unsigned long g_piezo_toggles;

int platform_piezo_init(void)
{
#ifdef __QNX__
    /* TODO(Nathan wiring, Munadir code): open the GPIO pin for the piezo
     * transistor using the QNX rpi_gpio sample
     * (github.com/qnx/Raspberry-Pi-Hardware-Component-Samples). Until the
     * buzzer and transistor arrive this stays a no-op. */
#endif
    g_piezo_state = 0;
    return 0;
}

void platform_piezo_set(int on)
{
    on = on ? 1 : 0;
    if (on == g_piezo_state)
        return;
    g_piezo_state = on;
    g_piezo_toggles++;
#ifdef __QNX__
    /* TODO: non-blocking GPIO write of `on` (must never block the 16 ms thread). */
#endif
}

/* ------------------------------------------------------------------ heartbeat */
#ifdef __QNX__
static int g_sup_coid = -1;
#endif

int platform_supervisor_connect(const char *spec)
{
    if (!spec)
        return -1;
#ifdef __QNX__
    int pid = 0, chid = 0;
    if (sscanf(spec, "%d:%d", &pid, &chid) != 2)
        return -1;
    g_sup_coid = ConnectAttach(0, pid, chid, _NTO_SIDE_CHANNEL, 0);
    return g_sup_coid == -1 ? -1 : 0;
#else
    fprintf(stderr, "guided: --sup %s ignored (supervisor pulses are QNX-only)\n", spec);
    return -1;
#endif
}

void platform_heartbeat(void)
{
#ifdef __QNX__
    if (g_sup_coid != -1)
        MsgSendPulse(g_sup_coid, BEACON_PRIO_GUIDED,
                     _PULSE_CODE_MINAVAIL + BEACON_PULSE_HB_GUIDED, 0);
#endif
}
