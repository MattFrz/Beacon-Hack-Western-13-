#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#define RP1_OFF 0x1000000000ull
static volatile uint32_t*mp(uint64_t p,size_t l){
    volatile uint32_t*m=mmap(0,l,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,p);
    if(m==MAP_FAILED){printf("mmap 0x%llx FAIL\n",(unsigned long long)p);exit(1);}
    return m;}
int main(int argc,char**argv){
    uint64_t base=strtoull(argv[1],0,0);
    volatile uint32_t*op=mp(base+0x20,0x400);
    uint64_t dcbaap=((uint64_t)op[0x30/4+1]<<32)|op[0x30/4];
    volatile uint64_t*d=(volatile uint64_t*)mp(dcbaap-RP1_OFF,0x1000);
    volatile uint32_t*ctx=(volatile uint32_t*)mp(d[1]-RP1_OFF,0x1000);
    volatile uint32_t*ec=(volatile uint32_t*)((uint8_t*)ctx+64+64*12);
    uint64_t ring=((((uint64_t)ec[3])<<32)|(ec[2]&0xfffffff0ull))-RP1_OFF;
    uint32_t dcs=ec[2]&1;
    printf("EP13: state=%u itv=%u dq=%08x DCS=%u ring=0x%llx\n",
        ec[0]&7,(ec[0]>>16)&0xff,ec[2],dcs,(unsigned long long)ring);
    volatile uint32_t*seg=mp(ring,0x1000);
    int flipped=0; uint64_t buf0=0; uint32_t len0=0;
    for(int i=0;i<255;i++){
        volatile uint32_t*t=seg+i*4;
        unsigned type=(t[3]>>10)&0x3f, cyc=t[3]&1;
        if(type==5 && !cyc){ t[3]|=1; flipped++;
            if(!buf0){ buf0=(((uint64_t)t[1])<<32)|t[0]; len0=t[2]&0x1ffff; } }
    }
    printf("flipped cycle on %d ISOCH TRBs\n",flipped);
    volatile uint32_t*cap=mp(base,0x40);
    uint32_t dboff=cap[0x14/4];
    volatile uint32_t*db=mp(base+dboff,0x1000);
    db[1]=13; printf("doorbell 13 rung; polling buffer 0x%llx\n",(unsigned long long)(buf0-RP1_OFF));
    volatile uint32_t*audio=mp(buf0-RP1_OFF,0x100);
    for(int i=0;i<8;i++){ sleep(2);
        uint32_t nz=0; for(int w=0;w<25;w++) if(audio[w]) nz++;
        printf("t+%02ds: nonzero dwords: %u/25 | EP13 dq=%08x\n",(i+1)*2,nz,ec[2]); }
    return 0;}
