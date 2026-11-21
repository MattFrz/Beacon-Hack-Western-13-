#ifndef BEACON_PREVIEW_H
#define BEACON_PREVIEW_H

#include <netinet/in.h>

void preview_tick(int sock, const struct sockaddr_in *dest);

#endif
