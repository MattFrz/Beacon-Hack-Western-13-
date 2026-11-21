#include "beacon.h"
#include <unistd.h>

/* Laptop heartbeat channel. The supervisor connects stdout to its pipe. */
int main(void)
{
    const char heartbeat = 'H';
    const struct timespec interval = {0, BEACON_SUP_TICK_NS};
    while (write(STDOUT_FILENO, &heartbeat, 1) == 1)
        nanosleep(&interval, NULL);
    return 0;
}
