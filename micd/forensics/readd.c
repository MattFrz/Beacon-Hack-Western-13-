/* Re-add the C270 audio EP (DCI 13) to the xHCI controller after the
 * QNX driver dropped it. Patches the driver input context, appends a
 * Configure Endpoint command TRB, rings the command doorbell, then
 * rings the EP doorbell and polls the TRB buffer for mic data. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#define RP1_OFF 0x1000000000ull
static volatile uint32_t*mp(uint64_t p,size_t l){
    volatile uint32_t*m=mmap(0,l,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,p);
    if(m==MAP_FAILED){printf("mmap 0x%llx FAILED\n",(unsigned long long)p);exit(1);}
    return m;}
int main(int argc,char**argv){
    uint64_t base=strtoull(argv[1],0,0);
    volatile uint32_t*op=mp(base+0x20,0x400);
    uint64_t dcbaap=((uint64_t)op[0x30/4+1]<<32)|op[0x30/4];
    uint64_t*d=(volatile uint64_t*)mp(dcbaap-RP1_OFF,0x1000);
    volatile uint32_t*ctx=(volatile uint32_t*)mp(d[1]-RP1_OFF,0x1000);
    volatile uint32_t*ec=(volatile uint32_t*)((uint8_t*)ctx+64+64*12);
    uint64_t ring=((((uint64_t)ec[3])<<32)|(ec[2]&0xfffffff0ull))-RP1_OFF;
    printf("EP13 dw0=%08x ring CPU=0x%llx\n",ec[0],(unsigned long long)ring);
    volatile uint32_t*tr=(volatile uint32_t*)mp(ring,0x100);
    printf("TRB[0]: %08x %08x %08x %08x\n",tr[0],tr[1],tr[2],tr[3]);
    uint64_t buf=((((uint64_t)tr[1])<<32)|tr[0])-RP1_OFF;
    printf("data buffer CPU=0x%llx len=%u\n",(unsigned long long)buf,tr[2]&0x1ffff);

    /* 1. patch driver input ctx at 0x1d7a000 (same ptr its own cmds use) */
    volatile uint32_t*ic=(volatile uint32_t*)mp(0x1d7a000,0x1000);
    /* copy current output slot ctx into input slot */
    volatile uint32_t*in_slot=(volatile uint32_t*)((uint8_t*)ic+8);
    for(int i=0;i<8;i++) in_slot[i]=((volatile uint32_t*)ctx)[i];
    in_slot[0]=(in_slot[0]&~0xf8000000u)|(15u<<27);  /* ctx entries>=13 */
    ic[0]=0x00002001;  /* ADD: slot + DCI13 */
    ic[1]=0;
    volatile uint32_t*in_ep=(volatile uint32_t*)((uint8_t*)ic+8+64+64*12);
    in_ep[0]=0x17030000u;              /* type=5 ISO IN, itv=3, cerr=3 */
    in_ep[1]=0x00000064u;              /* maxp 100 */
    in_ep[2]=(uint32_t)((ec[2]&0xfffffff0u)|1u); /* dequeue=ring start,DCS=1 */
    in_ep[3]=ec[3];
    in_ep[4]=0x00000064u;              /* avgTRB 100 */
    in_ep[5]=0x00000064u;              /* maxESIT lo 100 */
    printf("input ctx patched: EP13 dw0=%08x\n",in_ep[0]);

    /* 2. append Configure Endpoint command TRB at cmdring+0xb0, cycle 0 */
    volatile uint32_t*cr=(volatile uint32_t*)mp(0x1a5f000,0x2000);
    volatile uint32_t*ct=(volatile uint32_t*)((uint8_t*)cr+0xb0);
    ct[0]=0x01d7a000; ct[1]=0x00000010; ct[2]=0;
    ct[3]=0x08003000u;   /* cyc=0, type=12 CFG-EP, slot=1 */
    printf("cmd TRB written @0x1a5f0b0: %08x %08x %08x %08x\n",ct[0],ct[1],ct[2],ct[3]);

    /* 3. ring the command doorbell (slot 0) */
    volatile uint32_t*cap=mp(base,0x40);
    uint32_t dboff=cap[0x14/4];
    volatile uint32_t*db=mp(base+dboff,0x1000);
    db[0]=0;
    printf("command doorbell rung; waiting 300ms\n"); usleep(300000);
    printf("EP13 now: dw0=%08x dq=%08x\n",ec[0],ec[2]);

    /* 4. ring EP doorbell */
    db[1]=13;
    printf("EP doorbell rung (13); polling buffer for data\n");
    volatile uint32_t*audio=(volatile uint32_t*)mp(buf,0x100);
    for(int i=0;i<8;i++){ sleep(2);
        uint32_t nz=0; for(int w=0;w<25;w++) if(audio[w]) nz++;
        printf("t+%02ds: nonzero dwords in buffer: %u/25 | EP13 dq=%08x\n",
            (i+1)*2,nz,ec[2]); }
    return 0;}
