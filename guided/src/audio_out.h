/* audio_out.h: where the mixed sound goes. 16 kHz, stereo, 16-bit.
 *
 *   none          print only (default)
 *   <file>.wav    record exactly what the wearer would hear (laptop testing)
 *   qnx           QNX io-audio, the default sound device (USB headset/speaker)
 *   fifo:<path>   Bluetooth speaker through Combadge-HTN/qnx-bluetooth's PCM
 *                 pipe (audio.pcm), resampled to 44.1 kHz stereo
 *
 * Only the audio thread calls these; never the 16 ms thread.
 */
#ifndef GUIDED_AUDIO_OUT_H
#define GUIDED_AUDIO_OUT_H

#include <stddef.h>
#include <stdint.h>

#define AUDIO_RATE     16000
#define AUDIO_CHANNELS 2
#define AUDIO_FRAME    160   /* 10 ms per block */

/* Returns 0 on success. On failure the caller falls back to "none". */
int  audio_out_open(const char *spec);
/* 1 if writes block at the device rate (the caller then does not sleep). */
int  audio_out_paced(void);
void audio_out_write(const int16_t *interleaved, size_t frames);
void audio_out_close(void);

#endif /* GUIDED_AUDIO_OUT_H */
