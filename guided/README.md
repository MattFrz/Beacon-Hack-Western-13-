# guided

Owner: Munadir. C, core 0 (`0x1`), `SCHED_FIFO` 58. The 60 Hz synthesizer: mode, bind, laws (including REPEAT / REJECT), piezo, audio thread. No models, no blocking writes on the 16 ms thread. QNX calls behind `#ifdef __QNX__` so it runs on a laptop. Design: [`docs/nathans-revision.md`](../docs/nathans-revision.md) §6, §9, §10.
