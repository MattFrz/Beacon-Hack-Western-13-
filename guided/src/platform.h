/* platform.h: the only QNX-specific calls in guided, each with a laptop stand-in.
 * Everything QNX lives in platform.c behind #ifdef __QNX__. */
#ifndef GUIDED_PLATFORM_H
#define GUIDED_PLATFORM_H

/* Current thread: SCHED_FIFO at prio, pinned to runmask (QNX ThreadCtl).
 * Returns 0 on success, -1 if refused (normal on a laptop without root). */
int  platform_set_thread_sched(int prio, unsigned runmask);

/* GPIO piezo (spec §5.1). On a laptop these only count calls. */
int  platform_piezo_init(void);
void platform_piezo_set(int on);

/* Heartbeat pulse to the supervisor. spec is "pid:chid" from the supervisor's
 * argv. Without it (laptop or standalone) heartbeats only go into shm. */
int  platform_supervisor_connect(const char *spec);
void platform_heartbeat(void);

#endif /* GUIDED_PLATFORM_H */
