/*
 * epctx_probe.c — X-ray for the QNX dwc3-xhci stack's endpoint contexts.
 *
 * Maps the XHCI controller MMIO (base passed as argv[1]), walks
 * cap -> op -> DCBAAP -> slot device contexts, and dumps every endpoint
 * context that the stack actually programmed. Read-only by default;
 * with -w DCI:field:value it patches one 32-bit EP-context dword in
 * place (writes through the same physical mapping the driver uses).
 *
 * Build:  cc -O2 epctx_probe.c -o epctx_probe
 * Run:    sudo ./epctx_probe 0x1f00200000
 */

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>

#define XHCI_CAPLEN_MAX  0x40u
#define XHCI_OP_SIZE     0x400u
#define CTX_PER_PAGE      4096u

static volatile uint32_t *map_mmio(uint64_t phys, size_t len)
{
    void *p = mmap_device_memory(NULL, len, PROT_READ | PROT_WRITE, 0, phys);
    if (p == MAP_FAILED) {
        fprintf(stderr, "mmap 0x%llx len 0x%zx failed: %s\n",
                (unsigned long long)phys, len, strerror(errno));
        exit(1);
    }
    return (volatile uint32_t *)p;
}

static const char *ep_type_name(unsigned t)
{
    switch (t) {
    case 1: return "ISO OUT";
    case 2: return "BULK OUT";
    case 3: return "INT OUT";
    case 4: return "CONTROL";
    case 5: return "ISO IN";
    case 6: return "BULK IN";
    case 7: return "INT IN";
    default: return "?";
    }
}

static void dump_ep_ctx(unsigned dci, volatile uint32_t *ec)
{
    uint32_t dw0 = ec[0], dw1 = ec[1];
    unsigned state  = dw0 & 0x7;
    unsigned mult   = (dw0 >> 8) & 0x3;
    unsigned lsa    = (dw0 >> 15) & 0x1;
    unsigned itv    = (dw0 >> 16) & 0xff;
    unsigned cerr   = (dw0 >> 24) & 0x3;
    unsigned type   = (dw0 >> 26) & 0x1f;
    unsigned maxp   = dw1 & 0x7ff;
    unsigned burst  = (dw1 >> 16) & 0xff;
    uint32_t avg_trb = ec[4] & 0xffff;
    uint32_t esit_hi = ec[4] >> 16;
    uint32_t esit_lo = ec[5] & 0xffff;

    if (!state && !type && !maxp)
        return;                     /* empty context slot */

    printf(" DCI %2u: state=%u %s maxp=%3u burst=%u mult=%u itv=%2u "
           "(intv %u uf) cerr=%u lsa=%u avgTRB=%u maxESIT=%u\n",
           dci, state, ep_type_name(type), maxp, burst, mult, itv,
           (1u << itv), cerr, lsa, avg_trb,
           (unsigned)((esit_hi << 16) | esit_lo));
    printf("        dw: %08x %08x %08x %08x %08x %08x\n",
           ec[0], ec[1], ec[2], ec[3], ec[4], ec[5]);
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s mmio_base [slot] "
                "[-w dci:dword_index:value]\n", argv[0]);
        return 1;
    }
    uint64_t base = strtoull(argv[1], NULL, 0);
    int want_slot = (argc > 2 && argv[2][0] != '-') ? atoi(argv[2]) : -1;

    volatile uint32_t *cap = map_mmio(base, XHCI_CAPLEN_MAX);
    uint32_t caplen = cap[0] & 0xff;
    uint32_t dboff = cap[3];           /* DBOFF */
    uint32_t rtsoff = cap[4];           /* RTSOFF */
    (void)dboff; (void)rtsoff;

    volatile uint32_t *op = map_mmio(base + caplen, XHCI_OP_SIZE);
    uint64_t dcbaap = ((uint64_t)op[0x30 / 4 + 1] << 32) | op[0x30 / 4];
    uint32_t maxslots = (op[0x04 / 4] >> 0) & 0xff;
    printf("caplen=%u dboff=%#x rtsoff=%#x DCBAAP=0x%llx maxslots=%u\n",
           caplen, dboff, rtsoff, (unsigned long long)dcbaap, maxslots);

    volatile uint64_t *dcbaa =
        (volatile uint64_t *)map_mmio(dcbaap, CTX_PER_PAGE);

    for (int slot = 1; slot <= (int)maxslots; slot++) {
        uint64_t dc = dcbaa[slot];
        if (!dc) continue;
        if (want_slot > 0 && slot != want_slot) continue;
        printf("slot %d device context @ 0x%llx\n", slot,
               (unsigned long long)dc);
        volatile uint32_t *ctx =
            (volatile uint32_t *)map_mmio(dc & ~0xfffull, 0x1000);
        volatile uint32_t *slot_ctx = ctx + (dc & 0xfffull) / 4;
        printf("  slot ctx dw0=%08x (route 0x%x speed %u) "
               "dw1..3 %08x %08x %08x\n",
               slot_ctx[0], slot_ctx[0] & 0xf, (slot_ctx[0] >> 20) & 0xf,
               slot_ctx[1], slot_ctx[2], slot_ctx[3]);
        for (unsigned dci = 1; dci <= 31; dci++)
            dump_ep_ctx(dci, slot_ctx + 8 + (dci - 1) * 8);
    }
    return 0;
}
